import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Build on the target Linux or macOS host.")
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".work/native-build")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "packages")
    args = parser.parse_args()
    if sys.platform not in ("linux", "darwin"):
        parser.error("Run this script on Linux or macOS; cross-compilation is not supported.")
    if sys.platform == "linux" and platform.machine() not in ("x86_64", "AMD64"):
        parser.error("The Linux package currently targets x64.")
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["PYINSTALLER_CONFIG_DIR"] = str(work / "cache")
    environment.pop("PYTHONPATH", None)
    commands = [
        [sys.executable, "-m", "pytest", "-q", f"--basetemp={work / 'pytest'}"],
        [sys.executable, "scripts/prepare_assets.py"],
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
         "--distpath", str(work / "dist"), "--workpath", str(work / "pyinstaller"), "packaging/posix.spec"],
    ]
    if sys.platform == "linux":
        commands.append([sys.executable, "scripts/collect_linux_licenses.py", "--toc",
                         str(work / "pyinstaller/posix/COLLECT-00.toc"), "--destination",
                         str(work / "dist/ps4-unfself-ui/licenses/Linux-runtime")])
    commands.append([sys.executable, "scripts/package_posix.py", "--dist-dir", str(work / "dist"),
                     "--work-dir", str(work / "packaging"), "--output-dir", str(args.output_dir.resolve())])
    for command in commands:
        subprocess.run(command, cwd=ROOT, env=environment, check=True)
    print("NATIVE_BUILD_SUCCEEDED")


if __name__ == "__main__":
    main()
