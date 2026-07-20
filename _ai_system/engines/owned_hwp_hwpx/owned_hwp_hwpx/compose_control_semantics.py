"""HWP character-compose control semantics used by the owned HWPX writer."""

from __future__ import annotations

import struct
import unicodedata
from hashlib import sha256
from typing import Any
from xml.etree import ElementTree


UINT32_MAX = 0xFFFFFFFF
COMPOSE_CONTROL_ID = "spct"

# These are the values demonstrated by all eight compose controls in the
# paired corpus. Unknown values remain unsupported instead of being guessed.
HWP_BORDER_TO_HWPX_CIRCLE = {
    1: "SHAPE_CIRCLE",
    3: "SHAPE_RECTANGLE",
}
HWP_SPREAD_TO_HWPX_COMPOSE = {
    0: "SPREAD",
}


def parse_hwp_compose_control_body(body: bytes) -> dict[str, Any]:
    """Decode one HWP 5.x `tcps`/stored-`spct` control header."""

    if len(body) < 10 or body[:4] != COMPOSE_CONTROL_ID.encode("ascii"):
        return {"status": "not_compose_or_truncated"}

    char_unit_count = struct.unpack_from("<H", body, 4)[0]
    text_end = 6 + char_unit_count * 2
    if len(body) < text_end + 4:
        return {
            "status": "truncated_text_or_header",
            "char_unit_count": char_unit_count,
        }

    border_type = body[text_end]
    char_size = struct.unpack_from("<b", body, text_end + 1)[0]
    spread_type = body[text_end + 2]
    char_shape_count = body[text_end + 3]
    expected_size = text_end + 4 + char_shape_count * 4
    if len(body) < expected_size:
        return {
            "status": "truncated_char_shapes",
            "char_unit_count": char_unit_count,
            "char_shape_count": char_shape_count,
        }

    try:
        source_text = body[6:text_end].decode("utf-16le")
    except UnicodeDecodeError:
        return {
            "status": "invalid_utf16",
            "char_unit_count": char_unit_count,
            "char_shape_count": char_shape_count,
        }

    circle_type = HWP_BORDER_TO_HWPX_CIRCLE.get(border_type)
    compose_type = HWP_SPREAD_TO_HWPX_COMPOSE.get(spread_type)
    if circle_type is None or compose_type is None:
        return {
            "status": "unsupported_enum",
            "char_unit_count": char_unit_count,
            "border_type": border_type,
            "spread_type": spread_type,
            "char_shape_count": char_shape_count,
        }

    raw_char_shape_ids = [
        struct.unpack_from("<I", body, text_end + 4 + index * 4)[0]
        for index in range(char_shape_count)
    ]
    compose_text = _canonical_compose_text(source_text, border_type)
    char_shape_ids = _expand_inherited_char_shape_ids(
        raw_char_shape_ids,
        len(compose_text),
    )
    return {
        "status": "parsed",
        "char_unit_count": char_unit_count,
        "circle_type": circle_type,
        "char_size": char_size,
        "compose_type": compose_type,
        "char_shape_count": char_shape_count,
        "compose_text": compose_text,
        "char_shape_ids": char_shape_ids,
        "trailing_bytes": len(body) - expected_size,
    }


def parse_hwpx_compose_root(root: ElementTree.Element) -> dict[str, Any]:
    """Return text-free compose-control semantics for one HWPX section."""

    values = []
    for element in root.iter():
        if _local_name(element.tag) != "compose":
            continue
        text = str(element.attrib.get("composeText", ""))
        char_shape_ids = [
            _as_int(child.attrib.get("prIDRef"))
            for child in list(element)
            if _local_name(child.tag) == "charPr"
        ]
        values.append(
            {
                "circle_type": str(element.attrib.get("circleType", "")),
                "char_size": _signed_int(element.attrib.get("charSz")),
                "compose_type": str(element.attrib.get("composeType", "")),
                "char_shape_count": _as_int(element.attrib.get("charPrCnt")),
                "compose_text_length": len(text),
                "compose_text_digest": _text_digest(text),
                "char_shape_ids": char_shape_ids,
            }
        )
    return _compose_result(values)


def model_compose_control_semantics(section: dict[str, Any]) -> dict[str, Any]:
    """Project typed model controls to the HWPX compose contract."""

    values = []
    paragraph_controls = section.get("paragraph_controls", [])
    for controls in paragraph_controls if isinstance(paragraph_controls, list) else []:
        for control in controls if isinstance(controls, list) else []:
            if not isinstance(control, dict) or not isinstance(control.get("compose"), dict):
                continue
            compose = control["compose"]
            text = str(compose.get("compose_text", ""))
            values.append(
                {
                    "circle_type": str(compose.get("circle_type", "")),
                    "char_size": _signed_int(compose.get("char_size")),
                    "compose_type": str(compose.get("compose_type", "")),
                    "char_shape_count": _as_int(compose.get("char_shape_count")),
                    "compose_text_length": len(text),
                    "compose_text_digest": _text_digest(text),
                    "char_shape_ids": [
                        _as_int(value) for value in compose.get("char_shape_ids", [])
                    ],
                }
            )
    return _compose_result(values)


def compare_compose_control_semantics(
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    source_values = source.get("compose_controls", [])
    target_values = target.get("compose_controls", [])
    checks = {
        "source_parsed": source.get("status") == "parsed",
        "target_parsed": target.get("status") == "parsed",
        "compose_controls_exact": source_values == target_values,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "source_compose_control_count": len(source_values),
            "target_compose_control_count": len(target_values),
        },
    }


def _canonical_compose_text(value: str, border_type: int) -> str:
    text = unicodedata.normalize("NFKC", value)
    # Hancom's paired conversion replaces this legacy Hanyang rectangle lead
    # glyph while retaining the following private-use number glyph.
    if border_type == 3 and text.startswith("\U000F02BA"):
        text = "?" + text[1:]
    return text


def _expand_inherited_char_shape_ids(values: list[int], text_length: int) -> list[int]:
    result = list(values)
    inherited: int | None = None
    for index in range(min(text_length, len(result))):
        if result[index] != UINT32_MAX:
            inherited = result[index]
        elif inherited is not None:
            result[index] = inherited
    return result


def _compose_result(values: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "parsed",
        "counts": {"compose_control_count": len(values)},
        "compose_controls": values,
    }


def _text_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1] if "}" in value else value


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
