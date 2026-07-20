"""Text extraction and public-safe fidelity metrics for owned HWP/HWPX work."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile
import re
import unicodedata

from .cfb import CompoundFile, CompoundFileError
from .hwp_profile import _decode_record_stream, _parse_records, _read_file_header
from .hwpx_profile import _is_section_entry, _local_name


HWP_INLINE_CONTROL_CODES = frozenset({4, 5, 6, 7, 8, 9, 19, 20})
HWP_EXTENDED_CONTROL_CODES = frozenset({1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23})
HWP_EIGHT_UNIT_CONTROL_CODES = HWP_INLINE_CONTROL_CODES | HWP_EXTENDED_CONTROL_CODES
HWP_CONTROL_CODE_UNIT_COUNT = 8
HWP_CHARACTER_CONTROL_NAMES = {
    0: "reserved",
    10: "line_break",
    13: "paragraph_break",
    24: "hyphen",
    25: "reserved",
    26: "reserved",
    27: "reserved",
    28: "reserved",
    29: "reserved",
    30: "group_space",
    31: "fixed_width_space",
}


def extract_hwp_text(path: Path) -> dict[str, Any]:
    """Extract HWP paragraph text for local generation use.

    The returned `paragraphs` and `text` fields may contain private source text.
    Do not copy them into public reports.
    """

    try:
        cfb = CompoundFile.from_path(path)
    except (OSError, CompoundFileError) as exc:
        return {"status": "cfb_error", "error": exc.__class__.__name__, "paragraphs": [], "text": ""}

    file_header = _read_file_header(cfb)
    compressed = bool(file_header.get("flags", {}).get("compressed"))
    section_paths = [
        item
        for item in cfb.list_stream_paths()
        if item.startswith("BodyText/Section") and item.rsplit("Section", 1)[-1].isdigit()
    ]
    paragraphs: list[dict[str, Any]] = []
    control_code_counts: Counter[str] = Counter()
    control_id_counts: Counter[str] = Counter()
    malformed_control_count = 0
    control_payload_unit_count = 0
    for section_index, section_path in enumerate(sorted(section_paths)):
        try:
            payload = cfb.read_stream(section_path)
        except (KeyError, CompoundFileError):
            continue
        decoded, compression_status = _decode_record_stream(payload, compressed)
        if compression_status == "decompress_failed":
            continue
        records, parse_status, _trailing = _parse_records(decoded)
        if parse_status not in {"parsed", "trailing_bytes"}:
            continue
        section_paragraphs: list[dict[str, Any]] = []
        latest_paragraph_by_level: dict[int, dict[str, Any]] = {}
        for record in records:
            record_level = int(record.get("level", 0))
            if record["tag_name"] == "PARA_HEADER":
                paragraph = {
                    "section_index": section_index,
                    "paragraph_index": len(section_paragraphs),
                    "record_level": record_level,
                    "text": "",
                    "tokens": [],
                    "source_to_visible": [0],
                }
                section_paragraphs.append(paragraph)
                latest_paragraph_by_level[record_level] = paragraph
                continue
            if record["tag_name"] != "PARA_TEXT":
                continue
            tokenized = tokenize_hwp_para_text(bytes(record["body"]))
            text = sanitize_display_text(str(tokenized["text"]))
            control_code_counts.update(tokenized["control_code_counts"])
            control_id_counts.update(tokenized["control_id_counts"])
            malformed_control_count += int(tokenized["malformed_control_count"])
            control_payload_unit_count += int(tokenized["control_payload_unit_count"])
            paragraph = latest_paragraph_by_level.get(record_level - 1)
            if paragraph is None:
                paragraph = {
                    "section_index": section_index,
                    "paragraph_index": len(section_paragraphs),
                    "record_level": max(0, record_level - 1),
                    "text": "",
                    "tokens": [],
                    "source_to_visible": [0],
                }
                section_paragraphs.append(paragraph)
            paragraph["text"] = str(paragraph["text"]) + text
            paragraph["tokens"] = [*paragraph["tokens"], *tokenized["tokens"]]
            paragraph["source_to_visible"] = tokenized["source_to_visible"]
        paragraphs.extend(section_paragraphs)

    joined = "\n".join(item["text"] for item in paragraphs if item["text"])
    return {
        "status": "text_extracted",
        "paragraphs": paragraphs,
        "text": joined,
        "paragraph_count": len(paragraphs),
        "text_record_count": sum(bool(item.get("tokens")) for item in paragraphs),
        "text_char_count": len(normalize_text(joined)),
        "control_summary": {
            "control_count": sum(control_code_counts.values()),
            "control_code_counts": dict(sorted(control_code_counts.items())),
            "control_id_counts": dict(sorted(control_id_counts.items())),
            "control_payload_unit_count": control_payload_unit_count,
            "malformed_control_count": malformed_control_count,
        },
    }


def extract_hwpx_text(path: Path) -> dict[str, Any]:
    """Extract text from HWPX section XML. Returned text is private evidence."""

    try:
        with ZipFile(path, "r") as package:
            section_names = sorted(name for name in package.namelist() if _is_section_entry(name))
            paragraphs: list[str] = []
            for section_name in section_names:
                root = ElementTree.fromstring(package.read(section_name))
                for paragraph in root.iter():
                    if _local_name(paragraph.tag) != "p":
                        continue
                    current: list[str] = []
                    for run in list(paragraph):
                        if _local_name(run.tag) != "run":
                            continue
                        for element in list(run):
                            if _local_name(element.tag) == "t":
                                current.append("".join(element.itertext()))
                    paragraphs.append(sanitize_display_text("".join(current)))
            joined = "\n".join(item for item in paragraphs if item)
            return {
                "status": "text_extracted",
                "paragraphs": paragraphs,
                "text": joined,
                "paragraph_count": len(paragraphs),
                "text_char_count": len(normalize_text(joined)),
            }
    except (FileNotFoundError, BadZipFile, ElementTree.ParseError) as exc:
        return {"status": "text_error", "error": exc.__class__.__name__, "paragraphs": [], "text": ""}


def compare_texts(source_text: str, target_text: str) -> dict[str, Any]:
    source = normalize_text(source_text)
    target = normalize_text(target_text)
    source_len = len(source)
    target_len = len(target)
    overlap = _char_multiset_overlap(source, target)
    source_coverage = round(overlap / source_len, 4) if source_len else (1.0 if target_len == 0 else 0.0)
    target_coverage = round(overlap / target_len, 4) if target_len else (1.0 if source_len == 0 else 0.0)
    length_ratio = round(min(source_len, target_len) / max(source_len, target_len), 4) if max(source_len, target_len) else 1.0
    return {
        "source_char_count": source_len,
        "target_char_count": target_len,
        "overlap_char_count": overlap,
        "source_coverage": source_coverage,
        "target_coverage": target_coverage,
        "length_ratio": length_ratio,
        "digest_equal": _digest(source) == _digest(target),
    }


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = re.sub(r"\s+", "", normalized)
    return normalized


def sanitize_text(text: str) -> str:
    cleaned = []
    for char in text or "":
        if char in {"\n", "\t", "\r"}:
            cleaned.append(char)
            continue
        category = unicodedata.category(char)
        if category.startswith("C"):
            continue
        cleaned.append(char)
    return re.sub(r"[ \t\r\f\v]+", " ", "".join(cleaned)).strip()


def sanitize_display_text(text: str) -> str:
    """Preserve layout-significant whitespace while removing XML-invalid code points."""

    return "".join(
        char
        for char in text or ""
        if char in {"\n", "\t", "\r"}
        or 0x20 <= ord(char) <= 0xD7FF
        or 0xE000 <= ord(char) <= 0xFFFD
        or 0x10000 <= ord(char) <= 0x10FFFF
    )


def tokenize_hwp_para_text(payload: bytes) -> dict[str, Any]:
    """Decode visible text while retaining typed HWP control placeholders.

    HWP 5.x inline and extended controls occupy eight UTF-16 code units. Their
    payload bytes can resemble printable text and must be skipped atomically.
    """

    even_payload = payload[: len(payload) - (len(payload) % 2)]
    units = [
        int.from_bytes(even_payload[offset : offset + 2], "little")
        for offset in range(0, len(even_payload), 2)
    ]
    tokens: list[dict[str, Any]] = []
    visible_units: list[int] = []
    text_units: list[int] = []
    control_code_counts: Counter[str] = Counter()
    control_id_counts: Counter[str] = Counter()
    control_payload_unit_count = 0
    malformed_control_count = 0
    source_to_visible = [0 for _ in range(len(units) + 1)]
    visible_position = 0
    text_source_start = 0
    text_visible_start = 0

    def flush_text(source_end: int) -> None:
        nonlocal text_source_start, text_visible_start
        if not text_units:
            return
        text = _decode_utf16_units(text_units)
        if text:
            tokens.append(
                {
                    "type": "text",
                    "text": text,
                    "source_start": text_source_start,
                    "source_end": source_end,
                    "visible_start": text_visible_start,
                    "visible_end": visible_position,
                }
            )
        visible_units.extend(text_units)
        text_units.clear()

    index = 0
    while index < len(units):
        code = units[index]
        if code in HWP_EIGHT_UNIT_CONTROL_CODES:
            flush_text(index)
            if index + HWP_CONTROL_CODE_UNIT_COUNT > len(units):
                malformed_control_count += 1
                control_code_counts[f"{code}:malformed"] += 1
                tokens.append(
                    {
                        "type": "control",
                        "control_class": "malformed",
                        "code": code,
                        "control_id": "unknown",
                        "source_start": index,
                        "source_end": len(units),
                        "visible_start": visible_position,
                        "visible_end": visible_position,
                    }
                )
                for boundary in range(index, len(units) + 1):
                    source_to_visible[boundary] = visible_position
                break
            control_units = units[index : index + HWP_CONTROL_CODE_UNIT_COUNT]
            control_id = _control_id_from_units(code, control_units)
            control_class = "inline" if code in HWP_INLINE_CONTROL_CODES else "extended"
            control_code_counts[f"{code}:{control_class}"] += 1
            if control_id != "unknown":
                control_id_counts[control_id] += 1
            tokens.append(
                {
                    "type": "control",
                    "control_class": control_class,
                    "code": code,
                    "control_id": control_id,
                    **_inline_control_semantics(code, control_units),
                    "source_start": index,
                    "source_end": index + HWP_CONTROL_CODE_UNIT_COUNT,
                    "visible_start": visible_position,
                    "visible_end": visible_position,
                }
            )
            for boundary in range(index, index + HWP_CONTROL_CODE_UNIT_COUNT + 1):
                source_to_visible[boundary] = visible_position
            control_payload_unit_count += HWP_CONTROL_CODE_UNIT_COUNT - 1
            index += HWP_CONTROL_CODE_UNIT_COUNT
            continue

        if code < 32:
            flush_text(index)
            control_name = HWP_CHARACTER_CONTROL_NAMES.get(code, "reserved")
            control_code_counts[f"{code}:character"] += 1
            visible_start = visible_position
            is_visible_control = code == 10 or code in {30, 31}
            if is_visible_control:
                visible_position += 1
            tokens.append(
                {
                    "type": "control",
                    "control_class": "character",
                    "code": code,
                    "control_id": control_name,
                    "source_start": index,
                    "source_end": index + 1,
                    "visible_start": visible_start,
                    "visible_end": visible_position,
                }
            )
            if code == 10:
                visible_units.append(ord("\n"))
            elif code in {30, 31}:
                visible_units.append(ord(" "))
            source_to_visible[index] = visible_start
            source_to_visible[index + 1] = visible_position
            index += 1
            continue

        if not text_units:
            text_source_start = index
            text_visible_start = visible_position
        source_to_visible[index] = visible_position
        if 0xD800 <= code <= 0xDBFF and index + 1 < len(units) and 0xDC00 <= units[index + 1] <= 0xDFFF:
            text_units.extend((code, units[index + 1]))
            source_to_visible[index + 1] = visible_position
            visible_position += 1
            source_to_visible[index + 2] = visible_position
            index += 2
        else:
            text_units.append(code)
            visible_position += 1
            source_to_visible[index + 1] = visible_position
            index += 1

    flush_text(len(units))
    return {
        "text": _decode_utf16_units(visible_units),
        "tokens": tokens,
        "control_code_counts": dict(sorted(control_code_counts.items())),
        "control_id_counts": dict(sorted(control_id_counts.items())),
        "control_payload_unit_count": control_payload_unit_count,
        "malformed_control_count": malformed_control_count,
        "source_unit_count": len(units),
        "visible_char_count": visible_position,
        "source_to_visible": source_to_visible,
    }


def _decode_hwp_para_text(payload: bytes) -> str:
    return str(tokenize_hwp_para_text(payload)["text"])


def _decode_utf16_units(units: list[int]) -> str:
    if not units:
        return ""
    payload = b"".join(int(unit).to_bytes(2, "little") for unit in units)
    return payload.decode("utf-16le", errors="ignore")


def _control_id_from_units(code: int, units: list[int]) -> str:
    if code not in HWP_EXTENDED_CONTROL_CODES or len(units) < 3:
        return "unknown"
    payload = b"".join(int(unit).to_bytes(2, "little") for unit in units[1:3])
    if not payload:
        return "unknown"
    return "".join(chr(value) if 32 <= value < 127 else f"\\x{value:02x}" for value in payload)


def _inline_control_semantics(code: int, units: list[int]) -> dict[str, int]:
    if code != 9 or len(units) < HWP_CONTROL_CODE_UNIT_COUNT:
        return {}
    return {
        "tab_width": int(units[1]) | (int(units[2]) << 16),
        "tab_leader": int(units[3]) & 0xFF,
        "tab_type": (int(units[3]) >> 8) & 0xFF,
    }


def _char_multiset_overlap(left: str, right: str) -> int:
    left_counter = Counter(left)
    right_counter = Counter(right)
    return sum((left_counter & right_counter).values())


def _digest(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()
