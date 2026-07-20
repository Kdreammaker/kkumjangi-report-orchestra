"""Owned HWP 5.x structural profile without raw text extraction."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import struct
import zlib

from .border_fill_semantics import parse_hwp_border_fill_records
from .cfb import CompoundFile, CompoundFileError
from .compose_control_semantics import parse_hwp_compose_control_body
from .footnote_control_semantics import (
    parse_hwp_footnote_auto_number_body,
    parse_hwp_footnote_control_body,
)
from .list_section_semantics import parse_hwp_list_records, parse_hwp_section_records
from .line_segment_semantics import (
    build_hwp_line_segment_semantics,
    parse_hwp_line_segment_body,
)
from .object_binary_semantics import parse_hwp_binary_records, parse_hwp_object_records
from .page_hiding_semantics import parse_hwp_page_hiding_control_body
from .resource_limits import ResourceLimitError, decompress_bounded
from .style_semantics import parse_hwp_style_records
from .table_semantics import parse_hwp_table_records


HWPTAG_BEGIN = 0x010
HWP_SIGNATURE = b"HWP Document File"

TAG_NAMES = {
    HWPTAG_BEGIN + 0: "DOCUMENT_PROPERTIES",
    HWPTAG_BEGIN + 1: "ID_MAPPINGS",
    HWPTAG_BEGIN + 2: "BIN_DATA",
    HWPTAG_BEGIN + 3: "FACE_NAME",
    HWPTAG_BEGIN + 4: "BORDER_FILL",
    HWPTAG_BEGIN + 5: "CHAR_SHAPE",
    HWPTAG_BEGIN + 6: "TAB_DEF",
    HWPTAG_BEGIN + 7: "NUMBERING",
    HWPTAG_BEGIN + 8: "BULLET",
    HWPTAG_BEGIN + 9: "PARA_SHAPE",
    HWPTAG_BEGIN + 10: "STYLE",
    HWPTAG_BEGIN + 11: "DOC_DATA",
    HWPTAG_BEGIN + 12: "DISTRIBUTE_DOC_DATA",
    HWPTAG_BEGIN + 14: "COMPATIBLE_DOCUMENT",
    HWPTAG_BEGIN + 15: "LAYOUT_COMPATIBILITY",
    HWPTAG_BEGIN + 50: "PARA_HEADER",
    HWPTAG_BEGIN + 51: "PARA_TEXT",
    HWPTAG_BEGIN + 52: "PARA_CHAR_SHAPE",
    HWPTAG_BEGIN + 53: "PARA_LINE_SEG",
    HWPTAG_BEGIN + 54: "PARA_RANGE_TAG",
    HWPTAG_BEGIN + 55: "CTRL_HEADER",
    HWPTAG_BEGIN + 56: "LIST_HEADER",
    HWPTAG_BEGIN + 57: "PAGE_DEF",
    HWPTAG_BEGIN + 58: "FOOTNOTE_SHAPE",
    HWPTAG_BEGIN + 59: "PAGE_BORDER_FILL",
    HWPTAG_BEGIN + 60: "SHAPE_COMPONENT",
    HWPTAG_BEGIN + 61: "TABLE",
    HWPTAG_BEGIN + 62: "SHAPE_COMPONENT_LINE",
    HWPTAG_BEGIN + 63: "SHAPE_COMPONENT_RECTANGLE",
    HWPTAG_BEGIN + 64: "SHAPE_COMPONENT_ELLIPSE",
    HWPTAG_BEGIN + 65: "SHAPE_COMPONENT_ARC",
    HWPTAG_BEGIN + 66: "SHAPE_COMPONENT_POLYGON",
    HWPTAG_BEGIN + 67: "SHAPE_COMPONENT_CURVE",
    HWPTAG_BEGIN + 68: "SHAPE_COMPONENT_OLE",
    HWPTAG_BEGIN + 69: "SHAPE_COMPONENT_PICTURE",
    HWPTAG_BEGIN + 70: "SHAPE_COMPONENT_CONTAINER",
    HWPTAG_BEGIN + 71: "CTRL_DATA",
    HWPTAG_BEGIN + 72: "EQEDIT",
    HWPTAG_BEGIN + 74: "SHAPE_COMPONENT_TEXTART",
    HWPTAG_BEGIN + 75: "FORM_OBJECT",
    HWPTAG_BEGIN + 76: "MEMO_SHAPE",
    HWPTAG_BEGIN + 77: "MEMO_LIST",
    HWPTAG_BEGIN + 79: "CHART_DATA",
    HWPTAG_BEGIN + 82: "VIDEO_DATA",
    HWPTAG_BEGIN + 99: "SHAPE_COMPONENT_UNKNOWN",
}

ID_MAPPING_LABELS = (
    "bin_data",
    "face_name_hangul",
    "face_name_latin",
    "face_name_hanja",
    "face_name_japanese",
    "face_name_other",
    "face_name_symbol",
    "face_name_user",
    "border_fill",
    "char_shape",
    "tab_def",
    "numbering",
    "bullet",
    "para_shape",
    "style",
    "memo_shape",
    "track_change",
    "track_change_author",
)

FLAG_NAMES = {
    0: "compressed",
    1: "password_encrypted",
    2: "distributable",
    3: "script",
    4: "drm",
    5: "xml_template",
    6: "document_history",
    7: "electronic_signature",
    8: "certificate_encrypted",
    9: "spare_signature",
    10: "drm_certificate",
    11: "ccl",
    12: "mobile_optimized",
    13: "privacy_security",
    14: "track_changes",
    15: "kogl",
    16: "video_control",
    17: "order_field",
}

CONTROL_ID_TO_LAYOUT_CHILDREN = {
    "dhgp": ("pageHiding",),
    "pngp": ("pageNum",),
    "onwn": ("newNum",),
    "daeh": ("header",),
    "onta": ("autoNum",),
    "  nf": ("footNote",),
    "toof": ("footer",),
    "umf%": ("fieldBegin", "fieldEnd"),
    "kmb%": ("fieldBegin", "fieldEnd"),
    "klc%": ("fieldBegin", "fieldEnd"),
}


def profile_hwp_file(path: Path) -> dict[str, Any]:
    """Return a path-free HWP structural profile."""

    try:
        cfb = CompoundFile.from_path(path)
    except (OSError, CompoundFileError) as exc:
        return {"status": "cfb_error", "error": exc.__class__.__name__}

    stream_paths = cfb.list_stream_paths()
    stream_profile = _profile_stream_inventory(stream_paths)
    file_header = _read_file_header(cfb)
    compressed = bool(file_header.get("flags", {}).get("compressed"))

    doc_info = _profile_named_record_stream(cfb, "DocInfo", compressed)
    body_sections = [
        path
        for path in stream_paths
        if path.startswith("BodyText/Section") and path.rsplit("Section", 1)[-1].isdigit()
    ]
    body_section_profiles = [
        _profile_named_record_stream(cfb, section_path, compressed) for section_path in sorted(body_sections)
    ]
    body_aggregate = _aggregate_body_profiles(body_section_profiles)

    status = "profiled"
    if file_header.get("status") != "read":
        status = "profiled_with_missing_file_header"
    elif not body_section_profiles:
        status = "profiled_without_body_sections"
    elif any(profile.get("record_parse_status") != "parsed" for profile in body_section_profiles):
        status = "profiled_with_record_warnings"

    return {
        "status": status,
        "file_header": file_header,
        "stream_inventory": stream_profile,
        "doc_info": doc_info,
        "body": {
            "section_stream_count": len(body_section_profiles),
            "sections": body_section_profiles,
            "aggregate": body_aggregate,
        },
    }


def _profile_stream_inventory(paths: list[str]) -> dict[str, Any]:
    prefixes = Counter(path.split("/", 1)[0] if "/" in path else "root" for path in paths)
    return {
        "stream_count": len(paths),
        "prefix_counts": dict(sorted(prefixes.items())),
        "body_section_stream_count": sum(
            1 for path in paths if path.startswith("BodyText/Section") and path.rsplit("Section", 1)[-1].isdigit()
        ),
        "bin_data_stream_count": sum(1 for path in paths if path.startswith("BinData/")),
        "has_doc_info": "DocInfo" in paths,
        "has_file_header": "FileHeader" in paths,
    }


def _read_file_header(cfb: CompoundFile) -> dict[str, Any]:
    try:
        payload = cfb.read_stream("FileHeader")
    except (KeyError, CompoundFileError):
        return {"status": "missing"}
    if len(payload) < 40:
        return {"status": "too_short", "size": len(payload)}

    signature = payload[:32].split(b"\x00", 1)[0]
    version_raw = _u32(payload, 32)
    flags_raw = _u32(payload, 36)
    version = {
        "raw": version_raw,
        "major": (version_raw >> 24) & 0xFF,
        "minor": (version_raw >> 16) & 0xFF,
        "patch": (version_raw >> 8) & 0xFF,
        "build": version_raw & 0xFF,
    }
    flags = {name: bool(flags_raw & (1 << bit)) for bit, name in FLAG_NAMES.items()}
    return {
        "status": "read",
        "signature_ok": signature.startswith(HWP_SIGNATURE),
        "version": version,
        "flags_raw": flags_raw,
        "flags": flags,
    }


def _profile_named_record_stream(cfb: CompoundFile, path: str, compressed: bool) -> dict[str, Any]:
    try:
        payload = cfb.read_stream(path)
    except (KeyError, CompoundFileError) as exc:
        return {
            "stream_role": _stream_role(path),
            "status": "missing_or_unreadable",
            "error": exc.__class__.__name__,
        }
    decoded, compression_status = _decode_record_stream(payload, compressed)
    records, parse_status, trailing_bytes = _parse_records(decoded)
    return _summarize_records(
        records,
        stream_role=_stream_role(path),
        stream_size=len(payload),
        decoded_size=len(decoded),
        compression_status=compression_status,
        parse_status=parse_status,
        trailing_bytes=trailing_bytes,
    )


def _decode_record_stream(payload: bytes, compressed: bool) -> tuple[bytes, str]:
    if not compressed:
        return payload, "not_compressed"
    for wbits, label in ((-15, "raw_deflate"), (15, "zlib")):
        try:
            return decompress_bounded(payload, wbits), f"decompressed_{label}"
        except ResourceLimitError:
            raise
        except zlib.error:
            continue
    return payload, "decompress_failed"


def _parse_records(payload: bytes) -> tuple[list[dict[str, Any]], str, int]:
    records: list[dict[str, Any]] = []
    offset = 0
    while offset + 4 <= len(payload):
        header = _u32(payload, offset)
        offset += 4
        tag_id = header & 0x3FF
        level = (header >> 10) & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:
            if offset + 4 > len(payload):
                return records, "truncated_extended_size", len(payload) - offset
            size = _u32(payload, offset)
            offset += 4
        if offset + size > len(payload):
            return records, "truncated_payload", len(payload) - offset
        body = payload[offset : offset + size]
        offset += size
        records.append(
            {
                "tag_id": tag_id,
                "tag_name": TAG_NAMES.get(tag_id, f"UNKNOWN_{tag_id}"),
                "level": level,
                "size": size,
                "body": body,
            }
        )
    trailing = len(payload) - offset
    return records, "parsed" if trailing == 0 else "trailing_bytes", trailing


def _summarize_records(
    records: list[dict[str, Any]],
    *,
    stream_role: str,
    stream_size: int,
    decoded_size: int,
    compression_status: str,
    parse_status: str,
    trailing_bytes: int,
) -> dict[str, Any]:
    tag_counts = Counter(record["tag_name"] for record in records)
    tag_payload_bytes = Counter()
    max_level = 0
    para_header_signals = {
        "paragraph_count": 0,
        "declared_char_count": 0,
        "char_shape_run_count": 0,
        "declared_line_segment_count": 0,
        "control_mask_nonzero_count": 0,
    }
    layout_signals = {
        "para_text_char_estimate": 0,
        "line_segment_count": 0,
        "line_segment_record_count": 0,
        "line_segment_declared_mismatch_count": 0,
        "line_segment_remainder_bytes": 0,
        "orphan_line_segment_record_count": 0,
        "table_record_count": 0,
        "table_row_count": 0,
        "table_cell_count": 0,
        "picture_record_count": 0,
        "page_def_record_count": 0,
        "page_width_sum": 0,
        "page_height_sum": 0,
        "page_margin_sum": 0,
        "list_header_record_count": 0,
        "ctrl_header_record_count": 0,
        "known_layout_control_count": 0,
        "candidate_col_pr_control_count": 0,
        "portable_col_pr_control_count": 0,
        "hancom_col_pr_control_count": 0,
    }
    style_signals = {
        "paragraph_style_ref_count": 0,
        "distinct_para_shape_ref_count": 0,
        "distinct_style_ref_count": 0,
        "para_char_shape_record_count": 0,
        "para_char_shape_run_count": 0,
        "distinct_char_shape_ref_count": 0,
        "max_char_shape_run_count": 0,
    }
    doc_properties: dict[str, int] = {}
    id_mappings: dict[str, int] = {}
    paragraph_style_runs: list[dict[str, Any]] = []
    page_definitions: list[dict[str, Any]] = []
    table_semantics = parse_hwp_table_records(records) if stream_role == "body_section" else {}
    table_shapes = list(table_semantics.get("tables", [])) if isinstance(table_semantics, dict) else []
    if table_shapes:
        layout_signals["table_record_count"] = len(table_shapes)
        layout_signals["table_row_count"] = sum(_as_int(table.get("row_count")) for table in table_shapes)
        layout_signals["table_cell_count"] = sum(_as_int(table.get("cell_count")) for table in table_shapes)
        layout_signals["merged_table_cell_count"] = _as_int(
            table_semantics.get("counts", {}).get("merged_cell_count")
        )
        layout_signals["nested_table_count"] = _as_int(
            table_semantics.get("counts", {}).get("nested_table_count")
        )
    control_id_counts: Counter[str] = Counter()
    layout_control_child_counts: Counter[str] = Counter()
    para_shape_refs: set[int] = set()
    style_refs: set[int] = set()
    char_shape_refs: set[int] = set()
    current_paragraph: dict[str, Any] | None = None
    latest_paragraph_by_level: dict[int, dict[str, Any]] = {}

    for record in records:
        name = str(record["tag_name"])
        body = bytes(record["body"])
        tag_payload_bytes[name] += int(record["size"])
        max_level = max(max_level, int(record["level"]))
        if name == "DOCUMENT_PROPERTIES" and len(body) >= 2:
            doc_properties["section_count"] = _u16(body, 0)
        elif name == "ID_MAPPINGS":
            id_mappings = _parse_id_mappings(body)
        elif name == "PARA_HEADER":
            paragraph = _parse_para_header(body, len(paragraph_style_runs))
            paragraph["record_level"] = int(record.get("level", 0))
            record_level = int(record.get("level", 0))
            latest_paragraph_by_level[record_level] = paragraph
            for level in [value for value in latest_paragraph_by_level if value > record_level]:
                del latest_paragraph_by_level[level]
            _merge_para_header_signals_from_parsed(paragraph, para_header_signals)
            current_paragraph = paragraph
            paragraph_style_runs.append(paragraph)
            if paragraph["has_style_header"]:
                style_signals["paragraph_style_ref_count"] += 1
                para_shape_refs.add(int(paragraph["para_shape_id"]))
                style_refs.add(int(paragraph["style_id"]))
            style_signals["max_char_shape_run_count"] = max(
                style_signals["max_char_shape_run_count"],
                int(paragraph["declared_char_shape_run_count"]),
            )
        elif name == "PARA_TEXT":
            layout_signals["para_text_char_estimate"] += len(body) // 2
        elif name == "PARA_CHAR_SHAPE":
            runs = _parse_para_char_shape_runs(body)
            style_signals["para_char_shape_record_count"] += 1
            style_signals["para_char_shape_run_count"] += len(runs)
            style_signals["max_char_shape_run_count"] = max(
                style_signals["max_char_shape_run_count"],
                len(runs),
            )
            for run in runs:
                char_shape_refs.add(int(run["char_shape_id"]))
            if current_paragraph is not None:
                current_paragraph["char_shape_runs"] = runs
                current_paragraph["actual_char_shape_run_count"] = len(runs)
        elif name == "PARA_LINE_SEG":
            parsed = parse_hwp_line_segment_body(body)
            segments = parsed["segments"]
            layout_signals["line_segment_record_count"] += 1
            layout_signals["line_segment_count"] += len(segments)
            layout_signals["line_segment_remainder_bytes"] += int(parsed["remainder_bytes"])
            if current_paragraph is None:
                layout_signals["orphan_line_segment_record_count"] += 1
            else:
                current_paragraph["line_segments"].extend(segments)
                current_paragraph["actual_line_segment_count"] = len(current_paragraph["line_segments"])
                current_paragraph["line_segment_remainder_bytes"] += int(parsed["remainder_bytes"])
        elif name == "SHAPE_COMPONENT_PICTURE":
            layout_signals["picture_record_count"] += 1
        elif name == "PAGE_DEF":
            layout_signals["page_def_record_count"] += 1
            page_definition = _parse_page_definition(body, layout_signals["page_def_record_count"] - 1)
            page_definitions.append(page_definition)
            layout_signals["page_width_sum"] += _as_int(page_definition.get("width"))
            layout_signals["page_height_sum"] += _as_int(page_definition.get("height"))
            layout_signals["page_margin_sum"] += _page_margin_sum(page_definition)
        elif name == "LIST_HEADER":
            layout_signals["list_header_record_count"] += 1
        elif name == "CTRL_HEADER":
            layout_signals["ctrl_header_record_count"] += 1
            control_id = _parse_control_id(body)
            control_id_counts[control_id] += 1
            if control_id == "spct":
                owner = _nearest_parent_paragraph(
                    latest_paragraph_by_level,
                    int(record.get("level", 0)),
                )
                if owner is not None:
                    owner["compose_controls"].append(parse_hwp_compose_control_body(body))
            if control_id == "dhgp":
                owner = _nearest_parent_paragraph(
                    latest_paragraph_by_level,
                    int(record.get("level", 0)),
                )
                if owner is not None:
                    owner["page_hiding_controls"].append(
                        parse_hwp_page_hiding_control_body(body)
                    )
            if control_id in {"  nf", "onta"}:
                owner = _nearest_parent_paragraph(
                    latest_paragraph_by_level,
                    int(record.get("level", 0)),
                )
                if owner is not None and control_id == "  nf":
                    owner["footnote_controls"].append(
                        parse_hwp_footnote_control_body(body)
                    )
                elif owner is not None:
                    owner["auto_number_controls"].append(
                        parse_hwp_footnote_auto_number_body(body)
                    )
            if control_id == "dloc":
                layout_signals["candidate_col_pr_control_count"] += 1
                layout_signals["hancom_col_pr_control_count"] += 1
            elif control_id == "dces":
                layout_signals["portable_col_pr_control_count"] += 1
            layout_children = CONTROL_ID_TO_LAYOUT_CHILDREN.get(control_id, ())
            for layout_child in layout_children:
                layout_signals["known_layout_control_count"] += 1
                layout_control_child_counts[layout_child] += 1

    style_signals["distinct_para_shape_ref_count"] = len(para_shape_refs)
    style_signals["distinct_style_ref_count"] = len(style_refs)
    style_signals["distinct_char_shape_ref_count"] = len(char_shape_refs)
    style_details = parse_hwp_style_records(records, id_mappings) if stream_role == "doc_info" else {}
    list_semantics = parse_hwp_list_records(records) if stream_role == "doc_info" else {}
    border_fill_semantics = parse_hwp_border_fill_records(records) if stream_role == "doc_info" else {}
    section_semantics = parse_hwp_section_records(records) if stream_role == "body_section" else {}
    binary_semantics = parse_hwp_binary_records(records) if stream_role == "doc_info" else {}
    object_semantics = parse_hwp_object_records(records) if stream_role == "body_section" else {}
    line_segment_semantics = (
        build_hwp_line_segment_semantics(paragraph_style_runs) if stream_role == "body_section" else {}
    )
    line_segment_counts = (
        line_segment_semantics.get("counts", {}) if isinstance(line_segment_semantics, dict) else {}
    )
    layout_signals["line_segment_declared_mismatch_count"] = _as_int(
        line_segment_counts.get("declared_count_mismatch_count")
    )

    return {
        "stream_role": stream_role,
        "status": "profiled",
        "stream_size": stream_size,
        "decoded_size": decoded_size,
        "compression_status": compression_status,
        "record_parse_status": parse_status,
        "trailing_bytes": trailing_bytes,
        "record_count": len(records),
        "max_level": max_level,
        "tag_counts": dict(sorted(tag_counts.items())),
        "tag_payload_bytes": dict(sorted(tag_payload_bytes.items())),
        "doc_properties": doc_properties,
        "id_mappings": id_mappings,
        "para_header_signals": para_header_signals,
        "layout_signals": layout_signals,
        "layout_details": {
            "page_definitions": page_definitions,
            "table_shapes": table_shapes,
            "table_semantics": table_semantics,
            "control_id_counts": dict(sorted(control_id_counts.items())),
            "layout_control_child_counts": dict(sorted(layout_control_child_counts.items())),
            "section_semantics": section_semantics,
            "line_segment_semantics": line_segment_semantics,
        },
        "style_signals": style_signals,
        "style_details": style_details,
        "list_semantics": list_semantics,
        "border_fill_semantics": border_fill_semantics,
        "binary_semantics": binary_semantics,
        "object_semantics": object_semantics,
        "paragraph_style_runs": paragraph_style_runs,
    }


def _stream_role(path: str) -> str:
    if path == "DocInfo":
        return "doc_info"
    if path.startswith("BodyText/Section"):
        return "body_section"
    return "other"


def _parse_id_mappings(body: bytes) -> dict[str, int]:
    result: dict[str, int] = {}
    for index, label in enumerate(ID_MAPPING_LABELS):
        offset = index * 4
        if offset + 4 > len(body):
            break
        result[label] = _u32(body, offset)
    return result


def _merge_para_header_signals(body: bytes, target: dict[str, int]) -> None:
    _merge_para_header_signals_from_parsed(_parse_para_header(body, 0), target)


def _merge_para_header_signals_from_parsed(paragraph: dict[str, Any], target: dict[str, int]) -> None:
    target["paragraph_count"] += 1
    target["declared_char_count"] += _as_int(paragraph.get("declared_char_count"))
    target["char_shape_run_count"] += _as_int(paragraph.get("declared_char_shape_run_count"))
    target["declared_line_segment_count"] += _as_int(paragraph.get("declared_line_segment_count"))
    if paragraph.get("control_mask_nonzero"):
        target["control_mask_nonzero_count"] += 1


def _parse_para_header(body: bytes, paragraph_index: int) -> dict[str, Any]:
    paragraph = {
        "paragraph_index": paragraph_index,
        "declared_char_count": 0,
        "char_count_high_bit": False,
        "merged": False,
        "section_break": False,
        "column_definition_break": False,
        "page_break": False,
        "column_break": False,
        "control_mask_nonzero": False,
        "para_shape_id": 0,
        "style_id": 0,
        "paragraph_id": 0,
        "declared_char_shape_run_count": 0,
        "actual_char_shape_run_count": 0,
        "declared_line_segment_count": 0,
        "actual_line_segment_count": 0,
        "line_segment_remainder_bytes": 0,
        "has_style_header": False,
        "char_shape_runs": [],
        "line_segments": [],
        "compose_controls": [],
        "page_hiding_controls": [],
        "footnote_controls": [],
        "auto_number_controls": [],
    }
    if len(body) < 14:
        return paragraph
    declared_chars, control_mask, para_shape_id, style_id, divide, char_shape_count = struct.unpack_from(
        "<IIHBBH",
        body,
        0,
    )
    paragraph.update(
        {
            "declared_char_count": declared_chars & 0x7FFFFFFF,
            "char_count_high_bit": bool(declared_chars & 0x80000000),
            # The binary character-count flag is not the HWPX paragraph
            # `merged` attribute. Hancom-converted corpus pairs keep merged=0.
            "merged": False,
            "section_break": bool(divide & 0x01),
            "column_definition_break": bool(divide & 0x02),
            "page_break": bool(divide & 0x04),
            "column_break": bool(divide & 0x08),
            "control_mask_nonzero": bool(control_mask),
            "para_shape_id": para_shape_id,
            "style_id": style_id,
            "paragraph_id": _u32(body, 18) if len(body) >= 22 else 0,
            "declared_char_shape_run_count": char_shape_count,
            "declared_line_segment_count": _u16(body, 16) if len(body) >= 18 else 0,
            "has_style_header": True,
        }
    )
    return paragraph


def _parse_para_char_shape_runs(body: bytes) -> list[dict[str, int]]:
    runs: list[dict[str, int]] = []
    for offset in range(0, len(body) - 7, 8):
        char_position, char_shape_id = struct.unpack_from("<II", body, offset)
        runs.append(
            {
                "start": char_position,
                "char_shape_id": char_shape_id,
            }
        )
    return runs


def _parse_page_definition(body: bytes, page_def_index: int) -> dict[str, Any]:
    defaults = {
        "page_def_index": page_def_index,
        "width": 59528,
        "height": 84188,
        "margin": {
            "left": 8504,
            "right": 8504,
            "top": 8504,
            "bottom": 8504,
            "header": 5668,
            "footer": 5668,
            "gutter": 0,
        },
    }
    if len(body) < 32:
        return defaults
    width = _u32(body, 0)
    height = _u32(body, 4)
    left = _u32(body, 8)
    right = _u32(body, 12)
    top = _u32(body, 16)
    bottom = _u32(body, 20)
    header = _u32(body, 24)
    footer = _u32(body, 28)
    gutter = _u32(body, 32) if len(body) >= 36 else 0
    return {
        "page_def_index": page_def_index,
        "width": width or defaults["width"],
        "height": height or defaults["height"],
        "margin": {
            "left": left,
            "right": right,
            "top": top,
            "bottom": bottom,
            "header": header,
            "footer": footer,
            "gutter": gutter,
        },
    }


def _parse_table_shape(body: bytes, table_index: int) -> dict[str, Any]:
    if len(body) < 18:
        return {
            "table_index": table_index,
            "row_count": 1,
            "column_count": 1,
            "cell_count": 1,
            "row_cell_counts": [1],
            "parse_status": "fallback_short_body",
        }
    row_count = _u16(body, 4)
    column_count = _u16(body, 6)
    if 1 <= row_count <= 512 and 1 <= column_count <= 512 and 18 + (row_count * 2) <= len(body):
        row_cell_counts = [_u16(body, 18 + (index * 2)) for index in range(row_count)]
        if all(0 <= count <= 512 for count in row_cell_counts) and sum(row_cell_counts) > 0:
            return {
                "table_index": table_index,
                "row_count": row_count,
                "column_count": column_count,
                "cell_count": sum(row_cell_counts),
                "row_cell_counts": row_cell_counts,
                "parse_status": "parsed",
            }
    safe_rows = max(1, min(row_count, 512))
    safe_columns = max(1, min(column_count, 512))
    return {
        "table_index": table_index,
        "row_count": safe_rows,
        "column_count": safe_columns,
        "cell_count": safe_rows * safe_columns,
        "row_cell_counts": [safe_columns for _ in range(safe_rows)],
        "parse_status": "fallback_grid",
    }


def _parse_control_id(body: bytes) -> str:
    if len(body) < 4:
        return "unknown"
    return "".join(chr(value) if 32 <= value < 127 else f"\\x{value:02x}" for value in body[:4])


def _nearest_parent_paragraph(
    paragraphs_by_level: dict[int, dict[str, Any]],
    record_level: int,
) -> dict[str, Any] | None:
    parent_levels = [level for level in paragraphs_by_level if level < record_level]
    if not parent_levels:
        return None
    return paragraphs_by_level[max(parent_levels)]


def _page_margin_sum(page_definition: dict[str, Any]) -> int:
    margin = page_definition.get("margin", {}) if isinstance(page_definition.get("margin"), dict) else {}
    return sum(_as_int(margin.get(key)) for key in ("left", "right", "top", "bottom", "header", "footer", "gutter"))


def _aggregate_body_profiles(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    tag_counts: Counter[str] = Counter()
    layout_signals: Counter[str] = Counter()
    layout_control_child_counts: Counter[str] = Counter()
    control_id_counts: Counter[str] = Counter()
    para_signals: Counter[str] = Counter()
    style_signals: Counter[str] = Counter()
    parse_status_counts: Counter[str] = Counter()
    compression_status_counts: Counter[str] = Counter()

    for profile in profiles:
        tag_counts.update(profile.get("tag_counts", {}))
        layout_signals.update(profile.get("layout_signals", {}))
        layout_details = profile.get("layout_details", {})
        if isinstance(layout_details, dict):
            layout_control_child_counts.update(layout_details.get("layout_control_child_counts", {}))
            control_id_counts.update(layout_details.get("control_id_counts", {}))
        para_signals.update(profile.get("para_header_signals", {}))
        style_signals.update(profile.get("style_signals", {}))
        parse_status_counts[str(profile.get("record_parse_status", "unknown"))] += 1
        compression_status_counts[str(profile.get("compression_status", "unknown"))] += 1

    return {
        "tag_counts": dict(sorted(tag_counts.items())),
        "layout_signals": dict(sorted(layout_signals.items())),
        "layout_details": {
            "layout_control_child_counts": dict(sorted(layout_control_child_counts.items())),
            "control_id_counts": dict(sorted(control_id_counts.items())),
        },
        "para_header_signals": dict(sorted(para_signals.items())),
        "style_signals": dict(sorted(style_signals.items())),
        "record_parse_status_counts": dict(sorted(parse_status_counts.items())),
        "compression_status_counts": dict(sorted(compression_status_counts.items())),
    }


def _u16(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<H", payload, offset)[0]


def _u32(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<I", payload, offset)[0]


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
