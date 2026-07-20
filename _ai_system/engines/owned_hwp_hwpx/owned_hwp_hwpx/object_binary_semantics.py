"""Typed binary payload and drawing-object semantics for owned HWP/HWPX conversion."""

from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
import re
import struct
from typing import Any, Iterable
from xml.etree import ElementTree
from zipfile import ZipFile
import zlib

from .border_fill_semantics import _colorref, _parse_hwp_fill, _parse_hwpx_fill
from .cfb import CompoundFile, CompoundFileError
from .resource_limits import ResourceLimitError, decompress_bounded


OBJECT_KIND_BY_ID = {
    b"noc$": "container",
    b"cip$": "pic",
    b"cer$": "rect",
    b"loc$": "line",
    b"elo$": "ole",
    b"lop$": "polygon",
    b"lle$": "ellipse",
}
SPECIFIC_TAG_BY_KIND = {
    "pic": "SHAPE_COMPONENT_PICTURE",
    "rect": "SHAPE_COMPONENT_RECTANGLE",
    "line": "SHAPE_COMPONENT_LINE",
    "ole": "SHAPE_COMPONENT_OLE",
    "polygon": "SHAPE_COMPONENT_POLYGON",
    "ellipse": "SHAPE_COMPONENT_ELLIPSE",
}
XML_OBJECT_TAGS = frozenset({"container", "pic", "rect", "line", "connectLine", "ole", "polygon", "ellipse"})
VERT_REL_TO = {0: "PAPER", 1: "PAGE", 2: "PARA"}
HORZ_REL_TO = {0: "PAPER", 1: "PAGE", 2: "COLUMN", 3: "PARA"}
VERT_ALIGN = {0: "TOP", 1: "CENTER", 2: "BOTTOM", 3: "INSIDE", 4: "OUTSIDE"}
HORZ_ALIGN = {0: "LEFT", 1: "CENTER", 2: "RIGHT", 3: "INSIDE", 4: "OUTSIDE"}
WIDTH_REL_TO = {0: "PAPER", 1: "PAGE", 2: "COLUMN", 3: "PARA", 4: "ABSOLUTE"}
HEIGHT_REL_TO = {0: "PAPER", 1: "PAGE", 2: "ABSOLUTE"}
TEXT_WRAPS = {
    0: "SQUARE",
    1: "TIGHT",
    2: "THROUGH",
    3: "TOP_AND_BOTTOM",
    4: "BEHIND_TEXT",
    5: "IN_FRONT_OF_TEXT",
}
TEXT_FLOWS = {0: "BOTH_SIDES", 1: "LEFT_ONLY", 2: "RIGHT_ONLY", 3: "LARGEST_ONLY"}
NUMBERING_TYPES = {0: "NONE", 1: "PICTURE", 2: "TABLE", 3: "EQUATION"}
LINE_STYLES = {
    0: "NONE",
    1: "SOLID",
    2: "DOT",
    3: "DASH",
    4: "DASH_DOT",
    5: "DASH_DOT_DOT",
    6: "LONG_DASH",
}
ARROW_STYLES = {
    0: "NORMAL",
    1: "ARROW",
    2: "SPEAR",
    3: "CONCAVE_ARROW",
    4: "EMPTY_DIAMOND",
    5: "EMPTY_CIRCLE",
    6: "EMPTY_BOX",
    7: "FILLED_DIAMOND",
    8: "FILLED_CIRCLE",
    9: "FILLED_BOX",
}
IMAGE_EFFECTS = {0: "REAL_PIC", 1: "GRAY_SCALE", 2: "BLACK_WHITE", 4: "PATTERN8X8"}
BIN_STREAM_ID = re.compile(r"(\d+)")


def parse_hwp_binary_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = []
    statuses: Counter[str] = Counter()
    for record_index, record in enumerate(records):
        if record.get("tag_name") != "BIN_DATA":
            continue
        value = _parse_hwp_binary_record(bytes(record.get("body", b"")), len(values))
        value["_record_index"] = record_index
        values.append(value)
        statuses[str(value.get("parse_status", "unknown"))] += 1
    return _binary_result(values, statuses)


def load_hwp_binary_payloads(path: Path) -> dict[str, Any]:
    try:
        cfb = CompoundFile.from_path(path)
        header = cfb.read_stream("FileHeader")
        compressed = len(header) >= 40 and bool(_u32(header, 36) & 1)
        doc_info = _decode_record_stream(cfb.read_stream("DocInfo"), compressed)
        records = _parse_record_stream(doc_info)
    except (OSError, KeyError, CompoundFileError, struct.error):
        return _binary_result([], Counter({"package_read_error": 1}), status="package_read_error")

    semantics = parse_hwp_binary_records(records)
    stream_by_id: dict[int, tuple[str, bytes]] = {}
    for stream_name in cfb.list_stream_paths():
        if not stream_name.startswith("BinData/"):
            continue
        storage_id = _hwp_stream_storage_id(stream_name)
        if storage_id is None:
            continue
        try:
            stream_by_id[storage_id] = (stream_name, cfb.read_stream(stream_name))
        except (KeyError, CompoundFileError):
            continue

    values = []
    statuses: Counter[str] = Counter()
    for metadata in semantics.get("items", []):
        value = dict(metadata)
        storage_id = _as_int(value.get("storage_id"))
        stream = stream_by_id.get(storage_id)
        if stream is None:
            value.update({"payload": b"", "payload_size": 0, "payload_sha256": "", "parse_status": "missing_stream"})
        else:
            stream_name, raw_payload = stream
            payload, payload_encoding = _decode_binary_payload(
                raw_payload,
                binary_type=_as_int(value.get("type_code")),
                compression_code=_as_int(value.get("compression_code")),
                document_compressed=compressed,
            )
            stream_extension = Path(stream_name).suffix.lstrip(".").lower()
            extension = str(value.get("format") or stream_extension or "bin").lower()
            kind = "ole" if _as_int(value.get("type_code")) == 2 else "image"
            item_id = f'{"ole" if kind == "ole" else "image"}{storage_id}'
            value.update(
                {
                    "kind": kind,
                    "format": extension,
                    "item_id": item_id,
                    "entry_name": f"BinData/{item_id}.{extension}",
                    "payload": payload,
                    "payload_encoding": payload_encoding,
                    "payload_size": len(payload),
                    "payload_sha256": hashlib.sha256(payload).hexdigest(),
                    "parse_status": "parsed",
                }
            )
        values.append(value)
        statuses[str(value.get("parse_status", "unknown"))] += 1
    return _binary_result(values, statuses)


def parse_hwpx_binary_package(package: ZipFile, *, include_payload: bool = False) -> dict[str, Any]:
    manifest_items = _content_manifest_items(package)
    values = []
    statuses: Counter[str] = Counter()
    for entry_name in sorted(name for name in package.namelist() if name.startswith("BinData/") and not name.endswith("/")):
        payload = package.read(entry_name)
        basename = entry_name.rsplit("/", 1)[-1]
        stem = Path(basename).stem
        extension = Path(basename).suffix.lstrip(".").lower() or "bin"
        manifest = manifest_items.get(entry_name, {})
        item_id = str(manifest.get("id") or stem)
        kind = "ole" if item_id.lower().startswith("ole") or extension == "ole" else "image"
        match = BIN_STREAM_ID.search(item_id)
        value = {
            "index": len(values),
            "storage_id": int(match.group(1)) if match is not None else len(values) + 1,
            "kind": kind,
            "format": extension,
            "item_id": item_id,
            "entry_name": entry_name,
            "media_type": str(manifest.get("media_type", "")),
            "payload_size": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "parse_status": "parsed",
        }
        if include_payload:
            value["payload"] = payload
        values.append(value)
        statuses["parsed"] += 1
    return _binary_result(values, statuses)


def public_binary_semantics(value: dict[str, Any]) -> dict[str, Any]:
    items = []
    for item in value.get("items", []):
        if not isinstance(item, dict):
            continue
        items.append({key: nested for key, nested in item.items() if key not in {"payload", "payload_sha256", "entry_name"}})
    return {**{key: nested for key, nested in value.items() if key != "items"}, "items": items}


def compare_binary_semantics(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    source_items = [item for item in source.get("items", []) if isinstance(item, dict)]
    target_items = [item for item in target.get("items", []) if isinstance(item, dict)]
    source_digests = Counter(str(item.get("payload_sha256", "")) for item in source_items if item.get("payload_sha256"))
    target_digests = Counter(str(item.get("payload_sha256", "")) for item in target_items if item.get("payload_sha256"))
    matched = sum((source_digests & target_digests).values())
    source_images = Counter(
        str(item.get("payload_sha256", ""))
        for item in source_items
        if item.get("kind") == "image" and item.get("payload_sha256")
    )
    target_images = Counter(
        str(item.get("payload_sha256", ""))
        for item in target_items
        if item.get("kind") == "image" and item.get("payload_sha256")
    )
    image_matched = sum((source_images & target_images).values())
    return {
        "status": "pass" if len(source_items) == len(target_items) and matched == len(source_items) else "fail",
        "source_count": len(source_items),
        "target_count": len(target_items),
        "payload_digest_match_count": matched,
        "image_payload_digest_match_count": image_matched,
        "source_image_count": sum(source_images.values()),
        "target_image_count": sum(target_images.values()),
        "format_counts_equal": Counter(str(item.get("format", "")) for item in source_items)
        == Counter(str(item.get("format", "")) for item in target_items),
    }


def parse_hwp_object_records(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    values = list(records)
    paragraph_by_record: dict[int, int] = {}
    paragraph_levels: dict[int, int] = {}
    paragraph_index = 0
    for record_index, record in enumerate(values):
        if record.get("tag_name") == "PARA_HEADER":
            paragraph_by_record[record_index] = paragraph_index
            paragraph_levels[paragraph_index] = int(record.get("level", 0))
            paragraph_index += 1

    root_by_shape_record: dict[int, dict[str, Any]] = {}
    for control_index, record in enumerate(values):
        if record.get("tag_name") != "CTRL_HEADER" or bytes(record.get("body", b""))[:4] != b" osg":
            continue
        control_level = int(record.get("level", 0))
        shape_record = _next_shape_record(values, control_index, control_level + 1)
        if shape_record < 0:
            continue
        root_by_shape_record[shape_record] = {
            "common": _parse_hwp_common_object(bytes(record.get("body", b""))),
            "anchor_paragraph_index": _nearest_paragraph(values, paragraph_by_record, control_index, control_level - 1),
            "order_key": control_index,
            "_control_record_index": control_index,
        }

    shapes: list[dict[str, Any]] = []
    stack: list[tuple[int, int]] = []
    for record_index, record in enumerate(values):
        if record.get("tag_name") != "SHAPE_COMPONENT":
            continue
        body = bytes(record.get("body", b""))
        kind = OBJECT_KIND_BY_ID.get(body[:4])
        if kind is None:
            continue
        level = int(record.get("level", 0))
        while stack and stack[-1][0] >= level:
            stack.pop()
        root = root_by_shape_record.get(record_index)
        parent_shape_index = -1
        if root is None:
            parent_shape_index = next(
                (shape_index for _parent_level, shape_index in reversed(stack) if shapes[shape_index].get("kind") == "container"),
                -1,
            )
        scope_end = _shape_scope_end(values, record_index, level)
        specific = _specific_record(values, record_index, scope_end, level, kind)
        draw_text = _parse_hwp_draw_text(values, paragraph_by_record, record_index, scope_end, level)
        specific_value = _parse_hwp_specific(kind, bytes(specific.get("body", b"")) if specific else b"")
        element_value = _parse_hwp_shape_element(body, kind)
        if kind == "pic" and isinstance(specific_value, dict):
            element_value["instance_id"] = _as_int(specific_value.get("instance_id"))
        shape = {
            "shape_index": len(shapes),
            "kind": kind,
            "record_level": level,
            "parent_shape_index": parent_shape_index,
            "anchor_paragraph_index": int(root.get("anchor_paragraph_index", -1)) if root else -1,
            "order_key": int(root.get("order_key", record_index)) if root else record_index,
            "common": root.get("common") if root else None,
            "element": element_value,
            "draw_text": draw_text,
            "specific": specific_value,
            "parse_status": "parsed" if specific is not None or kind == "container" else "missing_specific_record",
            "source_only": {"record_size": len(body), "record_index": record_index},
        }
        if kind in {"rect", "line", "polygon", "ellipse"}:
            shape.update(_parse_hwp_drawing_style(body))
        shapes.append(shape)
        stack.append((level, len(shapes) - 1))

    statuses = Counter(str(shape.get("parse_status", "unknown")) for shape in shapes)
    return _object_result(shapes, paragraph_index, paragraph_levels, statuses)


def parse_hwpx_object_root(root: ElementTree.Element) -> dict[str, Any]:
    shapes: list[dict[str, Any]] = []
    paragraph_levels: dict[int, int] = {}
    state = {"paragraph": -1}

    def visit(
        element: ElementTree.Element,
        *,
        current_paragraph: int = -1,
        group_parent: int = -1,
        paragraph_level: int = 0,
        draw_text_owner: int = -1,
    ) -> None:
        name = _local_name(element.tag)
        if name == "p":
            state["paragraph"] += 1
            current_paragraph = state["paragraph"]
            paragraph_levels[current_paragraph] = paragraph_level
            if draw_text_owner >= 0:
                draw_text = shapes[draw_text_owner].get("draw_text")
                if isinstance(draw_text, dict):
                    draw_text["paragraph_indexes"].append(current_paragraph)

        if name in XML_OBJECT_TAGS:
            kind = "line" if name == "connectLine" else name
            children = {_local_name(child.tag): child for child in list(element)}
            has_common = "sz" in children and "pos" in children
            shape_index = len(shapes)
            shape = {
                "shape_index": shape_index,
                "kind": kind,
                "record_level": paragraph_level + 1,
                "parent_shape_index": group_parent if not has_common else -1,
                "anchor_paragraph_index": current_paragraph if has_common else -1,
                "order_key": shape_index,
                "common": _parse_hwpx_common_object(element, children) if has_common else None,
                "element": _parse_hwpx_shape_element(element, children),
                "draw_text": _parse_hwpx_draw_text(children.get("drawText")),
                "specific": _parse_hwpx_specific(kind, element, children),
                "parse_status": "parsed",
                "source_only": {},
            }
            if kind in {"rect", "line", "polygon", "ellipse"}:
                shape.update(
                    {
                        "line_shape": _parse_hwpx_line_shape(children.get("lineShape")),
                        "fill": _parse_hwpx_fill(children.get("fillBrush")),
                    }
                )
            shapes.append(shape)
            next_group_parent = shape_index if kind == "container" else group_parent
            for child in list(element):
                child_name = _local_name(child.tag)
                if child_name == "drawText":
                    visit(
                        child,
                        current_paragraph=current_paragraph,
                        group_parent=group_parent,
                        paragraph_level=paragraph_level + 2,
                        draw_text_owner=shape_index,
                    )
                else:
                    visit(
                        child,
                        current_paragraph=current_paragraph,
                        group_parent=next_group_parent,
                        paragraph_level=paragraph_level,
                        draw_text_owner=-1,
                    )
            return

        for child in list(element):
            child_name = _local_name(child.tag)
            direct_draw_text_owner = (
                draw_text_owner
                if (name == "drawText" and child_name == "subList")
                or (name == "subList" and child_name == "p")
                else -1
            )
            visit(
                child,
                current_paragraph=current_paragraph,
                group_parent=group_parent,
                paragraph_level=paragraph_level,
                draw_text_owner=direct_draw_text_owner,
            )

    visit(root)
    return _object_result(shapes, state["paragraph"] + 1, paragraph_levels, Counter({"parsed": len(shapes)}))


def compare_object_semantics(
    source: dict[str, Any],
    target: dict[str, Any],
    *,
    strict_paragraph_indexes: bool = False,
) -> dict[str, Any]:
    source_values = _canonical_shapes(source.get("shapes", []), strict_paragraph_indexes)
    target_values = _canonical_shapes(target.get("shapes", []), strict_paragraph_indexes)
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    _compare_leaves(source_values, target_values, "shapes", exact, total)
    return {
        "status": "pass" if source_values == target_values else "fail",
        "source_count": len(source_values),
        "target_count": len(target_values),
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def compare_ordered_object_semantics(
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    source_shapes = [value for value in source.get("shapes", []) if isinstance(value, dict)]
    target_shapes = [value for value in target.get("shapes", []) if isinstance(value, dict)]
    source_values = _canonical_shapes_ordered(source_shapes)
    target_values = _canonical_shapes_ordered(target_shapes)
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    _compare_leaves(source_values, target_values, "shapes", exact, total)
    source_roots = [value for value in source_shapes if isinstance(value.get("common"), dict)]
    target_roots = [value for value in target_shapes if isinstance(value.get("common"), dict)]
    root_kind_exact = sum(
        source_value.get("kind") == target_value.get("kind")
        for source_value, target_value in zip(source_roots, target_roots)
    )
    root_anchor_exact = sum(
        _as_int(source_value.get("anchor_paragraph_index"), -1)
        == _as_int(target_value.get("anchor_paragraph_index"), -1)
        for source_value, target_value in zip(source_roots, target_roots)
    )
    ordered_kind_exact = sum(
        source_value.get("kind") == target_value.get("kind")
        for source_value, target_value in zip(source_shapes, target_shapes)
    )
    parent_index_exact = sum(
        _as_int(source_value.get("parent_shape_index"), -1)
        == _as_int(target_value.get("parent_shape_index"), -1)
        for source_value, target_value in zip(source_shapes, target_shapes)
    )
    return {
        "status": "pass" if source_values == target_values else "diverged",
        "source_count": len(source_values),
        "target_count": len(target_values),
        "ordered_kind_exact_count": ordered_kind_exact,
        "parent_index_exact_count": parent_index_exact,
        "source_root_count": len(source_roots),
        "target_root_count": len(target_roots),
        "root_kind_exact_count": root_kind_exact,
        "root_anchor_exact_count": root_anchor_exact,
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def _parse_hwp_binary_record(body: bytes, index: int) -> dict[str, Any]:
    if len(body) < 4:
        return {"index": index, "parse_status": "short_body", "source_only": {"record_size": len(body)}}
    attributes = _u16(body, 0)
    type_code = attributes & 0xF
    cursor = 2
    value: dict[str, Any] = {
        "index": index,
        "type_code": type_code,
        "type": {0: "LINK", 1: "EMBEDDING", 2: "STORAGE"}.get(type_code, "UNKNOWN"),
        "compression_code": (attributes >> 4) & 0x3,
        "access_state": (attributes >> 8) & 0x3,
        "format": "",
    }
    try:
        if type_code == 0:
            absolute_length = _u16(body, cursor)
            cursor += 2 + absolute_length * 2
            relative_length = _u16(body, cursor)
            cursor += 2 + relative_length * 2
            value["link_path_char_counts"] = {"absolute": absolute_length, "relative": relative_length}
        elif type_code in {1, 2}:
            value["storage_id"] = _u16(body, cursor)
            cursor += 2
            if type_code == 1:
                extension_length = _u16(body, cursor)
                cursor += 2
                value["format"] = body[cursor : cursor + extension_length * 2].decode("utf-16le", errors="replace").lower()
                cursor += extension_length * 2
        value["parse_status"] = "parsed" if cursor == len(body) else "size_mismatch"
    except (struct.error, UnicodeDecodeError):
        value["parse_status"] = "truncated"
    value["source_only"] = {
        "record_size": len(body),
        "consumed_size": cursor,
        "raw_attributes": attributes,
        "unmapped_attribute_bits": attributes & ~0x033F,
    }
    return value


def _parse_hwp_common_object(body: bytes) -> dict[str, Any]:
    if len(body) < 46:
        return _default_common_object("short_body")
    attributes = _u32(body, 4)
    treat_as_char = bool(attributes & 1)
    wrap_code = (attributes >> 21) & 0x7
    return {
        "id": _u32(body, 36),
        "z_order": _i32(body, 24),
        "numbering_type": NUMBERING_TYPES.get((attributes >> 26) & 0x7, "NONE"),
        "text_wrap": "TOP_AND_BOTTOM" if treat_as_char and wrap_code == 0 else TEXT_WRAPS.get(wrap_code, "TOP_AND_BOTTOM"),
        "text_flow": TEXT_FLOWS.get((attributes >> 24) & 0x3, "BOTH_SIDES"),
        "lock": False,
        "dropcap_style": "None",
        "href": "",
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
        "parse_status": "parsed",
        "source_only": {"raw_attributes": attributes, "record_size": len(body)},
    }


def _parse_hwp_shape_element(body: bytes, kind: str) -> dict[str, Any]:
    offset = 8 if len(body) >= 8 and body[:4] == body[4:8] else 4
    if len(body) < offset + 92:
        return _default_shape_element("short_body")
    attributes = _u32(body, offset + 28)
    matrix_count = _u16(body, offset + 42)
    cursor = offset + 44
    matrices = []
    if cursor + 48 <= len(body):
        matrices.append({"type": "transMatrix", "values": list(struct.unpack_from("<6d", body, cursor))})
        cursor += 48
    for _index in range(matrix_count):
        for matrix_type in ("scaMatrix", "rotMatrix"):
            if cursor + 48 > len(body):
                break
            matrices.append({"type": matrix_type, "values": list(struct.unpack_from("<6d", body, cursor))})
            cursor += 48
    instance_id = 0
    if kind == "container" and len(body) >= 4:
        instance_id = _u32(body, len(body) - 4)
    elif kind in {"rect", "line", "polygon", "ellipse"} and len(body) >= 6:
        instance_id = _u32(body, len(body) - 6)
    return {
        "group_level": _u16(body, offset + 8),
        "local_version": _u16(body, offset + 10),
        "offset": {"x": _i32(body, offset), "y": _i32(body, offset + 4)},
        "original_size": {"width": _u32(body, offset + 12), "height": _u32(body, offset + 16)},
        "current_size": {"width": _u32(body, offset + 20), "height": _u32(body, offset + 24)},
        "flip": {"horizontal": bool(attributes & 1), "vertical": bool(attributes & 2)},
        "rotation": {
            "angle": _u16(body, offset + 32),
            "center_x": _i32(body, offset + 34),
            "center_y": _i32(body, offset + 38),
            "rotate_image": bool(attributes & 0x80000),
        },
        "matrices": matrices,
        "instance_id": instance_id,
        "parse_status": "parsed" if len(matrices) == 1 + matrix_count * 2 else "truncated_matrices",
        "source_only": {"raw_attributes": attributes, "id_byte_count": offset},
    }


def _parse_hwp_drawing_style(body: bytes) -> dict[str, Any]:
    offset = 8 if len(body) >= 8 and body[:4] == body[4:8] else 4
    if len(body) < offset + 92:
        return {"line_shape": _default_line_shape(), "fill": {"type": "none"}}
    matrix_count = _u16(body, offset + 42)
    cursor = offset + 92 + matrix_count * 96
    if cursor + 11 > len(body):
        return {"line_shape": _default_line_shape(), "fill": {"type": "none"}}
    style_byte = body[cursor + 8]
    head_byte = body[cursor + 9]
    tail_byte = body[cursor + 10]
    head_code = (head_byte >> 2) & 0x3F
    tail_code = tail_byte & 0x3F
    fill, _fill_end, _fill_status = _parse_hwp_fill(body, cursor + 13)
    if fill.get("type") == "unsupported":
        fill = {"type": "none"}
    return {
        "line_shape": {
            "color": _colorref(body, cursor),
            "width": _i16(body, cursor + 4),
            "style": LINE_STYLES.get(style_byte & 0x3F, "NONE"),
            "end_cap": "FLAT" if ((style_byte >> 6) & 0x3) == 1 else "ROUND",
            "head_style": ARROW_STYLES.get(head_code, "NORMAL"),
            "tail_style": ARROW_STYLES.get(tail_code, "NORMAL"),
            "head_fill": True,
            "tail_fill": True,
            "head_size": "SMALL_SMALL" if head_code else "MEDIUM_MEDIUM",
            "tail_size": "SMALL_SMALL" if tail_code else "MEDIUM_MEDIUM",
            "outline_style": "NORMAL",
            "alpha": 0,
        },
        "fill": fill,
    }


def _parse_hwp_specific(kind: str, body: bytes) -> dict[str, Any]:
    if kind == "pic":
        if len(body) < 78:
            return {"parse_status": "short_body"}
        points = [_point(_i32(body, 12 + index * 8), _i32(body, 16 + index * 8)) for index in range(4)]
        crop = {
            "left": _i32(body, 44),
            "top": _i32(body, 48),
            "right": _i32(body, 52),
            "bottom": _i32(body, 56),
        }
        return {
            "points": points,
            "crop": crop,
            "dimension": _parse_hwp_picture_dimension(body, crop),
            "in_margin": _margin(*struct.unpack_from("<HHHH", body, 60)),
            "brightness": _i8(body, 68),
            "contrast": _i8(body, 69),
            "effect": IMAGE_EFFECTS.get(body[70], "REAL_PIC"),
            "binary_storage_id": _u16(body, 71),
            "border_alpha": body[73],
            "instance_id": _u32(body, 74),
            "effects": _parse_hwp_picture_effects(body),
            "effect_payload_size": max(0, len(body) - 78),
            "parse_status": "parsed",
        }
    if kind == "rect":
        if len(body) < 33:
            return {"parse_status": "short_body"}
        return {
            "ratio": body[0],
            "points": [_point(_i32(body, 1 + index * 8), _i32(body, 5 + index * 8)) for index in range(4)],
            "parse_status": "parsed",
        }
    if kind == "line":
        if len(body) < 18:
            return {"parse_status": "short_body"}
        return {
            "start": _point(_i32(body, 0), _i32(body, 4)),
            "end": _point(_i32(body, 8), _i32(body, 12)),
            "reverse": bool(_u16(body, 16)),
            "parse_status": "parsed",
        }
    if kind == "polygon":
        if len(body) < 4:
            return {"parse_status": "short_body"}
        count = _u32(body, 0)
        points = [
            _point(_i32(body, 4 + index * 8), _i32(body, 8 + index * 8))
            for index in range(count)
            if 12 + index * 8 <= len(body)
        ]
        return {"points": points, "parse_status": "parsed" if len(points) == count else "truncated_points"}
    if kind == "ellipse":
        if len(body) < 60:
            return {"parse_status": "short_body"}
        names = ("center", "axis1", "axis2", "start1", "end1", "start2", "end2")
        return {
            "interval_dirty": bool(_u32(body, 0) & 1),
            "has_arc_property": bool(_u32(body, 0) & 2),
            "arc_type": {0: "NORMAL", 1: "PIE", 2: "CHORD"}.get((_u32(body, 0) >> 2) & 0x3, "NORMAL"),
            "points": {name: _point(_i32(body, 4 + index * 8), _i32(body, 8 + index * 8)) for index, name in enumerate(names)},
            "parse_status": "parsed",
        }
    if kind == "ole":
        if len(body) < 14:
            return {"parse_status": "short_body"}
        return {
            "attributes": _u32(body, 0),
            "extent": _point(_i32(body, 4), _i32(body, 8)),
            "binary_storage_id": _u16(body, 12),
            "parse_status": "parsed",
        }
    return {"parse_status": "not_applicable"}


def _parse_hwp_picture_dimension(
    body: bytes,
    crop: dict[str, int],
) -> dict[str, int]:
    candidates: list[tuple[int, int]] = []
    for trailing_bytes in (0, 1):
        offset = len(body) - 8 - trailing_bytes
        if offset < 82:
            continue
        width = _u32(body, offset)
        height = _u32(body, offset + 4)
        if 0 < width <= 100_000_000 and 0 < height <= 100_000_000:
            candidates.append((width, height))
    crop_right = max(0, _i32_value(crop.get("right")))
    crop_bottom = max(0, _i32_value(crop.get("bottom")))
    for width, height in candidates:
        if width >= crop_right and height >= crop_bottom:
            return {"width": width, "height": height}
    if candidates:
        width, height = candidates[0]
        return {"width": width, "height": height}
    return {
        "width": max(0, crop_right - _i32_value(crop.get("left"))),
        "height": max(0, crop_bottom - _i32_value(crop.get("top"))),
    }


def _parse_hwp_picture_effects(body: bytes) -> dict[str, Any]:
    if len(body) < 82:
        return {"flags": 0, "unsupported_flags": 0}
    flags = _u32(body, 78)
    effects: dict[str, Any] = {
        "flags": flags,
        "unsupported_flags": flags & ~0x1,
    }
    if not flags & 0x1 or len(body) < 138:
        return effects

    color_type = _i32(body, 126)
    color: dict[str, Any] = {
        "type": "RGB" if color_type == 0 else f"TYPE_{color_type}",
        "scheme_index": -1,
        "system_index": -1,
        "preset_index": -1,
    }
    if color_type == 0:
        rgb = _u32(body, 130)
        color.update(
            {
                "r": (rgb >> 16) & 0xFF,
                "g": (rgb >> 8) & 0xFF,
                "b": rgb & 0xFF,
            }
        )
    effects["shadow"] = {
        "style": {0: "OUTSIDE"}.get(_i32(body, 82), "OUTSIDE"),
        "alpha": _f32(body, 86),
        "radius": _f32(body, 90),
        "direction": _f32(body, 94),
        "distance": _f32(body, 98),
        "align_style": {
            0: "TOP_LEFT",
            1: "TOP",
            2: "TOP_RIGHT",
            3: "LEFT",
            4: "CENTER",
            5: "RIGHT",
            6: "BOTTOM_LEFT",
            7: "BOTTOM",
            8: "BOTTOM_RIGHT",
        }.get(_i32(body, 102), "CENTER"),
        "skew": {"x": _f32(body, 106), "y": _f32(body, 110)},
        "scale": {"x": _f32(body, 114), "y": _f32(body, 118)},
        "rotation_style": _i32(body, 122),
        "color": color,
    }
    return effects


def _i32_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_hwp_draw_text(
    records: list[dict[str, Any]],
    paragraph_by_record: dict[int, int],
    start: int,
    end: int,
    shape_level: int,
) -> dict[str, Any] | None:
    list_index = next(
        (
            index
            for index in range(start + 1, end)
            if records[index].get("tag_name") == "LIST_HEADER" and int(records[index].get("level", 0)) == shape_level + 1
        ),
        -1,
    )
    if list_index < 0:
        return None
    body = bytes(records[list_index].get("body", b""))
    if len(body) < 20:
        return None
    attributes = _u32(body, 2)
    list_level = int(records[list_index].get("level", 0))
    list_end = next(
        (
            index
            for index in range(list_index + 1, end)
            if int(records[index].get("level", 0)) < list_level
            or (
                int(records[index].get("level", 0)) == list_level
                and records[index].get("tag_name") != "PARA_HEADER"
            )
        ),
        end,
    )
    paragraphs = [
        paragraph_by_record[index]
        for index in range(list_index + 1, list_end)
        if index in paragraph_by_record and int(records[index].get("level", 0)) == list_level
    ]
    return {
        "sub_list": {
            "text_direction": "HORIZONTAL",
            "line_wrap": "SQUEEZE" if attributes & (1 << 19) else "BREAK",
            "vertical_align": {0: "TOP", 2: "CENTER", 3: "BOTTOM"}.get((attributes >> 20) & 0x3, "TOP"),
            "text_width": 0,
            "text_height": 0,
            "has_text_ref": False,
            "has_num_ref": False,
        },
        "margin": _margin(*struct.unpack_from("<HHHH", body, 8)),
        "last_width": _i32(body, 16),
        "paragraph_indexes": paragraphs,
        "_record_index": list_index,
    }


def _parse_hwpx_common_object(element: ElementTree.Element, children: dict[str, ElementTree.Element]) -> dict[str, Any]:
    size = children.get("sz")
    position = children.get("pos")
    out_margin = children.get("outMargin")
    return {
        "id": _xml_int(element.attrib.get("id")),
        "z_order": _xml_i32(element.attrib.get("zOrder")),
        "numbering_type": str(element.attrib.get("numberingType", "NONE")),
        "text_wrap": str(element.attrib.get("textWrap", "TOP_AND_BOTTOM")),
        "text_flow": str(element.attrib.get("textFlow", "BOTH_SIDES")),
        "lock": _xml_bool(element.attrib.get("lock")),
        "dropcap_style": str(element.attrib.get("dropcapstyle", "None")),
        "href": str(element.attrib.get("href", "")),
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


def _parse_hwpx_shape_element(element: ElementTree.Element, children: dict[str, ElementTree.Element]) -> dict[str, Any]:
    offset = children.get("offset")
    original = children.get("orgSz")
    current = children.get("curSz")
    flip = children.get("flip")
    rotation = children.get("rotationInfo")
    rendering = children.get("renderingInfo")
    matrices = []
    if rendering is not None:
        for matrix in list(rendering):
            name = _local_name(matrix.tag)
            if name not in {"transMatrix", "scaMatrix", "rotMatrix"}:
                continue
            matrices.append({"type": name, "values": [_xml_float(matrix.attrib.get(f"e{index}")) for index in range(1, 7)]})
    return {
        "group_level": _xml_int(element.attrib.get("groupLevel")),
        "local_version": 1,
        "offset": _parse_xml_point(offset),
        "original_size": {
            "width": _xml_int(original.attrib.get("width") if original is not None else None),
            "height": _xml_int(original.attrib.get("height") if original is not None else None),
        },
        "current_size": {
            "width": _xml_int(current.attrib.get("width") if current is not None else None),
            "height": _xml_int(current.attrib.get("height") if current is not None else None),
        },
        "flip": {
            "horizontal": _xml_bool(flip.attrib.get("horizontal") if flip is not None else None),
            "vertical": _xml_bool(flip.attrib.get("vertical") if flip is not None else None),
        },
        "rotation": {
            "angle": _xml_int(rotation.attrib.get("angle") if rotation is not None else None),
            "center_x": _xml_i32(rotation.attrib.get("centerX") if rotation is not None else None),
            "center_y": _xml_i32(rotation.attrib.get("centerY") if rotation is not None else None),
            "rotate_image": _xml_bool(rotation.attrib.get("rotateimage") if rotation is not None else None),
        },
        "matrices": matrices,
        "instance_id": _xml_int(element.attrib.get("instid")),
        "parse_status": "parsed",
        "source_only": {},
    }


def _parse_hwpx_line_shape(element: ElementTree.Element | None) -> dict[str, Any]:
    if element is None:
        return _default_line_shape()
    return {
        "color": str(element.attrib.get("color", "#000000")),
        "width": _xml_i32(element.attrib.get("width")),
        "style": str(element.attrib.get("style", "NONE")),
        "end_cap": str(element.attrib.get("endCap", "ROUND")),
        "head_style": str(element.attrib.get("headStyle", "NORMAL")),
        "tail_style": str(element.attrib.get("tailStyle", "NORMAL")),
        "head_fill": _xml_bool(element.attrib.get("headfill")),
        "tail_fill": _xml_bool(element.attrib.get("tailfill")),
        "head_size": str(element.attrib.get("headSz", "SMALL_SMALL")),
        "tail_size": str(element.attrib.get("tailSz", "SMALL_SMALL")),
        "outline_style": str(element.attrib.get("outlineStyle", "NORMAL")),
        "alpha": _xml_int(element.attrib.get("alpha")),
    }


def _parse_hwpx_specific(
    kind: str,
    element: ElementTree.Element,
    children: dict[str, ElementTree.Element],
) -> dict[str, Any]:
    if kind == "pic":
        rect = children.get("imgRect")
        clip = children.get("imgClip")
        dimension = children.get("imgDim")
        margin = children.get("inMargin")
        image = children.get("img")
        effects = children.get("effects")
        points = []
        if rect is not None:
            point_by_name = {_local_name(child.tag): child for child in list(rect)}
            points = [_parse_xml_point(point_by_name.get(f"pt{index}")) for index in range(4)]
        return {
            "points": points,
            "crop": {
                "left": _xml_i32(clip.attrib.get("left") if clip is not None else None),
                "top": _xml_i32(clip.attrib.get("top") if clip is not None else None),
                "right": _xml_i32(clip.attrib.get("right") if clip is not None else None),
                "bottom": _xml_i32(clip.attrib.get("bottom") if clip is not None else None),
            },
            "dimension": {
                "width": _xml_int(
                    dimension.attrib.get("dimwidth") if dimension is not None else None
                ),
                "height": _xml_int(
                    dimension.attrib.get("dimheight") if dimension is not None else None
                ),
            },
            "in_margin": _parse_xml_margin(margin),
            "brightness": _xml_i32(image.attrib.get("bright") if image is not None else None),
            "contrast": _xml_i32(image.attrib.get("contrast") if image is not None else None),
            "effect": str(image.attrib.get("effect", "REAL_PIC")) if image is not None else "REAL_PIC",
            "binary_storage_id": _binary_ref(image.attrib.get("binaryItemIDRef") if image is not None else None),
            "border_alpha": _xml_int(element.attrib.get("alpha")),
            "instance_id": _xml_int(element.attrib.get("instid")),
            "effects": _parse_hwpx_picture_effects(effects),
            "effect_payload_size": 0,
            "parse_status": "parsed",
        }
    if kind == "rect":
        return {
            "ratio": _xml_int(element.attrib.get("ratio")),
            "points": [_parse_xml_point(children.get(f"pt{index}")) for index in range(4)],
            "parse_status": "parsed",
        }
    if kind == "line":
        return {
            "start": _parse_xml_point(children.get("startPt")),
            "end": _parse_xml_point(children.get("endPt")),
            "reverse": _xml_bool(element.attrib.get("isReverseHV")),
            "parse_status": "parsed",
        }
    if kind == "polygon":
        return {
            "points": [_parse_xml_point(child) for child in list(element) if _local_name(child.tag) == "pt"],
            "parse_status": "parsed",
        }
    if kind == "ellipse":
        names = {"center": "center", "axis1": "ax1", "axis2": "ax2", "start1": "start1", "end1": "end1", "start2": "start2", "end2": "end2"}
        return {
            "interval_dirty": _xml_bool(element.attrib.get("intervalDirty")),
            "has_arc_property": _xml_bool(element.attrib.get("hasArcPr")),
            "arc_type": str(element.attrib.get("arcType", "NORMAL")),
            "points": {name: _parse_xml_point(children.get(tag)) for name, tag in names.items()},
            "parse_status": "parsed",
        }
    if kind == "ole":
        extent = children.get("extent")
        return {
            "attributes": 0,
            "extent": _parse_xml_point(extent),
            "binary_storage_id": _binary_ref(element.attrib.get("binaryItemIDRef")),
            "parse_status": "parsed",
        }
    return {"parse_status": "not_applicable"}


def _parse_hwpx_picture_effects(
    element: ElementTree.Element | None,
) -> dict[str, Any]:
    if element is None:
        return {"flags": 0, "unsupported_flags": 0}
    children = {_local_name(child.tag): child for child in list(element)}
    flags = (
        int("shadow" in children)
        | (int("glow" in children) << 1)
        | (int("softEdge" in children) << 2)
        | (int("reflection" in children) << 3)
    )
    effects: dict[str, Any] = {
        "flags": flags,
        "unsupported_flags": flags & ~0x1,
    }
    shadow = children.get("shadow")
    if shadow is None:
        return effects
    nested = {_local_name(child.tag): child for child in list(shadow)}
    skew = nested.get("skew")
    scale = nested.get("scale")
    color_element = nested.get("effectsColor")
    color_children = (
        {_local_name(child.tag): child for child in list(color_element)}
        if color_element is not None
        else {}
    )
    rgb = color_children.get("rgb")
    effects["shadow"] = {
        "style": str(shadow.attrib.get("style", "OUTSIDE")),
        "alpha": _xml_float(shadow.attrib.get("alpha")),
        "radius": _xml_float(shadow.attrib.get("radius")),
        "direction": _xml_float(shadow.attrib.get("direction")),
        "distance": _xml_float(shadow.attrib.get("distance")),
        "align_style": str(shadow.attrib.get("alignStyle", "CENTER")),
        "skew": {
            "x": _xml_float(skew.attrib.get("x") if skew is not None else None),
            "y": _xml_float(skew.attrib.get("y") if skew is not None else None),
        },
        "scale": {
            "x": _xml_float(scale.attrib.get("x") if scale is not None else None),
            "y": _xml_float(scale.attrib.get("y") if scale is not None else None),
        },
        "rotation_style": _xml_i32(shadow.attrib.get("rotationStyle")),
        "color": {
            "type": str(
                color_element.attrib.get("type", "RGB")
                if color_element is not None
                else "RGB"
            ),
            "scheme_index": _xml_i32(
                color_element.attrib.get("schemeIdx")
                if color_element is not None
                else -1,
                -1,
            ),
            "system_index": _xml_i32(
                color_element.attrib.get("systemIdx")
                if color_element is not None
                else -1,
                -1,
            ),
            "preset_index": _xml_i32(
                color_element.attrib.get("presetIdx")
                if color_element is not None
                else -1,
                -1,
            ),
            "r": _xml_int(rgb.attrib.get("r") if rgb is not None else None),
            "g": _xml_int(rgb.attrib.get("g") if rgb is not None else None),
            "b": _xml_int(rgb.attrib.get("b") if rgb is not None else None),
        },
    }
    return effects


def _parse_hwpx_draw_text(element: ElementTree.Element | None) -> dict[str, Any] | None:
    if element is None:
        return None
    children = {_local_name(child.tag): child for child in list(element)}
    sub_list = children.get("subList")
    margin = children.get("textMargin")
    return {
        "sub_list": {
            "text_direction": str(sub_list.attrib.get("textDirection", "HORIZONTAL")) if sub_list is not None else "HORIZONTAL",
            "line_wrap": str(sub_list.attrib.get("lineWrap", "BREAK")) if sub_list is not None else "BREAK",
            "vertical_align": str(sub_list.attrib.get("vertAlign", "TOP")) if sub_list is not None else "TOP",
            "text_width": _xml_i32(sub_list.attrib.get("textWidth") if sub_list is not None else None),
            "text_height": _xml_i32(sub_list.attrib.get("textHeight") if sub_list is not None else None),
            "has_text_ref": _xml_bool(sub_list.attrib.get("hasTextRef") if sub_list is not None else None),
            "has_num_ref": _xml_bool(sub_list.attrib.get("hasNumRef") if sub_list is not None else None),
        },
        "margin": _parse_xml_margin(margin),
        "last_width": _xml_i32(element.attrib.get("lastWidth")),
        "paragraph_indexes": [],
    }


def _binary_result(values: list[dict[str, Any]], statuses: Counter[str], *, status: str | None = None) -> dict[str, Any]:
    formats = Counter(str(value.get("format", "")) for value in values)
    kinds = Counter(str(value.get("kind", value.get("type", "unknown"))).lower() for value in values)
    return {
        "status": status or ("parsed" if set(statuses) <= {"parsed"} else "parsed_with_warnings"),
        "counts": {
            "binary_count": len(values),
            "image_count": sum(value == "image" for value in kinds.elements()),
            "ole_count": sum(value == "ole" for value in kinds.elements()),
            "format_counts": dict(sorted(formats.items())),
            "parse_warning_count": sum(count for key, count in statuses.items() if key != "parsed"),
        },
        "parse_status_counts": dict(sorted(statuses.items())),
        "items": values,
    }


def _object_result(
    shapes: list[dict[str, Any]],
    paragraph_count: int,
    paragraph_levels: dict[int, int],
    statuses: Counter[str],
) -> dict[str, Any]:
    kinds = Counter(str(shape.get("kind", "unknown")) for shape in shapes)
    return {
        "status": "parsed" if set(statuses) <= {"parsed"} else "parsed_with_warnings",
        "counts": {
            "shape_count": len(shapes),
            "root_object_count": sum(isinstance(shape.get("common"), dict) for shape in shapes),
            "group_child_count": sum(_as_int(shape.get("parent_shape_index")) >= 0 for shape in shapes),
            "picture_count": kinds.get("pic", 0),
            "draw_text_count": sum(isinstance(shape.get("draw_text"), dict) for shape in shapes),
            "draw_text_paragraph_count": sum(
                len(shape.get("draw_text", {}).get("paragraph_indexes", []))
                for shape in shapes
                if isinstance(shape.get("draw_text"), dict)
            ),
            "kind_counts": dict(sorted(kinds.items())),
            "paragraph_count": paragraph_count,
            "parse_warning_count": sum(count for key, count in statuses.items() if key != "parsed"),
        },
        "parse_status_counts": dict(sorted(statuses.items())),
        "paragraph_levels": {str(key): value for key, value in sorted(paragraph_levels.items())},
        "shapes": shapes,
    }


def _canonical_shapes(values: Any, strict_paragraph_indexes: bool) -> list[dict[str, Any]]:
    shapes = [value for value in values if isinstance(value, dict)] if isinstance(values, list) else []
    identities = [_shape_identity(shape, index) for index, shape in enumerate(shapes)]
    canonical = []
    for index, shape in enumerate(shapes):
        parent_index = _as_int(shape.get("parent_shape_index"), -1)
        parent_identity = identities[parent_index] if 0 <= parent_index < len(identities) else ""
        canonical.append(
            (
                identities[index],
                _canonical_shape(
                    shape,
                    parent_identity=parent_identity,
                    strict_paragraph_indexes=strict_paragraph_indexes,
                ),
            )
        )
    return [value for _identity, value in sorted(canonical, key=lambda item: item[0])]


def _canonical_shapes_ordered(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _canonical_shape(
            shape,
            parent_identity=str(_as_int(shape.get("parent_shape_index"), -1)),
            strict_paragraph_indexes=True,
        )
        for shape in values
    ]


def _canonical_shape(
    value: dict[str, Any],
    *,
    parent_identity: str,
    strict_paragraph_indexes: bool,
) -> dict[str, Any]:
    draw_text = _canonical_nested(value.get("draw_text"))
    if isinstance(draw_text, dict) and not strict_paragraph_indexes:
        draw_text["paragraph_count"] = len(draw_text.pop("paragraph_indexes", []))
    anchor = _as_int(value.get("anchor_paragraph_index"), -1)
    result = {
        "kind": value.get("kind"),
        "parent_identity": parent_identity,
        "anchor_paragraph_index": anchor if strict_paragraph_indexes else int(anchor >= 0),
        "common": _canonical_nested(value.get("common")),
        "element": _canonical_nested(value.get("element")),
        "line_shape": _canonical_nested(value.get("line_shape")),
        "fill": _canonical_nested(value.get("fill")),
        "draw_text": draw_text,
        "specific": _canonical_nested(value.get("specific")),
    }
    return result


def _shape_identity(value: dict[str, Any], index: int) -> str:
    common = value.get("common") if isinstance(value.get("common"), dict) else {}
    common_id = _as_int(common.get("id"))
    if common_id:
        return f"root:{common_id:010d}"
    element = value.get("element") if isinstance(value.get("element"), dict) else {}
    instance_id = _as_int(element.get("instance_id"))
    if instance_id:
        return f"inst:{instance_id:010d}"
    specific = value.get("specific") if isinstance(value.get("specific"), dict) else {}
    specific_instance_id = _as_int(specific.get("instance_id"))
    if specific_instance_id:
        return f"inst:{specific_instance_id:010d}"
    return f'fallback:{str(value.get("kind", "unknown"))}:{index:06d}'


def _canonical_nested(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _canonical_nested(nested)
            for key, nested in value.items()
            if key not in {"parse_status", "source_only", "_record_index", "local_version", "effect_payload_size", "attributes"}
        }
    if isinstance(value, list):
        return [_canonical_nested(nested) for nested in value]
    if isinstance(value, float):
        return round(value, 6)
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


def _content_manifest_items(package: ZipFile) -> dict[str, dict[str, str]]:
    try:
        root = ElementTree.fromstring(package.read("Contents/content.hpf"))
    except (KeyError, ElementTree.ParseError):
        return {}
    values = {}
    for element in root.iter():
        if _local_name(element.tag) != "item":
            continue
        href = str(element.attrib.get("href", ""))
        if not href.startswith("BinData/"):
            continue
        values[href] = {
            "id": str(element.attrib.get("id", "")),
            "media_type": str(element.attrib.get("media-type", "")),
        }
    return values


def _decode_binary_payload(
    payload: bytes,
    *,
    binary_type: int,
    compression_code: int,
    document_compressed: bool,
) -> tuple[bytes, str]:
    should_decompress = binary_type == 1 and (compression_code == 1 or (compression_code == 0 and document_compressed))
    if not should_decompress:
        return payload, "raw"
    for wbits, label in ((-15, "raw_deflate"), (15, "zlib")):
        try:
            return decompress_bounded(payload, wbits), label
        except ResourceLimitError:
            raise
        except zlib.error:
            continue
    return payload, "decompress_failed"


def _decode_record_stream(payload: bytes, compressed: bool) -> bytes:
    if not compressed:
        return payload
    for wbits in (-15, 15):
        try:
            return decompress_bounded(payload, wbits)
        except ResourceLimitError:
            raise
        except zlib.error:
            continue
    return payload


def _parse_record_stream(payload: bytes) -> list[dict[str, Any]]:
    records = []
    offset = 0
    while offset + 4 <= len(payload):
        header = _u32(payload, offset)
        offset += 4
        tag_id = header & 0x3FF
        level = (header >> 10) & 0x3FF
        size = (header >> 20) & 0xFFF
        if size == 0xFFF:
            if offset + 4 > len(payload):
                break
            size = _u32(payload, offset)
            offset += 4
        if offset + size > len(payload):
            break
        body = payload[offset : offset + size]
        offset += size
        records.append({"tag_name": "BIN_DATA" if tag_id == 0x12 else f"TAG_{tag_id}", "level": level, "body": body})
    return records


def _next_shape_record(records: list[dict[str, Any]], start: int, expected_level: int) -> int:
    for index in range(start + 1, len(records)):
        level = int(records[index].get("level", 0))
        if level < expected_level:
            break
        if level == expected_level and records[index].get("tag_name") == "SHAPE_COMPONENT":
            return index
    return -1


def _shape_scope_end(records: list[dict[str, Any]], start: int, level: int) -> int:
    return next(
        (
            index
            for index in range(start + 1, len(records))
            if records[index].get("tag_name") == "SHAPE_COMPONENT" and int(records[index].get("level", 0)) <= level
        ),
        len(records),
    )


def _specific_record(
    records: list[dict[str, Any]],
    start: int,
    end: int,
    level: int,
    kind: str,
) -> dict[str, Any] | None:
    expected = SPECIFIC_TAG_BY_KIND.get(kind)
    if expected is None:
        return None
    return next(
        (
            records[index]
            for index in range(start + 1, end)
            if records[index].get("tag_name") == expected and int(records[index].get("level", 0)) == level + 1
        ),
        None,
    )


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


def _default_common_object(status: str) -> dict[str, Any]:
    return {
        "id": 0,
        "z_order": 0,
        "numbering_type": "NONE",
        "text_wrap": "TOP_AND_BOTTOM",
        "text_flow": "BOTH_SIDES",
        "lock": False,
        "dropcap_style": "None",
        "href": "",
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


def _default_shape_element(status: str) -> dict[str, Any]:
    return {
        "group_level": 0,
        "local_version": 1,
        "offset": _point(0, 0),
        "original_size": {"width": 0, "height": 0},
        "current_size": {"width": 0, "height": 0},
        "flip": {"horizontal": False, "vertical": False},
        "rotation": {"angle": 0, "center_x": 0, "center_y": 0, "rotate_image": False},
        "matrices": [],
        "instance_id": 0,
        "parse_status": status,
        "source_only": {},
    }


def _default_line_shape() -> dict[str, Any]:
    return {
        "color": "#000000",
        "width": 0,
        "style": "NONE",
        "end_cap": "ROUND",
        "head_style": "NORMAL",
        "tail_style": "NORMAL",
        "head_fill": False,
        "tail_fill": False,
        "head_size": "SMALL_SMALL",
        "tail_size": "SMALL_SMALL",
        "outline_style": "NORMAL",
        "alpha": 0,
    }


def _point(x: int, y: int) -> dict[str, int]:
    return {"x": int(x), "y": int(y)}


def _margin(left: int, right: int, top: int, bottom: int) -> dict[str, int]:
    return {"left": int(left), "right": int(right), "top": int(top), "bottom": int(bottom)}


def _parse_xml_point(element: ElementTree.Element | None) -> dict[str, int]:
    if element is None:
        return _point(0, 0)
    return _point(_xml_i32(element.attrib.get("x")), _xml_i32(element.attrib.get("y")))


def _parse_xml_margin(element: ElementTree.Element | None) -> dict[str, int]:
    if element is None:
        return _margin(0, 0, 0, 0)
    return _margin(*(_xml_i32(element.attrib.get(key)) for key in ("left", "right", "top", "bottom")))


def _binary_ref(value: Any) -> int:
    match = BIN_STREAM_ID.search(str(value or ""))
    return int(match.group(1)) if match is not None else 0


def _hwp_stream_storage_id(value: str) -> int | None:
    stem = Path(value.rsplit("/", 1)[-1]).stem
    match = re.fullmatch(r"BIN([0-9A-Fa-f]+)", stem, re.IGNORECASE)
    if match is None:
        return None
    return int(match.group(1), 16)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _u16(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<H", payload, offset)[0]


def _i16(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<h", payload, offset)[0]


def _u32(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<I", payload, offset)[0]


def _i32(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<i", payload, offset)[0]


def _f32(payload: bytes, offset: int) -> float:
    return struct.unpack_from("<f", payload, offset)[0]


def _i8(payload: bytes, offset: int) -> int:
    return struct.unpack_from("<b", payload, offset)[0]


def _xml_bool(value: Any) -> bool:
    return str(value or "0").strip().lower() in {"1", "true", "yes"}


def _xml_int(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(str(value)))
    except (TypeError, ValueError):
        return default


def _xml_i32(value: Any, default: int = 0) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return default
    return parsed - (1 << 32) if parsed > 0x7FFFFFFF else parsed


def _xml_float(value: Any) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
