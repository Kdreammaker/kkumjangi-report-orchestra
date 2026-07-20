"""Small stdlib Compound File Binary reader for HWP analysis."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .resource_limits import read_file_bounded


CFB_MAGIC = bytes.fromhex("d0 cf 11 e0 a1 b1 1a e1")
FREE_SECTOR = 0xFFFFFFFF
END_OF_CHAIN = 0xFFFFFFFE
FAT_SECTOR = 0xFFFFFFFD
DIFAT_SECTOR = 0xFFFFFFFC
NO_STREAM = 0xFFFFFFFF


class CompoundFileError(ValueError):
    """Raised when the CFB container cannot be read safely."""


@dataclass(frozen=True)
class DirectoryEntry:
    index: int
    name: str
    object_type: int
    left: int
    right: int
    child: int
    start_sector: int
    stream_size: int

    @property
    def is_storage(self) -> bool:
        return self.object_type in {1, 5}

    @property
    def is_stream(self) -> bool:
        return self.object_type == 2


class CompoundFile:
    """Read enough OLE CFB to inspect HWP 5.x streams."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.sector_size = 0
        self.mini_sector_size = 0
        self.mini_stream_cutoff = 0
        self.first_directory_sector = END_OF_CHAIN
        self.first_mini_fat_sector = END_OF_CHAIN
        self.num_mini_fat_sectors = 0
        self.fat: list[int] = []
        self.mini_fat: list[int] = []
        self.directory_entries: list[DirectoryEntry] = []
        self.streams: dict[str, DirectoryEntry] = {}
        self.root_entry: DirectoryEntry | None = None
        self.root_mini_stream = b""
        self._parse()

    @classmethod
    def from_path(cls, path: Path) -> "CompoundFile":
        return cls(read_file_bounded(path))

    def list_stream_paths(self) -> list[str]:
        return sorted(self.streams)

    def read_stream(self, path: str) -> bytes:
        entry = self.streams[path]
        if entry.stream_size < self.mini_stream_cutoff and self.root_mini_stream:
            return self._read_mini_stream(entry.start_sector, entry.stream_size)
        return self._read_regular_stream(entry.start_sector, entry.stream_size)

    def _parse(self) -> None:
        if len(self.data) < 512 or self.data[:8] != CFB_MAGIC:
            raise CompoundFileError("not_ole_cfb")

        sector_shift = _u16(self.data, 30)
        mini_sector_shift = _u16(self.data, 32)
        self.sector_size = 1 << sector_shift
        self.mini_sector_size = 1 << mini_sector_shift
        if self.sector_size not in {512, 4096}:
            raise CompoundFileError("unsupported_sector_size")
        if self.mini_sector_size != 64:
            raise CompoundFileError("unsupported_mini_sector_size")

        num_fat_sectors = _u32(self.data, 44)
        self.first_directory_sector = _u32(self.data, 48)
        self.mini_stream_cutoff = _u32(self.data, 56)
        self.first_mini_fat_sector = _u32(self.data, 60)
        self.num_mini_fat_sectors = _u32(self.data, 64)
        first_difat_sector = _u32(self.data, 68)
        num_difat_sectors = _u32(self.data, 72)

        difat = [_u32(self.data, 76 + (index * 4)) for index in range(109)]
        difat = [sector for sector in difat if sector not in {FREE_SECTOR, END_OF_CHAIN}]
        difat.extend(self._read_difat_chain(first_difat_sector, num_difat_sectors))
        fat_sector_ids = difat[:num_fat_sectors]
        self.fat = self._read_fat(fat_sector_ids)
        self.directory_entries = self._read_directory()
        self.root_entry = self.directory_entries[0] if self.directory_entries else None
        if self.root_entry and self.root_entry.start_sector != END_OF_CHAIN:
            self.root_mini_stream = self._read_regular_stream(
                self.root_entry.start_sector,
                self.root_entry.stream_size,
            )
        self.mini_fat = self._read_mini_fat()
        self.streams = self._build_stream_paths()

    def _read_sector(self, sector_id: int) -> bytes:
        if sector_id in {FREE_SECTOR, END_OF_CHAIN, FAT_SECTOR, DIFAT_SECTOR, NO_STREAM}:
            raise CompoundFileError("invalid_sector_id")
        offset = (sector_id + 1) * self.sector_size
        end = offset + self.sector_size
        if offset < 0 or end > len(self.data):
            raise CompoundFileError("sector_out_of_range")
        return self.data[offset:end]

    def _read_difat_chain(self, first_sector: int, count: int) -> list[int]:
        if count == 0 or first_sector in {END_OF_CHAIN, FREE_SECTOR, NO_STREAM}:
            return []
        result: list[int] = []
        sector_id = first_sector
        seen: set[int] = set()
        entries_per_sector = (self.sector_size // 4) - 1
        maximum_sector_count = max(0, (len(self.data) // self.sector_size) - 1)
        for _ in range(min(count, maximum_sector_count)):
            if sector_id in seen:
                raise CompoundFileError("difat_chain_loop")
            seen.add(sector_id)
            payload = self._read_sector(sector_id)
            for index in range(entries_per_sector):
                value = _u32(payload, index * 4)
                if value not in {FREE_SECTOR, END_OF_CHAIN}:
                    result.append(value)
            sector_id = _u32(payload, entries_per_sector * 4)
            if sector_id in {END_OF_CHAIN, FREE_SECTOR, NO_STREAM}:
                break
        return result

    def _read_fat(self, fat_sector_ids: list[int]) -> list[int]:
        entries: list[int] = []
        for sector_id in fat_sector_ids:
            payload = self._read_sector(sector_id)
            entries.extend(_u32(payload, offset) for offset in range(0, len(payload), 4))
        return entries

    def _sector_chain(self, start_sector: int) -> list[int]:
        if start_sector in {END_OF_CHAIN, FREE_SECTOR, NO_STREAM}:
            return []
        chain: list[int] = []
        seen: set[int] = set()
        sector_id = start_sector
        while sector_id not in {END_OF_CHAIN, FREE_SECTOR, NO_STREAM}:
            if sector_id in seen:
                raise CompoundFileError("sector_chain_loop")
            if sector_id >= len(self.fat):
                raise CompoundFileError("fat_chain_out_of_range")
            seen.add(sector_id)
            chain.append(sector_id)
            sector_id = self.fat[sector_id]
        return chain

    def _read_regular_stream(self, start_sector: int, stream_size: int) -> bytes:
        payload = b"".join(self._read_sector(sector_id) for sector_id in self._sector_chain(start_sector))
        return payload[:stream_size]

    def _read_mini_fat(self) -> list[int]:
        if self.num_mini_fat_sectors == 0 or self.first_mini_fat_sector in {END_OF_CHAIN, FREE_SECTOR}:
            return []
        payload = self._read_regular_stream(
            self.first_mini_fat_sector,
            self.num_mini_fat_sectors * self.sector_size,
        )
        return [_u32(payload, offset) for offset in range(0, len(payload), 4)]

    def _read_mini_stream(self, start_sector: int, stream_size: int) -> bytes:
        if start_sector in {END_OF_CHAIN, FREE_SECTOR, NO_STREAM}:
            return b""
        chunks: list[bytes] = []
        seen: set[int] = set()
        sector_id = start_sector
        while sector_id not in {END_OF_CHAIN, FREE_SECTOR, NO_STREAM}:
            if sector_id in seen:
                raise CompoundFileError("mini_chain_loop")
            if sector_id >= len(self.mini_fat):
                raise CompoundFileError("mini_fat_chain_out_of_range")
            offset = sector_id * self.mini_sector_size
            end = offset + self.mini_sector_size
            if end > len(self.root_mini_stream):
                raise CompoundFileError("mini_stream_out_of_range")
            seen.add(sector_id)
            chunks.append(self.root_mini_stream[offset:end])
            sector_id = self.mini_fat[sector_id]
        return b"".join(chunks)[:stream_size]

    def _read_directory(self) -> list[DirectoryEntry]:
        payload = self._read_regular_stream(self.first_directory_sector, len(self.fat) * self.sector_size)
        entries: list[DirectoryEntry] = []
        for index, offset in enumerate(range(0, len(payload), 128)):
            chunk = payload[offset : offset + 128]
            if len(chunk) < 128:
                break
            object_type = chunk[66]
            if object_type == 0:
                continue
            name_len = _u16(chunk, 64)
            name_bytes = chunk[: max(0, name_len - 2)]
            name = name_bytes.decode("utf-16le", errors="replace")
            entries.append(
                DirectoryEntry(
                    index=index,
                    name=name,
                    object_type=object_type,
                    left=_u32(chunk, 68),
                    right=_u32(chunk, 72),
                    child=_u32(chunk, 76),
                    start_sector=_u32(chunk, 116),
                    stream_size=_u64(chunk, 120),
                )
            )
        return entries

    def _entry_by_index(self, index: int) -> DirectoryEntry | None:
        for entry in self.directory_entries:
            if entry.index == index:
                return entry
        return None

    def _collect_sibling_tree(self, index: int, visited: set[int]) -> list[DirectoryEntry]:
        result: list[DirectoryEntry] = []
        stack: list[tuple[int, bool]] = [(index, False)]
        while stack:
            current, emit = stack.pop()
            if current in {NO_STREAM, END_OF_CHAIN, FREE_SECTOR}:
                continue
            entry = self._entry_by_index(current)
            if entry is None:
                continue
            if emit:
                result.append(entry)
                continue
            if current in visited:
                continue
            visited.add(current)
            stack.append((entry.right, False))
            stack.append((current, True))
            stack.append((entry.left, False))
        return result

    def _build_stream_paths(self) -> dict[str, DirectoryEntry]:
        if not self.root_entry:
            return {}
        streams: dict[str, DirectoryEntry] = {}

        def visit_children(parent: DirectoryEntry, prefix: list[str]) -> None:
            for child in self._collect_sibling_tree(parent.child, set()):
                next_prefix = prefix + [child.name]
                if child.is_stream:
                    streams["/".join(next_prefix)] = child
                elif child.is_storage:
                    visit_children(child, next_prefix)

        visit_children(self.root_entry, [])
        return streams


def _u16(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<H", payload, offset)[0]


def _u32(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<I", payload, offset)[0]


def _u64(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", payload, offset)[0]
