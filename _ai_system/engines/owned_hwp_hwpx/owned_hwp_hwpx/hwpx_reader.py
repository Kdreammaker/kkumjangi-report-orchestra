"""Read HWPX packages into a reconstructable owned document IR."""

from __future__ import annotations

from base64 import b64encode
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path, PurePosixPath
import re
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile, ZipInfo

from .document_ir import DOCUMENT_IR_SCHEMA_VERSION
from .hwpx_profile import profile_hwpx_file
from .resource_limits import MAX_SOURCE_BYTES
from .style_semantics import parse_hwpx_style_root


MAX_PACKAGE_ENTRIES = 4096
MAX_PACKAGE_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
MAX_XML_ENTRY_BYTES = 32 * 1024 * 1024


class OwnedHwpxReadError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def read_hwpx_document_ir(path: Path, *, document_ref: str | None = None) -> dict[str, Any]:
    source = path.resolve()
    try:
        size = source.stat().st_size
    except FileNotFoundError as exc:
        raise OwnedHwpxReadError("hwpx_source_missing") from exc
    if source.suffix.lower() != ".hwpx":
        raise OwnedHwpxReadError("hwpx_source_required")
    if size > MAX_SOURCE_BYTES:
        raise OwnedHwpxReadError("hwpx_source_size_limit_exceeded")

    profile = profile_hwpx_file(source)
    if not str(profile.get("status", "")).startswith("profiled"):
        raise OwnedHwpxReadError("hwpx_profile_failed")

    try:
        with ZipFile(source, "r") as package:
            infos = package.infolist()
            _validate_package_infos(infos)
            names = {info.filename for info in infos}
            if "Contents/header.xml" not in names:
                raise OwnedHwpxReadError("hwpx_header_missing")
            loss_counts: Counter[str] = Counter()
            header_root = _parse_xml(package, "Contents/header.xml", loss_counts=loss_counts)
            styles = _style_catalog(profile, header_root)
            resources, binary_items = _read_resources(package)
            sections = []
            paragraph_catalogs = []
            for resource in resources:
                if not resource.get("browser_renderable", False):
                    loss_counts[f"browser_resource_unsupported:{resource.get('media_type', 'unknown')}"] += 1
            section_names = sorted(
                (name for name in names if _is_section_name(name)),
                key=_section_number,
            )
            for index, name in enumerate(section_names):
                root = _parse_xml(package, name, loss_counts=loss_counts)
                paragraph_elements = [
                    element for element in root.iter() if _local_name(element.tag) == "p"
                ]
                table_index_lookup = {
                    id(element): table_index
                    for table_index, element in enumerate(
                        element for element in root.iter() if _local_name(element.tag) == "tbl"
                    )
                }
                layout_lookup = _paragraph_line_segment_lookup(profile, index, paragraph_elements)
                paragraph_catalogs.append([
                    _parse_paragraph(
                        paragraph,
                        index,
                        paragraph_index,
                        styles,
                        line_segments=layout_lookup.get(id(paragraph), []),
                    )
                    for paragraph_index, paragraph in enumerate(paragraph_elements)
                ])
                section, section_losses = _parse_section(
                    root,
                    index,
                    styles,
                    binary_items,
                    layout_lookup,
                    table_index_lookup,
                )
                sections.append(section)
                loss_counts.update(section_losses)
    except BadZipFile as exc:
        raise OwnedHwpxReadError("hwpx_bad_zip") from exc

    ref = document_ref or f"owned_hwpx_doc_{sha256(source.read_bytes()).hexdigest()[:24]}"
    page_geometries = profile.get("section_page_geometries", [])
    for index, section in enumerate(sections):
        if index < len(page_geometries):
            section["page"] = page_geometries[index]
        elif page_geometries:
            section["page"] = page_geometries[-1]
        else:
            section["page"] = _default_page()
        if index < len(profile.get("section_semantics", [])):
            section["section_semantics"] = _public_semantics(profile["section_semantics"][index])
    _apply_profile_object_geometry(sections, profile, paragraph_catalogs)
    _apply_profile_table_semantics(sections, profile)

    return {
        "schema_version": DOCUMENT_IR_SCHEMA_VERSION,
        "source_format": "hwpx",
        "document_ref": ref,
        "producer_family": profile.get("producer_family", "unknown"),
        "title": ref,
        "styles": styles,
        "sections": sections,
        "resources": resources,
        "loss_report": {
            "unsupported_feature_count": sum(loss_counts.values()),
            "event_counts": dict(sorted(loss_counts.items())),
            "silent_drop_allowed": False,
        },
        "security": {
            "package_entry_limit": MAX_PACKAGE_ENTRIES,
            "package_uncompressed_byte_limit": MAX_PACKAGE_UNCOMPRESSED_BYTES,
            "xml_entry_byte_limit": MAX_XML_ENTRY_BYTES,
            "external_resource_fetch": False,
            "local_absolute_paths_included": False,
        },
    }


def _validate_package_infos(infos: list[ZipInfo]) -> None:
    if len(infos) > MAX_PACKAGE_ENTRIES:
        raise OwnedHwpxReadError("hwpx_entry_count_limit_exceeded")
    total = 0
    for info in infos:
        name = info.filename.replace("\\", "/")
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts:
            raise OwnedHwpxReadError("hwpx_unsafe_entry_path")
        total += max(0, int(info.file_size))
        if total > MAX_PACKAGE_UNCOMPRESSED_BYTES:
            raise OwnedHwpxReadError("hwpx_uncompressed_size_limit_exceeded")
        if name.endswith(".xml") and info.file_size > MAX_XML_ENTRY_BYTES:
            raise OwnedHwpxReadError("hwpx_xml_size_limit_exceeded")


def _paragraph_line_segment_lookup(
    profile: dict[str, Any],
    section_index: int,
    paragraph_elements: list[ElementTree.Element],
) -> dict[int, list[dict[str, int]]]:
    sections = profile.get("line_segment_semantics", [])
    if not isinstance(sections, list) or section_index >= len(sections):
        return {}
    section = sections[section_index]
    paragraphs = section.get("paragraphs", []) if isinstance(section, dict) else []
    by_index = {
        int(item.get("paragraph_index", index)): item.get("segments", [])
        for index, item in enumerate(paragraphs)
        if isinstance(item, dict)
    }
    return {
        id(element): [deepcopy(segment) for segment in by_index.get(index, []) if isinstance(segment, dict)]
        for index, element in enumerate(paragraph_elements)
    }


def _parse_xml(
    package: ZipFile,
    name: str,
    *,
    loss_counts: Counter[str] | None = None,
) -> ElementTree.Element:
    try:
        payload = package.read(name)
    except KeyError as exc:
        raise OwnedHwpxReadError("hwpx_required_xml_missing") from exc
    try:
        return ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        sanitized, replacement_count = _sanitize_invalid_xml_character_references(payload)
        if not replacement_count:
            raise OwnedHwpxReadError("hwpx_xml_parse_failed") from exc
        try:
            root = ElementTree.fromstring(sanitized)
        except ElementTree.ParseError as sanitized_exc:
            raise OwnedHwpxReadError("hwpx_xml_parse_failed") from sanitized_exc
        if loss_counts is not None:
            loss_counts["invalid_xml_character_reference_replaced"] += replacement_count
        return root


def _sanitize_invalid_xml_character_references(payload: bytes) -> tuple[bytes, int]:
    replacement_count = 0

    def replace(match: re.Match[bytes]) -> bytes:
        nonlocal replacement_count
        value = match.group(1)
        number = int(value[1:], 16) if value[:1].lower() == b"x" else int(value, 10)
        valid = (
            number in {0x09, 0x0A, 0x0D}
            or 0x20 <= number <= 0xD7FF
            or 0xE000 <= number <= 0xFFFD
            or 0x10000 <= number <= 0x10FFFF
        )
        if valid:
            return match.group(0)
        replacement_count += 1
        return b"&#xFFFD;"

    return re.sub(br"&#(x[0-9A-Fa-f]+|[0-9]+);", replace, payload), replacement_count


def _style_catalog(profile: dict[str, Any], header_root: ElementTree.Element) -> dict[str, Any]:
    semantics = profile.get("style_semantics", {})
    if not isinstance(semantics, dict) or not semantics.get("char_shapes") or not semantics.get("para_shapes"):
        semantics = parse_hwpx_style_root(header_root)
    font_faces = semantics.get("font_faces", []) if isinstance(semantics, dict) else []
    font_lookup: dict[str, dict[str, str]] = {}
    for group in font_faces if isinstance(font_faces, list) else []:
        language = str(group.get("language", "unknown"))
        for font in group.get("fonts", []) if isinstance(group, dict) else []:
            font_lookup.setdefault(str(font.get("id", "0")), {})[language] = _safe_font_name(font.get("face"))

    named_styles = []
    for element in header_root.iter():
        if _local_name(element.tag) != "style":
            continue
        named_styles.append({
            "id": _int_attr(element, "id"),
            "name": str(element.attrib.get("name", ""))[:160],
            "type": str(element.attrib.get("type", "PARA")),
            "para_pr_id_ref": _int_attr(element, "paraPrIDRef"),
            "char_pr_id_ref": _int_attr(element, "charPrIDRef"),
        })
    return {
        "font_lookup": font_lookup,
        "font_faces": deepcopy(font_faces) if isinstance(font_faces, list) else [],
        "char_shapes": semantics.get("char_shapes", []) if isinstance(semantics, dict) else [],
        "para_shapes": semantics.get("para_shapes", []) if isinstance(semantics, dict) else [],
        "named_styles": named_styles,
        "list_semantics": profile.get("list_semantics", {}),
        "border_fill_semantics": profile.get("border_fill_semantics", {}),
    }


def _read_resources(package: ZipFile) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    resources: list[dict[str, Any]] = []
    binary_items: dict[str, dict[str, Any]] = {}
    if "Contents/content.hpf" not in package.namelist():
        return resources, binary_items
    root = _parse_xml(package, "Contents/content.hpf")
    for element in root.iter():
        if _local_name(element.tag) != "item":
            continue
        item_id = str(element.attrib.get("id", ""))
        href = str(element.attrib.get("href", "")).replace("\\", "/")
        declared_media_type = str(element.attrib.get("media-type", "application/octet-stream"))
        if not item_id or not href.startswith("BinData/"):
            continue
        pure = PurePosixPath(href)
        if pure.is_absolute() or ".." in pure.parts or href not in package.namelist():
            raise OwnedHwpxReadError("hwpx_binary_reference_invalid")
        payload = package.read(href)
        media_type = _detect_media_type(payload, declared_media_type)
        digest = sha256(payload).hexdigest()
        resource = {
            "resource_ref": f"resource:{digest[:24]}",
            "source_item_id": item_id,
            "source_href": href,
            "source_media_type": declared_media_type,
            "is_embedded": str(element.attrib.get("isEmbeded", "1")) != "0",
            "media_type": _safe_media_type(media_type),
            "browser_renderable": media_type in {
                "image/png", "image/jpeg", "image/gif", "image/bmp", "image/webp", "image/svg+xml"
            },
            "byte_count": len(payload),
            "sha256": digest,
            "payload_base64": b64encode(payload).decode("ascii"),
        }
        resources.append(resource)
        binary_items[item_id] = resource
    return resources, binary_items


def _detect_media_type(payload: bytes, declared: str) -> str:
    normalized = _safe_media_type(declared)
    if normalized != "application/octet-stream":
        return normalized
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if payload.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if payload.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if payload.startswith(b"BM"):
        return "image/bmp"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "image/webp"
    if payload.lstrip().startswith((b"<svg", b"<?xml")) and b"<svg" in payload[:4096]:
        return "image/svg+xml"
    if payload.startswith(b"\xd7\xcd\xc6\x9a") or payload.startswith(b"\x01\x00\x09\x00"):
        return "image/wmf"
    if len(payload) >= 44 and payload[:4] == b"\x01\x00\x00\x00" and payload[40:44] == b" EMF":
        return "image/emf"
    return normalized


def _apply_profile_object_geometry(
    sections: list[dict[str, Any]],
    profile: dict[str, Any],
    paragraph_catalogs: list[list[dict[str, Any]]],
) -> None:
    semantic_sections = profile.get("object_semantics", [])
    for section_index, section in enumerate(sections):
        if section_index >= len(semantic_sections) or not isinstance(semantic_sections[section_index], dict):
            continue
        shapes = [shape for shape in semantic_sections[section_index].get("shapes", []) if isinstance(shape, dict)]
        pictures = [shape for shape in shapes if shape.get("kind") == "pic"]
        image_blocks = list(_walk_image_blocks(section.get("blocks", [])))
        group_owner_refs: dict[int, str] = {}
        for block, shape in zip(image_blocks, pictures):
            shape_index = int(shape.get("shape_index", 0))
            root_index = _root_shape_index(shapes, shape_index)
            owner_ref = group_owner_refs.get(root_index)
            is_group_owner = owner_ref is None
            if owner_ref is None:
                selected_indexes = [
                    candidate_index
                    for candidate_index in range(len(shapes))
                    if _root_shape_index(shapes, candidate_index) == root_index
                ]
                index_map = {source_index: local_index for local_index, source_index in enumerate(selected_indexes)}
                block["object_semantics"] = [
                    {
                        **_public_semantics(shapes[source_index]),
                        "parent_shape_index": index_map.get(
                            int(shapes[source_index].get("parent_shape_index", -1)),
                            -1,
                        ),
                    }
                    for source_index in selected_indexes
                ]
                group_owner_refs[root_index] = str(block.get("block_ref", ""))
            else:
                block["object_semantics"] = []
                block["object_group_owner_ref"] = owner_ref
            group_shape = shapes[root_index] if 0 <= root_index < len(shapes) else None
            common = shape.get("common") if isinstance(shape.get("common"), dict) else None
            if common is None and group_shape is not None:
                common = group_shape.get("common") if isinstance(group_shape.get("common"), dict) else None
                block["group_parent_kind"] = str(group_shape.get("kind", ""))
            if common is None:
                continue
            size = common.get("size", {}) if isinstance(common.get("size"), dict) else {}
            position = common.get("position", {}) if isinstance(common.get("position"), dict) else {}
            width = int(size.get("width", 0))
            height = int(size.get("height", 0))
            if width > 0 and height > 0:
                block["width"] = width
                block["height"] = height
            block["object_position"] = position
            block["object_z_order"] = int(common.get("z_order", 0))
            if is_group_owner and group_shape is not None and group_shape.get("kind") == "container":
                block["overlay_layers"] = _group_overlay_layers(
                    shapes,
                    root_index,
                    width,
                    height,
                    paragraph_catalogs[section_index] if section_index < len(paragraph_catalogs) else [],
                    section_index,
                )


def _root_shape_index(shapes: list[dict[str, Any]], shape_index: int) -> int:
    current = shape_index
    visited = set()
    while 0 <= current < len(shapes) and current not in visited:
        visited.add(current)
        parent = int(shapes[current].get("parent_shape_index", -1))
        if parent < 0 or parent >= len(shapes):
            return current
        current = parent
    return shape_index


def _walk_image_blocks(blocks: Any):
    for block in blocks if isinstance(blocks, list) else []:
        if not isinstance(block, dict):
            continue
        if block.get("kind") == "image":
            yield block
            for layer in block.get("overlay_layers", []):
                if isinstance(layer, dict):
                    yield from _walk_image_blocks(layer.get("blocks", []))
        elif block.get("kind") == "table":
            caption = block.get("caption")
            if isinstance(caption, dict):
                yield from _walk_image_blocks(caption.get("blocks", []))
            for row in block.get("rows", []):
                for cell in row if isinstance(row, list) else []:
                    if isinstance(cell, dict):
                        yield from _walk_image_blocks(cell.get("blocks", []))


def _apply_profile_table_semantics(
    sections: list[dict[str, Any]],
    profile: dict[str, Any],
) -> None:
    semantic_sections = profile.get("table_semantics", [])
    for section_index, section in enumerate(sections):
        if section_index >= len(semantic_sections) or not isinstance(semantic_sections[section_index], dict):
            continue
        semantics = [
            _public_semantics(value)
            for value in semantic_sections[section_index].get("tables", [])
            if isinstance(value, dict)
        ]
        for block in _walk_table_blocks(section.get("blocks", [])):
            source_index = int(block.get("source_table_index", -1))
            if 0 <= source_index < len(semantics):
                block["table_semantics"] = semantics[source_index]


def _walk_table_blocks(blocks: Any):
    for block in blocks if isinstance(blocks, list) else []:
        if not isinstance(block, dict):
            continue
        if block.get("kind") == "table":
            yield block
            caption = block.get("caption")
            if isinstance(caption, dict):
                yield from _walk_table_blocks(caption.get("blocks", []))
            for row in block.get("rows", []):
                for cell in row if isinstance(row, list) else []:
                    if isinstance(cell, dict):
                        yield from _walk_table_blocks(cell.get("blocks", []))
        elif block.get("kind") == "image":
            for layer in block.get("overlay_layers", []):
                if isinstance(layer, dict):
                    yield from _walk_table_blocks(layer.get("blocks", []))


def _public_semantics(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _public_semantics(item)
            for key, item in value.items()
            if not str(key).startswith("_")
        }
    if isinstance(value, list):
        return [_public_semantics(item) for item in value]
    return value


def _group_overlay_layers(
    shapes: list[dict[str, Any]],
    parent_index: int,
    group_width: int,
    group_height: int,
    paragraphs: list[dict[str, Any]],
    section_index: int,
) -> list[dict[str, Any]]:
    layers = []
    for shape_index, shape in enumerate(shapes):
        if shape_index == parent_index or _root_shape_index(shapes, shape_index) != parent_index:
            continue
        draw_text = shape.get("draw_text") if isinstance(shape.get("draw_text"), dict) else None
        if draw_text is None:
            continue
        indexes = [int(value) for value in draw_text.get("paragraph_indexes", [])]
        blocks = []
        for paragraph_offset, paragraph_index in enumerate(indexes):
            if not 0 <= paragraph_index < len(paragraphs):
                continue
            paragraph = deepcopy(paragraphs[paragraph_index])
            paragraph["block_ref"] = (
                f"block:{section_index + 1}:object:{parent_index + 1}:"
                f"layer:{len(layers) + 1}:paragraph:{paragraph_offset + 1}"
            )
            blocks.append(paragraph)
        if not blocks:
            continue
        box = _shape_render_box(shape, group_width, group_height, len(layers))
        layers.append({
            "layer_ref": f"object-layer:{section_index + 1}:{parent_index + 1}:{len(layers) + 1}",
            **box,
            "vertical_align": str(draw_text.get("sub_list", {}).get("vertical_align", "TOP")),
            "margin": draw_text.get("margin", {}),
            "blocks": blocks,
        })
    return layers


def _shape_render_box(shape: dict[str, Any], group_width: int, group_height: int, layer_index: int) -> dict[str, int]:
    element = shape.get("element", {}) if isinstance(shape.get("element"), dict) else {}
    original = element.get("original_size", {}) if isinstance(element.get("original_size"), dict) else {}
    width = max(1, int(original.get("width", 0)))
    height = max(1, int(original.get("height", 0)))
    x = 0.0
    y = 0.0
    scale_x = 1.0
    scale_y = 1.0
    for matrix in element.get("matrices", []):
        if not isinstance(matrix, dict):
            continue
        values = list(matrix.get("values", []))
        if len(values) < 6:
            continue
        a, b, c, d, e, f = (float(value) for value in values[:6])
        x, y = a * x + b * y + c, d * x + e * y + f
        if matrix.get("type") == "scaMatrix":
            scale_x *= abs(a)
            scale_y *= abs(e)
    rendered_width = max(1, int(round(width * scale_x)))
    rendered_height = max(1, int(round(height * scale_y)))
    left = max(0, min(int(round(x)), max(0, group_width - rendered_width)))
    top = int(round(y))
    if top < 0 or top + rendered_height > group_height:
        top = int(group_height * (0.015 if layer_index == 0 else 0.085 + 0.02 * (layer_index - 1)))
    return {
        "left": left,
        "top": max(0, top),
        "width": min(rendered_width, max(1, group_width - left)),
        "height": min(rendered_height, max(1, group_height - max(0, top))),
    }


def _parse_section(
    root: ElementTree.Element,
    section_index: int,
    styles: dict[str, Any],
    binary_items: dict[str, dict[str, Any]],
    line_segment_lookup: dict[int, list[dict[str, int]]],
    table_index_lookup: dict[int, int],
) -> tuple[dict[str, Any], Counter[str]]:
    blocks: list[dict[str, Any]] = []
    losses: Counter[str] = Counter()
    block_index = 0
    for child in list(root):
        local = _local_name(child.tag)
        if local == "p":
            parsed, parsed_losses = _parse_paragraph_container(
                child,
                section_index,
                block_index,
                styles,
                binary_items,
                line_segment_lookup,
                table_index_lookup,
            )
            blocks.extend(parsed)
            block_index += len(parsed)
            losses.update(parsed_losses)
        elif local == "tbl":
            blocks.append(_parse_table(
                child,
                section_index,
                block_index,
                styles,
                binary_items,
                line_segment_lookup,
                table_index_lookup,
            ))
            block_index += 1
        else:
            losses[f"unsupported_section_child:{local}"] += 1
    return ({
        "section_ref": f"section:{section_index + 1}",
        "reading_order": section_index + 1,
        "blocks": blocks,
    }, losses)


def _parse_paragraph_container(
    element: ElementTree.Element,
    section_index: int,
    block_index: int,
    styles: dict[str, Any],
    binary_items: dict[str, dict[str, Any]],
    line_segment_lookup: dict[int, list[dict[str, int]]],
    table_index_lookup: dict[int, int],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    losses: Counter[str] = Counter()
    paragraph = _parse_paragraph(
        element,
        section_index,
        block_index,
        styles,
        line_segments=line_segment_lookup.get(id(element), []),
    )
    blocks = [paragraph]
    object_offset = 1
    for descendant in _direct_paragraph_objects(element):
        local = _local_name(descendant.tag)
        if local == "tbl":
            blocks.append(_parse_table(
                descendant,
                section_index,
                block_index + object_offset,
                styles,
                binary_items,
                line_segment_lookup,
                table_index_lookup,
            ))
            object_offset += 1
        elif local == "pic":
            blocks.append(_parse_picture(descendant, section_index, block_index + object_offset, binary_items))
            object_offset += 1
        elif local in {"container", "rect", "ellipse", "line", "polygon", "curve", "arc"}:
            blocks.append({
                "block_ref": f"block:{section_index + 1}:{block_index + object_offset}:drawing",
                "kind": "drawing",
                "raw_xml": ElementTree.tostring(descendant, encoding="unicode"),
            })
            object_offset += 1
        elif local in {"equation", "ole"}:
            losses[f"unsupported_object:{local}"] += 1
    for block in blocks[1:]:
        block["anchor_block_ref"] = paragraph["block_ref"]
    return blocks, losses


def _direct_paragraph_objects(paragraph: ElementTree.Element):
    def walk(element: ElementTree.Element):
        for child in list(element):
            local = _local_name(child.tag)
            if local == "p":
                continue
            if local in {"tbl", "pic"}:
                yield child
                continue
            if local in {"equation", "ole", "container", "rect", "ellipse", "line", "polygon", "curve", "arc"}:
                if local == "rect" and any(
                    _local_name(descendant.tag) == "tbl" for descendant in child.iter()
                ):
                    yield child
                    continue
                pictures = [
                    descendant
                    for descendant in child.iter()
                    if _local_name(descendant.tag) == "pic"
                ]
                if pictures:
                    yield from pictures
                else:
                    yield child
                continue
            yield from walk(child)

    yield from walk(paragraph)


def _parse_paragraph(
    element: ElementTree.Element,
    section_index: int,
    block_index: int,
    styles: dict[str, Any],
    *,
    line_segments: list[dict[str, int]] | None = None,
) -> dict[str, Any]:
    para_pr_id = _int_attr(element, "paraPrIDRef")
    style_id = _int_attr(element, "styleIDRef")
    para_style = _catalog_item(styles.get("para_shapes"), para_pr_id)
    named_style = _catalog_item(styles.get("named_styles"), style_id)
    runs = []
    children = list(element)
    for child_index, child in enumerate(children):
        if _local_name(child.tag) != "run":
            continue
        run = _parse_run(child, styles)
        runs.append(run)
    text = "".join(str(run.get("text", "")) for run in runs)
    inline_controls = []
    structural_controls = []
    visible_offset = 0
    for run_index, run in enumerate(runs):
        for control in run.get("controls", []):
            if not isinstance(control, dict) or "code" not in control:
                continue
            item = deepcopy(control)
            item["visible_start"] = visible_offset + int(item.get("visible_start", 0))
            item["visible_end"] = visible_offset + int(item.get("visible_end", item["visible_start"]))
            item["source_start"] = item["visible_start"]
            inline_controls.append(item)
        for control in run.get("structural_controls", []):
            if not isinstance(control, dict):
                continue
            item = deepcopy(control)
            item["visible_start"] = visible_offset + int(item.get("visible_start", 0))
            item["visible_end"] = item["visible_start"]
            item["source_start"] = item["visible_start"]
            item["source_run_index"] = run_index
            structural_controls.append(item)
        visible_offset += len(str(run.get("text", "")))
    heading = para_style.get("heading", {}) if isinstance(para_style, dict) else {}
    heading_type = str(heading.get("type", "NONE")).upper()
    named_style_name = str(named_style.get("name", "")) if isinstance(named_style, dict) else ""
    kind = "paragraph"
    list_kind = None
    if heading_type in {"BULLET", "NUMBER"}:
        kind = "list_item"
        list_kind = "unordered" if heading_type == "BULLET" else "ordered"
    elif any(token in named_style_name.lower() for token in ("heading", "title", "제목")):
        kind = "heading"
    return {
        "block_ref": f"block:{section_index + 1}:{block_index + 1}:paragraph",
        "kind": kind,
        "paragraph_id": str(element.attrib.get("id", ""))[:80],
        "para_pr_id_ref": para_pr_id,
        "style_id_ref": style_id,
        "text": text,
        "runs": runs,
        "paragraph_style": para_style,
        "named_style": named_style,
        "list_kind": list_kind,
        "list_level": int(heading.get("level", 0)) if isinstance(heading, dict) else 0,
        "page_break": _bool_attr(element, "pageBreak"),
        "column_break": _bool_attr(element, "columnBreak"),
        "merged": _bool_attr(element, "merged"),
        "line_segments": [deepcopy(segment) for segment in line_segments or []],
        "inline_controls": inline_controls,
        "structural_controls": structural_controls,
    }


def _parse_run(element: ElementTree.Element, styles: dict[str, Any]) -> dict[str, Any]:
    char_pr_id = _int_attr(element, "charPrIDRef")
    char_style = _catalog_item(styles.get("char_shapes"), char_pr_id)
    text_parts: list[str] = []
    controls: list[dict[str, str]] = []
    structural_controls: list[dict[str, Any]] = []
    children = list(element)
    for child_index, child in enumerate(children):
        local = _local_name(child.tag)
        if local == "t":
            parsed_text, parsed_controls = _parse_text_container(child, len("".join(text_parts)))
            text_parts.append(parsed_text)
            controls.extend(parsed_controls)
        elif local == "ctrl":
            control = _parse_structural_control(child, len("".join(text_parts)))
            if control is not None:
                structural_controls.append(control)
        elif local in {
            "tbl", "pic", "container", "rect", "ellipse", "line",
            "polygon", "curve", "arc", "equation", "ole",
        }:
            structural_controls.append({
                "control_id": "object",
                "control_class": "extended",
                "visible_start": len("".join(text_parts)),
                "requires_text_tail": (
                    child_index + 1 < len(children)
                    and _local_name(children[child_index + 1].tag) == "t"
                    and not "".join(children[child_index + 1].itertext())
                ),
            })
        elif local == "tab":
            text_parts.append("\t")
            controls.append({"kind": "tab"})
        elif local == "lineBreak":
            text_parts.append("\n")
            controls.append({"kind": "line_break"})
        elif local == "hyphen":
            text_parts.append("-")
            controls.append({"kind": "hyphen"})
        elif local == "nbSpace":
            text_parts.append("\u00a0")
            controls.append({"kind": "nonbreaking_space"})
        elif local == "fwSpace":
            text_parts.append("\u3000")
            controls.append({"kind": "fixed_width_space"})
    font_ref = char_style.get("font_ref", {}) if isinstance(char_style, dict) else {}
    font_lookup = styles.get("font_lookup", {}) if isinstance(styles.get("font_lookup"), dict) else {}
    preferred_font_id = str(font_ref.get("hangul", font_ref.get("latin", 0))) if isinstance(font_ref, dict) else "0"
    font_family = _preferred_font(font_lookup.get(preferred_font_id, {}))
    return {
        "char_pr_id_ref": char_pr_id,
        "text": "".join(text_parts),
        "empty_text_container_count": sum(
            _local_name(child.tag) == "t"
            and not "".join(child.itertext())
            and not list(child)
            for child in children
        ),
        "controls": controls,
        "structural_controls": structural_controls,
        "font_family": font_family,
        "character_style": char_style,
    }


def _parse_text_container(
    element: ElementTree.Element,
    initial_position: int,
) -> tuple[str, list[dict[str, int]]]:
    parts = [element.text or ""]
    controls: list[dict[str, int]] = []
    position = initial_position + len(parts[0])
    control_values = {
        "tab": (9, ""),
        "lineBreak": (10, "\n"),
        "hyphen": (24, "-"),
        "nbSpace": (30, "\u00a0"),
        "fwSpace": (31, "\u3000"),
    }
    for child in list(element):
        local = _local_name(child.tag)
        if local in control_values:
            code, visible_text = control_values[local]
            item = {
                "code": code,
                "visible_start": position,
                "visible_end": position + len(visible_text),
            }
            if code == 9:
                item.update({
                    "tab_width": _int_attr(child, "width"),
                    "tab_leader": _int_attr(child, "leader"),
                    "tab_type": _int_attr(child, "type"),
                })
            controls.append(item)
            parts.append(visible_text)
            position += len(visible_text)
        else:
            nested_text, nested_controls = _parse_text_container(child, position)
            parts.append(nested_text)
            controls.extend(nested_controls)
            position += len(nested_text)
        tail = child.tail or ""
        parts.append(tail)
        position += len(tail)
    return "".join(parts), controls


def _parse_structural_control(
    element: ElementTree.Element,
    visible_position: int,
) -> dict[str, Any] | None:
    child = next(iter(element), None)
    if child is None:
        return None
    local = _local_name(child.tag)
    control_ids = {
        "colPr": "dloc",
        "pageNum": "pngp",
        "pageHiding": "dhgp",
        "newNum": "onwn",
        "header": "daeh",
        "footer": "toof",
    }
    if local not in control_ids:
        return None
    control: dict[str, Any] = {
        "control_id": control_ids[local],
        "render_layout_child": local,
        "visible_start": visible_position,
    }
    if local in {"header", "footer"}:
        control["preserved_xml"] = ElementTree.tostring(child, encoding="unicode")
        return control
    if local == "colPr":
        control["column_definition"] = {
            "id": str(child.attrib.get("id", "")),
            "type": str(child.attrib.get("type", "NEWSPAPER")),
            "layout": str(child.attrib.get("layout", "LEFT")),
            "column_count": _int_attr(child, "colCount", 1),
            "same_size": _bool_attr(child, "sameSz"),
            "same_gap": _int_attr(child, "sameGap"),
        }
    elif local == "pageNum":
        control["page_number"] = {
            "position": str(child.attrib.get("pos", "BOTTOM_CENTER")),
            "format_type": str(child.attrib.get("formatType", "DIGIT")),
            "side_character": str(child.attrib.get("sideChar", "-")),
        }
    elif local == "pageHiding":
        control["page_hiding"] = {
            "attributes": {name: _int_attr(child, name) for name in (
                "hideHeader", "hideFooter", "hideMasterPage",
                "hideBorder", "hideFill", "hidePageNum",
            )}
        }
    elif local == "newNum":
        control["new_number"] = {
            "number": _int_attr(child, "num", 1),
            "number_type": str(child.attrib.get("numType", "PAGE")),
        }
    return control


def _parse_table(
    element: ElementTree.Element,
    section_index: int,
    block_index: int,
    styles: dict[str, Any],
    binary_items: dict[str, dict[str, Any]],
    line_segment_lookup: dict[int, list[dict[str, int]]],
    table_index_lookup: dict[int, int],
) -> dict[str, Any]:
    caption = None
    caption_element = _first_child(element, "caption")
    if caption_element is not None:
        caption_blocks = []
        for sub_list in (child for child in list(caption_element) if _local_name(child.tag) == "subList"):
            for paragraph_index, paragraph in enumerate(
                child for child in list(sub_list) if _local_name(child.tag) == "p"
            ):
                parsed = _parse_paragraph(
                    paragraph,
                    section_index,
                    block_index,
                    styles,
                    line_segments=line_segment_lookup.get(id(paragraph), []),
                )
                parsed["block_ref"] = (
                    f"block:{section_index + 1}:{block_index + 1}:caption:paragraph:{paragraph_index + 1}"
                )
                caption_blocks.append(parsed)
        caption = {
            "side": str(caption_element.attrib.get("side", "TOP")),
            "full_size": _bool_attr(caption_element, "fullSz"),
            "width": _int_attr(caption_element, "width"),
            "gap": _int_attr(caption_element, "gap"),
            "last_width": _int_attr(caption_element, "lastWidth"),
            "blocks": caption_blocks,
        }
    rows = []
    for row_index, row_element in enumerate(child for child in list(element) if _local_name(child.tag) == "tr"):
        row = []
        for cell_index, cell in enumerate(child for child in list(row_element) if _local_name(child.tag) == "tc"):
            address = _first_child(cell, "cellAddr")
            span = _first_child(cell, "cellSpan")
            size = _first_child(cell, "cellSz")
            margin = _first_child(cell, "cellMargin")
            cell_blocks = []
            for sub_list in (child for child in list(cell) if _local_name(child.tag) == "subList"):
                for paragraph_index, paragraph in enumerate(
                    child for child in list(sub_list) if _local_name(child.tag) == "p"
                ):
                    parsed_blocks, _ = _parse_paragraph_container(
                        paragraph,
                        section_index,
                        block_index,
                        styles,
                        binary_items,
                        line_segment_lookup,
                        table_index_lookup,
                    )
                    paragraph_ref = (
                        f"block:{section_index + 1}:{block_index + 1}:"
                        f"cell:{row_index + 1}:{cell_index + 1}:paragraph:{paragraph_index + 1}"
                    )
                    parsed_blocks[0]["block_ref"] = paragraph_ref
                    for object_index, parsed in enumerate(parsed_blocks[1:], start=1):
                        parsed["block_ref"] = f"{paragraph_ref}:object:{object_index}:{parsed.get('kind', 'unknown')}"
                        parsed["anchor_block_ref"] = paragraph_ref
                        _rebase_nested_block_content(parsed, parsed["block_ref"])
                    cell_blocks.extend(parsed_blocks)
            row.append({
                "cell_ref": f"cell:{section_index + 1}:{block_index + 1}:{row_index + 1}:{cell_index + 1}",
                "column": _int_attr(address, "colAddr") if address is not None else cell_index,
                "row": _int_attr(address, "rowAddr") if address is not None else row_index,
                "column_span": max(1, _int_attr(span, "colSpan")) if span is not None else 1,
                "row_span": max(1, _int_attr(span, "rowSpan")) if span is not None else 1,
                "width": _int_attr(size, "width") if size is not None else 0,
                "height": _int_attr(size, "height") if size is not None else 0,
                "margin": _edge_attrs(margin),
                "border_fill_id_ref": _int_attr(cell, "borderFillIDRef"),
                "header": _bool_attr(cell, "header"),
                "blocks": cell_blocks,
            })
        rows.append(row)
    size = _first_child(element, "sz")
    position = _first_child(element, "pos")
    return {
        "block_ref": f"block:{section_index + 1}:{block_index + 1}:table",
        "kind": "table",
        "source_table_index": int(table_index_lookup.get(id(element), -1)),
        "row_count": _int_attr(element, "rowCnt") or len(rows),
        "column_count": _int_attr(element, "colCnt") or max((len(row) for row in rows), default=0),
        "rows": rows,
        "width": _int_attr(size, "width") if size is not None else 0,
        "height": _int_attr(size, "height") if size is not None else 0,
        "border_fill_id_ref": _int_attr(element, "borderFillIDRef"),
        "cell_spacing": _int_attr(element, "cellSpacing"),
        "repeat_header": _bool_attr(element, "repeatHeader"),
        "page_break_policy": str(element.attrib.get("pageBreak", "CELL")),
        "treat_as_character": _bool_attr(position, "treatAsChar") if position is not None else True,
        "caption": caption,
    }


def _rebase_nested_block_content(block: dict[str, Any], prefix: str) -> None:
    if block.get("kind") == "table":
        caption = block.get("caption")
        if isinstance(caption, dict):
            _rebase_block_list(caption.get("blocks", []), f"{prefix}:caption")
        for row_index, row in enumerate(block.get("rows", [])):
            for cell_index, cell in enumerate(row if isinstance(row, list) else []):
                if isinstance(cell, dict):
                    _rebase_block_list(
                        cell.get("blocks", []),
                        f"{prefix}:cell:{row_index + 1}:{cell_index + 1}",
                    )
    elif block.get("kind") == "image":
        for layer_index, layer in enumerate(block.get("overlay_layers", [])):
            if isinstance(layer, dict):
                _rebase_block_list(layer.get("blocks", []), f"{prefix}:layer:{layer_index + 1}")


def _rebase_block_list(blocks: Any, prefix: str) -> None:
    if not isinstance(blocks, list):
        return
    ref_map = {}
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        old_ref = str(block.get("block_ref", ""))
        new_ref = f"{prefix}:block:{index + 1}:{block.get('kind', 'unknown')}"
        block["block_ref"] = new_ref
        if old_ref:
            ref_map[old_ref] = new_ref
    for block in blocks:
        if not isinstance(block, dict):
            continue
        anchor_ref = str(block.get("anchor_block_ref", ""))
        if anchor_ref in ref_map:
            block["anchor_block_ref"] = ref_map[anchor_ref]
        _rebase_nested_block_content(block, str(block.get("block_ref", prefix)))


def _parse_picture(
    element: ElementTree.Element,
    section_index: int,
    block_index: int,
    binary_items: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    image = next((child for child in element.iter() if _local_name(child.tag) == "img"), None)
    item_id = str(image.attrib.get("binaryItemIDRef", "")) if image is not None else ""
    resource = binary_items.get(item_id, {})
    size = _first_child(element, "curSz")
    if size is None:
        size = _first_child(element, "orgSz")
    dimension = _first_child(element, "imgDim")
    crop = _first_child(element, "imgClip")
    return {
        "block_ref": f"block:{section_index + 1}:{block_index + 1}:image",
        "kind": "image",
        "resource_ref": resource.get("resource_ref"),
        "source_item_id": item_id,
        "width": _int_attr(size, "width") if size is not None else 0,
        "height": _int_attr(size, "height") if size is not None else 0,
        "intrinsic_width": _int_attr(dimension, "dimwidth") if dimension is not None else 0,
        "intrinsic_height": _int_attr(dimension, "dimheight") if dimension is not None else 0,
        "crop": {
            "left": _int_attr(crop, "left") if crop is not None else 0,
            "right": _int_attr(crop, "right") if crop is not None else 0,
            "top": _int_attr(crop, "top") if crop is not None else 0,
            "bottom": _int_attr(crop, "bottom") if crop is not None else 0,
        },
        "alt": "Embedded document image",
    }


def _catalog_item(value: Any, item_id: int) -> dict[str, Any]:
    if not isinstance(value, list):
        return {}
    for item in value:
        if isinstance(item, dict) and int(item.get("id", -1)) == item_id:
            return item
    return {}


def _preferred_font(value: Any) -> str:
    if not isinstance(value, dict):
        return "HancomBatang"
    for language in ("hangul", "latin", "hanja", "other"):
        candidate = _safe_font_name(value.get(language))
        if candidate != "HancomBatang":
            return candidate
    return "HancomBatang"


def _safe_font_name(value: Any) -> str:
    candidate = str(value or "").strip()
    if not candidate or "\ufffd" in candidate or any(ord(char) < 32 for char in candidate):
        return "HancomBatang"
    return candidate[:120]


def _safe_media_type(value: str) -> str:
    candidate = value.lower().replace("image/jpg", "image/jpeg")
    return candidate if candidate in {
        "image/png", "image/jpeg", "image/bmp", "image/gif", "image/webp", "image/svg+xml",
        "image/wmf", "image/emf",
    } else "application/octet-stream"


def _default_page() -> dict[str, Any]:
    return {
        "width": 59528,
        "height": 84188,
        "margin": {
            "left": 8504,
            "right": 8504,
            "top": 8504,
            "bottom": 8504,
            "header": 4252,
            "footer": 4252,
            "gutter": 0,
        },
    }


def _is_section_name(name: str) -> bool:
    return name.startswith("Contents/section") and name.endswith(".xml") and name[len("Contents/section"):-4].isdigit()


def _section_number(name: str) -> int:
    return int(name[len("Contents/section"):-4])


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _int_attr(element: ElementTree.Element | None, name: str, fallback: int = 0) -> int:
    if element is None:
        return fallback
    try:
        return int(str(element.attrib.get(name, fallback)), 0)
    except (TypeError, ValueError):
        return fallback


def _bool_attr(element: ElementTree.Element | None, name: str) -> bool:
    return _int_attr(element, name) == 1


def _first_child(element: ElementTree.Element, name: str) -> ElementTree.Element | None:
    return next((child for child in list(element) if _local_name(child.tag) == name), None)


def _edge_attrs(element: ElementTree.Element | None) -> dict[str, int]:
    return {name: _int_attr(element, name) for name in ("left", "right", "top", "bottom")}
