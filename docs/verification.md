# Verification record

Date: 2026-10-16. Platform: Windows 11 Pro x64, build 26300. Python 3.12.14; PySide6 6.10.3.

- 71 automated tests pass for conversion and real Qt event-loop workflows. They include both SELF length conventions for library-version trailers, one-to-fifteen-byte truncation rejection, actual drop events and keyboard activation.
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
