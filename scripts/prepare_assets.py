import io
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

root = Path(__file__).resolve().parents[1]
application = QApplication([])
icon = QIcon(str(root / "assets" / "icon.svg"))
data = QByteArray()
buffer = QBuffer(data)
buffer.open(QIODevice.OpenModeFlag.WriteOnly)
assert icon.pixmap(256, 256).save(buffer, "PNG")
image = Image.open(io.BytesIO(bytes(data)))
image.save(root / "assets" / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
image.save(root / "assets" / "icon.png")
large_data = QByteArray()
large_buffer = QBuffer(large_data)
large_buffer.open(QIODevice.OpenModeFlag.WriteOnly)
assert icon.pixmap(1024, 1024).save(large_buffer, "PNG")
Image.open(io.BytesIO(bytes(large_data))).save(root / "assets" / "icon.icns")
print("Icon generated from the project SVG")

