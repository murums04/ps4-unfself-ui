# Publication checklist

Proposed destination: **murums04/ps4-unfself-ui**, a new independent **public** repository. Verify the authenticated login and repository owner immediately before publication. The product identity is **murums**.

## Repository contents

- `src/`: converter, Qt worker, UI and entry point.
- `tests/`: synthetic fixtures and regression/workflow tests only.
- `scripts/`, `packaging/`, `requirements-build.txt`, `pyproject.toml`: reproducible build and verification inputs.
- `assets/`: project SVG/ICO/PNG/ICNS and the attributed official GitHub link icon; `licenses/`: runtime license and attribution texts.
- `.github/workflows/build.yml`: Windows x64, Linux x64 and macOS arm64/x64 build/tests and workflow artifacts; no automatic release publication.
- README with screenshot and instructions, GPL-3.0 LICENSE, third-party notices, changelog, release notes and verification record.

Exclude local virtual environments, build tools, temporary data, personal inputs, game files, test outputs, machine-specific records and binary packages from Git history.

## GitHub presentation

- Name: `ps4-unfself-ui`
- Description: `Desktop GUI for ps4_unfself: convert fake-signed PS4 SELF files to ELF. Windows, macOS and Linux builds.`
- Topics: `ps4`, `playstation-4`, `self`, `elf`, `gui`, `windows`, `macos`, `linux`, `python`, `pyside6`
- Initial release tag: `v0.1.0`
- Release title: `PS4 Unfself UI 0.1.0`
- Release body: `docs/release-notes.md`
- Verified local assets: Windows installer EXE, portable ZIP, corresponding source ZIP, `SHA256SUMS.txt`.
- Pending native assets: Linux x64 tar.gz and `.deb`; macOS arm64/x64 `.app` ZIPs and DMGs; platform-specific SHA256SUMS files. These files do not exist locally yet.

The README prominently credits and links the original project. A link from the upstream README can be proposed later, with a separately approved contribution; upstream acceptance is not guaranteed.

The update checker targets `murums04/ps4-unfself-ui`. If the approved destination changes, update that constant and the project links before rebuilding. Publish stable tags as `vMAJOR.MINOR.PATCH`, keep the versioned platform asset names, and mark the intended stable release as latest. Drafts/prereleases are not offered. The app only opens browser downloads and never replaces itself.

## Owner review before upload

Present the rendered application, exact destination/visibility, source inclusion list, asset sizes/hashes, executed checks and remaining limitations. Wait for explicit approval before creating the repository, pushing, publishing a release, or contacting upstream.

Current state: local preparation only. Nothing has been published by this task.

Use two review steps for the expanded platform scope: first approve creating the public repository and uploading the reviewed source, which allows native CI to run. Inspect the resulting native artifacts and checks before asking for approval to publish the complete release. Do not publish unverified macOS/Linux artifacts or imply that an unrun workflow has passed.
