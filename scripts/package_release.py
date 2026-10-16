import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from unfself_ui import __version__

SOURCE_DIRECTORIES = ("src", "tests", "scripts", "packaging", "assets", "licenses", ".github")
SOURCE_FILES = ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", ".gitignore",
                "pyproject.toml", "requirements-build.txt", "docs/images/app.png", "docs/images/logo.png",
                "docs/release-notes.md", "docs/verification.md", "docs/publication.md", "docs/building.md")


def source_files():
    paths = [ROOT / name for name in SOURCE_FILES]
    for name in SOURCE_DIRECTORIES:
        paths.extend(path for path in (ROOT / name).rglob("*")
                     if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc")
    return sorted(paths)


def hash_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iscc", type=Path, required=True)
    parser.add_argument("--payload", type=Path, default=ROOT / ".work/build/dist/ps4-unfself-ui")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "packages")
    args = parser.parse_args()
    packages = args.output_dir.resolve()
    packages.mkdir(parents=True, exist_ok=True)
    payload = args.payload.resolve()
    if not (payload / "PS4 Unfself UI.exe").exists():
        raise FileNotFoundError("Build the executable first")
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "README.md"):
        shutil.copyfile(ROOT / name, payload / name)
    shutil.copytree(ROOT / "licenses", payload / "licenses", dirs_exist_ok=True)
    (payload / "docs" / "images").mkdir(parents=True, exist_ok=True)
    for name in ("release-notes.md", "verification.md", "publication.md", "building.md"):
        shutil.copyfile(ROOT / "docs" / name, payload / "docs" / name)
    shutil.copyfile(ROOT / "docs" / "images" / "app.png", payload / "docs" / "images" / "app.png")
    shutil.copyfile(ROOT / "docs" / "images" / "logo.png", payload / "docs" / "images" / "logo.png")
    prefix = f"ps4-unfself-ui-{__version__}"
    with zipfile.ZipFile(packages / f"{prefix}-windows-x64-portable.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                archive.write(path, Path("ps4-unfself-ui") / path.relative_to(payload))
    with zipfile.ZipFile(packages / f"{prefix}-source.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in source_files():
            archive.write(path, Path(prefix) / path.relative_to(ROOT))
    subprocess.run([str(args.iscc), "/Q", f"/DAppVersion={__version__}", f"/DPayloadDir={payload}",
                    f"/DOutputDir={packages}", str(ROOT / "packaging" / "installer.iss")], check=True)
    assets = [packages / f"{prefix}-source.zip", packages / f"{prefix}-windows-x64-portable.zip",
              packages / f"{prefix}-windows-x64-setup.exe"]
    (packages / "SHA256SUMS.txt").write_text(
        "".join(f"{hash_file(path)}  {path.name}\n" for path in assets), encoding="utf-8")
    print("Release archives and checksums created")


if __name__ == "__main__":
    main()
