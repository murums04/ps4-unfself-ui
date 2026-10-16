import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from unfself_ui.updates import REPOSITORY_URL, UpdateChecker, parse_release


def release_data(version="0.2.0", target="windows-x64", extension="zip"):
    tag = f"v{version}"
    name = f"ps4-unfself-ui-{version}-{target}-portable.{extension}"
    return {
        "tag_name": tag, "draft": False, "prerelease": False,
        "html_url": f"{REPOSITORY_URL}/releases/tag/{tag}",
        "assets": [{"name": name, "state": "uploaded",
                    "browser_download_url": f"{REPOSITORY_URL}/releases/download/{tag}/{name}"}],
    }


@pytest.mark.parametrize("system,machine,target,extension", [
    ("win32", "AMD64", "windows-x64", "zip"),
    ("darwin", "arm64", "macos-arm64", "zip"),
    ("darwin", "x86_64", "macos-x64", "zip"),
    ("linux", "x86_64", "linux-x64", "tar.gz"),
])
def test_new_release_selects_matching_portable_download(system, machine, target, extension):
    data = release_data(target=target, extension=extension)
    release = parse_release(data, "0.1.0", system, machine)
    assert release.version == "0.2.0"
    assert release.download_url == data["assets"][0]["browser_download_url"]


@pytest.mark.parametrize("version", ["0.1.0", "0.0.9"])
def test_current_or_older_version_has_no_update(version):
    assert parse_release(release_data(version), "0.1.0", "win32", "AMD64") is None


def test_numeric_version_comparison():
    assert parse_release(release_data("0.10.0"), "0.9.0", "win32", "AMD64")


@pytest.mark.parametrize("flag", ["draft", "prerelease"])
def test_unstable_releases_are_ignored(flag):
    data = release_data()
    data[flag] = True
    assert parse_release(data, "0.1.0", "win32", "AMD64") is None


@pytest.mark.parametrize("tag", ["v0.2.0-beta", "../../setup.exe", "<b>0.2.0</b>", None])
def test_invalid_version_is_rejected(tag):
    data = release_data()
    data["tag_name"] = tag
    with pytest.raises(ValueError):
        parse_release(data, "0.1.0", "win32", "AMD64")


@pytest.mark.parametrize("url", ["file:///C:/evil.exe", "https://github.com.evil.example/release",
                                 "https://github.com/other/repo/releases/tag/v0.2.0"])
def test_unexpected_release_links_are_rejected(url):
    data = release_data()
    data["html_url"] = url
    with pytest.raises(ValueError):
        parse_release(data, "0.1.0", "win32", "AMD64")


def test_unsafe_asset_or_unmatched_platform_uses_release_page():
    data = release_data()
    data["assets"][0]["browser_download_url"] = "https://evil.example/update.exe"
    release = parse_release(data, "0.1.0", "win32", "AMD64")
    assert not release.download_url
    assert release.release_url == data["html_url"]
    assert not parse_release(release_data(), "0.1.0", "linux", "aarch64").download_url


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def server():
    response = {"status": 200, "body": json.dumps(release_data()).encode(), "delay": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(response["delay"])
            try:
                self.send_response(response["status"])
                self.end_headers()
                self.wfile.write(response["body"])
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{http.server_port}/latest", response
    http.shutdown()
    http.server_close()
    thread.join(timeout=2)


def finish_check(application, checker):
    deadline = time.monotonic() + 3
    while checker.busy and time.monotonic() < deadline:
        QTest.qWait(10)
    assert not checker.busy


@pytest.mark.parametrize("status,state", [(200, "available"), (404, "unpublished"),
                                         (403, "error"), (429, "error"), (500, "error")])
def test_http_results_are_reported_without_blocking(application, server, status, state):
    endpoint, response = server
    response["status"] = status
    checker = UpdateChecker(endpoint=endpoint)
    checker.check()
    assert checker.busy
    finish_check(application, checker)
    assert checker.state == state
    checker.deleteLater()


@pytest.mark.parametrize("body", [b"not JSON", b"[]", b"{}", b"x" * (1024 * 1024 + 1)],
                         ids=["invalid-json", "array", "missing-fields", "oversized"])
def test_bad_responses_can_be_retried(application, server, body):
    endpoint, response = server
    response["body"] = body
    checker = UpdateChecker(endpoint=endpoint)
    checker.check()
    finish_check(application, checker)
    assert checker.state == "error"
    response["body"] = json.dumps(release_data()).encode()
    checker.check()
    finish_check(application, checker)
    assert checker.state == "available"
    checker.deleteLater()


def test_timeout_leaves_event_loop_responsive(application, server):
    endpoint, response = server
    response["delay"] = 0.4
    checker = UpdateChecker(endpoint=endpoint, timeout_ms=100)
    ticks = []
    timer = QTimer()
    timer.timeout.connect(lambda: ticks.append(True))
    timer.start(10)
    checker.check()
    finish_check(application, checker)
    timer.stop()
    assert ticks and checker.state == "error"
    assert "timed out" in checker.message
    checker.deleteLater()
