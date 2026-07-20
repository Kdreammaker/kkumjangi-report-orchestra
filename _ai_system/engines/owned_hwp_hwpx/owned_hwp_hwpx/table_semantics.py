"""Typed HWP/HWPX table, cell, caption, and nesting semantics."""

from __future__ import annotations

from collections import Counter
import struct
from typing import Any, Iterable
from xml.etree import ElementTree


PAGE_BREAKS = {0: "NONE", 1: "TABLE", 2: "CELL", 3: "CELL"}
VERT_REL_TO = {0: "PAPER", 1: "PAGE", 2: "PARA"}
HORZ_REL_TO = {0: "PAGE", 1: "PAGE", 2: "COLUMN", 3: "PARA"}
VERT_ALIGN = {0: "TOP", 1: "CENTER", 2: "BOTTOM", 3: "INSIDE", 4: "OUTSIDE"}
HORZ_ALIGN = {0: "LEFT", 1: "CENTER", 2: "RIGHT", 3: "INSIDE", 4: "OUTSIDE"}
WIDTH_REL_TO = {0: "PAPER", 1: "PAGE", 2: "COLUMN", 3: "PARA", 4: "ABSOLUTE"}
HEIGHT_REL_TO = {0: "PAPER", 1: "PAGE", 2: "ABSOLUTE"}
TEXT_WRAPS = {0: "SQUARE", 1: "TOP_AND_BOTTOM", 2: "BEHIND_TEXT", 3: "IN_FRONT_OF_TEXT"}
TEXT_FLOWS = {0: "BOTH_SIDES", 1: "LEFT_ONLY", 2: "RIGHT_ONLY", 3: "LARGEST_ONLY"}
NUMBERING_TYPES = {0: "NONE", 1: "PICTURE", 2: "TABLE", 3: "EQUATION"}
CAPTION_SIDES = {0: "LEFT", 1: "RIGHT", 2: "TOP", 3: "BOTTOM"}


def parse_hwp_table_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = list(records)
    paragraph_by_record: dict[int, int] = {}
    paragraph_level: dict[int, int] = {}
    paragraph_index = 0
    for record_index, record in enumerate(values):
        if record.get("tag_name") == "PARA_HEADER":
            paragraph_by_record[record_index] = paragraph_index
            paragraph_level[paragraph_index] = int(record.get("level", 0))
            paragraph_index += 1

    tables: list[dict[str, Any]] = []
    for record_index, record in enumerate(values):
        if record.get("tag_name") != "TABLE":
            continue
        level = int(record.get("level", 0))
        control_index = _find_table_control(values, record_index, level)
        anchor_paragraph = _nearest_paragraph(
            values,
            paragraph_by_record,
            control_index if control_index >= 0 else record_index,
            level - 2,
        )
        caption = _parse_hwp_caption_before_table(
            values,
            paragraph_by_record,
            control_index,
            record_index,
            level,
        )
        table = _parse_hwp_table_body(bytes(record.get("body", b"")), len(tables))
        table["object"] = _parse_hwp_table_object(
            bytes(values[control_index].get("body", b"")) if control_index >= 0 else b""
        )
        table["order_key"] = control_index if control_index >= 0 else record_index
        table["anchor_paragraph_index"] = anchor_paragraph
        table["parent_table_index"] = -1
        table["caption"] = caption
        table["cells"] = _parse_hwp_cells(
            values,
            paragraph_by_record,
            record_index,
            level,
            int(table["row_count"]),
            int(table["column_count"]),
        )
        expected_cells = sum(int(value) for value in table["row_cell_counts"])
        table["cell_count"] = len(table["cells"])
        if table["parse_status"] == "parsed" and len(table["cells"]) != expected_cells:
            table["parse_status"] = "cell_count_mismatch"
        tables.append(table)

    paragraph_container: dict[int, tuple[int, int]] = {}
    for table_index, table in enumerate(tables):
        caption = table.get("caption")
        if isinstance(caption, dict):
            for index in caption.get("paragraph_indexes", []):
                paragraph_container[int(index)] = (table_index, -1)
        for cell_index, cell in enumerate(table.get("cells", [])):
            for index in cell.get("paragraph_indexes", []):
                paragraph_container[int(index)] = (table_index, cell_index)
    for table in tables:
        owner = paragraph_container.get(int(table.get("anchor_paragraph_index", -1)))
        table["parent_table_index"] = owner[0] if owner is not None else -1
    _remove_descendant_table_paragraphs(tables)

    used_list_headers = {
        int(container.get("_record_index"))
        for table in tables
        for container in [
            *(table.get("cells", []) if isinstance(table.get("cells"), list) else []),
            *([table.get("caption")] if isinstance(table.get("caption"), dict) else []),
        ]
        if isinstance(container, dict) and container.get("_record_index") is not None
    }
    direct_table_paragraphs = {
        int(paragraph_index)
        for table in tables
        for container in [
            *(table.get("cells", []) if isinstance(table.get("cells"), list) else []),
            *([table.get("caption")] if isinstance(table.get("caption"), dict) else []),
        ]
        if isinstance(container, dict)
        for paragraph_index in container.get("_direct_paragraph_indexes", [])
    }
    embedded_sub_lists = _parse_hwp_embedded_sub_lists(
        values,
        paragraph_by_record,
        used_list_headers,
        direct_table_paragraphs,
    )
    statuses = Counter(str(table.get("parse_status", "unknown")) for table in tables)
    return _table_result(
        tables,
        paragraph_index,
        paragraph_level,
        statuses,
        embedded_sub_lists=embedded_sub_lists,
    )


def parse_hwpx_table_root(root: ElementTree.Element) -> dict[str, Any]:
    tables: list[dict[str, Any]] = []
    paragraph_levels: dict[int, int] = {}
    paragraph_counter = 0

    def visit(
        element: ElementTree.Element,
        *,
        current_paragraph: int = -1,
        parent_table: int = -1,
        paragraph_level: int = 0,
        container: tuple[str, int, int] | None = None,
    ) -> None:
        nonlocal paragraph_counter
        name = _local_name(element.tag)
        if name == "p":
            current_paragraph = paragraph_counter
            paragraph_levels[current_paragraph] = paragraph_level
            paragraph_counter += 1
            if container is not None:
                kind, table_index, item_index = container
                if kind == "cell":
                    tables[table_index]["cells"][item_index]["paragraph_indexes"].append(current_paragraph)
                elif kind == "caption" and isinstance(tables[table_index].get("caption"), dict):
                    tables[table_index]["caption"]["paragraph_indexes"].append(current_paragraph)
        if name == "tbl":
            table_index = len(tables)
            table = _parse_hwpx_table(element, table_index, parent_table, current_paragraph)
            tables.append(table)
            caption = next((child for child in list(element) if _local_name(child.tag) == "caption"), None)
            for child in list(element):
                child_name = _local_name(child.tag)
                if child_name == "tr":
                    for cell_element in list(child):
                        if _local_name(cell_element.tag) != "tc":
                            continue
                        cell_index = _direct_cell_index(table, cell_element)
                        visit(
                            cell_element,
                            current_paragraph=current_paragraph,
                            parent_table=table_index,
                            paragraph_level=paragraph_level + 2,
                            container=("cell", table_index, cell_index),
                        )
                elif child is caption:
                    visit(
                        child,
                        current_paragraph=current_paragraph,
                        parent_table=table_index,
                        paragraph_level=paragraph_level + 2,
                        container=("caption", table_index, 0),
                    )
                else:
                    visit(
                        child,
                        current_paragraph=current_paragraph,
                        parent_table=table_index,
                        paragraph_level=paragraph_level,
                        container=container,
                    )
            return
        for child in list(element):
            visit(
                child,
                current_paragraph=current_paragraph,
                parent_table=parent_table,
                paragraph_level=paragraph_level,
                container=container,
            )

    visit(root)
    statuses = Counter({"parsed": len(tables)})
    return _table_result(tables, paragraph_counter, paragraph_levels, statuses)


def compare_table_semantics(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    source_values = [_canonical_table(value) for value in source.get("tables", []) if isinstance(value, dict)]
    target_values = [_canonical_table(value) for value in target.get("tables", []) if isinstance(value, dict)]
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    _compare_leaves(source_values, target_values, "tables", exact, total)
    return {
        "status": "pass" if source_values == target_values else "fail",
        "checks": {"tables": source_values == target_values},
        "source_count": len(source_values),
        "target_count": len(target_values),
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def _parse_hwp_table_body(body: bytes, table_index: int) -> dict[str, Any]:
    if len(body) < 22:
        return {
            "table_index": table_index,
            "row_count": 1,
            "column_count": 1,
            "cell_count": 0,
            "row_cell_counts": [1],
            "page_break": "NONE",
            "repeat_header": False,
            "no_adjust": False,
            "cell_spacing": 0,
            "in_margin": _margin(0, 0, 0, 0),
            "border_fill_id_ref": 0,
            "zones": [],
            "parse_status": "short_body",
            "source_only": {"record_size": len(body)},
        }
    attributes = _u32(body, 0)
    rows = _u16(body, 4)
    columns = _u16(body, 6)
    row_array_end = 18 + rows * 2
    if rows <= 0 or columns <= 0 or row_array_end + 4 > len(body):
        return _parse_hwp_table_body(b"", table_index)
    row_cell_counts = [_u16(body, 18 + index * 2) for index in range(rows)]
    border_fill_id = _u16(body, row_array_end)
    zone_count = _u16(body, row_array_end + 2)
    expected_size = row_array_end + 4 + zone_count * 10
    zones = [
        {
            "start_row": _u16(body, row_array_end + 4 + index * 10),
            "start_column": _u16(body, row_array_end + 6 + index * 10),
            "end_row": _u16(body, row_array_end + 8 + index * 10),
            "end_column": _u16(body, row_array_end + 10 + index * 10),
            "border_fill_id_ref": _u16(body, row_array_end + 12 + index * 10),
        }
        for index in range(zone_count)
        if row_array_end + 14 + index * 10 <= len(body)
    ]
    return {
        "table_index": table_index,
        "row_count": rows,
        "column_count": columns,
        "cell_count": sum(row_cell_counts),
        "row_cell_counts": row_cell_counts,
        "page_break": PAGE_BREAKS.get(attributes & 0x3, "NONE"),
        "repeat_header": bool(attributes & 4),
        "no_adjust": bool(attributes & 8),
        "cell_spacing": _u16(body, 8),
        "in_margin": _margin(*struct.unpack_from("<HHHH", body, 10)),
        "border_fill_id_ref": border_fill_id,
        "zones": zones,
        "parse_status": "parsed" if expected_size == len(body) and len(zones) == zone_count else "size_mismatch",
        "source_only": {
            "record_size": len(body),
            "expected_size": expected_size,
            "unmapped_attribute_bits": attributes & ~0xF,
        },
    }


def _parse_hwp_table_object(body: bytes) -> dict[str, Any]:
    if len(body) < 46 or body[:4] != b" lbt":
        return _default_table_object("missing_table_control")
    attributes = _u32(body, 4)
    description_length = _u16(body, 44)
    expected_size = 46 + description_length * 2
    treat_as_char = bool(attributes & 1)
    wrap_code = (attributes >> 21) & 0x7
    text_wrap = "TOP_AND_BOTTOM" if wrap_code == 0 and treat_as_char else TEXT_WRAPS.get(wrap_code, "TOP_AND_BOTTOM")
    return {
        "id": _u32(body, 36),
        "z_order": _i32(body, 24),
        "numbering_type": NUMBERING_TYPES.get(((attributes >> 26) & 0x7) & 0x3, "TABLE"),
        "text_wrap": text_wrap,
        "text_flow": TEXT_FLOWS.get((attributes >> 24) & 0x3, "BOTH_SIDES"),
        "lock": False,
        "dropcap_style": "None",
        "size": {
            "width": _u32(body, 16),
            "width_rel_to": WIDTH_REL_TO.get((attributes >> 15) & 0x7, "ABSOLUTE"),
            "height": _u32(body, 20),
            "height_rel_to": HEIGHT_REL_TO.get((attributes >> 18) & 0x3, "ABSOLUTE"),
            "protect": bool(attributes & (1 << 20)),
        },
        "position": {
            "treat_as_char": treat_as_char,
            "affect_line_spacing": bool(attributes & 4),
            "flow_with_text": bool(attributes & (1 << 13)),
            "allow_overlap": bool(attributes & (1 << 14)),
            "hold_anchor_and_so": False,
            "vert_rel_to": VERT_REL_TO.get((attributes >> 3) & 0x3, "PARA"),
            "horz_rel_to": HORZ_REL_TO.get((attributes >> 8) & 0x3, "PARA"),
            "vert_align": VERT_ALIGN.get((attributes >> 5) & 0x7, "TOP"),
            "horz_align": HORZ_ALIGN.get((attributes >> 10) & 0x7, "LEFT"),
            "vert_offset": _i32(body, 8),
            "horz_offset": _i32(body, 12),
        },
        "out_margin": _margin(*struct.unpack_from("<HHHH", body, 28)),
        "parse_status": "parsed" if expected_size <= len(body) else "truncated_description",
        "source_only": {
            "record_size": len(body),
            "expected_size": expected_size,
            "description_char_count": description_length,
            "prevent_page_break": bool(_i32(body, 40)),
            "unmapped_attribute_bits": attributes & ~0x1FFFFFFD,
        },
    }


def _parse_hwp_cells(
    records: list[dict[str, Any]],
    paragraph_by_record: dict[int, int],
    table_record_index: int,
    table_level: int,
    rows: int,
    columns: int,
) -> list[dict[str, Any]]:
    candidates: list[int] = []
    for index in range(table_record_index + 1, len(records)):
        record = records[index]
        level = int(record.get("level", 0))
        if level < table_level:
            break
        if level != table_level or record.get("tag_name") != "LIST_HEADER":
            continue
        body = bytes(record.get("body", b""))
        if len(body) < 34:
            continue
        column, row, column_span, row_span = struct.unpack_from("<HHHH", body, 8)
        if column < columns and row < rows and column_span >= 1 and row_span >= 1:
            candidates.append(index)

    cells = []
    scope_end = next(
        (
            index
            for index in range(table_record_index + 1, len(records))
            if int(records[index].get("level", 0)) < table_level
        ),
        len(records),
    )
    for cell_index, record_index in enumerate(candidates):
        end = candidates[cell_index + 1] if cell_index + 1 < len(candidates) else scope_end
        paragraphs = [
            paragraph_by_record[index]
            for index in range(record_index + 1, end)
            if index in paragraph_by_record and int(records[index].get("level", 0)) >= table_level
        ]
        direct_paragraphs = [
            paragraph_by_record[index]
            for index in range(record_index + 1, end)
            if index in paragraph_by_record and int(records[index].get("level", 0)) == table_level
        ]
        cell = _parse_hwp_cell(bytes(records[record_index].get("body", b"")), cell_index, paragraphs)
        cell["_record_index"] = record_index
        cell["_direct_paragraph_indexes"] = direct_paragraphs
        cells.append(cell)
    return cells


def _parse_hwp_cell(body: bytes, cell_index: int, paragraphs: list[int]) -> dict[str, Any]:
    attributes = _u32(body, 2)
    extension_flags = _u16(body, 6)
    column, row, column_span, row_span = struct.unpack_from("<HHHH", body, 8)
    width, height = struct.unpack_from("<ii", body, 16)
    margins = tuple(_inherit_margin(value) for value in struct.unpack_from("<HHHH", body, 24))
    tail = body[34:]
    vertical_code = (attributes >> 20) & 0x3
    vertical_align = {0: "TOP", 2: "CENTER", 3: "BOTTOM"}.get(vertical_code, "TOP")
    return {
        "cell_index": cell_index,
        "column": column,
        "row": row,
        "column_span": column_span,
        "row_span": row_span,
        "width": width,
        "height": height,
        "margin": _margin(*margins),
        "border_fill_id_ref": _u16(body, 32),
        "header": bool(extension_flags & 4),
        "has_margin": bool(extension_flags & 1),
        "protect": False,
        "editable": False,
        "dirty": False,
        "sub_list": {
            "text_direction": "HORIZONTAL",
            "line_wrap": "SQUEEZE" if attributes & (1 << 19) else "BREAK",
            "vertical_align": vertical_align,
            "text_width": 0,
            "text_height": 0,
            "has_text_ref": False,
            "has_num_ref": False,
        },
        "paragraph_indexes": paragraphs,
        "parse_status": "parsed" if len(body) == 47 else "size_mismatch",
        "source_only": {
            "record_size": len(body),
            "extension_flags": extension_flags,
            "unmapped_extension_flags": extension_flags & ~0x5,
            "tail_byte_count": len(tail),
            "tail_nonzero_byte_count": sum(value != 0 for value in tail),
        },
    }


def _parse_hwp_caption_before_table(
    records: list[dict[str, Any]],
    paragraph_by_record: dict[int, int],
    control_index: int,
    table_index: int,
    level: int,
) -> dict[str, Any] | None:
    if control_index < 0:
        return None
    candidate = next(
        (
            index
            for index in range(control_index + 1, table_index)
            if records[index].get("tag_name") == "LIST_HEADER"
            and int(records[index].get("level", 0)) == level
            and len(bytes(records[index].get("body", b""))) >= 22
        ),
        -1,
    )
    if candidate < 0:
        return None
    body = bytes(records[candidate].get("body", b""))
    attributes = _u32(body, 8)
    paragraphs = [
        paragraph_by_record[index]
        for index in range(candidate + 1, table_index)
        if index in paragraph_by_record and int(records[index].get("level", 0)) >= level
    ]
    direct_paragraphs = [
        paragraph_by_record[index]
        for index in range(candidate + 1, table_index)
        if index in paragraph_by_record and int(records[index].get("level", 0)) == level
    ]
    return {
        "side": CAPTION_SIDES.get(attributes & 0x3, "TOP"),
        "full_size": bool(attributes & 4),
        "width": _i32(body, 12),
        "gap": _u16(body, 16),
        "last_width": _i32(body, 18),
        "sub_list": _default_sub_list("TOP"),
        "paragraph_indexes": paragraphs,
        "_record_index": candidate,
        "_direct_paragraph_indexes": direct_paragraphs,
        "source_only": {"unmapped_attribute_bits": attributes & ~0x7, "record_size": len(body)},
    }


def _parse_hwpx_table(
    element: ElementTree.Element,
    table_index: int,
    parent_table_index: int,
    anchor_paragraph_index: int,
) -> dict[str, Any]:
    children: dict[str, ElementTree.Element] = {}
    for child in list(element):
        name = _local_name(child.tag)
        if name != "tr":
            children.setdefault(name, child)
    cells = []
    row_counts = []
    for row in [child for child in list(element) if _local_name(child.tag) == "tr"]:
        row_cells = [child for child in list(row) if _local_name(child.tag) == "tc"]
        row_counts.append(len(row_cells))
        cells.extend(_parse_hwpx_cell(cell, len(cells)) for cell in row_cells)
    in_margin = children.get("inMargin")
    caption = children.get("caption")
    zone_list = children.get("cellzoneList")
    if zone_list is None:
        zone_list = children.get("cellZoneList")
    zones = [
        {
            "start_column": _xml_int(zone.attrib.get("startColAddr")),
            "start_row": _xml_int(zone.attrib.get("startRowAddr")),
            "end_column": _xml_int(zone.attrib.get("endColAddr")),
            "end_row": _xml_int(zone.attrib.get("endRowAddr")),
            "border_fill_id_ref": _xml_int(zone.attrib.get("borderFillIDRef")),
        }
        for zone in (list(zone_list) if zone_list is not None else [])
        if _local_name(zone.tag) in {"cellzone", "cellZone"}
    ]
    return {
        "table_index": table_index,
        "anchor_paragraph_index": anchor_paragraph_index,
        "parent_table_index": parent_table_index,
        "row_count": _xml_int(element.attrib.get("rowCnt"), len(row_counts)),
        "column_count": _xml_int(element.attrib.get("colCnt")),
        "cell_count": len(cells),
        "row_cell_counts": row_counts,
        "page_break": str(element.attrib.get("pageBreak", "NONE")),
        "repeat_header": _xml_bool(element.attrib.get("repeatHeader")),
        "no_adjust": _xml_bool(element.attrib.get("noAdjust")),
        "cell_spacing": _xml_int(element.attrib.get("cellSpacing")),
        "in_margin": _parse_xml_margin(in_margin),
        "border_fill_id_ref": _xml_int(element.attrib.get("borderFillIDRef")),
        "zones": zones,
        "object": _parse_hwpx_table_object(element, children),
        "caption": _parse_hwpx_caption(caption),
        "cells": cells,
        "parse_status": "parsed",
        "source_only": {},
    }


def _parse_hwpx_table_object(element: ElementTree.Element, children: dict[str, ElementTree.Element]) -> dict[str, Any]:
    size = children.get("sz")
    position = children.get("pos")
    out_margin = children.get("outMargin")
    return {
        "id": _xml_int(element.attrib.get("id")),
        "z_order": _xml_signed_int(element.attrib.get("zOrder")),
        "numbering_type": str(element.attrib.get("numberingType", "TABLE")),
        "text_wrap": str(element.attrib.get("textWrap", "TOP_AND_BOTTOM")),
        "text_flow": str(element.attrib.get("textFlow", "BOTH_SIDES")),
        "lock": _xml_bool(element.attrib.get("lock")),
        "dropcap_style": str(element.attrib.get("dropcapstyle", "None")),
        "size": {
            "width": _xml_int(size.attrib.get("width") if size is not None else None),
            "width_rel_to": str(size.attrib.get("widthRelTo", "ABSOLUTE")) if size is not None else "ABSOLUTE",
            "height": _xml_int(size.attrib.get("height") if size is not None else None),
            "height_rel_to": str(size.attrib.get("heightRelTo", "ABSOLUTE")) if size is not None else "ABSOLUTE",
            "protect": _xml_bool(size.attrib.get("protect") if size is not None else None),
        },
        "position": {
            "treat_as_char": _xml_bool(position.attrib.get("treatAsChar") if position is not None else None),
            "affect_line_spacing": _xml_bool(position.attrib.get("affectLSpacing") if position is not None else None),
            "flow_with_text": _xml_bool(position.attrib.get("flowWithText") if position is not None else None),
            "allow_overlap": _xml_bool(position.attrib.get("allowOverlap") if position is not None else None),
            "hold_anchor_and_so": _xml_bool(position.attrib.get("holdAnchorAndSO") if position is not None else None),
            "vert_rel_to": str(position.attrib.get("vertRelTo", "PARA")) if position is not None else "PARA",
            "horz_rel_to": str(position.attrib.get("horzRelTo", "PARA")) if position is not None else "PARA",
            "vert_align": str(position.attrib.get("vertAlign", "TOP")) if position is not None else "TOP",
            "horz_align": str(position.attrib.get("horzAlign", "LEFT")) if position is not None else "LEFT",
            "vert_offset": _xml_i32(position.attrib.get("vertOffset") if position is not None else None),
            "horz_offset": _xml_i32(position.attrib.get("horzOffset") if position is not None else None),
        },
        "out_margin": _parse_xml_margin(out_margin),
        "parse_status": "parsed",
        "source_only": {},
    }


def _parse_hwpx_cell(element: ElementTree.Element, cell_index: int) -> dict[str, Any]:
    children: dict[str, ElementTree.Element] = {}
    for child in list(element):
        children.setdefault(_local_name(child.tag), child)
    address = children.get("cellAddr")
    span = children.get("cellSpan")
    size = children.get("cellSz")
    margin = children.get("cellMargin")
    sub_list = children.get("subList")
    return {
        "cell_index": cell_index,
        "column": _xml_int(address.attrib.get("colAddr") if address is not None else None),
        "row": _xml_int(address.attrib.get("rowAddr") if address is not None else None),
        "column_span": _xml_int(span.attrib.get("colSpan") if span is not None else None, 1),
        "row_span": _xml_int(span.attrib.get("rowSpan") if span is not None else None, 1),
        "width": _xml_signed_int(size.attrib.get("width") if size is not None else None),
        "height": _xml_signed_int(size.attrib.get("height") if size is not None else None),
        "margin": _parse_xml_margin(margin),
        "border_fill_id_ref": _xml_int(element.attrib.get("borderFillIDRef")),
        "header": _xml_bool(element.attrib.get("header")),
        "has_margin": _xml_bool(element.attrib.get("hasMargin")),
        "protect": _xml_bool(element.attrib.get("protect")),
        "editable": _xml_bool(element.attrib.get("editable")),
        "dirty": _xml_bool(element.attrib.get("dirty")),
        "sub_list": _parse_hwpx_sub_list(sub_list),
        "paragraph_indexes": [],
        "parse_status": "parsed",
        "source_only": {},
        "_element_id": id(element),
    }


def _parse_hwpx_caption(element: ElementTree.Element | None) -> dict[str, Any] | None:
    if element is None:
        return None
    sub_list = next((child for child in list(element) if _local_name(child.tag) == "subList"), None)
    return {
        "side": str(element.attrib.get("side", "TOP")),
        "full_size": _xml_bool(element.attrib.get("fullSz")),
        "width": _xml_signed_int(element.attrib.get("width")),
        "gap": _xml_signed_int(element.attrib.get("gap")),
        "last_width": _xml_signed_int(element.attrib.get("lastWidth")),
        "sub_list": _parse_hwpx_sub_list(sub_list),
        "paragraph_indexes": [],
        "source_only": {},
    }


def _parse_hwpx_sub_list(element: ElementTree.Element | None) -> dict[str, Any]:
    if element is None:
        return _default_sub_list("TOP")
    return {
        "text_direction": str(element.attrib.get("textDirection", "HORIZONTAL")),
        "line_wrap": str(element.attrib.get("lineWrap", "BREAK")),
        "vertical_align": str(element.attrib.get("vertAlign", "TOP")),
        "text_width": _xml_signed_int(element.attrib.get("textWidth")),
        "text_height": _xml_signed_int(element.attrib.get("textHeight")),
        "has_text_ref": _xml_bool(element.attrib.get("hasTextRef")),
        "has_num_ref": _xml_bool(element.attrib.get("hasNumRef")),
    }


def _direct_cell_index(table: dict[str, Any], element: ElementTree.Element) -> int:
    element_id = id(element)
    for index, cell in enumerate(table.get("cells", [])):
        if cell.get("_element_id") == element_id:
            return index
    return 0


def _remove_descendant_table_paragraphs(tables: list[dict[str, Any]]) -> None:
    children: dict[int, list[int]] = {}
    for table_index, table in enumerate(tables):
        parent = int(table.get("parent_table_index", -1))
        if parent >= 0:
            children.setdefault(parent, []).append(table_index)

    def descendants(table_index: int) -> set[int]:
        result: set[int] = set()
        pending = list(children.get(table_index, []))
        while pending:
            child = pending.pop()
            if child in result:
                continue
            result.add(child)
            pending.extend(children.get(child, []))
        return result

    for table_index, table in enumerate(tables):
        excluded: set[int] = set()
        for descendant_index in descendants(table_index):
            descendant = tables[descendant_index]
            caption = descendant.get("caption")
            if isinstance(caption, dict):
                excluded.update(int(value) for value in caption.get("paragraph_indexes", []))
            for cell in descendant.get("cells", []):
                if isinstance(cell, dict):
                    excluded.update(int(value) for value in cell.get("paragraph_indexes", []))
        if not excluded:
            continue
        caption = table.get("caption")
        if isinstance(caption, dict):
            caption["paragraph_indexes"] = [
                value for value in caption.get("paragraph_indexes", []) if int(value) not in excluded
            ]
        for cell in table.get("cells", []):
            if isinstance(cell, dict):
                cell["paragraph_indexes"] = [
                    value for value in cell.get("paragraph_indexes", []) if int(value) not in excluded
                ]


def _parse_hwp_embedded_sub_lists(
    records: list[dict[str, Any]],
    paragraph_by_record: dict[int, int],
    used_list_headers: set[int],
    direct_table_paragraphs: set[int],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for record_index, record in enumerate(records):
        if record_index in used_list_headers or record.get("tag_name") != "LIST_HEADER":
            continue
        level = int(record.get("level", 0))
        end = len(records)
        for index in range(record_index + 1, len(records)):
            sibling = records[index]
            sibling_level = int(sibling.get("level", 0))
            if sibling_level < level or (
                sibling_level == level and sibling.get("tag_name") == "LIST_HEADER"
            ):
                end = index
                break
        paragraphs = [
            paragraph_by_record[index]
            for index in range(record_index + 1, end)
            if index in paragraph_by_record and int(records[index].get("level", 0)) >= level
            and paragraph_by_record[index] not in direct_table_paragraphs
        ]
        if not paragraphs:
            continue
        anchor = _nearest_lower_paragraph(
            records,
            paragraph_by_record,
            record_index,
            level,
        )
        candidates.append(
            {
                "anchor_paragraph_index": anchor,
                "paragraph_indexes": paragraphs,
                "record_level": level,
                "order_key": record_index,
                "_record_index": record_index,
            }
        )

    for index, candidate in enumerate(candidates):
        nested_paragraphs = {
            paragraph
            for descendant in candidates[index + 1 :]
            if int(descendant.get("record_level", 0)) > int(candidate.get("record_level", 0))
            and set(descendant.get("paragraph_indexes", [])) <= set(candidate.get("paragraph_indexes", []))
            for paragraph in descendant.get("paragraph_indexes", [])
        }
        if nested_paragraphs:
            candidate["paragraph_indexes"] = [
                paragraph
                for paragraph in candidate.get("paragraph_indexes", [])
                if paragraph not in nested_paragraphs
            ]
    return [value for value in candidates if value.get("paragraph_indexes")]


def _nearest_lower_paragraph(
    records: list[dict[str, Any]],
    paragraph_by_record: dict[int, int],
    start: int,
    level: int,
) -> int:
    for index in range(start - 1, -1, -1):
        if index in paragraph_by_record and int(records[index].get("level", 0)) < level:
            return paragraph_by_record[index]
    return -1


def _find_table_control(records: list[dict[str, Any]], table_index: int, table_level: int) -> int:
    for index in range(table_index - 1, -1, -1):
        record = records[index]
        level = int(record.get("level", 0))
        if level < table_level - 1:
            break
        if level == table_level - 1 and record.get("tag_name") == "CTRL_HEADER":
            if bytes(record.get("body", b""))[:4] == b" lbt":
                return index
    return -1


def _nearest_paragraph(
    records: list[dict[str, Any]],
    paragraph_by_record: dict[int, int],
    start: int,
    expected_level: int,
) -> int:
    for index in range(start - 1, -1, -1):
        if index in paragraph_by_record and int(records[index].get("level", 0)) == expected_level:
            return paragraph_by_record[index]
        if int(records[index].get("level", 0)) < expected_level:
            break
    return -1


def _table_result(
    tables: list[dict[str, Any]],
    paragraph_count: int,
    paragraph_levels: dict[int, int],
    statuses: Counter[str],
    *,
    embedded_sub_lists: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    cells = [cell for table in tables for cell in table.get("cells", [])]
    captions = [table.get("caption") for table in tables if isinstance(table.get("caption"), dict)]
    return {
        "status": "parsed" if set(statuses) <= {"parsed"} else "parsed_with_warnings",
        "counts": {
            "table_count": len(tables),
            "cell_count": len(cells),
            "merged_cell_count": sum(int(cell.get("column_span", 1)) > 1 or int(cell.get("row_span", 1)) > 1 for cell in cells),
            "nested_table_count": sum(int(table.get("parent_table_index", -1)) >= 0 for table in tables),
            "caption_count": len(captions),
            "zone_count": sum(len(table.get("zones", [])) for table in tables),
            "paragraph_count": paragraph_count,
            "embedded_sub_list_count": len(embedded_sub_lists or []),
            "parse_warning_count": sum(count for status, count in statuses.items() if status != "parsed"),
        },
        "parse_status_counts": dict(sorted(statuses.items())),
        "paragraph_levels": {str(key): int(value) for key, value in sorted(paragraph_levels.items())},
        "embedded_sub_lists": embedded_sub_lists or [],
        "tables": tables,
    }


def _canonical_table(value: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: item
        for key, item in value.items()
        if key not in {
            "parse_status",
            "source_only",
            "table_index",
            "sub_list_count",
            "extra_sub_list_count",
            "order_key",
        }
    }
    result["object"] = _canonical_nested(result.get("object"))
    result["caption"] = _canonical_nested(result.get("caption"))
    result["cells"] = [_canonical_nested(cell) for cell in result.get("cells", [])]
    return result


def _canonical_nested(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _canonical_nested(item)
            for key, item in value.items()
            if key not in {
                "parse_status",
                "source_only",
                "cell_index",
                "_element_id",
                "_record_index",
                "_direct_paragraph_indexes",
                "render_paragraph_indexes",
            }
        }
    if isinstance(value, list):
        return [_canonical_nested(item) for item in value]
    return value


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


def _default_table_object(status: str) -> dict[str, Any]:
    return {
        "id": 0,
        "z_order": 0,
        "numbering_type": "TABLE",
        "text_wrap": "TOP_AND_BOTTOM",
        "text_flow": "BOTH_SIDES",
        "lock": False,
        "dropcap_style": "None",
        "size": {"width": 0, "width_rel_to": "ABSOLUTE", "height": 0, "height_rel_to": "ABSOLUTE", "protect": False},
        "position": {
            "treat_as_char": False,
            "affect_line_spacing": False,
            "flow_with_text": True,
            "allow_overlap": False,
            "hold_anchor_and_so": False,
            "vert_rel_to": "PARA",
            "horz_rel_to": "PARA",
            "vert_align": "TOP",
            "horz_align": "LEFT",
            "vert_offset": 0,
            "horz_offset": 0,
        },
        "out_margin": _margin(0, 0, 0, 0),
        "parse_status": status,
        "source_only": {},
    }


def _default_sub_list(vertical_align: str) -> dict[str, Any]:
    return {
        "text_direction": "HORIZONTAL",
        "line_wrap": "BREAK",
        "vertical_align": vertical_align,
        "text_width": 0,
        "text_height": 0,
        "has_text_ref": False,
        "has_num_ref": False,
    }


def _margin(left: int, right: int, top: int, bottom: int) -> dict[str, int]:
    return {"left": int(left), "right": int(right), "top": int(top), "bottom": int(bottom)}


def _inherit_margin(value: int) -> int:
    return 0xFFFFFFFF if value == 0xFFFF else value


def _parse_xml_margin(element: ElementTree.Element | None) -> dict[str, int]:
    if element is None:
        return _margin(0, 0, 0, 0)
    return _margin(*(_xml_signed_int(element.attrib.get(key)) for key in ("left", "right", "top", "bottom")))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


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


def _xml_i32(value: Any, default: int = 0) -> int:
    parsed = _xml_signed_int(value, default)
    return parsed - (1 << 32) if parsed > 0x7FFFFFFF else parsed
