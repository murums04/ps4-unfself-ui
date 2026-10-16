# <img src="docs/images/logo.png" alt="" width="64" height="64" align="middle"> &nbsp; murums PS4 Unfself UI

**Download:** [Windows](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-windows-x64-setup.exe) · [macOS (Apple Silicon)](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-macos-arm64.dmg) · [macOS (Intel)](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-macos-x64.dmg) · [Linux](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-linux-x64.deb)

[All downloads](https://github.com/murums04/ps4-unfself-ui/releases/latest) · [Report a bug](https://github.com/murums04/ps4-unfself-ui/issues)

Convert fake-signed PS4 SELF files to ELF. Requires **unencrypted, uncompressed** files; no retail decryption or PKG extraction.

Community GUI by **murums**, based on [ps4_unfself by SocraticBliss](https://github.com/SocraticBliss/ps4_unfself). Research: Znullptr, flatz and zecoxao.

![PS4 Unfself UI](docs/images/app.png)

## Download

**Version 0.1.0** · [SHA-256 checksums](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/SHA256SUMS.txt)

| Platform | Installer | Portable |
| --- | --- | --- |
| Windows x64 | [Setup EXE](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-windows-x64-setup.exe) | [ZIP](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-windows-x64-portable.zip) |
| macOS · Apple Silicon | [DMG](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-macos-arm64.dmg) | [ZIP](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-macos-arm64-portable.zip) |
| macOS · Intel | [DMG](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-macos-x64.dmg) | [ZIP](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-macos-x64-portable.zip) |
| Linux x64 | [DEB](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-linux-x64.deb) | [tar.gz](https://github.com/murums04/ps4-unfself-ui/releases/latest/download/ps4-unfself-ui-0.1.0-linux-x64-portable.tar.gz) |

Choose an installer for normal use. All packages include Python and Qt. GitHub's **Code → Download ZIP** contains source code.

- **Windows:** run Setup for a per-user installation, shortcuts and uninstaller. For portable use, extract the whole ZIP and run `PS4 Unfself UI.exe`; keep `_internal` beside it.
- **macOS:** open the DMG and drag the app to Applications, or extract the ZIP. The app is not notarized; macOS may require approval in Privacy & Security.
- **Linux:** install the DEB, or extract the tar.gz and run `./ps4-unfself-ui`.

Windows executables are unsigned. See [supported systems and installation details](docs/building.md).

## Use

1. Drop files or select **Add files**.
2. Choose an **Output folder**; it defaults to the first input's folder.
3. Select **Convert to ELF**, then **Open output folder**. Use **Show details** for errors and paths.

Inputs stay read-only. Existing outputs get numbered alternatives: `eboot.elf`, `eboot (2).elf`. **Convert again** creates another copy. Cancel or close to discard the current partial file and keep completed results. Failed files do not stop the queue.

## Updates & privacy

The app checks GitHub on launch; retry through **About → Check now**. Download the matching portable archive in your browser and extract it to a new folder; choose **View release** for installers. Install updates yourself.

The anonymous HTTPS check sends connection metadata, not your file names or contents. No telemetry or uploads. Headless conversion makes no update requests.

## Details

Supports stripped ELF64, little-endian x86-64 layouts. See [format limits and test coverage](docs/verification.md), [build/CLI instructions](docs/building.md) and [release notes](docs/release-notes.md).

**GPL-3.0.** Keep [LICENSE](LICENSE), [third-party notices](THIRD_PARTY_NOTICES.md) and corresponding source when redistributing. Dependency licenses are in `licenses/`.

<sub><a href="https://ko-fi.com/murums">Ko-fi</a></sub>

