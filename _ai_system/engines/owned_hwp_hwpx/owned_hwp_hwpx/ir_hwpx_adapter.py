"""Adapt canonical document IR to the existing owned HWPX writer model."""

from __future__ import annotations

from base64 import b64decode
from copy import deepcopy
from pathlib import Path
import re
from typing import Any


def build_hwpx_writer_model_from_document_ir(ir: dict[str, Any]) -> dict[str, Any]:
    styles = ir.get("styles", {}) if isinstance(ir.get("styles"), dict) else {}
    style_semantics = _style_semantics(styles)
    border_fill_semantics = styles.get("border_fill_semantics", {}) if isinstance(styles.get("border_fill_semantics"), dict) else {}
    border_counts = border_fill_semantics.get("counts", {}) if isinstance(border_fill_semantics.get("counts"), dict) else {}
    border_fill_count = max(1, int(border_counts.get("border_fill_count", 0)))
    resources = [item for item in ir.get("resources", []) if isinstance(item, dict)]
    resource_indexes = {
        str(resource.get("resource_ref", "")): _resource_storage_id(resource, index)
        for index, resource in enumerate(resources)
    }
    sections = [
        _adapt_section(section, index, resource_indexes, border_fill_count)
        for index, section in enumerate(ir.get("sections", []))
    ]
    line_segment_textpos_remap_count = sum(
        int(section.get("line_segment_textpos_remap_count", 0)) for section in sections
    )
    known_layout_control_count = sum(
        sum(int(value) for value in section.get("layout_control_child_counts", {}).values())
        for section in sections
    )
    binary_payloads = [_binary_payload(resource, index) for index, resource in enumerate(resources)]
    paragraph_count = sum(int(section.get("paragraph_count", 0)) for section in sections)
    line_segment_count = sum(int(section.get("line_segment_count", 0)) for section in sections)
    table_count = sum(int(section.get("table_count", 0)) for section in sections)
    picture_count = sum(int(section.get("picture_count", 0)) for section in sections)
    run_count = sum(
        max(1, len(style.get("char_shape_runs", [])))
        for section in sections
        for style in section.get("paragraph_styles", [])
        if isinstance(style, dict)
    )
    table_row_count = sum(
        len(table.get("row_cell_counts", []))
        for section in sections
        for table in section.get("table_shapes", [])
        if isinstance(table, dict)
    )
    table_cell_count = sum(
        len(table.get("cells", []))
        for section in sections
        for table in section.get("table_shapes", [])
        if isinstance(table, dict)
    )
    shape_draw_text_count = sum(
        isinstance(shape.get("draw_text"), dict)
        for section in sections
        for shape in section.get("object_shapes", [])
        if isinstance(shape, dict)
    )
    table_caption_count = sum(
        isinstance(table.get("caption"), dict)
        for section in sections
        for table in section.get("table_shapes", [])
        if isinstance(table, dict)
    )
    char_shapes = style_semantics.get("char_shapes", [])
    para_shapes = style_semantics.get("para_shapes", [])
    list_semantics = styles.get("list_semantics", {}) if isinstance(styles.get("list_semantics"), dict) else {}
    list_counts = list_semantics.get("counts", {}) if isinstance(list_semantics.get("counts"), dict) else {}
    bullet_count = max(
        int(list_counts.get("bullet_count", 0)),
        int(any(_section_has_list(section, "BULLET") for section in sections)),
    )
    numbering_count = max(
        int(list_counts.get("numbering_count", 0)),
        int(any(_section_has_list(section, "NUMBER") for section in sections)),
    )
    return {
        "schema_version": "owned_hwp_hwpx_document_model.v1",
        "status": "model_built",
        "source_profile_status": "owned_document_ir",
        "text_extraction_status": "provided",
        "compatibility_profile": "hancom",
        "rules_applied": [
            "document_ir_v2",
            "hwpx_authoring_html_v1",
            "layout.line_segment_textpos_fit_to_generated_paragraph",
        ],
        "rules_deferred": [],
        "summary": {
            "section_count": len(sections),
            "paragraph_count": paragraph_count,
            "table_count": table_count,
            "table_row_count": table_row_count,
            "table_cell_count": table_cell_count,
            "sub_list_count": table_cell_count + shape_draw_text_count + table_caption_count,
            "picture_count": picture_count,
            "shape_draw_text_count": shape_draw_text_count,
            "page_def_count": len(sections),
            "line_segment_count": line_segment_count,
            "line_segment_textpos_remap_count": line_segment_textpos_remap_count,
            "char_shape_run_count": run_count,
            "known_layout_control_count": known_layout_control_count,
            "bin_data_count": len(binary_payloads),
            "text_char_count": sum(len(text) for section in sections for text in section.get("paragraph_texts", [])),
            "char_pr_count": max(1, len(char_shapes)),
            "para_pr_count": max(1, len(para_shapes)),
            "style_count": max(1, len(styles.get("named_styles", [])) if isinstance(styles.get("named_styles"), list) else 0),
            "border_fill_count": border_fill_count,
            "tab_pr_count": max(1, int(list_counts.get("tab_definition_count", 0))),
            "numbering_count": numbering_count,
            "bullet_count": bullet_count,
        },
        "document_defaults": {
            "font_family": "HancomBatang",
            "language": "ko",
            "page_width_hwpunit": 59528,
            "page_height_hwpunit": 84188,
            "margin_hwpunit": 8504,
        },
        "style_semantics": style_semantics,
        "list_semantics": _ensure_list_semantics(list_semantics, bullet_count, numbering_count),
        "border_fill_semantics": border_fill_semantics,
        "binary_semantics": {},
        "_binary_payloads": binary_payloads,
        "sections": sections,
    }


def _adapt_section(
    section: dict[str, Any],
    section_index: int,
    resource_indexes: dict[str, int],
    border_fill_count: int,
) -> dict[str, Any]:
    paragraph_texts: list[str] = []
    paragraph_styles: list[dict[str, Any]] = []
    paragraph_line_segments: list[list[dict[str, int]]] = []
    paragraph_controls: list[list[dict[str, Any]]] = []
    paragraph_indexes_by_ref: dict[str, int] = {}
    root_indexes: list[int] = []
    tables: list[dict[str, Any]] = []
    objects: list[dict[str, Any]] = []
    bullet_count = 0
    numbering_count = 0
    line_segment_textpos_remap_count = 0

    def add_paragraph(block: dict[str, Any], *, root: bool) -> int:
        nonlocal line_segment_textpos_remap_count
        index = len(paragraph_texts)
        text = str(block.get("text", ""))
        paragraph_texts.append(text)
        paragraph_styles.append(_paragraph_writer_style(block, text, index))
        line_segments = [
            _normalized_line_segment(segment)
            for segment in block.get("line_segments", [])
            if isinstance(segment, dict)
        ]
        if block.get("preserve_line_segment_text_positions"):
            remapped = False
        else:
            line_segments, remapped = _fit_line_segment_text_positions(line_segments, len(text))
        paragraph_line_segments.append(line_segments)
        paragraph_controls.append([
            _fit_inline_control(control, len(text))
            for control in block.get("inline_controls", [])
            if isinstance(control, dict)
        ] + [
            _fit_structural_control(control, len(text))
            for control in block.get("structural_controls", [])
            if isinstance(control, dict)
        ])
        line_segment_textpos_remap_count += int(remapped)
        block_ref = str(block.get("block_ref", ""))
        if block_ref:
            paragraph_indexes_by_ref[block_ref] = index
        if root:
            root_indexes.append(index)
        return index

    def add_anchor() -> int:
        return add_paragraph({"text": "", "runs": [], "paragraph_style": {}}, root=True)

    def add_table(block: dict[str, Any], anchor: int, order: int) -> None:
        tables.extend(_table_writer_shapes(
            block,
            anchor,
            order,
            add_paragraph,
            add_picture,
            add_drawing,
            border_fill_count,
        ))

    def add_picture(block: dict[str, Any], anchor: int, order: int) -> None:
        objects.extend(
            _picture_writer_shapes(
                block,
                anchor,
                order,
                len(objects),
                resource_indexes,
                add_paragraph,
            )
        )

    def add_drawing(block: dict[str, Any], anchor: int, order: int) -> None:
        objects.append({
            "kind": "raw",
            "anchor_paragraph_index": anchor,
            "order_key": order,
            "parent_shape_index": -1,
            "common": {},
            "raw_xml": str(block.get("raw_xml", "")),
        })

    for order, block in enumerate(section.get("blocks", [])):
        if not isinstance(block, dict):
            continue
        kind = str(block.get("kind", "paragraph"))
        if kind in {"paragraph", "heading", "list_item"}:
            add_paragraph(block, root=True)
            if kind == "list_item":
                if block.get("list_kind") == "ordered":
                    numbering_count += 1
                else:
                    bullet_count += 1
        elif kind == "table":
            anchor = paragraph_indexes_by_ref.get(str(block.get("anchor_block_ref", "")))
            if anchor is None:
                anchor = add_anchor()
            add_table(block, anchor, order)
        elif kind == "image":
            if block.get("object_group_owner_ref"):
                continue
            anchor = paragraph_indexes_by_ref.get(str(block.get("anchor_block_ref", "")))
            if anchor is None:
                anchor = add_anchor()
            add_picture(block, anchor, order)
        elif kind == "drawing":
            anchor = paragraph_indexes_by_ref.get(str(block.get("anchor_block_ref", "")))
            if anchor is None:
                anchor = add_anchor()
            add_drawing(block, anchor, order)

    if not paragraph_texts:
        add_anchor()
    page = section.get("page", {}) if isinstance(section.get("page"), dict) else {}
    layout_control_child_counts: dict[str, int] = {}
    for controls in paragraph_controls:
        for control in controls:
            child = str(control.get("render_layout_child", ""))
            if child:
                layout_control_child_counts[child] = layout_control_child_counts.get(child, 0) + 1
    return {
        "section_ref": int(section_index),
        "paragraph_count": len(paragraph_texts),
        "paragraph_texts": paragraph_texts,
        "paragraph_styles": paragraph_styles,
        "paragraph_controls": paragraph_controls,
        "root_paragraph_indexes": root_indexes,
        "line_segment_count": sum(len(group) for group in paragraph_line_segments),
        "line_segment_textpos_remap_count": line_segment_textpos_remap_count,
        "line_segment_semantics": {
            "paragraphs": [
                {
                    "paragraph_index": index,
                    "declared_count": len(group),
                    "segments": group,
                }
                for index, group in enumerate(paragraph_line_segments)
            ],
            "counts": {
                "paragraph_count": len(paragraph_texts),
                "declared_segment_count": sum(len(group) for group in paragraph_line_segments),
                "segment_count": sum(len(group) for group in paragraph_line_segments),
            },
        },
        "page_def_count": 1,
        "page_definitions": [{"page_def_index": 0, **page}],
        "section_semantics": deepcopy(section.get("section_semantics", {})) or {"page": page},
        "table_count": len(tables),
        "table_shapes": tables,
        "object_shapes": objects,
        "picture_count": sum(item.get("kind") == "pic" for item in objects),
        "shape_count": len(objects),
        "bullet_item_count": bullet_count,
        "numbering_item_count": numbering_count,
        "embedded_paragraph_groups": [],
        "layout_control_child_counts": layout_control_child_counts,
        "compatibility_profile": "hancom",
    }


def _paragraph_writer_style(block: dict[str, Any], text: str, paragraph_id: int) -> dict[str, Any]:
    runs = [item for item in block.get("runs", []) if isinstance(item, dict)]
    positions = []
    cursor = 0
    for run in runs:
        positions.append({
            "start": cursor,
            "visible_start": cursor,
            "source_start": cursor,
            "char_shape_id": int(run.get("char_pr_id_ref", 0)),
            "empty_text_count": max(0, min(8, int(run.get("empty_text_container_count", 0)))),
        })
        cursor += len(str(run.get("text", "")))
    try:
        preserved_paragraph_id = int(str(block.get("paragraph_id", "")))
    except (TypeError, ValueError):
        preserved_paragraph_id = paragraph_id + 1
    return {
        "paragraph_id": preserved_paragraph_id,
        "para_shape_id": int(block.get("para_pr_id_ref", 0)),
        "style_id": int(block.get("style_id_ref", 0)),
        "page_break": bool(block.get("page_break")),
        "column_break": bool(block.get("column_break")),
        "merged": bool(block.get("merged")),
        "char_shape_runs": positions,
        "actual_char_shape_run_count": max(1, len(positions)),
        "declared_char_shape_run_count": max(1, len(positions)),
        "declared_char_count": len(text),
    }


def _normalized_line_segment(value: dict[str, Any]) -> dict[str, int]:
    return {
        name: int(value.get(name, 0))
        for name in (
            "textpos", "vertpos", "vertsize", "textheight", "baseline",
            "spacing", "horzpos", "horzsize", "flags",
        )
    }


def _fit_line_segment_text_positions(
    segments: list[dict[str, int]],
    visible_text_length: int,
) -> tuple[list[dict[str, int]], bool]:
    source_max = max((segment["textpos"] for segment in segments), default=0)
    target_max = max(0, int(visible_text_length))
    if source_max <= target_max:
        return segments, False
    for segment in segments:
        segment["textpos"] = min(
            target_max,
            max(0, round(segment["textpos"] * target_max / source_max)),
        )
    return segments, True


def _fit_inline_control(value: dict[str, Any], visible_text_length: int) -> dict[str, Any]:
    limit = max(0, int(visible_text_length))
    visible_start = min(limit, max(0, int(value.get("visible_start", 0))))
    visible_end = min(limit, max(visible_start, int(value.get("visible_end", visible_start))))
    result = {
        "code": int(value.get("code", -1)),
        "source_start": min(limit, max(0, int(value.get("source_start", visible_start)))),
        "visible_start": visible_start,
        "visible_end": visible_end,
    }
    if result["code"] == 9:
        result.update({
            "tab_width": max(0, int(value.get("tab_width", 0))),
            "tab_leader": max(0, int(value.get("tab_leader", 0))),
            "tab_type": max(0, int(value.get("tab_type", 0))),
        })
    return result


def _fit_structural_control(value: dict[str, Any], visible_text_length: int) -> dict[str, Any]:
    limit = max(0, int(visible_text_length))
    position = min(limit, max(0, int(value.get("visible_start", 0))))
    result = deepcopy(value)
    result["source_start"] = position
    result["visible_start"] = position
    result["visible_end"] = position
    return result


def _table_writer_shapes(
    block: dict[str, Any],
    anchor: int,
    order: int,
    add_paragraph,
    add_picture,
    add_drawing,
    border_fill_count: int,
) -> list[dict[str, Any]]:
    cells = []
    row_cell_counts = []
    nested_tables: list[dict[str, Any]] = []
    semantics = block.get("table_semantics") if isinstance(block.get("table_semantics"), dict) else {}
    semantic_cells = semantics.get("cells", []) if isinstance(semantics.get("cells"), list) else []
    semantic_cell_index = 0
    caption_value = block.get("caption") if isinstance(block.get("caption"), dict) else None
    semantic_caption = semantics.get("caption") if isinstance(semantics.get("caption"), dict) else None
    caption = None
    if caption_value is not None:
        indexes = [
            add_paragraph(value, root=False)
            for value in caption_value.get("blocks", [])
            if isinstance(value, dict)
        ]
        caption = {
            **deepcopy(semantic_caption or {}),
            "side": str((semantic_caption or caption_value).get("side", "TOP")),
            "full_size": bool((semantic_caption or caption_value).get("full_size")),
            "width": int((semantic_caption or caption_value).get("width", 0)),
            "gap": int((semantic_caption or caption_value).get("gap", 0)),
            "last_width": int((semantic_caption or caption_value).get("last_width", 0)),
            "paragraph_indexes": indexes,
            "render_paragraph_indexes": indexes,
            "sub_list": deepcopy((semantic_caption or {}).get("sub_list", {})) or {
                "vertical_align": "TOP",
                "line_wrap": "BREAK",
                "text_width": int(caption_value.get("last_width", 0)),
            },
        }
    for row in block.get("rows", []):
        row_values = [cell for cell in row if isinstance(cell, dict)] if isinstance(row, list) else []
        row_cell_counts.append(len(row_values))
        for cell in row_values:
            semantic_cell = (
                semantic_cells[semantic_cell_index]
                if semantic_cell_index < len(semantic_cells) and isinstance(semantic_cells[semantic_cell_index], dict)
                else {}
            )
            semantic_cell_index += 1
            indexes = []
            local_paragraph_indexes: dict[str, int] = {}
            for value in cell.get("blocks", []):
                if not isinstance(value, dict):
                    continue
                if value.get("kind") in {"paragraph", "heading", "list_item"}:
                    paragraph_index = add_paragraph(value, root=False)
                    indexes.append(paragraph_index)
                    block_ref = str(value.get("block_ref", ""))
                    if block_ref:
                        local_paragraph_indexes[block_ref] = paragraph_index
                elif value.get("kind") == "table":
                    nested_anchor = local_paragraph_indexes.get(str(value.get("anchor_block_ref", "")))
                    if nested_anchor is None:
                        nested_anchor = indexes[-1] if indexes else add_paragraph(
                            {"text": "", "runs": [], "paragraph_style": {}},
                            root=False,
                        )
                        if not indexes:
                            indexes.append(nested_anchor)
                    nested_tables.extend(_table_writer_shapes(
                        value,
                        nested_anchor,
                        order * 1000 + len(nested_tables) + 1,
                        add_paragraph,
                        add_picture,
                        add_drawing,
                        border_fill_count,
                    ))
                elif value.get("kind") == "image":
                    if value.get("object_group_owner_ref"):
                        continue
                    image_anchor = local_paragraph_indexes.get(str(value.get("anchor_block_ref", "")))
                    if image_anchor is None:
                        image_anchor = indexes[-1] if indexes else add_paragraph(
                            {"text": "", "runs": [], "paragraph_style": {}},
                            root=False,
                        )
                        if not indexes:
                            indexes.append(image_anchor)
                    add_picture(value, image_anchor, order * 1000 + semantic_cell_index)
                elif value.get("kind") == "drawing":
                    drawing_anchor = local_paragraph_indexes.get(str(value.get("anchor_block_ref", "")))
                    if drawing_anchor is None:
                        drawing_anchor = indexes[-1] if indexes else add_paragraph(
                            {"text": "", "runs": [], "paragraph_style": {}},
                            root=False,
                        )
                        if not indexes:
                            indexes.append(drawing_anchor)
                    add_drawing(value, drawing_anchor, order * 1000 + semantic_cell_index)
            if not indexes:
                indexes = [add_paragraph({"text": "", "runs": [], "paragraph_style": {}}, root=False)]
            cells.append({
                "column": int(cell.get("column", 0)),
                "row": int(cell.get("row", 0)),
                "column_span": max(1, int(cell.get("column_span", 1))),
                "row_span": max(1, int(cell.get("row_span", 1))),
                "width": int(cell.get("width", 0)),
                "height": int(cell.get("height", 0)),
                "margin": deepcopy(semantic_cell.get("margin", cell.get("margin", {}))),
                "border_fill_id_ref": _bounded_ref(cell.get("border_fill_id_ref"), border_fill_count, minimum=1),
                "header": bool(cell.get("header")),
                "has_margin": bool(semantic_cell.get("has_margin", True)),
                "protect": bool(semantic_cell.get("protect")),
                "editable": bool(semantic_cell.get("editable")),
                "dirty": bool(semantic_cell.get("dirty")),
                "paragraph_indexes": indexes,
                "render_paragraph_indexes": indexes,
                "sub_list": deepcopy(semantic_cell.get("sub_list", {})) or {
                    "vertical_align": "CENTER", "line_wrap": "BREAK"
                },
            })
    width = int(block.get("width", 0))
    height = int(block.get("height", 0))
    object_semantics = deepcopy(semantics.get("object", {})) if isinstance(semantics.get("object"), dict) else {}
    if not object_semantics:
        object_semantics = {
            "id": order + 1,
            "z_order": order,
            "numbering_type": "TABLE",
            "text_wrap": "TOP_AND_BOTTOM",
            "text_flow": "BOTH_SIDES",
            "size": {"width": width, "height": height, "width_rel_to": "ABSOLUTE", "height_rel_to": "ABSOLUTE"},
            "position": {"treat_as_char": bool(block.get("treat_as_character", True)), "vert_rel_to": "PARA", "horz_rel_to": "COLUMN"},
        }
    return [{
        **deepcopy(semantics),
        "anchor_paragraph_index": anchor,
        "order_key": order,
        "row_count": max(1, int(block.get("row_count", len(row_cell_counts)))),
        "column_count": max(1, int(block.get("column_count", 1))),
        "row_cell_counts": row_cell_counts,
        "cells": cells,
        "cell_spacing": int(semantics.get("cell_spacing", block.get("cell_spacing", 0))),
        "border_fill_id_ref": _bounded_ref(block.get("border_fill_id_ref"), border_fill_count, minimum=1),
        "repeat_header": bool(semantics.get("repeat_header", block.get("repeat_header"))),
        "page_break": str(semantics.get("page_break", block.get("page_break_policy", "CELL"))),
        "no_adjust": bool(semantics.get("no_adjust")),
        "in_margin": deepcopy(semantics.get("in_margin", {})),
        "zones": deepcopy(semantics.get("zones", [])),
        "caption": caption,
        "object": object_semantics,
    }, *nested_tables]


def _picture_writer_shapes(
    block: dict[str, Any],
    anchor: int,
    order: int,
    shape_index: int,
    resource_indexes: dict[str, int],
    add_paragraph,
) -> list[dict[str, Any]]:
    width = max(1, int(block.get("width", 0)))
    height = max(1, int(block.get("height", 0)))
    intrinsic_width = max(width, int(block.get("intrinsic_width", 0)))
    intrinsic_height = max(height, int(block.get("intrinsic_height", 0)))
    crop = block.get("crop", {}) if isinstance(block.get("crop"), dict) else {}
    if int(crop.get("right", 0)) <= int(crop.get("left", 0)):
        crop = {"left": 0, "right": intrinsic_width, "top": 0, "bottom": intrinsic_height}
    resource_ref = str(block.get("resource_ref", ""))
    storage_id = resource_indexes.get(resource_ref, 0)
    preserved_shapes = [
        deepcopy(value)
        for value in block.get("object_semantics", [])
        if isinstance(value, dict)
    ]
    if preserved_shapes:
        preserved_picture_count = sum(shape.get("kind") == "pic" for shape in preserved_shapes)
        layers = [layer for layer in block.get("overlay_layers", []) if isinstance(layer, dict)]
        layer_index = 0
        for local_index, shape in enumerate(preserved_shapes):
            parent_index = int(shape.get("parent_shape_index", -1))
            shape["parent_shape_index"] = shape_index + parent_index if parent_index >= 0 else -1
            shape["anchor_paragraph_index"] = anchor if parent_index < 0 else -1
            shape["order_key"] = order + local_index
            if shape.get("kind") == "pic":
                specific = shape.get("specific") if isinstance(shape.get("specific"), dict) else {}
                if preserved_picture_count == 1:
                    specific["binary_storage_id"] = storage_id
                shape["specific"] = specific
            if isinstance(shape.get("draw_text"), dict):
                layer = layers[layer_index] if layer_index < len(layers) else {}
                indexes = [
                    add_paragraph(value, root=False)
                    for value in layer.get("blocks", [])
                    if isinstance(value, dict)
                ]
                shape["draw_text"]["paragraph_indexes"] = indexes
                layer_index += 1
        return preserved_shapes
    picture = {
        "kind": "pic",
        "anchor_paragraph_index": anchor,
        "order_key": order,
        "parent_shape_index": -1,
        "element": {
            "group_level": 0,
            "local_version": 1,
            "instance_id": shape_index + 1,
            "original_size": {"width": intrinsic_width, "height": intrinsic_height},
            "current_size": {"width": width, "height": height},
            "rotation": {"angle": 0, "center_x": width // 2, "center_y": height // 2, "rotate_image": True},
            "matrices": [
                {"type": "transMatrix", "values": [1, 0, 0, 0, 1, 0]},
                {"type": "scaMatrix", "values": [width / intrinsic_width, 0, 0, 0, height / intrinsic_height, 0]},
                {"type": "rotMatrix", "values": [1, 0, 0, 0, 1, 0]},
            ],
        },
        "common": {
            "id": shape_index + 1,
            "z_order": order,
            "numbering_type": "PICTURE",
            "text_wrap": "TOP_AND_BOTTOM",
            "text_flow": "BOTH_SIDES",
            "size": {"width": width, "height": height, "width_rel_to": "ABSOLUTE", "height_rel_to": "ABSOLUTE"},
            "position": {"treat_as_char": True, "vert_rel_to": "PARA", "horz_rel_to": "COLUMN"},
        },
        "specific": {
            "instance_id": shape_index + 1,
            "binary_storage_id": storage_id,
            "dimension": {"width": intrinsic_width, "height": intrinsic_height},
            "crop": crop,
            "points": [
                {"x": 0, "y": 0}, {"x": intrinsic_width, "y": 0},
                {"x": intrinsic_width, "y": intrinsic_height}, {"x": 0, "y": intrinsic_height},
            ],
        },
    }
    layers = [layer for layer in block.get("overlay_layers", []) if isinstance(layer, dict)]
    if not layers:
        return [picture]

    group = {
        "kind": "container",
        "anchor_paragraph_index": anchor,
        "order_key": order,
        "parent_shape_index": -1,
        "element": {
            "instance_id": shape_index + 1,
            "original_size": {"width": width, "height": height},
            "current_size": {"width": width, "height": height},
            "rotation": {"angle": 0, "center_x": width // 2, "center_y": height // 2, "rotate_image": False},
            "matrices": [{"type": "transMatrix", "values": [1, 0, 0, 0, 1, 0]}],
        },
        "common": {
            "id": shape_index + 1,
            "z_order": order,
            "numbering_type": "PICTURE",
            "text_wrap": "TOP_AND_BOTTOM",
            "text_flow": "BOTH_SIDES",
            "size": {"width": width, "height": height, "width_rel_to": "ABSOLUTE", "height_rel_to": "ABSOLUTE"},
            "position": {"treat_as_char": True, "flow_with_text": False, "allow_overlap": True, "vert_rel_to": "PARA", "horz_rel_to": "PARA"},
        },
        "specific": {},
    }
    picture["anchor_paragraph_index"] = -1
    picture["parent_shape_index"] = shape_index
    picture["common"] = None
    picture["order_key"] = order + 1
    picture["element"]["group_level"] = 1
    picture["element"]["local_version"] = 1
    shapes = [group, picture]
    for layer_index, layer in enumerate(layers):
        indexes = [
            add_paragraph(value, root=False)
            for value in layer.get("blocks", [])
            if isinstance(value, dict)
        ]
        layer_width = max(1, int(layer.get("width", 0)))
        layer_height = max(1, int(layer.get("height", 0)))
        shapes.append({
            "kind": "rect",
            "anchor_paragraph_index": -1,
            "order_key": order + 2 + layer_index,
            "parent_shape_index": shape_index,
            "element": {
                "group_level": 1,
                "local_version": 1,
                "instance_id": shape_index + 2 + layer_index,
                "offset": {"x": int(layer.get("left", 0)), "y": int(layer.get("top", 0))},
                "original_size": {"width": layer_width, "height": layer_height},
                "current_size": {"width": layer_width, "height": layer_height},
                "rotation": {"angle": 0, "center_x": layer_width // 2, "center_y": layer_height // 2, "rotate_image": False},
                "matrices": [
                    {"type": "transMatrix", "values": [1, 0, int(layer.get("left", 0)), 0, 1, int(layer.get("top", 0))]},
                    {"type": "scaMatrix", "values": [1, 0, 0, 0, 1, 0]},
                    {"type": "rotMatrix", "values": [1, 0, 0, 0, 1, 0]},
                ],
            },
            "common": None,
            "draw_text": {
                "paragraph_indexes": indexes,
                "sub_list": {"vertical_align": str(layer.get("vertical_align", "TOP")), "line_wrap": "BREAK"},
                "margin": layer.get("margin", {}),
                "last_width": layer_width,
            },
            "specific": {
                "ratio": 0,
                "points": [
                    {"x": 0, "y": 0}, {"x": layer_width, "y": 0},
                    {"x": layer_width, "y": layer_height}, {"x": 0, "y": layer_height},
                ],
            },
            "line_shape": {"style": "NONE", "width": 0, "color": "#000000"},
            "fill": {"type": "none"},
        })
    return shapes


def _binary_payload(resource: dict[str, Any], index: int) -> dict[str, Any]:
    media_type = str(resource.get("media_type", "application/octet-stream"))
    source_href = str(resource.get("source_href", ""))
    source_item_id = str(resource.get("source_item_id", ""))
    safe_item_id = source_item_id if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,159}", source_item_id) else ""
    safe_href = source_href if re.fullmatch(r"BinData/[A-Za-z0-9_.-]{1,160}", source_href) else ""
    extension = Path(safe_href).suffix.removeprefix(".").lower() if safe_href else {
        "image/png": "png", "image/jpeg": "jpg", "image/gif": "gif", "image/bmp": "bmp",
        "image/webp": "webp", "image/svg+xml": "svg", "image/wmf": "wmf", "image/emf": "emf",
    }.get(media_type, "bin")
    try:
        payload = b64decode(str(resource.get("payload_base64", "")), validate=True)
    except ValueError:
        payload = b""
    storage_id = _resource_storage_id(resource, index)
    item_id = safe_item_id or f"image{storage_id}"
    return {
        "item_id": item_id,
        "entry_name": safe_href or f"BinData/{item_id}.{extension}",
        "format": extension,
        "kind": "image" if media_type.startswith("image/") else "binary",
        "media_type": media_type,
        "manifest_media_type": str(resource.get("source_media_type", media_type))[:120],
        "is_embedded": bool(resource.get("is_embedded", True)),
        "payload": payload,
        "payload_sha256": str(resource.get("sha256", "")),
    }


def _resource_storage_id(resource: dict[str, Any], index: int) -> int:
    match = re.fullmatch(r"image([1-9][0-9]*)", str(resource.get("source_item_id", "")))
    return int(match.group(1)) if match else index + 1


def _style_semantics(styles: dict[str, Any]) -> dict[str, Any]:
    font_faces = styles.get("font_faces") if isinstance(styles.get("font_faces"), list) else []
    if not font_faces:
        lookup = styles.get("font_lookup", {}) if isinstance(styles.get("font_lookup"), dict) else {}
        groups = []
        for language in ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user"):
            fonts = []
            for raw_id, names in sorted(lookup.items(), key=lambda item: int(item[0]) if str(item[0]).isdigit() else 0):
                if isinstance(names, dict):
                    face = str(names.get(language) or names.get("hangul") or names.get("latin") or "HancomBatang")
                    fonts.append({"id": int(raw_id), "face": face, "type": "TTF", "is_embedded": False})
            groups.append({"language": language, "fonts": fonts})
        font_faces = groups
    return {
        "font_faces": font_faces,
        "char_shapes": styles.get("char_shapes", []),
        "para_shapes": styles.get("para_shapes", []),
    }


def _ensure_list_semantics(value: dict[str, Any], bullet_count: int, numbering_count: int) -> dict[str, Any]:
    result = dict(value)
    if bullet_count and not result.get("bullets"):
        result["bullets"] = [{"id": 1, "char": "\u2022", "para_head": {"level": 0, "text_offset": 50}}]
    if numbering_count and not result.get("numberings"):
        result["numberings"] = [{"id": 1, "start": 1}]
    return result


def _section_has_list(section: dict[str, Any], kind: str) -> bool:
    key = "bullet_item_count" if kind == "BULLET" else "numbering_item_count"
    return int(section.get(key, 0)) > 0


def _bounded_ref(value: Any, count: int, *, minimum: int = 0) -> int:
    try:
        candidate = int(value)
    except (TypeError, ValueError):
        candidate = minimum
    return candidate if minimum <= candidate <= count else minimum
