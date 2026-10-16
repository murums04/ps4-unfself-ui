import os
import sys
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", type=Path, default=ROOT / "docs" / "images")
args = parser.parse_args()
images = args.output_dir.resolve()
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from tests.fixtures import write_fixture
from unfself_ui.window import MainWindow

demo = ROOT / ".work" / "ui-demo"
demo.mkdir(parents=True, exist_ok=True)
output = demo / "ELF output"
output.mkdir(exist_ok=True)
os.chdir(demo)
app = QApplication([])
app.setStyle("Fusion")
window = MainWindow()
window.add_files([write_fixture(demo, name)[0] for name in ("hello-world.self", "graphics-demo.self")])
window.output_edit.setText("ELF output")
window.show()
window.start_conversion()
deadline = time.monotonic() + 10
while window.worker is not None and time.monotonic() < deadline:
    app.processEvents()
assert window.worker is None
images.mkdir(parents=True, exist_ok=True)
app.processEvents()
window.grab().save(str(images / "app.png"))
window.resize(window.minimumSize())
window.toggle_details()
app.processEvents()
window.grab().save(str(images / "ui-minimum.png"))
window.close()
print("UI screenshots captured from completed synthetic conversions")
