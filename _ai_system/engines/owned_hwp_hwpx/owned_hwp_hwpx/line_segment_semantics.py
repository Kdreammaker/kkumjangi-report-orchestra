"""Typed HWP/HWPX paragraph line-segment cache semantics."""

from __future__ import annotations

from collections import Counter
import struct
from typing import Any
from xml.etree import ElementTree


LINE_SEGMENT_FIELDS = (
    "textpos",
    "vertpos",
    "vertsize",
    "textheight",
    "baseline",
    "spacing",
    "horzpos",
    "horzsize",
    "flags",
)
LINE_SEGMENT_STRUCT = struct.Struct("<IiiiiiiiI")


def parse_hwp_line_segment_body(body: bytes) -> dict[str, Any]:
    """Decode the 36-byte entries from one HWPTAG_PARA_LINE_SEG body."""

    segments = [
        dict(zip(LINE_SEGMENT_FIELDS, LINE_SEGMENT_STRUCT.unpack_from(body, offset), strict=True))
        for offset in range(0, len(body) - LINE_SEGMENT_STRUCT.size + 1, LINE_SEGMENT_STRUCT.size)
    ]
    remainder = len(body) % LINE_SEGMENT_STRUCT.size
    return {
        "status": "parsed" if remainder == 0 else "trailing_bytes",
        "record_size": len(body),
        "remainder_bytes": remainder,
        "segments": segments,
    }


def build_hwp_line_segment_semantics(paragraphs: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a path-free section payload from parsed HWP paragraphs."""

    values = []
    declared_total = 0
    actual_total = 0
    mismatch_count = 0
    remainder_bytes = 0
    for index, paragraph in enumerate(paragraphs):
        segments = [
            _canonical_segment(item)
            for item in paragraph.get("line_segments", [])
            if isinstance(item, dict)
        ]
        declared = _unsigned_int(paragraph.get("declared_line_segment_count"))
        actual = len(segments)
        declared_total += declared
        actual_total += actual
        mismatch_count += int(declared != actual)
        remainder_bytes += _unsigned_int(paragraph.get("line_segment_remainder_bytes"))
        values.append(
            {
                "paragraph_index": index,
                "declared_count": declared,
                "segments": segments,
            }
        )
    status = "parsed"
    if remainder_bytes:
        status = "trailing_bytes"
    elif mismatch_count:
        status = "declared_count_mismatch"
    return {
        "status": status,
        "paragraphs": values,
        "counts": {
            "paragraph_count": len(values),
            "declared_segment_count": declared_total,
            "segment_count": actual_total,
            "declared_count_mismatch_count": mismatch_count,
            "remainder_bytes": remainder_bytes,
        },
    }


def map_hwp_line_segment_text_positions(
    semantics: dict[str, Any],
    paragraph_controls: list[list[dict[str, Any]]],
    *,
    excluded_control_ids: frozenset[str] = frozenset({"dloc"}),
) -> dict[str, Any]:
    """Remove selected non-visible HWP control widths from HWPX positions."""
    paragraphs = []
    changed_count = 0
    for index, paragraph in enumerate(
        semantics.get("paragraphs", [])
        if isinstance(semantics.get("paragraphs"), list)
        else []
    ):
        if not isinstance(paragraph, dict):
            continue
        controls = (
            paragraph_controls[index]
            if index < len(paragraph_controls)
            and isinstance(paragraph_controls[index], list)
            else []
        )
        segments = []
        for value in paragraph.get("segments", []):
            if not isinstance(value, dict):
                continue
            segment = dict(value)
            source_position = _unsigned_int(segment.get("textpos"))
            visible_position = _position_without_selected_controls(
                source_position,
                controls,
                excluded_control_ids,
            )
            changed_count += int(visible_position != source_position)
            segment["textpos"] = visible_position
            segments.append(segment)
        paragraphs.append({**paragraph, "segments": segments})
    counts = (
        dict(semantics.get("counts", {}))
        if isinstance(semantics.get("counts"), dict)
        else {}
    )
    counts["source_to_visible_textpos_change_count"] = changed_count
    return {
        **semantics,
        "text_position_space": "hwpx_visible",
        "paragraphs": paragraphs,
        "counts": counts,
    }


def _position_without_selected_controls(
    position: int,
    controls: list[dict[str, Any]],
    excluded_control_ids: frozenset[str],
) -> int:
    removed = 0
    for control in sorted(
        (item for item in controls if isinstance(item, dict)),
        key=lambda item: _unsigned_int(item.get("source_start")),
    ):
        if str(control.get("control_id", "")) not in excluded_control_ids:
            continue
        source_start = _unsigned_int(control.get("source_start"))
        source_end = max(source_start, _unsigned_int(control.get("source_end")))
        visible_start = _unsigned_int(control.get("visible_start"))
        visible_end = max(visible_start, _unsigned_int(control.get("visible_end")))
        source_width = source_end - source_start
        visible_width = visible_end - visible_start
        removable_width = max(0, source_width - visible_width)
        if position >= source_end:
            removed += removable_width
            continue
        if position > source_start:
            return max(
                0,
                source_start - removed + min(position - source_start, visible_width),
            )
    return max(0, position - removed)


def parse_hwpx_line_segment_root(root: ElementTree.Element) -> dict[str, Any]:
    """Read direct linesegarray children without double-counting nested paragraphs."""

    paragraphs = []
    invalid_attribute_count = 0
    missing_attribute_count = 0
    segment_count = 0
    for element in root.iter():
        if _local_name(element.tag) != "p":
            continue
        segments = []
        for child in list(element):
            if _local_name(child.tag) != "linesegarray":
                continue
            for segment_element in list(child):
                if _local_name(segment_element.tag) != "lineseg":
                    continue
                segment: dict[str, int] = {}
                for field in LINE_SEGMENT_FIELDS:
                    if field not in segment_element.attrib:
                        missing_attribute_count += 1
                    try:
                        segment[field] = int(segment_element.attrib.get(field, 0))
                    except (TypeError, ValueError):
                        invalid_attribute_count += 1
                        segment[field] = 0
                segments.append(segment)
        segment_count += len(segments)
        paragraphs.append(
            {
                "paragraph_index": len(paragraphs),
                "declared_count": len(segments),
                "segments": segments,
            }
        )
    status = "parsed" if not (missing_attribute_count or invalid_attribute_count) else "attribute_errors"
    return {
        "status": status,
        "paragraphs": paragraphs,
        "counts": {
            "paragraph_count": len(paragraphs),
            "declared_segment_count": segment_count,
            "segment_count": segment_count,
            "declared_count_mismatch_count": 0,
            "remainder_bytes": 0,
            "missing_attribute_count": missing_attribute_count,
            "invalid_attribute_count": invalid_attribute_count,
        },
    }


def compare_line_segment_semantics(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Compare paragraph ownership, counts, signed values, and flags exactly."""

    source_values = _canonical_paragraphs(source.get("paragraphs"))
    target_values = _canonical_paragraphs(target.get("paragraphs"))
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    paragraph_count_exact = len(source_values) == len(target_values)
    paragraph_segment_counts_exact = 0
    source_segment_count = 0
    target_segment_count = 0

    for index, source_paragraph in enumerate(source_values):
        target_paragraph = target_values[index] if index < len(target_values) else {"segments": []}
        source_segments = source_paragraph["segments"]
        target_segments = target_paragraph["segments"]
        source_segment_count += len(source_segments)
        target_segment_count += len(target_segments)
        paragraph_segment_counts_exact += int(len(source_segments) == len(target_segments))
        total["paragraph_segment_count"] += 1
        exact["paragraph_segment_count"] += int(len(source_segments) == len(target_segments))
        for segment_index, source_segment in enumerate(source_segments):
            target_segment = target_segments[segment_index] if segment_index < len(target_segments) else {}
            for field in LINE_SEGMENT_FIELDS:
                total[field] += 1
                exact[field] += int(source_segment[field] == target_segment.get(field))

    for paragraph in target_values[len(source_values) :]:
        target_segment_count += len(paragraph["segments"])

    field_checks = {field: exact[field] == total[field] for field in LINE_SEGMENT_FIELDS}
    checks = {
        "paragraph_count": paragraph_count_exact,
        "paragraph_segment_counts": paragraph_segment_counts_exact == len(source_values),
        "segment_count": source_segment_count == target_segment_count,
        "fields": all(field_checks.values()),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "field_checks": field_checks,
        "source_counts": {
            "paragraph_count": len(source_values),
            "segment_count": source_segment_count,
        },
        "target_counts": {
            "paragraph_count": len(target_values),
            "segment_count": target_segment_count,
        },
        "paragraph_segment_count_exact_count": paragraph_segment_counts_exact,
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def _canonical_paragraphs(value: Any) -> list[dict[str, Any]]:
    result = []
    for index, paragraph in enumerate(value if isinstance(value, list) else []):
        if not isinstance(paragraph, dict):
            continue
        result.append(
            {
                "paragraph_index": index,
                "segments": [
                    _canonical_segment(segment)
                    for segment in paragraph.get("segments", [])
                    if isinstance(segment, dict)
                ],
            }
        )
    return result


def _canonical_segment(value: dict[str, Any]) -> dict[str, int]:
    return {
        "textpos": _unsigned_int(value.get("textpos")),
        "vertpos": _signed_int(value.get("vertpos")),
        "vertsize": _signed_int(value.get("vertsize")),
        "textheight": _signed_int(value.get("textheight")),
        "baseline": _signed_int(value.get("baseline")),
        "spacing": _signed_int(value.get("spacing")),
        "horzpos": _signed_int(value.get("horzpos")),
        "horzsize": _signed_int(value.get("horzsize")),
        "flags": _unsigned_int(value.get("flags")),
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _unsigned_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _signed_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
