from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import re
from html import escape
from pathlib import Path
from typing import Any, Iterable

from bs4 import BeautifulSoup, NavigableString, Tag


SCHEMA_VERSION = "report_export_ir.v1"
HWPX_CONTRACT_VERSION = "hwpx-authoring-html.v1"
PAGE_ATTRIBUTES = (
    'data-hwpx-page-width="59528" data-hwpx-page-height="84188" '
    'data-hwpx-margin-left="6236" data-hwpx-margin-right="6236" '
    'data-hwpx-margin-top="6519" data-hwpx-margin-bottom="6519" '
    'data-hwpx-margin-header="2835" data-hwpx-margin-footer="2835"'
)

SUPPORTED_STYLE_PROPERTIES = {
    "font-family", "font-size", "font-weight", "font-style", "color",
    "background-color", "text-decoration", "vertical-align", "margin",
    "line-height", "text-align", "break-before", "break-after", "padding",
    "width", "height", "border-spacing", "text-indent", "page-break-before",
    "page-break-after",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def chapter_paths(project: Path) -> list[Path]:
    return sorted((project / "reports" / "chapters").glob("ch*.html"))


def build_report_export_ir(project: Path, cover_data_path: Path) -> dict[str, Any]:
    cover = json.loads(read_text(cover_data_path))
    chapters = chapter_paths(project)
    if not chapters:
        raise ValueError("report chapter HTML files were not found")

    sections: list[dict[str, Any]] = [{
        "section_ref": "cover",
        "source": cover_data_path.relative_to(project).as_posix(),
        "blocks": _cover_blocks(cover),
    }]
    warnings: list[str] = []
    for chapter in chapters:
        soup = BeautifulSoup(read_text(chapter), "html.parser")
        root = soup.find("section", class_="report-chapter") or soup
        blocks, chapter_warnings = _parse_children(root.children, project, chapter)
        warnings.extend(f"{chapter.name}:{item}" for item in chapter_warnings)
        sections.append({
            "section_ref": str(root.get("data-chapter-id") or chapter.stem) if isinstance(root, Tag) else chapter.stem,
            "source": chapter.relative_to(project).as_posix(),
            "blocks": blocks,
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "project": project.name,
        "title": str(cover.get("report_title") or cover.get("title") or project.name),
        "source_format": "report-orchestra-chapter-html",
        "cover_source": cover_data_path.relative_to(project).as_posix(),
        "sections": sections,
        "warnings": sorted(set(warnings)),
        "security": {
            "external_resource_fetch": False,
            "active_content_allowed": False,
            "absolute_paths_serialized": False,
        },
    }


def summarize_report_export_ir(model: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    text_parts: list[str] = []
    for section in model.get("sections", []):
        for block in _walk_blocks(section.get("blocks", [])):
            kind = str(block.get("kind", "unknown"))
            counts[kind] = counts.get(kind, 0) + 1
            if block.get("text"):
                text_parts.append(str(block["text"]))
    normalized = " ".join(" ".join(text_parts).split())
    return {
        "schema_version": "report_export_ir_summary.v1",
        "section_count": len(model.get("sections", [])),
        "block_kind_counts": dict(sorted(counts.items())),
        "text_char_count": len(normalized),
        "normalized_text_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "warning_count": len(model.get("warnings", [])),
    }


def render_hwpx_authoring_html(model: dict[str, Any], project: Path) -> str:
    if model.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("report export IR schema version is invalid")
    sections = []
    for section_index, section in enumerate(model.get("sections", []), start=1):
        blocks = "\n".join(
            _render_block(block, project, section_index, block_index)
            for block_index, block in enumerate(section.get("blocks", []), start=1)
        )
        section_ref = _safe_ref(str(section.get("section_ref") or f"section-{section_index}"))
        sections.append(
            f'<section data-hwpx-section-ref="{escape(section_ref)}" {PAGE_ATTRIBUTES}>\n{blocks}\n</section>'
        )
    title = escape(str(model.get("title") or "Report Orchestra document"))
    return (
        "<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>"
        + title
        + "</title></head><body data-hwpx-contract=\""
        + HWPX_CONTRACT_VERSION
        + "\" data-hwpx-document-ref=\""
        + escape(_safe_ref(str(model.get("project") or "report")))
        + "\">\n"
        + "\n".join(sections)
        + "\n</body></html>\n"
    )


def _cover_blocks(cover: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    kicker = str(cover.get("kicker") or cover.get("report_type") or "")
    if kicker:
        blocks.append(_text_block("paragraph", kicker, "font-size:10pt;color:#616670;margin:0 0 12pt"))
    blocks.append(_text_block(
        "heading", str(cover.get("report_title") or cover.get("title") or "보고서"),
        "font-size:24pt;font-weight:800;color:#172033;margin:0 0 12pt;line-height:130%;break-after:avoid", level=1,
    ))
    subtitle = str(cover.get("subtitle") or "")
    if subtitle:
        blocks.append(_text_block("paragraph", subtitle, "font-size:13pt;color:#344054;margin:0 0 24pt;line-height:150%"))
    metadata = [
        ("문서 유형", cover.get("report_type")), ("문서 번호", cover.get("report_no")),
        ("작성일", cover.get("date")), ("버전", cover.get("version")),
        ("작성", cover.get("prepared_by")), ("대상", cover.get("prepared_for")),
        ("배포", cover.get("distribution")), ("분류", cover.get("classification")),
    ]
    rows = [
        [
            {"text": label, "header": True, "style": "width:28%;padding:5pt;background-color:#EDF3FA"},
            {"text": str(value), "header": False, "style": "width:72%;padding:5pt"},
        ]
        for label, value in metadata if value not in (None, "")
    ]
    if rows:
        blocks.append({"kind": "table", "style": "width:100%;border-spacing:0", "rows": rows})
    purpose = str(cover.get("purpose") or "")
    if purpose:
        blocks.append(_text_block("paragraph", purpose, "font-size:10.5pt;margin:18pt 0 0;line-height:165%"))
    return blocks


def _parse_children(
    children: Iterable[Any], project: Path, source_path: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    blocks: list[dict[str, Any]] = []
    warnings: list[str] = []
    for child in children:
        if isinstance(child, NavigableString) or not isinstance(child, Tag):
            continue
        tag = child.name.lower()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            blocks.append(_tag_text_block(child, "heading", int(tag[1])))
        elif tag == "p":
            blocks.append(_tag_text_block(child, "paragraph"))
        elif tag in {"ul", "ol"}:
            kind = "ordered" if tag == "ol" else "unordered"
            for item in child.find_all("li", recursive=False):
                block = _tag_text_block(item, "list_item")
                block["list_kind"] = kind
                block["list_level"] = 0
                blocks.append(block)
        elif tag == "table":
            blocks.append(_parse_table(child))
        elif tag == "figure":
            image = child.find("img")
            if image is not None:
                asset = _resolve_asset(project, source_path, str(image.get("src") or ""))
                if asset is None:
                    warnings.append(f"image_not_embedded:{image.get('src', '')}")
                else:
                    blocks.append({
                        "kind": "image", "asset_path": asset.relative_to(project).as_posix(),
                        "alt": str(image.get("alt") or "Embedded report image")[:500],
                        "style": _sanitize_style(str(image.get("style") or "width:100%")),
                    })
            caption = child.find("figcaption")
            if caption is not None and caption.get_text(" ", strip=True):
                blocks.append(_tag_text_block(caption, "paragraph", extra_style="font-size:9pt;color:#616670;margin:5pt 0 12pt"))
        elif tag in {"section", "article", "aside", "main", "div", "header", "footer"}:
            nested, nested_warnings = _parse_children(child.children, project, source_path)
            blocks.extend(nested)
            warnings.extend(nested_warnings)
        elif tag in {"style", "script", "noscript"}:
            continue
        else:
            text = child.get_text(" ", strip=True)
            if text:
                blocks.append(_text_block("paragraph", text, _sanitize_style(str(child.get("style") or ""))))
                warnings.append(f"flattened_element:{tag}")
    return blocks, warnings


def _parse_table(table: Tag) -> dict[str, Any]:
    rows = []
    for row in table.find_all("tr"):
        cells = []
        for cell in row.find_all(["th", "td"], recursive=False):
            cells.append({
                "text": cell.get_text(" ", strip=True),
                "header": cell.name.lower() == "th",
                "colspan": max(1, _int(cell.get("colspan"), 1)),
                "rowspan": max(1, _int(cell.get("rowspan"), 1)),
                "style": _sanitize_style(str(cell.get("style") or "padding:5pt")),
            })
        if cells:
            rows.append(cells)
    caption = table.find("caption")
    return {
        "kind": "table", "style": _sanitize_style(str(table.get("style") or "width:100%;border-spacing:0")),
        "caption": caption.get_text(" ", strip=True) if caption else "", "rows": rows,
    }


def _tag_text_block(tag: Tag, kind: str, level: int = 0, *, extra_style: str = "") -> dict[str, Any]:
    style = _sanitize_style(";".join(filter(None, [str(tag.get("style") or ""), extra_style])))
    block = _text_block(kind, tag.get_text(" ", strip=True), style, level=level)
    runs = []
    for child in tag.children:
        if isinstance(child, NavigableString) and str(child):
            runs.append({"text": str(child), "style": ""})
        elif isinstance(child, Tag):
            run_style = str(child.get("style") or "")
            if child.name.lower() in {"strong", "b"}:
                run_style += ";font-weight:700"
            if child.name.lower() in {"em", "i"}:
                run_style += ";font-style:italic"
            if child.name.lower() == "code":
                run_style += ";font-family:Consolas;font-size:9.5pt"
            runs.append({"text": child.get_text(" ", strip=False), "style": _sanitize_style(run_style)})
    if runs and "".join(item["text"] for item in runs).strip():
        block["runs"] = runs
    return block


def _text_block(kind: str, text: str, style: str, *, level: int = 0) -> dict[str, Any]:
    return {"kind": kind, "text": text, "style": style, "level": level}


def _render_block(block: dict[str, Any], project: Path, section_index: int, block_index: int) -> str:
    kind = str(block.get("kind") or "paragraph")
    block_ref = f"report-{section_index}-{block_index}-{kind}"
    if kind in {"paragraph", "heading", "list_item"}:
        if kind == "heading":
            tag = f"h{max(1, min(6, int(block.get('level') or 1)))}"
        else:
            tag = "p"
        style = str(block.get("style") or _default_style(kind, int(block.get("level") or 0)))
        content = _render_runs(block)
        attrs = f'data-hwpx-block-ref="{block_ref}" style="{escape(style, quote=True)}"'
        if kind == "list_item":
            list_tag = "ol" if block.get("list_kind") == "ordered" else "ul"
            return f'<{list_tag}><li {attrs} data-hwpx-list-level="{int(block.get("list_level") or 0)}">{content}</li></{list_tag}>'
        return f"<{tag} {attrs}>{content}</{tag}>"
    if kind == "table":
        caption = ""
        if block.get("caption"):
            caption = (
                f'<caption><p data-hwpx-block-ref="{block_ref}-caption" '
                f'style="font-size:9pt;font-weight:700;margin:0 0 5pt">'
                f'{escape(str(block["caption"]))}</p></caption>'
            )
        rows = []
        for row_index, row in enumerate(block.get("rows", []), start=1):
            cells = []
            for cell_index, cell in enumerate(row, start=1):
                tag = "th" if cell.get("header") else "td"
                attrs = [f'style="{escape(str(cell.get("style") or "padding:5pt"), quote=True)}"']
                if int(cell.get("colspan") or 1) > 1:
                    attrs.append(f'colspan="{int(cell["colspan"])}"')
                if int(cell.get("rowspan") or 1) > 1:
                    attrs.append(f'rowspan="{int(cell["rowspan"])}"')
                cell_ref = f"{block_ref}-r{row_index}-c{cell_index}"
                cells.append(
                    f'<{tag} {" ".join(attrs)} data-hwpx-cell-ref="{cell_ref}">'
                    f'<p data-hwpx-block-ref="{cell_ref}-paragraph">{escape(str(cell.get("text") or ""))}</p>'
                    f'</{tag}>'
                )
            rows.append("<tr>" + "".join(cells) + "</tr>")
        style = escape(str(block.get("style") or "width:100%;border-spacing:0"), quote=True)
        return f'<table data-hwpx-block-ref="{block_ref}" style="{style}">{caption}<tbody>{"".join(rows)}</tbody></table>'
    if kind == "image":
        asset = project / str(block["asset_path"])
        payload = base64.b64encode(asset.read_bytes()).decode("ascii")
        media_type = mimetypes.guess_type(asset.name)[0] or "image/png"
        style = str(block.get("style") or "width:100%;height:auto")
        alt = escape(str(block.get("alt") or "Embedded report image"), quote=True)
        return (
            f'<figure data-hwpx-block-ref="{block_ref}"><img src="data:{media_type};base64,{payload}" '
            f'alt="{alt}" style="{escape(style, quote=True)}"></figure>'
        )
    return f'<p data-hwpx-block-ref="{block_ref}">{escape(str(block.get("text") or ""))}</p>'


def _render_runs(block: dict[str, Any]) -> str:
    runs = block.get("runs")
    if not isinstance(runs, list) or not runs:
        return escape(str(block.get("text") or ""))
    return "".join(
        f'<span style="{escape(str(run.get("style") or ""), quote=True)}">{escape(str(run.get("text") or ""))}</span>'
        for run in runs
    )


def _default_style(kind: str, level: int) -> str:
    if kind == "heading":
        sizes = {1: "22pt", 2: "16pt", 3: "13pt"}
        return f"font-size:{sizes.get(level, '11pt')};font-weight:700;margin:16pt 0 7pt;line-height:135%;break-after:avoid"
    return "font-size:10.5pt;margin:5pt 0;line-height:165%"


def _sanitize_style(value: str) -> str:
    result = []
    for declaration in value.split(";"):
        if ":" not in declaration:
            continue
        name, item = declaration.split(":", 1)
        name = name.strip().lower()
        item = item.strip()
        if name in SUPPORTED_STYLE_PROPERTIES and item and not re.search(r"url\s*\(|@import", item, re.I):
            if name == "page-break-before":
                name = "break-before"
            elif name == "page-break-after":
                name = "break-after"
            result.append(f"{name}:{item}")
    return ";".join(result)


def _resolve_asset(project: Path, source_path: Path, value: str) -> Path | None:
    if not value or value.startswith(("http:", "https:", "data:", "file:")):
        return None
    candidates = [project / "reports" / value, source_path.parent / value, project / value]
    for candidate in candidates:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(project.resolve())
        except ValueError:
            continue
        if resolved.is_file():
            return resolved
    return None


def _walk_blocks(blocks: Iterable[dict[str, Any]]):
    for block in blocks:
        yield block


def _safe_ref(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip())
    return cleaned[:160] or "report"


def _int(value: Any, fallback: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return fallback
