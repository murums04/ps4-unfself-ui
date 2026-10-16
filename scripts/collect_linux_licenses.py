import argparse
import ast
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote


def find_library_package(library):
    for path in (library, library.resolve()):
        found = subprocess.run(["dpkg-query", "-S", str(path)], capture_output=True, text=True)
        if found.returncode == 0:
            return found.stdout.split(": ", 1)[0].splitlines()[0]
    raise RuntimeError(f"No installed package owns bundled library {library}; add its license and provenance before release.")


def collect(toc, destination):
    records = {}
    entries = ast.literal_eval(toc.read_text(encoding="utf-8"))[0]
    for name, source, kind in entries:
        path = Path(source)
        if kind != "BINARY" or any(part in path.parts for part in ("site-packages", "lib-dynload")):
            continue
        if path.name.startswith("libpython"):
            continue
        package = find_library_package(path)
        if package in records:
            continue
        copyright_file = Path("/usr/share/doc") / package.split(":", 1)[0] / "copyright"
        if not copyright_file.is_file():
            raise RuntimeError(f"Missing runtime copyright for {package}")
        version, source_package, source_version = subprocess.check_output(
            ["dpkg-query", "-W", "-f=${Version}\t${source:Package}\t${source:Version}", package], text=True).split("\t")
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(copyright_file, destination / f"{package.replace(':', '-')}.txt")
        records[package] = {"version": version, "source_package": source_package,
                            "source_version": source_version,
                            "source": f"https://launchpad.net/ubuntu/+source/{quote(source_package)}/{quote(source_version)}"}
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "packages.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    common = Path("/usr/share/common-licenses")
    if common.is_dir():
        shutil.copytree(common, destination / "common-licenses", dirs_exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toc", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    collect(args.toc, args.destination)


if __name__ == "__main__":
    main()
