"""HWP footnote and footnote auto-number control semantics."""

from __future__ import annotations

import struct
from typing import Any
from xml.etree import ElementTree


FOOTNOTE_CONTROL_ID = "  nf"
AUTO_NUMBER_CONTROL_ID = "onta"


def parse_hwp_footnote_control_body(body: bytes) -> dict[str, Any]:
    if len(body) < 20 or body[:4] != FOOTNOTE_CONTROL_ID.encode("ascii"):
        return {"status": "not_footnote_or_truncated"}
    return {
        "status": "parsed",
        "number": struct.unpack_from("<I", body, 4)[0],
        "prefix_char": struct.unpack_from("<H", body, 8)[0],
        "suffix_char": struct.unpack_from("<H", body, 10)[0],
        "instance_id": 0,
        "trailing_bytes": len(body) - 20,
    }


def parse_hwp_footnote_auto_number_body(body: bytes) -> dict[str, Any]:
    if len(body) < 16 or body[:4] != AUTO_NUMBER_CONTROL_ID.encode("ascii"):
        return {"status": "not_auto_number_or_truncated"}
    number_type = struct.unpack_from("<I", body, 4)[0]
    if number_type != 1:
        return {"status": "unsupported_auto_number_type", "number_type": number_type}
    return {
        "status": "parsed",
        "number": struct.unpack_from("<I", body, 8)[0],
        "number_type": "FOOTNOTE",
        "prefix_char": struct.unpack_from("<H", body, 12)[0],
        "suffix_char": struct.unpack_from("<H", body, 14)[0],
    }


def parse_hwpx_footnote_root(root: ElementTree.Element) -> dict[str, Any]:
    values = []
    for element in root.iter():
        if _local_name(element.tag) != "footNote":
            continue
        auto_number = next(
            (
                child
                for child in element.iter()
                if _local_name(child.tag) == "autoNum"
            ),
            None,
        )
        values.append(
            {
                "number": _as_int(element.attrib.get("number")),
                "prefix_char": _as_int(element.attrib.get("prefixChar")),
                "suffix_char": _as_int(element.attrib.get("suffixChar")),
                "instance_id": _as_int(element.attrib.get("instId")),
                "auto_number": {
                    "number": _as_int(auto_number.attrib.get("num")) if auto_number is not None else 0,
                    "number_type": str(auto_number.attrib.get("numType", ""))
                    if auto_number is not None
                    else "",
                },
            }
        )
    return _footnote_result(values)


def model_footnote_control_semantics(section: dict[str, Any]) -> dict[str, Any]:
    footnotes = []
    auto_numbers = []
    for controls in section.get("paragraph_controls", []):
        for control in controls if isinstance(controls, list) else []:
            if not isinstance(control, dict):
                continue
            if isinstance(control.get("footnote"), dict):
                footnotes.append(control["footnote"])
            if isinstance(control.get("auto_number"), dict):
                auto_numbers.append(control["auto_number"])
    values = []
    for index, footnote in enumerate(footnotes):
        auto_number = auto_numbers[index] if index < len(auto_numbers) else {}
        values.append(
            {
                "number": _as_int(footnote.get("number")),
                "prefix_char": _as_int(footnote.get("prefix_char")),
                "suffix_char": _as_int(footnote.get("suffix_char")),
                "instance_id": _as_int(footnote.get("instance_id")),
                "auto_number": {
                    "number": _as_int(auto_number.get("number")),
                    "number_type": str(auto_number.get("number_type", "")),
                },
            }
        )
    return _footnote_result(values)


def compare_footnote_control_semantics(
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    source_values = source.get("footnotes", [])
    target_values = target.get("footnotes", [])
    checks = {
        "source_parsed": source.get("status") == "parsed",
        "target_parsed": target.get("status") == "parsed",
        "footnotes_exact": source_values == target_values,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "source_footnote_count": len(source_values),
            "target_footnote_count": len(target_values),
        },
    }


def _footnote_result(values: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "parsed",
        "counts": {"footnote_count": len(values)},
        "footnotes": values,
    }


def _local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1] if "}" in value else value


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
