import sys
from pathlib import Path

root = Path(SPECPATH).parent
is_mac = sys.platform == 'darwin'
analysis = Analysis(
    [str(root / 'packaging/launch.py')],
    pathex=[str(root / 'src')],
    datas=[(str(root / 'assets' / name), 'assets') for name in ('icon.svg', 'github.svg', 'kofi.png')],
    excludes=['tkinter', 'pytest', 'PIL', 'PySide6.QtQml',
              'PySide6.QtQuick', 'PySide6.QtTest', 'PySide6.QtOpenGL'],
    noarchive=False,
)
archive = PYZ(analysis.pure)
executable = EXE(
    archive, analysis.scripts, [], exclude_binaries=True,
    name='ps4-unfself-ui', console=not is_mac, strip=False, upx=False,
    icon=str(root / 'assets/icon.icns') if is_mac else None,
)
collection = COLLECT(executable, analysis.binaries, analysis.datas,
                     strip=False, upx=False, name='ps4-unfself-ui')
if is_mac:
    application = BUNDLE(
        collection, name='PS4 Unfself UI.app', icon=str(root / 'assets/icon.icns'),
        bundle_identifier='io.github.murums04.ps4-unfself-ui',
        info_plist={
            'CFBundleName': 'PS4 Unfself UI',
            'CFBundleShortVersionString': '0.1.0',
            'CFBundleVersion': '0.1.0',
            'LSMinimumSystemVersion': '13.0',
            'NSHighResolutionCapable': True,
        },
    )
