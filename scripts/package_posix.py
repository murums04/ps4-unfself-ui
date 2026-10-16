import argparse
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from package_release import ROOT, hash_file

sys.path.insert(0, str(ROOT / "src"))
from unfself_ui import __version__

LINUX_DEPENDENCIES = (
    "libc6 (>= 2.35), libstdc++6, libgcc-s1, libglib2.0-0, libgl1, libegl1, libopengl0, "
    "libdbus-1-3, libfontconfig1, libfreetype6, libx11-6, libx11-xcb1, libxext6, "
    "libxcb1, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, "
    "libxcb-randr0, libxcb-render0, libxcb-render-util0, libxcb-shape0, libxcb-shm0, "
    "libxcb-sync1, libxcb-xfixes0, libxcb-xinerama0, libxcb-xkb1, libxkbcommon0, libxkbcommon-x11-0"
)


def copy_notices(destination):
    for name in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md"):
        shutil.copyfile(ROOT / name, destination / name)
    shutil.copytree(ROOT / "licenses", destination / "licenses", dirs_exist_ok=True)
    images = destination / "docs/images"
    images.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "docs/images/app.png", images / "app.png")
    for name in ("release-notes.md", "verification.md", "publication.md"):
        shutil.copyfile(ROOT / "docs" / name, destination / "docs" / name)


def stage_debian(payload, destination):
    shutil.copytree(payload, destination / "opt/ps4-unfself-ui", symlinks=True)
    control = destination / "DEBIAN"
    control.mkdir()
    (control / "control").write_text(
        f"Package: ps4-unfself-ui\nVersion: {__version__}\nArchitecture: amd64\n"
        "Maintainer: murums <208348100+murums04@users.noreply.github.com>\n"
        "Section: utils\nPriority: optional\nHomepage: https://github.com/murums04/ps4-unfself-ui\n"
        f"Depends: {LINUX_DEPENDENCIES}\n"
        "Description: Desktop interface for PS4 SELF to ELF reconstruction\n"
        " Converts already fake-signed, unencrypted and uncompressed SELF files locally.\n",
        encoding="utf-8")
    desktop = destination / "usr/share/applications"
    desktop.mkdir(parents=True)
    shutil.copyfile(ROOT / "packaging/ps4-unfself-ui.desktop", desktop / "ps4-unfself-ui.desktop")
    icons = destination / "usr/share/icons/hicolor/256x256/apps"
    icons.mkdir(parents=True)
    shutil.copyfile(ROOT / "assets/icon.png", icons / "ps4-unfself-ui.png")
    documentation = destination / "usr/share/doc/ps4-unfself-ui"
    documentation.mkdir(parents=True)
    shutil.copyfile(ROOT / "LICENSE", documentation / "copyright")


def package_linux(dist, output, workspace):
    payload = dist / "ps4-unfself-ui"
    copy_notices(payload)
    prefix = f"ps4-unfself-ui-{__version__}-linux-x64"
    portable = output / f"{prefix}-portable.tar.gz"
    with tarfile.open(portable, "w:gz") as archive:
        archive.add(payload, arcname="ps4-unfself-ui")
    stage = workspace / "deb"
    stage_debian(payload, stage)
    installer = output / f"{prefix}.deb"
    subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(stage), str(installer)], check=True)
    return [portable, installer], "linux-x64"


def package_macos(dist, output, workspace):
    architecture = platform.machine()
    if architecture not in ("arm64", "x86_64"):
        raise RuntimeError(f"Unsupported macOS architecture: {architecture}")
    target = "macos-" + ("arm64" if architecture == "arm64" else "x64")
    application = dist / "PS4 Unfself UI.app"
    copy_notices(application / "Contents/Resources")
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(application)], check=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(application)], check=True)
    prefix = f"ps4-unfself-ui-{__version__}-{target}"
    portable = output / f"{prefix}-portable.zip"
    subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(application), str(portable)], check=True)
    image_root = workspace / "dmg"
    image_root.mkdir()
    shutil.copytree(application, image_root / application.name, symlinks=True)
    (image_root / "Applications").symlink_to("/Applications", target_is_directory=True)
    image = output / f"{prefix}.dmg"
    subprocess.run(["hdiutil", "create", "-volname", "PS4 Unfself UI", "-srcfolder", str(image_root),
                    "-ov", "-format", "UDZO", str(image)], check=True)
    return [portable, image], target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform not in ("linux", "darwin"):
        parser.error("Native packaging requires Linux or macOS.")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="package-", dir=args.work_dir.resolve()) as directory:
        package = package_macos if sys.platform == "darwin" else package_linux
        assets, target = package(args.dist_dir.resolve(), output, Path(directory))
    (output / f"SHA256SUMS-{target}.txt").write_text(
        "".join(f"{hash_file(path)}  {path.name}\n" for path in assets), encoding="utf-8")
    print(f"NATIVE_PACKAGES_CREATED: {target}")


if __name__ == "__main__":
    main()
