"""Inline paragraph-control semantics shared by HWPX profiling and validation."""

from __future__ import annotations

from collections import Counter
from typing import Any
from xml.etree import ElementTree


INLINE_CONTROL_TAG_TO_CODE = {
    "tab": 9,
    "lineBreak": 10,
    "hyphen": 24,
    "nbSpace": 30,
    "fwSpace": 31,
}
INLINE_CONTROL_CODE_TO_TAG = {
    code: tag for tag, code in INLINE_CONTROL_TAG_TO_CODE.items()
}
VISIBLE_CONSUMING_CONTROL_CODES = frozenset({10, 30, 31})


def parse_hwpx_inline_control_root(root: ElementTree.Element) -> dict[str, Any]:
    """Return text-free inline-control sequences for one HWPX section root."""

    paragraph_sequences: list[list[dict[str, int]]] = []
    code_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    tab_semantics: list[dict[str, int]] = []

    for paragraph in root.iter():
        if _local_name(paragraph.tag) != "p":
            continue
        sequence = _parse_paragraph_controls(paragraph)
        if not sequence:
            continue
        paragraph_sequences.append(sequence)
        for item in sequence:
            code = _as_int(item.get("code"))
            tag = INLINE_CONTROL_CODE_TO_TAG.get(code, "unknown")
            code_counts[str(code)] += 1
            tag_counts[tag] += 1
            if code == 9:
                tab_semantics.append(
                    {
                        "width": _as_int(item.get("width")),
                        "leader": _as_int(item.get("leader")),
                        "type": _as_int(item.get("type")),
                    }
                )

    return {
        "status": "parsed",
        "counts": {
            "paragraph_sequence_count": len(paragraph_sequences),
            "control_count": sum(code_counts.values()),
            "tab_count": code_counts.get("9", 0),
        },
        "control_code_counts": dict(sorted(code_counts.items())),
        "tag_counts": dict(sorted(tag_counts.items())),
        "tab_semantics": tab_semantics,
        "paragraph_sequences": paragraph_sequences,
    }


def model_inline_control_semantics(section: dict[str, Any]) -> dict[str, Any]:
    """Project supported HWP paragraph tokens to the generated HWPX contract."""

    paragraph_sequences: list[list[dict[str, int]]] = []
    code_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    tab_semantics: list[dict[str, int]] = []
    paragraph_controls = section.get("paragraph_controls", [])
    for controls in paragraph_controls if isinstance(paragraph_controls, list) else []:
        if not isinstance(controls, list):
            continue
        sequence = []
        for control in sorted(
            (item for item in controls if isinstance(item, dict)),
            key=lambda item: _as_int(item.get("source_start")),
        ):
            code = _as_int(control.get("code"))
            if code not in INLINE_CONTROL_CODE_TO_TAG:
                continue
            item = {
                "code": code,
                "visible_start": _as_int(control.get("visible_start")),
                "visible_end": _as_int(control.get("visible_end")),
            }
            if code == 9:
                item.update(
                    {
                        "width": _as_int(control.get("tab_width")),
                        "leader": _as_int(control.get("tab_leader")),
                        "type": _as_int(control.get("tab_type")),
                    }
                )
                tab_semantics.append(
                    {
                        "width": item["width"],
                        "leader": item["leader"],
                        "type": item["type"],
                    }
                )
            sequence.append(item)
            code_counts[str(code)] += 1
            tag_counts[INLINE_CONTROL_CODE_TO_TAG[code]] += 1
        if sequence:
            paragraph_sequences.append(sequence)

    return {
        "status": "parsed",
        "counts": {
            "paragraph_sequence_count": len(paragraph_sequences),
            "control_count": sum(code_counts.values()),
            "tab_count": code_counts.get("9", 0),
        },
        "control_code_counts": dict(sorted(code_counts.items())),
        "tag_counts": dict(sorted(tag_counts.items())),
        "tab_semantics": tab_semantics,
        "paragraph_sequences": paragraph_sequences,
    }


def compare_inline_control_semantics(
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    """Compare inline controls without relying on paragraph serialization order."""

    source_counts = _mapping(source.get("counts"))
    target_counts = _mapping(target.get("counts"))
    source_sequences = _sequence_counter(source.get("paragraph_sequences"))
    target_sequences = _sequence_counter(target.get("paragraph_sequences"))
    checks = {
        "source_parsed": source.get("status") == "parsed",
        "target_parsed": target.get("status") == "parsed",
        "control_count": _as_int(source_counts.get("control_count"))
        == _as_int(target_counts.get("control_count")),
        "paragraph_sequence_count": _as_int(source_counts.get("paragraph_sequence_count"))
        == _as_int(target_counts.get("paragraph_sequence_count")),
        "control_code_counts": _count_map(source.get("control_code_counts"))
        == _count_map(target.get("control_code_counts")),
        "tag_counts": _count_map(source.get("tag_counts"))
        == _count_map(target.get("tag_counts")),
        "tab_semantics": _tab_sequence(source.get("tab_semantics"))
        == _tab_sequence(target.get("tab_semantics")),
        "paragraph_control_sequences": source_sequences == target_sequences,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "source_control_count": _as_int(source_counts.get("control_count")),
            "target_control_count": _as_int(target_counts.get("control_count")),
            "source_tab_count": _as_int(source_counts.get("tab_count")),
            "target_tab_count": _as_int(target_counts.get("tab_count")),
        },
    }


def _parse_paragraph_controls(paragraph: ElementTree.Element) -> list[dict[str, int]]:
    sequence: list[dict[str, int]] = []
    visible_position = 0
    for run in list(paragraph):
        if _local_name(run.tag) != "run":
            continue
        for element in list(run):
            if _local_name(element.tag) != "t":
                continue
            visible_position = _parse_text_container(element, sequence, visible_position)
    return sequence


def _parse_text_container(
    element: ElementTree.Element,
    sequence: list[dict[str, int]],
    visible_position: int,
) -> int:
    visible_position += len(element.text or "")
    for child in list(element):
        local = _local_name(child.tag)
        code = INLINE_CONTROL_TAG_TO_CODE.get(local)
        if code is not None:
            item = {
                "code": code,
                "visible_start": visible_position,
                "visible_end": visible_position + int(code in VISIBLE_CONSUMING_CONTROL_CODES),
            }
            if code == 9:
                item.update(
                    {
                        "width": _as_int(child.attrib.get("width")),
                        "leader": _as_int(child.attrib.get("leader")),
                        "type": _as_int(child.attrib.get("type")),
                    }
                )
            sequence.append(item)
            visible_position = item["visible_end"]
        else:
            visible_position = _parse_text_container(child, sequence, visible_position)
        visible_position += len(child.tail or "")
    return visible_position


def _sequence_counter(value: Any) -> Counter[tuple[tuple[tuple[str, int], ...], ...]]:
    counter: Counter[tuple[tuple[tuple[str, int], ...], ...]] = Counter()
    for sequence in value if isinstance(value, list) else []:
        if not isinstance(sequence, list):
            continue
        canonical = tuple(
            tuple(sorted((str(key), _as_int(item_value)) for key, item_value in item.items()))
            for item in sequence
            if isinstance(item, dict)
        )
        if canonical:
            counter[canonical] += 1
    return counter


def _tab_sequence(value: Any) -> list[tuple[int, int, int]]:
    return [
        (
            _as_int(item.get("width")),
            _as_int(item.get("leader")),
            _as_int(item.get("type")),
        )
        for item in value if isinstance(value, list) and isinstance(item, dict)
    ]


def _count_map(value: Any) -> dict[str, int]:
    return {
        str(key): _as_int(item)
        for key, item in value.items()
    } if isinstance(value, dict) else {}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
