# Verification

2026-10-16 · Windows 11 Pro x64, build 26300 · Python 3.12.14 · PySide6 6.10.3.

## Passed

- **110 tests:** exact reconstruction, equal-sized/reordered segments, both library-trailer length conventions, 1–15-byte truncations, Unicode paths, collisions/cancellation; Qt drop/keyboard/batch workflows; POSIX hard links, Debian staging and GUI startup.
- **Updates:** versions/platforms, exact GitHub URLs, drafts/prereleases, invalid/oversized JSON, HTTP errors/rate limits, responsive timeouts and retries; About links and browser failures. Mouse/keyboard checks retain focus and ignore duplicate requests without opening links. Packaged HTTPS returned “no public release”; future downloads use controlled responses.
- **UI:** 1020 × 780 and minimum 860 × 660, details/errors at 100%/150%; packaged title bars and About inspected.
- **Packages:** GUI/conversion without development Python on PATH, invalid-input rejection, per-user install/reinstall/uninstall and shortcut/registry cleanup. No prior release for a cross-version upgrade test.
- **Review:** fixed trailer truncation, an ICU DLL collected from PATH and the About focus jump. The earlier independent platform/update reviews covered 104 tests; the current suite includes six focus regressions.

## Real input

Two copies of one 93,825,704-byte SELF produced a 93,667,640-byte ELF matching the user's reference, including its 2,088-byte trailer. The packaged EXE matched too. Two encrypted modules failed as expected; an ELF input needed no conversion. Before/after hashes matched for all five inputs. No game data enters the release.

This proves reconstruction, not broad compatibility or console/emulator execution. Windows 10 remains untested; Windows binaries are unsigned. SHA256SUMS.txt identifies checked packages.

## Format limits

- Stripped ELF64, little-endian x86-64; validate headers, not extensions (`.self`, `.bin`, `.sprx`, `.elf`).
- Reject encryption, compression, section tables, invalid bounds/indexes, overlaps/conflicts and missing SELF data. No key retrieval or PKG extraction.
- Map segments by index, not size; stream into new outputs. Cap size at 4 GiB and `max(64 MiB, 16 × input size)`.
- No signature/digest authentication, telemetry, uploads, persistent settings or file associations.

Baseline: upstream `794ed5460ea6d82def0ed661d05d8171fa09ce1b`; format cross-check: [OpenOrbis create-fself](https://github.com/OpenOrbis/create-fself), crediting flatz.

## Pending

No macOS/Linux binaries or remote CI results yet; no WSL/Docker or Mac on this host.

- Linux x64/Ubuntu 22.04: suite, tar.gz/DEB, XCB under Xvfb, conversion, install/reinstall/purge, licenses and TLS.
- macOS arm64/x64: suite, app ZIP/DMG, architecture/ad-hoc signature, DMG copy, Cocoa GUI, conversion and TLS. No notarization.

Recheck Windows after shared changes. Publish native artifacts after their checks pass, with owner approval.
