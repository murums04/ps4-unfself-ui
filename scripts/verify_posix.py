import argparse
import json
import os
import platform
import plistlib
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from package_release import ROOT, hash_file

sys.path.insert(0, str(ROOT))
from tests.fixtures import write_fixture
from unfself_ui import __version__


def verify_runtime_contents(folder):
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "licenses/Python.txt"):
        assert (folder / name).is_file(), f"Missing license: {name}"
    for name in ("README.md", "CHANGELOG.md", "docs", "tests", "scripts"):
        assert not (folder / name).exists(), f"Unexpected development file: {name}"


def verify_application(executable, folder, tag):
    folder.mkdir()
    source, expected = write_fixture(folder, "Prüfung 日本.self", reverse=True, version_tail=b"library versions")
    original = source.read_bytes()
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"):
        environment.pop(name, None)
    environment["PATH"] = "/usr/bin:/bin"
    environment["QT_QPA_PLATFORM"] = "cocoa" if sys.platform == "darwin" else "xcb"
    report = folder / "result.json"
    subprocess.run([str(executable), "--convert", str(source), "--output-dir", str(folder),
                    "--report", str(report)], env=environment, check=True, timeout=60)
    record = json.loads(report.read_text())[0]
    assert record["status"] == "converted"
    assert Path(record["output"]).read_bytes() == expected
    assert source.read_bytes() == original
    invalid = folder / "invalid.self"
    invalid.write_bytes(b"invalid")
    result = subprocess.run([str(executable), "--convert", str(invalid), "--output-dir", str(folder),
                             "--report", str(folder / "invalid.json")], env=environment, timeout=60)
    assert result.returncode == 1 and not (folder / "invalid.elf").exists()
    ui_report = folder / "ui.json"
    subprocess.run([str(executable), "--check-ui", str(ui_report)], env=environment, check=True, timeout=60)
    ui = json.loads(ui_report.read_text())
    assert ui["visible"] and ui["platform"] == environment["QT_QPA_PLATFORM"]
    assert ui["width"] >= 860 and ui["height"] >= 660
    print(f"{tag}: exact conversion, input preservation, rejection and native Qt event loop passed")


def verify_linux(packages, workspace, install):
    prefix = f"ps4-unfself-ui-{__version__}-linux-x64"
    portable = workspace / "portable"
    portable.mkdir()
    with tarfile.open(packages / f"{prefix}-portable.tar.gz") as archive:
        archive.extractall(portable, filter="data")
    executable = portable / "ps4-unfself-ui/ps4-unfself-ui"
    assert os.access(executable, os.X_OK)
    verify_runtime_contents(portable / "ps4-unfself-ui")
    verify_application(executable, workspace / "portable-check", "portable")
    installer = packages / f"{prefix}.deb"
    extracted = workspace / "debian"
    subprocess.run(["dpkg-deb", "-x", str(installer), str(extracted)], check=True)
    verify_runtime_contents(extracted / "opt/ps4-unfself-ui")
    desktop = extracted / "usr/share/applications/ps4-unfself-ui.desktop"
    subprocess.run(["desktop-file-validate", str(desktop)], check=True)
    verify_application(extracted / "opt/ps4-unfself-ui/ps4-unfself-ui", workspace / "debian-check", "Debian payload")
    if install:
        status = subprocess.run(["dpkg-query", "-W", "-f=${Status}", "ps4-unfself-ui"], capture_output=True, text=True)
        if status.returncode == 0 and "installed" in status.stdout:
            raise RuntimeError("An existing installation was found; refusing to replace it.")
        if Path("/opt/ps4-unfself-ui").exists():
            raise RuntimeError("An existing application folder was found; refusing to replace it.")
        try:
            subprocess.run(["sudo", "apt-get", "install", "-y", str(installer)], check=True)
            verify_application(Path("/opt/ps4-unfself-ui/ps4-unfself-ui"), workspace / "installed-check", "installed")
            subprocess.run(["sudo", "dpkg", "-i", str(installer)], check=True)
            verify_application(Path("/opt/ps4-unfself-ui/ps4-unfself-ui"), workspace / "reinstall-check", "reinstalled")
        finally:
            subprocess.run(["sudo", "apt-get", "purge", "-y", "ps4-unfself-ui"], check=True)
        assert not Path("/opt/ps4-unfself-ui").exists()
        assert not Path("/usr/share/applications/ps4-unfself-ui.desktop").exists()


def verify_macos(packages, workspace, target):
    prefix = f"ps4-unfself-ui-{__version__}-{target}"
    portable = workspace / "portable"
    subprocess.run(["ditto", "-x", "-k", str(packages / f"{prefix}-portable.zip"), str(portable)], check=True)
    application = portable / "PS4 Unfself UI.app"
    verify_runtime_contents(application / "Contents/Resources")
    with (application / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    assert info["LSMinimumSystemVersion"] == "13.0"
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(application)], check=True)
    executable = application / "Contents/MacOS/ps4-unfself-ui"
    expected_arch = "arm64" if target.endswith("arm64") else "x86_64"
    assert subprocess.check_output(["lipo", "-archs", str(executable)], text=True).strip() == expected_arch
    verify_application(executable, workspace / "portable-check", "application ZIP")
    mount = workspace / "mounted"
    subprocess.run(["hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", str(mount),
                    str(packages / f"{prefix}.dmg")], check=True)
    try:
        assert (mount / "Applications").is_symlink()
        installed = workspace / "Applications/PS4 Unfself UI.app"
        subprocess.run(["ditto", str(mount / "PS4 Unfself UI.app"), str(installed)], check=True)
        verify_runtime_contents(installed / "Contents/Resources")
        subprocess.run(["codesign", "--verify", "--deep", "--strict", str(installed)], check=True)
        verify_application(installed / "Contents/MacOS/ps4-unfself-ui", workspace / "dmg-check", "DMG application copy")
    finally:
        subprocess.run(["hdiutil", "detach", str(mount)], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packages", type=Path, default=ROOT / "packages")
    parser.add_argument("--install", action="store_true", help="Test system install/reinstall/removal on a disposable Linux runner")
    args = parser.parse_args()
    if sys.platform not in ("linux", "darwin"):
        parser.error("Run on the native Linux or macOS host.")
    target = "linux-x64" if sys.platform == "linux" else "macos-" + ("arm64" if platform.machine() == "arm64" else "x64")
    packages = args.packages.resolve()
    manifest = packages / f"SHA256SUMS-{target}.txt"
    expected_suffixes = ("-portable.tar.gz", ".deb") if target == "linux-x64" else ("-portable.zip", ".dmg")
    expected = {f"ps4-unfself-ui-{__version__}-{target}{suffix}" for suffix in expected_suffixes}
    checked = set()
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert name in expected and hash_file(packages / name) == digest
        checked.add(name)
    assert checked == expected
    work = ROOT / ".work/native-verification"
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="check-", dir=work) as directory:
        workspace = Path(directory)
        if sys.platform == "linux":
            verify_linux(packages, workspace, args.install)
        else:
            verify_macos(packages, workspace, target)
    print(f"NATIVE_PACKAGE_VERIFICATION_PASSED: {target}")


if __name__ == "__main__":
    main()
