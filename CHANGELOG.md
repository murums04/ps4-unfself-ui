# Changelog

## 0.1.3

- Queue: adding files after a batch converts only new files; "Convert remaining" skips converted files.
- Input: dropped folders add their SELF files; the whole window accepts drops.
- Output: explains a missing output folder and rechecks it when the window regains focus.
- UI: Delete removes selected rows, aligned table header with rounded corners, labeled About links, summaries without zero counts.
- Conversion: a locked temporary file no longer replaces the actual result or error.
- Tests run on a fresh checkout and skip symlink checks where Windows denies symlinks.

## 0.1.2

- Fixed CLI report errors before conversion.
- Added exFAT output support on macOS and Linux.
- Fixed output paths, filename display and queue status.
- Updated Pillow to 13.0.0 and setuptools to 84.1.0.
- Removed macOS Intel builds and downloads; macOS now targets Apple Silicon only.

## 0.1.1

- Logo: added SELF to the original file icon across the app, installers and README.

## 0.1.0

- UI: file queue, drag-and-drop, progress, cancellation and error details.
- Conversion: indexed segments, validation and protected originals/outputs.
- About: GitHub/Ko-fi links, release checks and browser downloads; manual installation. Update checks keep keyboard focus.
- Windows: dark title bars, portable ZIP, per-user installer, source and checksums.
- macOS: Apple Silicon/Intel app ZIP and DMG, with native tests.
- Linux: portable tar.gz and DEB, with installation tests and runtime notices.
- Packages: app runtime and license notices only; tests and documentation stay in the source ZIP.

