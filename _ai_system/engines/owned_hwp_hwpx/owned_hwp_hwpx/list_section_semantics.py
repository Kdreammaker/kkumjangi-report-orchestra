"""Typed HWP/HWPX list and section semantics."""

from __future__ import annotations

from collections import Counter
import struct
from typing import Any, Iterable
from xml.etree import ElementTree


TAB_TYPES = {0: "LEFT", 1: "RIGHT", 2: "CENTER", 3: "DECIMAL"}
TAB_LEADERS = {
    0: "NONE",
    1: "SOLID",
    2: "DOT",
    3: "DASH",
    4: "DASH_DOT",
    5: "DASH_DOT_DOT",
    6: "LONG_DASH",
    7: "CIRCLE",
}
HEAD_ALIGNMENTS = {0: "LEFT", 1: "CENTER", 2: "RIGHT"}
NUMBER_FORMATS = {
    0: "DIGIT",
    1: "CIRCLED_DIGIT",
    2: "ROMAN_CAPITAL",
    3: "ROMAN_SMALL",
    4: "LATIN_CAPITAL",
    5: "LATIN_SMALL",
    6: "CIRCLED_LATIN_CAPITAL",
    7: "CIRCLED_LATIN_SMALL",
    8: "HANGUL_SYLLABLE",
    9: "CIRCLED_HANGUL_SYLLABLE",
    10: "HANGUL_JAMO",
    11: "CIRCLED_HANGUL_JAMO",
    12: "HANGUL_PHONETIC",
    13: "IDEOGRAPH",
    14: "CIRCLED_IDEOGRAPH",
}
TEXT_DIRECTIONS = {0: "HORIZONTAL", 1: "VERTICAL"}
PAGE_START_MODES = {0: "BOTH", 1: "EVEN", 2: "ODD"}
PAGE_LANDSCAPES = {0: "WIDELY", 1: "NARROWLY"}
GUTTER_TYPES = {0: "LEFT_ONLY", 1: "LEFT_RIGHT", 2: "TOP_BOTTOM"}
NOTE_LINE_TYPES = {
    0: "NONE",
    1: "SOLID",
    2: "DASH",
    3: "DOT",
    4: "DASH_DOT",
    5: "DASH_DOT_DOT",
    6: "LONG_DASH",
}
NOTE_LINE_WIDTHS = {
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
PAGE_BORDER_TYPES = ("BOTH", "EVEN", "ODD")
FILL_AREAS = {0: "PAPER", 1: "PAGE", 2: "BORDER"}


def parse_hwp_list_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    tabs: list[dict[str, Any]] = []
    numberings: list[dict[str, Any]] = []
    bullets: list[dict[str, Any]] = []
    parse_statuses: Counter[str] = Counter()

    for record in records:
        name = str(record.get("tag_name", ""))
        body = bytes(record.get("body", b""))
        if name == "TAB_DEF":
            value = _parse_hwp_tab_definition(body, len(tabs))
            tabs.append(value)
            parse_statuses[value["parse_status"]] += 1
        elif name == "NUMBERING":
            value = _parse_hwp_numbering(body, len(numberings) + 1)
            numberings.append(value)
            parse_statuses[value["parse_status"]] += 1
        elif name == "BULLET":
            value = _parse_hwp_bullet(body, len(bullets) + 1)
            bullets.append(value)
            parse_statuses[value["parse_status"]] += 1

    return _list_result(tabs, numberings, bullets, parse_statuses)


def parse_hwpx_list_root(root: ElementTree.Element) -> dict[str, Any]:
    tabs = [_parse_hwpx_tab_definition(element) for element in root.iter() if _local_name(element.tag) == "tabPr"]
    numberings = [_parse_hwpx_numbering(element) for element in root.iter() if _local_name(element.tag) == "numbering"]
    bullets = [_parse_hwpx_bullet(element) for element in root.iter() if _local_name(element.tag) == "bullet"]
    statuses = Counter({"parsed": len(tabs) + len(numberings) + len(bullets)})
    return _list_result(tabs, numberings, bullets, statuses)


def parse_hwp_section_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    section_body = next(
        (
            bytes(record.get("body", b""))
            for record in records
            if record.get("tag_name") == "CTRL_HEADER" and bytes(record.get("body", b""))[:4] == b"dces"
        ),
        b"",
    )
    page_body = next(
        (bytes(record.get("body", b"")) for record in records if record.get("tag_name") == "PAGE_DEF"),
        b"",
    )
    note_bodies = [
        bytes(record.get("body", b"")) for record in records if record.get("tag_name") == "FOOTNOTE_SHAPE"
    ]
    border_bodies = [
        bytes(record.get("body", b"")) for record in records if record.get("tag_name") == "PAGE_BORDER_FILL"
    ]

    section = _parse_hwp_section_definition(section_body)
    section["page"] = _parse_hwp_page_definition(page_body)
    section["footnote"] = _parse_hwp_note(note_bodies[0], "footnote") if note_bodies else _default_note("footnote")
    section["endnote"] = _parse_hwp_note(note_bodies[1], "endnote") if len(note_bodies) > 1 else _default_note("endnote")
    section["page_borders"] = [
        _parse_hwp_page_border(body, index) for index, body in enumerate(border_bodies[:3])
    ]
    section["parse_status"] = "parsed" if section_body and page_body else "incomplete"
    section["source_only"] = {
        "representative_language": section.pop("representative_language", 0),
        "extension_byte_count": section.pop("extension_byte_count", 0),
        "extension_nonzero_byte_count": section.pop("extension_nonzero_byte_count", 0),
        "page_border_unmapped_attr_bit_count": sum(
            int(border.pop("unmapped_attr_bits", 0)).bit_count() for border in section["page_borders"]
        ),
    }
    return section


def parse_hwpx_section_root(root: ElementTree.Element) -> list[dict[str, Any]]:
    return [_parse_hwpx_section(element) for element in root.iter() if _local_name(element.tag) == "secPr"]


def compare_list_semantics(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    return _compare_payloads(source, target, ("tab_definitions", "numberings", "bullets"))


def compare_section_semantics(source: list[dict[str, Any]], target: list[dict[str, Any]]) -> dict[str, Any]:
    source_payload = {"sections": [_canonical_section(value) for value in source]}
    target_payload = {"sections": [_canonical_section(value) for value in target]}
    return _compare_payloads(source_payload, target_payload, ("sections",))


def _parse_hwp_tab_definition(body: bytes, definition_id: int) -> dict[str, Any]:
    if len(body) < 8:
        return {
            "id": definition_id,
            "auto_tab_left": False,
            "auto_tab_right": False,
            "items": [],
            "parse_status": "short_body",
        }
    attributes, count, _reserved = struct.unpack_from("<IHH", body, 0)
    expected_size = 8 + count * 8
    items = []
    for offset in range(8, min(len(body), expected_size), 8):
        if offset + 8 > len(body):
            break
        position, tab_type, leader, reserved = struct.unpack_from("<iBBH", body, offset)
        items.append(
            {
                "position": position,
                "type": TAB_TYPES.get(tab_type, "LEFT"),
                "leader": TAB_LEADERS.get(leader, "NONE"),
                "reserved": reserved,
            }
        )
    return {
        "id": definition_id,
        "auto_tab_left": bool(attributes & 1),
        "auto_tab_right": bool(attributes & 2),
        "items": items,
        "parse_status": "parsed" if len(body) == expected_size and len(items) == count else "size_mismatch",
    }


def _parse_hwp_numbering(body: bytes, numbering_id: int) -> dict[str, Any]:
    levels: list[dict[str, Any]] = []
    extended_levels: list[dict[str, Any]] = []
    offset = 0
    status = "parsed"
    for level in range(1, 8):
        head, offset, ok = _read_hwp_paragraph_head(body, offset, level)
        if not ok:
            status = "truncated_base_level"
            break
        levels.append(head)

    start = 0
    level_starts: list[int] = []
    if status == "parsed" and offset + 30 <= len(body):
        start = _u16(body, offset)
        offset += 2
        level_starts = [_u32(body, offset + index * 4) for index in range(7)]
        offset += 28
    elif status == "parsed":
        status = "truncated_base_starts"

    if status == "parsed" and offset < len(body):
        for level in range(8, 11):
            head, offset, ok = _read_hwp_paragraph_head(body, offset, level)
            if not ok:
                status = "truncated_extended_level"
                break
            extended_levels.append(head)
        if status == "parsed":
            remaining_starts = min(3, (len(body) - offset) // 4)
            level_starts.extend(_u32(body, offset + index * 4) for index in range(remaining_starts))
            offset += remaining_starts * 4

    for index, level in enumerate(levels):
        level["start"] = level_starts[index] if index < len(level_starts) else 0
    for index, level in enumerate(extended_levels, start=7):
        level["start"] = level_starts[index] if index < len(level_starts) else 0
    if status == "parsed" and offset != len(body):
        status = "trailing_bytes"
    return {
        "id": numbering_id,
        "start": start,
        "levels": levels,
        "source_only_extended_levels": extended_levels,
        "parse_status": status,
        "consumed_size": offset,
        "record_size": len(body),
    }


def _read_hwp_paragraph_head(body: bytes, offset: int, level: int) -> tuple[dict[str, Any], int, bool]:
    if offset + 14 > len(body):
        return _default_paragraph_head(level), offset, False
    attributes = _u32(body, offset)
    width_adjust = _i16(body, offset + 4)
    text_offset = _i16(body, offset + 6)
    char_pr_id = _u32(body, offset + 8)
    text_length = _u16(body, offset + 12)
    offset += 14
    byte_length = text_length * 2
    if offset + byte_length > len(body):
        return _default_paragraph_head(level), offset, False
    text = body[offset : offset + byte_length].decode("utf-16le", errors="replace")
    offset += byte_length
    return _paragraph_head(attributes, width_adjust, text_offset, char_pr_id, level, text), offset, True


def _parse_hwp_bullet(body: bytes, bullet_id: int) -> dict[str, Any]:
    if len(body) < 25:
        return {
            "id": bullet_id,
            "char": "\u2022",
            "use_image": False,
            "para_head": _default_paragraph_head(0),
            "check_char": "",
            "source_only_image": {},
            "parse_status": "short_body",
        }
    attributes = _u32(body, 0)
    image_id = _i32(body, 14)
    image_ref = _u16(body, 21)
    return {
        "id": bullet_id,
        "char": chr(_u16(body, 12)),
        "use_image": image_id != 0,
        "para_head": _paragraph_head(
            attributes,
            _i16(body, 4),
            _i16(body, 6),
            _u32(body, 8),
            0,
            "",
            bullet=True,
        ),
        "check_char": _wchar(body, 23),
        "source_only_image": {
            "image_id": image_id,
            "brightness": _i8(body, 18),
            "contrast": _i8(body, 19),
            "effect": body[20],
            "bin_item_ref": image_ref,
        },
        "parse_status": "parsed" if len(body) == 25 else "trailing_bytes",
    }


def _paragraph_head(
    attributes: int,
    width_adjust: int,
    text_offset: int,
    char_pr_id: int,
    level: int,
    text: str,
    *,
    bullet: bool = False,
) -> dict[str, Any]:
    format_code = (attributes >> 5) & 0xF
    return {
        "level": level,
        "align": HEAD_ALIGNMENTS.get(attributes & 0x3, "LEFT"),
        "use_instance_width": bool(attributes & (1 << 2)),
        "auto_indent": bool(attributes & (1 << 3)),
        "width_adjust": width_adjust,
        "text_offset_type": "HWPUNIT" if attributes & (1 << 4) else "PERCENT",
        "text_offset": text_offset,
        "num_format": "DIGIT" if bullet else NUMBER_FORMATS.get(format_code, "DIGIT"),
        "char_pr_id_ref": char_pr_id,
        "checkable": False if bullet else format_code == 1,
        "format": text,
    }


def _parse_hwpx_tab_definition(element: ElementTree.Element) -> dict[str, Any]:
    defaults = [
        item
        for branch in element.iter()
        if _local_name(branch.tag) == "default"
        for item in branch.iter()
        if _local_name(item.tag) == "tabItem"
    ]
    direct = [item for item in list(element) if _local_name(item.tag) == "tabItem"]
    cases = [
        item
        for item in element.iter()
        if _local_name(item.tag) == "tabItem" and item.attrib.get("unit") == "HWPUNIT"
    ]
    selected = defaults or direct or cases
    items = []
    for item in selected:
        position = _xml_signed_int(item.attrib.get("pos"))
        if not defaults and not direct and item.attrib.get("unit") == "HWPUNIT":
            position *= 2
        items.append(
            {
                "position": position,
                "type": str(item.attrib.get("type", "LEFT")),
                "leader": str(item.attrib.get("leader", "NONE")),
                "reserved": 0,
            }
        )
    return {
        "id": _xml_int(element.attrib.get("id")),
        "auto_tab_left": _xml_bool(element.attrib.get("autoTabLeft")),
        "auto_tab_right": _xml_bool(element.attrib.get("autoTabRight")),
        "items": items,
        "parse_status": "parsed",
    }


def _parse_hwpx_numbering(element: ElementTree.Element) -> dict[str, Any]:
    levels = [_parse_hwpx_paragraph_head(child) for child in list(element) if _local_name(child.tag) == "paraHead"]
    return {
        "id": _xml_int(element.attrib.get("id")),
        "start": _xml_int(element.attrib.get("start")),
        "levels": levels,
        "source_only_extended_levels": [],
        "parse_status": "parsed",
        "consumed_size": 0,
        "record_size": 0,
    }


def _parse_hwpx_bullet(element: ElementTree.Element) -> dict[str, Any]:
    head = next((child for child in list(element) if _local_name(child.tag) == "paraHead"), None)
    return {
        "id": _xml_int(element.attrib.get("id")),
        "char": str(element.attrib.get("char", "\u2022")),
        "use_image": _xml_bool(element.attrib.get("useImage")),
        "para_head": _parse_hwpx_paragraph_head(head) if head is not None else _default_paragraph_head(0),
        "check_char": str(element.attrib.get("checkChar", "")),
        "source_only_image": {},
        "parse_status": "parsed",
    }


def _parse_hwpx_paragraph_head(element: ElementTree.Element) -> dict[str, Any]:
    return {
        "level": _xml_int(element.attrib.get("level")),
        "align": str(element.attrib.get("align", "LEFT")),
        "use_instance_width": _xml_bool(element.attrib.get("useInstWidth")),
        "auto_indent": _xml_bool(element.attrib.get("autoIndent")),
        "width_adjust": _xml_signed_int(element.attrib.get("widthAdjust")),
        "text_offset_type": str(element.attrib.get("textOffsetType", "PERCENT")),
        "text_offset": _xml_signed_int(element.attrib.get("textOffset")),
        "num_format": str(element.attrib.get("numFormat", "DIGIT")),
        "char_pr_id_ref": _xml_int(element.attrib.get("charPrIDRef")),
        "checkable": _xml_bool(element.attrib.get("checkable")),
        "format": str(element.text or ""),
        **({"start": _xml_int(element.attrib.get("start"))} if "start" in element.attrib else {}),
    }


def _list_result(
    tabs: list[dict[str, Any]],
    numberings: list[dict[str, Any]],
    bullets: list[dict[str, Any]],
    parse_statuses: Counter[str],
) -> dict[str, Any]:
    return {
        "status": "parsed" if set(parse_statuses) <= {"parsed"} else "parsed_with_warnings",
        "counts": {
            "tab_definition_count": len(tabs),
            "tab_item_count": sum(len(value.get("items", [])) for value in tabs),
            "numbering_count": len(numberings),
            "numbering_level_count": sum(len(value.get("levels", [])) for value in numberings),
            "numbering_extended_level_count": sum(
                len(value.get("source_only_extended_levels", [])) for value in numberings
            ),
            "bullet_count": len(bullets),
            "image_bullet_count": sum(bool(value.get("use_image")) for value in bullets),
            "parse_warning_count": sum(count for status, count in parse_statuses.items() if status != "parsed"),
        },
        "parse_status_counts": dict(sorted(parse_statuses.items())),
        "tab_definitions": tabs,
        "numberings": numberings,
        "bullets": bullets,
    }


def _parse_hwp_section_definition(body: bytes) -> dict[str, Any]:
    if len(body) < 30 or body[:4] != b"dces":
        return _default_section()
    attributes = _u32(body, 4)
    extension = body[30:]
    border = _section_visibility(attributes, hide_bit=3, first_only_bit=8)
    fill = _section_visibility(attributes, hide_bit=4, first_only_bit=9)
    return {
        "text_direction": TEXT_DIRECTIONS.get((attributes >> 16) & 0x7, "HORIZONTAL"),
        "space_columns": _i16(body, 8),
        "tab_stop": _i32(body, 14),
        "tab_stop_value": _i32(body, 14) // 2,
        "tab_stop_unit": "HWPUNIT",
        "outline_shape_id_ref": _u16(body, 18),
        "memo_shape_id_ref": 0,
        "text_vertical_width_head": 0,
        "master_page_count": 0,
        "grid": {
            "line_grid": _i16(body, 10),
            "char_grid": _i16(body, 12),
            "wonggoji_format": bool(attributes & (1 << 22)),
        },
        "start_num": {
            "page_starts_on": PAGE_START_MODES.get((attributes >> 20) & 0x3, "BOTH"),
            "page": _u16(body, 20),
            "pic": _u16(body, 22),
            "tbl": _u16(body, 24),
            "equation": _u16(body, 26),
        },
        "visibility": {
            "hide_first_header": bool(attributes & 1),
            "hide_first_footer": bool(attributes & 2),
            "hide_first_master_page": bool(attributes & 4),
            "border": border,
            "fill": fill,
            "hide_first_page_num": bool(attributes & (1 << 5)),
            "hide_first_empty_line": bool(attributes & (1 << 19)),
            "show_line_number": False,
        },
        "line_number": {"restart_type": 0, "count_by": 0, "distance": 0, "start_number": 0},
        "representative_language": _u16(body, 28),
        "extension_byte_count": len(extension),
        "extension_nonzero_byte_count": sum(value != 0 for value in extension),
    }


def _parse_hwp_page_definition(body: bytes) -> dict[str, Any]:
    if len(body) < 40:
        return _default_page()
    attributes = _u32(body, 36)
    return {
        "landscape": PAGE_LANDSCAPES.get(attributes & 1, "WIDELY"),
        "width": _i32(body, 0),
        "height": _i32(body, 4),
        "gutter_type": GUTTER_TYPES.get((attributes >> 1) & 0x3, "LEFT_ONLY"),
        "margin": {
            "left": _i32(body, 8),
            "right": _i32(body, 12),
            "top": _i32(body, 16),
            "bottom": _i32(body, 20),
            "header": _i32(body, 24),
            "footer": _i32(body, 28),
            "gutter": _i32(body, 32),
        },
    }


def _parse_hwp_note(body: bytes, kind: str) -> dict[str, Any]:
    if len(body) < 28:
        return _default_note(kind)
    attributes = _u32(body, 0)
    format_code = attributes & 0xFF
    placement_code = (attributes >> 8) & 0x3
    numbering_code = (attributes >> 10) & 0x3
    placement = (
        {0: "EACH_COLUMN", 1: "MERGED_COLUMN", 2: "RIGHT_MOST_COLUMN"}.get(placement_code, "EACH_COLUMN")
        if kind == "footnote"
        else {0: "END_OF_DOCUMENT", 1: "END_OF_SECTION"}.get(placement_code, "END_OF_DOCUMENT")
    )
    return {
        "auto_num_format": {
            "type": NUMBER_FORMATS.get(format_code, "DIGIT"),
            "user_char": _wchar(body, 4),
            "prefix_char": _wchar(body, 6),
            "suffix_char": _wchar(body, 8),
            "superscript": bool(attributes & (1 << 12)),
        },
        "note_line": {
            "length": _i32(body, 12),
            "type": NOTE_LINE_TYPES.get(body[22], "SOLID"),
            "width": NOTE_LINE_WIDTHS.get(body[23], "0.12 mm"),
            "color": _colorref(body, 24),
        },
        "note_spacing": {
            "between_notes": _u16(body, 20),
            "below_line": _u16(body, 18),
            "above_line": _u16(body, 16),
        },
        "numbering": {
            "type": {0: "CONTINUOUS", 1: "ON_SECTION", 2: "ON_PAGE"}.get(numbering_code, "CONTINUOUS"),
            "new_num": _u16(body, 10),
        },
        "placement": {"place": placement, "beneath_text": bool(attributes & (1 << 13))},
    }


def _parse_hwp_page_border(body: bytes, index: int) -> dict[str, Any]:
    if len(body) < 14:
        return _default_page_border(index)
    attributes = _u32(body, 0)
    return {
        "type": PAGE_BORDER_TYPES[index] if index < len(PAGE_BORDER_TYPES) else "BOTH",
        "border_fill_id_ref": _u16(body, 12),
        "text_border": "PAPER" if attributes & 1 else "CONTENT",
        "header_inside": bool(attributes & 2),
        "footer_inside": bool(attributes & 4),
        "fill_area": FILL_AREAS.get((attributes >> 3) & 0x3, "PAPER"),
        "offset": {
            "left": _u16(body, 4),
            "right": _u16(body, 6),
            "top": _u16(body, 8),
            "bottom": _u16(body, 10),
        },
        "unmapped_attr_bits": attributes & ~0x1F,
    }


def _parse_hwpx_section(element: ElementTree.Element) -> dict[str, Any]:
    children = {_local_name(child.tag): child for child in list(element) if _local_name(child.tag) != "pageBorderFill"}
    page = children.get("pagePr")
    margin = next((child for child in list(page or []) if _local_name(child.tag) == "margin"), None)
    grid = children.get("grid")
    start = children.get("startNum")
    visibility = children.get("visibility")
    line_number = children.get("lineNumberShape")
    return {
        "text_direction": str(element.attrib.get("textDirection", "HORIZONTAL")),
        "space_columns": _xml_signed_int(element.attrib.get("spaceColumns")),
        "tab_stop": _xml_signed_int(element.attrib.get("tabStop")),
        "tab_stop_value": _xml_signed_int(element.attrib.get("tabStopVal")),
        "tab_stop_unit": str(element.attrib.get("tabStopUnit", "HWPUNIT")),
        "outline_shape_id_ref": _xml_int(element.attrib.get("outlineShapeIDRef")),
        "memo_shape_id_ref": _xml_int(element.attrib.get("memoShapeIDRef")),
        "text_vertical_width_head": _xml_int(element.attrib.get("textVerticalWidthHead")),
        "master_page_count": _xml_int(element.attrib.get("masterPageCnt")),
        "grid": {
            "line_grid": _xml_signed_int(grid.attrib.get("lineGrid") if grid is not None else None),
            "char_grid": _xml_signed_int(grid.attrib.get("charGrid") if grid is not None else None),
            "wonggoji_format": _xml_bool(grid.attrib.get("wonggojiFormat") if grid is not None else None),
        },
        "start_num": {
            "page_starts_on": str(start.attrib.get("pageStartsOn", "BOTH")) if start is not None else "BOTH",
            "page": _xml_int(start.attrib.get("page") if start is not None else None),
            "pic": _xml_int(start.attrib.get("pic") if start is not None else None),
            "tbl": _xml_int(start.attrib.get("tbl") if start is not None else None),
            "equation": _xml_int(start.attrib.get("equation") if start is not None else None),
        },
        "visibility": {
            "hide_first_header": _xml_bool(visibility.attrib.get("hideFirstHeader") if visibility is not None else None),
            "hide_first_footer": _xml_bool(visibility.attrib.get("hideFirstFooter") if visibility is not None else None),
            "hide_first_master_page": _xml_bool(visibility.attrib.get("hideFirstMasterPage") if visibility is not None else None),
            "border": str(visibility.attrib.get("border", "SHOW_ALL")) if visibility is not None else "SHOW_ALL",
            "fill": str(visibility.attrib.get("fill", "SHOW_ALL")) if visibility is not None else "SHOW_ALL",
            "hide_first_page_num": _xml_bool(visibility.attrib.get("hideFirstPageNum") if visibility is not None else None),
            "hide_first_empty_line": _xml_bool(visibility.attrib.get("hideFirstEmptyLine") if visibility is not None else None),
            "show_line_number": _xml_bool(visibility.attrib.get("showLineNumber") if visibility is not None else None),
        },
        "line_number": {
            "restart_type": _xml_int(line_number.attrib.get("restartType") if line_number is not None else None),
            "count_by": _xml_int(line_number.attrib.get("countBy") if line_number is not None else None),
            "distance": _xml_int(line_number.attrib.get("distance") if line_number is not None else None),
            "start_number": _xml_int(line_number.attrib.get("startNumber") if line_number is not None else None),
        },
        "page": {
            "landscape": str(page.attrib.get("landscape", "WIDELY")) if page is not None else "WIDELY",
            "width": _xml_int(page.attrib.get("width") if page is not None else None),
            "height": _xml_int(page.attrib.get("height") if page is not None else None),
            "gutter_type": str(page.attrib.get("gutterType", "LEFT_ONLY")) if page is not None else "LEFT_ONLY",
            "margin": {
                key: _xml_int(margin.attrib.get(key)) if margin is not None else 0
                for key in ("left", "right", "top", "bottom", "header", "footer", "gutter")
            },
        },
        "footnote": _parse_hwpx_note(children.get("footNotePr"), "footnote"),
        "endnote": _parse_hwpx_note(children.get("endNotePr"), "endnote"),
        "page_borders": [
            _parse_hwpx_page_border(child)
            for child in list(element)
            if _local_name(child.tag) == "pageBorderFill"
        ],
        "parse_status": "parsed",
        "source_only": {},
    }


def _parse_hwpx_note(element: ElementTree.Element | None, kind: str) -> dict[str, Any]:
    if element is None:
        return _default_note(kind)
    children = {_local_name(child.tag): child for child in list(element)}
    auto = children.get("autoNumFormat")
    line = children.get("noteLine")
    spacing = children.get("noteSpacing")
    numbering = children.get("numbering")
    placement = children.get("placement")
    return {
        "auto_num_format": {
            "type": str(auto.attrib.get("type", "DIGIT")) if auto is not None else "DIGIT",
            "user_char": str(auto.attrib.get("userChar", "")) if auto is not None else "",
            "prefix_char": str(auto.attrib.get("prefixChar", "")) if auto is not None else "",
            "suffix_char": str(auto.attrib.get("suffixChar", "")) if auto is not None else "",
            "superscript": _xml_bool(auto.attrib.get("supscript") if auto is not None else None),
        },
        "note_line": {
            "length": _xml_signed_int(line.attrib.get("length") if line is not None else None),
            "type": str(line.attrib.get("type", "SOLID")) if line is not None else "SOLID",
            "width": str(line.attrib.get("width", "0.12 mm")) if line is not None else "0.12 mm",
            "color": str(line.attrib.get("color", "#000000")) if line is not None else "#000000",
        },
        "note_spacing": {
            "between_notes": _xml_int(spacing.attrib.get("betweenNotes") if spacing is not None else None),
            "below_line": _xml_int(spacing.attrib.get("belowLine") if spacing is not None else None),
            "above_line": _xml_int(spacing.attrib.get("aboveLine") if spacing is not None else None),
        },
        "numbering": {
            "type": str(numbering.attrib.get("type", "CONTINUOUS")) if numbering is not None else "CONTINUOUS",
            "new_num": _xml_int(numbering.attrib.get("newNum") if numbering is not None else None),
        },
        "placement": {
            "place": str(placement.attrib.get("place", "EACH_COLUMN" if kind == "footnote" else "END_OF_DOCUMENT"))
            if placement is not None
            else ("EACH_COLUMN" if kind == "footnote" else "END_OF_DOCUMENT"),
            "beneath_text": _xml_bool(placement.attrib.get("beneathText") if placement is not None else None),
        },
    }


def _parse_hwpx_page_border(element: ElementTree.Element) -> dict[str, Any]:
    offset = next((child for child in list(element) if _local_name(child.tag) == "offset"), None)
    return {
        "type": str(element.attrib.get("type", "BOTH")),
        "border_fill_id_ref": _xml_int(element.attrib.get("borderFillIDRef")),
        "text_border": str(element.attrib.get("textBorder", "PAPER")),
        "header_inside": _xml_bool(element.attrib.get("headerInside")),
        "footer_inside": _xml_bool(element.attrib.get("footerInside")),
        "fill_area": str(element.attrib.get("fillArea", "PAPER")),
        "offset": {
            key: _xml_int(offset.attrib.get(key)) if offset is not None else 0
            for key in ("left", "right", "top", "bottom")
        },
    }


def _section_visibility(attributes: int, *, hide_bit: int, first_only_bit: int) -> str:
    if attributes & (1 << hide_bit):
        return "HIDE_ALL"
    if attributes & (1 << first_only_bit):
        return "SHOW_FIRST_PAGE"
    return "SHOW_ALL"


def _canonical_list_value(value: dict[str, Any]) -> dict[str, Any]:
    result = {key: item for key, item in value.items() if key not in {"parse_status", "consumed_size", "record_size"}}
    result.pop("source_only_image", None)
    result.pop("source_only_extended_levels", None)
    result.pop("check_char", None)
    return result


def _canonical_section(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key not in {"parse_status", "source_only"}}


def _compare_payloads(
    source: dict[str, Any],
    target: dict[str, Any],
    keys: tuple[str, ...],
) -> dict[str, Any]:
    source_payload: dict[str, Any] = {}
    target_payload: dict[str, Any] = {}
    for key in keys:
        source_value = source.get(key, [])
        target_value = target.get(key, [])
        if key in {"tab_definitions", "numberings", "bullets"}:
            source_value = [_canonical_list_value(item) for item in source_value if isinstance(item, dict)]
            target_value = [_canonical_list_value(item) for item in target_value if isinstance(item, dict)]
        source_payload[key] = source_value
        target_payload[key] = target_value

    checks = {key: source_payload[key] == target_payload[key] for key in keys}
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    for key in keys:
        _compare_leaves(source_payload[key], target_payload[key], key, exact, total)
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "source_counts": {key: len(source_payload[key]) if isinstance(source_payload[key], list) else 1 for key in keys},
        "target_counts": {key: len(target_payload[key]) if isinstance(target_payload[key], list) else 1 for key in keys},
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def _compare_leaves(
    source: Any,
    target: Any,
    path: str,
    exact: Counter[str],
    total: Counter[str],
) -> None:
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


def _default_paragraph_head(level: int) -> dict[str, Any]:
    return {
        "level": level,
        "align": "LEFT",
        "use_instance_width": False,
        "auto_indent": False,
        "width_adjust": 0,
        "text_offset_type": "PERCENT",
        "text_offset": 0,
        "num_format": "DIGIT",
        "char_pr_id_ref": 0xFFFFFFFF,
        "checkable": False,
        "format": "",
    }


def _default_section() -> dict[str, Any]:
    return {
        "text_direction": "HORIZONTAL",
        "space_columns": 1135,
        "tab_stop": 8000,
        "tab_stop_value": 4000,
        "tab_stop_unit": "HWPUNIT",
        "outline_shape_id_ref": 1,
        "memo_shape_id_ref": 0,
        "text_vertical_width_head": 0,
        "master_page_count": 0,
        "grid": {"line_grid": 0, "char_grid": 0, "wonggoji_format": False},
        "start_num": {"page_starts_on": "BOTH", "page": 0, "pic": 0, "tbl": 0, "equation": 0},
        "visibility": {
            "hide_first_header": False,
            "hide_first_footer": False,
            "hide_first_master_page": False,
            "border": "SHOW_ALL",
            "fill": "SHOW_ALL",
            "hide_first_page_num": False,
            "hide_first_empty_line": False,
            "show_line_number": False,
        },
        "line_number": {"restart_type": 0, "count_by": 0, "distance": 0, "start_number": 0},
        "representative_language": 0,
        "extension_byte_count": 0,
        "extension_nonzero_byte_count": 0,
    }


def _default_page() -> dict[str, Any]:
    return {
        "landscape": "WIDELY",
        "width": 59528,
        "height": 84188,
        "gutter_type": "LEFT_ONLY",
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


def _default_note(kind: str) -> dict[str, Any]:
    return {
        "auto_num_format": {
            "type": "DIGIT",
            "user_char": "",
            "prefix_char": "",
            "suffix_char": ")",
            "superscript": False,
        },
        "note_line": {"length": -1, "type": "SOLID", "width": "0.12 mm", "color": "#000000"},
        "note_spacing": {"between_notes": 0, "below_line": 567, "above_line": 850},
        "numbering": {"type": "CONTINUOUS", "new_num": 1},
        "placement": {
            "place": "EACH_COLUMN" if kind == "footnote" else "END_OF_DOCUMENT",
            "beneath_text": False,
        },
    }


def _default_page_border(index: int) -> dict[str, Any]:
    return {
        "type": PAGE_BORDER_TYPES[index] if index < len(PAGE_BORDER_TYPES) else "BOTH",
        "border_fill_id_ref": 0,
        "text_border": "PAPER",
        "header_inside": False,
        "footer_inside": False,
        "fill_area": "PAPER",
        "offset": {"left": 0, "right": 0, "top": 0, "bottom": 0},
        "unmapped_attr_bits": 0,
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _wchar(body: bytes, offset: int) -> str:
    value = _u16(body, offset)
    return "" if value == 0 else chr(value)


def _colorref(body: bytes, offset: int) -> str:
    if offset + 4 > len(body):
        return "#000000"
    return f"#{body[offset]:02X}{body[offset + 1]:02X}{body[offset + 2]:02X}"


def _u16(body: bytes, offset: int) -> int:
    return struct.unpack_from("<H", body, offset)[0]


def _i16(body: bytes, offset: int) -> int:
    return struct.unpack_from("<h", body, offset)[0]


def _u32(body: bytes, offset: int) -> int:
    return struct.unpack_from("<I", body, offset)[0]


def _i32(body: bytes, offset: int) -> int:
    return struct.unpack_from("<i", body, offset)[0]


def _i8(body: bytes, offset: int) -> int:
    return struct.unpack_from("<b", body, offset)[0]


def _xml_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _xml_signed_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _xml_bool(value: Any) -> bool:
    return str(value or "0").strip().lower() in {"1", "true", "yes"}
