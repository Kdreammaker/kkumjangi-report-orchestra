"""Renderer-facing paragraph and unit-compatibility semantics for HWPX."""

from __future__ import annotations

from collections import Counter
from typing import Any
from xml.etree import ElementTree


MARGIN_FIELDS = ("indent", "left", "right", "prev", "next")


def parse_hwpx_header_compatibility_root(root: ElementTree.Element) -> dict[str, Any]:
    para_shapes = []
    for element in root.iter():
        if _local_name(element.tag) != "paraPr":
            continue
        switch = _first_child(element, "switch")
        case = _first_child(switch, "case") if switch is not None else None
        default = _first_child(switch, "default") if switch is not None else None
        para_shapes.append(
            {
                "id": _as_int(element.attrib.get("id")),
                "snap_to_grid": _as_bool(element.attrib.get("snapToGrid"), True),
                "case": _parse_margin_spacing_branch(case),
                "default": _parse_margin_spacing_branch(default),
            }
        )
    return {
        "status": "parsed",
        "counts": {
            "para_shape_count": len(para_shapes),
            "snap_to_grid_true_count": sum(bool(item["snap_to_grid"]) for item in para_shapes),
            "complete_switch_count": sum(bool(item["case"] and item["default"]) for item in para_shapes),
        },
        "para_shapes": para_shapes,
    }


def model_header_compatibility_semantics(style_semantics: dict[str, Any]) -> dict[str, Any]:
    para_shapes = []
    for shape in style_semantics.get("para_shapes", []):
        if not isinstance(shape, dict):
            continue
        margin = _mapping(shape.get("margin"))
        line_spacing = _mapping(shape.get("line_spacing"))
        line_type = str(line_spacing.get("type", "PERCENT")).upper()
        line_value = _as_int(line_spacing.get("value"))
        default = {
            "margin": {field: _signed_int(margin.get(field)) for field in MARGIN_FIELDS},
            "line_spacing": {
                "type": line_type,
                "value": line_value,
                "unit": str(line_spacing.get("unit", "HWPUNIT")).upper(),
            },
        }
        case = {
            "margin": {
                field: _half_signed(margin.get(field))
                for field in MARGIN_FIELDS
            },
            "line_spacing": {
                "type": line_type,
                "value": _half_signed(line_value)
                if line_type in {"FIXED", "AT_LEAST"}
                else line_value,
                "unit": str(line_spacing.get("unit", "HWPUNIT")).upper(),
            },
        }
        para_shapes.append(
            {
                "id": _as_int(shape.get("id")),
                "snap_to_grid": _as_bool(shape.get("snap_to_grid"), True),
                "case": case,
                "default": default,
            }
        )
    return {
        "status": "parsed",
        "counts": {
            "para_shape_count": len(para_shapes),
            "snap_to_grid_true_count": sum(bool(item["snap_to_grid"]) for item in para_shapes),
            "complete_switch_count": len(para_shapes),
        },
        "para_shapes": para_shapes,
    }


def compare_header_compatibility_semantics(
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    source_shapes = _shape_map(source.get("para_shapes"))
    target_shapes = _shape_map(target.get("para_shapes"))
    checks = {
        "source_parsed": source.get("status") == "parsed",
        "target_parsed": target.get("status") == "parsed",
        "para_shape_ids": set(source_shapes) == set(target_shapes),
        "snap_to_grid": all(
            source_shapes[key].get("snap_to_grid") == target_shapes.get(key, {}).get("snap_to_grid")
            for key in source_shapes
        ),
        "default_margin_and_spacing": all(
            source_shapes[key].get("default") == target_shapes.get(key, {}).get("default")
            for key in source_shapes
        ),
        "case_margin_and_spacing": all(
            source_shapes[key].get("case") == target_shapes.get(key, {}).get("case")
            for key in source_shapes
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "source_para_shape_count": len(source_shapes),
            "target_para_shape_count": len(target_shapes),
        },
    }


def parse_hwpx_paragraph_render_root(root: ElementTree.Element) -> dict[str, Any]:
    signatures: Counter[str] = Counter()
    paragraph_ids: list[int] = []
    paragraph_count = 0
    for element in root.iter():
        if _local_name(element.tag) != "p":
            continue
        paragraph_count += 1
        paragraph_ids.append(_as_int(element.attrib.get("id")))
        signatures[_paragraph_signature(element.attrib)] += 1
    return {
        "status": "parsed",
        "counts": {
            "paragraph_count": paragraph_count,
            "page_break_count": _signature_flag_count(signatures, 0),
            "column_break_count": _signature_flag_count(signatures, 1),
            "merged_count": _signature_flag_count(signatures, 2),
            "nonzero_paragraph_id_count": sum(value != 0 for value in paragraph_ids),
            "distinct_paragraph_id_count": len(set(paragraph_ids)),
        },
        "flag_signature_counts": dict(sorted(signatures.items())),
        "paragraph_ids": paragraph_ids,
    }


def model_paragraph_render_semantics(section: dict[str, Any]) -> dict[str, Any]:
    signatures: Counter[str] = Counter()
    paragraph_ids: list[int] = []
    high_bit_count = 0
    styles = section.get("paragraph_styles", [])
    for style in styles if isinstance(styles, list) else []:
        if not isinstance(style, dict):
            continue
        high_bit_count += int(bool(style.get("char_count_high_bit")))
        paragraph_ids.append(_as_int(style.get("paragraph_id")))
        signatures[
            _flag_signature(
                bool(style.get("page_break")),
                bool(style.get("column_break")),
                bool(style.get("merged")),
            )
        ] += 1
    return {
        "status": "parsed",
        "counts": {
            "paragraph_count": sum(signatures.values()),
            "page_break_count": _signature_flag_count(signatures, 0),
            "column_break_count": _signature_flag_count(signatures, 1),
            "merged_count": _signature_flag_count(signatures, 2),
            "source_char_count_high_bit_count": high_bit_count,
            "nonzero_paragraph_id_count": sum(value != 0 for value in paragraph_ids),
            "distinct_paragraph_id_count": len(set(paragraph_ids)),
        },
        "flag_signature_counts": dict(sorted(signatures.items())),
        "paragraph_ids": paragraph_ids,
    }


def compare_paragraph_render_semantics(
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    source_counts = _mapping(source.get("counts"))
    target_counts = _mapping(target.get("counts"))
    checks = {
        "source_parsed": source.get("status") == "parsed",
        "target_parsed": target.get("status") == "parsed",
        "paragraph_count": _as_int(source_counts.get("paragraph_count"))
        == _as_int(target_counts.get("paragraph_count")),
        "flag_signatures": _count_map(source.get("flag_signature_counts"))
        == _count_map(target.get("flag_signature_counts")),
        "paragraph_ids": source.get("paragraph_ids") == target.get("paragraph_ids"),
        "source_high_bit_not_mapped_to_merged": not (
            _as_int(source_counts.get("source_char_count_high_bit_count")) > 0
            and _as_int(target_counts.get("merged_count")) > 0
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "source_paragraph_count": _as_int(source_counts.get("paragraph_count")),
            "target_paragraph_count": _as_int(target_counts.get("paragraph_count")),
            "source_char_count_high_bit_count": _as_int(
                source_counts.get("source_char_count_high_bit_count")
            ),
            "target_merged_count": _as_int(target_counts.get("merged_count")),
            "source_nonzero_paragraph_id_count": _as_int(
                source_counts.get("nonzero_paragraph_id_count")
            ),
            "target_nonzero_paragraph_id_count": _as_int(
                target_counts.get("nonzero_paragraph_id_count")
            ),
            "source_distinct_paragraph_id_count": _as_int(
                source_counts.get("distinct_paragraph_id_count")
            ),
            "target_distinct_paragraph_id_count": _as_int(
                target_counts.get("distinct_paragraph_id_count")
            ),
        },
    }


def _parse_margin_spacing_branch(element: ElementTree.Element | None) -> dict[str, Any]:
    if element is None:
        return {}
    margin_element = next(
        (item for item in element.iter() if _local_name(item.tag) == "margin"),
        None,
    )
    margin: dict[str, int] = {field: 0 for field in MARGIN_FIELDS}
    if margin_element is not None:
        for item in margin_element.iter():
            local = _local_name(item.tag)
            field = "indent" if local == "intent" else local
            if field in margin:
                margin[field] = _signed_int(item.attrib.get("value"))
    line_element = next(
        (item for item in element.iter() if _local_name(item.tag) == "lineSpacing"),
        None,
    )
    return {
        "margin": margin,
        "line_spacing": {
            "type": str(line_element.attrib.get("type", "PERCENT")).upper()
            if line_element is not None
            else "PERCENT",
            "value": _as_int(line_element.attrib.get("value"))
            if line_element is not None
            else 0,
            "unit": str(line_element.attrib.get("unit", "HWPUNIT")).upper()
            if line_element is not None
            else "HWPUNIT",
        },
    }


def _shape_map(value: Any) -> dict[int, dict[str, Any]]:
    return {
        _as_int(item.get("id")): item
        for item in value if isinstance(value, list) and isinstance(item, dict)
    }


def _paragraph_signature(attributes: dict[str, str]) -> str:
    return _flag_signature(
        _as_bool(attributes.get("pageBreak")),
        _as_bool(attributes.get("columnBreak")),
        _as_bool(attributes.get("merged")),
    )


def _flag_signature(page_break: bool, column_break: bool, merged: bool) -> str:
    return f"{int(page_break)}:{int(column_break)}:{int(merged)}"


def _signature_flag_count(signatures: Counter[str], index: int) -> int:
    return sum(
        count
        for signature, count in signatures.items()
        if signature.split(":")[index] == "1"
    )


def _first_child(
    element: ElementTree.Element | None,
    name: str,
) -> ElementTree.Element | None:
    if element is None:
        return None
    return next((child for child in list(element) if _local_name(child.tag) == name), None)


def _count_map(value: Any) -> dict[str, int]:
    return {
        str(key): _as_int(item)
        for key, item in value.items()
    } if isinstance(value, dict) else {}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _half_signed(value: Any) -> int:
    parsed = _signed_int(value)
    return parsed // 2 if parsed >= 0 else -((-parsed) // 2)


def _as_bool(value: Any, fallback: bool = False) -> bool:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _signed_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
