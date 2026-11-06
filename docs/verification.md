# Verification

## 0.1.2 local checks

2026-11-06 · macOS arm64 · Python 3.12.

- 143 tests passed, including report failures, exclusive-copy cleanup, output paths, literal filenames and queue state.
- Five checks on an exFAT disk image passed: Unicode, existing outputs, `.elf` inputs, cancellation during copying and a full volume. Inputs and existing results remained unchanged; partial outputs were removed.
- ZIP and DMG passed exact conversion, invalid-input rejection, native Cocoa startup, version, architecture, signature and checksum checks.
- Manual packaged UI checks passed: About, file selection, literal filenames, conversion into a folder with a trailing space, details and queue reset. Output matched the fixture; the input remained unchanged.

On filesystems without hard links, a forced process exit during the final copy can leave a partial output.

## Earlier Windows checks

2026-10-16 · Windows 11 Pro x64, build 26300 · Python 3.12.14 · PySide6 6.10.3.

- **113 tests:** exact reconstruction, equal-sized/reordered segments, both library-trailer length conventions, 1–15-byte truncations, Unicode paths, collisions/cancellation; Qt drop/keyboard/batch workflows; POSIX hard links, Debian staging, Linux library provenance and GUI startup.
- **Updates:** versions/platforms, exact GitHub URLs, drafts/prereleases, invalid/oversized JSON, HTTP errors/rate limits, responsive timeouts and retries; About links and browser failures. Mouse/keyboard checks retain focus and ignore duplicate requests without opening links. Packaged HTTPS returned “no public release”; future downloads use controlled responses.
- **UI:** 1020 × 780 and minimum 860 × 660, details/errors at 100%/150%; packaged title bars and About inspected.
- **Packages:** GUI/conversion without development Python on PATH, invalid-input rejection, per-user install/reinstall/uninstall and shortcut/registry cleanup.
- **Review:** fixed trailer truncation, an ICU DLL collected from PATH and the About focus jump. The earlier independent platform/update reviews covered 104 tests; the current suite includes six focus regressions.

## Real input

Two copies of one 93,825,704-byte SELF produced a 93,667,640-byte ELF matching the user's reference, including its 2,088-byte trailer. The packaged EXE matched too. Two encrypted modules failed as expected; an ELF input needed no conversion. Before/after hashes matched for all five inputs. No game data enters the release.

The comparison verifies reconstruction of these inputs. Windows binaries are unsigned. SHA256SUMS.txt identifies checked packages.

## Format limits

- Stripped ELF64, little-endian x86-64; validate headers, not extensions (`.self`, `.bin`, `.sprx`, `.elf`).
- Reject encryption, compression, section tables, invalid bounds/indexes, overlaps/conflicts and missing SELF data. No key retrieval or PKG extraction.
- Map segments by index, not size; stream into new outputs. Cap size at 4 GiB and `max(64 MiB, 16 × input size)`.
- No signature/digest authentication, telemetry, uploads, persistent settings or file associations.

Baseline: upstream `794ed5460ea6d82def0ed661d05d8171fa09ce1b`; format cross-check: [OpenOrbis create-fself](https://github.com/OpenOrbis/create-fself), crediting flatz.

## Native packages

GitHub Actions builds and tests Windows x64, Linux x64 and macOS arm64 on native runners. See [build results](https://github.com/murums04/ps4-unfself-ui/actions/workflows/build.yml).

- Linux x64/Ubuntu 22.04: suite, tar.gz/DEB, XCB under Xvfb, exact conversion, input preservation, invalid-file rejection, install/reinstall/purge and runtime licenses.
- macOS arm64 on macOS 15: suite, app ZIP/DMG, architecture/ad-hoc signature, DMG copy, Cocoa GUI, exact conversion, input preservation and invalid-file rejection. No notarization.

All three jobs must pass on the final release commit. Minimum OS versions describe build baselines.
