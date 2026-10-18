# Platforms and builds

| Platform | Baseline | Packages | Status |
| --- | --- | --- | --- |
| Windows x64 | Windows 10 1809+ | Setup EXE, portable ZIP | Windows 11 tested; Windows 10 untested |
| macOS arm64 / x64 | macOS 13+ | App ZIP, DMG | Built and tested on macOS 15, both architectures |
| Linux x64 | glibc 2.35+, X11/XWayland; Ubuntu 22.04 | tar.gz, DEB | Built and tested on Ubuntu 22.04 |

Windows setup offers a desktop shortcut. On macOS, extract the ZIP or drag the DMG app to Applications. Builds use an ad-hoc signature without Developer ID/notarization; Gatekeeper may require approval in Privacy & Security.

On Linux, extract the tar.gz and run `./ps4-unfself-ui`, or use:

```sh
sudo apt install ./ps4-unfself-ui-0.1.1-linux-x64.deb
sudo apt remove ps4-unfself-ui
```

Portable Linux users need the dependencies in `scripts/package_posix.py`. Choose an output filesystem with hard-link support; unsupported destinations fail without overwriting files.

## Build

Use Python 3.12 matching the target architecture. Build on each target OS; PyInstaller cannot cross-compile.

Windows needs PowerShell and Inno Setup (tested: 7.1.0):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.venv\Scripts\python.exe -m pip install --no-deps -e .
.venv\Scripts\python.exe -m unfself_ui
powershell -ExecutionPolicy Bypass -File scripts\build.ps1 -IsccPath "C:\Path\To\Inno Setup\ISCC.exe"
.venv\Scripts\python.exe scripts\verify_packages.py
.venv\Scripts\python.exe scripts\verify_release.py
```

macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m unfself_ui
.venv/bin/python scripts/build_posix.py
.venv/bin/python scripts/verify_posix.py
```

Build scripts run pytest and write to `packages/`. Run tests alone with `.venv/Scripts/python.exe -m pytest -q` (POSIX: `.venv/bin/python`).

macOS requires Xcode command-line tools, `codesign`, `ditto` and `hdiutil`. Linux requires `dpkg-deb` and `desktop-file-validate`; see `.github/workflows/build.yml` for desktop dependencies and `xvfb-run`.

Windows package checks install/reinstall/uninstall in `.work/package-check-*/installed` and verify shortcuts/registration. They refuse to alter an existing installation. POSIX checks extract packages; reserve `verify_posix.py --install` for disposable Linux runners because it uses sudo to install and purge.

CI builds/tests Windows x64, Linux x64 and both macOS architectures, then saves artifacts. Publishing needs owner approval; see [checklist](publication.md).

## Headless conversion

```powershell
.venv\Scripts\python.exe -m unfself_ui --convert eboot.bin --output-dir output --report result.json
```

The packaged executable accepts these arguments. Create the output folder first; choose a new report path. For the windowed Windows EXE, wait for completion and read `--report`. Exit `0`: all conversions passed. Exit `1`: at least one failed.
