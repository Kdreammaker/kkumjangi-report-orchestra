"""Typed HWP/HWPX character and paragraph style semantics."""

from __future__ import annotations

from hashlib import sha256
import json
import struct
from typing import Any, Iterable
from xml.etree import ElementTree


FONT_LANGUAGES = ("hangul", "latin", "hanja", "japanese", "other", "symbol", "user")
HWP_FONT_MAPPING_KEYS = tuple(f"face_name_{language}" for language in FONT_LANGUAGES)
HWPX_FONT_LANGUAGES = {language.upper(): language for language in FONT_LANGUAGES}
FONT_FAMILY_TYPES = {
    0: "FCAT_UNKNOWN",
    1: "FCAT_MYUNGJO",
    2: "FCAT_GOTHIC",
    3: "FCAT_SSERIF",
}
ALTERNATE_FONT_TYPES = {0: "UNKNOWN", 1: "TTF", 2: "HFT"}

LINE_SHAPES = {
    0: "SOLID",
    1: "DASH",
    2: "DOT",
    3: "DASH_DOT",
    4: "DASH_DOT_DOT",
    5: "LONG_DASH",
    6: "CIRCLE",
    7: "DOUBLE_SLIM",
    8: "SLIM_THICK",
    9: "THICK_SLIM",
    10: "SLIM_THICK_SLIM",
    11: "WAVE",
    12: "DOUBLE_WAVE",
    13: "THICK_3D",
    14: "THICK_3D_REVERSE_LIGHT",
    15: "3D",
    16: "3D_REVERSE_LIGHT",
}
OUTLINE_TYPES = {
    0: "NONE",
    1: "SOLID",
    2: "DOT",
    3: "THICK",
    4: "DASH",
    5: "DASH_DOT",
    6: "DASH_DOT_DOT",
}
SHADOW_TYPES = {0: "NONE", 1: "DROP", 2: "CONTINUOUS"}
SYMBOL_MARKS = {
    0: "NONE",
    1: "DOT_ABOVE",
    2: "RING_ABOVE",
    3: "CARON",
    4: "TILDE",
    5: "MIDDLE_DOT",
    6: "COLON",
}
HORIZONTAL_ALIGNMENTS = {
    0: "JUSTIFY",
    1: "LEFT",
    2: "RIGHT",
    3: "CENTER",
    4: "DISTRIBUTE",
    5: "DISTRIBUTE",
}
VERTICAL_ALIGNMENTS = {0: "BASELINE", 1: "TOP", 2: "CENTER", 3: "BOTTOM"}
HEADING_TYPES = {0: "NONE", 1: "OUTLINE", 2: "NUMBER", 3: "BULLET"}
LINE_SPACING_TYPES = {0: "PERCENT", 1: "FIXED", 2: "BETWEEN_LINES", 3: "AT_LEAST"}
LINE_WRAP_TYPES = {0: "BREAK", 1: "SQUEEZE", 2: "KEEP"}

CHAR_SEMANTIC_FIELDS = (
    "font_ref",
    "ratio",
    "spacing",
    "relative_size",
    "offset",
    "height",
    "text_color",
    "shade_color",
    "use_font_space",
    "use_kerning",
    "sym_mark",
    "border_fill_id",
    "italic",
    "bold",
    "emboss",
    "engrave",
    "superscript",
    "subscript",
    "underline",
    "strikeout",
    "outline",
    "shadow",
)
PARA_SEMANTIC_FIELDS = (
    "tab_pr_id",
    "condense",
    "font_line_height",
    "snap_to_grid",
    "suppress_line_numbers",
    "checked",
    "align",
    "heading",
    "break_setting",
    "auto_spacing",
    "margin",
    "line_spacing",
    "border",
)


def parse_hwp_style_records(
    records: Iterable[dict[str, Any]],
    id_mappings: dict[str, Any],
) -> dict[str, Any]:
    """Parse DocInfo style records into a path-free semantic table."""

    face_records = [bytes(item["body"]) for item in records if item.get("tag_name") == "FACE_NAME"]
    char_records = [bytes(item["body"]) for item in records if item.get("tag_name") == "CHAR_SHAPE"]
    para_records = [bytes(item["body"]) for item in records if item.get("tag_name") == "PARA_SHAPE"]
    font_faces: list[dict[str, Any]] = []
    face_offset = 0
    font_parse_errors = 0
    for language, mapping_key in zip(FONT_LANGUAGES, HWP_FONT_MAPPING_KEYS):
        expected = _nonnegative_int(id_mappings.get(mapping_key))
        selected = face_records[face_offset : face_offset + expected]
        fonts = []
        for font_id, body in enumerate(selected):
            parsed = parse_hwp_face_name(body, font_id)
            font_parse_errors += int(parsed.get("parse_status") != "parsed")
            fonts.append(parsed)
        font_faces.append({"language": language, "fonts": fonts})
        face_offset += expected

    char_shapes = [parse_hwp_char_shape(body, index) for index, body in enumerate(char_records)]
    para_shapes = [parse_hwp_para_shape(body, index) for index, body in enumerate(para_records)]
    expected_face_count = sum(_nonnegative_int(id_mappings.get(key)) for key in HWP_FONT_MAPPING_KEYS)
    expected_char_count = _nonnegative_int(id_mappings.get("char_shape"))
    expected_para_count = _nonnegative_int(id_mappings.get("para_shape"))
    checks = {
        "font_face_count": len(face_records) == expected_face_count,
        "char_shape_count": len(char_shapes) == expected_char_count,
        "para_shape_count": len(para_shapes) == expected_para_count,
        "font_face_parse": font_parse_errors == 0,
        "char_shape_parse": all(item["parse_status"] == "parsed" for item in char_shapes),
        "para_shape_parse": all(item["parse_status"] in {"parsed", "parsed_with_extension"} for item in para_shapes),
    }
    return {
        "status": "parsed" if all(checks.values()) else "parsed_with_warnings",
        "checks": checks,
        "counts": {
            "expected_font_face_count": expected_face_count,
            "font_face_count": len(face_records),
            "expected_char_shape_count": expected_char_count,
            "char_shape_count": len(char_shapes),
            "expected_para_shape_count": expected_para_count,
            "para_shape_count": len(para_shapes),
            "para_shape_extension_count": sum(bool(item.get("extension_byte_count")) for item in para_shapes),
            "para_shape_extension_nonzero_count": sum(bool(item.get("extension_word")) for item in para_shapes),
            "font_alternate_face_count": sum(
                bool(font.get("alternate_face")) for group in font_faces for font in group["fonts"]
            ),
            "font_default_face_unmapped_count": sum(
                bool(font.get("default_face")) for group in font_faces for font in group["fonts"]
            ),
            "font_type_info_count": sum(
                bool(font.get("type_info")) for group in font_faces for font in group["fonts"]
            ),
            "font_serif_style_unmapped_count": sum(
                bool(font.get("type_info", {}).get("serif_style"))
                for group in font_faces
                for font in group["fonts"]
            ),
        },
        "font_faces": font_faces,
        "char_shapes": char_shapes,
        "para_shapes": para_shapes,
    }


def parse_hwp_face_name(body: bytes, font_id: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": font_id,
        "face": "HancomBatang",
        "type": "TTF",
        "is_embedded": False,
        "alternate_face": "",
        "alternate_type": "UNKNOWN",
        "default_face": "",
        "type_info": {},
        "parse_status": "fallback_short_body",
    }
    if len(body) < 3:
        return result
    properties = body[0]
    offset = 1
    face, offset, ok = _read_hwp_string(body, offset)
    if not ok:
        return result
    result["face"] = face or result["face"]
    if properties & 0x80:
        if offset >= len(body):
            return result
        alternate_type = body[offset]
        alternate, offset, ok = _read_hwp_string(body, offset + 1)
        if not ok:
            return result
        result["alternate_face"] = alternate
        result["alternate_type"] = ALTERNATE_FONT_TYPES.get(alternate_type, "UNKNOWN")
    if properties & 0x40:
        if offset + 10 > len(body):
            return result
        values = list(body[offset : offset + 10])
        result["type_info"] = {
            "family_type": FONT_FAMILY_TYPES.get(values[0], "FCAT_UNKNOWN"),
            "serif_style": values[1],
            "weight": values[2],
            "proportion": values[3],
            "contrast": values[4],
            "stroke_variation": values[5],
            "arm_style": values[6],
            "letterform": values[7],
            "midline": values[8],
            "x_height": values[9],
        }
        offset += 10
    if properties & 0x20:
        default_face, offset, ok = _read_hwp_string(body, offset)
        if not ok:
            return result
        result["default_face"] = default_face
    result["parse_status"] = "parsed" if offset == len(body) else "parsed_with_trailing_bytes"
    result["trailing_byte_count"] = max(0, len(body) - offset)
    return result


def parse_hwp_char_shape(body: bytes, shape_id: int) -> dict[str, Any]:
    default = _default_char_shape(shape_id)
    if len(body) < 68:
        default["parse_status"] = "fallback_short_body"
        return default
    face_ids = struct.unpack_from("<7H", body, 0)
    ratios = tuple(body[14:21])
    spacings = struct.unpack_from("<7b", body, 21)
    relative_sizes = tuple(body[28:35])
    offsets = struct.unpack_from("<7b", body, 35)
    height = max(0, struct.unpack_from("<i", body, 42)[0])
    attributes = struct.unpack_from("<I", body, 46)[0]
    shadow_x, shadow_y = struct.unpack_from("<bb", body, 50)
    underline_type = (attributes >> 2) & 0x3
    underline = _canonical_underline(
        {
            "type": {0: "NONE", 1: "BOTTOM", 3: "TOP"}.get(underline_type, "NONE"),
            "shape": LINE_SHAPES.get((attributes >> 4) & 0xF, "SOLID"),
            "color": _colorref(body, 56),
        }
    )
    strikeout_type = (attributes >> 18) & 0x7
    result = {
        "id": shape_id,
        "font_ref": _language_map(face_ids),
        "ratio": _language_map(ratios),
        "spacing": _language_map(spacings),
        "relative_size": _language_map(relative_sizes),
        "offset": _language_map(offsets),
        "height": height,
        "text_color": _colorref(body, 52),
        "shade_color": _colorref(body, 60, allow_none=True),
        "use_font_space": bool(attributes & (1 << 25)),
        "use_kerning": bool(attributes & (1 << 30)),
        "sym_mark": SYMBOL_MARKS.get((attributes >> 21) & 0xF, "NONE"),
        "border_fill_id": struct.unpack_from("<H", body, 68)[0] if len(body) >= 70 else 0,
        "italic": bool(attributes & 0x1),
        "bold": bool(attributes & 0x2),
        "emboss": bool(attributes & (1 << 13)),
        "engrave": bool(attributes & (1 << 14)),
        "superscript": bool(attributes & (1 << 15)),
        "subscript": bool(attributes & (1 << 16)),
        "underline": underline,
        "strikeout": {
            "shape": LINE_SHAPES.get((attributes >> 26) & 0xF, "SOLID") if strikeout_type else "NONE",
            "color": _colorref(body, 70, allow_none=True) if len(body) >= 74 else "#000000",
        },
        "outline": {"type": OUTLINE_TYPES.get((attributes >> 8) & 0x7, "NONE")},
        "shadow": {
            "type": SHADOW_TYPES.get((attributes >> 11) & 0x3, "NONE"),
            "color": _colorref(body, 64),
            "offset_x": shadow_x,
            "offset_y": shadow_y,
        },
        "parse_status": "parsed",
    }
    return result


def parse_hwp_para_shape(body: bytes, shape_id: int) -> dict[str, Any]:
    default = _default_para_shape(shape_id)
    if len(body) < 42:
        default["parse_status"] = "fallback_short_body"
        return default
    attr1 = struct.unpack_from("<I", body, 0)[0]
    left, right, indent, prev, next_spacing, old_line_spacing = struct.unpack_from("<6i", body, 4)
    tab_id, numbering_id, border_fill_id = struct.unpack_from("<3H", body, 28)
    border_offsets = struct.unpack_from("<4h", body, 34)
    attr2 = struct.unpack_from("<I", body, 42)[0] if len(body) >= 46 else 0
    attr3 = struct.unpack_from("<I", body, 46)[0] if len(body) >= 50 else 0
    line_spacing = struct.unpack_from("<I", body, 50)[0] if len(body) >= 54 else max(0, old_line_spacing)
    extension_word = struct.unpack_from("<I", body, 54)[0] if len(body) >= 58 else 0
    heading_type = (attr1 >> 23) & 0x3
    result = {
        "id": shape_id,
        "tab_pr_id": tab_id,
        "condense": (attr1 >> 9) & 0x7F,
        "font_line_height": bool(attr1 & (1 << 22)),
        "snap_to_grid": bool(attr1 & (1 << 8)),
        "suppress_line_numbers": False,
        "checked": False,
        "align": {
            "horizontal": HORIZONTAL_ALIGNMENTS.get((attr1 >> 2) & 0x7, "JUSTIFY"),
            "vertical": VERTICAL_ALIGNMENTS.get((attr1 >> 20) & 0x3, "BASELINE"),
        },
        "heading": {
            "type": HEADING_TYPES.get(heading_type, "NONE"),
            "id_ref": 0 if heading_type == 0 or numbering_id == 0xFFFF else numbering_id,
            "level": (attr1 >> 25) & 0x7,
        },
        "break_setting": {
            "break_latin_word": {0: "KEEP_WORD", 1: "HYPHENATION", 2: "BREAK_WORD"}.get(
                (attr1 >> 5) & 0x3,
                "KEEP_WORD",
            ),
            "break_non_latin_word": "KEEP_WORD" if attr1 & (1 << 7) else "BREAK_WORD",
            "widow_orphan": bool(attr1 & (1 << 16)),
            "keep_with_next": bool(attr1 & (1 << 17)),
            "keep_lines": bool(attr1 & (1 << 18)),
            "page_break_before": bool(attr1 & (1 << 19)),
            "line_wrap": LINE_WRAP_TYPES.get(attr2 & 0x3, "BREAK"),
        },
        "auto_spacing": {
            "e_asian_eng": bool(attr2 & (1 << 4)),
            "e_asian_num": bool(attr2 & (1 << 5)),
        },
        "margin": {
            "indent": indent,
            "left": left,
            "right": right,
            "prev": prev,
            "next": next_spacing,
        },
        "line_spacing": {
            "type": LINE_SPACING_TYPES.get(attr3 & 0x1F, "PERCENT"),
            "value": line_spacing,
            "unit": "HWPUNIT",
        },
        "border": {
            "border_fill_id": border_fill_id,
            "offset_left": border_offsets[0],
            "offset_right": border_offsets[1],
            "offset_top": border_offsets[2],
            "offset_bottom": border_offsets[3],
            "connect": bool(attr1 & (1 << 28)),
            "ignore_margin": bool(attr1 & (1 << 29)),
        },
        "parse_status": "parsed_with_extension" if len(body) > 54 else "parsed",
        "extension_byte_count": max(0, len(body) - 54),
        "extension_word": extension_word,
    }
    return result


def parse_hwpx_style_root(root: ElementTree.Element) -> dict[str, Any]:
    """Parse an HWPX header root into the same semantic table as HWP."""

    font_faces: list[dict[str, Any]] = []
    for language in FONT_LANGUAGES:
        font_faces.append({"language": language, "fonts": []})
    font_groups = {item["language"]: item["fonts"] for item in font_faces}
    char_shapes: list[dict[str, Any]] = []
    para_shapes: list[dict[str, Any]] = []

    for element in root.iter():
        local = _local_name(element.tag)
        if local == "fontface":
            language = HWPX_FONT_LANGUAGES.get(str(element.attrib.get("lang", "")).upper())
            if not language:
                continue
            fonts = []
            for child in element:
                if _local_name(child.tag) != "font":
                    continue
                font_children = {_local_name(item.tag): item for item in child}
                subst_font = font_children.get("substFont")
                type_info = font_children.get("typeInfo")
                fonts.append(
                    {
                        "id": _xml_int(child.attrib.get("id")),
                        "face": str(child.attrib.get("face", "HancomBatang")),
                        "type": str(child.attrib.get("type", "TTF")),
                        "is_embedded": _xml_bool(child.attrib.get("isEmbedded")),
                        "alternate_face": str(_element_attr(subst_font, "face") or ""),
                        "alternate_type": str(_element_attr(subst_font, "type") or "UNKNOWN").upper(),
                        "default_face": "",
                        "type_info": _parse_hwpx_font_type_info(type_info),
                    }
                )
            font_groups[language].extend(sorted(fonts, key=lambda item: item["id"]))
        elif local == "charPr":
            char_shapes.append(_parse_hwpx_char_shape(element))
        elif local == "paraPr":
            para_shapes.append(_parse_hwpx_para_shape(element))

    char_shapes.sort(key=lambda item: item["id"])
    para_shapes.sort(key=lambda item: item["id"])
    return {
        "status": "parsed",
        "counts": {
            "font_face_count": sum(len(item["fonts"]) for item in font_faces),
            "char_shape_count": len(char_shapes),
            "para_shape_count": len(para_shapes),
        },
        "font_faces": font_faces,
        "char_shapes": char_shapes,
        "para_shapes": para_shapes,
    }


def compare_style_semantics(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Return path-free field exactness without exposing font names."""

    source_chars = source.get("char_shapes", []) if isinstance(source, dict) else []
    target_chars = target.get("char_shapes", []) if isinstance(target, dict) else []
    source_paras = source.get("para_shapes", []) if isinstance(source, dict) else []
    target_paras = target.get("para_shapes", []) if isinstance(target, dict) else []
    char_field_exact = _field_exact_counts(source_chars, target_chars, CHAR_SEMANTIC_FIELDS)
    para_field_exact = _field_exact_counts(source_paras, target_paras, PARA_SEMANTIC_FIELDS)
    font_source = _font_semantic_table(source)
    font_target = _font_semantic_table(target)
    font_names_source = _font_name_table(source)
    font_names_target = _font_name_table(target)
    checks = {
        "font_face_count": len(font_source) == len(font_target),
        "font_face_names": font_names_source == font_names_target,
        "font_face_semantics": font_source == font_target,
        "char_shape_count": len(source_chars) == len(target_chars),
        "char_shape_fields": all(value == len(source_chars) for value in char_field_exact.values())
        and len(source_chars) == len(target_chars),
        "para_shape_count": len(source_paras) == len(target_paras),
        "para_shape_fields": all(value == len(source_paras) for value in para_field_exact.values())
        and len(source_paras) == len(target_paras),
    }
    return {
        "status": "pass" if all(checks.values()) else "diverged",
        "checks": checks,
        "counts": {
            "source_font_face_count": len(font_source),
            "target_font_face_count": len(font_target),
            "source_default_face_unmapped_count": _default_face_count(source),
            "target_default_face_unmapped_count": _default_face_count(target),
            "source_char_shape_count": len(source_chars),
            "target_char_shape_count": len(target_chars),
            "source_para_shape_count": len(source_paras),
            "target_para_shape_count": len(target_paras),
        },
        "char_field_exact_counts": char_field_exact,
        "para_field_exact_counts": para_field_exact,
        "source_digest": _semantic_digest(source),
        "target_digest": _semantic_digest(target),
    }


def _parse_hwpx_char_shape(element: ElementTree.Element) -> dict[str, Any]:
    children = {_local_name(child.tag): child for child in element}
    flags = {_local_name(child.tag) for child in element}
    return {
        "id": _xml_int(element.attrib.get("id")),
        "font_ref": _language_attrs(children.get("fontRef"), 0),
        "ratio": _language_attrs(children.get("ratio"), 100),
        "spacing": _language_attrs(children.get("spacing"), 0),
        "relative_size": _language_attrs(children.get("relSz"), 100),
        "offset": _language_attrs(children.get("offset"), 0),
        "height": _xml_int(element.attrib.get("height"), 1000),
        "text_color": _normalize_color(element.attrib.get("textColor")),
        "shade_color": _normalize_color(element.attrib.get("shadeColor"), allow_none=True),
        "use_font_space": _xml_bool(element.attrib.get("useFontSpace")),
        "use_kerning": _xml_bool(element.attrib.get("useKerning")),
        "sym_mark": str(element.attrib.get("symMark", "NONE")).upper(),
        "border_fill_id": _xml_int(element.attrib.get("borderFillIDRef")),
        "italic": "italic" in flags,
        "bold": "bold" in flags,
        "emboss": "emboss" in flags,
        "engrave": "engrave" in flags,
        "superscript": "supscript" in flags,
        "subscript": "subscript" in flags,
        "underline": _canonical_underline(
            _style_child(children.get("underline"), {"type": "NONE", "shape": "SOLID", "color": "#000000"})
        ),
        "strikeout": _style_child(children.get("strikeout"), {"shape": "NONE", "color": "#000000"}),
        "outline": _style_child(children.get("outline"), {"type": "NONE"}),
        "shadow": _shadow_child(children.get("shadow")),
        "parse_status": "parsed",
    }


def _parse_hwpx_font_type_info(element: ElementTree.Element | None) -> dict[str, Any]:
    if element is None:
        return {}
    return {
        "family_type": str(element.attrib.get("familyType", "FCAT_UNKNOWN")).upper(),
        "weight": _xml_int(element.attrib.get("weight")),
        "proportion": _xml_int(element.attrib.get("proportion")),
        "contrast": _xml_int(element.attrib.get("contrast")),
        "stroke_variation": _xml_int(element.attrib.get("strokeVariation")),
        "arm_style": _xml_int(element.attrib.get("armStyle")),
        "letterform": _xml_int(element.attrib.get("letterform")),
        "midline": _xml_int(element.attrib.get("midline")),
        "x_height": _xml_int(element.attrib.get("xHeight")),
    }


def _parse_hwpx_para_shape(element: ElementTree.Element) -> dict[str, Any]:
    children = {_local_name(child.tag): child for child in element}
    margin, line_spacing = _canonical_margin_and_spacing(element)
    align = children.get("align")
    heading = children.get("heading")
    breaks = children.get("breakSetting")
    auto_spacing = children.get("autoSpacing")
    border = children.get("border")
    return {
        "id": _xml_int(element.attrib.get("id")),
        "tab_pr_id": _xml_int(element.attrib.get("tabPrIDRef")),
        "condense": _xml_int(element.attrib.get("condense")),
        "font_line_height": _xml_bool(element.attrib.get("fontLineHeight")),
        "snap_to_grid": _xml_bool(element.attrib.get("snapToGrid"), True),
        "suppress_line_numbers": _xml_bool(element.attrib.get("suppressLineNumbers")),
        "checked": _xml_bool(element.attrib.get("checked")),
        "align": {
            "horizontal": _attr_upper(align, "horizontal", "JUSTIFY"),
            "vertical": _attr_upper(align, "vertical", "BASELINE"),
        },
        "heading": {
            "type": _attr_upper(heading, "type", "NONE"),
            "id_ref": _child_int(heading, "idRef"),
            "level": _child_int(heading, "level"),
        },
        "break_setting": {
            "break_latin_word": _attr_upper(breaks, "breakLatinWord", "KEEP_WORD"),
            "break_non_latin_word": _attr_upper(breaks, "breakNonLatinWord", "KEEP_WORD"),
            "widow_orphan": _child_bool(breaks, "widowOrphan"),
            "keep_with_next": _child_bool(breaks, "keepWithNext"),
            "keep_lines": _child_bool(breaks, "keepLines"),
            "page_break_before": _child_bool(breaks, "pageBreakBefore"),
            "line_wrap": _attr_upper(breaks, "lineWrap", "BREAK"),
        },
        "auto_spacing": {
            "e_asian_eng": _child_bool(auto_spacing, "eAsianEng"),
            "e_asian_num": _child_bool(auto_spacing, "eAsianNum"),
        },
        "margin": margin,
        "line_spacing": line_spacing,
        "border": {
            "border_fill_id": _child_int(border, "borderFillIDRef"),
            "offset_left": _child_signed_int(border, "offsetLeft"),
            "offset_right": _child_signed_int(border, "offsetRight"),
            "offset_top": _child_signed_int(border, "offsetTop"),
            "offset_bottom": _child_signed_int(border, "offsetBottom"),
            "connect": _child_bool(border, "connect"),
            "ignore_margin": _child_bool(border, "ignoreMargin"),
        },
        "parse_status": "parsed",
    }


def _canonical_margin_and_spacing(element: ElementTree.Element) -> tuple[dict[str, int], dict[str, Any]]:
    preferred_root = element
    for child in element:
        if _local_name(child.tag) != "switch":
            continue
        default = next((item for item in child if _local_name(item.tag) == "default"), None)
        preferred_root = default if default is not None else child
        break
    margin_element = next((item for item in preferred_root.iter() if _local_name(item.tag) == "margin"), None)
    line_element = next((item for item in preferred_root.iter() if _local_name(item.tag) == "lineSpacing"), None)
    margin_children = (
        {_local_name(child.tag): child for child in margin_element}
        if margin_element is not None
        else {}
    )
    margin = {
        "indent": _xml_signed_int(_element_attr(margin_children.get("intent"), "value")),
        "left": _xml_signed_int(_element_attr(margin_children.get("left"), "value")),
        "right": _xml_signed_int(_element_attr(margin_children.get("right"), "value")),
        "prev": _xml_signed_int(_element_attr(margin_children.get("prev"), "value")),
        "next": _xml_signed_int(_element_attr(margin_children.get("next"), "value")),
    }
    line_spacing = {
        "type": _attr_upper(line_element, "type", "PERCENT"),
        "value": _child_int(line_element, "value"),
        "unit": _attr_upper(line_element, "unit", "HWPUNIT"),
    }
    return margin, line_spacing


def _default_char_shape(shape_id: int) -> dict[str, Any]:
    return {
        "id": shape_id,
        "font_ref": _language_map((0,) * 7),
        "ratio": _language_map((100,) * 7),
        "spacing": _language_map((0,) * 7),
        "relative_size": _language_map((100,) * 7),
        "offset": _language_map((0,) * 7),
        "height": 1000,
        "text_color": "#000000",
        "shade_color": "none",
        "use_font_space": False,
        "use_kerning": False,
        "sym_mark": "NONE",
        "border_fill_id": 0,
        "italic": False,
        "bold": False,
        "emboss": False,
        "engrave": False,
        "superscript": False,
        "subscript": False,
        "underline": {"type": "NONE", "shape": "SOLID", "color": "#000000"},
        "strikeout": {"shape": "NONE", "color": "#000000"},
        "outline": {"type": "NONE"},
        "shadow": {"type": "NONE", "color": "#B2B2B2", "offset_x": 10, "offset_y": 10},
        "parse_status": "fallback",
    }


def _default_para_shape(shape_id: int) -> dict[str, Any]:
    return {
        "id": shape_id,
        "tab_pr_id": 0,
        "condense": 0,
        "font_line_height": False,
        "snap_to_grid": True,
        "suppress_line_numbers": False,
        "checked": False,
        "align": {"horizontal": "JUSTIFY", "vertical": "BASELINE"},
        "heading": {"type": "NONE", "id_ref": 0, "level": 0},
        "break_setting": {
            "break_latin_word": "KEEP_WORD",
            "break_non_latin_word": "KEEP_WORD",
            "widow_orphan": False,
            "keep_with_next": False,
            "keep_lines": False,
            "page_break_before": False,
            "line_wrap": "BREAK",
        },
        "auto_spacing": {"e_asian_eng": False, "e_asian_num": False},
        "margin": {"indent": 0, "left": 0, "right": 0, "prev": 0, "next": 0},
        "line_spacing": {"type": "PERCENT", "value": 160, "unit": "HWPUNIT"},
        "border": {
            "border_fill_id": 0,
            "offset_left": 0,
            "offset_right": 0,
            "offset_top": 0,
            "offset_bottom": 0,
            "connect": False,
            "ignore_margin": False,
        },
        "parse_status": "fallback",
        "extension_byte_count": 0,
    }


def _read_hwp_string(body: bytes, offset: int) -> tuple[str, int, bool]:
    if offset + 2 > len(body):
        return "", offset, False
    length = struct.unpack_from("<H", body, offset)[0]
    offset += 2
    byte_length = length * 2
    if offset + byte_length > len(body):
        return "", offset, False
    text = body[offset : offset + byte_length].decode("utf-16le", errors="replace")
    return text, offset + byte_length, True


def _colorref(body: bytes, offset: int, *, allow_none: bool = False) -> str:
    if offset + 4 > len(body):
        return "none" if allow_none else "#000000"
    value = struct.unpack_from("<I", body, offset)[0]
    if allow_none and value == 0xFFFFFFFF:
        return "none"
    red, green, blue = body[offset], body[offset + 1], body[offset + 2]
    return f"#{red:02X}{green:02X}{blue:02X}"


def _language_map(values: Iterable[Any]) -> dict[str, int]:
    return {language: int(value) for language, value in zip(FONT_LANGUAGES, values)}


def _language_attrs(element: ElementTree.Element | None, fallback: int) -> dict[str, int]:
    if element is None:
        return {language: fallback for language in FONT_LANGUAGES}
    return {language: _xml_signed_int(element.attrib.get(language), fallback) for language in FONT_LANGUAGES}


def _style_child(element: ElementTree.Element | None, defaults: dict[str, str]) -> dict[str, str]:
    result = dict(defaults)
    if element is None:
        return result
    for key in result:
        attr = "color" if key == "color" else key
        if attr in element.attrib:
            value = str(element.attrib[attr])
            result[key] = _normalize_color(value, allow_none=True) if key == "color" else value.upper()
    return result


def _canonical_underline(value: dict[str, str]) -> dict[str, str]:
    if str(value.get("type", "NONE")).upper() == "NONE":
        return {"type": "NONE", "shape": "SOLID", "color": "#000000"}
    return value


def _shadow_child(element: ElementTree.Element | None) -> dict[str, Any]:
    if element is None:
        return {"type": "NONE", "color": "#B2B2B2", "offset_x": 10, "offset_y": 10}
    return {
        "type": str(element.attrib.get("type", "NONE")).upper(),
        "color": _normalize_color(element.attrib.get("color")),
        "offset_x": _xml_signed_int(element.attrib.get("offsetX"), 10),
        "offset_y": _xml_signed_int(element.attrib.get("offsetY"), 10),
    }


def _field_exact_counts(
    source: list[dict[str, Any]],
    target: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> dict[str, int]:
    return {
        field: sum(
            1
            for left, right in zip(source, target)
            if left.get(field) == right.get(field)
        )
        for field in fields
    }


def _font_name_table(payload: dict[str, Any]) -> list[tuple[str, int, str]]:
    result = []
    for group in payload.get("font_faces", []) if isinstance(payload, dict) else []:
        language = str(group.get("language", ""))
        for font in group.get("fonts", []):
            result.append((language, _nonnegative_int(font.get("id")), str(font.get("face", ""))))
    return result


def _font_semantic_table(payload: dict[str, Any]) -> list[tuple[Any, ...]]:
    result = []
    for group in payload.get("font_faces", []) if isinstance(payload, dict) else []:
        language = str(group.get("language", ""))
        for font in group.get("fonts", []):
            result.append(
                (
                    language,
                    _nonnegative_int(font.get("id")),
                    str(font.get("face", "")),
                    str(font.get("alternate_face", "")),
                    str(font.get("alternate_type", "UNKNOWN")).upper(),
                    _canonical_type_info(font.get("type_info")),
                )
            )
    return result


def _canonical_type_info(value: Any) -> tuple[Any, ...]:
    payload = value if isinstance(value, dict) else {}
    if not payload:
        return ()
    return (
        str(payload.get("family_type", "FCAT_UNKNOWN")).upper(),
        _nonnegative_int(payload.get("weight")),
        _nonnegative_int(payload.get("proportion")),
        _nonnegative_int(payload.get("contrast")),
        _nonnegative_int(payload.get("stroke_variation")),
        _nonnegative_int(payload.get("arm_style")),
        _nonnegative_int(payload.get("letterform")),
        _nonnegative_int(payload.get("midline")),
        _nonnegative_int(payload.get("x_height")),
    )


def _default_face_count(payload: dict[str, Any]) -> int:
    return sum(
        bool(font.get("default_face"))
        for group in payload.get("font_faces", []) if isinstance(payload, dict)
        for font in group.get("fonts", [])
    )


def _semantic_digest(payload: dict[str, Any]) -> str:
    semantic = {
        "font_faces": _font_semantic_table(payload),
        "char_shapes": [
            {field: item.get(field) for field in CHAR_SEMANTIC_FIELDS}
            for item in payload.get("char_shapes", [])
        ],
        "para_shapes": [
            {field: item.get(field) for field in PARA_SEMANTIC_FIELDS}
            for item in payload.get("para_shapes", [])
        ],
    }
    encoded = json.dumps(semantic, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _normalize_color(value: Any, *, allow_none: bool = False) -> str:
    text = str(value or "")
    if allow_none and text.lower() == "none":
        return "none"
    if len(text) == 7 and text.startswith("#"):
        return text.upper()
    return "none" if allow_none else "#000000"


def _attr_upper(element: ElementTree.Element | None, name: str, fallback: str) -> str:
    if element is None:
        return fallback
    return str(element.attrib.get(name, fallback)).upper()


def _element_attr(element: ElementTree.Element | None, name: str) -> Any:
    return element.attrib.get(name) if element is not None else None


def _child_int(element: ElementTree.Element | None, name: str) -> int:
    return _xml_int(_element_attr(element, name))


def _child_signed_int(element: ElementTree.Element | None, name: str) -> int:
    return _xml_signed_int(_element_attr(element, name))


def _child_bool(element: ElementTree.Element | None, name: str) -> bool:
    return _xml_bool(_element_attr(element, name))


def _xml_int(value: Any, fallback: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return fallback


def _xml_signed_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _xml_bool(value: Any, fallback: bool = False) -> bool:
    if value is None:
        return fallback
    return str(value).strip().lower() in {"1", "true", "yes"}


def _nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag
