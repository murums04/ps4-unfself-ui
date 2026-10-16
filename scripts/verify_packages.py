import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import winreg
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from tests.fixtures import write_fixture
from unfself_ui import __version__

APP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{9C1623D7-1B18-4F87-A62C-F6A88C16B4B5}_is1"


def installed():
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive, APP_KEY, 0, winreg.KEY_READ | view):
                    return True
            except FileNotFoundError:
                pass
    return False


def wait_until(condition, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.1)
    raise AssertionError("Timed out while waiting for the packaged application")


def verify_executable(executable, workspace, tag):
    environment = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM", "QT_QPA_PLATFORM_PLUGIN_PATH"):
        environment.pop(key, None)
    environment["PATH"] = os.path.join(os.environ["SystemRoot"], "System32")
    folder = workspace / f"{tag}-check"
    folder.mkdir()
    source, expected = write_fixture(folder, "Prüfung 日本.self", reverse=True)
    original = source.read_bytes()
    report = folder / "result.json"
    result = subprocess.run([str(executable), "--convert", str(source), "--output-dir", str(folder),
                             "--report", str(report)], cwd=folder, env=environment, timeout=60)
    assert result.returncode == 0, f"{tag} conversion failed: {result.returncode}"
    records = json.loads(report.read_text(encoding="utf-8"))
    assert records[0]["status"] == "converted"
    assert Path(records[0]["output"]).read_bytes() == expected
    assert source.read_bytes() == original
    bad = folder / "invalid.self"
    bad.write_bytes(b"invalid")
    invalid_report = folder / "invalid.json"
    result = subprocess.run([str(executable), "--convert", str(bad), "--output-dir", str(folder),
                             "--report", str(invalid_report)], cwd=folder, env=environment, timeout=60)
    assert result.returncode == 1
    assert json.loads(invalid_report.read_text())[0]["status"] == "failed"
    assert not (folder / "invalid.elf").exists()
    ui_report = folder / "ui.json"
    subprocess.run([str(executable), "--check-ui", str(ui_report)], cwd=folder,
                   env=environment, check=True, timeout=60)
    ui = json.loads(ui_report.read_text())
    assert ui["visible"] and ui["platform"] == "windows"
    assert ui["width"] >= 860 and ui["height"] >= 660
    print(f"{tag}: GUI and exact conversion verified without development PATH", flush=True)


def main():
    if installed():
        raise RuntimeError("An existing PS4 Unfself UI installation was found. Refusing to alter it.")
    work_root = ROOT / ".work"
    work_root.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="package-check-", dir=work_root)).resolve()
    assert workspace.is_relative_to(work_root.resolve())
    group_name = "murums PS4 Unfself UI"
    shortcut_dir = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs" / group_name
    if shortcut_dir.exists():
        raise RuntimeError("The verification shortcut folder already exists; refusing to replace it.")
    install_dir = workspace / "installed"
    uninstaller = install_dir / "unins000.exe"
    success = False
    try:
        prefix = f"ps4-unfself-ui-{__version__}-windows-x64"
        with zipfile.ZipFile(ROOT / "packages" / f"{prefix}-portable.zip") as archive:
            for name in archive.namelist():
                target = (workspace / "portable" / name).resolve()
                assert target.is_relative_to(workspace / "portable")
            archive.extractall(workspace / "portable")
        executable = workspace / "portable/ps4-unfself-ui/PS4 Unfself UI.exe"
        verify_executable(executable, workspace, "portable")
        setup = ROOT / "packages" / f"{prefix}-setup.exe"
        command = [str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LANG=english",
                   f"/DIR={install_dir}", "/TASKS=", f"/LOG={workspace / 'setup.log'}"]
        subprocess.run(command, check=True, timeout=120)
        assert installed()
        assert (shortcut_dir / "PS4 Unfself UI.lnk").is_file()
        verify_executable(install_dir / "PS4 Unfself UI.exe", workspace, "installed")
        subprocess.run(command, check=True, timeout=120)
        verify_executable(install_dir / "PS4 Unfself UI.exe", workspace, "upgraded")
        success = True
    finally:
        if uninstaller.exists():
            subprocess.run([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                           check=True, timeout=120)
            wait_until(lambda: not installed() and not shortcut_dir.exists() and not uninstaller.exists())
        if success:
            assert not installed()
            assert not shortcut_dir.exists()
            assert not (install_dir / "PS4 Unfself UI.exe").exists()
            shutil.rmtree(workspace)
        else:
            print(f"Failure evidence retained at {workspace}")
    print("PACKAGE_VERIFICATION_PASSED")


if __name__ == "__main__":
    main()

