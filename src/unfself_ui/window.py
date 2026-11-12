from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QPlainTextEdit, QProgressBar,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from . import __version__
from .about import AboutDialog
from .assets import asset_path
from .jobs import ConversionWorker
from .native_theme import install_native_theme
from .theme import STYLE
from .updates import UpdateChecker

# Folder drops skip .elf so earlier outputs next to their inputs are not queued again.
FOLDER_SUFFIXES = {".self", ".bin", ".sprx"}
OUTPUT_HINT = "Originals unchanged. Duplicate outputs numbered."


def expand_folders(paths, suffixes):
    """Yield dropped files, plus matching files directly inside dropped folders."""
    for path in map(Path, paths):
        try:
            if path.is_dir():
                matches = sorted(child for child in path.iterdir()
                                 if child.suffix.lower() in suffixes and child.is_file())
                if matches:
                    yield from matches
                    continue
        except OSError:
            pass
        yield path


def label(text: str, name: str = "", wrap=False) -> QLabel:
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
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
        text.addWidget(label("Drop SELF files", "DropTitle"))
        text.addWidget(label(".self · .bin · .sprx · .elf", "Hint"))
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
        install_native_theme()
        self.update_checker = UpdateChecker(self)
        self.sources: list[Path] = []
        self.worker = None
        self.close_after_cancel = False
        self.results = {}
        self.completed: set[Path] = set()
        self.batch_rows: list[int] = []
        self.setAcceptDrops(True)
        self.setWindowTitle(f"murums PS4 Unfself UI · {__version__}")
        self.setWindowIcon(QIcon(str(asset_path("icon.svg"))))
        self.resize(1020, 780)
        self.setMinimumSize(860, 660)
        self.setStyleSheet(STYLE)
        self.build_interface()
        self.update_checker.changed.connect(self.refresh_update_notice)
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
        identity.addWidget(label("FILE TOOLS", "Brand"))
        identity.addWidget(label("murums PS4 Unfself UI", "Title"))
        identity.addWidget(label("Convert fake-signed SELF to ELF.", "Subtitle"))
        header.addLayout(identity, 1)
        self.update_notice = QPushButton("Update available")
        self.update_notice.clicked.connect(self.show_about)
        self.update_notice.hide()
        header.addWidget(self.update_notice, 0, Qt.AlignmentFlag.AlignTop)
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
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 125)
        self.table.setMinimumHeight(100)
        self.table.itemSelectionChanged.connect(self.update_actions)
        # macOS labels Backspace as "delete", so both keys remove selected rows.
        for key in (QKeySequence(QKeySequence.StandardKey.Delete), QKeySequence(Qt.Key.Key_Backspace)):
            remove_shortcut = QShortcut(key, self.table)
            remove_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            remove_shortcut.activated.connect(self.remove_selected)
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
        self.output_edit.setPlaceholderText("Choose an ELF output folder")
        self.output_edit.setAccessibleName("Output folder")
        output_label.setBuddy(self.output_edit)
        self.output_edit.textChanged.connect(self.output_changed)
        output_row.addWidget(self.output_edit, 1)
        self.browse_button = QPushButton("Browse…")
        self.browse_button.clicked.connect(self.choose_output)
        output_row.addWidget(self.browse_button)
        output_layout.addLayout(output_row)
        self.output_hint = label(OUTPUT_HINT, "Hint")
        output_layout.addWidget(self.output_hint)
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
        self.status_label = label("Add fake-signed files. No decryption.", "Hint", True)
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
        previous_count = len(self.sources)
        skipped = 0
        for path in expand_folders(paths, FOLDER_SUFFIXES):
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
        if len(self.sources) != previous_count:
            self.results.clear()
            self.progress.setValue(0)
        self.queue_label.setText(f"Files · {len(self.sources)}")
        self.status_label.setText(f"Queued: {len(self.sources)}" +
                                  (f" · Skipped: {skipped} duplicates/non-files" if skipped else ""))
        self.update_actions()

    def remove_selected(self):
        if self.worker is not None:
            return
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.sources.pop(row)
            self.table.removeRow(row)
        self.completed &= set(self.sources)
        if rows:
            self.results.clear()
            self.progress.setValue(0)
        self.queue_label.setText(f"Files · {len(self.sources)}")
        self.status_label.setText(f"Queued: {len(self.sources)}")
        self.update_actions()

    def clear_files(self):
        if self.worker is not None:
            return
        self.sources.clear()
        self.results.clear()
        self.completed.clear()
        self.table.setRowCount(0)
        self.details.clear()
        self.progress.setValue(0)
        self.queue_label.setText("Files · 0")
        self.status_label.setText("Add files.")
        self.update_actions()

    def choose_output(self):
        path = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_edit.text())
        if path:
            self.output_edit.setText(path)

    def output_changed(self):
        # Results in another folder do not count as done for the new one.
        self.completed.clear()
        self.update_actions()

    def update_actions(self):
        busy = self.worker is not None
        text = self.output_edit.text()
        try:
            folder = Path(text).expanduser()
            absolute = folder.is_absolute()
            valid_output = bool(text) and absolute and folder.is_dir()
        except (OSError, ValueError, RuntimeError):
            absolute = valid_output = False
        if not text or valid_output:
            self.output_hint.setText(OUTPUT_HINT)
        elif not absolute:
            self.output_hint.setText("Enter a full folder path or choose Browse…")
        else:
            self.output_hint.setText("Folder not found. Choose an existing folder.")
        self.add_button.setEnabled(not busy)
        self.drop_area.setEnabled(not busy)
        self.output_edit.setEnabled(not busy)
        self.browse_button.setEnabled(not busy)
        self.remove_button.setEnabled(not busy and bool(self.table.selectedIndexes()))
        self.clear_button.setEnabled(not busy and bool(self.sources))
        self.convert_button.setEnabled(not busy and bool(self.sources) and valid_output)
        self.open_button.setEnabled(valid_output)
        self.cancel_button.setVisible(busy)
        done = sum(path in self.completed for path in self.sources)
        if self.sources and done == len(self.sources):
            self.convert_button.setText("Convert again")
        else:
            self.convert_button.setText("Convert remaining" if done else "Convert to ELF")

    def start_conversion(self):
        if self.worker is not None or not self.convert_button.isEnabled():
            return
        self.results = {}
        self.details.clear()
        self.progress.setValue(0)
        # Only unfinished rows run again; a fully converted queue converts every file once more.
        self.batch_rows = [row for row, path in enumerate(self.sources) if path not in self.completed]
        if not self.batch_rows:
            self.completed.clear()
            self.batch_rows = list(range(len(self.sources)))
        for row in self.batch_rows:
            self.set_row(row, "Waiting", "—")
        batch = [self.sources[row] for row in self.batch_rows]
        self.worker = ConversionWorker(batch, Path(self.output_edit.text()).expanduser(), self)
        self.worker.file_started.connect(self.file_started)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.file_finished.connect(self.file_finished)
        self.worker.finished.connect(self.batch_finished)
        self.cancel_button.setEnabled(True)
        self.status_label.setText("Converting…")
        self.update_actions()
        self.worker.start()

    def batch_row(self, index):
        # Worker signals count within the running batch; outside a batch they are queue rows.
        return self.batch_rows[index] if self.batch_rows else index

    def batch_size(self):
        return max(len(self.batch_rows) or len(self.sources), 1)

    def file_started(self, index):
        row = self.batch_row(index)
        self.set_row(row, "Converting", "—")
        self.status_label.setText(f"Converting {index + 1} of {self.batch_size()} · {self.sources[row].name}")

    def update_progress(self, index, percent):
        self.progress.setValue(int((index * 100 + percent) / self.batch_size()))

    def set_row(self, row, state, result):
        colors = {"Converted": "#73e0be", "Failed": "#ffb4b4", "Cancelled": "#d7bd8a", "Converting": "#70cfee"}
        self.table.item(row, 1).setText(state)
        self.table.item(row, 1).setForeground(QColor(colors.get(state, "#a7bbce")))
        self.table.item(row, 2).setText(result)

    def file_finished(self, index, state, detail):
        row = self.batch_row(index)
        self.results[row] = state
        if state == "Converted":
            self.completed.add(self.sources[row])
        self.set_row(row, state, Path(detail).name if state == "Converted" else detail)
        self.table.item(row, 2).setToolTip(detail)
        self.details.appendPlainText(f"{state} · {self.sources[row].name}\n{detail}\n")
        if state != "Cancelled":
            self.progress.setValue(int((index + 1) * 100 / self.batch_size()))
        if state == "Failed":
            self.details.show()
            self.details_button.setText("Hide details")

    def batch_finished(self):
        worker = self.worker
        self.worker = None
        worker.deleteLater()
        self.batch_rows = []
        states = list(self.results.values())
        counts = [f"{states.count(state)} {state.lower()}" for state in ("Converted", "Failed", "Cancelled")
                  if states.count(state)]
        self.status_label.setText(" · ".join(counts) or "Nothing converted.")
        self.update_actions()
        if self.close_after_cancel:
            self.close()

    def cancel_conversion(self):
        if self.worker is not None:
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Cancelling… Keeping completed files.")

    def toggle_details(self):
        visible = not self.details.isVisible()
        self.details.setVisible(visible)
        self.details_button.setText("Hide details" if visible else "Show details")

    def open_output(self):
        path = str(Path(self.output_edit.text()).expanduser().resolve())
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
            self.status_label.setText("Could not open folder. Copy the output path above.")

    def show_about(self):
        dialog = AboutDialog(self.update_checker, self)
        dialog.exec()
        dialog.deleteLater()

    def refresh_update_notice(self):
        self.update_notice.setVisible(self.update_checker.release is not None)

    def dragEnterEvent(self, event):
        # Drops outside the drop area, such as onto the file list, add files too.
        if self.worker is None and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if self.worker is None:
            self.add_files([Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()])
            event.acceptProposedAction()

    def changeEvent(self, event):
        # Recheck the output folder after it was created or removed in another app.
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self.update_actions()
        super().changeEvent(event)

    def closeEvent(self, event):
        if self.worker is not None:
            self.close_after_cancel = True
            self.cancel_conversion()
            event.ignore()
        else:
            event.accept()

