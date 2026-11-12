import os
import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt, QMimeData, QPoint, QPointF, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from tests.fixtures import write_fixture
from unfself_ui.window import MainWindow


@pytest.fixture(scope="session")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(application):
    view = MainWindow()
    view.show()
    application.processEvents()
    yield view
    if view.worker and view.worker.isRunning():
        view.worker.cancel()
        view.worker.wait(5000)
    view.close()
    application.processEvents()


def wait_for(application, condition, timeout=10):
    deadline = time.monotonic() + timeout
    while not condition() and time.monotonic() < deadline:
        application.processEvents()
        QTest.qWait(10)
    assert condition(), "The Qt workflow did not finish within the test deadline"


def test_file_queue_deduplicates_and_can_remove(window, tmp_path):
    source, _ = write_fixture(tmp_path)
    window.add_files([source, source, tmp_path])
    assert window.table.rowCount() == 1
    assert window.convert_button.isEnabled()
    window.table.selectRow(0)
    QTest.mouseClick(window.remove_button, Qt.MouseButton.LeftButton)
    assert window.table.rowCount() == 0
    assert not window.convert_button.isEnabled()


def test_real_mixed_batch_completes_without_blocking_ui(window, application, tmp_path):
    source, expected = write_fixture(tmp_path)
    bad = tmp_path / "invalid.bin"
    bad.write_bytes(b"not a valid file")
    window.add_files([source, bad])
    window.output_edit.setText(str(tmp_path))
    QTest.mouseClick(window.convert_button, Qt.MouseButton.LeftButton)
    assert not window.add_button.isEnabled()
    assert not window.output_edit.isEnabled()
    wait_for(application, lambda: window.worker is None)
    assert (tmp_path / "sample.elf").read_bytes() == expected
    assert window.table.item(0, 1).text() == "Converted"
    assert window.table.item(1, 1).text() == "Failed"
    assert "1 converted" in window.status_label.text()
    assert window.add_button.isEnabled()
    assert "invalid.bin" in window.details.toPlainText()


def test_missing_destination_disables_conversion(window, tmp_path):
    source, _ = write_fixture(tmp_path)
    window.add_files([source])
    window.output_edit.setText(str(tmp_path / "not-there"))
    assert not window.convert_button.isEnabled()
    assert "not found" in window.output_hint.text()
    (tmp_path / "not-there").mkdir()
    window.update_actions()
    assert window.convert_button.isEnabled()
    assert "not found" not in window.output_hint.text()


def test_relative_destination_is_rejected(window, tmp_path, monkeypatch):
    source, _ = write_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    window.add_files([source])
    window.output_edit.setText(".")
    assert not window.convert_button.isEnabled()
    assert "full folder path" in window.output_hint.text()


def test_adding_files_converts_only_new_ones(window, application, tmp_path):
    source, expected = write_fixture(tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    window.add_files([source])
    window.output_edit.setText(str(output))
    window.start_conversion()
    wait_for(application, lambda: window.worker is None)
    added = tmp_path / "added.self"
    added.write_bytes(source.read_bytes())
    window.add_files([added])
    window.start_conversion()
    wait_for(application, lambda: window.worker is None)
    assert sorted(path.name for path in output.iterdir()) == ["added.elf", "sample.elf"]
    assert window.table.item(0, 1).text() == "Converted"
    assert window.status_label.text() == "1 converted"
    assert window.convert_button.text() == "Convert again"


def test_dropped_folder_adds_matching_files(window, tmp_path):
    source, _ = write_fixture(tmp_path)
    (tmp_path / "notes.txt").write_text("skip")
    (tmp_path / "sample.elf").write_bytes(b"earlier output")
    window.add_files([tmp_path])
    assert window.sources == [source.resolve()]
    empty = tmp_path / "empty"
    empty.mkdir()
    window.add_files([empty])
    assert "Skipped: 1" in window.status_label.text()


def test_new_output_folder_converts_whole_queue(window, application, tmp_path):
    source, _ = write_fixture(tmp_path)
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    window.add_files([source])
    window.output_edit.setText(str(first))
    window.start_conversion()
    wait_for(application, lambda: window.worker is None)
    window.output_edit.setText(str(second))
    assert window.convert_button.text() == "Convert to ELF"
    window.start_conversion()
    wait_for(application, lambda: window.worker is None)
    assert [path.name for path in second.iterdir()] == ["sample.elf"]


def test_delete_keys_remove_selected_rows(window, tmp_path):
    from PySide6.QtGui import QKeySequence, QShortcut

    # Headless X servers may not give the table keyboard focus, so trigger the shortcuts directly.
    shortcuts = window.table.findChildren(QShortcut)
    keys = {shortcut.key().toString() for shortcut in shortcuts}
    assert QKeySequence(Qt.Key.Key_Backspace).toString() in keys
    assert QKeySequence(QKeySequence.StandardKey.Delete).toString() in keys
    for shortcut in shortcuts:
        source, _ = write_fixture(tmp_path)
        window.add_files([source])
        window.table.selectRow(0)
        shortcut.activated.emit()
        assert window.table.rowCount() == 0


@pytest.mark.parametrize("output_name", ["output", pytest.param("output ", marks=pytest.mark.skipif(
    os.name == "nt", reason="Windows trims trailing spaces in directory names"))])
def test_home_output_path_converts_and_opens_the_same_folder(
        window, application, tmp_path, monkeypatch, output_name):
    from PySide6.QtGui import QDesktopServices

    source, expected = write_fixture(tmp_path)
    destination = tmp_path / output_name
    destination.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toLocalFile()) or True)
    window.add_files([source])
    window.output_edit.setText(f"~/{output_name}")
    assert window.convert_button.isEnabled()
    window.start_conversion()
    wait_for(application, lambda: window.worker is None)
    assert (destination / "sample.elf").read_bytes() == expected
    window.open_output()
    assert [Path(path) for path in opened] == [destination.resolve()]


def test_unknown_home_disables_conversion(window, tmp_path):
    source, _ = write_fixture(tmp_path)
    window.add_files([source])
    window.output_edit.setText("~missing-test-user/output")
    assert not window.convert_button.isEnabled()
    assert not window.open_button.isEnabled()


@pytest.mark.skipif(os.name == "nt", reason="Windows disallows angle brackets in filenames")
def test_conversion_status_preserves_filename_markup(window, tmp_path):
    source, _ = write_fixture(tmp_path)
    source = source.rename(tmp_path / "<b>sample.self")
    window.add_files([source])
    window.file_started(0)
    expected = f"Converting 1 of 1 · {source.name}"
    window.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    window.status_label.setSelection(0, len(expected))
    assert window.status_label.selectedText() == expected


@pytest.mark.parametrize("change", ["add", "remove", "clear"])
def test_changing_completed_queue_resets_batch_summary(window, application, tmp_path, change):
    source, _ = write_fixture(tmp_path)
    window.add_files([source])
    window.start_conversion()
    wait_for(application, lambda: window.worker is None)
    assert window.results == {0: "Converted"}
    assert window.progress.value() == 100
    if change == "add":
        added = tmp_path / "another.self"
        added.write_bytes(source.read_bytes())
        window.add_files([added])
    elif change == "remove":
        window.table.selectRow(0)
        window.remove_selected()
    else:
        window.clear_files()
    assert not window.results
    assert window.progress.value() == 0
    assert window.convert_button.text() == ("Convert remaining" if change == "add" else "Convert to ELF")
    assert window.status_label.text() == ("Add files." if change == "clear" else
                                          f"Queued: {len(window.sources)}")
    assert window.queue_label.text() == f"Files · {len(window.sources)}"


def test_cancelling_a_queue_settles_every_row(window, application, tmp_path):
    source, _ = write_fixture(tmp_path, payloads=(b"x" * (16 * 1024 * 1024),))
    paths = []
    for index in range(10):
        path = tmp_path / f"copy-{index}.self"
        path.write_bytes(source.read_bytes())
        paths.append(path)
    window.add_files(paths)
    window.output_edit.setText(str(tmp_path))
    QTest.mouseClick(window.convert_button, Qt.MouseButton.LeftButton)
    QTest.mouseClick(window.cancel_button, Qt.MouseButton.LeftButton)
    wait_for(application, lambda: window.worker is None)
    states = [window.table.item(row, 1).text() for row in range(10)]
    assert "Cancelled" in states
    assert set(states) <= {"Converted", "Cancelled"}
    assert not list(tmp_path.glob(".unfself-*"))
    assert window.convert_button.isEnabled()


def test_closing_during_conversion_waits_for_worker(window, application, tmp_path):
    source, _ = write_fixture(tmp_path, payloads=(b"x" * (16 * 1024 * 1024),))
    window.add_files([source])
    window.output_edit.setText(str(tmp_path))
    QTest.mouseClick(window.convert_button, Qt.MouseButton.LeftButton)
    window.close()
    wait_for(application, lambda: window.worker is None and not window.isVisible())
    assert not list(tmp_path.glob(".unfself-*"))


def test_minimum_size_keeps_main_actions_visible(window, application):
    window.resize(window.minimumSize())
    application.processEvents()
    for widget in (window.convert_button, window.add_button, window.output_edit, window.table):
        assert widget.isVisible()
        assert window.rect().contains(widget.mapTo(window, widget.rect().bottomRight()))
    assert window.table.height() >= 90


def test_native_drop_event_adds_a_local_file(window, application, tmp_path):
    source, _ = write_fixture(tmp_path)
    data = QMimeData()
    data.setUrls([QUrl.fromLocalFile(str(source))])
    enter = QDragEnterEvent(QPoint(25, 25), Qt.DropAction.CopyAction, data,
                            Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    application.sendEvent(window.drop_area, enter)
    assert enter.isAccepted()
    drop = QDropEvent(QPointF(25, 25), Qt.DropAction.CopyAction, data,
                      Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    application.sendEvent(window.drop_area, drop)
    assert window.table.rowCount() == 1
    assert window.sources == [source.resolve()]


def test_keyboard_can_start_conversion(window, application, tmp_path):
    source, expected = write_fixture(tmp_path)
    window.add_files([source])
    window.convert_button.setFocus()
    QTest.keyClick(window.convert_button, Qt.Key.Key_Space)
    wait_for(application, lambda: window.worker is None)
    assert (tmp_path / "sample.elf").read_bytes() == expected


def test_about_icons_open_their_links_only_on_click(application, monkeypatch):
    from PySide6.QtGui import QDesktopServices
    from unfself_ui.about import AboutDialog
    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()) or True)
    dialog = AboutDialog()
    dialog.show()
    application.processEvents()
    assert opened == []
    assert not dialog.kofi_link.autoDefault()
    assert dialog.owner_link.text() != dialog.upstream_link.text()
    for button in (dialog.owner_link, dialog.upstream_link, dialog.kofi_link):
        assert not button.icon().isNull()
        assert button.accessibleName() and button.toolTip()
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    dialog.close()
    assert opened == ["https://github.com/murums04", "https://github.com/SocraticBliss/ps4_unfself",
                      "https://ko-fi.com/murums"]


def test_update_notice_opens_download_and_release_links(window, application, monkeypatch):
    from PySide6.QtGui import QDesktopServices
    from unfself_ui.about import AboutDialog
    from unfself_ui.updates import parse_release
    from tests.test_updates import release_data

    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()) or True)
    release = parse_release(release_data(), "0.1.0", "win32", "AMD64")
    window.update_checker.release = release
    window.update_checker.set_status("available", "Version 0.2.0 is available.")
    assert window.update_notice.isVisible()
    dialog = AboutDialog(window.update_checker, window)
    dialog.show()
    application.processEvents()
    assert dialog.download_button.isVisible() and dialog.release_button.isVisible()
    for button in (dialog.download_button, dialog.release_button):
        assert dialog.rect().contains(button.mapTo(dialog, button.rect().bottomRight()))
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert opened == [release.download_url, release.release_url]
    dialog.close()


def test_about_reports_browser_failure(application, monkeypatch):
    from PySide6.QtGui import QDesktopServices
    from unfself_ui.about import AboutDialog

    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: False)
    dialog = AboutDialog()
    dialog.show()
    QTest.mouseClick(dialog.owner_link, Qt.MouseButton.LeftButton)
    assert "Could not open your browser" in dialog.update_status.text()
    QTest.mouseClick(dialog.kofi_link, Qt.MouseButton.LeftButton)
    assert "https://ko-fi.com/murums" in dialog.update_status.text()
    dialog.close()
