import json
import platform
import re
import sys
from dataclasses import dataclass

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from . import __version__

REPOSITORY_URL = "https://github.com/murums04/ps4-unfself-ui"
LATEST_RELEASE_API = "https://api.github.com/repos/murums04/ps4-unfself-ui/releases/latest"
MAX_RESPONSE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class Release:
    version: str
    release_url: str
    download_url: str


def version_parts(value):
    if not isinstance(value, str) or not re.fullmatch(r"v?(0|[1-9]\d{0,5})\.(0|[1-9]\d{0,5})\.(0|[1-9]\d{0,5})", value):
        raise ValueError("Invalid stable release version")
    return tuple(int(part) for part in value.removeprefix("v").split("."))


def portable_asset_name(version, system, machine):
    architecture = {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(machine.lower())
    target = {"win32": "windows", "darwin": "macos", "linux": "linux"}.get(system)
    if not target or not architecture or (architecture != "x64" and target != "macos"):
        return None
    extension = "tar.gz" if target == "linux" else "zip"
    return f"ps4-unfself-ui-{version}-{target}-{architecture}-portable.{extension}"


def parse_release(data, current_version, system=None, machine=None):
    if not isinstance(data, dict):
        raise ValueError("Invalid release response")
    if data.get("draft") or data.get("prerelease"):
        return None
    tag = data.get("tag_name")
    latest_version = version_parts(tag)
    if latest_version <= version_parts(current_version):
        return None
    release_url = f"{REPOSITORY_URL}/releases/tag/{tag}"
    if data.get("html_url") != release_url:
        raise ValueError("Unexpected release location")
    version = tag.removeprefix("v")
    asset_name = portable_asset_name(version, system or sys.platform, machine or platform.machine())
    assets = data.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("Invalid release assets")
    download_url = ""
    if asset_name:
        expected_url = f"{REPOSITORY_URL}/releases/download/{tag}/{asset_name}"
        for asset in assets:
            if (isinstance(asset, dict) and asset.get("name") == asset_name
                    and asset.get("state") == "uploaded" and asset.get("browser_download_url") == expected_url):
                download_url = expected_url
                break
    return Release(version, release_url, download_url)


class UpdateChecker(QObject):
    changed = Signal()

    def __init__(self, parent=None, *, endpoint=LATEST_RELEASE_API, timeout_ms=8000):
        super().__init__(parent)
        self.endpoint = endpoint
        self.timeout_ms = timeout_ms
        self.manager = QNetworkAccessManager(self)
        self.reply = None
        self.body = bytearray()
        self.failure_message = ""
        self.state = "idle"
        self.message = "Check GitHub for updates."
        self.release = None
        self.deadline = QTimer(self)
        self.deadline.setSingleShot(True)
        self.deadline.timeout.connect(lambda: self.abort("Check timed out. Retry later."))
        self.startup_timer = QTimer(self)
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self.check)

    @property
    def busy(self):
        return self.reply is not None

    def start_automatic_check(self):
        self.startup_timer.start(1200)

    def set_status(self, state, message):
        self.state = state
        self.message = message
        self.changed.emit()

    def check(self):
        self.startup_timer.stop()
        if self.busy:
            return
        self.body.clear()
        self.failure_message = ""
        request = QNetworkRequest(QUrl(self.endpoint))
        request.setRawHeader(b"Accept", b"application/vnd.github+json")
        request.setRawHeader(b"User-Agent", f"ps4-unfself-ui/{__version__}".encode("ascii"))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        self.reply = self.manager.get(request)
        self.reply.setReadBufferSize(MAX_RESPONSE_BYTES + 1)
        self.reply.readyRead.connect(self.read_response)
        self.reply.finished.connect(self.finish)
        self.deadline.start(self.timeout_ms)
        self.set_status("checking", "Checking GitHub…")

    def read_response(self):
        self.body.extend(bytes(self.reply.read(MAX_RESPONSE_BYTES + 1 - len(self.body))))
        if len(self.body) > MAX_RESPONSE_BYTES:
            self.abort("GitHub response too large. Retry later.")

    def abort(self, message):
        if self.reply is not None:
            self.failure_message = message
            self.reply.abort()

    def finish(self):
        self.deadline.stop()
        reply = self.reply
        self.reply = None
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error = reply.error()
        reply.deleteLater()
        if self.failure_message:
            self.set_status("error", self.failure_message)
        elif status == 404:
            self.set_status("unpublished", "No public release yet.")
        elif status in (403, 429):
            self.set_status("error", "GitHub rate limit. Retry later.")
        elif status != 200 or error != QNetworkReply.NetworkError.NoError:
            self.set_status("error", "Cannot reach GitHub. Check your connection; retry.")
        else:
            try:
                release = parse_release(json.loads(self.body), __version__)
            except (ValueError, UnicodeError, RecursionError):
                self.set_status("error", "Invalid GitHub release data. Retry later.")
            else:
                self.release = release
                if release:
                    self.set_status("available", f"Update available: {release.version}")
                else:
                    self.set_status("current", "Up to date (stable).")
        self.body.clear()
