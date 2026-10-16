# Third-party notices

## ps4_unfself

PS4 unfself by SocraticBliss (R). Big thanks to Znullptr and flatz; also zecoxao.

Source: https://github.com/SocraticBliss/ps4_unfself
Baseline: 794ed5460ea6d82def0ed661d05d8171fa09ce1b
License: GNU GPL version 3 (see LICENSE).

This project is a modified implementation by murums. It adds a GUI, validation, index-based segment mapping, streaming conversion, cancellation, safe output publication, tests and desktop packaging. It is not an official release by SocraticBliss.

## Runtime components

- Python 3.12: Python Software Foundation License and included third-party notices. See `licenses/Python.txt`. Source: https://www.python.org/downloads/source/
- OpenSSL 3.x, used by Python's bundled hashing module: OpenSSL Project and contributors, Apache-2.0. See `licenses/OpenSSL.txt`. Source: https://github.com/openssl/openssl . The locally verified Windows Python runtime uses OpenSSL 3.5.8.
- PySide6 Essentials and Shiboken6 6.10.3: The Qt Company Ltd. and contributors. Distributed here under the open-source terms, with LGPL-3.0 and GPL-3.0 texts included. Source: https://github.com/pyside/pyside-setup/tree/v6.10.3
- Qt 6.10.3: The Qt Company Ltd. and contributors. Unmodified shared libraries under LGPL-3.0; included components also carry the notices collected under `licenses/Qt/`. Source: https://github.com/qt/qtbase/tree/v6.10.3 and https://github.com/qt/qtsvg/tree/v6.10.3
- PyInstaller: GPL-2.0-or-later with its bootloader distribution exception. See `licenses/PyInstaller.txt`. Source: https://github.com/pyinstaller/pyinstaller/tree/v6.22.3
- Inno Setup: Copyright (C) 1997-2026 Jordan Russell; portions Copyright (C) 2000-2026 Martijn Laan. Installer produced by https://jrsoftware.org/ . See `licenses/InnoSetup.txt`.
- Microsoft Visual C++ Runtime: Microsoft Corporation. Runtime DLLs are redistributed unmodified as supplied with the official Python and Qt wheels; these are system runtime components, not part of this project's GPL-licensed source.

Qt is dynamically linked in `_internal/PySide6` on Windows/Linux and in the macOS application bundle. Users may replace the shared Qt libraries with ABI-compatible modified builds; the application does not prevent replacement or reverse engineering for debugging those modifications. A modified macOS bundle needs a new local ad-hoc signature. Build instructions and dependency source locations accompany the application. A commercial Qt license is not required for the open-source license option used here.

The `licenses/Qt/` collection includes upstream attribution records, their referenced license texts and Qt license templates. It is intentionally broader than the small QtCore/QtGui/QtWidgets/QtSvg subset used by this application. Not every component listed there is used in each platform build. Linux builds also collect installed package copyrights, versions and source references for bundled system libraries under `licenses/Linux-runtime`; an unknown library owner stops packaging for review.

Corresponding application source is supplied in the versioned source ZIP beside the binary downloads. A public release must provide both together. Source locations for unmodified dependencies are listed above and in their collected notices; the distributor remains responsible for keeping the required source available.

