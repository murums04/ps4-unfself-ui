import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from unfself_ui import __version__
from package_release import source_files


def main():
    packages = ROOT / "packages"
    prefix = f"ps4-unfself-ui-{__version__}"
    expected_assets = {f"{prefix}-source.zip", f"{prefix}-windows-x64-portable.zip", f"{prefix}-windows-x64-setup.exe"}
    hashes = {}
    for line in (packages / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert name in expected_assets, f"Unexpected release asset: {name}"
        with (packages / name).open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == digest, f"Checksum mismatch: {name}"
        hashes[name] = digest
    assert set(hashes) == expected_assets
    with zipfile.ZipFile(packages / f"{prefix}-source.zip") as archive:
        expected_paths = {f"{prefix}/{path.relative_to(ROOT).as_posix()}": path for path in source_files()}
        assert set(archive.namelist()) == set(expected_paths), "Source archive contains unexpected or missing files"
        for name, path in expected_paths.items():
            assert archive.read(name) == path.read_bytes(), f"Stale source file: {name}"
    with zipfile.ZipFile(packages / f"{prefix}-windows-x64-portable.zip") as archive:
        names = set(archive.namelist())
        for required in ("PS4 Unfself UI.exe", "LICENSE", "THIRD_PARTY_NOTICES.md", "licenses/Python.txt",
                         "licenses/Qt/qtbase/LICENSES/LGPL-3.0-only.txt", "_internal/python312.dll",
                         "_internal/PySide6/Qt6Core.dll", "_internal/PySide6/plugins/platforms/qwindows.dll"):
            assert f"ps4-unfself-ui/{required}" in names, f"Missing runtime file: {required}"
        assert not any(name.lower().endswith((".self", ".elf", ".sprx", ".log")) for name in names)
        for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "README.md"):
            assert archive.read(f"ps4-unfself-ui/{name}") == (ROOT / name).read_bytes()
    for name in sorted(expected_assets):
        print(f"{name}: {(packages / name).stat().st_size:,} bytes")
    print("RELEASE_VERIFICATION_PASSED")


if __name__ == "__main__":
    main()

