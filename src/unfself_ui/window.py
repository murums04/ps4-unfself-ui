from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from . import __version__
from .jobs import ConversionWorker
from .theme import STYLE


def asset_path(name: str) -> Path:
    import sys
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return root / "assets" / name


def label(text: str, name: str = "", wrap=False) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


class DropArea(QFrame):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("DropArea")
        self.setAcceptDrops(True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 14, 18, 14)
        layout.addWidget(label("↓", "DropIcon"))
        text = QVBoxLayout()
        text.setSpacing(3)
        text.addWidget(label("Drop your SELF files here", "DropTitle"))
        text.addWidget(label("Or choose files · .self, .bin, .sprx, .elf", "Hint"))
        layout.addLayout(text, 1)
        self.add_button = QPushButton("Add files…")
        self.add_button.setAccessibleName("Add input files")
        layout.addWidget(self.add_button)

    def dragEnterEvent(self, event):
        if self.isEnabled() and event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.reset_highlight()

    def dropEvent(self, event):
        self.reset_highlight()
        if self.isEnabled():
            self.files_dropped.emit([Path(url.toLocalFile()) for url in event.mimeData().urls()
                                     if url.isLocalFile()])
            event.acceptProposedAction()

    def reset_highlight(self):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sources: list[Path] = []
        self.worker = None
        self.close_after_cancel = False
        self.results = {}
        self.setWindowTitle(f"murums PS4 Unfself UI · {__version__}")
        self.setWindowIcon(QIcon(str(asset_path("icon.svg"))))
        self.resize(1020, 780)
        self.setMinimumSize(860, 660)
        self.setStyleSheet(STYLE)
        self.build_interface()
        self.update_actions()

    def build_interface(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 22, 28, 20)
        layout.setSpacing(13)
        header = QHBoxLayout()
        identity = QVBoxLayout()
        identity.setSpacing(2)
        identity.addWidget(label("murums  /  FILE TOOLS", "Brand"))
        identity.addWidget(label("PS4 Unfself", "Title"))
        identity.addWidget(label("Turn fake-signed SELF files back into ELF files.", "Subtitle"))
        header.addLayout(identity, 1)
        about = QPushButton("About")
        about.setObjectName("Quiet")
        about.clicked.connect(self.show_about)
        header.addWidget(about, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        self.drop_area = DropArea()
        self.add_button = self.drop_area.add_button
        self.add_button.clicked.connect(self.choose_files)
        self.drop_area.files_dropped.connect(self.add_files)
        layout.addWidget(self.drop_area)

        queue_header = QHBoxLayout()
        self.queue_label = label("Files · 0", "SectionTitle")
        queue_header.addWidget(self.queue_label, 1)
        self.remove_button = QPushButton("Remove selected")
        self.remove_button.setObjectName("Quiet")
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("Quiet")
        self.clear_button.clicked.connect(self.clear_files)
        queue_header.addWidget(self.remove_button)
        queue_header.addWidget(self.clear_button)
        layout.addLayout(queue_header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["SOURCE FILE", "STATUS", "RESULT"])
        self.table.setAccessibleName("Files to convert")
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 125)
        self.table.setMinimumHeight(100)
        self.table.itemSelectionChanged.connect(self.update_actions)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setAccessibleName("Conversion details")
        self.details.setMaximumBlockCount(3000)
        self.details.setMinimumHeight(60)
        self.details.hide()
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.details)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        panel = QFrame()
        panel.setObjectName("OutputPanel")
        output_layout = QVBoxLayout(panel)
        output_layout.setContentsMargins(14, 11, 14, 11)
        output_layout.setSpacing(6)
        output_label = label("Output folder", "SectionTitle")
        output_layout.addWidget(output_label)
        output_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Choose where the ELF files will be saved")
        self.output_edit.setAccessibleName("Output folder")
        output_label.setBuddy(self.output_edit)
        self.output_edit.textChanged.connect(self.update_actions)
        output_row.addWidget(self.output_edit, 1)
        self.browse_button = QPushButton("Browse…")
        self.browse_button.clicked.connect(self.choose_output)
        output_row.addWidget(self.browse_button)
        output_layout.addLayout(output_row)
        output_layout.addWidget(label("Originals stay untouched. Existing names get a numbered suffix.", "Hint"))
        layout.addWidget(panel)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Overall conversion progress")
        layout.addWidget(self.progress)
        actions = QHBoxLayout()
        self.details_button = QPushButton("Show details")
        self.details_button.setObjectName("Quiet")
        self.details_button.clicked.connect(self.toggle_details)
        self.open_button = QPushButton("Open output folder")
        self.open_button.setObjectName("Quiet")
        self.open_button.clicked.connect(self.open_output)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_conversion)
        self.cancel_button.hide()
        self.convert_button = QPushButton("Convert to ELF")
        self.convert_button.setObjectName("Primary")
        self.convert_button.clicked.connect(self.start_conversion)
        actions.addWidget(self.details_button)
        actions.addWidget(self.open_button)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.convert_button)
        layout.addLayout(actions)
        self.status_label = label("Add files to get started. Already fake-signed files only; no decryption.", "Hint", True)
        layout.addWidget(self.status_label)
        QWidget.setTabOrder(self.add_button, self.table)
        QWidget.setTabOrder(self.table, self.remove_button)
        QWidget.setTabOrder(self.remove_button, self.clear_button)
        QWidget.setTabOrder(self.clear_button, self.output_edit)
        QWidget.setTabOrder(self.output_edit, self.browse_button)
        QWidget.setTabOrder(self.browse_button, self.convert_button)

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add fake-signed PS4 files", "",
            "PS4 executables (*.self *.bin *.sprx *.elf);;All files (*)")
        self.add_files([Path(path) for path in paths])

    def add_files(self, paths):
        if self.worker is not None:
            return
        skipped = 0
        for path in paths:
            try:
                path = Path(path).resolve(strict=True)
                if not path.is_file() or path in self.sources:
                    skipped += 1
                    continue
            except (OSError, ValueError):
                skipped += 1
                continue
            self.sources.append(path)
            row = self.table.rowCount()
            self.table.insertRow(row)
            for column, text in enumerate((path.name, "Ready", "—")):
                self.table.setItem(row, column, QTableWidgetItem(text))
            self.table.item(row, 0).setToolTip(str(path))
        if self.sources and not self.output_edit.text():
            self.output_edit.setText(str(self.sources[0].parent))
        self.queue_label.setText(f"Files · {len(self.sources)}")
        self.status_label.setText(f"{len(self.sources)} file(s) in the queue." +
                                  (f" {skipped} duplicate(s) or non-file item(s) skipped." if skipped else ""))
        self.update_actions()

    def remove_selected(self):
        if self.worker is not None:
            return
        for row in sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True):
            self.sources.pop(row)
            self.table.removeRow(row)
        self.queue_label.setText(f"Files · {len(self.sources)}")
        self.update_actions()

    def clear_files(self):
        if self.worker is not None:
            return
        self.sources.clear()
        self.table.setRowCount(0)
        self.details.clear()
        self.progress.setValue(0)
        self.queue_label.setText("Files · 0")
        self.status_label.setText("Add files to get started.")
        self.update_actions()

    def choose_output(self):
        path = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_edit.text())
        if path:
            self.output_edit.setText(path)

    def update_actions(self):
        busy = self.worker is not None
        try:
            valid_output = bool(self.output_edit.text().strip()) and Path(self.output_edit.text()).is_dir()
        except (OSError, ValueError):
            valid_output = False
        self.add_button.setEnabled(not busy)
        self.drop_area.setEnabled(not busy)
        self.output_edit.setEnabled(not busy)
        self.browse_button.setEnabled(not busy)
        self.remove_button.setEnabled(not busy and bool(self.table.selectedIndexes()))
        self.clear_button.setEnabled(not busy and bool(self.sources))
        self.convert_button.setEnabled(not busy and bool(self.sources) and valid_output)
        self.open_button.setEnabled(valid_output)
        self.cancel_button.setVisible(busy)

    def start_conversion(self):
        if self.worker is not None or not self.convert_button.isEnabled():
            return
        self.results = {}
        self.details.clear()
        self.progress.setValue(0)
        for row in range(len(self.sources)):
            self.set_row(row, "Waiting", "—")
        self.worker = ConversionWorker(list(self.sources), Path(self.output_edit.text()), self)
        self.worker.file_started.connect(self.file_started)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.file_finished.connect(self.file_finished)
        self.worker.finished.connect(self.batch_finished)
        self.cancel_button.setEnabled(True)
        self.status_label.setText("Converting…")
        self.update_actions()
        self.worker.start()

    def file_started(self, row):
        self.set_row(row, "Converting", "—")
        self.status_label.setText(f"Converting {row + 1} of {len(self.sources)} · {self.sources[row].name}")

    def update_progress(self, row, percent):
        self.progress.setValue(int((row * 100 + percent) / max(len(self.sources), 1)))

    def set_row(self, row, state, result):
        colors = {"Converted": "#73e0be", "Failed": "#ffb4b4", "Cancelled": "#d7bd8a", "Converting": "#70cfee"}
        self.table.item(row, 1).setText(state)
        self.table.item(row, 1).setForeground(QColor(colors.get(state, "#a7bbce")))
        self.table.item(row, 2).setText(result)

    def file_finished(self, row, state, detail):
        self.results[row] = state
        self.set_row(row, state, Path(detail).name if state == "Converted" else detail)
        self.table.item(row, 2).setToolTip(detail)
        self.details.appendPlainText(f"{state} · {self.sources[row].name}\n{detail}\n")
        self.progress.setValue(int((row + 1) * 100 / max(len(self.sources), 1)))
        if state == "Failed":
            self.details.show()
            self.details_button.setText("Hide details")

    def batch_finished(self):
        worker = self.worker
        self.worker = None
        worker.deleteLater()
        counts = {state: list(self.results.values()).count(state) for state in ("Converted", "Failed", "Cancelled")}
        self.status_label.setText(" · ".join(f"{counts[state]} {state.lower()}" for state in counts))
        self.convert_button.setText("Convert again")
        self.update_actions()
        if self.close_after_cancel:
            self.close()

    def cancel_conversion(self):
        if self.worker is not None:
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Cancelling… Completed files will be kept.")

    def toggle_details(self):
        visible = not self.details.isVisible()
        self.details.setVisible(visible)
        self.details_button.setText("Hide details" if visible else "Show details")

    def open_output(self):
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_edit.text())):
            self.status_label.setText("Could not open the folder. Copy its path from the field above.")

    def show_about(self):
        QMessageBox.about(self, "About PS4 Unfself UI",
            f"<h3>murums PS4 Unfself UI {__version__}</h3>"
            "<p>A desktop interface for restoring ELF files from unencrypted, uncompressed PS4 SELF files.</p>"
            "<p>Based on <a href='https://github.com/SocraticBliss/ps4_unfself'>ps4_unfself by SocraticBliss</a>. "
            "Original research: Znullptr, flatz and zecoxao.</p>"
            "<p>GPL-3.0. Built with Python and Qt for Python. See THIRD_PARTY_NOTICES.md and licenses/ in the application folder.</p>"
            "<p>No decryption, network uploads or automatic updates.</p>")

    def closeEvent(self, event):
        if self.worker is not None:
            self.close_after_cancel = True
            self.cancel_conversion()
            event.ignore()
        else:
            event.accept()

