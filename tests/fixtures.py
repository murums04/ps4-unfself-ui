"""Synthetic binary fixtures, with independently specified expected ELF bytes."""

import struct
from pathlib import Path


def fake_self(*, reverse=False, payloads=(b"CODE1234", b"DATA5678"), version_tail=b"", trailer_in_size=True):
    count = len(payloads)
    program_count = count + bool(version_tail)
    identity = b"\x7fELF\x02\x01\x01\x09" + bytes(8)
    elf_header = struct.pack(
        "<16sHHIQQQIHHHHHH", identity, 0xFE00, 0x3E, 1, 0x400100,
        64, 0, 0, 64, 56, program_count, 0, 0, 0,
    )
    program_headers = b"".join(
        struct.pack("<IIQQQQQQ", 1, 5 if i == 0 else 6, 0x200 + i * 0x1000,
                    0x400200 + i * 0x1000, 0, len(data), len(data) + 16, 0x1000)
        for i, data in enumerate(payloads)
    )
    segment_end = 0x200 + (count - 1) * 0x1000 + len(payloads[-1])
    version_offset = (segment_end + 15) & ~15
    if version_tail:
        program_headers += struct.pack("<IIQQQQQQ", 0x6FFFFF01, 0, version_offset,
                                        0, 0, len(version_tail), 0, 16)
    expected = bytearray(version_offset + len(version_tail) if version_tail else segment_end)
    expected[:64] = elf_header
    expected[64:64 + len(program_headers)] = program_headers
    for i, data in enumerate(payloads):
        expected[0x200 + i * 0x1000:0x200 + i * 0x1000 + len(data)] = data
    if version_tail:
        expected[version_offset:] = version_tail

    header_size = (32 + count * 64 + 64 + program_count * 56 + 15) & ~15
    header_size += 112
    metadata_size = count * 2 * 80 + 80 + 256
    data_start = header_size + metadata_size
    entries, blocks = [], bytearray()
    for i, data in enumerate(payloads):
        metadata_offset = data_start + len(blocks)
        blocks.extend(bytes(32))
        entries.append(struct.pack("<QQQQ", 0x10004 | ((2 * i + 1) << 20),
                                   metadata_offset, 32, 32))
        data_offset = data_start + len(blocks)
        entries.append(struct.pack("<QQQQ", 0x2804 | (i << 20), data_offset,
                                   len(data), len(data)))
        blocks.extend(data)
        blocks.extend(bytes(-len(blocks) % 16))
    if reverse:
        entries.reverse()
    blocks.extend(version_tail)
    wrapped = bytearray(data_start + len(blocks))
    declared_size = len(wrapped) if trailer_in_size else len(wrapped) - len(version_tail)
    wrapped[:32] = struct.pack("<4sBBBBIHHQHH4x", b"\x4f\x15\x3d\x1d",
                               0, 1, 1, 0x12, 0x101, header_size,
                               metadata_size, declared_size, count * 2, 0x22)
    wrapped[32:32 + len(entries) * 32] = b"".join(entries)
    elf_start = 32 + len(entries) * 32
    wrapped[elf_start:elf_start + 64 + program_count * 56] = elf_header + program_headers
    ext_start = (elf_start + 64 + program_count * 56 + 15) & ~15
    wrapped[ext_start:ext_start + 64] = struct.pack("<QQQQ32s", 0x3100000000000001,
                                                  1, 0, 0, bytes(32))
    wrapped[data_start:] = blocks
    return bytes(wrapped), bytes(expected)


def write_fixture(folder: Path, name="sample.self", **options):
    wrapped, expected = fake_self(**options)
    source = folder / name
    source.write_bytes(wrapped)
    return source, expected

