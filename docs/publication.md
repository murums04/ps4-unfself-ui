# Publication checklist

Destination: **murums04/ps4-unfself-ui**, public. Product: **murums PS4 Unfself UI**. Verify the signed-in account and repository owner before upload.

## Content

Include source, tests, build scripts/configuration, assets, licenses, README, screenshot and public docs. Exclude personal/game files, ELF outputs, local records, environments and build tools. Keep binary packages out of Git; attach them to Releases.

- Description: `Desktop GUI for SocraticBliss' ps4_unfself. Convert fake-signed PS4 SELF files to ELF.`
- Topics: `ps4`, `ps4-unfself`, `unfself`, `self-to-elf`, `playstation-4`, `elf`, `homebrew`, `gui`, `windows`, `macos`, `linux`, `pyside6`
- Homepage: `https://github.com/murums04/ps4-unfself-ui/releases/latest`
- Tag/title: `v0.1.0` / `murums PS4 Unfself UI 0.1.0`
- Body: `docs/release-notes.md`
- Windows setup EXE and portable ZIP.
- macOS arm64/x64 DMG and app ZIP for each architecture.
- Linux DEB and portable tar.gz.
- Shared source ZIP and combined `SHA256SUMS.txt`.

Put direct app downloads above the README screenshot and at the top of the release notes. Use plain platform names, separate Apple Silicon/Intel Mac, and distinguish installers from portable archives. Keep the original project link near the introduction. Topics improve discovery; search placement and an upstream backlink are not guaranteed.

## Approval

1. Show the owner the destination, visibility, changes, asset sizes/hashes, checks and limitations. Get approval before creating the repository or pushing source.
2. Run native CI, inspect its artifacts, then get approval before publishing the release.

The owner may approve both steps together for the reviewed scope, conditional on all four platform jobs passing. Do not publish a partial release or label untested platforms as supported. Report failures and repair within the approved scope; request a new review for changed functionality or platform scope.

Keep direct download links and platform/test records current. Build the final packages from the same commit and combine platform checksums into `SHA256SUMS.txt`. Publish the ten assets (eight app packages, source ZIP and checksums) as a stable latest release. Verify the public README, asset links and updater response after publication.

Credit/link upstream in the README. Contacting upstream requires separate approval; a backlink is not guaranteed.

The updater targets `murums04/ps4-unfself-ui`. A destination change requires updated links and a rebuild. Use stable `vMAJOR.MINOR.PATCH` tags, existing asset names and GitHub's latest-release setting. Exclude drafts/prereleases; updates use browser downloads with manual installation.
