"""HWP page-hiding control semantics used by the owned HWPX writer."""

from __future__ import annotations

import struct
from typing import Any
from xml.etree import ElementTree


PAGE_HIDING_CONTROL_ID = "dhgp"
PAGE_HIDING_ATTRIBUTES = (
    "hideHeader",
    "hideFooter",
    "hideMasterPage",
    "hideBorder",
    "hideFill",
    "hidePageNum",
)


def parse_hwp_page_hiding_control_body(body: bytes) -> dict[str, Any]:
    """Decode the six observed HWP page-hiding attribute bits."""

    if len(body) < 8 or body[:4] != PAGE_HIDING_CONTROL_ID.encode("ascii"):
        return {"status": "not_page_hiding_or_truncated"}
    flags = struct.unpack_from("<I", body, 4)[0]
    return {
        "status": "parsed",
        "flags": flags,
        "attributes": {
            name: 1 if flags & (1 << bit) else 0
            for bit, name in enumerate(PAGE_HIDING_ATTRIBUTES)
        },
        "unknown_flags": flags & ~0x3F,
        "trailing_bytes": len(body) - 8,
    }


def parse_hwpx_page_hiding_root(root: ElementTree.Element) -> dict[str, Any]:
    """Return page-hiding attributes in section document order."""

    values = [
        {
            name: 1 if str(element.attrib.get(name, "0")) == "1" else 0
            for name in PAGE_HIDING_ATTRIBUTES
        }
        for element in root.iter()
        if _local_name(element.tag) == "pageHiding"
    ]
    return _page_hiding_result(values)


def model_page_hiding_semantics(section: dict[str, Any]) -> dict[str, Any]:
    """Project typed model controls to the HWPX page-hiding contract."""

    values = []
    paragraph_controls = section.get("paragraph_controls", [])
    for controls in paragraph_controls if isinstance(paragraph_controls, list) else []:
        for control in controls if isinstance(controls, list) else []:
            page_hiding = control.get("page_hiding") if isinstance(control, dict) else None
            if not isinstance(page_hiding, dict):
                continue
            attributes = page_hiding.get("attributes", {})
            if not isinstance(attributes, dict):
                continue
            values.append(
                {
                    name: 1 if _as_int(attributes.get(name)) else 0
                    for name in PAGE_HIDING_ATTRIBUTES
                }
            )
    return _page_hiding_result(values)


def compare_page_hiding_semantics(
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    source_values = source.get("page_hiding_controls", [])
    target_values = target.get("page_hiding_controls", [])
    checks = {
        "source_parsed": source.get("status") == "parsed",
        "target_parsed": target.get("status") == "parsed",
        "page_hiding_controls_exact": source_values == target_values,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "source_page_hiding_control_count": len(source_values),
            "target_page_hiding_control_count": len(target_values),
        },
    }


def _page_hiding_result(values: list[dict[str, int]]) -> dict[str, Any]:
    return {
        "status": "parsed",
        "counts": {"page_hiding_control_count": len(values)},
        "page_hiding_controls": values,
    }


def _local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1] if "}" in value else value


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
