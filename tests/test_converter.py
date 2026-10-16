import os
import struct
from pathlib import Path

import pytest

from tests.fixtures import fake_self, write_fixture
from unfself_ui.converter import ConversionCancelled, ConversionError, convert_file


@pytest.mark.parametrize("reverse", [False, True])
def test_maps_same_sized_segments_by_index(tmp_path, reverse):
    source, expected = write_fixture(tmp_path, reverse=reverse)
    before = source.read_bytes()
    result = convert_file(source, tmp_path)
    assert result.read_bytes() == expected
    assert source.read_bytes() == before


def test_unicode_paths_and_existing_outputs_are_preserved(tmp_path):
    source, expected = write_fixture(tmp_path, "Größe 日本.self")
    original = tmp_path / "Größe 日本.elf"
    original.write_bytes(b"keep me")
    result = convert_file(source, tmp_path)
    assert result.name == "Größe 日本 (2).elf"
    assert result.read_bytes() == expected
    assert original.read_bytes() == b"keep me"


def test_elf_extension_never_overwrites_source(tmp_path):
    source, expected = write_fixture(tmp_path, "sample.elf")
    before = source.read_bytes()
    result = convert_file(source, tmp_path)
    assert result.name == "sample (2).elf"
    assert result.read_bytes() == expected
    assert source.read_bytes() == before


def test_hardlinked_output_never_modifies_source(tmp_path):
    source, expected = write_fixture(tmp_path)
    os.link(source, tmp_path / "sample.elf")
    before = source.read_bytes()
    result = convert_file(source, tmp_path)
    assert result.read_bytes() == expected
    assert source.read_bytes() == before


@pytest.mark.parametrize("change, message", [
    (lambda b: b.__setitem__(slice(0, 4), b"NOPE"), "SELF"),
    (lambda b: b.__setitem__(6, 2), "endian"),
    (lambda b: struct.pack_into("<H", b, 24, 0), "entries"),
    (lambda b: struct.pack_into("<Q", b, 64, 0x2806), "encrypted"),
    (lambda b: struct.pack_into("<Q", b, 64, 0x280C), "compressed"),
    (lambda b: struct.pack_into("<Q", b, 72, len(b) + 1), "outside"),
    (lambda b: struct.pack_into("<Q", b, 64, (99 << 20) | 0x2804), "index"),
    (lambda b: struct.pack_into("<Q", b, 128, 0x2804), "Duplicate"),
    (lambda b: b.__setitem__(164, 1), "ELF64"),
    (lambda b: struct.pack_into("<H", b, 220, 1), "section"),
    (lambda b: struct.pack_into("<Q", b, 232, 1 << 40), "large"),
    (lambda b: struct.pack_into("<Q", b, 256, 7), "size"),
])
def test_invalid_input_has_no_output(tmp_path, change, message):
    wrapped, _ = fake_self()
    damaged = bytearray(wrapped)
    change(damaged)
    source = tmp_path / "invalid.self"
    source.write_bytes(damaged)
    with pytest.raises(ConversionError, match=message):
        convert_file(source, tmp_path)
    assert list(tmp_path.iterdir()) == [source]
    assert source.read_bytes() == damaged


@pytest.mark.parametrize("length", [0, 4, 31, 80, 170, 300, 900])
def test_truncated_inputs_fail_cleanly(tmp_path, length):
    wrapped, _ = fake_self()
    source = tmp_path / "short.self"
    source.write_bytes(wrapped[:length])
    with pytest.raises(ConversionError):
        convert_file(source, tmp_path)
    assert list(tmp_path.iterdir()) == [source]


def test_already_elf_has_actionable_error(tmp_path):
    _, expected = fake_self()
    source = tmp_path / "ready.elf"
    source.write_bytes(expected)
    with pytest.raises(ConversionError, match="already an ELF"):
        convert_file(source, tmp_path)


def test_cancellation_cleans_partial_output(tmp_path):
    source, _ = write_fixture(tmp_path, payloads=(b"x" * (2 * 1024 * 1024),))
    copied = []
    with pytest.raises(ConversionCancelled):
        convert_file(source, tmp_path, cancel=lambda: bool(copied),
                     progress=lambda current, total: copied.append(current))
    assert list(tmp_path.iterdir()) == [source]


def test_progress_reaches_total(tmp_path):
    source, _ = write_fixture(tmp_path)
    calls = []
    convert_file(source, tmp_path, progress=lambda done, total: calls.append((done, total)))
    assert calls[-1] == (16, 16)
    assert [done for done, total in calls] == sorted(done for done, total in calls)


def test_output_directory_must_exist(tmp_path):
    source, _ = write_fixture(tmp_path)
    with pytest.raises(ConversionError, match="folder"):
        convert_file(source, tmp_path / "missing")


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("trailer_in_size", [False, True])
def test_preserves_sce_library_version_trailer(tmp_path, reverse, trailer_in_size):
    source, expected = write_fixture(tmp_path, reverse=reverse,
                                      version_tail=b"Library version metadata" * 3,
                                      trailer_in_size=trailer_in_size)
    output = convert_file(source, tmp_path)
    assert output.read_bytes() == expected


def test_missing_version_trailer_is_rejected(tmp_path):
    wrapped, _ = fake_self(version_tail=b"version" * 8)
    source = tmp_path / "short-version.self"
    source.write_bytes(wrapped[:-32])
    with pytest.raises(ConversionError, match="version"):
        convert_file(source, tmp_path)
    assert list(tmp_path.iterdir()) == [source]


@pytest.mark.parametrize("missing", range(1, 16))
@pytest.mark.parametrize("trailer_in_size", [False, True])
def test_short_trailer_truncation_cannot_shift_into_padding(tmp_path, missing, trailer_in_size):
    wrapped, _ = fake_self(version_tail=b"library-version-test", trailer_in_size=trailer_in_size)
    source = tmp_path / "truncated.self"
    source.write_bytes(wrapped[:-missing])
    with pytest.raises(ConversionError):
        convert_file(source, tmp_path)
    assert list(tmp_path.iterdir()) == [source]
