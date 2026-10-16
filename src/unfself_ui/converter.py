"""PS4 SELF reconstruction, based on SocraticBliss' ps4_unfself (GPL-3.0).

Original research credits: SocraticBliss, Znullptr, flatz and zecoxao.
The index-based, validated streaming implementation is maintained by murums.
"""

import os
import struct
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

SELF_MAGIC = b"\x4f\x15\x3d\x1d"
CHUNK_SIZE = 1024 * 1024
MAX_OUTPUT_SIZE = 4 * 1024**3


class ConversionError(Exception):
    """The input cannot be converted safely."""


class ConversionCancelled(Exception):
    """The user cancelled the current conversion."""


@dataclass(frozen=True)
class Segment:
    source_offset: int
    output_offset: int
    size: int


@dataclass(frozen=True)
class Layout:
    headers: bytes
    segments: tuple[Segment, ...]
    output_size: int


def read_at(stream: BinaryIO, offset: int, size: int, file_size: int) -> bytes:
    if offset < 0 or size < 0 or offset + size > file_size:
        raise ConversionError("A header or segment points outside the input file.")
    stream.seek(offset)
    data = stream.read(size)
    if len(data) != size:
        raise ConversionError("Input truncated or changed while reading.")
    return data


def inspect_layout(stream: BinaryIO, file_size: int) -> Layout:
    header = read_at(stream, 0, 32, file_size)
    if header[:4] == b"\x7fELF":
        raise ConversionError("File is already an ELF; no conversion needed.")
    if header[:4] != SELF_MAGIC:
        raise ConversionError("Not a PS4 SELF. Choose a fake-signed file.")
    if header[6] != 1:
        raise ConversionError("Only little-endian SELF files are supported.")
    header_size, metadata_size = struct.unpack_from("<HH", header, 12)
    declared_file_size = struct.unpack_from("<Q", header, 16)[0]
    entry_count = struct.unpack_from("<H", header, 24)[0]
    if not 1 <= entry_count <= 4096:
        raise ConversionError("Invalid or unsupported SELF entries count.")
    elf_offset = 32 + entry_count * 32
    elf_header = read_at(stream, elf_offset, 64, file_size)
    if elf_header[:7] != b"\x7fELF\x02\x01\x01":
        raise ConversionError("Only ELF64 little-endian version 1 is supported.")
    fields = struct.unpack("<16sHHIQQQIHHHHHH", elf_header)
    if fields[2] != 0x3E or fields[3] != 1 or fields[8] != 64:
        raise ConversionError("The embedded ELF header is not a supported x86-64 executable.")
    ph_offset, ph_size, ph_count = fields[5], fields[9], fields[10]
    if ph_offset != 64 or ph_size != 56 or not 1 <= ph_count <= 4096:
        raise ConversionError("Unsupported ELF program-header layout.")
    if fields[6] or fields[12] or fields[13]:
        raise ConversionError("Unsupported ELF section tables. Use a stripped fake-signed SELF.")
    header_end = elf_offset + 64 + ph_count * 56
    if header_size < header_end or header_size + metadata_size > file_size:
        raise ConversionError("The SELF header or metadata extends outside the input file.")
    program_bytes = read_at(stream, elf_offset + 64, ph_count * 56, file_size)
    programs = list(struct.iter_unpack("<IIQQQQQQ", program_bytes))
    headers = elf_header + program_bytes
    mapped = {}
    data_end = header_size + metadata_size
    for index in range(entry_count):
        properties, offset, size, memory_size = struct.unpack(
            "<QQQQ", read_at(stream, 32 + index * 32, 32, file_size))
        if properties & 2:
            raise ConversionError("SELF contains encrypted data; decryption is unsupported.")
        if properties & 8:
            raise ConversionError("SELF contains unsupported compressed data.")
        if offset + size > file_size or (size and offset < header_size + metadata_size):
            raise ConversionError("A SELF segment points outside its data area.")
        data_end = max(data_end, offset + size)
        if not properties & 0x800:
            continue
        program_index = (properties >> 20) & 0xFFFF
        if program_index >= ph_count:
            raise ConversionError("A SELF segment has an invalid program-header index.")
        if program_index in mapped:
            raise ConversionError("Duplicate SELF data entries reference the same ELF segment.")
        program = programs[program_index]
        if size != program[5] or memory_size != size:
            raise ConversionError("The SELF segment size does not match its ELF program header.")
        mapped[program_index] = Segment(offset, program[2], size)
    if not mapped:
        raise ConversionError("No uncompressed ELF data segments were found.")
    version_programs = [(index, program) for index, program in enumerate(programs)
                        if program[0] == 0x6FFFFF01 and program[5] and index not in mapped]
    if len(version_programs) > 1:
        raise ConversionError("Multiple unmapped library-version segments are not supported.")
    for index, program in version_programs:
        trailer_offset = file_size - program[5]
        # Some SELF writers exclude this trailer from the declared file length.
        if declared_file_size not in (file_size, trailer_offset):
            raise ConversionError("The SELF file length does not match its declared library-version trailer extent.")
        padding_size = trailer_offset - data_end
        if trailer_offset not in (data_end, (data_end + 15) & ~15):
            raise ConversionError("The library-version trailer is missing or has an unsupported layout.")
        if any(read_at(stream, data_end, padding_size, file_size)):
            raise ConversionError("Unexpected bytes before the library-version trailer.")
        mapped[index] = Segment(trailer_offset, program[2], program[5])
    segments = tuple(sorted(mapped.values(), key=lambda segment: segment.output_offset))
    output_size = max(len(headers), *(s.output_offset + s.size for s in segments))
    if output_size > min(MAX_OUTPUT_SIZE, max(64 * 1024**2, file_size * 16)):
        raise ConversionError("The reconstructed ELF is too large or has unreasonable segment offsets.")
    previous_end = 0
    for segment in segments:
        if segment.size and segment.output_offset < previous_end:
            raise ConversionError("ELF data segments overlap; this layout cannot be reconstructed safely.")
        previous_end = max(previous_end, segment.output_offset + segment.size)
        overlap = min(segment.size, len(headers) - segment.output_offset)
        if overlap > 0:
            data = read_at(stream, segment.source_offset, overlap, file_size)
            if data != headers[segment.output_offset:segment.output_offset + overlap]:
                raise ConversionError("A data segment conflicts with the embedded ELF headers.")
    covered = [(0, len(headers))] + [(s.output_offset, s.output_offset + s.size) for s in segments]
    for index, program in enumerate(programs):
        kind, _, offset, _, _, size, memory_size, alignment = program
        if kind == 1 and size > memory_size:
            raise ConversionError("An ELF load segment has an invalid memory size.")
        if index in mapped or not size or kind == 0:
            continue
        if not any(start <= offset and offset + size <= end for start, end in covered):
            raise ConversionError(f"ELF segment {index} has no corresponding SELF data; unsupported layout.")
    return Layout(headers, segments, output_size)


def publish_output(temporary: Path, source: Path, output_dir: Path) -> Path:
    number = 1
    while True:
        suffix = "" if number == 1 else f" ({number})"
        destination = output_dir / f"{source.stem}{suffix}.elf"
        try:
            if os.name == "nt":
                # Windows rename fails if the target exists, including a concurrent creator.
                os.rename(temporary, destination)
            else:
                os.link(temporary, destination)
                temporary.unlink()
            return destination
        except FileExistsError:
            number += 1


def convert_file(
    source: Path,
    output_dir: Path,
    cancel: Callable[[], bool] = lambda: False,
    progress: Callable[[int, int], None] = lambda done, total: None,
) -> Path:
    source, output_dir = Path(source), Path(output_dir)
    temporary = None
    try:
        if not output_dir.is_dir():
            raise ConversionError("Choose an existing output folder.")
        with source.open("rb") as input_file:
            initial_stat = os.fstat(input_file.fileno())
            layout = inspect_layout(input_file, initial_stat.st_size)
            if cancel():
                raise ConversionCancelled()
            total = sum(segment.size for segment in layout.segments)
            completed = 0
            with tempfile.NamedTemporaryFile(mode="w+b", prefix=".unfself-", suffix=".tmp",
                                             dir=output_dir, delete=False) as output:
                temporary = Path(output.name)
                output.truncate(layout.output_size)
                for segment in layout.segments:
                    input_file.seek(segment.source_offset)
                    output.seek(segment.output_offset)
                    remaining = segment.size
                    while remaining:
                        if cancel():
                            raise ConversionCancelled()
                        chunk = input_file.read(min(CHUNK_SIZE, remaining))
                        if not chunk:
                            raise ConversionError("The input was truncated during conversion.")
                        output.write(chunk)
                        remaining -= len(chunk)
                        completed += len(chunk)
                        progress(completed, total)
                if cancel():
                    raise ConversionCancelled()
                final_stat = os.fstat(input_file.fileno())
                if (initial_stat.st_size, initial_stat.st_mtime_ns) != (final_stat.st_size, final_stat.st_mtime_ns):
                    raise ConversionError("Input changed during conversion. Retry with a stable copy.")
                output.seek(0)
                output.write(layout.headers)
                output.flush()
                os.fsync(output.fileno())
            if cancel():
                raise ConversionCancelled()
            return publish_output(temporary, source, output_dir)
    except OSError as error:
        raise ConversionError(f"File access failed: {error.strerror or error}") from error
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
