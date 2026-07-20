"""Render owned document IR as inline-first HWPX authoring HTML."""

from __future__ import annotations

from base64 import urlsafe_b64encode
from hashlib import sha256
from html import escape
import json
from typing import Any

from .document_ir import AUTHORING_HTML_CONTRACT_VERSION


def render_document_ir_to_html(model: dict[str, Any]) -> str:
    page = _first_page(model)
    page_margin = page.get("margin", {}) if isinstance(page.get("margin"), dict) else {}
    page_width_mm = _hwpunit_to_mm(page.get("width", 59528))
    page_height_mm = _hwpunit_to_mm(page.get("height", 84188))
    margins = {
        name: _hwpunit_to_mm(page_margin.get(name, fallback))
        for name, fallback in (("top", 8504), ("right", 8504), ("bottom", 8504), ("left", 8504))
    }
    preview_top = margins["top"] + _hwpunit_to_mm(page_margin.get("header", 0))
    preview_bottom = margins["bottom"] + _hwpunit_to_mm(page_margin.get("footer", 0))
    page_rule = (
        f"@page{{size:{page_width_mm}mm {page_height_mm}mm;"
        f"margin:{preview_top}mm {margins['right']}mm {preview_bottom}mm {margins['left']}mm;}}"
        "html,body{margin:0;padding:0;background:#fff;}"
        "*{box-sizing:border-box;}"
        "section[data-hwpx-section]{break-before:page;}"
        "section[data-hwpx-section=\"1\"]{break-before:auto;}"
        "[data-hwpx-preview-page-break=\"true\"]{break-before:page!important;}"
        "[data-hwpx-preview-negative-indent=\"true\"]{text-indent:0!important;}"
        "[data-hwpx-preview-line-segments=\"true\"]{white-space:pre!important;}"
        "table{break-inside:auto;}tr{break-inside:avoid;}"
    )
    resources = {
        str(resource.get("resource_ref")): resource
        for resource in model.get("resources", [])
        if isinstance(resource, dict)
    }
    sections = "".join(
        _render_section(section, index, resources)
        for index, section in enumerate(model.get("sections", []))
        if isinstance(section, dict)
    )
    title = escape(str(model.get("title") or "HWPX document"))
    document_ref = escape(str(model.get("document_ref", "owned_hwpx_document")), quote=True)
    loss_payload = urlsafe_b64encode(
        json.dumps(model.get("loss_report", {}), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    style_payload = _encoded_json(model.get("styles", {}))
    referenced_resources = _referenced_resource_refs(model)
    preserved_resource_payload = _encoded_json([
        resource
        for resource in model.get("resources", [])
        if isinstance(resource, dict) and str(resource.get("resource_ref", "")) not in referenced_resources
    ])
    body_style = _style({
        "font-family": "'HCR Batang', 'Malgun Gothic', serif",
        "color": "#000000",
        "background": "#ffffff",
        "word-break": "keep-all",
        "overflow-wrap": "break-word",
    })
    return (
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"hwpx-authoring-contract\" content=\"{AUTHORING_HTML_CONTRACT_VERSION}\">"
        f"<title>{title}</title><style data-hwpx-generated-print-rules=\"true\">{page_rule}</style>"
        f"</head><body style=\"{body_style}\" data-hwpx-contract=\"{AUTHORING_HTML_CONTRACT_VERSION}\" "
        f"data-hwpx-document-ref=\"{document_ref}\" data-hwpx-loss-report=\"{loss_payload}\" "
        f"data-hwpx-style-catalog=\"{style_payload}\" "
        f"data-hwpx-preserved-resources=\"{preserved_resource_payload}\">"
        f"<main style=\"width:100%;\">{sections}</main></body></html>\n"
    )


def _render_section(section: dict[str, Any], index: int, resources: dict[str, dict[str, Any]]) -> str:
    page = section.get("page", {}) if isinstance(section.get("page"), dict) else {}
    page_margin = page.get("margin", {}) if isinstance(page.get("margin"), dict) else {}
    attrs = {
        "data-hwpx-section": str(index + 1),
        "data-hwpx-section-ref": str(section.get("section_ref", f"section:{index + 1}")),
        "data-hwpx-page-width": str(page.get("width", 59528)),
        "data-hwpx-page-height": str(page.get("height", 84188)),
        "data-hwpx-margin-left": str(page_margin.get("left", 8504)),
        "data-hwpx-margin-right": str(page_margin.get("right", 8504)),
        "data-hwpx-margin-top": str(page_margin.get("top", 8504)),
        "data-hwpx-margin-bottom": str(page_margin.get("bottom", 8504)),
        "data-hwpx-margin-header": str(page_margin.get("header", 4252)),
        "data-hwpx-margin-footer": str(page_margin.get("footer", 4252)),
        "data-hwpx-margin-gutter": str(page_margin.get("gutter", 0)),
        "data-hwpx-section-semantics": _encoded_json(section.get("section_semantics", {})),
    }
    blocks = section.get("blocks", []) if isinstance(section.get("blocks"), list) else []
    content = _render_blocks(
        blocks,
        resources,
        preview_page_break_refs=_preview_page_break_refs(blocks),
    )
    return f"<section {_attrs(attrs)} style=\"width:100%;min-height:1px;\">{content}</section>"


def _render_blocks(
    blocks: list[dict[str, Any]],
    resources: dict[str, dict[str, Any]],
    *,
    preview_page_break_refs: set[str] | None = None,
) -> str:
    output: list[str] = []
    page_break_refs = preview_page_break_refs or set()
    index = 0
    while index < len(blocks):
        block = blocks[index]
        if block.get("kind") == "list_item":
            list_kind = str(block.get("list_kind") or "unordered")
            group = []
            while index < len(blocks) and blocks[index].get("kind") == "list_item" and str(blocks[index].get("list_kind") or "unordered") == list_kind:
                group.append(blocks[index])
                index += 1
            output.append(_render_list(group, list_kind, resources, page_break_refs))
            continue
        output.append(
            _render_block(
                block,
                resources,
                preview_page_break=str(block.get("block_ref", "")) in page_break_refs,
            )
        )
        index += 1
    return "".join(output)


def _render_block(
    block: dict[str, Any],
    resources: dict[str, dict[str, Any]],
    *,
    preview_page_break: bool = False,
) -> str:
    kind = str(block.get("kind", "paragraph"))
    if kind == "table":
        return _render_table(block, resources)
    if kind == "image":
        return _render_image(block, resources)
    if kind == "drawing":
        attrs = {
            "data-hwpx-raw-drawing": _encoded_json({"raw_xml": str(block.get("raw_xml", ""))}),
            "data-hwpx-block-ref": str(block.get("block_ref", "")),
            "data-hwpx-anchor-block-ref": str(block.get("anchor_block_ref", "")),
        }
        return f"<div {_attrs(attrs)} style=\"display:none;\"></div>"
    return _render_paragraph(
        block,
        "h2" if kind == "heading" else "p",
        preview_page_break=preview_page_break,
    )


def _render_paragraph(
    block: dict[str, Any],
    tag: str,
    *,
    preview_page_break: bool = False,
) -> str:
    paragraph_style = block.get("paragraph_style", {}) if isinstance(block.get("paragraph_style"), dict) else {}
    align = paragraph_style.get("align", {}) if isinstance(paragraph_style.get("align"), dict) else {}
    margin = paragraph_style.get("margin", {}) if isinstance(paragraph_style.get("margin"), dict) else {}
    line_spacing = paragraph_style.get("line_spacing", {}) if isinstance(paragraph_style.get("line_spacing"), dict) else {}
    break_setting = paragraph_style.get("break_setting", {}) if isinstance(paragraph_style.get("break_setting"), dict) else {}
    indent = int(margin.get("indent", 0))
    line_segments = block.get("line_segments", []) if isinstance(block.get("line_segments"), list) else []
    css = {
        "margin": f"{_hwpunit_to_pt(margin.get('prev', 0))}pt {_hwpunit_to_pt(margin.get('right', 0))}pt {_hwpunit_to_pt(margin.get('next', 0))}pt {_hwpunit_to_pt(margin.get('left', 0))}pt",
        "text-indent": f"{_hwpunit_to_pt(indent)}pt",
        "text-align": _text_align(align.get("horizontal")),
        "line-height": _line_height(line_spacing),
        "break-before": "page" if block.get("page_break") or break_setting.get("page_break_before") else "auto",
        "break-after": "avoid" if break_setting.get("keep_with_next") else "auto",
        "white-space": "pre-wrap",
        "min-height": "1em",
    }
    attrs = {
        "data-hwpx-block-ref": str(block.get("block_ref", "")),
        "data-hwpx-block-kind": str(block.get("kind", "paragraph")),
        "data-hwpx-para-pr-id": str(block.get("para_pr_id_ref", 0)),
        "data-hwpx-style-id": str(block.get("style_id_ref", 0)),
        "data-hwpx-paragraph-id": str(block.get("paragraph_id", "")),
        "data-hwpx-merged": "true" if block.get("merged") else "false",
        "data-hwpx-column-break": "true" if block.get("column_break") else "false",
        "data-hwpx-line-segments": _encoded_json(line_segments),
        "data-hwpx-source-text-sha256": sha256(str(block.get("text", "")).encode("utf-8")).hexdigest(),
        "data-hwpx-inline-controls": _encoded_json(block.get("inline_controls", [])),
        "data-hwpx-structural-controls": _encoded_json(block.get("structural_controls", [])),
        "data-hwpx-preview-page-break": "true" if preview_page_break else "false",
        "data-hwpx-preview-negative-indent": "true" if indent < 0 else "false",
        "data-hwpx-preview-line-segments": "true" if line_segments else "false",
        "data-hwpx-empty-runs": "true" if not block.get("runs") else "false",
    }
    runs = block.get("runs", []) if isinstance(block.get("runs"), list) else []
    content = _render_runs(runs, line_segments)
    if not content:
        content = escape(str(block.get("text", ""))) or "&#8203;"
    return f"<{tag} {_attrs(attrs)} style=\"{_style(css)}\">{content}</{tag}>"


def _render_runs(runs: list[dict[str, Any]], line_segments: list[dict[str, Any]]) -> str:
    text_length = sum(len(str(run.get("text", ""))) for run in runs if isinstance(run, dict))
    break_positions = {
        int(segment.get("textpos", 0))
        for segment in line_segments
        if isinstance(segment, dict) and 0 < int(segment.get("textpos", 0)) < text_length
    }
    output = []
    offset = 0
    for index, run in enumerate(runs):
        if not isinstance(run, dict):
            continue
        output.append(_render_run(run, index, offset, break_positions))
        offset += len(str(run.get("text", "")))
    return "".join(output)


def _render_run(
    run: dict[str, Any],
    index: int,
    offset: int,
    break_positions: set[int],
) -> str:
    style = run.get("character_style", {}) if isinstance(run.get("character_style"), dict) else {}
    underline = style.get("underline", {}) if isinstance(style.get("underline"), dict) else {}
    strikeout = style.get("strikeout", {}) if isinstance(style.get("strikeout"), dict) else {}
    decorations = []
    if str(underline.get("type", "NONE")).upper() != "NONE":
        decorations.append("underline")
    if str(strikeout.get("shape", "NONE")).upper() != "NONE":
        decorations.append("line-through")
    css = {
        "font-family": _css_font_family(run.get("font_family")),
        "font-size": f"{max(1, int(style.get('height', 1000))) / 100:g}pt",
        "font-weight": "700" if style.get("bold") else "400",
        "font-style": "italic" if style.get("italic") else "normal",
        "color": _safe_color(style.get("text_color"), "#000000"),
        "background-color": _safe_color(style.get("shade_color"), "transparent", allow_transparent=True),
        "text-decoration": " ".join(decorations) if decorations else "none",
        "vertical-align": "super" if style.get("superscript") else "sub" if style.get("subscript") else "baseline",
    }
    attrs = {
        "data-hwpx-run": str(index + 1),
        "data-hwpx-char-pr-id": str(run.get("char_pr_id_ref", 0)),
        "data-hwpx-empty-text-count": str(max(0, min(8, int(run.get("empty_text_container_count", 0))))),
    }
    text = str(run.get("text", ""))
    boundaries = sorted(
        position - offset
        for position in break_positions
        if offset <= position < offset + len(text)
    )
    fragments = []
    cursor = 0
    for boundary in boundaries:
        fragments.append(escape(text[cursor:boundary]))
        fragments.append('<br data-hwpx-preview-only="line-segment">')
        cursor = boundary
    fragments.append(escape(text[cursor:]))
    return f"<span {_attrs(attrs)} style=\"{_style(css)}\">{''.join(fragments)}</span>"


def _render_list(
    items: list[dict[str, Any]],
    list_kind: str,
    resources: dict[str, dict[str, Any]],
    preview_page_break_refs: set[str],
) -> str:
    tag = "ol" if list_kind == "ordered" else "ul"
    rendered = "".join(
        _render_list_item(
            item,
            preview_page_break=str(item.get("block_ref", "")) in preview_page_break_refs,
        )
        for item in items
    )
    return f"<{tag} data-hwpx-list-kind=\"{list_kind}\" style=\"margin:0 0 6pt 18pt;padding:0;\">{rendered}</{tag}>"


def _render_list_item(item: dict[str, Any], *, preview_page_break: bool = False) -> str:
    line_segments = item.get("line_segments", []) if isinstance(item.get("line_segments"), list) else []
    attrs = {
        "data-hwpx-block-ref": str(item.get("block_ref", "")),
        "data-hwpx-list-level": str(int(item.get("list_level", 0))),
        "data-hwpx-para-pr-id": str(item.get("para_pr_id_ref", 0)),
        "data-hwpx-style-id": str(item.get("style_id_ref", 0)),
        "data-hwpx-paragraph-id": str(item.get("paragraph_id", "")),
        "data-hwpx-merged": "true" if item.get("merged") else "false",
        "data-hwpx-column-break": "true" if item.get("column_break") else "false",
        "data-hwpx-line-segments": _encoded_json(line_segments),
        "data-hwpx-inline-controls": _encoded_json(item.get("inline_controls", [])),
        "data-hwpx-structural-controls": _encoded_json(item.get("structural_controls", [])),
        "data-hwpx-preview-page-break": "true" if preview_page_break else "false",
        "data-hwpx-preview-line-segments": "true" if line_segments else "false",
    }
    runs = [run for run in item.get("runs", []) if isinstance(run, dict)]
    content = _render_runs(runs, line_segments) or escape(str(item.get("text", "")))
    return f"<li {_attrs(attrs)} style=\"margin:0 0 2pt 0;\">{content}</li>"


def _render_table(block: dict[str, Any], resources: dict[str, dict[str, Any]]) -> str:
    width = int(block.get("width", 0))
    table_css = {
        "width": f"{_hwpunit_to_mm(width)}mm" if width > 0 else "100%",
        "height": f"{_hwpunit_to_mm(block.get('height', 0))}mm" if int(block.get("height", 0)) > 0 else "auto",
        "border-collapse": "collapse",
        "border-spacing": f"{_hwpunit_to_pt(block.get('cell_spacing', 0))}pt",
        "margin": "0 0 6pt 0",
        "table-layout": "fixed",
    }
    rows = []
    for row in block.get("rows", []):
        cells = []
        for cell_index, cell in enumerate(row if isinstance(row, list) else []):
            margin = cell.get("margin", {}) if isinstance(cell.get("margin"), dict) else {}
            cell_css = {
                "border": "0.5pt solid #666666",
                "padding": f"{_hwpunit_to_pt(margin.get('top', 140))}pt {_hwpunit_to_pt(margin.get('right', 140))}pt {_hwpunit_to_pt(margin.get('bottom', 140))}pt {_hwpunit_to_pt(margin.get('left', 140))}pt",
                "vertical-align": "middle",
                "width": f"{_hwpunit_to_mm(cell.get('width', 0))}mm" if int(cell.get("width", 0)) > 0 else "auto",
                "height": f"{_hwpunit_to_mm(cell.get('height', 0))}mm" if int(cell.get("height", 0)) > 0 else "auto",
            }
            cell_content = _render_blocks(cell.get("blocks", []), resources)
            cells.append(
                f"<td data-hwpx-cell-ref=\"{escape(str(cell.get('cell_ref', '')), quote=True)}\" "
                f"data-hwpx-cell-column=\"{int(cell.get('column', cell_index))}\" "
                f"data-hwpx-cell-row=\"{int(cell.get('row', 0))}\" "
                f"data-hwpx-cell-header=\"{'1' if cell.get('header') else '0'}\" "
                f"data-hwpx-border-fill-id=\"{int(cell.get('border_fill_id_ref', 0))}\" "
                f"colspan=\"{max(1, int(cell.get('column_span', 1)))}\" rowspan=\"{max(1, int(cell.get('row_span', 1)))}\" "
                f"style=\"{_style(cell_css)}\">{cell_content}</td>"
            )
        rows.append(f"<tr>{''.join(cells)}</tr>")
    caption = block.get("caption") if isinstance(block.get("caption"), dict) else None
    caption_html = ""
    if caption is not None:
        caption_attrs = {
            "data-hwpx-caption-side": str(caption.get("side", "TOP")),
            "data-hwpx-caption-full-size": "1" if caption.get("full_size") else "0",
            "data-hwpx-caption-width": str(caption.get("width", 0)),
            "data-hwpx-caption-gap": str(caption.get("gap", 0)),
            "data-hwpx-caption-last-width": str(caption.get("last_width", 0)),
        }
        caption_html = (
            f"<caption {_attrs(caption_attrs)} style=\"caption-side:top;text-align:left;\">"
            f"{_render_blocks(caption.get('blocks', []), resources)}</caption>"
        )
    return (
        f"<table data-hwpx-block-ref=\"{escape(str(block.get('block_ref', '')), quote=True)}\" "
        f"data-hwpx-anchor-block-ref=\"{escape(str(block.get('anchor_block_ref', '')), quote=True)}\" "
        f"data-hwpx-table-semantics=\"{_encoded_json(block.get('table_semantics', {}))}\" "
        f"data-hwpx-border-fill-id=\"{int(block.get('border_fill_id_ref', 0))}\" "
        f"data-hwpx-repeat-header=\"{'1' if block.get('repeat_header') else '0'}\" "
        f"style=\"{_style(table_css)}\">{caption_html}<tbody>{''.join(rows)}</tbody></table>"
    )


def _render_image(block: dict[str, Any], resources: dict[str, dict[str, Any]]) -> str:
    resource_ref = str(block.get("resource_ref", ""))
    resource = resources.get(resource_ref, {})
    media_type = str(resource.get("media_type", "application/octet-stream"))
    payload = str(resource.get("payload_base64", ""))
    src = f"data:{media_type};base64,{payload}" if payload and media_type.startswith("image/") else ""
    width = int(block.get("width", 0))
    height = int(block.get("height", 0))
    css = {
        "display": "block",
        "width": f"{_hwpunit_to_mm(width)}mm" if width > 0 else "auto",
        "height": f"{_hwpunit_to_mm(height)}mm" if height > 0 else "auto",
        "max-width": "100%",
        "object-fit": "contain",
        "margin": "0",
    }
    overlay_layers = [layer for layer in block.get("overlay_layers", []) if isinstance(layer, dict)]
    if overlay_layers:
        css.update({"position": "absolute", "inset": "0"})
    layer_html = "".join(_render_overlay_layer(layer, resources) for layer in overlay_layers)
    figure_css = {
        "margin": "0",
        "break-inside": "avoid",
        "position": "relative" if overlay_layers else "static",
        "width": f"{_hwpunit_to_mm(width)}mm" if overlay_layers and width > 0 else "auto",
        "height": f"{_hwpunit_to_mm(height)}mm" if overlay_layers and height > 0 else "auto",
    }
    return (
        f"<figure data-hwpx-block-ref=\"{escape(str(block.get('block_ref', '')), quote=True)}\" "
        f"data-hwpx-anchor-block-ref=\"{escape(str(block.get('anchor_block_ref', '')), quote=True)}\" "
        f"data-hwpx-source-item-id=\"{escape(str(block.get('source_item_id') or resource.get('source_item_id', '')), quote=True)}\" "
        f"data-hwpx-source-href=\"{escape(str(resource.get('source_href', '')), quote=True)}\" "
        f"data-hwpx-source-media-type=\"{escape(str(resource.get('source_media_type', '')), quote=True)}\" "
        f"data-hwpx-is-embedded=\"{'1' if resource.get('is_embedded', True) else '0'}\" "
        f"data-hwpx-object-semantics=\"{_encoded_json(block.get('object_semantics', []))}\" "
        f"data-hwpx-object-group-owner-ref=\"{escape(str(block.get('object_group_owner_ref', '')), quote=True)}\" "
        f"data-hwpx-resource-ref=\"{escape(resource_ref, quote=True)}\" style=\"{_style(figure_css)}\">"
        f"<img src=\"{src}\" alt=\"{escape(str(block.get('alt', 'Embedded document image')), quote=True)}\" "
        f"data-hwpx-intrinsic-width=\"{int(block.get('intrinsic_width', 0))}\" "
        f"data-hwpx-intrinsic-height=\"{int(block.get('intrinsic_height', 0))}\" "
        f"data-hwpx-crop-left=\"{int(block.get('crop', {}).get('left', 0))}\" "
        f"data-hwpx-crop-right=\"{int(block.get('crop', {}).get('right', 0))}\" "
        f"data-hwpx-crop-top=\"{int(block.get('crop', {}).get('top', 0))}\" "
        f"data-hwpx-crop-bottom=\"{int(block.get('crop', {}).get('bottom', 0))}\" "
        f"style=\"{_style(css)}\">{layer_html}</figure>"
    )


def _render_overlay_layer(layer: dict[str, Any], resources: dict[str, dict[str, Any]]) -> str:
    margin = layer.get("margin", {}) if isinstance(layer.get("margin"), dict) else {}
    vertical = str(layer.get("vertical_align", "TOP")).upper()
    css = {
        "position": "absolute",
        "left": f"{_hwpunit_to_mm(layer.get('left', 0))}mm",
        "top": f"{_hwpunit_to_mm(layer.get('top', 0))}mm",
        "width": f"{_hwpunit_to_mm(layer.get('width', 0))}mm",
        "height": f"{_hwpunit_to_mm(layer.get('height', 0))}mm",
        "padding": f"{_hwpunit_to_pt(margin.get('top', 0))}pt {_hwpunit_to_pt(margin.get('right', 0))}pt {_hwpunit_to_pt(margin.get('bottom', 0))}pt {_hwpunit_to_pt(margin.get('left', 0))}pt",
        "display": "flex",
        "flex-direction": "column",
        "justify-content": "center" if vertical == "CENTER" else "flex-end" if vertical == "BOTTOM" else "flex-start",
        "overflow": "visible",
        "z-index": "1",
    }
    attrs = {
        "data-hwpx-overlay-layer": str(layer.get("layer_ref", "")),
        "data-hwpx-left": str(layer.get("left", 0)),
        "data-hwpx-top": str(layer.get("top", 0)),
        "data-hwpx-width": str(layer.get("width", 0)),
        "data-hwpx-height": str(layer.get("height", 0)),
        "data-hwpx-vertical-align": vertical,
        "data-hwpx-margin-left": str(margin.get("left", 0)),
        "data-hwpx-margin-right": str(margin.get("right", 0)),
        "data-hwpx-margin-top": str(margin.get("top", 0)),
        "data-hwpx-margin-bottom": str(margin.get("bottom", 0)),
    }
    return f"<div {_attrs(attrs)} style=\"{_style(css)}\">{_render_blocks(layer.get('blocks', []), resources)}</div>"


def _preview_page_break_refs(blocks: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    previous_vertpos: int | None = None
    for block in blocks:
        if not isinstance(block, dict):
            continue
        segments = block.get("line_segments", [])
        if not isinstance(segments, list) or not segments or not isinstance(segments[0], dict):
            continue
        current_vertpos = int(segments[0].get("vertpos", 0))
        if previous_vertpos is not None and current_vertpos < previous_vertpos:
            block_ref = str(block.get("block_ref", ""))
            if block_ref and not block.get("page_break"):
                refs.add(block_ref)
        previous_vertpos = current_vertpos
    return refs


def _first_page(model: dict[str, Any]) -> dict[str, Any]:
    for section in model.get("sections", []):
        if isinstance(section, dict) and isinstance(section.get("page"), dict):
            return section["page"]
    return {}


def _referenced_resource_refs(model: dict[str, Any]) -> set[str]:
    refs: set[str] = set()

    def walk(blocks: Any) -> None:
        for block in blocks if isinstance(blocks, list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("kind") == "image":
                refs.add(str(block.get("resource_ref", "")))
                for layer in block.get("overlay_layers", []):
                    if isinstance(layer, dict):
                        walk(layer.get("blocks", []))
            elif block.get("kind") == "table":
                caption = block.get("caption")
                if isinstance(caption, dict):
                    walk(caption.get("blocks", []))
                for row in block.get("rows", []):
                    for cell in row if isinstance(row, list) else []:
                        if isinstance(cell, dict):
                            walk(cell.get("blocks", []))

    for section in model.get("sections", []):
        if isinstance(section, dict):
            walk(section.get("blocks", []))
    refs.discard("")
    return refs


def _line_height(value: dict[str, Any]) -> str:
    kind = str(value.get("type", "PERCENT")).upper()
    amount = int(value.get("value", 160))
    if kind == "PERCENT":
        return f"{max(10, amount)}%"
    return f"{_hwpunit_to_pt(amount)}pt"


def _text_align(value: Any) -> str:
    return {
        "LEFT": "left",
        "RIGHT": "right",
        "CENTER": "center",
        "JUSTIFY": "justify",
        "DISTRIBUTE": "justify",
    }.get(str(value or "LEFT").upper(), "left")


def _css_font_family(value: Any) -> str:
    candidate = str(value or "HancomBatang").replace("\\", "").replace("\"", "").replace("'", "").strip()
    normalized = candidate.replace(" ", "").lower()
    serif_tokens = ("명조", "바탕", "batang", "myeongjo", "myungjo", "serif")
    sans_tokens = ("고딕", "돋움", "dotum", "gothic", "sans")
    fallback = "HCR Batang" if any(token in normalized for token in serif_tokens) else "HCR Dotum" if any(token in normalized for token in sans_tokens) else "HCR Batang"
    return f"'{candidate or fallback}', '{fallback}', 'Malgun Gothic', serif"


def _safe_color(value: Any, fallback: str, *, allow_transparent: bool = False) -> str:
    candidate = str(value or "").strip()
    if allow_transparent and candidate.lower() in {"none", "transparent"}:
        return "transparent"
    if len(candidate) == 7 and candidate.startswith("#") and all(char in "0123456789abcdefABCDEF" for char in candidate[1:]):
        return candidate.upper()
    return fallback


def _hwpunit_to_pt(value: Any) -> float:
    try:
        return round(int(value) / 100, 3)
    except (TypeError, ValueError):
        return 0.0


def _hwpunit_to_mm(value: Any) -> float:
    try:
        return round(int(value) * 25.4 / 7200, 3)
    except (TypeError, ValueError):
        return 0.0


def _style(values: dict[str, Any]) -> str:
    return ";".join(f"{name}:{value}" for name, value in values.items() if value not in {None, ""}) + ";"


def _attrs(values: dict[str, str]) -> str:
    return " ".join(f"{name}=\"{escape(value, quote=True)}\"" for name, value in values.items())


def _encoded_json(value: Any) -> str:
    return urlsafe_b64encode(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
