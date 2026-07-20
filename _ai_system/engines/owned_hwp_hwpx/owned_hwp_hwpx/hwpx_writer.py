"""Deterministic HWPX writer for owned HWP-derived document models."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo


DETERMINISTIC_ZIP_DATETIME = (1980, 1, 1, 0, 0, 0)


def write_hwpx_package(path: Path, model: dict[str, Any]) -> dict[str, Any]:
    """Write a deterministic HWPX package from a neutral document model."""

    path.parent.mkdir(parents=True, exist_ok=True)
    entries = build_hwpx_entries(model)
    with ZipFile(path, "w") as package:
        for index, (name, data) in enumerate(entries):
            payload = data.encode("utf-8") if isinstance(data, str) else data
            info = ZipInfo(name, date_time=DETERMINISTIC_ZIP_DATETIME)
            info.create_system = 0
            info.external_attr = 0
            info.compress_type = ZIP_STORED if index == 0 and name == "mimetype" else ZIP_DEFLATED
            if info.compress_type == ZIP_STORED:
                package.writestr(info, payload, compress_type=ZIP_STORED)
            else:
                package.writestr(info, payload, compress_type=ZIP_DEFLATED, compresslevel=9)
    return {
        "status": "written",
        "entry_count": len(entries),
        "section_count": len(model.get("sections", [])),
        "bin_data_count": _as_int(model.get("summary", {}).get("bin_data_count")),
        "deterministic_zip_metadata": True,
    }


def write_dry_run_hwpx(path: Path, model: dict[str, Any]) -> dict[str, Any]:
    """Compatibility alias for the former research writer entrypoint."""

    return write_hwpx_package(path, model)


def build_hwpx_entries(model: dict[str, Any]) -> list[tuple[str, str | bytes]]:
    sections = list(model.get("sections", []))
    bin_data_count = _as_int(model.get("summary", {}).get("bin_data_count"))
    binary_items = [item for item in model.get("_binary_payloads", []) if isinstance(item, dict)]
    if not binary_items:
        binary_items = [
            {
                "item_id": f"binary{index + 1}",
                "entry_name": f"BinData/Bin{index + 1:04d}.bin",
                "format": "bin",
                "kind": "binary",
                "payload": b"",
            }
            for index in range(bin_data_count)
        ]
    summary = model.get("summary", {})
    section_entries = [
        (f"Contents/section{index}.xml", _section_xml(section, summary))
        for index, section in enumerate(sections)
    ]
    bin_entries = [
        (str(item.get("entry_name", f"BinData/Bin{index + 1:04d}.bin")), bytes(item.get("payload", b"")))
        for index, item in enumerate(binary_items)
    ]
    return [
        ("mimetype", "application/hwp+zip"),
        ("version.xml", _version_xml()),
        ("META-INF/container.xml", _container_xml()),
        ("settings.xml", _settings_xml()),
        ("Contents/header.xml", _header_xml(model)),
        ("Contents/content.hpf", _content_hpf_xml(model, binary_items)),
        *section_entries,
        ("META-INF/manifest.xml", _manifest_xml(len(sections), binary_items)),
        *bin_entries,
    ]


def build_dry_run_hwpx_entries(model: dict[str, Any]) -> list[tuple[str, str | bytes]]:
    """Compatibility alias for callers that inspect generated package entries."""

    return build_hwpx_entries(model)


def _section_xml(section: dict[str, Any], summary: dict[str, Any]) -> str:
    paragraph_count = max(1, _as_int(section.get("paragraph_count")))
    page_def_count = _as_int(section.get("page_def_count"))
    line_segment_count = _as_int(section.get("line_segment_count"))

    line_segment_groups = _fit_line_segment_groups(
        section.get("line_segment_semantics"),
        paragraph_count,
        line_segment_count,
    )
    page_defs = _fit_page_definitions(section.get("page_definitions", []), page_def_count)
    section_semantics = section.get("section_semantics", {})
    if page_defs and isinstance(section_semantics, dict) and section_semantics:
        page_defs[0] = {**page_defs[0], "section_semantics": section_semantics}
    page_def_groups = _distribute_items(page_defs, paragraph_count)
    paragraph_texts = list(section.get("paragraph_texts", []))
    paragraph_controls = _select_anchored_layout_controls(
        list(section.get("paragraph_controls", [])),
        section.get("layout_control_child_counts", {}),
    )
    paragraph_styles = list(section.get("paragraph_styles", []))
    table_shapes = list(section.get("table_shapes", []))
    object_shapes = [value for value in section.get("object_shapes", []) if isinstance(value, dict)]
    table_by_anchor: dict[int, list[int]] = {}
    for table_index, table in enumerate(table_shapes):
        if not isinstance(table, dict):
            continue
        table_by_anchor.setdefault(_signed_int(table.get("anchor_paragraph_index"), -1), []).append(table_index)
    embedded_groups = [
        value
        for value in section.get("embedded_paragraph_groups", [])
        if isinstance(value, dict)
    ]
    embedded_groups_by_anchor: dict[int, list[dict[str, Any]]] = {}
    for group in embedded_groups:
        embedded_groups_by_anchor.setdefault(
            _signed_int(group.get("anchor_paragraph_index"), -1),
            [],
        ).append(group)
    object_by_anchor: dict[int, list[int]] = {}
    object_children: dict[int, list[int]] = {}
    for shape_index, shape in enumerate(object_shapes):
        parent = _signed_int(shape.get("parent_shape_index"), -1)
        if parent >= 0:
            object_children.setdefault(parent, []).append(shape_index)
            continue
        if isinstance(shape.get("common"), dict):
            object_by_anchor.setdefault(_signed_int(shape.get("anchor_paragraph_index"), -1), []).append(shape_index)
    render_context = {
        "section_ref": section["section_ref"],
        "line_segment_groups": line_segment_groups,
        "page_def_groups": page_def_groups,
        "paragraph_texts": paragraph_texts,
        "paragraph_controls": paragraph_controls,
        "paragraph_styles": paragraph_styles,
        "summary": summary,
        "tables": table_shapes,
        "table_by_anchor": table_by_anchor,
        "embedded_groups_by_anchor": embedded_groups_by_anchor,
        "rendering_tables": set(),
        "objects": object_shapes,
        "object_by_anchor": object_by_anchor,
        "object_children": object_children,
        "rendering_objects": set(),
        "compatibility_profile": str(section.get("compatibility_profile", "")),
    }
    raw_root_indexes = section.get("root_paragraph_indexes", [])
    root_indexes = [
        _as_int(index)
        for index in raw_root_indexes
        if 0 <= _as_int(index) < paragraph_count
    ] if isinstance(raw_root_indexes, list) else list(range(paragraph_count))
    if not root_indexes and paragraph_count:
        root_indexes = list(range(paragraph_count))
    paragraphs = "".join(_render_paragraph(render_context, index) for index in root_indexes)
    orphan_tables = "".join(
        _render_table(render_context, index)
        for index in table_by_anchor.get(-1, [])
    )
    orphan_objects = "".join(
        _render_object(render_context, index)
        for index in object_by_anchor.get(-1, [])
    )
    controls = _remaining_layout_controls_xml(
        section.get("layout_control_child_counts", {}),
        render_context.get("paragraph_controls", []),
        render_context["compatibility_profile"],
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
        'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
        'xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" '
        'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section">'
        f"{paragraphs}{orphan_tables}{orphan_objects}{controls}</hs:sec>"
    )


def _render_paragraph(context: dict[str, Any], index: int) -> str:
    line_segment_groups = context["line_segment_groups"]
    page_groups = context["page_def_groups"]
    texts = context["paragraph_texts"]
    controls = context["paragraph_controls"]
    styles = context["paragraph_styles"]
    embedded_items: list[tuple[int, int, str]] = []
    for group_index, group in enumerate(context.get("embedded_groups_by_anchor", {}).get(index, [])):
        embedded_items.append(
            (
                _as_int(group.get("order_key")),
                group_index,
                _embedded_paragraph_group_xml(context, index, group_index, group),
            )
        )
    for table_index in context["table_by_anchor"].get(index, []):
        table = context["tables"][table_index]
        embedded_items.append(
            (
                _table_order_key(table, index),
                len(embedded_items),
                _render_table(context, table_index),
            )
        )
    for shape_index in context.get("object_by_anchor", {}).get(index, []):
        shape = context["objects"][shape_index]
        embedded_items.append(
            (
                _as_int(shape.get("order_key")),
                len(embedded_items),
                _render_object(context, shape_index),
            )
        )
    return _paragraph_xml(
        context["section_ref"],
        index,
        line_segment_groups[index] if index < len(line_segment_groups) else [],
        page_groups[index] if index < len(page_groups) else [],
        texts[index] if index < len(texts) else "",
        controls[index] if index < len(controls) else [],
        styles[index] if index < len(styles) else {},
        context["summary"],
        sorted(embedded_items),
        context.get("compatibility_profile", ""),
    )


def _embedded_paragraph_group_xml(
    context: dict[str, Any],
    anchor_index: int,
    group_index: int,
    group: dict[str, Any],
) -> str:
    paragraph_indexes = group.get("paragraph_indexes", [])
    paragraphs = "".join(
        _render_paragraph(context, index)
        for index in (_as_int(value) for value in paragraph_indexes if value is not None)
        if 0 <= index < len(context.get("paragraph_styles", []))
    )
    return _sub_list_container_xml({}, paragraphs)


def _render_object(context: dict[str, Any], shape_index: int) -> str:
    shapes = context.get("objects", [])
    if not isinstance(shapes, list) or not 0 <= shape_index < len(shapes):
        return ""
    rendering = context.get("rendering_objects")
    if not isinstance(rendering, set):
        rendering = set()
        context["rendering_objects"] = rendering
    if shape_index in rendering:
        return ""
    rendering.add(shape_index)
    try:
        return _object_xml(context, shape_index, shapes[shape_index])
    finally:
        rendering.remove(shape_index)


def _object_xml(context: dict[str, Any], shape_index: int, shape: dict[str, Any]) -> str:
    kind = str(shape.get("kind", "rect"))
    if kind == "raw":
        raw_xml = str(shape.get("raw_xml", ""))
        try:
            root = ElementTree.fromstring(raw_xml)
        except ElementTree.ParseError:
            return ""
        if root.tag.rsplit("}", 1)[-1] in {
            "container", "rect", "ellipse", "line", "connectLine", "polygon", "curve", "arc"
        }:
            return raw_xml
        return ""
    tag_name = "connectLine" if kind == "line" and context.get("compatibility_profile") == "hancom" else kind
    element = shape.get("element", {}) if isinstance(shape.get("element"), dict) else {}
    common = shape.get("common") if isinstance(shape.get("common"), dict) else None
    specific = shape.get("specific", {}) if isinstance(shape.get("specific"), dict) else {}
    instance_id = _as_int(element.get("instance_id"))
    if kind == "pic":
        instance_id = _as_int(specific.get("instance_id")) or instance_id
    attributes = _object_attributes(shape_index, kind, element, common, specific, instance_id)
    base = _shape_element_xml(element)
    children = "".join(
        _render_object(context, child_index)
        for child_index in context.get("object_children", {}).get(shape_index, [])
    )
    drawing = ""
    if kind in {"rect", "line", "polygon", "ellipse"}:
        drawing = (
            f'{_shape_line_xml(shape.get("line_shape"))}'
            f'{_fill_brush_xml(shape.get("fill"))}'
            '<hp:shadow type="NONE" color="#B2B2B2" offsetX="0" offsetY="0" alpha="0"/>'
            f'{_shape_draw_text_xml(context, shape.get("draw_text"))}'
        )
    point_prefix = "hp" if tag_name == "connectLine" else "hc"
    object_specific = _shape_specific_xml(kind, specific, point_prefix=point_prefix)
    common_xml = _shape_common_xml(common) if common is not None else ""
    return f'<hp:{tag_name}{attributes}>{base}{children}{drawing}{object_specific}{common_xml}</hp:{tag_name}>'


def _object_attributes(
    shape_index: int,
    kind: str,
    element: dict[str, Any],
    common: dict[str, Any] | None,
    specific: dict[str, Any],
    instance_id: int,
) -> str:
    if common is None:
        attributes = (
            f' href="" groupLevel="{_as_int(element.get("group_level"))}" '
            f'instid="{instance_id}"'
        )
        if kind == "pic":
            attributes += f' reverse="0" alpha="{_as_int(specific.get("border_alpha"))}"'
        elif kind == "rect":
            attributes += f' ratio="{_as_int(specific.get("ratio"))}"'
        elif kind == "line":
            attributes += f' isReverseHV="{_bool_int(specific.get("reverse"))}"'
        elif kind == "ellipse":
            attributes += (
                f' intervalDirty="{_bool_int(specific.get("interval_dirty"))}" '
                f'hasArcPr="{_bool_int(specific.get("has_arc_property"))}" '
                f'arcType="{_safe_enum(specific.get("arc_type"), "NORMAL")}"'
            )
        return attributes
    values = common or {}
    object_id = _as_int(values.get("id")) if common else shape_index
    attributes = (
        f' id="{object_id}" zOrder="{_signed_int(values.get("z_order"))}" '
        f'numberingType="{_safe_enum(values.get("numbering_type"), "NONE")}" '
        f'textWrap="{_safe_enum(values.get("text_wrap"), "TOP_AND_BOTTOM")}" '
        f'textFlow="{_safe_enum(values.get("text_flow"), "BOTH_SIDES")}" '
        f'lock="{_bool_int(values.get("lock"))}" dropcapstyle="{_xml_escape(values.get("dropcap_style", "None"))}" '
        f'href="{_xml_escape(values.get("href", ""))}" '
        f'groupLevel="{_as_int(element.get("group_level"))}" instid="{instance_id}"'
    )
    if kind == "pic":
        attributes += f' reverse="0" alpha="{_as_int(specific.get("border_alpha"))}"'
    elif kind == "rect":
        attributes += f' ratio="{_as_int(specific.get("ratio"))}"'
    elif kind == "line":
        attributes += f' isReverseHV="{_bool_int(specific.get("reverse"))}" type="STRAIGHT_ONEWAY"'
    elif kind == "ellipse":
        attributes += (
            f' intervalDirty="{_bool_int(specific.get("interval_dirty"))}" '
            f'hasArcPr="{_bool_int(specific.get("has_arc_property"))}" '
            f'arcType="{_safe_enum(specific.get("arc_type"), "NORMAL")}"'
        )
    elif kind == "ole":
        storage_id = _as_int(specific.get("binary_storage_id"))
        attributes += (
            f' objectType="STATIC" binaryItemIDRef="ole{storage_id}" hasMoniker="0" '
            f'drawAspect="CONTENT" eqBaseLine="0"'
        )
    return attributes


def _shape_element_xml(value: dict[str, Any]) -> str:
    offset = value.get("offset", {}) if isinstance(value.get("offset"), dict) else {}
    original = value.get("original_size", {}) if isinstance(value.get("original_size"), dict) else {}
    current = value.get("current_size", {}) if isinstance(value.get("current_size"), dict) else {}
    flip = value.get("flip", {}) if isinstance(value.get("flip"), dict) else {}
    rotation = value.get("rotation", {}) if isinstance(value.get("rotation"), dict) else {}
    matrices = "".join(_shape_matrix_xml(matrix) for matrix in value.get("matrices", []) if isinstance(matrix, dict))
    return (
        f'<hp:offset x="{_unsigned_i32(offset.get("x"))}" y="{_unsigned_i32(offset.get("y"))}"/>'
        f'<hp:orgSz width="{_as_int(original.get("width"))}" height="{_as_int(original.get("height"))}"/>'
        f'<hp:curSz width="{_as_int(current.get("width"))}" height="{_as_int(current.get("height"))}"/>'
        f'<hp:flip horizontal="{_bool_int(flip.get("horizontal"))}" vertical="{_bool_int(flip.get("vertical"))}"/>'
        f'<hp:rotationInfo angle="{_as_int(rotation.get("angle"))}" '
        f'centerX="{_unsigned_i32(rotation.get("center_x"))}" centerY="{_unsigned_i32(rotation.get("center_y"))}" '
        f'rotateimage="{_bool_int(rotation.get("rotate_image"))}"/>'
        f'<hp:renderingInfo>{matrices}</hp:renderingInfo>'
    )


def _shape_matrix_xml(value: dict[str, Any]) -> str:
    matrix_type = str(value.get("type", "transMatrix"))
    if matrix_type not in {"transMatrix", "scaMatrix", "rotMatrix"}:
        matrix_type = "transMatrix"
    raw_values = value.get("values", []) if isinstance(value.get("values"), list) else []
    numbers = [float(raw_values[index]) if index < len(raw_values) else 0.0 for index in range(6)]
    attributes = " ".join(f'e{index + 1}="{_float_token(number)}"' for index, number in enumerate(numbers))
    return f'<hc:{matrix_type} {attributes}/>'


def _shape_line_xml(value: Any) -> str:
    line = value if isinstance(value, dict) else {}
    return (
        f'<hp:lineShape color="{_safe_color(line.get("color"), "#000000")}" '
        f'width="{_signed_int(line.get("width"))}" style="{_safe_enum(line.get("style"), "NONE")}" '
        f'endCap="{_safe_enum(line.get("end_cap"), "ROUND")}" '
        f'headStyle="{_safe_enum(line.get("head_style"), "NORMAL")}" '
        f'tailStyle="{_safe_enum(line.get("tail_style"), "NORMAL")}" '
        f'headfill="{_bool_int(line.get("head_fill"))}" tailfill="{_bool_int(line.get("tail_fill"))}" '
        f'headSz="{_safe_enum(line.get("head_size"), "SMALL_SMALL")}" '
        f'tailSz="{_safe_enum(line.get("tail_size"), "SMALL_SMALL")}" '
        f'outlineStyle="{_safe_enum(line.get("outline_style"), "NORMAL")}" '
        f'alpha="{_as_int(line.get("alpha"))}"/>'
    )


def _shape_draw_text_xml(context: dict[str, Any], value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    paragraphs = "".join(
        _render_paragraph(context, index)
        for index in (_as_int(item) for item in value.get("paragraph_indexes", []))
        if 0 <= index < len(context.get("paragraph_styles", []))
    )
    return (
        f'<hp:drawText lastWidth="{_signed_int(value.get("last_width"))}" name="" editable="0">'
        f'{_sub_list_container_xml(value.get("sub_list"), paragraphs)}'
        f'{_margin_xml("textMargin", value.get("margin"))}'
        '</hp:drawText>'
    )


def _shape_specific_xml(
    kind: str,
    value: dict[str, Any],
    *,
    point_prefix: str = "hc",
) -> str:
    if kind == "pic":
        points = value.get("points", []) if isinstance(value.get("points"), list) else []
        point_xml = "".join(
            _shape_point_xml(
                f"pt{index}",
                points[index] if index < len(points) else {},
                prefix="hc",
            )
            for index in range(4)
        )
        crop = value.get("crop", {}) if isinstance(value.get("crop"), dict) else {}
        dimension = (
            value.get("dimension") if isinstance(value.get("dimension"), dict) else {}
        )
        storage_id = _as_int(value.get("binary_storage_id"))
        width = _as_int(dimension.get("width")) or max(
            0,
            _signed_int(crop.get("right")) - _signed_int(crop.get("left")),
        )
        height = _as_int(dimension.get("height")) or max(
            0,
            _signed_int(crop.get("bottom")) - _signed_int(crop.get("top")),
        )
        return (
            f'<hp:imgRect>{point_xml}</hp:imgRect>'
            f'<hp:imgClip left="{_signed_int(crop.get("left"))}" right="{_signed_int(crop.get("right"))}" '
            f'top="{_signed_int(crop.get("top"))}" bottom="{_signed_int(crop.get("bottom"))}"/>'
            f'{_margin_xml("inMargin", value.get("in_margin"))}'
            f'<hp:imgDim dimwidth="{width}" dimheight="{height}"/>'
            f'<hc:img binaryItemIDRef="image{storage_id}" bright="{_signed_int(value.get("brightness"))}" '
            f'contrast="{_signed_int(value.get("contrast"))}" effect="{_safe_enum(value.get("effect"), "REAL_PIC")}" alpha="0"/>'
            f'{_picture_effects_xml(value.get("effects"))}'
        )
    if kind == "rect":
        points = value.get("points", []) if isinstance(value.get("points"), list) else []
        return "".join(
            _shape_point_xml(
                f"pt{index}",
                points[index] if index < len(points) else {},
                prefix="hc",
            )
            for index in range(4)
        )
    if kind == "line":
        return (
            f'{_shape_point_xml("startPt", value.get("start"), prefix=point_prefix)}'
            f'{_shape_point_xml("endPt", value.get("end"), prefix=point_prefix)}'
        )
    if kind == "polygon":
        return "".join(
            _shape_point_xml("pt", point, prefix="hc")
            for point in value.get("points", [])
            if isinstance(point, dict)
        )
    if kind == "ellipse":
        points = value.get("points", {}) if isinstance(value.get("points"), dict) else {}
        names = (("center", "center"), ("ax1", "axis1"), ("ax2", "axis2"), ("start1", "start1"), ("end1", "end1"), ("start2", "start2"), ("end2", "end2"))
        return "".join(
            _shape_point_xml(tag, points.get(key), prefix="hc")
            for tag, key in names
        )
    if kind == "ole":
        return _shape_point_xml("extent", value.get("extent"), prefix="hc") + _shape_line_xml({})
    return ""


def _shape_point_xml(tag_name: str, value: Any, *, prefix: str) -> str:
    point = value if isinstance(value, dict) else {}
    return (
        f'<{prefix}:{tag_name} x="{_signed_int(point.get("x"))}" '
        f'y="{_signed_int(point.get("y"))}"/>'
    )


def _picture_effects_xml(value: Any) -> str:
    effects = value if isinstance(value, dict) else {}
    shadow = effects.get("shadow") if isinstance(effects.get("shadow"), dict) else None
    if shadow is None:
        return "<hp:effects/>"
    skew = shadow.get("skew") if isinstance(shadow.get("skew"), dict) else {}
    scale = shadow.get("scale") if isinstance(shadow.get("scale"), dict) else {}
    color = shadow.get("color") if isinstance(shadow.get("color"), dict) else {}
    return (
        '<hp:effects>'
        f'<hp:shadow style="{_safe_enum(shadow.get("style"), "OUTSIDE")}" '
        f'alpha="{_float_token(float(shadow.get("alpha", 0)))}" '
        f'radius="{_float_token(float(shadow.get("radius", 0)))}" '
        f'direction="{_float_token(float(shadow.get("direction", 0)))}" '
        f'distance="{_float_token(float(shadow.get("distance", 0)))}" '
        f'alignStyle="{_safe_enum(shadow.get("align_style"), "CENTER")}" '
        f'rotationStyle="{_signed_int(shadow.get("rotation_style"))}">'
        f'<hp:skew x="{_float_token(float(skew.get("x", 0)))}" '
        f'y="{_float_token(float(skew.get("y", 0)))}"/>'
        f'<hp:scale x="{_float_token(float(scale.get("x", 1)))}" '
        f'y="{_float_token(float(scale.get("y", 1)))}"/>'
        f'<hp:effectsColor type="{_safe_enum(color.get("type"), "RGB")}" '
        f'schemeIdx="{_signed_int(color.get("scheme_index"), -1)}" '
        f'systemIdx="{_signed_int(color.get("system_index"), -1)}" '
        f'presetIdx="{_signed_int(color.get("preset_index"), -1)}">'
        f'<hp:rgb r="{_as_int(color.get("r"))}" g="{_as_int(color.get("g"))}" '
        f'b="{_as_int(color.get("b"))}"/>'
        '</hp:effectsColor></hp:shadow></hp:effects>'
    )


def _shape_common_xml(value: dict[str, Any]) -> str:
    size = value.get("size", {}) if isinstance(value.get("size"), dict) else {}
    position = value.get("position", {}) if isinstance(value.get("position"), dict) else {}
    return (
        f'<hp:sz width="{_as_int(size.get("width"))}" widthRelTo="{_safe_enum(size.get("width_rel_to"), "ABSOLUTE")}" '
        f'height="{_as_int(size.get("height"))}" heightRelTo="{_safe_enum(size.get("height_rel_to"), "ABSOLUTE")}" '
        f'protect="{_bool_int(size.get("protect"))}"/>'
        f'<hp:pos treatAsChar="{_bool_int(position.get("treat_as_char"))}" '
        f'affectLSpacing="{_bool_int(position.get("affect_line_spacing"))}" '
        f'flowWithText="{_bool_int(position.get("flow_with_text"))}" '
        f'allowOverlap="{_bool_int(position.get("allow_overlap"))}" '
        f'holdAnchorAndSO="{_bool_int(position.get("hold_anchor_and_so"))}" '
        f'vertRelTo="{_safe_enum(position.get("vert_rel_to"), "PARA")}" '
        f'horzRelTo="{_safe_enum(position.get("horz_rel_to"), "PARA")}" '
        f'vertAlign="{_safe_enum(position.get("vert_align"), "TOP")}" '
        f'horzAlign="{_safe_enum(position.get("horz_align"), "LEFT")}" '
        f'vertOffset="{_unsigned_i32(position.get("vert_offset"))}" '
        f'horzOffset="{_unsigned_i32(position.get("horz_offset"))}"/>'
        f'{_margin_xml("outMargin", value.get("out_margin"))}'
    )


def _table_order_key(table: Any, fallback: int) -> int:
    if not isinstance(table, dict):
        return fallback
    if table.get("order_key") is not None:
        return _as_int(table.get("order_key"))
    indexes = []
    caption = table.get("caption")
    if isinstance(caption, dict):
        indexes.extend(_as_int(value) for value in caption.get("paragraph_indexes", []))
    for cell in table.get("cells", []):
        if isinstance(cell, dict):
            indexes.extend(_as_int(value) for value in cell.get("paragraph_indexes", []))
    return min(indexes) if indexes else fallback


def _paragraph_xml(
    section_ref: str,
    index: int,
    line_segments: list[dict[str, Any]],
    page_definitions: list[dict[str, Any]],
    text: str,
    paragraph_controls: list[dict[str, Any]],
    paragraph_style: dict[str, Any],
    summary: dict[str, Any],
    embedded_items: list[tuple[int, int, str]] | None = None,
    compatibility_profile: str = "",
) -> str:
    para_pr_ref = _normalize_ref(paragraph_style.get("para_shape_id"), summary.get("para_pr_count"))
    style_ref = _normalize_ref(paragraph_style.get("style_id"), summary.get("style_count"))
    paragraph_id = _as_int(paragraph_style.get("paragraph_id"))
    sec_pr = "".join(_sec_pr_xml(page_definition) for page_definition in page_definitions)
    runs = _text_runs_for_paragraph(text, paragraph_style, summary)
    text_controls_by_run = _text_controls_by_run(runs, paragraph_controls)
    structural_events_by_run = _structural_events_by_run(
        runs,
        paragraph_controls,
        sec_pr,
        embedded_items or [],
        compatibility_profile,
    )
    run_parts = []
    for run_index, run in enumerate(runs):
        content = _run_content_xml(
            run,
            text_controls_by_run[run_index],
            structural_events_by_run[run_index],
            is_last_run=run_index == len(runs) - 1,
        )
        run_parts.append(f'<hp:run charPrIDRef="{run["char_pr_ref"]}">{content}</hp:run>')
    run_xml = "".join(run_parts)
    lines = "".join(_line_segment_xml(segment) for segment in line_segments)
    line_array = f"<hp:linesegarray>{lines}</hp:linesegarray>" if lines else ""
    return (
        f'<hp:p id="{paragraph_id}" paraPrIDRef="{para_pr_ref}" styleIDRef="{style_ref}" '
        f'pageBreak="{_bool_int(paragraph_style.get("page_break"))}" '
        f'columnBreak="{_bool_int(paragraph_style.get("column_break"))}" '
        f'merged="{_bool_int(paragraph_style.get("merged"))}">'
        f"{run_xml}{line_array}</hp:p>"
    )


def _line_segment_xml(value: dict[str, Any]) -> str:
    return (
        f'<hp:lineseg textpos="{_as_int(value.get("textpos"))}" '
        f'vertpos="{_signed_int(value.get("vertpos"))}" '
        f'vertsize="{_signed_int(value.get("vertsize"))}" '
        f'textheight="{_signed_int(value.get("textheight"))}" '
        f'baseline="{_signed_int(value.get("baseline"))}" '
        f'spacing="{_signed_int(value.get("spacing"))}" '
        f'horzpos="{_signed_int(value.get("horzpos"))}" '
        f'horzsize="{_signed_int(value.get("horzsize"))}" '
        f'flags="{_as_int(value.get("flags"))}"/>'
    )


def _structural_events_by_run(
    runs: list[dict[str, Any]],
    paragraph_controls: list[dict[str, Any]],
    sec_pr: str,
    embedded_items: list[tuple[int, int, str]],
    compatibility_profile: str = "",
) -> list[list[tuple[int, int, str, bool]]]:
    parts: list[list[tuple[int, int, str, bool]]] = [[] for _ in runs]
    pending_embedded = [value for _order, _index, value in embedded_items]
    embedded_index = 0
    sec_pr_written = False
    event_order = 0
    controls = sorted(
        (item for item in paragraph_controls if isinstance(item, dict)),
        key=lambda item: _as_int(item.get("source_start")),
    )
    for control in controls:
        control_id = str(control.get("control_id", ""))
        child_name = str(control.get("render_layout_child", ""))
        xml = ""
        requires_text_tail = False
        if control_id == "dces" and sec_pr and not sec_pr_written:
            xml = sec_pr
            sec_pr_written = True
        elif control_id == "spct" and isinstance(control.get("compose"), dict):
            xml = _compose_control_xml(control["compose"])
        elif (
            control_id == "  nf"
            and isinstance(control.get("footnote"), dict)
            and embedded_index < len(pending_embedded)
        ):
            xml = _footnote_control_xml(
                control["footnote"],
                pending_embedded[embedded_index],
            )
            embedded_index += 1
        elif child_name:
            xml = (
                f"<hp:ctrl>{_layout_control_child_xml(child_name, compatibility_profile, control)}</hp:ctrl>"
            )
        elif (
            control.get("control_class") == "extended"
            and embedded_index < len(pending_embedded)
        ):
            xml = pending_embedded[embedded_index]
            embedded_index += 1
            requires_text_tail = bool(control.get("requires_text_tail"))
        if xml:
            requested_run_index = control.get("source_run_index")
            run_index = (
                _as_int(requested_run_index)
                if requested_run_index is not None
                and 0 <= _as_int(requested_run_index) < len(runs)
                else _run_index_for_source(runs, control.get("source_start"))
            )
            run = runs[run_index]
            visible_position = _signed_int(
                control.get("visible_start"),
                _as_int(run.get("visible_start")),
            )
            parts[run_index].append(
                (visible_position, event_order, xml, requires_text_tail)
            )
            event_order += 1

    if sec_pr and not sec_pr_written:
        parts[0].insert(
            0,
            (_as_int(runs[0].get("visible_start")), -1, sec_pr, False),
        )
    for xml in pending_embedded[embedded_index:]:
        parts[-1].append(
            (_as_int(runs[-1].get("visible_end")), event_order, xml, True)
        )
        event_order += 1
    return [sorted(values) for values in parts]


def _run_index_for_source(runs: list[dict[str, Any]], source_position: Any) -> int:
    position = _as_int(source_position)
    selected = 0
    for index, run in enumerate(runs):
        if _as_int(run.get("source_start")) > position:
            break
        selected = index
    return selected


def _sec_pr_xml(page_definition: dict[str, Any]) -> str:
    semantics = (
        page_definition.get("section_semantics", {})
        if isinstance(page_definition.get("section_semantics"), dict)
        else {}
    )
    page = semantics.get("page", page_definition) if isinstance(semantics.get("page", page_definition), dict) else page_definition
    margin = page.get("margin", {}) if isinstance(page.get("margin"), dict) else {}
    grid = semantics.get("grid", {}) if isinstance(semantics.get("grid"), dict) else {}
    start = semantics.get("start_num", {}) if isinstance(semantics.get("start_num"), dict) else {}
    visibility = semantics.get("visibility", {}) if isinstance(semantics.get("visibility"), dict) else {}
    line_number = semantics.get("line_number", {}) if isinstance(semantics.get("line_number"), dict) else {}
    footnote = semantics.get("footnote", {}) if isinstance(semantics.get("footnote"), dict) else {}
    endnote = semantics.get("endnote", {}) if isinstance(semantics.get("endnote"), dict) else {}
    page_borders = semantics.get("page_borders", []) if isinstance(semantics.get("page_borders"), list) else []
    return (
        f'<hp:secPr id="" textDirection="{_safe_enum(semantics.get("text_direction"), "HORIZONTAL")}" '
        f'spaceColumns="{_signed_int(semantics.get("space_columns"), 1135)}" '
        f'tabStop="{_signed_int(semantics.get("tab_stop"), 8000)}" '
        f'tabStopVal="{_signed_int(semantics.get("tab_stop_value"), 4000)}" '
        f'tabStopUnit="{_safe_enum(semantics.get("tab_stop_unit"), "HWPUNIT")}" '
        f'outlineShapeIDRef="{_as_int(semantics.get("outline_shape_id_ref"))}" '
        f'memoShapeIDRef="{_as_int(semantics.get("memo_shape_id_ref"))}" '
        f'textVerticalWidthHead="{_as_int(semantics.get("text_vertical_width_head"))}" '
        f'masterPageCnt="{_as_int(semantics.get("master_page_count"))}">'
        f'<hp:grid lineGrid="{_signed_int(grid.get("line_grid"))}" '
        f'charGrid="{_signed_int(grid.get("char_grid"))}" '
        f'wonggojiFormat="{_bool_int(grid.get("wonggoji_format"))}"/>'
        f'<hp:startNum pageStartsOn="{_safe_enum(start.get("page_starts_on"), "BOTH")}" '
        f'page="{_as_int(start.get("page"))}" pic="{_as_int(start.get("pic"))}" '
        f'tbl="{_as_int(start.get("tbl"))}" equation="{_as_int(start.get("equation"))}"/>'
        f'<hp:visibility hideFirstHeader="{_bool_int(visibility.get("hide_first_header"))}" '
        f'hideFirstFooter="{_bool_int(visibility.get("hide_first_footer"))}" '
        f'hideFirstMasterPage="{_bool_int(visibility.get("hide_first_master_page"))}" '
        f'border="{_safe_enum(visibility.get("border"), "SHOW_ALL")}" '
        f'fill="{_safe_enum(visibility.get("fill"), "SHOW_ALL")}" '
        f'hideFirstPageNum="{_bool_int(visibility.get("hide_first_page_num"))}" '
        f'hideFirstEmptyLine="{_bool_int(visibility.get("hide_first_empty_line"))}" '
        f'showLineNumber="{_bool_int(visibility.get("show_line_number"))}"/>'
        f'<hp:lineNumberShape restartType="{_as_int(line_number.get("restart_type"))}" '
        f'countBy="{_as_int(line_number.get("count_by"))}" '
        f'distance="{_as_int(line_number.get("distance"))}" '
        f'startNumber="{_as_int(line_number.get("start_number"))}"/>'
        f'<hp:pagePr landscape="{_safe_enum(page.get("landscape"), "WIDELY")}" '
        f'width="{_signed_int(page.get("width"), 59528)}" '
        f'height="{_signed_int(page.get("height"), 84188)}" '
        f'gutterType="{_safe_enum(page.get("gutter_type"), "LEFT_ONLY")}">'
        f'<hp:margin header="{_signed_int(margin.get("header"), 5668)}" '
        f'footer="{_signed_int(margin.get("footer"), 5668)}" '
        f'gutter="{_signed_int(margin.get("gutter"))}" '
        f'left="{_signed_int(margin.get("left"), 8504)}" '
        f'right="{_signed_int(margin.get("right"), 8504)}" '
        f'top="{_signed_int(margin.get("top"), 8504)}" '
        f'bottom="{_signed_int(margin.get("bottom"), 8504)}"/>'
        '</hp:pagePr>'
        f'{_note_pr_xml("footNotePr", footnote, "EACH_COLUMN")}'
        f'{_note_pr_xml("endNotePr", endnote, "END_OF_DOCUMENT")}'
        f'{"".join(_page_border_fill_xml(value) for value in page_borders if isinstance(value, dict))}'
        '</hp:secPr>'
    )


def _note_pr_xml(tag_name: str, value: dict[str, Any], default_place: str) -> str:
    auto = value.get("auto_num_format", {}) if isinstance(value.get("auto_num_format"), dict) else {}
    line = value.get("note_line", {}) if isinstance(value.get("note_line"), dict) else {}
    spacing = value.get("note_spacing", {}) if isinstance(value.get("note_spacing"), dict) else {}
    numbering = value.get("numbering", {}) if isinstance(value.get("numbering"), dict) else {}
    placement = value.get("placement", {}) if isinstance(value.get("placement"), dict) else {}
    return (
        f'<hp:{tag_name}>'
        f'<hp:autoNumFormat type="{_safe_enum(auto.get("type"), "DIGIT")}" '
        f'userChar="{_xml_escape(auto.get("user_char", ""))}" '
        f'prefixChar="{_xml_escape(auto.get("prefix_char", ""))}" '
        f'suffixChar="{_xml_escape(auto.get("suffix_char", ")"))}" '
        f'supscript="{_bool_int(auto.get("superscript"))}"/>'
        f'<hp:noteLine length="{_signed_int(line.get("length"), -1)}" '
        f'type="{_safe_enum(line.get("type"), "SOLID")}" '
        f'width="{_xml_escape(line.get("width", "0.12 mm"))}" '
        f'color="{_safe_color(line.get("color"), "#000000")}"/>'
        f'<hp:noteSpacing betweenNotes="{_as_int(spacing.get("between_notes"))}" '
        f'belowLine="{_as_int(spacing.get("below_line"))}" '
        f'aboveLine="{_as_int(spacing.get("above_line"))}"/>'
        f'<hp:numbering type="{_safe_enum(numbering.get("type"), "CONTINUOUS")}" '
        f'newNum="{_as_int(numbering.get("new_num"))}"/>'
        f'<hp:placement place="{_safe_enum(placement.get("place"), default_place)}" '
        f'beneathText="{_bool_int(placement.get("beneath_text"))}"/>'
        f'</hp:{tag_name}>'
    )


def _page_border_fill_xml(value: dict[str, Any]) -> str:
    offset = value.get("offset", {}) if isinstance(value.get("offset"), dict) else {}
    return (
        f'<hp:pageBorderFill type="{_safe_enum(value.get("type"), "BOTH")}" '
        f'borderFillIDRef="{_as_int(value.get("border_fill_id_ref"))}" '
        f'textBorder="{_safe_enum(value.get("text_border"), "PAPER")}" '
        f'headerInside="{_bool_int(value.get("header_inside"))}" '
        f'footerInside="{_bool_int(value.get("footer_inside"))}" '
        f'fillArea="{_safe_enum(value.get("fill_area"), "PAPER")}">'
        f'<hp:offset left="{_as_int(offset.get("left"))}" '
        f'right="{_as_int(offset.get("right"))}" '
        f'top="{_as_int(offset.get("top"))}" '
        f'bottom="{_as_int(offset.get("bottom"))}"/>'
        '</hp:pageBorderFill>'
    )


def _render_table(context: dict[str, Any], table_index: int) -> str:
    tables = context.get("tables", [])
    if not isinstance(tables, list) or not 0 <= table_index < len(tables):
        return ""
    rendering = context.get("rendering_tables")
    if not isinstance(rendering, set):
        rendering = set()
        context["rendering_tables"] = rendering
    if table_index in rendering:
        return ""
    table = tables[table_index]
    if not isinstance(table, dict):
        return ""
    rendering.add(table_index)
    try:
        return _table_xml(context, table_index, table)
    finally:
        rendering.remove(table_index)


def _table_xml(context: dict[str, Any], table_index: int, table: dict[str, Any]) -> str:
    row_cell_counts = [
        max(0, _as_int(value))
        for value in table.get("row_cell_counts", [])
    ] if isinstance(table.get("row_cell_counts"), list) else []
    row_count = max(1, _as_int(table.get("row_count")))
    column_count = max(1, _as_int(table.get("column_count")))
    while len(row_cell_counts) < row_count:
        row_cell_counts.append(column_count)
    row_cell_counts = row_cell_counts[:row_count]
    cells = [value for value in table.get("cells", []) if isinstance(value, dict)]
    extra_sub_lists = _distribute_sub_lists(_as_int(table.get("extra_sub_list_count")), len(cells))
    cell_index = 0
    rows = []
    for row_cells in row_cell_counts:
        row_parts = []
        for _ in range(row_cells):
            cell = cells[cell_index] if cell_index < len(cells) else _default_table_cell(cell_index)
            row_parts.append(
                _table_cell_xml(
                    context,
                    cell,
                    extra_sub_lists[cell_index] if cell_index < len(extra_sub_lists) else 0,
                )
            )
            cell_index += 1
        rows.append(f'<hp:tr>{"".join(row_parts)}</hp:tr>')

    object_value = table.get("object", {}) if isinstance(table.get("object"), dict) else {}
    size = object_value.get("size", {}) if isinstance(object_value.get("size"), dict) else {}
    position = object_value.get("position", {}) if isinstance(object_value.get("position"), dict) else {}
    render_position = dict(position)
    portable_profile = context.get("compatibility_profile") == "portable"
    if portable_profile and bool(render_position.get("treat_as_char")):
        render_position["flow_with_text"] = False
        render_position["horz_rel_to"] = "COLUMN"
    caption = table.get("caption") if isinstance(table.get("caption"), dict) else None
    table_id = _as_int(object_value.get("id"))
    if not table_id:
        table_id = table_index + 1
    common = (
        f'<hp:sz width="{_as_int(size.get("width"))}" '
        f'widthRelTo="{_safe_enum(size.get("width_rel_to"), "ABSOLUTE")}" '
        f'height="{_as_int(size.get("height"))}" '
        f'heightRelTo="{_safe_enum(size.get("height_rel_to"), "ABSOLUTE")}" '
        f'protect="{_bool_int(size.get("protect"))}"/>'
        f'<hp:pos treatAsChar="{_bool_int(render_position.get("treat_as_char"))}" '
        f'affectLSpacing="{_bool_int(render_position.get("affect_line_spacing"))}" '
        f'flowWithText="{_bool_int(render_position.get("flow_with_text"))}" '
        f'allowOverlap="{_bool_int(render_position.get("allow_overlap"))}" '
        f'holdAnchorAndSO="{_bool_int(render_position.get("hold_anchor_and_so"))}" '
        f'vertRelTo="{_safe_enum(render_position.get("vert_rel_to"), "PARA")}" '
        f'horzRelTo="{_safe_enum(render_position.get("horz_rel_to"), "PARA")}" '
        f'vertAlign="{_safe_enum(render_position.get("vert_align"), "TOP")}" '
        f'horzAlign="{_safe_enum(render_position.get("horz_align"), "LEFT")}" '
        f'vertOffset="{_signed_int(render_position.get("vert_offset"))}" '
        f'horzOffset="{_signed_int(render_position.get("horz_offset"))}"/>'
        f'{_margin_xml("outMargin", object_value.get("out_margin"))}'
        f'{_caption_xml(context, caption) if caption is not None else ""}'
        f'{_margin_xml("inMargin", table.get("in_margin"))}'
    )
    return (
        f'<hp:tbl id="{table_id}" zOrder="{_signed_int(object_value.get("z_order"))}" '
        f'numberingType="{_safe_enum(object_value.get("numbering_type"), "TABLE")}" '
        f'textWrap="{_safe_enum(object_value.get("text_wrap"), "TOP_AND_BOTTOM")}" '
        f'textFlow="{_safe_enum(object_value.get("text_flow"), "BOTH_SIDES")}" '
        f'lock="{_bool_int(object_value.get("lock"))}" '
        f'dropcapstyle="{_safe_case_token(object_value.get("dropcap_style"), "None")}" '
        f'pageBreak="{_safe_enum(table.get("page_break"), "NONE")}" '
        f'repeatHeader="{_bool_int(_table_repeat_header(table, cells, portable_profile))}" '
        f'rowCnt="{row_count}" colCnt="{column_count}" '
        f'cellSpacing="{_as_int(table.get("cell_spacing"))}" '
        f'borderFillIDRef="{_as_int(table.get("border_fill_id_ref"))}" '
        f'noAdjust="{_bool_int(table.get("no_adjust"))}">'
        f'{common}{_cell_zone_list_xml(table.get("zones"))}{"".join(rows)}</hp:tbl>'
    )


def _table_repeat_header(
    table: dict[str, Any],
    cells: list[dict[str, Any]],
    portable_profile: bool,
) -> bool:
    enabled = bool(table.get("repeat_header"))
    if not portable_profile:
        return enabled
    return enabled and any(bool(cell.get("header")) for cell in cells)


def _table_cell_xml(context: dict[str, Any], cell: dict[str, Any], extra_sub_list_count: int) -> str:
    primary_sub_list = _sub_list_xml(
        context,
        cell.get("sub_list"),
        cell.get("render_paragraph_indexes", cell.get("paragraph_indexes")),
    )
    extra_sub_lists = "".join(
        _sub_list_xml(context, {}, [])
        for _ in range(max(0, extra_sub_list_count))
    )
    return (
        f'<hp:tc name="" header="{_bool_int(cell.get("header"))}" '
        f'hasMargin="{_bool_int(cell.get("has_margin"))}" '
        f'protect="{_bool_int(cell.get("protect"))}" '
        f'editable="{_bool_int(cell.get("editable"))}" '
        f'dirty="{_bool_int(cell.get("dirty"))}" '
        f'borderFillIDRef="{_as_int(cell.get("border_fill_id_ref"))}">'
        f'{primary_sub_list}{extra_sub_lists}'
        f'<hp:cellAddr colAddr="{_as_int(cell.get("column"))}" rowAddr="{_as_int(cell.get("row"))}"/>'
        f'<hp:cellSpan colSpan="{max(1, _as_int(cell.get("column_span")))}" '
        f'rowSpan="{max(1, _as_int(cell.get("row_span")))}"/>'
        f'<hp:cellSz width="{_signed_int(cell.get("width"))}" height="{_signed_int(cell.get("height"))}"/>'
        f'{_margin_xml("cellMargin", cell.get("margin"))}'
        '</hp:tc>'
    )


def _caption_xml(context: dict[str, Any], caption: dict[str, Any]) -> str:
    paragraph_indexes = caption.get(
        "render_paragraph_indexes",
        caption.get("paragraph_indexes"),
    )
    return (
        f'<hp:caption side="{_safe_enum(caption.get("side"), "TOP")}" '
        f'fullSz="{_bool_int(caption.get("full_size"))}" '
        f'width="{_signed_int(caption.get("width"))}" '
        f'gap="{_signed_int(caption.get("gap"))}" '
        f'lastWidth="{_signed_int(caption.get("last_width"))}">'
        f'{_sub_list_xml(context, caption.get("sub_list"), paragraph_indexes)}'
        '</hp:caption>'
    )


def _sub_list_xml(context: dict[str, Any], value: Any, paragraph_indexes: Any) -> str:
    sub_list = value if isinstance(value, dict) else {}
    indexes = paragraph_indexes if isinstance(paragraph_indexes, list) else []
    paragraphs = "".join(
        _render_paragraph(context, index)
        for index in (_as_int(raw_index) for raw_index in indexes)
        if 0 <= index < len(context.get("paragraph_styles", []))
    )
    return _sub_list_container_xml(sub_list, paragraphs)


def _sub_list_container_xml(sub_list: dict[str, Any], paragraphs: str) -> str:
    return (
        f'<hp:subList id="" textDirection="{_safe_enum(sub_list.get("text_direction"), "HORIZONTAL")}" '
        f'lineWrap="{_safe_enum(sub_list.get("line_wrap"), "BREAK")}" '
        f'vertAlign="{_safe_enum(sub_list.get("vertical_align"), "TOP")}" '
        'linkListIDRef="0" linkListNextIDRef="0" '
        f'textWidth="{_signed_int(sub_list.get("text_width"))}" '
        f'textHeight="{_signed_int(sub_list.get("text_height"))}" '
        f'hasTextRef="{_bool_int(sub_list.get("has_text_ref"))}" '
        f'hasNumRef="{_bool_int(sub_list.get("has_num_ref"))}">'
        f'{paragraphs}</hp:subList>'
    )


def _cell_zone_list_xml(value: Any) -> str:
    zones = value if isinstance(value, list) else []
    parts = [
        (
            f'<hp:cellzone startRowAddr="{_as_int(zone.get("start_row"))}" '
            f'startColAddr="{_as_int(zone.get("start_column"))}" '
            f'endRowAddr="{_as_int(zone.get("end_row"))}" '
            f'endColAddr="{_as_int(zone.get("end_column"))}" '
            f'borderFillIDRef="{_as_int(zone.get("border_fill_id_ref"))}"/>'
        )
        for zone in zones
        if isinstance(zone, dict)
    ]
    return f'<hp:cellzoneList>{"".join(parts)}</hp:cellzoneList>' if parts else ""


def _margin_xml(tag_name: str, value: Any) -> str:
    margin = value if isinstance(value, dict) else {}
    return (
        f'<hp:{tag_name} left="{_signed_int(margin.get("left"))}" '
        f'right="{_signed_int(margin.get("right"))}" '
        f'top="{_signed_int(margin.get("top"))}" '
        f'bottom="{_signed_int(margin.get("bottom"))}"/>'
    )


def _default_table_cell(cell_index: int) -> dict[str, Any]:
    return {
        "cell_index": cell_index,
        "column": 0,
        "row": 0,
        "column_span": 1,
        "row_span": 1,
        "width": 0,
        "height": 0,
        "margin": {},
        "border_fill_id_ref": 0,
        "sub_list": {},
        "paragraph_indexes": [],
    }


def _layout_controls_xml(
    layout_control_child_counts: Any,
    compatibility_profile: str = "",
) -> str:
    if not isinstance(layout_control_child_counts, dict):
        return ""
    parts = []
    for child_name, count in sorted(layout_control_child_counts.items()):
        if not _is_safe_xml_name(child_name):
            continue
        for _ in range(_as_int(count)):
            parts.append(
                f"<hp:ctrl>{_layout_control_child_xml(child_name, compatibility_profile)}</hp:ctrl>"
            )
    return "".join(parts)


_ANCHORED_LAYOUT_CONTROL_CHILDREN = {
    "dloc": "colPr",
    "onwn": "newNum",
    "dhgp": "pageHiding",
    "pngp": "pageNum",
    "daeh": "header",
    "toof": "footer",
    "  nf": "footNote",
    "onta": "autoNum",
}


def _select_anchored_layout_controls(paragraph_controls: Any, layout_control_child_counts: Any) -> list[list[dict[str, Any]]]:
    budgets = (
        {str(name): _as_int(count) for name, count in layout_control_child_counts.items()}
        if isinstance(layout_control_child_counts, dict)
        else {}
    )
    selected = []
    for controls in paragraph_controls if isinstance(paragraph_controls, list) else []:
        paragraph = []
        for control in controls if isinstance(controls, list) else []:
            if not isinstance(control, dict):
                continue
            value = dict(control)
            child_name = _ANCHORED_LAYOUT_CONTROL_CHILDREN.get(str(value.get("control_id", "")))
            if child_name == "autoNum" and not isinstance(value.get("auto_number"), dict):
                child_name = None
            if child_name and budgets.get(child_name, 0) > 0:
                value["render_layout_child"] = child_name
                budgets[child_name] -= 1
            paragraph.append(value)
        selected.append(paragraph)
    return selected


def _anchored_layout_controls_xml(
    paragraph_controls: Any,
    compatibility_profile: str = "",
) -> str:
    if not isinstance(paragraph_controls, list):
        return ""
    parts = []
    for control in sorted(
        (item for item in paragraph_controls if isinstance(item, dict)),
        key=lambda item: _as_int(item.get("source_start")),
    ):
        child_name = str(control.get("render_layout_child", ""))
        if child_name:
            parts.append(
                f"<hp:ctrl>{_layout_control_child_xml(child_name, compatibility_profile, control)}</hp:ctrl>"
            )
    return "".join(parts)


def _remaining_layout_controls_xml(
    layout_control_child_counts: Any,
    paragraph_controls: Any,
    compatibility_profile: str = "",
) -> str:
    counts = (
        {str(name): _as_int(count) for name, count in layout_control_child_counts.items()}
        if isinstance(layout_control_child_counts, dict)
        else {}
    )
    if isinstance(paragraph_controls, list):
        for controls in paragraph_controls:
            if not isinstance(controls, list):
                continue
            for control in controls:
                if not isinstance(control, dict):
                    continue
                child_name = str(control.get("render_layout_child", ""))
                if child_name and counts.get(child_name, 0) > 0:
                    counts[child_name] -= 1
    return _layout_controls_xml(counts, compatibility_profile)


def _layout_control_child_xml(
    child_name: str,
    compatibility_profile: str = "",
    control: dict[str, Any] | None = None,
) -> str:
    preserved_xml = str(control.get("preserved_xml", "")) if isinstance(control, dict) else ""
    if preserved_xml and child_name in {"header", "footer"}:
        try:
            root = ElementTree.fromstring(preserved_xml)
        except ElementTree.ParseError:
            root = None
        if root is not None and root.tag.rsplit("}", 1)[-1] == child_name:
            return preserved_xml
    if child_name == "colPr":
        column = control.get("column_definition", {}) if isinstance(control, dict) else {}
        if isinstance(column, dict) and column:
            return (
                f'<hp:colPr id="{_xml_escape(column.get("id"))}" '
                f'type="{_safe_enum(column.get("type"), "NEWSPAPER")}" '
                f'layout="{_safe_enum(column.get("layout"), "LEFT")}" '
                f'colCount="{max(1, _as_int(column.get("column_count")))}" '
                f'sameSz="{_bool_int(column.get("same_size"))}" '
                f'sameGap="{_signed_int(column.get("same_gap"))}"></hp:colPr>'
            )
        if compatibility_profile == "hancom":
            return (
                '<hp:colPr id="" type="NEWSPAPER" layout="LEFT" '
                'colCount="1" sameSz="1" sameGap="0"></hp:colPr>'
            )
        return (
            '<hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0">'
            '<hp:colLine type="NONE" width="0.1 mm" color="#000000"/>'
            '</hp:colPr>'
        )
    if child_name == "pageNum":
        page_number = control.get("page_number", {}) if isinstance(control, dict) else {}
        if isinstance(page_number, dict) and page_number:
            return (
                f'<hp:pageNum pos="{_safe_enum(page_number.get("position"), "BOTTOM_CENTER")}" '
                f'formatType="{_safe_enum(page_number.get("format_type"), "DIGIT")}" '
                f'sideChar="{_xml_escape(page_number.get("side_character") or "-")}"/>'
            )
        return '<hp:pageNum pos="BOTTOM_CENTER" formatType="DIGIT" sideChar="-"/>'
    if child_name == "pageHiding":
        page_hiding = control.get("page_hiding", {}) if isinstance(control, dict) else {}
        attributes = (
            page_hiding.get("attributes", {})
            if isinstance(page_hiding, dict)
            else {}
        )
        if isinstance(attributes, dict) and attributes:
            return (
                '<hp:pageHiding '
                f'hideHeader="{1 if _as_int(attributes.get("hideHeader")) else 0}" '
                f'hideFooter="{1 if _as_int(attributes.get("hideFooter")) else 0}" '
                f'hideMasterPage="{1 if _as_int(attributes.get("hideMasterPage")) else 0}" '
                f'hideBorder="{1 if _as_int(attributes.get("hideBorder")) else 0}" '
                f'hideFill="{1 if _as_int(attributes.get("hideFill")) else 0}" '
                f'hidePageNum="{1 if _as_int(attributes.get("hidePageNum")) else 0}"/>'
            )
        return (
            '<hp:pageHiding hideHeader="0" hideFooter="0" hideMasterPage="0" '
            'hideBorder="0" hideFill="0" hidePageNum="1"/>'
        )
    if child_name == "newNum":
        new_number = control.get("new_number", {}) if isinstance(control, dict) else {}
        if isinstance(new_number, dict) and new_number:
            return (
                f'<hp:newNum num="{max(1, _as_int(new_number.get("number")))}" '
                f'numType="{_safe_enum(new_number.get("number_type"), "PAGE")}"/>'
            )
        return '<hp:newNum num="1" numType="PAGE"/>'
    if child_name == "autoNum":
        auto_number = control.get("auto_number", {}) if isinstance(control, dict) else {}
        if isinstance(auto_number, dict) and auto_number:
            return (
                f'<hp:autoNum num="{_as_int(auto_number.get("number"))}" '
                f'numType="{_safe_enum(auto_number.get("number_type"), "FOOTNOTE")}">'
                '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" '
                f'suffixChar="{_xml_escape(chr(_as_int(auto_number.get("suffix_char"))))}" '
                'supscript="0"/></hp:autoNum>'
            )
    return f"<hp:{child_name}/>"


def _footnote_control_xml(value: dict[str, Any], sub_list_xml: str) -> str:
    return (
        '<hp:ctrl>'
        f'<hp:footNote number="{_as_int(value.get("number"))}" '
        f'prefixChar="{_as_int(value.get("prefix_char"))}" '
        f'suffixChar="{_as_int(value.get("suffix_char"))}" '
        f'instId="{_as_int(value.get("instance_id"))}">'
        f'{sub_list_xml}</hp:footNote></hp:ctrl>'
    )


def _header_xml(model: dict[str, Any]) -> str:
    summary = model.get("summary", {})
    style_semantics = model.get("style_semantics", {})
    list_semantics = model.get("list_semantics", {})
    border_fill_semantics = model.get("border_fill_semantics", {})
    section_count = _as_int(summary.get("section_count"))
    bin_data_count = _as_int(summary.get("bin_data_count"))
    bullet_count = _as_int(summary.get("bullet_count"))
    numbering_count = _as_int(summary.get("numbering_count"))
    char_pr_count = max(1, _as_int(summary.get("char_pr_count")))
    para_pr_count = max(1, _as_int(summary.get("para_pr_count")))
    style_count = max(1, _as_int(summary.get("style_count")))
    border_fill_count = max(1, _as_int(summary.get("border_fill_count")))
    tab_pr_count = max(1, _as_int(summary.get("tab_pr_count")))
    binary_items = [item for item in model.get("_binary_payloads", []) if isinstance(item, dict)]
    bin_list = "".join(
        f'<hh:binData id="{_xml_escape(item.get("item_id", index + 1))}" '
        f'binaryItemIDRef="{_xml_escape(str(item.get("entry_name", "")).removeprefix("BinData/"))}" '
        f'format="{_xml_escape(item.get("format", "bin"))}"/>'
        for index, item in enumerate(binary_items)
    )
    bullets = _bullets_xml(list_semantics, bullet_count)
    numberings = _numberings_xml(list_semantics, numbering_count)
    fontfaces = _fontfaces_xml(style_semantics)
    char_properties = _char_properties_xml(style_semantics, char_pr_count)
    para_properties = _para_properties_xml(style_semantics, para_pr_count)
    border_fills = _border_fills_xml(border_fill_semantics, border_fill_count)
    tab_properties = _tab_properties_xml(list_semantics, tab_pr_count)
    styles = "".join(
        f'<hh:style id="{index}" type="PARA" name="Body{index}" '
        f'paraPrIDRef="{_normalize_ref(index, para_pr_count)}" charPrIDRef="{_normalize_ref(index, char_pr_count)}"/>'
        for index in range(style_count)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
        'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
        'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
        'xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" '
        f'version="1.4" secCnt="{section_count}">'
        '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>'
        '<hh:refList>'
        f'{fontfaces}'
        f'<hh:borderFills itemCnt="{border_fill_count}">{border_fills}</hh:borderFills>'
        f'<hh:charProperties itemCnt="{char_pr_count}">{char_properties}</hh:charProperties>'
        f'<hh:tabProperties itemCnt="{tab_pr_count}">{tab_properties}</hh:tabProperties>'
        f'<hh:numberings itemCnt="{numbering_count}">{numberings}</hh:numberings>'
        f'<hh:bullets itemCnt="{bullet_count}">{bullets}</hh:bullets>'
        f'<hh:paraProperties itemCnt="{para_pr_count}">{para_properties}</hh:paraProperties>'
        f'<hh:styles itemCnt="{style_count}">{styles}</hh:styles>'
        f'<hh:binDataList itemCnt="{bin_data_count}">{bin_list}</hh:binDataList>'
        '</hh:refList>'
        '<hh:compatibleDocument targetProgram="HWP201X"><hh:layoutCompatibility/></hh:compatibleDocument>'
        '<hh:docOption><hh:linkinfo path="" pageInherit="0" footnoteInherit="0"/></hh:docOption>'
        '<hh:trackchageConfig flags="56"/>'
        '</hh:head>'
    )


def _tab_properties_xml(list_semantics: Any, count: int) -> str:
    raw = list_semantics.get("tab_definitions", []) if isinstance(list_semantics, dict) else []
    by_id = {_as_int(item.get("id")): item for item in raw if isinstance(item, dict)}
    return "".join(_tab_pr_xml(by_id.get(index, {}), index) for index in range(count))


def _tab_pr_xml(value: dict[str, Any], definition_id: int) -> str:
    items = value.get("items", []) if isinstance(value.get("items"), list) else []
    switches = "".join(_tab_item_switch_xml(item) for item in items if isinstance(item, dict))
    return (
        f'<hh:tabPr id="{definition_id}" '
        f'autoTabLeft="{_bool_int(value.get("auto_tab_left"))}" '
        f'autoTabRight="{_bool_int(value.get("auto_tab_right"))}">'
        f'{switches}</hh:tabPr>'
    )


def _tab_item_switch_xml(value: dict[str, Any]) -> str:
    position = _signed_int(value.get("position"))
    tab_type = _safe_enum(value.get("type"), "LEFT")
    leader = _safe_enum(value.get("leader"), "NONE")
    return (
        '<hp:switch>'
        '<hp:case hp:required-namespace="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar">'
        f'<hh:tabItem pos="{position // 2}" type="{tab_type}" leader="{leader}" unit="HWPUNIT"/>'
        '</hp:case><hp:default>'
        f'<hh:tabItem pos="{position}" type="{tab_type}" leader="{leader}"/>'
        '</hp:default></hp:switch>'
    )


def _numberings_xml(list_semantics: Any, count: int) -> str:
    raw = list_semantics.get("numberings", []) if isinstance(list_semantics, dict) else []
    by_id = {_as_int(item.get("id")): item for item in raw if isinstance(item, dict)}
    return "".join(_numbering_xml(by_id.get(index + 1, {}), index + 1) for index in range(count))


def _numbering_xml(value: dict[str, Any], numbering_id: int) -> str:
    levels = value.get("levels", []) if isinstance(value.get("levels"), list) else []
    if not levels:
        levels = [{"level": level, "start": 1, "format": f"^{level}."} for level in range(1, 8)]
    heads = "".join(
        _paragraph_head_xml(item, include_start=True)
        for item in levels
        if isinstance(item, dict)
    )
    return (
        f'<hh:numbering id="{numbering_id}" start="{_as_int(value.get("start"))}">'
        f'{heads}</hh:numbering>'
    )


def _bullets_xml(list_semantics: Any, count: int) -> str:
    raw = list_semantics.get("bullets", []) if isinstance(list_semantics, dict) else []
    by_id = {_as_int(item.get("id")): item for item in raw if isinstance(item, dict)}
    return "".join(_bullet_xml(by_id.get(index + 1, {}), index + 1) for index in range(count))


def _bullet_xml(value: dict[str, Any], bullet_id: int) -> str:
    head = value.get("para_head", {}) if isinstance(value.get("para_head"), dict) else {}
    return (
        f'<hh:bullet id="{bullet_id}" char="{_xml_escape(value.get("char", "\u2022"))}" '
        f'useImage="{_bool_int(value.get("use_image"))}">'
        f'{_paragraph_head_xml(head, include_start=False)}</hh:bullet>'
    )


def _paragraph_head_xml(value: dict[str, Any], *, include_start: bool) -> str:
    start_attr = f' start="{_as_int(value.get("start"))}"' if include_start else ""
    return (
        f'<hh:paraHead{start_attr} level="{_as_int(value.get("level"))}" '
        f'align="{_safe_enum(value.get("align"), "LEFT")}" '
        f'useInstWidth="{_bool_int(value.get("use_instance_width"))}" '
        f'autoIndent="{_bool_int(value.get("auto_indent"))}" '
        f'widthAdjust="{_signed_int(value.get("width_adjust"))}" '
        f'textOffsetType="{_safe_enum(value.get("text_offset_type"), "PERCENT")}" '
        f'textOffset="{_signed_int(value.get("text_offset"))}" '
        f'numFormat="{_safe_enum(value.get("num_format"), "DIGIT")}" '
        f'charPrIDRef="{_as_int(value.get("char_pr_id_ref", 0xFFFFFFFF))}" '
        f'checkable="{_bool_int(value.get("checkable"))}">'
        f'{_xml_escape(value.get("format", ""))}</hh:paraHead>'
    )


def _fontfaces_xml(style_semantics: Any) -> str:
    language_labels = {
        "hangul": "HANGUL",
        "latin": "LATIN",
        "hanja": "HANJA",
        "japanese": "JAPANESE",
        "other": "OTHER",
        "symbol": "SYMBOL",
        "user": "USER",
    }
    groups = style_semantics.get("font_faces", []) if isinstance(style_semantics, dict) else []
    by_language = {
        str(group.get("language", "")): group.get("fonts", [])
        for group in groups
        if isinstance(group, dict)
    }
    parts = []
    for language, label in language_labels.items():
        raw_fonts = by_language.get(language, [])
        fonts = [item for item in raw_fonts if isinstance(item, dict)]
        if not fonts:
            fonts = [{"id": 0, "face": "HancomBatang", "type": "TTF", "is_embedded": False}]
        font_xml = "".join(_font_xml(font) for font in fonts)
        parts.append(f'<hh:fontface lang="{label}" fontCnt="{len(fonts)}">{font_xml}</hh:fontface>')
    return f'<hh:fontfaces itemCnt="{len(parts)}">{"".join(parts)}</hh:fontfaces>'


def _font_xml(font: dict[str, Any]) -> str:
    alternate_face = str(font.get("alternate_face", ""))
    type_info = font.get("type_info", {}) if isinstance(font.get("type_info"), dict) else {}
    type_info_xml = ""
    if type_info:
        type_info_xml = (
            f'<hh:typeInfo familyType="{_safe_enum(type_info.get("family_type"), "FCAT_UNKNOWN")}" '
            f'weight="{_as_int(type_info.get("weight"))}" '
            f'proportion="{_as_int(type_info.get("proportion"))}" '
            f'contrast="{_as_int(type_info.get("contrast"))}" '
            f'strokeVariation="{_as_int(type_info.get("stroke_variation"))}" '
            f'armStyle="{_as_int(type_info.get("arm_style"))}" '
            f'letterform="{_as_int(type_info.get("letterform"))}" '
            f'midline="{_as_int(type_info.get("midline"))}" '
            f'xHeight="{_as_int(type_info.get("x_height"))}"/>'
        )
    alternate_xml = ""
    if alternate_face:
        alternate_xml = (
            f'<hh:substFont face="{_xml_escape(alternate_face)}" '
            f'type="{_safe_enum(font.get("alternate_type"), "UNKNOWN")}" '
            'isEmbedded="0" binaryItemIDRef=""/>'
        )
    return (
        f'<hh:font id="{_as_int(font.get("id"))}" '
        f'face="{_xml_escape(font.get("face") or "HancomBatang")}" '
        f'type="{_safe_enum(font.get("type"), "TTF")}" '
        f'isEmbedded="{_bool_int(font.get("is_embedded"))}">'
        f'{type_info_xml}{alternate_xml}</hh:font>'
    )


def _border_fills_xml(semantics: Any, count: int) -> str:
    raw = semantics.get("border_fills", []) if isinstance(semantics, dict) else []
    by_id = {_as_int(value.get("id")): value for value in raw if isinstance(value, dict)}
    return "".join(_border_fill_xml(by_id.get(index + 1, {}), index + 1) for index in range(count))


def _border_fill_xml(value: dict[str, Any], border_id: int) -> str:
    slash = value.get("slash", {}) if isinstance(value.get("slash"), dict) else {}
    back_slash = value.get("back_slash", {}) if isinstance(value.get("back_slash"), dict) else {}
    borders = value.get("borders", {}) if isinstance(value.get("borders"), dict) else {}
    diagonal = value.get("diagonal") if isinstance(value.get("diagonal"), dict) else None
    diagonal_xml = _border_line_xml("diagonal", diagonal) if diagonal is not None else ""
    return (
        f'<hh:borderFill id="{border_id}" threeD="{_bool_int(value.get("three_d"))}" '
        f'shadow="{_bool_int(value.get("shadow"))}" '
        f'centerLine="{_safe_enum(value.get("center_line"), "NONE")}" '
        f'breakCellSeparateLine="{_bool_int(value.get("break_cell_separate_line"))}">'
        f'{_slash_xml("slash", slash)}{_slash_xml("backSlash", back_slash)}'
        f'{_border_line_xml("leftBorder", borders.get("left"))}'
        f'{_border_line_xml("rightBorder", borders.get("right"))}'
        f'{_border_line_xml("topBorder", borders.get("top"))}'
        f'{_border_line_xml("bottomBorder", borders.get("bottom"))}'
        f'{diagonal_xml}{_fill_brush_xml(value.get("fill"))}</hh:borderFill>'
    )


def _slash_xml(tag_name: str, value: dict[str, Any]) -> str:
    return (
        f'<hh:{tag_name} type="{_safe_enum(value.get("type"), "NONE")}" '
        f'Crooked="{_bool_int(value.get("crooked"))}" '
        f'isCounter="{_bool_int(value.get("is_counter"))}"/>'
    )


def _border_line_xml(tag_name: str, value: Any) -> str:
    line = value if isinstance(value, dict) else {}
    return (
        f'<hh:{tag_name} type="{_safe_enum(line.get("type"), "NONE")}" '
        f'width="{_xml_escape(line.get("width") or "0.1 mm")}" '
        f'color="{_border_color(line.get("color"), "#000000")}"/>'
    )


def _fill_brush_xml(value: Any) -> str:
    fill = value if isinstance(value, dict) else {}
    fill_type = str(fill.get("type", "none"))
    if fill_type == "solid":
        hatch_style = (
            f' hatchStyle="{_safe_enum(fill.get("hatch_style"), "HORIZONTAL")}"'
            if fill.get("hatch_style")
            else ""
        )
        return (
            '<hc:fillBrush><hc:winBrush '
            f'faceColor="{_border_color(fill.get("face_color"), "none")}" '
            f'hatchColor="{_border_color(fill.get("hatch_color"), "#000000")}"'
            f'{hatch_style} alpha="{_as_int(fill.get("alpha"))}"/>'
            '</hc:fillBrush>'
        )
    if fill_type == "gradation":
        colors = list(fill.get("colors", [])) if isinstance(fill.get("colors"), list) else []
        positions = list(fill.get("positions", [])) if isinstance(fill.get("positions"), list) else []
        color_xml = "".join(
            f'<hc:color value="{_border_color(color, "#000000")}"'
            f'{f" pos=\"{_signed_int(positions[index])}\"" if index < len(positions) else ""}/>'
            for index, color in enumerate(colors)
        )
        return (
            '<hc:fillBrush><hc:gradation '
            f'type="{_safe_enum(fill.get("gradation_type"), "LINEAR")}" '
            f'angle="{_signed_int(fill.get("angle"))}" '
            f'centerX="{_signed_int(fill.get("center_x"))}" '
            f'centerY="{_signed_int(fill.get("center_y"))}" '
            f'step="{_signed_int(fill.get("step"))}" colorNum="{len(colors)}" '
            f'stepCenter="{_signed_int(fill.get("step_center"), 50)}" '
            f'alpha="{_as_int(fill.get("alpha"))}">{color_xml}</hc:gradation></hc:fillBrush>'
        )
    if fill_type == "image":
        return (
            f'<hc:fillBrush><hc:imgBrush mode="{_safe_enum(fill.get("mode"), "TOTAL")}">'
            f'<hc:img bright="{_signed_int(fill.get("brightness"))}" '
            f'contrast="{_signed_int(fill.get("contrast"))}" '
            f'effect="{_safe_enum(fill.get("effect"), "REAL_PIC")}" '
            f'binaryItemIDRef="image{_as_int(fill.get("binary_item_id_ref"))}" '
            f'alpha="{_as_int(fill.get("alpha"))}"/>'
            '</hc:imgBrush></hc:fillBrush>'
        )
    return ""


def _border_color(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip()
    if text.lower() == "none":
        return "none"
    if len(text) in {7, 9} and text.startswith("#"):
        try:
            int(text[1:], 16)
        except ValueError:
            return fallback
        return text.upper()
    return fallback


def _char_properties_xml(style_semantics: Any, count: int) -> str:
    raw = style_semantics.get("char_shapes", []) if isinstance(style_semantics, dict) else []
    by_id = {_as_int(item.get("id")): item for item in raw if isinstance(item, dict)}
    return "".join(_char_pr_xml(by_id.get(index, {}), index) for index in range(count))


def _char_pr_xml(shape: dict[str, Any], shape_id: int) -> str:
    font_ref = _language_values(shape.get("font_ref"), 0)
    ratio = _language_values(shape.get("ratio"), 100)
    spacing = _language_values(shape.get("spacing"), 0)
    relative_size = _language_values(shape.get("relative_size"), 100)
    offset = _language_values(shape.get("offset"), 0)
    underline = shape.get("underline", {}) if isinstance(shape.get("underline"), dict) else {}
    strikeout = shape.get("strikeout", {}) if isinstance(shape.get("strikeout"), dict) else {}
    outline = shape.get("outline", {}) if isinstance(shape.get("outline"), dict) else {}
    shadow = shape.get("shadow", {}) if isinstance(shape.get("shadow"), dict) else {}
    flags = "".join(
        f"<hh:{tag}/>"
        for key, tag in (
            ("italic", "italic"),
            ("bold", "bold"),
        )
        if bool(shape.get(key))
    )
    trailing_flags = "".join(
        f"<hh:{tag}/>"
        for key, tag in (
            ("emboss", "emboss"),
            ("engrave", "engrave"),
            ("superscript", "supscript"),
            ("subscript", "subscript"),
        )
        if bool(shape.get(key))
    )
    return (
        f'<hh:charPr id="{shape_id}" height="{max(1, _as_int(shape.get("height")) or 1000)}" '
        f'textColor="{_safe_color(shape.get("text_color"), "#000000")}" '
        f'shadeColor="{_safe_color(shape.get("shade_color"), "none", allow_none=True)}" '
        f'useFontSpace="{_bool_int(shape.get("use_font_space"))}" '
        f'useKerning="{_bool_int(shape.get("use_kerning"))}" '
        f'symMark="{_safe_enum(shape.get("sym_mark"), "NONE")}" '
        f'borderFillIDRef="{_as_int(shape.get("border_fill_id"))}">'
        f'<hh:fontRef {_language_attrs(font_ref)}/>'
        f'<hh:ratio {_language_attrs(ratio)}/>'
        f'<hh:spacing {_language_attrs(spacing)}/>'
        f'<hh:relSz {_language_attrs(relative_size)}/>'
        f'<hh:offset {_language_attrs(offset)}/>'
        f'{flags}'
        f'<hh:underline type="{_safe_enum(underline.get("type"), "NONE")}" '
        f'shape="{_safe_enum(underline.get("shape"), "SOLID")}" '
        f'color="{_safe_color(underline.get("color"), "#000000")}"/>'
        f'<hh:strikeout shape="{_safe_enum(strikeout.get("shape"), "NONE")}" '
        f'color="{_safe_color(strikeout.get("color"), "#000000", allow_none=True)}"/>'
        f'<hh:outline type="{_safe_enum(outline.get("type"), "NONE")}"/>'
        f'<hh:shadow type="{_safe_enum(shadow.get("type"), "NONE")}" '
        f'color="{_safe_color(shadow.get("color"), "#B2B2B2")}" '
        f'offsetX="{_signed_int(shadow.get("offset_x"), 10)}" '
        f'offsetY="{_signed_int(shadow.get("offset_y"), 10)}"/>'
        f'{trailing_flags}</hh:charPr>'
    )


def _para_properties_xml(style_semantics: Any, count: int) -> str:
    raw = style_semantics.get("para_shapes", []) if isinstance(style_semantics, dict) else []
    by_id = {_as_int(item.get("id")): item for item in raw if isinstance(item, dict)}
    return "".join(_para_pr_xml(by_id.get(index, {}), index) for index in range(count))


def _para_pr_xml(shape: dict[str, Any], shape_id: int) -> str:
    align = shape.get("align", {}) if isinstance(shape.get("align"), dict) else {}
    heading = shape.get("heading", {}) if isinstance(shape.get("heading"), dict) else {}
    breaks = shape.get("break_setting", {}) if isinstance(shape.get("break_setting"), dict) else {}
    auto = shape.get("auto_spacing", {}) if isinstance(shape.get("auto_spacing"), dict) else {}
    margin = shape.get("margin", {}) if isinstance(shape.get("margin"), dict) else {}
    line = shape.get("line_spacing", {}) if isinstance(shape.get("line_spacing"), dict) else {}
    border = shape.get("border", {}) if isinstance(shape.get("border"), dict) else {}
    line_type = _safe_enum(line.get("type"), "PERCENT")
    line_value = _as_int(line.get("value"))
    default_margin_xml = _para_margin_spacing_xml(
        margin,
        line_type,
        line_value,
    )
    case_margin_xml = _para_margin_spacing_xml(
        {key: _half_signed(value) for key, value in margin.items()},
        line_type,
        _half_signed(line_value) if line_type in {"FIXED", "AT_LEAST"} else line_value,
    )
    return (
        f'<hh:paraPr id="{shape_id}" tabPrIDRef="{_as_int(shape.get("tab_pr_id"))}" '
        f'condense="{_as_int(shape.get("condense"))}" '
        f'fontLineHeight="{_bool_int(shape.get("font_line_height"))}" '
        f'snapToGrid="{_bool_int(shape.get("snap_to_grid"), True)}" '
        f'suppressLineNumbers="{_bool_int(shape.get("suppress_line_numbers"))}" '
        f'checked="{_bool_int(shape.get("checked"))}">'
        f'<hh:align horizontal="{_safe_enum(align.get("horizontal"), "JUSTIFY")}" '
        f'vertical="{_safe_enum(align.get("vertical"), "BASELINE")}"/>'
        f'<hh:heading type="{_safe_enum(heading.get("type"), "NONE")}" '
        f'idRef="{_as_int(heading.get("id_ref"))}" level="{_as_int(heading.get("level"))}"/>'
        f'<hh:breakSetting breakLatinWord="{_safe_enum(breaks.get("break_latin_word"), "KEEP_WORD")}" '
        f'breakNonLatinWord="{_safe_enum(breaks.get("break_non_latin_word"), "KEEP_WORD")}" '
        f'widowOrphan="{_bool_int(breaks.get("widow_orphan"))}" '
        f'keepWithNext="{_bool_int(breaks.get("keep_with_next"))}" '
        f'keepLines="{_bool_int(breaks.get("keep_lines"))}" '
        f'pageBreakBefore="{_bool_int(breaks.get("page_break_before"))}" '
        f'lineWrap="{_safe_enum(breaks.get("line_wrap"), "BREAK")}"/>'
        f'<hh:autoSpacing eAsianEng="{_bool_int(auto.get("e_asian_eng"))}" '
        f'eAsianNum="{_bool_int(auto.get("e_asian_num"))}"/>'
        '<hp:switch><hp:case hp:required-namespace="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar">'
        f'{case_margin_xml}</hp:case><hp:default>{default_margin_xml}</hp:default></hp:switch>'
        f'<hh:border borderFillIDRef="{_as_int(border.get("border_fill_id"))}" '
        f'offsetLeft="{_signed_int(border.get("offset_left"))}" '
        f'offsetRight="{_signed_int(border.get("offset_right"))}" '
        f'offsetTop="{_signed_int(border.get("offset_top"))}" '
        f'offsetBottom="{_signed_int(border.get("offset_bottom"))}" '
        f'connect="{_bool_int(border.get("connect"))}" '
        f'ignoreMargin="{_bool_int(border.get("ignore_margin"))}"/>'
        '</hh:paraPr>'
    )


def _para_margin_spacing_xml(
    margin: dict[str, Any],
    line_type: str,
    line_value: int,
) -> str:
    return (
        '<hh:margin>'
        f'<hc:intent value="{_signed_int(margin.get("indent"))}" unit="HWPUNIT"/>'
        f'<hc:left value="{_signed_int(margin.get("left"))}" unit="HWPUNIT"/>'
        f'<hc:right value="{_signed_int(margin.get("right"))}" unit="HWPUNIT"/>'
        f'<hc:prev value="{_signed_int(margin.get("prev"))}" unit="HWPUNIT"/>'
        f'<hc:next value="{_signed_int(margin.get("next"))}" unit="HWPUNIT"/>'
        '</hh:margin>'
        f'<hh:lineSpacing type="{line_type}" value="{line_value}" unit="HWPUNIT"/>'
    )


def _content_hpf_xml(model: dict[str, Any], binary_items: list[dict[str, Any]]) -> str:
    section_items = "".join(
        f'<opf:item id="section{index}" href="Contents/section{index}.xml" media-type="application/xml"/>'
        for index, _section in enumerate(model.get("sections", []))
    )
    spine = "".join(
        f'<opf:itemref idref="section{index}" linear="yes"/>'
        for index, _section in enumerate(model.get("sections", []))
    )
    binary_manifest = "".join(
        f'<opf:item id="{_xml_escape(item.get("item_id", index + 1))}" '
        f'href="{_xml_escape(item.get("entry_name", ""))}" '
        f'media-type="{_binary_media_type(item)}" '
        f'isEmbeded="{1 if item.get("is_embedded", True) else 0}"/>'
        for index, item in enumerate(binary_items)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/" '
        'version="" unique-identifier="" id="">'
        '<opf:metadata><opf:title>owned-hwp-conversion</opf:title><opf:language>ko</opf:language></opf:metadata>'
        '<opf:manifest><opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>'
        f'<opf:item id="settings" href="settings.xml" media-type="application/xml"/>{section_items}{binary_manifest}</opf:manifest>'
        f'<opf:spine><opf:itemref idref="header" linear="yes"/>{spine}</opf:spine></opf:package>'
    )


def _manifest_xml(section_count: int, binary_items: list[dict[str, Any]]) -> str:
    del section_count, binary_items
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>'
    )


def _version_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" '
        'tagetApplication="WORDPROCESSOR" major="5" minor="0" micro="5" buildNumber="0" '
        'os="1" xmlVersion="1.4" application="owned-hwp-hwpx" appVersion="1.0.0"/>'
    )


def _container_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" '
        'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"><ocf:rootfiles>'
        '<ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>'
        '</ocf:rootfiles></ocf:container>'
    )


def _settings_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ha:HWPApplicationSetting xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
        'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">'
        '<ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/>'
        '<config:config-item-set name="PrintInfo">'
        '<config:config-item name="PrintAutoFootNote" type="boolean">false</config:config-item>'
        '<config:config-item name="PrintAutoHeadNote" type="boolean">false</config:config-item>'
        '<config:config-item name="PrintMethod" type="short">0</config:config-item>'
        '<config:config-item name="OverlapSize" type="short">0</config:config-item>'
        '<config:config-item name="PrintCropMark" type="short">0</config:config-item>'
        '<config:config-item name="BinderHoleType" type="short">0</config:config-item>'
        '<config:config-item name="ZoomX" type="short">100</config:config-item>'
        '<config:config-item name="ZoomY" type="short">100</config:config-item>'
        '</config:config-item-set></ha:HWPApplicationSetting>'
    )


def _distribute(total: int, slots: int) -> list[int]:
    if slots <= 0:
        return []
    base, remainder = divmod(max(0, total), slots)
    return [base + (1 if index < remainder else 0) for index in range(slots)]


def _fit_line_segment_groups(value: Any, slots: int, fallback_total: int) -> list[list[dict[str, Any]]]:
    semantics = value if isinstance(value, dict) else {}
    paragraphs = semantics.get("paragraphs", []) if isinstance(semantics.get("paragraphs"), list) else []
    if paragraphs:
        groups = [
            [segment for segment in paragraph.get("segments", []) if isinstance(segment, dict)]
            if isinstance(paragraph, dict)
            else []
            for paragraph in paragraphs[:slots]
        ]
        while len(groups) < slots:
            groups.append([])
        return groups

    return [
        [_default_line_segment() for _ in range(count)]
        for count in _distribute(fallback_total, slots)
    ]


def _default_line_segment() -> dict[str, int]:
    return {
        "textpos": 0,
        "vertpos": 0,
        "vertsize": 1000,
        "textheight": 1000,
        "baseline": 850,
        "spacing": 600,
        "horzpos": 0,
        "horzsize": 0,
        "flags": 0,
    }


def _distribute_items(items: list[dict[str, Any]], slots: int) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = [[] for _ in range(max(0, slots))]
    if slots <= 0:
        return groups
    for index, item in enumerate(items):
        groups[index % slots].append(item)
    return groups


def _fit_page_definitions(values: Any, count: int) -> list[dict[str, Any]]:
    raw_values = values if isinstance(values, list) else []
    fitted = [
        item if isinstance(item, dict) else {}
        for item in raw_values[:count]
    ]
    while len(fitted) < count:
        fitted.append({})
    return fitted


def _distribute_sub_lists(total: int, cells: int) -> list[int]:
    if cells <= 0:
        return []
    target = max(0, total)
    base, remainder = divmod(target, cells)
    return [base + (1 if index < remainder else 0) for index in range(cells)]


def _xml_escape(value: Any) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _xml_safe_text(value: Any) -> str:
    return "".join(
        char
        for char in str(value or "")
        if char in {"\n", "\t", "\r"} or ord(char) >= 32
    )


def _run_content_xml(
    run: dict[str, Any],
    paragraph_controls: list[dict[str, Any]],
    structural_events: list[tuple[int, int, str, bool]],
    *,
    is_last_run: bool,
) -> str:
    if not structural_events:
        run_text = _text_run_xml(
            run,
            paragraph_controls,
            is_last_run=is_last_run,
        )
        if run_text:
            empty_text = "<hp:t/>" * max(0, _as_int(run.get("empty_text_count")))
            return f"<hp:t>{run_text}</hp:t>{empty_text}"
        return "<hp:t/>" * max(0, _as_int(run.get("empty_text_count")))

    text = _xml_safe_text(run.get("text", ""))
    run_start = _as_int(run.get("visible_start"))
    run_end = _signed_int(run.get("visible_end"), run_start + len(text))
    cursor = run_start
    parts: list[str] = []
    trailing_text_required = False
    for visible_position, _order, xml, requires_text_tail in structural_events:
        position = min(run_end, max(run_start, _as_int(visible_position)))
        fragment = _run_text_fragment_xml(
            run,
            text,
            cursor,
            position,
            _text_controls_for_visible_range(
                paragraph_controls,
                cursor,
                position,
                include_end=False,
            ),
            is_last_fragment=False,
        )
        if fragment:
            parts.append(f"<hp:t>{fragment}</hp:t>")
        parts.append(xml)
        cursor = max(cursor, position)
        trailing_text_required = trailing_text_required or (
            requires_text_tail and position >= run_end
        )
    fragment = _run_text_fragment_xml(
        run,
        text,
        cursor,
        run_end,
        _text_controls_for_visible_range(
            paragraph_controls,
            cursor,
            run_end,
            include_end=True,
        ),
        is_last_fragment=is_last_run,
    )
    if fragment:
        parts.append(f"<hp:t>{fragment}</hp:t>")
    else:
        empty_text_count = max(0, _as_int(run.get("empty_text_count")))
        if empty_text_count:
            parts.append("<hp:t/>" * empty_text_count)
        elif trailing_text_required:
            parts.append("<hp:t/>")
    return "".join(parts)


def _run_text_fragment_xml(
    run: dict[str, Any],
    text: str,
    start: int,
    end: int,
    paragraph_controls: list[dict[str, Any]],
    *,
    is_last_fragment: bool,
) -> str:
    run_start = _as_int(run.get("visible_start"))
    start_offset = min(len(text), max(0, start - run_start))
    end_offset = min(len(text), max(start_offset, end - run_start))
    fragment_run = {
        **run,
        "text": text[start_offset:end_offset],
        "visible_start": start,
        "visible_end": end,
    }
    return _text_run_xml(
        fragment_run,
        paragraph_controls,
        is_last_run=is_last_fragment,
    )


def _text_controls_by_run(
    runs: list[dict[str, Any]],
    paragraph_controls: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = [[] for _ in runs]
    if not groups:
        return groups
    for control in paragraph_controls:
        if not isinstance(control, dict) or not _supported_text_control(control):
            continue
        owner = _run_index_for_source(runs, control.get("source_start"))
        groups[owner].append(control)
    return groups


def _text_controls_for_visible_range(
    controls: list[dict[str, Any]],
    start: int,
    end: int,
    *,
    include_end: bool,
) -> list[dict[str, Any]]:
    return [
        control
        for control in controls
        if start <= _as_int(control.get("visible_start")) < end
        or (
            include_end
            and _as_int(control.get("visible_start")) == end
        )
    ]


def _text_run_xml(
    run: dict[str, Any],
    paragraph_controls: list[dict[str, Any]],
    *,
    is_last_run: bool,
) -> str:
    text = _xml_safe_text(run.get("text", ""))
    start = _as_int(run.get("visible_start"))
    end = _signed_int(run.get("visible_end"), start + len(text))
    controls_by_position: dict[int, list[dict[str, Any]]] = {}
    for control in paragraph_controls:
        if not isinstance(control, dict) or not _supported_text_control(control):
            continue
        position = _as_int(control.get("visible_start"))
        visible_owned = start <= position <= end
        if visible_owned:
            controls_by_position.setdefault(position, []).append(control)

    parts = []
    for offset, char in enumerate(text):
        position = start + offset
        controls = controls_by_position.get(position, [])
        for control in controls:
            if _as_int(control.get("visible_end")) == position:
                parts.append(_text_control_xml(control))
        consuming = next(
            (
                control
                for control in controls
                if _as_int(control.get("visible_end")) > position
            ),
            None,
        )
        parts.append(_text_control_xml(consuming) if consuming is not None else _xml_escape(char))
    for control in controls_by_position.get(end, []):
        if _as_int(control.get("visible_end")) == end:
            parts.append(_text_control_xml(control))
    return "".join(parts)


def _supported_text_control(value: dict[str, Any]) -> bool:
    return _signed_int(value.get("code"), -1) in {9, 10, 24, 30, 31}


def _text_control_xml(value: dict[str, Any]) -> str:
    code = _signed_int(value.get("code"), -1)
    if code == 9:
        return (
            f'<hp:tab width="{_as_int(value.get("tab_width"))}" '
            f'leader="{_as_int(value.get("tab_leader"))}" '
            f'type="{_as_int(value.get("tab_type"))}"/>'
        )
    if code == 10:
        return "<hp:lineBreak/>"
    if code == 24:
        return "<hp:hyphen/>"
    if code == 30:
        return "<hp:nbSpace/>"
    if code == 31:
        return "<hp:fwSpace/>"
    return ""


def _compose_control_xml(value: dict[str, Any]) -> str:
    char_shape_ids = [
        _as_int(item)
        for item in value.get("char_shape_ids", [])
    ]
    char_pr = "".join(
        f'<hp:charPr prIDRef="{char_shape_id}"/>'
        for char_shape_id in char_shape_ids
    )
    return (
        f'<hp:compose circleType="{_xml_escape(value.get("circle_type"))}" '
        f'charSz="{_signed_int(value.get("char_size"))}" '
        f'composeType="{_xml_escape(value.get("compose_type"))}" '
        f'charPrCnt="{len(char_shape_ids)}" '
        f'composeText="{_xml_escape(_xml_safe_text(value.get("compose_text")))}">'
        f"{char_pr}</hp:compose>"
    )


def _text_runs_for_paragraph(text: str, paragraph_style: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    char_pr_count = max(1, _as_int(summary.get("char_pr_count")))
    raw_runs = [
        item
        for item in paragraph_style.get("char_shape_runs", [])
        if isinstance(item, dict)
    ]
    run_count = max(
        1,
        len(raw_runs),
        _as_int(paragraph_style.get("actual_char_shape_run_count")),
        _as_int(paragraph_style.get("declared_char_shape_run_count")),
    )
    safe_text = _xml_safe_text(text)
    if raw_runs:
        sorted_runs = sorted(
            raw_runs,
            key=lambda item: _as_int(item.get("visible_start", item.get("start"))),
        )
        return _split_text_by_positions(
            safe_text,
            sorted_runs,
            char_pr_count,
            run_count,
            _as_int(paragraph_style.get("declared_char_count")),
        )
    return _split_text_evenly(safe_text, run_count, char_pr_count)


def _split_text_by_positions(
    text: str,
    runs: list[dict[str, Any]],
    char_pr_count: int,
    run_count: int,
    declared_char_count: int,
) -> list[dict[str, Any]]:
    normalized_runs = []
    for item in runs[:run_count]:
        normalized_runs.append(
            {
                "start": min(
                    len(text),
                    _as_int(item.get("visible_start", item.get("start"))),
                ),
                "source_start": _as_int(item.get("source_start", item.get("start"))),
                "char_shape_id": _as_int(item.get("char_shape_id")),
                "empty_text_count": max(0, _as_int(item.get("empty_text_count"))),
            }
        )
    if not normalized_runs or normalized_runs[0]["start"] != 0:
        normalized_runs.insert(
            0,
            {
                "start": 0,
                "source_start": 0,
                "char_shape_id": normalized_runs[0]["char_shape_id"] if normalized_runs else 0,
            },
        )
    normalized_runs = sorted(
        normalized_runs[:run_count],
        key=lambda item: (item["start"], item["source_start"]),
    )
    result = []
    for index, item in enumerate(normalized_runs):
        start = item["start"]
        end = normalized_runs[index + 1]["start"] if index + 1 < len(normalized_runs) else len(text)
        source_start = item["source_start"]
        source_end = (
            normalized_runs[index + 1]["source_start"]
            if index + 1 < len(normalized_runs)
            else declared_char_count
        )
        if end < start:
            end = start
        result.append(
            {
                "char_pr_ref": _normalize_ref(item["char_shape_id"], char_pr_count),
                "text": text[start:end],
                "visible_start": start,
                "visible_end": end,
                "source_start": source_start,
                "source_end": max(source_start, source_end),
                "empty_text_count": max(0, _as_int(item.get("empty_text_count"))),
            }
        )
    while len(result) < run_count:
        result.append(
            {
                "char_pr_ref": 0,
                "text": "",
                "visible_start": len(text),
                "visible_end": len(text),
                "source_start": declared_char_count,
                "source_end": declared_char_count,
            }
        )
    return result


def _split_text_evenly(text: str, run_count: int, char_pr_count: int) -> list[dict[str, Any]]:
    if run_count <= 1:
        return [
            {
                "char_pr_ref": 0,
                "text": text,
                "visible_start": 0,
                "visible_end": len(text),
                "source_start": 0,
                "source_end": len(text),
            }
        ]
    result = []
    length = len(text)
    for index in range(run_count):
        start = round((length * index) / run_count)
        end = round((length * (index + 1)) / run_count)
        result.append(
            {
                "char_pr_ref": _normalize_ref(index, char_pr_count),
                "text": text[start:end],
                "visible_start": start,
                "visible_end": end,
                "source_start": start,
                "source_end": end,
            }
        )
    return result


def _normalize_ref(value: Any, count: Any) -> int:
    count_int = max(1, _as_int(count))
    return _as_int(value) % count_int


def _bounded_hwpunit(value: Any, fallback: int) -> int:
    parsed = _as_int(value)
    if parsed <= 0:
        return fallback
    return min(parsed, 1_000_000)


def _is_safe_xml_name(value: Any) -> bool:
    text = str(value or "")
    if not text or not (text[0].isalpha() or text[0] == "_"):
        return False
    return all(char.isalnum() or char in {"_", "-", "."} for char in text)


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _signed_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _half_signed(value: Any) -> int:
    parsed = _signed_int(value)
    return parsed // 2 if parsed >= 0 else -((-parsed) // 2)


def _bool_int(value: Any, fallback: bool = False) -> int:
    if value is None:
        value = fallback
    if isinstance(value, str):
        return int(value.strip().lower() in {"1", "true", "yes"})
    return int(bool(value))


def _safe_enum(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip().upper()
    if text and all(char.isalnum() or char == "_" for char in text):
        return text
    return fallback


def _safe_case_token(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip()
    if text and all(char.isalnum() or char == "_" for char in text):
        return text
    return fallback


def _safe_color(value: Any, fallback: str, *, allow_none: bool = False) -> str:
    text = str(value or "").strip()
    if allow_none and text.lower() == "none":
        return "none"
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
        except ValueError:
            pass
        else:
            return text.upper()
    return fallback


def _unsigned_i32(value: Any) -> int:
    parsed = _signed_int(value)
    return parsed + (1 << 32) if parsed < 0 else parsed


def _float_token(value: float) -> str:
    token = format(value, ".6f").rstrip("0").rstrip(".")
    return "0" if token in {"", "-0"} else token


def _binary_media_type(value: dict[str, Any]) -> str:
    manifest_media_type = str(value.get("manifest_media_type", ""))
    if manifest_media_type:
        return manifest_media_type
    extension = str(value.get("format", "bin")).lower()
    if str(value.get("kind", "")) == "image":
        return {
            "jpg": "image/jpg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "bmp": "image/bmp",
            "gif": "image/gif",
            "wmf": "image/wmf",
            "emf": "image/emf",
        }.get(extension, f"image/{extension}")
    return "application/octet-stream"


def _language_values(value: Any, fallback: int) -> dict[str, int]:
    languages = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
    payload = value if isinstance(value, dict) else {}
    return {language: _signed_int(payload.get(language), fallback) for language in languages}


def _language_attrs(values: dict[str, int]) -> str:
    languages = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
    return " ".join(f'{language}="{_signed_int(values.get(language))}"' for language in languages)
