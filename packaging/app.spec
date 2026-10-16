from pathlib import Path

root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / 'packaging' / 'launch.py')],
    pathex=[str(root / 'src')],
    datas=[(str(root / 'assets' / name), 'assets') for name in ('icon.svg', 'github.svg')],
    excludes=['tkinter', 'pytest', 'PIL', 'PySide6.QtQml',
              'PySide6.QtQuick', 'PySide6.QtTest', 'PySide6.QtOpenGL'],
    noarchive=False,
)
archive = PYZ(analysis.pure)
executable = EXE(
    archive, analysis.scripts, [], exclude_binaries=True,
    name='PS4 Unfself UI', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    icon=str(root / 'assets' / 'icon.ico'),
    version=str(root / 'packaging' / 'version-info.txt'),
)
collection = COLLECT(
    executable, analysis.binaries, analysis.datas,
    strip=False, upx=False, name='ps4-unfself-ui',
)

