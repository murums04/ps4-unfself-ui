from pathlib import Path
from threading import Event

from PySide6.QtCore import QThread, Signal

from .converter import ConversionCancelled, ConversionError, convert_file


class ConversionWorker(QThread):
    file_started = Signal(int)
    progress_changed = Signal(int, int)
    file_finished = Signal(int, str, str)

    def __init__(self, sources: list[Path], output_dir: Path, parent=None):
        super().__init__(parent)
        self.sources = sources
        self.output_dir = output_dir
        self.stop_requested = Event()

    def cancel(self):
        self.stop_requested.set()

    def run(self):
        for row, source in enumerate(self.sources):
            if self.stop_requested.is_set():
                self.file_finished.emit(row, "Cancelled", "Not processed. Run again to retry.")
                continue
            self.file_started.emit(row)
            last_percent = -1

            def report_progress(done, total):
                nonlocal last_percent
                percent = int(done * 100 / max(total, 1))
                if percent != last_percent:
                    last_percent = percent
                    self.progress_changed.emit(row, percent)

            try:
                output = convert_file(source, self.output_dir, self.stop_requested.is_set, report_progress)
                self.file_finished.emit(row, "Converted", str(output))
            except ConversionCancelled:
                self.file_finished.emit(row, "Cancelled", "Cancelled; partial output removed.")
            except ConversionError as error:
                self.file_finished.emit(row, "Failed", str(error))
            except Exception as error:
                self.file_finished.emit(row, "Failed", f"Unexpected error ({type(error).__name__}): {error}")

