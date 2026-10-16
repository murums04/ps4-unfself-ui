import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from unfself_ui import converter


def test_posix_publication_preserves_existing_files(tmp_path, monkeypatch):
    temporary = tmp_path / "partial.tmp"
    temporary.write_bytes(b"complete ELF")
    source = tmp_path / "source.self"
    source.write_bytes(b"original")
    existing = tmp_path / "source.elf"
    existing.write_bytes(b"keep existing")
    monkeypatch.setattr(converter, "os", SimpleNamespace(name="posix", link=os.link))
    result = converter.publish_output(temporary, source, tmp_path)
    assert result.name == "source (2).elf"
    assert result.read_bytes() == b"complete ELF"
    assert existing.read_bytes() == b"keep existing"
    assert source.read_bytes() == b"original"
    assert not temporary.exists()


def test_native_ui_smoke_check_runs_event_loop(tmp_path):
    report = tmp_path / "ui.json"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run([sys.executable, "-m", "unfself_ui", "--check-ui", str(report)],
                            env=environment, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    record = json.loads(report.read_text())
    assert record["visible"] and record["width"] >= 860 and record["height"] >= 660
    assert record["platform"]


def test_debian_payload_includes_launcher_icon_and_notices(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from package_posix import stage_debian
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "ps4-unfself-ui").write_bytes(b"synthetic executable")
    (payload / "LICENSE").write_text("license fixture")
    stage = tmp_path / "debian"
    stage_debian(payload, stage)
    assert (stage / "opt/ps4-unfself-ui/ps4-unfself-ui").read_bytes() == b"synthetic executable"
    assert (stage / "opt/ps4-unfself-ui/LICENSE").read_text() == "license fixture"
    assert "Architecture: amd64" in (stage / "DEBIAN/control").read_text()
    assert "Exec=/opt/ps4-unfself-ui/ps4-unfself-ui %F" in (stage / "usr/share/applications/ps4-unfself-ui.desktop").read_text()
    assert (stage / "usr/share/icons/hicolor/256x256/apps/ps4-unfself-ui.png").is_file()
    assert (stage / "usr/share/doc/ps4-unfself-ui/copyright").is_file()


@pytest.mark.parametrize("owned_path", ["original", "resolved", "unknown"])
def test_linux_runtime_license_lookup_resolves_library_symlinks(monkeypatch, owned_path):
    from scripts.collect_linux_licenses import find_library_package

    library = Path("/lib/x86_64-linux-gnu/libX11-xcb.so.1")
    resolved = Path("/usr/lib/x86_64-linux-gnu/libX11-xcb.so.1.0.0")
    owner_path = {"original": str(library), "resolved": str(resolved), "unknown": None}[owned_path]
    monkeypatch.setattr(Path, "resolve", lambda self: resolved)

    def query(command, **kwargs):
        assert command[:2] == ["dpkg-query", "-S"]
        found = command[2] == owner_path
        return SimpleNamespace(returncode=0 if found else 1,
                               stdout=f"libx11-xcb1:amd64: {owner_path}\n" if found else "")

    monkeypatch.setattr(subprocess, "run", query)
    if owned_path == "unknown":
        with pytest.raises(RuntimeError, match="No installed package owns"):
            find_library_package(library)
    else:
        assert find_library_package(library) == "libx11-xcb1:amd64"
