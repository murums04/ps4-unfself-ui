# murums PS4 Unfself UI 0.1.0

First release candidate of a desktop interface based on SocraticBliss' ps4_unfself.

- Add files by drag-and-drop and convert multiple files in one run.
- Choose an output folder; original files and existing results are preserved.
- See progress and per-file errors, cancel safely, and open the output folder.
- Choose a per-user installer or portable ZIP. No separate Python installation is needed.
- Native packaging is prepared for macOS Apple Silicon/Intel (`.app` ZIP and DMG) and Linux x64 (portable tar.gz and `.deb`). These artifacts must pass their native CI checks before publication; they have not been built locally.

Requires Windows x64. Windows 11 tested; Windows 10 1809+ is the dependency baseline, not separately tested. Only unencrypted, uncompressed fake-signed SELF files with supported stripped ELF64 layouts are accepted. This is not a retail decryption tool. A user-supplied SELF matched its existing ELF reference byte-for-byte; broader compatibility is not guaranteed. Binaries are unsigned.

Locally verified downloads: Windows setup EXE, portable ZIP, corresponding source ZIP and SHA256SUMS.txt. Native platform downloads and their separate checksum manifests are added only after successful native verification. All source and credits are included under GPL-3.0 with third-party runtime notices.
