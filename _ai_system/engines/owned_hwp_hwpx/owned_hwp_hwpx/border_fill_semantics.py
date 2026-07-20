"""Typed HWP/HWPX border and fill semantics."""

from __future__ import annotations

from collections import Counter
import struct
from typing import Any, Iterable
from xml.etree import ElementTree


LINE_TYPES = {
    0: "NONE",
    1: "SOLID",
    2: "DOT",
    3: "DASH",
    4: "DASH_DOT",
    5: "DASH_DOT_DOT",
    6: "LONG_DASH",
    7: "CIRCLE",
    8: "DOUBLE_SLIM",
    9: "SLIM_THICK",
    10: "THICK_SLIM",
    11: "SLIM_THICK_SLIM",
    12: "WAVE",
    13: "DOUBLE_WAVE",
    14: "THICK_3D",
    15: "THICK_3D_REV",
    16: "SOLID_3D",
    17: "SOLID_3D_REV",
}
LINE_WIDTHS = {
    0: "0.1 mm",
    1: "0.12 mm",
    2: "0.15 mm",
    3: "0.2 mm",
    4: "0.25 mm",
    5: "0.3 mm",
    6: "0.4 mm",
    7: "0.5 mm",
    8: "0.6 mm",
    9: "0.7 mm",
    10: "1.0 mm",
    11: "1.5 mm",
    12: "2.0 mm",
    13: "3.0 mm",
    14: "4.0 mm",
    15: "5.0 mm",
}
SLASH_TYPES = {0: "NONE", 2: "CENTER", 3: "CENTER_BELOW", 6: "CENTER_ABOVE", 7: "ALL"}
HATCH_STYLES = {
    1: "HORIZONTAL",
    2: "VERTICAL",
    3: "BACK_SLASH",
    4: "CROSS",
    5: "CROSS_DIAGONAL",
    6: "CROSS_DIAGONAL",
}
GRADATION_TYPES = {1: "LINEAR", 2: "RADIAL", 3: "CONICAL", 4: "SQUARE"}
IMAGE_FILL_MODES = {
    0: "TILE",
    1: "TILE_HORZ_TOP",
    2: "TILE_HORZ_BOTTOM",
    3: "TILE_VERT_LEFT",
    4: "TILE_VERT_RIGHT",
    5: "TOTAL",
    6: "CENTER",
    7: "CENTER_TOP",
    8: "CENTER_BOTTOM",
    9: "LEFT_CENTER",
    10: "LEFT_TOP",
    11: "LEFT_BOTTOM",
    12: "RIGHT_CENTER",
    13: "RIGHT_TOP",
    14: "RIGHT_BOTTOM",
    15: "NONE",
}
IMAGE_EFFECTS = {0: "REAL_PIC", 1: "GRAY_SCALE", 2: "BLACK_WHITE", 4: "PATTERN8X8"}


def parse_hwp_border_fill_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = []
    statuses: Counter[str] = Counter()
    for record in records:
        if record.get("tag_name") != "BORDER_FILL":
            continue
        value = _parse_hwp_border_fill(bytes(record.get("body", b"")), len(values) + 1)
        values.append(value)
        statuses[str(value.get("parse_status", "unknown"))] += 1
    return _result(values, statuses)


def parse_hwpx_border_fill_root(root: ElementTree.Element) -> dict[str, Any]:
    values = [
        _parse_hwpx_border_fill(element)
        for element in root.iter()
        if _local_name(element.tag) == "borderFill"
    ]
    return _result(values, Counter({"parsed": len(values)}))


def compare_border_fill_semantics(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    source_values = [_canonical(value) for value in source.get("border_fills", []) if isinstance(value, dict)]
    target_values = [_canonical(value) for value in target.get("border_fills", []) if isinstance(value, dict)]
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    _compare_leaves(source_values, target_values, "border_fills", exact, total)
    return {
        "status": "pass" if source_values == target_values else "fail",
        "checks": {"border_fills": source_values == target_values},
        "source_count": len(source_values),
        "target_count": len(target_values),
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def _parse_hwp_border_fill(body: bytes, border_id: int) -> dict[str, Any]:
    if len(body) < 36:
        return {
            "id": border_id,
            **_default_border_fill(),
            "parse_status": "short_body",
            "source_only": {"record_size": len(body)},
        }
    attributes = _u16(body, 0)
    borders = {
        name: _parse_hwp_line(body, 2 + index * 6)
        for index, name in enumerate(("left", "right", "top", "bottom"))
    }
    diagonal = _parse_hwp_line(body, 26)
    if diagonal["type"] == "NONE":
        diagonal = None
    fill, consumed, fill_status = _parse_hwp_fill(body, 32)
    known_attr_mask = 0x7FFF
    return {
        "id": border_id,
        "three_d": bool(attributes & 1),
        "shadow": bool(attributes & 2),
        "center_line": "CENTER" if attributes & (1 << 13) else "NONE",
        "break_cell_separate_line": bool(attributes & (1 << 14)),
        "slash": _slash_value((attributes >> 2) & 0x7, bool(attributes & (0x3 << 8)), bool(attributes & (1 << 11))),
        "back_slash": _slash_value((attributes >> 5) & 0x7, bool(attributes & (1 << 10)), bool(attributes & (1 << 12))),
        "borders": borders,
        "diagonal": diagonal,
        "fill": fill,
        "parse_status": "parsed" if consumed == len(body) and fill_status == "parsed" else fill_status,
        "source_only": {
            "record_size": len(body),
            "consumed_size": consumed,
            "unmapped_attribute_bits": attributes & ~known_attr_mask,
        },
    }


def _parse_hwp_line(body: bytes, offset: int) -> dict[str, Any]:
    return {
        "type": LINE_TYPES.get(_byte(body, offset), "NONE"),
        "width": LINE_WIDTHS.get(_byte(body, offset + 1), "0.1 mm"),
        "color": _colorref(body, offset + 2, allow_none=True),
    }


def _parse_hwp_fill(body: bytes, offset: int) -> tuple[dict[str, Any], int, str]:
    if offset + 4 > len(body):
        return {"type": "none"}, len(body), "truncated_fill_type"
    fill_type = _u32(body, offset)
    cursor = offset + 4
    if fill_type == 0:
        cursor = min(len(body), cursor + 4)
        return {"type": "none"}, cursor, "parsed"
    if fill_type & 1:
        if cursor + 12 > len(body):
            return {"type": "solid"}, len(body), "truncated_solid_fill"
        pattern = _i32(body, cursor + 8)
        cursor += 12
        extra_size, cursor, extra = _extra_fill_bytes(body, cursor)
        alpha = extra[-1] if extra else (_byte(body, cursor) if cursor < len(body) else 0)
        if cursor < len(body) and not extra:
            cursor += 1
        value = {
            "type": "solid",
            "face_color": _colorref(body, offset + 4, allow_none=True),
            "hatch_color": _colorref(body, offset + 8, allow_none=True, keep_alpha=True),
            "hatch_style": HATCH_STYLES.get(pattern) if pattern >= 0 else None,
            "alpha": alpha,
        }
        return value, cursor, "parsed" if extra_size >= 0 else "truncated_extra_fill"
    if fill_type & 4:
        if cursor + 21 > len(body):
            return {"type": "gradation"}, len(body), "truncated_gradation_fill"
        gradation_type = _byte(body, cursor)
        angle = _i32(body, cursor + 1)
        center_x = _i32(body, cursor + 5)
        center_y = _i32(body, cursor + 9)
        step = _i32(body, cursor + 13)
        color_count = max(0, _i32(body, cursor + 17))
        cursor += 21
        positions = []
        if color_count > 2:
            byte_count = color_count * 4
            if cursor + byte_count > len(body):
                return {"type": "gradation"}, len(body), "truncated_gradation_positions"
            positions = [_i32(body, cursor + index * 4) for index in range(color_count)]
            cursor += byte_count
        if cursor + color_count * 4 > len(body):
            return {"type": "gradation"}, len(body), "truncated_gradation_colors"
        colors = [_colorref(body, cursor + index * 4) for index in range(color_count)]
        cursor += color_count * 4
        extra_size, cursor, extra = _extra_fill_bytes(body, cursor)
        step_center = extra[0] if extra else 50
        alpha = _byte(body, cursor) if cursor < len(body) else 0
        if cursor < len(body):
            cursor += 1
        return {
            "type": "gradation",
            "gradation_type": GRADATION_TYPES.get(gradation_type, "LINEAR"),
            "angle": angle,
            "center_x": center_x,
            "center_y": center_y,
            "step": step,
            "positions": positions,
            "colors": colors,
            "step_center": step_center,
            "alpha": alpha,
        }, cursor, "parsed" if extra_size >= 0 else "truncated_extra_fill"
    if fill_type & 2:
        if cursor + 6 > len(body):
            return {"type": "image"}, len(body), "truncated_image_fill"
        mode = _byte(body, cursor)
        brightness = _i8(body, cursor + 1)
        contrast = _i8(body, cursor + 2)
        effect = _byte(body, cursor + 3)
        binary_item_id = _u16(body, cursor + 4)
        cursor += 6
        extra_size, cursor, _extra = _extra_fill_bytes(body, cursor)
        alpha = _byte(body, cursor) if cursor < len(body) else 0
        if cursor < len(body):
            cursor += 1
        return {
            "type": "image",
            "mode": IMAGE_FILL_MODES.get(mode, "FIT_SIZE"),
            "brightness": brightness,
            "contrast": contrast,
            "effect": IMAGE_EFFECTS.get(effect, "REAL_PIC"),
            "binary_item_id_ref": binary_item_id,
            "alpha": alpha,
        }, cursor, "parsed" if extra_size >= 0 else "truncated_extra_fill"
    return {"type": "unsupported", "raw_type": fill_type}, len(body), "unsupported_fill_type"


def _extra_fill_bytes(body: bytes, cursor: int) -> tuple[int, int, bytes]:
    if cursor + 4 > len(body):
        return -1, len(body), b""
    size = _u32(body, cursor)
    cursor += 4
    if cursor + size > len(body):
        return -1, len(body), body[cursor:]
    extra = body[cursor : cursor + size]
    return size, cursor + size, extra


def _parse_hwpx_border_fill(element: ElementTree.Element) -> dict[str, Any]:
    children = {_local_name(child.tag): child for child in list(element)}
    borders = {
        name: _parse_hwpx_line(children.get(f"{name}Border"))
        for name in ("left", "right", "top", "bottom")
    }
    diagonal_element = children.get("diagonal")
    diagonal = _parse_hwpx_line(diagonal_element) if diagonal_element is not None else None
    return {
        "id": _xml_int(element.attrib.get("id")),
        "three_d": _xml_bool(element.attrib.get("threeD")),
        "shadow": _xml_bool(element.attrib.get("shadow")),
        "center_line": str(element.attrib.get("centerLine", "NONE")),
        "break_cell_separate_line": _xml_bool(element.attrib.get("breakCellSeparateLine")),
        "slash": _parse_hwpx_slash(children.get("slash")),
        "back_slash": _parse_hwpx_slash(children.get("backSlash")),
        "borders": borders,
        "diagonal": diagonal,
        "fill": _parse_hwpx_fill(children.get("fillBrush")),
        "parse_status": "parsed",
        "source_only": {},
    }


def _parse_hwpx_line(element: ElementTree.Element | None) -> dict[str, Any]:
    if element is None:
        return {"type": "NONE", "width": "0.1 mm", "color": "#000000"}
    return {
        "type": str(element.attrib.get("type", "NONE")),
        "width": str(element.attrib.get("width", "0.1 mm")),
        "color": str(element.attrib.get("color", "#000000")),
    }


def _parse_hwpx_slash(element: ElementTree.Element | None) -> dict[str, Any]:
    if element is None:
        return _slash_value(0, False, False)
    return {
        "type": str(element.attrib.get("type", "NONE")),
        "crooked": _xml_bool(element.attrib.get("Crooked")),
        "is_counter": _xml_bool(element.attrib.get("isCounter")),
    }


def _parse_hwpx_fill(element: ElementTree.Element | None) -> dict[str, Any]:
    if element is None:
        return {"type": "none"}
    child = next(iter(list(element)), None)
    if child is None:
        return {"type": "none"}
    name = _local_name(child.tag)
    if name == "winBrush":
        return {
            "type": "solid",
            "face_color": str(child.attrib.get("faceColor", "none")),
            "hatch_color": str(child.attrib.get("hatchColor", "#000000")),
            "hatch_style": child.attrib.get("hatchStyle"),
            "alpha": _xml_int(child.attrib.get("alpha")),
        }
    if name == "gradation":
        colors = [
            str(item.attrib.get("value", "#000000"))
            for item in list(child)
            if _local_name(item.tag) == "color"
        ]
        positions = [
            _xml_signed_int(item.attrib.get("pos"))
            for item in list(child)
            if _local_name(item.tag) == "color" and "pos" in item.attrib
        ]
        return {
            "type": "gradation",
            "gradation_type": str(child.attrib.get("type", "LINEAR")),
            "angle": _xml_signed_int(child.attrib.get("angle")),
            "center_x": _xml_signed_int(child.attrib.get("centerX")),
            "center_y": _xml_signed_int(child.attrib.get("centerY")),
            "step": _xml_signed_int(child.attrib.get("step")),
            "positions": positions,
            "colors": colors,
            "step_center": _xml_signed_int(child.attrib.get("stepCenter"), 50),
            "alpha": _xml_int(child.attrib.get("alpha")),
        }
    if name == "imgBrush":
        image = next((item for item in list(child) if _local_name(item.tag) == "img"), None)
        return {
            "type": "image",
            "mode": str(child.attrib.get("mode", "TOTAL")),
            "brightness": _xml_signed_int(image.attrib.get("bright") if image is not None else None),
            "contrast": _xml_signed_int(image.attrib.get("contrast") if image is not None else None),
            "effect": str(image.attrib.get("effect", "REAL_PIC")) if image is not None else "REAL_PIC",
            "binary_item_id_ref": _binary_ref(image.attrib.get("binaryItemIDRef") if image is not None else None),
            "alpha": _xml_int(
                image.attrib.get("alpha") if image is not None else child.attrib.get("alpha")
            ),
        }
    return {"type": "unsupported", "raw_type": name}


def _result(values: list[dict[str, Any]], statuses: Counter[str]) -> dict[str, Any]:
    fill_types = Counter(str(value.get("fill", {}).get("type", "none")) for value in values)
    return {
        "status": "parsed" if set(statuses) <= {"parsed"} else "parsed_with_warnings",
        "counts": {
            "border_fill_count": len(values),
            "fill_type_counts": dict(sorted(fill_types.items())),
            "parse_warning_count": sum(count for status, count in statuses.items() if status != "parsed"),
        },
        "parse_status_counts": dict(sorted(statuses.items())),
        "border_fills": values,
    }


def _default_border_fill() -> dict[str, Any]:
    return {
        "three_d": False,
        "shadow": False,
        "center_line": "NONE",
        "break_cell_separate_line": False,
        "slash": _slash_value(0, False, False),
        "back_slash": _slash_value(0, False, False),
        "borders": {name: {"type": "NONE", "width": "0.1 mm", "color": "#000000"} for name in ("left", "right", "top", "bottom")},
        "diagonal": None,
        "fill": {"type": "none"},
    }


def _slash_value(code: int, crooked: bool, is_counter: bool) -> dict[str, Any]:
    return {"type": SLASH_TYPES.get(code, "NONE"), "crooked": crooked, "is_counter": is_counter}


def _canonical(value: dict[str, Any]) -> dict[str, Any]:
    result = {key: item for key, item in value.items() if key not in {"parse_status", "source_only"}}
    if result.get("diagonal") and result["diagonal"].get("type") == "NONE":
        result["diagonal"] = None
    return result


def _compare_leaves(source: Any, target: Any, path: str, exact: Counter[str], total: Counter[str]) -> None:
    if isinstance(source, dict):
        target_dict = target if isinstance(target, dict) else {}
        for key, value in source.items():
            _compare_leaves(value, target_dict.get(key), f"{path}.{key}", exact, total)
        return
    if isinstance(source, list):
        target_list = target if isinstance(target, list) else []
        total[f"{path}.__count__"] += 1
        exact[f"{path}.__count__"] += int(len(source) == len(target_list))
        for index, value in enumerate(source):
            _compare_leaves(value, target_list[index] if index < len(target_list) else None, f"{path}[]", exact, total)
        return
    total[path] += 1
    exact[path] += int(source == target)


def _colorref(body: bytes, offset: int, *, allow_none: bool = False, keep_alpha: bool = False) -> str:
    if offset + 4 > len(body):
        return "none" if allow_none else "#000000"
    value = _u32(body, offset)
    if allow_none and value == 0xFFFFFFFF:
        return "none"
    rgb = f"{body[offset]:02X}{body[offset + 1]:02X}{body[offset + 2]:02X}"
    if keep_alpha and body[offset + 3]:
        return f"#{body[offset + 3]:02X}{rgb}"
    return f"#{rgb}"


def _binary_ref(value: Any) -> int:
    text = str(value or "")
    digits = "".join(char for char in text if char.isdigit())
    return int(digits or 0)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _byte(body: bytes, offset: int) -> int:
    return body[offset] if 0 <= offset < len(body) else 0


def _i8(body: bytes, offset: int) -> int:
    return struct.unpack_from("<b", body, offset)[0]


def _u16(body: bytes, offset: int) -> int:
    return struct.unpack_from("<H", body, offset)[0]


def _u32(body: bytes, offset: int) -> int:
    return struct.unpack_from("<I", body, offset)[0]


def _i32(body: bytes, offset: int) -> int:
    return struct.unpack_from("<i", body, offset)[0]


def _xml_bool(value: Any) -> bool:
    return str(value or "0").strip().lower() in {"1", "true", "yes"}


def _xml_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(str(value)))
    except (TypeError, ValueError):
        return default


def _xml_signed_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default
