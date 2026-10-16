# Verification record

Date: 2026-10-16. Platform: Windows 11 Pro x64, build 26300. Python 3.12.14; PySide6 6.10.3.

- 104 automated tests pass on Windows for conversion, real Qt event-loop workflows, updates and platform packaging preparation. They include both SELF length conventions for library-version trailers, one-to-fifteen-byte truncation rejection, actual drop events and keyboard activation, POSIX publication through hard links, Debian staging and a UI event-loop subprocess check.
- Update checks cover numeric versions, platform-specific assets, draft/prerelease exclusion, exact GitHub URL validation, invalid/oversized JSON, missing releases, rate limiting, server errors, retries and a responsive event loop during timeouts. About tests verify both GitHub links, browser-only download/release actions and browser failure feedback.
- The packaged Windows GUI was visually inspected with its matching native title bars and revised About layout. Its real HTTPS startup request reached GitHub and displayed the expected no-public-release status. Future-release downloads were tested with controlled responses; no future public release exists to download yet.
- Normal 1020 × 780 and minimum 860 × 660 windows were rendered and visually inspected, including expanded error/details view at 100% and 150% scaling.
- A user-provided 93,825,704-byte SELF was tested at two paths with identical content. Both conversions produced a 93,667,640-byte ELF matching an existing reference byte-for-byte, including its 2,088-byte library-version trailer.
- The final packaged executable also reconstructed that input exactly with the development Python removed from PATH.
- Two encrypted module files were rejected explicitly; an existing ELF was recognized as already converted.
- SHA-256 before/after checks confirmed that all five inspected input files were unchanged. No game files or extracted data are included in the repository or downloads.
- The equal-sized-segment regression fixture exposes incorrect size-only mapping in upstream; the indexed implementation produces the independently specified ELF.

- Portable and installed executables launch their GUI, reconstruct the expected fixture and reject invalid input with the development Python removed from PATH.
- Per-user installation, same-version reinstallation and uninstall pass. The Start menu shortcut and uninstall registration are verified and removed on uninstall. A previous-release-to-new-release upgrade is not applicable to this first release.
- An independent code review found a short-trailer truncation bug, which was reproduced, fixed and covered by regression tests. Package verification also caught an unrelated ICU DLL being collected from the build machine's PATH; the build now uses a restricted PATH.

Package tests are rerun against the final artifacts. SHA256SUMS.txt identifies the reviewed downloads. All checks are local; no claim is made that CI has run remotely.

Limitations: no console/emulator launch test, no broad game compatibility claim, no separate Windows 10 machine test, and no code signing certificate. GitHub Actions has not run because publication is not yet authorized.

## Native platform release gates

macOS and Linux support has been added to the shared application and packaging. No native macOS/Linux binaries have been produced or tested on this Windows host; WSL/Docker are unavailable and no Mac is connected. Do not describe the prepared CI jobs as passing builds.

- Linux x64: Ubuntu 22.04 runner; full suite, portable tar.gz, Debian payload, native XCB UI event loop under Xvfb, exact conversion, installation/reinstallation/removal and runtime license collection.
- macOS arm64 and x64: separate native runners; full suite, `.app` ZIP and DMG, architecture/signature checks, copying from the mounted DMG, native Cocoa event loop and exact conversion.
- Windows x64: the existing build and package verification remain required after shared code changes.

An independent review of the platform changes found no Critical or Important issue; its shared test run passed 74 tests on Windows. Native execution and visual inspection on macOS/Linux remain pending. The macOS bundles are ad-hoc signed and not notarized.

The subsequent About/update-check review found no Critical or Important issue and independently passed all 104 current tests. QtNetwork and native TLS plugins are included in the new package specifications; their macOS/Linux execution remains part of the native release gates.
