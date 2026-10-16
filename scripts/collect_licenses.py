"""Refresh unmodified dependency notices from their pinned upstream sources."""

import importlib.metadata
import json
import posixpath
import shutil
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "licenses"
VERSION = "v6.10.3"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ps4-unfself-ui-license-collector"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def collect_repository(repository):
    tree_url = f"https://api.github.com/repos/{repository}/git/trees/{VERSION}?recursive=1"
    tree = json.loads(fetch(tree_url))["tree"]
    files = {item["path"] for item in tree if item["type"] == "blob"}
    notices = sorted(path for path in files if path.endswith("qt_attribution.json"))
    licenses = {path for path in files if path.startswith("LICENSES/")}
    base_url = f"https://raw.githubusercontent.com/{repository}/{VERSION}/"
    destination = DESTINATION / "Qt" / repository.split("/")[1]

    def save(path):
        content = fetch(base_url + path)
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return path, content

    with ThreadPoolExecutor(max_workers=8) as pool:
        for path, content in pool.map(save, notices):
            records = json.loads(content, strict=False)
            for record in records if isinstance(records, list) else [records]:
                license_files = record.get("LicenseFile", [])
                if isinstance(license_files, str):
                    license_files = [license_files]
                for license_file in license_files:
                    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), license_file))
                    if resolved not in files:
                        raise ValueError(f"Missing referenced license: {repository}/{resolved}")
                    licenses.add(resolved)
        list(pool.map(save, sorted(licenses)))
    return len(notices) + len(licenses)


def main():
    DESTINATION.mkdir(exist_ok=True)
    shutil.copyfile(Path(sys.base_prefix) / "LICENSE.txt", DESTINATION / "Python.txt")
    distribution = importlib.metadata.distribution("pyinstaller")
    notice = next(file for file in distribution.files if str(file).endswith("licenses/COPYING.txt"))
    shutil.copyfile(distribution.locate_file(notice), DESTINATION / "PyInstaller.txt")
    compiler_license = ROOT / ".tools" / "InnoSetup" / "License.txt"
    if compiler_license.exists():
        shutil.copyfile(compiler_license, DESTINATION / "InnoSetup.txt")
    for repository in ("qt/qtbase", "qt/qtsvg", "pyside/pyside-setup"):
        print(repository, collect_repository(repository), "notice files", flush=True)


if __name__ == "__main__":
    main()

