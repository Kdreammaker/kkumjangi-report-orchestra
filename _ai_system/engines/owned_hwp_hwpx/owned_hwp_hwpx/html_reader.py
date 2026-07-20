"""Parse the controlled inline-first HWPX authoring HTML contract into IR."""

from __future__ import annotations

from base64 import b64decode, urlsafe_b64decode
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from typing import Any
from xml.etree import ElementTree

from .document_ir import AUTHORING_HTML_CONTRACT_VERSION, DOCUMENT_IR_SCHEMA_VERSION


MAX_HTML_BYTES = 256 * 1024 * 1024
MAX_EMBEDDED_RESOURCE_BYTES = 64 * 1024 * 1024
MAX_HTML_NODES = 250_000
MAX_HTML_NESTING_DEPTH = 256
ALLOWED_TAGS = {
    "html", "head", "meta", "title", "style", "body", "main", "section",
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "span", "ul", "ol", "li",
    "table", "caption", "thead", "tbody", "tfoot", "tr", "td", "th", "figure", "img", "div", "br",
}
REJECTED_TAGS = {"script", "link", "iframe", "object", "embed", "form", "input", "button"}


class OwnedAuthoringHtmlError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    children: list[Any] = field(default_factory=list)


class _ContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document", {})
        self.stack = [self.root]
        self.node_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in REJECTED_TAGS or tag not in ALLOWED_TAGS:
            raise OwnedAuthoringHtmlError(f"authoring_html_tag_forbidden:{tag}")
        self.node_count += 1
        if self.node_count > MAX_HTML_NODES:
            raise OwnedAuthoringHtmlError("authoring_html_node_limit_exceeded")
        if len(self.stack) >= MAX_HTML_NESTING_DEPTH:
            raise OwnedAuthoringHtmlError("authoring_html_nesting_limit_exceeded")
        values = {str(name).lower(): str(value or "") for name, value in attrs}
        if any(name.startswith("on") for name in values):
            raise OwnedAuthoringHtmlError("authoring_html_event_handler_forbidden")
        node = _Node(tag, values)
        self.stack[-1].children.append(node)
        if tag not in {"meta", "img", "br"}:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack[-1].tag == tag.lower() and tag.lower() not in {"meta", "img", "br"}:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"meta", "img", "br"}:
            return
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            raise OwnedAuthoringHtmlError("authoring_html_structure_invalid")
        self.stack.pop()

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)


def parse_authoring_html_document_ir(html: str) -> dict[str, Any]:
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        raise OwnedAuthoringHtmlError("authoring_html_size_limit_exceeded")
    parser = _ContractParser()
    try:
        parser.feed(html)
        parser.close()
    except RecursionError as exc:
        raise OwnedAuthoringHtmlError("authoring_html_nesting_limit_exceeded") from exc
    if len(parser.stack) != 1:
        raise OwnedAuthoringHtmlError("authoring_html_structure_invalid")
    _validate_css_resource_boundary(parser.root)

    body = _first_descendant(parser.root, "body")
    if body is None or body.attrs.get("data-hwpx-contract") != AUTHORING_HTML_CONTRACT_VERSION:
        raise OwnedAuthoringHtmlError("authoring_html_contract_required")
    state = _ParseState(
        _decode_style_catalog(body.attrs.get("data-hwpx-style-catalog", "")),
        _decode_preserved_resources(body.attrs.get("data-hwpx-preserved-resources", "")),
    )
    sections = [
        _parse_section(node, index, state)
        for index, node in enumerate(_descendants(body, "section"))
    ]
    if not sections:
        raise OwnedAuthoringHtmlError("authoring_html_section_required")
    upstream_loss = _decode_loss_report(body.attrs.get("data-hwpx-loss-report", ""))
    current_losses = dict(sorted(state.losses.items()))
    upstream_counts = upstream_loss.get("event_counts", {}) if isinstance(upstream_loss, dict) else {}
    combined = Counter({str(key): int(value) for key, value in upstream_counts.items()})
    combined.update(current_losses)
    return {
        "schema_version": DOCUMENT_IR_SCHEMA_VERSION,
        "source_format": "hwpx-authoring-html",
        "document_ref": _safe_ref(body.attrs.get("data-hwpx-document-ref", "owned_html_document")),
        "producer_family": "owned-authoring-html",
        "title": _node_text(_first_descendant(parser.root, "title")) or "HWPX authoring document",
        "styles": state.styles(),
        "sections": sections,
        "resources": state.resources,
        "loss_report": {
            "unsupported_feature_count": sum(combined.values()),
            "event_counts": dict(sorted(combined.items())),
            "silent_drop_allowed": False,
        },
        "security": {
            "external_resource_fetch": False,
            "local_absolute_paths_included": False,
            "active_content_allowed": False,
        },
    }


def _validate_css_resource_boundary(root: _Node) -> None:
    pending = [root]
    while pending:
        node = pending.pop()
        style = node.attrs.get("style", "")
        if re.search(r"(?:url\s*\(|@import\b)", style, flags=re.IGNORECASE):
            raise OwnedAuthoringHtmlError("authoring_html_css_resource_forbidden")
        if node.tag == "style" and re.search(
            r"(?:url\s*\(|@import\b)",
            _node_text(node),
            flags=re.IGNORECASE,
        ):
            raise OwnedAuthoringHtmlError("authoring_html_css_resource_forbidden")
        pending.extend(child for child in node.children if isinstance(child, _Node))


class _ParseState:
    def __init__(
        self,
        preserved_styles: dict[str, Any] | None = None,
        preserved_resources: list[dict[str, Any]] | None = None,
    ) -> None:
        self.preserved_styles = deepcopy(preserved_styles) if isinstance(preserved_styles, dict) else {}
        self.char_shapes: list[dict[str, Any]] = deepcopy(
            self.preserved_styles.get("char_shapes", [])
            if isinstance(self.preserved_styles.get("char_shapes"), list)
            else []
        )
        self.para_shapes: list[dict[str, Any]] = deepcopy(
            self.preserved_styles.get("para_shapes", [])
            if isinstance(self.preserved_styles.get("para_shapes"), list)
            else []
        )
        self._char_ids: dict[str, int] = {}
        self._para_ids: dict[str, int] = {}
        self.resources: list[dict[str, Any]] = deepcopy(preserved_resources or [])
        self._resource_refs: dict[str, str] = {
            str(resource.get("sha256", "")): str(resource.get("resource_ref", ""))
            for resource in self.resources
            if resource.get("sha256") and resource.get("resource_ref")
        }
        self.losses: Counter[str] = Counter()

    def char_shape_id(
        self,
        style: dict[str, str],
        preferred_id: int = -1,
    ) -> tuple[int, dict[str, Any], str]:
        if 0 <= preferred_id < len(self.char_shapes):
            return preferred_id, deepcopy(self.char_shapes[preferred_id]), _font_family(style.get("font-family", "HancomBatang"))
        shape, font = _character_style(style)
        key = json.dumps(shape, sort_keys=True, separators=(",", ":")) + "|" + font
        if key not in self._char_ids:
            self._char_ids[key] = len(self.char_shapes)
            if self.preserved_styles:
                shape.pop("_font_family", None)
                shape["font_ref"] = {
                    language: 0
                    for language in ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
                }
            self.char_shapes.append({"id": len(self.char_shapes), **shape})
        return self._char_ids[key], shape, font

    def para_shape_id(
        self,
        style: dict[str, str],
        *,
        list_kind: str | None,
        level: int,
        preferred_id: int = -1,
    ) -> tuple[int, dict[str, Any]]:
        if 0 <= preferred_id < len(self.para_shapes):
            return preferred_id, deepcopy(self.para_shapes[preferred_id])
        shape = _paragraph_style(style, list_kind=list_kind, level=level)
        key = json.dumps(shape, sort_keys=True, separators=(",", ":"))
        if key not in self._para_ids:
            self._para_ids[key] = len(self.para_shapes)
            self.para_shapes.append({"id": len(self.para_shapes), **shape})
        return self._para_ids[key], shape

    def add_resource(
        self,
        src: str,
        source_item_id: str = "",
        *,
        source_href: str = "",
        source_media_type: str = "",
        is_embedded: bool = True,
    ) -> str:
        match = re.fullmatch(r"data:([a-z0-9.+-]+/[a-z0-9.+-]+);base64,([A-Za-z0-9+/=_-]+)", src, re.IGNORECASE)
        if not match or not match.group(1).lower().startswith("image/"):
            raise OwnedAuthoringHtmlError("authoring_html_image_data_uri_required")
        try:
            payload = b64decode(match.group(2), validate=True)
        except ValueError as exc:
            raise OwnedAuthoringHtmlError("authoring_html_image_base64_invalid") from exc
        if len(payload) > MAX_EMBEDDED_RESOURCE_BYTES:
            raise OwnedAuthoringHtmlError("authoring_html_image_size_limit_exceeded")
        digest = sha256(payload).hexdigest()
        if digest in self._resource_refs:
            return self._resource_refs[digest]
        source_item_id = source_item_id if re.fullmatch(r"image[1-9][0-9]*", source_item_id) else ""
        used_item_ids = {
            str(resource.get("source_item_id", ""))
            for resource in self.resources
            if isinstance(resource, dict)
        }
        if source_item_id in used_item_ids:
            raise OwnedAuthoringHtmlError("authoring_html_image_item_id_conflict")
        if not source_item_id:
            next_id = 1
            while f"image{next_id}" in used_item_ids:
                next_id += 1
            source_item_id = f"image{next_id}"
        ref = f"resource:{digest[:24]}"
        self._resource_refs[digest] = ref
        preserved_media_type = _safe_preserved_media_type(source_media_type)
        if not preserved_media_type.startswith("image/"):
            preserved_media_type = match.group(1).lower()
        self.resources.append({
            "resource_ref": ref,
            "source_item_id": source_item_id,
            "source_href": _safe_preserved_resource_href(source_href),
            "source_media_type": preserved_media_type,
            "is_embedded": is_embedded,
            "media_type": match.group(1).lower(),
            "byte_count": len(payload),
            "sha256": digest,
            "payload_base64": match.group(2),
        })
        return ref

    def styles(self) -> dict[str, Any]:
        if self.preserved_styles:
            result = deepcopy(self.preserved_styles)
            result["char_shapes"] = self.char_shapes
            result["para_shapes"] = self.para_shapes
            return result
        fonts: list[dict[str, Any]] = []
        for shape in self.char_shapes:
            font = str(shape.get("_font_family", "HancomBatang"))
            if font not in [str(item.get("name")) for item in fonts]:
                fonts.append({"id": len(fonts), "name": font})
        font_names = [str(item.get("name", "HancomBatang")) for item in fonts]
        for shape in self.char_shapes:
            font = str(shape.pop("_font_family", "HancomBatang"))
            font_id = font_names.index(font) if font in font_names else 0
            shape["font_ref"] = {language: font_id for language in ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")}
        font_groups = [
            {
                "language": language,
                "fonts": [{"id": index, "face": name, "type": "TTF", "is_embedded": False} for index, name in enumerate(font_names)],
            }
            for language in ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
        ]
        return {
            "font_faces": font_groups,
            "font_lookup": {},
            "char_shapes": self.char_shapes,
            "para_shapes": self.para_shapes,
            "named_styles": [],
            "list_semantics": {},
            "border_fill_semantics": {},
        }


def _parse_section(node: _Node, section_index: int, state: _ParseState) -> dict[str, Any]:
    page = {
        "width": _int_value(node.attrs.get("data-hwpx-page-width"), 59528),
        "height": _int_value(node.attrs.get("data-hwpx-page-height"), 84188),
        "margin": {
            edge: _int_value(node.attrs.get(f"data-hwpx-margin-{edge}"), fallback)
            for edge, fallback in (
                ("left", 8504), ("right", 8504), ("top", 8504), ("bottom", 8504),
                ("header", 4252), ("footer", 4252), ("gutter", 0),
            )
        },
    }
    return {
        "section_ref": _safe_ref(node.attrs.get("data-hwpx-section-ref", f"section:{section_index + 1}")),
        "reading_order": section_index + 1,
        "page": page,
        "section_semantics": _decode_json_object(
            node.attrs.get("data-hwpx-section-semantics", ""),
            "authoring_html_section_semantics_invalid",
            max_encoded_bytes=2 * 1024 * 1024,
        ),
        "blocks": _parse_block_children(node.children, section_index, state),
    }


def _parse_block_children(children: list[Any], section_index: int, state: _ParseState) -> list[dict[str, Any]]:
    blocks = []
    for child in children:
        if not isinstance(child, _Node):
            if str(child).strip():
                state.losses["unwrapped_text"] += 1
            continue
        if child.tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6"}:
            blocks.append(_parse_paragraph_node(child, section_index, len(blocks), state))
        elif child.tag in {"ul", "ol"}:
            list_kind = "ordered" if child.tag == "ol" else "unordered"
            for item in (value for value in child.children if isinstance(value, _Node) and value.tag == "li"):
                blocks.append(_parse_paragraph_node(item, section_index, len(blocks), state, list_kind=list_kind))
        elif child.tag == "table":
            blocks.append(_parse_table_node(child, section_index, len(blocks), state))
        elif child.tag == "figure":
            image = _first_descendant(child, "img")
            if image is not None:
                blocks.append(_parse_image_node(child, image, section_index, len(blocks), state))
        elif child.tag == "div" and "data-hwpx-raw-drawing" in child.attrs:
            payload = _decode_json_object(
                child.attrs.get("data-hwpx-raw-drawing", ""),
                "authoring_html_raw_drawing_invalid",
                max_encoded_bytes=8 * 1024 * 1024,
            )
            raw_xml = str(payload.get("raw_xml", ""))
            try:
                drawing_root = ElementTree.fromstring(raw_xml)
            except ElementTree.ParseError as exc:
                raise OwnedAuthoringHtmlError("authoring_html_raw_drawing_invalid") from exc
            if drawing_root.tag.rsplit("}", 1)[-1] not in {
                "container", "rect", "ellipse", "line", "connectLine", "polygon", "curve", "arc"
            }:
                raise OwnedAuthoringHtmlError("authoring_html_raw_drawing_invalid")
            blocks.append({
                "block_ref": _safe_ref(child.attrs.get("data-hwpx-block-ref", f"block:{section_index + 1}:{len(blocks) + 1}:drawing")),
                "anchor_block_ref": _optional_ref(child.attrs.get("data-hwpx-anchor-block-ref", "")),
                "kind": "drawing",
                "raw_xml": raw_xml,
            })
        elif child.tag in {"thead", "tbody", "tfoot", "main"}:
            blocks.extend(_parse_block_children(child.children, section_index, state))
        elif child.tag == "style":
            continue
        else:
            state.losses[f"unsupported_authoring_element:{child.tag}"] += 1
    return blocks


def _parse_paragraph_node(
    node: _Node,
    section_index: int,
    block_index: int,
    state: _ParseState,
    *,
    list_kind: str | None = None,
) -> dict[str, Any]:
    style = _style_map(node.attrs.get("style", ""))
    level = _int_value(node.attrs.get("data-hwpx-list-level"), 0)
    para_id, para_shape = state.para_shape_id(
        style,
        list_kind=list_kind,
        level=level,
        preferred_id=_int_value(node.attrs.get("data-hwpx-para-pr-id"), -1),
    )
    runs = []
    if node.attrs.get("data-hwpx-empty-runs", "false").strip().lower() not in {"1", "true", "yes"}:
        for child in node.children:
            if isinstance(child, str):
                if child:
                    runs.append(_run_from_text(child, {}, state))
            elif child.tag == "span":
                runs.append(_run_from_text(
                    _node_text(child),
                    _style_map(child.attrs.get("style", "")),
                    state,
                    preferred_id=_int_value(child.attrs.get("data-hwpx-char-pr-id"), -1),
                    empty_text_count=max(
                        0,
                        min(8, _int_value(child.attrs.get("data-hwpx-empty-text-count"), 0)),
                    ),
                ))
            elif child.tag == "br":
                runs.append(_run_from_text("\n", {}, state))
            else:
                state.losses[f"unsupported_inline_element:{child.tag}"] += 1
    text = "".join(str(run.get("text", "")) for run in runs)
    kind = "list_item" if list_kind else "heading" if node.tag.startswith("h") else "paragraph"
    source_text_digest = node.attrs.get("data-hwpx-source-text-sha256", "").lower()
    line_segments = _decode_line_segments(node.attrs.get("data-hwpx-line-segments", ""))
    structural_controls = _decode_structural_controls(
        node.attrs.get("data-hwpx-structural-controls", "")
    )
    source_position_limit = len(text) + (8 * len(structural_controls))
    line_positions_fit_text = all(
        0 <= int(segment.get("textpos", 0)) <= source_position_limit
        for segment in line_segments
        if isinstance(segment, dict)
    )
    return {
        "block_ref": _safe_ref(node.attrs.get("data-hwpx-block-ref", f"block:{section_index + 1}:{block_index + 1}:paragraph")),
        "kind": kind,
        "paragraph_id": node.attrs.get("data-hwpx-paragraph-id", ""),
        "para_pr_id_ref": para_id,
        "style_id_ref": _int_value(node.attrs.get("data-hwpx-style-id"), 0),
        "text": text,
        "runs": runs,
        "paragraph_style": para_shape,
        "named_style": {},
        "list_kind": list_kind,
        "list_level": level,
        "page_break": style.get("break-before") == "page",
        "column_break": node.attrs.get("data-hwpx-column-break", "false").strip().lower() in {"1", "true", "yes"},
        "merged": node.attrs.get("data-hwpx-merged", "false").strip().lower() in {"1", "true", "yes"},
        "line_segments": line_segments,
        "preserve_line_segment_text_positions": (
            bool(re.fullmatch(r"[0-9a-f]{64}", source_text_digest))
            and source_text_digest == sha256(text.encode("utf-8")).hexdigest()
            and line_positions_fit_text
        ),
        "inline_controls": _decode_inline_controls(node.attrs.get("data-hwpx-inline-controls", "")),
        "structural_controls": structural_controls,
    }


def _run_from_text(
    text: str,
    style: dict[str, str],
    state: _ParseState,
    *,
    preferred_id: int = -1,
    empty_text_count: int = 0,
) -> dict[str, Any]:
    char_id, char_shape, font = state.char_shape_id(style, preferred_id)
    controls = []
    if "\t" in text:
        controls.extend({"kind": "tab"} for _ in range(text.count("\t")))
    if "\n" in text:
        controls.extend({"kind": "line_break"} for _ in range(text.count("\n")))
    return {
        "char_pr_id_ref": char_id,
        "text": text.replace("\u200b", ""),
        "controls": controls,
        "font_family": font,
        "character_style": char_shape,
        "empty_text_container_count": empty_text_count,
    }


def _parse_table_node(node: _Node, section_index: int, block_index: int, state: _ParseState) -> dict[str, Any]:
    caption_node = next(
        (value for value in node.children if isinstance(value, _Node) and value.tag == "caption"),
        None,
    )
    caption = None
    if caption_node is not None:
        caption = {
            "side": caption_node.attrs.get("data-hwpx-caption-side", "TOP"),
            "full_size": caption_node.attrs.get("data-hwpx-caption-full-size") == "1",
            "width": _int_value(caption_node.attrs.get("data-hwpx-caption-width"), 0),
            "gap": _int_value(caption_node.attrs.get("data-hwpx-caption-gap"), 0),
            "last_width": _int_value(caption_node.attrs.get("data-hwpx-caption-last-width"), 0),
            "blocks": _parse_block_children(caption_node.children, section_index, state),
        }
    row_nodes = _direct_table_rows(node)
    rows = []
    for row_index, row_node in enumerate(row_nodes):
        row = []
        cells = [value for value in row_node.children if isinstance(value, _Node) and value.tag in {"td", "th"}]
        for cell_index, cell in enumerate(cells):
            cell_style = _style_map(cell.attrs.get("style", ""))
            row.append({
                "cell_ref": _safe_ref(cell.attrs.get("data-hwpx-cell-ref", f"cell:{section_index + 1}:{block_index + 1}:{row_index + 1}:{cell_index + 1}")),
                "column": _int_value(cell.attrs.get("data-hwpx-cell-column"), cell_index),
                "row": _int_value(cell.attrs.get("data-hwpx-cell-row"), row_index),
                "column_span": max(1, _int_value(cell.attrs.get("colspan"), 1)),
                "row_span": max(1, _int_value(cell.attrs.get("rowspan"), 1)),
                "width": _css_length_hwpunit(cell_style.get("width")),
                "height": _css_length_hwpunit(cell_style.get("height")),
                "margin": _padding_edges(cell_style.get("padding", "0")),
                "border_fill_id_ref": _int_value(cell.attrs.get("data-hwpx-border-fill-id"), 0),
                "header": cell.attrs.get("data-hwpx-cell-header") == "1" or cell.tag == "th",
                "blocks": _parse_block_children(cell.children, section_index, state),
            })
        rows.append(row)
    style = _style_map(node.attrs.get("style", ""))
    return {
        "block_ref": _safe_ref(node.attrs.get("data-hwpx-block-ref", f"block:{section_index + 1}:{block_index + 1}:table")),
        "anchor_block_ref": _optional_ref(node.attrs.get("data-hwpx-anchor-block-ref", "")),
        "table_semantics": _decode_json_object(
            node.attrs.get("data-hwpx-table-semantics", ""),
            "authoring_html_table_semantics_invalid",
            max_encoded_bytes=2 * 1024 * 1024,
        ),
        "kind": "table",
        "row_count": len(rows),
        "column_count": max((sum(cell.get("column_span", 1) for cell in row) for row in rows), default=0),
        "rows": rows,
        "width": _css_length_hwpunit(style.get("width")),
        "height": _css_length_hwpunit(style.get("height")),
        "border_fill_id_ref": _int_value(node.attrs.get("data-hwpx-border-fill-id"), 0),
        "cell_spacing": _css_length_hwpunit(style.get("border-spacing")),
        "repeat_header": node.attrs.get("data-hwpx-repeat-header") == "1",
        "page_break_policy": "CELL",
        "treat_as_character": True,
        "caption": caption,
    }


def _direct_table_rows(node: _Node) -> list[_Node]:
    rows = [
        child for child in node.children
        if isinstance(child, _Node) and child.tag == "tr"
    ]
    for group in (
        child for child in node.children
        if isinstance(child, _Node) and child.tag in {"thead", "tbody", "tfoot"}
    ):
        rows.extend(
            child for child in group.children
            if isinstance(child, _Node) and child.tag == "tr"
        )
    return rows


def _parse_image_node(figure: _Node, image: _Node, section_index: int, block_index: int, state: _ParseState) -> dict[str, Any]:
    source_item_id = figure.attrs.get("data-hwpx-source-item-id", "")
    resource_ref = state.add_resource(
        image.attrs.get("src", ""),
        source_item_id,
        source_href=figure.attrs.get("data-hwpx-source-href", ""),
        source_media_type=figure.attrs.get("data-hwpx-source-media-type", ""),
        is_embedded=figure.attrs.get("data-hwpx-is-embedded", "1") != "0",
    )
    style = _style_map(image.attrs.get("style", ""))
    overlay_layers = []
    for layer in (
        child for child in figure.children
        if isinstance(child, _Node) and child.tag == "div" and "data-hwpx-overlay-layer" in child.attrs
    ):
        overlay_layers.append({
            "layer_ref": _safe_ref(layer.attrs.get("data-hwpx-overlay-layer", f"layer:{len(overlay_layers) + 1}")),
            "left": _int_value(layer.attrs.get("data-hwpx-left"), 0),
            "top": _int_value(layer.attrs.get("data-hwpx-top"), 0),
            "width": _int_value(layer.attrs.get("data-hwpx-width"), 0),
            "height": _int_value(layer.attrs.get("data-hwpx-height"), 0),
            "vertical_align": layer.attrs.get("data-hwpx-vertical-align", "TOP"),
            "margin": {
                edge: _int_value(layer.attrs.get(f"data-hwpx-margin-{edge}"), 0)
                for edge in ("left", "right", "top", "bottom")
            },
            "blocks": _parse_block_children(layer.children, section_index, state),
        })
    return {
        "block_ref": _safe_ref(figure.attrs.get("data-hwpx-block-ref", f"block:{section_index + 1}:{block_index + 1}:image")),
        "anchor_block_ref": _optional_ref(figure.attrs.get("data-hwpx-anchor-block-ref", "")),
        "object_semantics": _decode_json_list(
            figure.attrs.get("data-hwpx-object-semantics", ""),
            "authoring_html_object_semantics_invalid",
            max_encoded_bytes=4 * 1024 * 1024,
        ),
        "object_group_owner_ref": _optional_ref(
            figure.attrs.get("data-hwpx-object-group-owner-ref", "")
        ),
        "kind": "image",
        "resource_ref": resource_ref,
        "source_item_id": source_item_id,
        "width": _css_length_hwpunit(style.get("width")),
        "height": _css_length_hwpunit(style.get("height")),
        "intrinsic_width": _int_value(image.attrs.get("data-hwpx-intrinsic-width"), 0),
        "intrinsic_height": _int_value(image.attrs.get("data-hwpx-intrinsic-height"), 0),
        "crop": {
            edge: _int_value(image.attrs.get(f"data-hwpx-crop-{edge}"), 0)
            for edge in ("left", "right", "top", "bottom")
        },
        "overlay_layers": overlay_layers,
        "alt": image.attrs.get("alt", "Embedded document image")[:500],
    }


def _character_style(style: dict[str, str]) -> tuple[dict[str, Any], str]:
    font = _font_family(style.get("font-family", "HancomBatang"))
    decoration = style.get("text-decoration", "none").lower()
    shape = {
        "height": max(100, _css_length_hwpunit(style.get("font-size", "10pt"))),
        "text_color": _color(style.get("color"), "#000000"),
        "shade_color": _color(style.get("background-color"), "none", allow_none=True),
        "italic": style.get("font-style", "normal").lower() == "italic",
        "bold": style.get("font-weight", "400").lower() in {"bold", "600", "700", "800", "900"},
        "superscript": style.get("vertical-align", "baseline").lower() == "super",
        "subscript": style.get("vertical-align", "baseline").lower() == "sub",
        "underline": {"type": "BOTTOM" if "underline" in decoration else "NONE", "shape": "SOLID", "color": "#000000"},
        "strikeout": {"shape": "SOLID" if "line-through" in decoration else "NONE", "color": "#000000"},
        "_font_family": font,
    }
    return shape, font


def _paragraph_style(style: dict[str, str], *, list_kind: str | None, level: int) -> dict[str, Any]:
    margin = _margin_edges(style.get("margin", "0"))
    line_height = style.get("line-height", "160%")
    if line_height.endswith("%"):
        spacing = {"type": "PERCENT", "value": _float_int(line_height[:-1], 160), "unit": "HWPUNIT"}
    else:
        spacing = {"type": "FIXED", "value": _css_length_hwpunit(line_height), "unit": "HWPUNIT"}
    return {
        "align": {"horizontal": style.get("text-align", "left").upper(), "vertical": "BASELINE"},
        "heading": {"type": "NUMBER" if list_kind == "ordered" else "BULLET" if list_kind else "NONE", "id_ref": 1 if list_kind else 0, "level": level},
        "break_setting": {
            "break_latin_word": "KEEP_WORD", "break_non_latin_word": "KEEP_WORD",
            "widow_orphan": False, "keep_with_next": style.get("break-after") == "avoid",
            "keep_lines": False, "page_break_before": style.get("break-before") == "page", "line_wrap": "BREAK",
        },
        "margin": {
            "indent": _css_length_hwpunit(style.get("text-indent")),
            "left": margin[3], "right": margin[1], "prev": margin[0], "next": margin[2],
        },
        "line_spacing": spacing,
    }


def _style_map(value: str) -> dict[str, str]:
    result = {}
    for declaration in value.split(";"):
        if ":" not in declaration:
            continue
        name, item = declaration.split(":", 1)
        name = name.strip().lower()
        if name and re.fullmatch(r"[a-z-]+", name):
            result[name] = item.strip()
    return result


def _margin_edges(value: str) -> tuple[int, int, int, int]:
    parts = [_css_length_hwpunit(item) for item in value.split()[:4]] or [0]
    if len(parts) == 1:
        return parts[0], parts[0], parts[0], parts[0]
    if len(parts) == 2:
        return parts[0], parts[1], parts[0], parts[1]
    if len(parts) == 3:
        return parts[0], parts[1], parts[2], parts[1]
    return parts[0], parts[1], parts[2], parts[3]


def _padding_edges(value: str) -> dict[str, int]:
    top, right, bottom, left = _margin_edges(value)
    return {"top": top, "right": right, "bottom": bottom, "left": left}


def _css_length_hwpunit(value: str | None) -> int:
    candidate = str(value or "0").strip().lower()
    match = re.fullmatch(r"(-?\d+(?:\.\d+)?)(pt|mm|cm|in|px)?", candidate)
    if not match:
        return 0
    number = float(match.group(1))
    factor = {"pt": 100, "mm": 7200 / 25.4, "cm": 7200 / 2.54, "in": 7200, "px": 75}.get(match.group(2) or "pt", 100)
    return int(round(number * factor))


def _font_family(value: str) -> str:
    return value.split(",", 1)[0].strip().strip("'\"")[:160] or "HancomBatang"


def _color(value: str | None, fallback: str, *, allow_none: bool = False) -> str:
    candidate = str(value or "").strip()
    if allow_none and candidate.lower() in {"none", "transparent"}:
        return "none"
    return candidate.upper() if re.fullmatch(r"#[0-9a-fA-F]{6}", candidate) else fallback


def _decode_loss_report(value: str) -> dict[str, Any]:
    if not value:
        return {}
    try:
        decoded = urlsafe_b64decode(value.encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise OwnedAuthoringHtmlError("authoring_html_loss_report_invalid") from exc
    return payload if isinstance(payload, dict) else {}


def _decode_line_segments(value: str) -> list[dict[str, int]]:
    if not value:
        return []
    if len(value) > 512 * 1024:
        raise OwnedAuthoringHtmlError("authoring_html_line_segments_size_limit_exceeded")
    try:
        decoded = urlsafe_b64decode(value.encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise OwnedAuthoringHtmlError("authoring_html_line_segments_invalid") from exc
    if not isinstance(payload, list) or len(payload) > 4096:
        raise OwnedAuthoringHtmlError("authoring_html_line_segments_invalid")
    fields = (
        "textpos", "vertpos", "vertsize", "textheight", "baseline",
        "spacing", "horzpos", "horzsize", "flags",
    )
    segments = []
    for item in payload:
        if not isinstance(item, dict) or any(field not in item for field in fields):
            raise OwnedAuthoringHtmlError("authoring_html_line_segments_invalid")
        normalized = {}
        for field in fields:
            try:
                number = int(item[field])
            except (TypeError, ValueError) as exc:
                raise OwnedAuthoringHtmlError("authoring_html_line_segments_invalid") from exc
            lower_bound = 0 if field in {"textpos", "flags"} else -0x80000000
            if not lower_bound <= number <= 0xFFFFFFFF:
                raise OwnedAuthoringHtmlError("authoring_html_line_segments_invalid")
            normalized[field] = number
        segments.append(normalized)
    return segments


def _decode_inline_controls(value: str) -> list[dict[str, int]]:
    payload = _decode_json_list(
        value,
        "authoring_html_inline_controls_invalid",
        max_encoded_bytes=2 * 1024 * 1024,
    )
    controls = []
    for item in payload:
        if not isinstance(item, dict):
            raise OwnedAuthoringHtmlError("authoring_html_inline_controls_invalid")
        try:
            code = int(item.get("code", -1))
            visible_start = int(item.get("visible_start", 0))
            visible_end = int(item.get("visible_end", visible_start))
            source_start = int(item.get("source_start", visible_start))
        except (TypeError, ValueError) as exc:
            raise OwnedAuthoringHtmlError("authoring_html_inline_controls_invalid") from exc
        if code not in {9, 10, 24, 30, 31} or min(visible_start, visible_end, source_start) < 0:
            raise OwnedAuthoringHtmlError("authoring_html_inline_controls_invalid")
        control = {
            "code": code,
            "visible_start": visible_start,
            "visible_end": visible_end,
            "source_start": source_start,
        }
        if code == 9:
            control.update({
                "tab_width": max(0, int(item.get("tab_width", 0))),
                "tab_leader": max(0, int(item.get("tab_leader", 0))),
                "tab_type": max(0, int(item.get("tab_type", 0))),
            })
        controls.append(control)
    return controls


def _decode_structural_controls(value: str) -> list[dict[str, Any]]:
    payload = _decode_json_list(
        value,
        "authoring_html_structural_controls_invalid",
        max_encoded_bytes=2 * 1024 * 1024,
    )
    allowed = {
        "colPr": "dloc",
        "pageNum": "pngp",
        "pageHiding": "dhgp",
        "newNum": "onwn",
        "header": "daeh",
        "footer": "toof",
    }
    controls = []
    for item in payload:
        if not isinstance(item, dict):
            raise OwnedAuthoringHtmlError("authoring_html_structural_controls_invalid")
        child = str(item.get("render_layout_child", ""))
        if (
            not child
            and str(item.get("control_id", "")) == "object"
            and str(item.get("control_class", "")) == "extended"
        ):
            try:
                position = max(0, int(item.get("visible_start", 0)))
            except (TypeError, ValueError) as exc:
                raise OwnedAuthoringHtmlError("authoring_html_structural_controls_invalid") from exc
            controls.append({
                "control_id": "object",
                "control_class": "extended",
                "visible_start": position,
                "visible_end": position,
                "source_start": position,
                "source_run_index": max(0, int(item.get("source_run_index", 0))),
                "requires_text_tail": bool(item.get("requires_text_tail")),
            })
            continue
        if child not in allowed or str(item.get("control_id", "")) != allowed[child]:
            raise OwnedAuthoringHtmlError("authoring_html_structural_controls_invalid")
        try:
            position = max(0, int(item.get("visible_start", 0)))
        except (TypeError, ValueError) as exc:
            raise OwnedAuthoringHtmlError("authoring_html_structural_controls_invalid") from exc
        control = {
            "control_id": allowed[child],
            "render_layout_child": child,
            "visible_start": position,
            "visible_end": position,
            "source_start": position,
            "source_run_index": max(0, int(item.get("source_run_index", 0))),
        }
        if child in {"header", "footer"}:
            preserved_xml = str(item.get("preserved_xml", ""))
            if not preserved_xml or len(preserved_xml.encode("utf-8")) > 2 * 1024 * 1024:
                raise OwnedAuthoringHtmlError("authoring_html_structural_controls_invalid")
            try:
                preserved_root = ElementTree.fromstring(preserved_xml)
            except ElementTree.ParseError as exc:
                raise OwnedAuthoringHtmlError("authoring_html_structural_controls_invalid") from exc
            if preserved_root.tag.rsplit("}", 1)[-1] != child:
                raise OwnedAuthoringHtmlError("authoring_html_structural_controls_invalid")
            control["preserved_xml"] = preserved_xml
            controls.append(control)
            continue
        detail_key = {
            "colPr": "column_definition",
            "pageNum": "page_number",
            "pageHiding": "page_hiding",
            "newNum": "new_number",
        }[child]
        detail = item.get(detail_key)
        if isinstance(detail, dict):
            control[detail_key] = deepcopy(detail)
        controls.append(control)
    return controls


def _decode_style_catalog(value: str) -> dict[str, Any]:
    if not value:
        return {}
    if len(value) > 16 * 1024 * 1024:
        raise OwnedAuthoringHtmlError("authoring_html_style_catalog_size_limit_exceeded")
    try:
        decoded = urlsafe_b64decode(value.encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise OwnedAuthoringHtmlError("authoring_html_style_catalog_invalid") from exc
    if not isinstance(payload, dict):
        raise OwnedAuthoringHtmlError("authoring_html_style_catalog_invalid")
    for key in ("font_faces", "char_shapes", "para_shapes", "named_styles"):
        if key in payload and not isinstance(payload[key], list):
            raise OwnedAuthoringHtmlError("authoring_html_style_catalog_invalid")
    if (
        len(payload.get("font_faces", [])) > 16
        or len(payload.get("char_shapes", [])) > 16384
        or len(payload.get("para_shapes", [])) > 16384
    ):
        raise OwnedAuthoringHtmlError("authoring_html_style_catalog_invalid")
    return payload


def _decode_preserved_resources(value: str) -> list[dict[str, Any]]:
    if not value:
        return []
    if len(value) > 128 * 1024 * 1024:
        raise OwnedAuthoringHtmlError("authoring_html_preserved_resources_size_limit_exceeded")
    try:
        decoded = urlsafe_b64decode(value.encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise OwnedAuthoringHtmlError("authoring_html_preserved_resources_invalid") from exc
    if not isinstance(payload, list) or len(payload) > 4096:
        raise OwnedAuthoringHtmlError("authoring_html_preserved_resources_invalid")
    resources = []
    total_bytes = 0
    for resource in payload:
        if not isinstance(resource, dict):
            raise OwnedAuthoringHtmlError("authoring_html_preserved_resources_invalid")
        media_type = str(resource.get("media_type", ""))
        encoded = str(resource.get("payload_base64", ""))
        try:
            binary = b64decode(encoded, validate=True)
        except ValueError as exc:
            raise OwnedAuthoringHtmlError("authoring_html_preserved_resources_invalid") from exc
        total_bytes += len(binary)
        digest = sha256(binary).hexdigest()
        if (
            not (media_type.startswith("image/") or media_type == "application/octet-stream")
            or digest != str(resource.get("sha256", ""))
            or total_bytes > MAX_EMBEDDED_RESOURCE_BYTES
        ):
            raise OwnedAuthoringHtmlError("authoring_html_preserved_resources_invalid")
        resources.append({
            "resource_ref": f"resource:{digest[:24]}",
            "source_item_id": str(resource.get("source_item_id", ""))[:160],
            "source_href": _safe_preserved_resource_href(resource.get("source_href")),
            "source_media_type": _safe_preserved_media_type(resource.get("source_media_type")),
            "is_embedded": bool(resource.get("is_embedded", True)),
            "media_type": media_type,
            "byte_count": len(binary),
            "sha256": digest,
            "payload_base64": encoded,
        })
    return resources


def _safe_preserved_resource_href(value: Any) -> str:
    candidate = str(value or "")
    return candidate if re.fullmatch(r"BinData/[A-Za-z0-9_.-]{1,160}", candidate) else ""


def _safe_preserved_media_type(value: Any) -> str:
    candidate = str(value or "").lower()
    if re.fullmatch(r"(?:image/[a-z0-9.+-]+|application/(?:ole|octet-stream))", candidate):
        return candidate[:120]
    return "application/octet-stream"


def _decode_json_object(
    value: str,
    error_code: str,
    *,
    max_encoded_bytes: int,
) -> dict[str, Any]:
    if not value:
        return {}
    if len(value) > max_encoded_bytes:
        raise OwnedAuthoringHtmlError(error_code)
    try:
        payload = json.loads(urlsafe_b64decode(value.encode("ascii")).decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise OwnedAuthoringHtmlError(error_code) from exc
    if not isinstance(payload, dict):
        raise OwnedAuthoringHtmlError(error_code)
    return payload


def _decode_json_list(
    value: str,
    error_code: str,
    *,
    max_encoded_bytes: int,
) -> list[Any]:
    if not value:
        return []
    if len(value) > max_encoded_bytes:
        raise OwnedAuthoringHtmlError(error_code)
    try:
        payload = json.loads(urlsafe_b64decode(value.encode("ascii")).decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise OwnedAuthoringHtmlError(error_code) from exc
    if not isinstance(payload, list) or len(payload) > 16384:
        raise OwnedAuthoringHtmlError(error_code)
    return payload


def _descendants(node: _Node, tag: str):
    for child in node.children:
        if not isinstance(child, _Node):
            continue
        if child.tag == tag:
            yield child
        yield from _descendants(child, tag)


def _first_descendant(node: _Node, tag: str) -> _Node | None:
    return next(_descendants(node, tag), None)


def _node_text(node: _Node | None) -> str:
    if node is None:
        return ""
    return "".join(child if isinstance(child, str) else _node_text(child) for child in node.children)


def _safe_ref(value: str) -> str:
    candidate = str(value)[:200]
    return candidate if re.fullmatch(r"[A-Za-z0-9:._-]+", candidate) else f"ref:{sha256(candidate.encode('utf-8')).hexdigest()[:24]}"


def _optional_ref(value: str) -> str:
    return _safe_ref(value) if value else ""


def _int_value(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _float_int(value: Any, fallback: int) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return fallback
