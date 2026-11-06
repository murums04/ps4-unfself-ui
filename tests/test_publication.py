import errno
import os
from pathlib import Path

import pytest

from tests.fixtures import write_fixture
from unfself_ui import converter


@pytest.fixture
def without_hardlinks(monkeypatch):
    def unsupported(*args):
        raise OSError(errno.ENOTSUP, "Hard links unsupported")

    monkeypatch.setattr(converter.os, "link", unsupported)
    if os.name == "nt":
        pytest.skip("Windows uses rename instead of hard links")


@pytest.mark.parametrize("error_number", sorted({errno.ENOTSUP, errno.EOPNOTSUPP, errno.EPERM}))
def test_copy_fallback_preserves_input_and_existing_output(tmp_path, monkeypatch, without_hardlinks, error_number):
    def unsupported(*args):
        raise OSError(error_number, "Hard links unsupported")

    monkeypatch.setattr(converter.os, "link", unsupported)
    source, expected = write_fixture(tmp_path, "Größe 日本.elf")
    original = source.read_bytes()
    existing = tmp_path / "Größe 日本 (2).elf"
    existing.write_bytes(b"keep existing")
    output = converter.convert_file(source, tmp_path)
    assert output.name == "Größe 日本 (3).elf"
    assert output.read_bytes() == expected
    assert source.read_bytes() == original
    assert existing.read_bytes() == b"keep existing"
    assert set(tmp_path.iterdir()) == {source, existing, output}


def test_copy_fallback_preserves_concurrent_output(tmp_path, monkeypatch, without_hardlinks):
    source, expected = write_fixture(tmp_path)
    destination = tmp_path / "sample.elf"
    original_open = Path.open

    def open_with_collision(path, mode="r", *args, **kwargs):
        if path == destination and mode == "xb":
            with original_open(path, "wb") as stream:
                stream.write(b"concurrent output")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_with_collision)
    output = converter.convert_file(source, tmp_path)
    assert output.name == "sample (2).elf"
    assert output.read_bytes() == expected
    assert destination.read_bytes() == b"concurrent output"


def test_copy_fallback_preserves_dangling_symlink(tmp_path, without_hardlinks):
    source, expected = write_fixture(tmp_path)
    destination = tmp_path / "sample.elf"
    target = tmp_path / "missing.elf"
    destination.symlink_to(target)
    output = converter.convert_file(source, tmp_path)
    assert output.name == "sample (2).elf"
    assert output.read_bytes() == expected
    assert destination.is_symlink()
    assert not target.exists()


def test_cancel_during_fallback_removes_partial_output(tmp_path, without_hardlinks):
    source, _ = write_fixture(tmp_path, payloads=(b"x" * (2 * converter.CHUNK_SIZE),))
    original = source.read_bytes()
    destination = tmp_path / "sample.elf"

    def cancel():
        return destination.exists() and destination.stat().st_size > 0

    with pytest.raises(converter.ConversionCancelled):
        converter.convert_file(source, tmp_path, cancel=cancel)
    assert list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == original


@pytest.mark.parametrize("operation", ["write", "fsync"])
def test_fallback_io_error_removes_partial_output(tmp_path, monkeypatch, without_hardlinks, operation):
    source, _ = write_fixture(tmp_path)
    original = source.read_bytes()
    destination = tmp_path / "sample.elf"
    original_open = Path.open
    original_fsync = os.fsync

    def fail(*args):
        raise OSError(errno.ENOSPC, "No space left on device")

    def open_with_error(path, mode="r", *args, **kwargs):
        stream = original_open(path, mode, *args, **kwargs)
        if path == destination and mode == "xb" and operation == "write":
            stream.write = fail
        return stream

    def fsync_with_error(descriptor):
        if destination.exists() and operation == "fsync":
            fail()
        original_fsync(descriptor)

    monkeypatch.setattr(Path, "open", open_with_error)
    monkeypatch.setattr(os, "fsync", fsync_with_error)
    with pytest.raises(converter.ConversionError, match="No space"):
        converter.convert_file(source, tmp_path)
    assert list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == original


@pytest.mark.parametrize("error_number", [errno.ENOSPC, errno.EACCES, errno.EIO, errno.EROFS, errno.EXDEV])
def test_other_link_errors_do_not_copy(tmp_path, monkeypatch, without_hardlinks, error_number):
    source, _ = write_fixture(tmp_path)

    def fail(*args):
        raise OSError(error_number, "Link failed")

    def unexpected_copy(*args):
        pytest.fail("Unexpected fallback for a filesystem error")

    monkeypatch.setattr(converter.os, "link", fail)
    monkeypatch.setattr(converter, "copy_output", unexpected_copy)
    with pytest.raises(converter.ConversionError, match="Link failed"):
        converter.convert_file(source, tmp_path)
    assert list(tmp_path.iterdir()) == [source]
