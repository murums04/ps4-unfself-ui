# Publication checklist

Proposed destination: **murums04/ps4-unfself-ui**, a new independent **public** repository. Verify the authenticated login and repository owner immediately before publication. The product identity is **murums**.

## Repository contents

- `src/`: converter, Qt worker, UI and entry point.
- `tests/`: synthetic fixtures and regression/workflow tests only.
- `scripts/`, `packaging/`, `requirements-build.txt`, `pyproject.toml`: reproducible build and verification inputs.
- `assets/`: project SVG/ICO; `licenses/`: runtime license and attribution texts.
- `.github/workflows/build.yml`: Windows build/tests and workflow artifacts; no automatic release publication.
- README with screenshot and instructions, GPL-3.0 LICENSE, third-party notices, changelog, release notes and verification record.

Exclude local virtual environments, build tools, temporary data, personal inputs, game files, test outputs, machine-specific records and binary packages from Git history.

## GitHub presentation

- Name: `ps4-unfself-ui`
- Description: `Windows GUI for ps4_unfself: convert fake-signed PS4 SELF files to ELF. Portable app and installer.`
- Topics: `ps4`, `playstation-4`, `self`, `elf`, `gui`, `windows`, `python`, `pyside6`
- Initial release tag: `v0.1.0`
- Release title: `PS4 Unfself UI 0.1.0`
- Release body: `docs/release-notes.md`
- Assets: installer EXE, portable ZIP, corresponding source ZIP, `SHA256SUMS.txt`.

The README prominently credits and links the original project. A link from the upstream README can be proposed later, with a separately approved contribution; upstream acceptance is not guaranteed.

## Owner review before upload

Present the rendered application, exact destination/visibility, source inclusion list, asset sizes/hashes, executed checks and remaining limitations. Wait for explicit approval before creating the repository, pushing, publishing a release, or contacting upstream.

Current state: local preparation only. Nothing has been published by this task.
