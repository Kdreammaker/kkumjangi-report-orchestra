"""Neutral document model derived from owned HWP structural profiles."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .hwp_profile import profile_hwp_file
from .line_segment_semantics import map_hwp_line_segment_text_positions
from .object_binary_semantics import load_hwp_binary_payloads, public_binary_semantics
from .text_fidelity import extract_hwp_text


HIGH_CONFIDENCE_RULES = (
    "sections.hwp_body_streams_to_hwpx_sections",
    "sections.hwp_doc_properties_to_hwpx_sections",
    "paragraphs.para_header_to_hwpx_p",
    "layout.para_line_seg_to_hwpx_lineseg",
    "layout.portable_line_segment_source_positions_to_visible_positions",
    "tables.table_record_to_hwpx_tbl",
    "tables.table_record_rows_to_hwpx_tr",
    "tables.table_record_cell_array_to_hwpx_tc",
    "objects.picture_record_to_hwpx_pic_tags",
    "package.bindata_streams_to_hwpx_bindata_entries",
    "package.bindata_metadata_to_hwpx_content_manifest",
    "package.bindata_payload_decode_to_hwpx_payload",
    "objects.shape_component_to_hwpx_drawing_object",
    "objects.shape_control_to_paragraph_anchor",
    "objects.shape_geometry_transform_to_hwpx_geometry",
    "objects.picture_crop_effect_to_hwpx_picture",
    "page.page_def_to_hwpx_page_pr",
    "page.page_def_to_hwpx_sec_pr",
    "page.page_def_geometry_to_hwpx_page_pr_attrs",
    "tables.list_header_to_hwpx_sub_list",
    "lists.bullet_to_hwpx_bullet",
    "runs.para_char_shape_runs_to_hwpx_runs",
    "styles.id_mapping_char_shape_to_hwpx_char_pr",
    "styles.id_mapping_para_shape_to_hwpx_para_pr",
    "styles.face_name_to_hwpx_fontfaces",
    "styles.char_shape_semantics_to_hwpx_char_pr",
    "styles.para_shape_semantics_to_hwpx_para_pr",
    "styles.portable_snap_to_grid_to_hwpx_para_pr",
    "styles.compatibility_font_type_to_hwpx_fontface",
    "lists.tab_def_semantics_to_hwpx_tab_pr",
    "lists.numbering_semantics_to_hwpx_numbering",
    "lists.bullet_semantics_to_hwpx_bullet",
    "sections.section_definition_to_hwpx_sec_pr",
    "sections.note_shapes_to_hwpx_note_pr",
    "sections.page_border_fill_to_hwpx_page_border_fill",
    "tables.border_fill_semantics_to_hwpx_border_fill",
    "tables.portable_no_effect_solid_fill_to_hwpx_no_fill",
    "tables.table_object_semantics_to_hwpx_tbl",
    "tables.cell_semantics_to_hwpx_tc",
    "tables.paragraph_ownership_to_hwpx_sub_list",
    "tables.nested_table_parentage_to_hwpx_nested_tbl",
    "runs.control_aware_source_positions_to_visible_runs",
    "runs.hwp_compose_control_to_hwpx_compose",
    "objects.page_hiding_bits_to_hwpx_page_hiding_attributes",
    "objects.footnote_control_to_hwpx_footnote",
    "objects.footnote_autonum_to_hwpx_autonum",
    "styles.style_records_to_hwpx_style_tags",
    "lists.numbering_to_hwpx_numbering",
    "objects.known_layout_ctrl_ids_to_hwpx_ctrl_children",
    "objects.field_ctrl_ids_to_hwpx_field_begin_end",
    "objects.profiled_column_ctrl_to_hwpx_col_pr",
    "objects.hancom_dloc_to_hwpx_col_pr",
    "objects.portable_section_ctrl_to_hwpx_col_pr",
    "objects.hancom_root_tight_wrap_to_top_and_bottom",
    "objects.hancom_root_non_char_top_and_bottom_wrap_to_in_front",
    "objects.portable_root_non_char_top_and_bottom_wrap_to_in_front",
    "objects.portable_child_line_direction_to_hwpx_forward_line",
    "objects.portable_large_group_affine_geometry_to_canonical_hwpx",
    "objects.hancom_unscaled_shape_current_size_to_zero",
    "objects.picture_additional_size_to_hwpx_image_dimension",
    "objects.picture_effect_flags_to_hwpx_shadow_effect",
)

DEFERRED_RULES = (
    "text.para_declared_chars_to_hwpx_text_chars",
    "text.para_text_records_to_hwpx_text_nodes",
    "objects.ctrl_header_to_hwpx_ctrl_tags",
    "objects.column_control_position_semantics",
)

COLUMN_COMPATIBILITY_PROFILES = frozenset({"hancom", "portable"})

_PORTABLE_HFT_FACES = frozenset(
    {
        "#그래픽",
        "#신명조",
        "HCI Hollyhock",
        "HCI Poppy",
        "HCI Tulip",
        "명조",
        "산세리프",
        "신명 견명조",
        "신명 신명조",
        "신명 중고딕",
        "신명 중명조",
        "신명 태고딕",
        "신명 태그래픽",
        "신명 태명조",
        "양재 튼튼B",
        "태 가는 헤드라인D",
        "태 헤드라인T",
        "한양견고딕",
        "한양견명조",
        "한양그래픽",
        "한양신명조",
        "한양중고딕",
    }
)

_HANCOM_HFT_FACES = frozenset(
    {
        "HCI Tulip",
        "명조",
        "산세리프",
        "신명 견명조",
        "신명 세명조",
        "신명 신명조",
        "신명 중명조",
        "태 헤드라인D",
        "태 헤드라인T",
        "한양견고딕",
        "한양신명조",
        "한양중고딕",
    }
)

_HANCOM_HFT_LANGUAGE_FACES = frozenset(
    {
        ("latin", "HCI Poppy"),
    }
)


def build_document_model_from_hwp(
    path: Path,
    *,
    include_text: bool = False,
    compatibility_profile: str = "portable",
) -> dict[str, Any]:
    """Build a public-safe structural model from a HWP file."""

    profile = profile_hwp_file(path)
    binary_payloads = load_hwp_binary_payloads(path)
    body = profile.get("body", {}) if isinstance(profile, dict) else {}
    section_profiles = body.get("sections", []) if isinstance(body, dict) else []
    text_payload = extract_hwp_text(path) if include_text else {"paragraphs": [], "text_char_count": 0}
    compatibility_profile = _normalize_compatibility_profile(compatibility_profile)
    text_by_section = _text_by_section(text_payload.get("paragraphs", []))
    sections = [
        _section_from_profile(
            index,
            section_profile,
            text_by_section.get(index, []),
            include_text,
            compatibility_profile,
        )
        for index, section_profile in enumerate(section_profiles)
    ]
    doc_info = profile.get("doc_info", {}) if isinstance(profile, dict) else {}
    stream_inventory = profile.get("stream_inventory", {}) if isinstance(profile, dict) else {}
    bin_data_count = _as_int(binary_payloads.get("counts", {}).get("binary_count"))
    if not bin_data_count:
        bin_data_count = _as_int(stream_inventory.get("bin_data_stream_count"))
    doc_section_count = _as_int(_dig(doc_info, ("doc_properties", "section_count")))
    doc_tag_counts = doc_info.get("tag_counts", {}) if isinstance(doc_info, dict) else {}
    id_mappings = doc_info.get("id_mappings", {}) if isinstance(doc_info, dict) else {}
    section_count = max(len(sections), doc_section_count)

    while len(sections) < section_count:
        sections.append(_empty_section(len(sections)))

    summary = _summarize_sections(sections)
    summary["section_count"] = section_count
    summary["bin_data_count"] = bin_data_count
    summary["text_char_count"] = _as_int(text_payload.get("text_char_count"))
    control_summary = text_payload.get("control_summary", {}) if isinstance(text_payload, dict) else {}
    summary["text_control_count"] = _as_int(control_summary.get("control_count"))
    summary["text_control_payload_unit_count"] = _as_int(control_summary.get("control_payload_unit_count"))
    summary["text_malformed_control_count"] = _as_int(control_summary.get("malformed_control_count"))
    summary["text_control_code_counts"] = _normalize_count_map(control_summary.get("control_code_counts", {}))
    summary["text_control_id_counts"] = _normalize_count_map(control_summary.get("control_id_counts", {}))
    summary["char_pr_count"] = _style_count(id_mappings, doc_tag_counts, "char_shape", "CHAR_SHAPE")
    summary["para_pr_count"] = _style_count(id_mappings, doc_tag_counts, "para_shape", "PARA_SHAPE")
    summary["style_count"] = _style_count(id_mappings, doc_tag_counts, "style", "STYLE")
    summary["border_fill_count"] = _style_count(id_mappings, doc_tag_counts, "border_fill", "BORDER_FILL")
    summary["tab_pr_count"] = _style_count(id_mappings, doc_tag_counts, "tab_def", "TAB_DEF")
    summary["numbering_count"] = max(
        summary.get("numbering_count", 0),
        _style_count(id_mappings, doc_tag_counts, "numbering", "NUMBERING", minimum=0),
    )
    summary["bullet_count"] = max(
        summary.get("bullet_count", 0),
        _style_count(id_mappings, doc_tag_counts, "bullet", "BULLET", minimum=0),
    )
    style_semantics = _apply_style_compatibility_profile(
        doc_info.get("style_details", {}) if isinstance(doc_info, dict) else {},
        compatibility_profile,
    )
    list_semantics = doc_info.get("list_semantics", {}) if isinstance(doc_info, dict) else {}
    border_fill_semantics = _apply_border_fill_compatibility_profile(
        doc_info.get("border_fill_semantics", {}) if isinstance(doc_info, dict) else {},
        compatibility_profile,
    )
    list_counts = list_semantics.get("counts", {}) if isinstance(list_semantics, dict) else {}
    if list_counts:
        summary["tab_pr_count"] = _as_int(list_counts.get("tab_definition_count"))
        summary["numbering_count"] = _as_int(list_counts.get("numbering_count"))
        summary["bullet_count"] = _as_int(list_counts.get("bullet_count"))
    summary["tab_item_count"] = _as_int(list_counts.get("tab_item_count"))
    summary["numbering_level_count"] = _as_int(list_counts.get("numbering_level_count"))
    summary["numbering_extended_level_count"] = _as_int(list_counts.get("numbering_extended_level_count"))
    summary["list_parse_warning_count"] = _as_int(list_counts.get("parse_warning_count"))
    border_fill_counts = (
        border_fill_semantics.get("counts", {}) if isinstance(border_fill_semantics, dict) else {}
    )
    if border_fill_counts:
        summary["border_fill_count"] = _as_int(border_fill_counts.get("border_fill_count"))
    summary["border_fill_parse_warning_count"] = _as_int(border_fill_counts.get("parse_warning_count"))
    style_counts = style_semantics.get("counts", {}) if isinstance(style_semantics, dict) else {}
    summary["style_semantic_font_face_count"] = _as_int(style_counts.get("font_face_count"))
    summary["style_semantic_char_shape_count"] = _as_int(style_counts.get("char_shape_count"))
    summary["style_semantic_para_shape_count"] = _as_int(style_counts.get("para_shape_count"))
    summary["style_semantic_para_extension_count"] = _as_int(style_counts.get("para_shape_extension_count"))
    summary["style_semantic_para_extension_nonzero_count"] = _as_int(
        style_counts.get("para_shape_extension_nonzero_count")
    )
    summary["style_semantic_font_alternate_face_count"] = _as_int(style_counts.get("font_alternate_face_count"))
    summary["style_semantic_font_default_face_unmapped_count"] = _as_int(
        style_counts.get("font_default_face_unmapped_count")
    )
    summary["style_semantic_font_type_info_count"] = _as_int(style_counts.get("font_type_info_count"))
    summary["style_semantic_font_serif_style_unmapped_count"] = _as_int(
        style_counts.get("font_serif_style_unmapped_count")
    )

    return {
        "schema_version": "owned_hwp_hwpx_document_model.v1",
        "status": "model_built" if str(profile.get("status", "")).startswith("profiled") else "model_with_profile_warning",
        "source_profile_status": profile.get("status", "unknown"),
        "text_extraction_status": text_payload.get("status", "not_requested") if include_text else "not_requested",
        "compatibility_profile": compatibility_profile,
        "rules_applied": list(HIGH_CONFIDENCE_RULES),
        "rules_deferred": list(DEFERRED_RULES),
        "summary": summary,
        "document_defaults": {
            "font_family": "HancomBatang",
            "language": "ko",
            "page_width_hwpunit": 59528,
            "page_height_hwpunit": 84188,
            "margin_hwpunit": 8504,
        },
        "style_semantics": style_semantics,
        "list_semantics": list_semantics,
        "border_fill_semantics": border_fill_semantics,
        "binary_semantics": public_binary_semantics(binary_payloads),
        "_binary_payloads": binary_payloads.get("items", []),
        "sections": sections,
    }


def _section_from_profile(
    index: int,
    profile: dict[str, Any],
    paragraph_texts: list[dict[str, Any]],
    include_text: bool,
    compatibility_profile: str,
) -> dict[str, Any]:
    para = profile.get("para_header_signals", {})
    layout = profile.get("layout_signals", {})
    tag_counts = profile.get("tag_counts", {})
    paragraph_count = _as_int(para.get("paragraph_count"))
    line_segment_count = _as_int(layout.get("line_segment_count"))
    table_count = _as_int(layout.get("table_record_count"))
    table_row_count = _as_int(layout.get("table_row_count"))
    table_cell_count = _as_int(layout.get("table_cell_count"))
    sub_list_count = max(_as_int(layout.get("list_header_record_count")), table_cell_count)
    picture_count = _as_int(layout.get("picture_record_count"))
    page_def_count = _as_int(layout.get("page_def_record_count"))
    bullet_count = _as_int(tag_counts.get("BULLET"))
    numbering_count = _as_int(tag_counts.get("NUMBERING"))
    layout_details = profile.get("layout_details", {}) if isinstance(profile.get("layout_details"), dict) else {}
    line_segment_semantics = _fit_line_segment_semantics(
        layout_details.get("line_segment_semantics", {}),
        paragraph_count,
    )
    semantic_line_segment_count = _as_int(
        line_segment_semantics.get("counts", {}).get("segment_count")
    )
    if semantic_line_segment_count or line_segment_count == 0:
        line_segment_count = semantic_line_segment_count
    page_definitions = _fit_page_definitions(layout_details.get("page_definitions", []), page_def_count)
    section_semantics = (
        layout_details.get("section_semantics", {})
        if isinstance(layout_details.get("section_semantics"), dict)
        else {}
    )
    section_semantics = _apply_section_compatibility_profile(
        section_semantics,
        compatibility_profile,
    )
    section_page = section_semantics.get("page", {}) if isinstance(section_semantics.get("page"), dict) else {}
    if section_page and page_definitions:
        page_definitions[0] = {"page_def_index": 0, **section_page}
    raw_table_semantics = (
        layout_details.get("table_semantics", {})
        if isinstance(layout_details.get("table_semantics"), dict)
        else {}
    )
    raw_object_semantics = (
        profile.get("object_semantics", {})
        if isinstance(profile.get("object_semantics"), dict)
        else {}
    )
    object_shapes = [dict(value) for value in raw_object_semantics.get("shapes", []) if isinstance(value, dict)]
    object_counts = raw_object_semantics.get("counts", {}) if isinstance(raw_object_semantics, dict) else {}
    picture_count = _as_int(object_counts.get("picture_count")) or picture_count
    table_shapes = _fit_table_shapes(raw_table_semantics.get("tables", []), table_count)
    _apply_table_compatibility_profile(table_shapes, compatibility_profile)
    _apply_object_compatibility_profile(object_shapes, compatibility_profile)
    layout_control_child_counts = _normalize_count_map(layout_details.get("layout_control_child_counts", {}))
    control_id_counts = _normalize_count_map(layout_details.get("control_id_counts", {}))
    portable_col_pr_count = _as_int(control_id_counts.get("dces"))
    hancom_col_pr_count = _as_int(control_id_counts.get("dloc")) or portable_col_pr_count
    selected_col_pr_count = (
        hancom_col_pr_count if compatibility_profile == "hancom" else portable_col_pr_count
    )
    if selected_col_pr_count:
        layout_control_child_counts["colPr"] = selected_col_pr_count
    raw_paragraph_styles = profile.get("paragraph_style_runs", [])
    paragraph_styles = _fit_paragraph_styles(raw_paragraph_styles, paragraph_count)
    if compatibility_profile != "hancom":
        for paragraph_style in paragraph_styles:
            paragraph_style["paragraph_id"] = 0
    paragraph_payloads = _fit_paragraph_payloads(paragraph_texts, paragraph_count) if include_text else []
    paragraph_control_groups = [
        [
            token
            for token in payload.get("tokens", [])
            if isinstance(token, dict) and token.get("type") == "control"
        ]
        for payload in paragraph_payloads
    ]
    _attach_compose_control_semantics(paragraph_control_groups, raw_paragraph_styles)
    _attach_page_hiding_control_semantics(paragraph_control_groups, raw_paragraph_styles)
    _attach_footnote_control_semantics(paragraph_control_groups, raw_paragraph_styles)
    if include_text and compatibility_profile != "hancom":
        line_segment_semantics = map_hwp_line_segment_text_positions(
            line_segment_semantics,
            paragraph_control_groups,
        )
    if include_text:
        paragraph_styles = [
            _with_visible_run_positions(style, paragraph_payloads[index])
            for index, style in enumerate(paragraph_styles)
        ]
    char_shape_run_count = sum(_paragraph_run_count(item) for item in paragraph_styles)
    table_row_count = sum(_as_int(item.get("row_count")) for item in table_shapes) if table_shapes else table_row_count
    table_cell_count = sum(_as_int(item.get("cell_count")) for item in table_shapes) if table_shapes else table_cell_count
    known_layout_control_count = sum(layout_control_child_counts.values())
    contained_paragraph_indexes = {
        _as_int(paragraph_index)
        for table in table_shapes
        for container in [
            *(table.get("cells", []) if isinstance(table.get("cells"), list) else []),
            *([table.get("caption")] if isinstance(table.get("caption"), dict) else []),
        ]
        if isinstance(container, dict)
        for paragraph_index in container.get("paragraph_indexes", [])
    }
    shape_list_record_indexes = {
        _signed_int(shape.get("draw_text", {}).get("_record_index"), -1)
        for shape in object_shapes
        if isinstance(shape.get("draw_text"), dict)
    }
    raw_embedded_sub_lists = [
        value
        for value in raw_table_semantics.get("embedded_sub_lists", [])
        if isinstance(value, dict) and _signed_int(value.get("_record_index"), -1) not in shape_list_record_indexes
    ]
    embedded_paragraph_groups = _normalize_embedded_sub_lists(
        raw_embedded_sub_lists,
        paragraph_count,
    )
    embedded_paragraph_indexes = {
        paragraph_index
        for group in embedded_paragraph_groups
        for paragraph_index in group["paragraph_indexes"]
    }
    shape_paragraph_indexes = {
        _as_int(paragraph_index)
        for shape in object_shapes
        if isinstance(shape.get("draw_text"), dict)
        for paragraph_index in shape.get("draw_text", {}).get("paragraph_indexes", [])
    }
    for table in table_shapes:
        containers = [
            *(table.get("cells", []) if isinstance(table.get("cells"), list) else []),
            *([table.get("caption")] if isinstance(table.get("caption"), dict) else []),
        ]
        for container in containers:
            if isinstance(container, dict):
                container["render_paragraph_indexes"] = [
                    _as_int(paragraph_index)
                    for paragraph_index in container.get("paragraph_indexes", [])
                    if _as_int(paragraph_index) not in embedded_paragraph_indexes
                    and _as_int(paragraph_index) not in shape_paragraph_indexes
                ]
    root_paragraph_indexes = [
        paragraph_index
        for paragraph_index in range(paragraph_count)
        if paragraph_index not in contained_paragraph_indexes
        and paragraph_index not in embedded_paragraph_indexes
        and paragraph_index not in shape_paragraph_indexes
    ]
    _assign_sub_lists(
        table_shapes,
        max(0, sub_list_count - len(embedded_paragraph_groups) - _as_int(object_counts.get("draw_text_count"))),
    )

    section = {
        "section_ref": f"section_{index}",
        "section_index": index,
        "compatibility_profile": compatibility_profile,
        "paragraph_count": paragraph_count,
        "char_shape_run_count": char_shape_run_count,
        "line_segment_count": line_segment_count,
        "table_count": table_count,
        "table_row_count": table_row_count,
        "table_cell_count": table_cell_count,
        "sub_list_count": sub_list_count,
        "picture_count": picture_count,
        "shape_count": _as_int(object_counts.get("shape_count")),
        "root_object_count": _as_int(object_counts.get("root_object_count")),
        "shape_draw_text_count": _as_int(object_counts.get("draw_text_count")),
        "page_def_count": page_def_count,
        "bullet_count": bullet_count,
        "numbering_count": numbering_count,
        "control_anchor_count": _as_int(layout.get("ctrl_header_record_count")),
        "known_layout_control_count": known_layout_control_count,
        "candidate_col_pr_control_count": _as_int(layout.get("candidate_col_pr_control_count")),
        "column_control_counts": {
            "portable": portable_col_pr_count,
            "hancom": hancom_col_pr_count,
            "selected": selected_col_pr_count,
        },
        "expected_hwpx": {
            "p": paragraph_count,
            "run": char_shape_run_count,
            "lineseg": line_segment_count,
            "tbl": table_count,
            "tr": table_row_count,
            "tc": table_cell_count,
            "subList": sub_list_count,
            "pic": picture_count,
            "pagePr": page_def_count,
            "secPr": page_def_count,
            "ctrl": known_layout_control_count,
        },
        "page_definitions": page_definitions,
        "section_semantics": section_semantics,
        "line_segment_semantics": line_segment_semantics,
        "table_shapes": table_shapes,
        "table_semantics_status": str(raw_table_semantics.get("status", "not_parsed")),
        "object_shapes": object_shapes,
        "object_semantics_status": str(raw_object_semantics.get("status", "not_parsed")),
        "embedded_paragraph_groups": embedded_paragraph_groups,
        "root_paragraph_indexes": root_paragraph_indexes,
        "layout_control_child_counts": layout_control_child_counts,
        "paragraph_styles": paragraph_styles,
    }
    if include_text:
        section["paragraph_texts"] = [str(item.get("text", "")) for item in paragraph_payloads]
        section["paragraph_controls"] = paragraph_control_groups
    return section


def _empty_section(index: int) -> dict[str, Any]:
    return {
        "section_ref": f"section_{index}",
        "section_index": index,
        "compatibility_profile": "portable",
        "paragraph_count": 1,
        "char_shape_run_count": 1,
        "line_segment_count": 0,
        "table_count": 0,
        "table_row_count": 0,
        "table_cell_count": 0,
        "sub_list_count": 0,
        "picture_count": 0,
        "shape_count": 0,
        "root_object_count": 0,
        "shape_draw_text_count": 0,
        "page_def_count": 1,
        "bullet_count": 0,
        "numbering_count": 0,
        "control_anchor_count": 0,
        "known_layout_control_count": 0,
        "candidate_col_pr_control_count": 0,
        "column_control_counts": {"portable": 0, "hancom": 0, "selected": 0},
        "expected_hwpx": {
            "p": 1,
            "run": 1,
            "lineseg": 0,
            "tbl": 0,
            "tr": 0,
            "tc": 0,
            "subList": 0,
            "pic": 0,
            "pagePr": 1,
            "secPr": 1,
            "ctrl": 0,
        },
        "page_definitions": [_default_page_definition(0)],
        "section_semantics": {},
        "line_segment_semantics": {
            "status": "parsed",
            "paragraphs": [{"paragraph_index": 0, "declared_count": 0, "segments": []}],
            "counts": {
                "paragraph_count": 1,
                "declared_segment_count": 0,
                "segment_count": 0,
                "declared_count_mismatch_count": 0,
                "remainder_bytes": 0,
            },
        },
        "table_shapes": [],
        "table_semantics_status": "empty",
        "object_shapes": [],
        "object_semantics_status": "empty",
        "embedded_paragraph_groups": [],
        "root_paragraph_indexes": [0],
        "layout_control_child_counts": {},
        "paragraph_styles": [_empty_paragraph_style(0)],
    }


def _text_by_section(paragraphs: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    result: dict[int, list[dict[str, Any]]] = {}
    for item in paragraphs:
        section_index = _as_int(item.get("section_index"))
        result.setdefault(section_index, []).append(
            {
                "text": str(item.get("text", "")),
                "tokens": [token for token in item.get("tokens", []) if isinstance(token, dict)],
                "source_to_visible": [_as_int(position) for position in item.get("source_to_visible", [])],
            }
        )
    return result


def _fit_paragraph_payloads(values: list[dict[str, Any]], paragraph_count: int) -> list[dict[str, Any]]:
    fitted = [
        {
            "text": str(item.get("text", "")),
            "tokens": [token for token in item.get("tokens", []) if isinstance(token, dict)],
            "source_to_visible": [_as_int(position) for position in item.get("source_to_visible", [])],
        }
        for item in values[:paragraph_count]
        if isinstance(item, dict)
    ]
    while len(fitted) < paragraph_count:
        fitted.append({"text": "", "tokens": [], "source_to_visible": [0]})
    return fitted


def _attach_compose_control_semantics(
    paragraph_control_groups: list[list[dict[str, Any]]],
    paragraph_styles: Any,
) -> None:
    styles = paragraph_styles if isinstance(paragraph_styles, list) else []
    for paragraph_index, controls in enumerate(paragraph_control_groups):
        style = styles[paragraph_index] if paragraph_index < len(styles) else {}
        compose_controls = [
            value
            for value in style.get("compose_controls", [])
            if isinstance(value, dict) and value.get("status") == "parsed"
        ] if isinstance(style, dict) else []
        compose_index = 0
        for control_index, control in enumerate(controls):
            if str(control.get("control_id", "")) != "spct":
                continue
            if compose_index >= len(compose_controls):
                break
            controls[control_index] = {
                **control,
                "compose": compose_controls[compose_index],
            }
            compose_index += 1


def _attach_page_hiding_control_semantics(
    paragraph_control_groups: list[list[dict[str, Any]]],
    paragraph_styles: Any,
) -> None:
    styles = paragraph_styles if isinstance(paragraph_styles, list) else []
    for paragraph_index, controls in enumerate(paragraph_control_groups):
        style = styles[paragraph_index] if paragraph_index < len(styles) else {}
        page_hiding_controls = [
            value
            for value in style.get("page_hiding_controls", [])
            if isinstance(value, dict) and value.get("status") == "parsed"
        ] if isinstance(style, dict) else []
        page_hiding_index = 0
        for control_index, control in enumerate(controls):
            if str(control.get("control_id", "")) != "dhgp":
                continue
            if page_hiding_index >= len(page_hiding_controls):
                break
            controls[control_index] = {
                **control,
                "page_hiding": page_hiding_controls[page_hiding_index],
            }
            page_hiding_index += 1


def _attach_footnote_control_semantics(
    paragraph_control_groups: list[list[dict[str, Any]]],
    paragraph_styles: Any,
) -> None:
    styles = paragraph_styles if isinstance(paragraph_styles, list) else []
    for paragraph_index, controls in enumerate(paragraph_control_groups):
        style = styles[paragraph_index] if paragraph_index < len(styles) else {}
        if not isinstance(style, dict):
            continue
        typed_controls = {
            "  nf": [
                value
                for value in style.get("footnote_controls", [])
                if isinstance(value, dict) and value.get("status") == "parsed"
            ],
            "onta": [
                value
                for value in style.get("auto_number_controls", [])
                if isinstance(value, dict) and value.get("status") == "parsed"
            ],
        }
        indexes = {"  nf": 0, "onta": 0}
        for control_index, control in enumerate(controls):
            control_id = str(control.get("control_id", ""))
            if control_id not in typed_controls:
                continue
            typed_index = indexes[control_id]
            if typed_index >= len(typed_controls[control_id]):
                continue
            key = "footnote" if control_id == "  nf" else "auto_number"
            controls[control_index] = {
                **control,
                key: typed_controls[control_id][typed_index],
            }
            indexes[control_id] += 1


def _with_visible_run_positions(style: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    source_to_visible = payload.get("source_to_visible", [])
    if not isinstance(source_to_visible, list) or not source_to_visible:
        return style
    visible_limit = len(str(payload.get("text", "")))
    runs = []
    previous = 0
    for item in style.get("char_shape_runs", []):
        source_start = _as_int(item.get("start"))
        boundary = min(source_start, len(source_to_visible) - 1)
        visible_start = min(visible_limit, max(previous, _as_int(source_to_visible[boundary])))
        runs.append({**item, "source_start": source_start, "visible_start": visible_start})
        previous = visible_start
    return {**style, "char_shape_runs": runs}


def _normalize_compatibility_profile(value: Any) -> str:
    profile = str(value or "portable").strip().lower()
    if profile not in COLUMN_COMPATIBILITY_PROFILES:
        raise ValueError(f"unsupported_compatibility_profile:{profile}")
    return profile


def _apply_border_fill_compatibility_profile(
    value: Any,
    compatibility_profile: str,
) -> dict[str, Any]:
    semantics = deepcopy(value) if isinstance(value, dict) else {}
    if compatibility_profile != "portable":
        return semantics
    for border_fill in semantics.get("border_fills", []):
        if not isinstance(border_fill, dict):
            continue
        fill = border_fill.get("fill")
        if not isinstance(fill, dict) or fill.get("type") != "solid":
            continue
        face_color = str(fill.get("face_color", ""))
        black_no_effect = (
            face_color == "#000000"
            and str(fill.get("hatch_color", "")) == "#FF000000"
            and fill.get("hatch_style") is None
            and _as_int(fill.get("alpha")) == 0
        )
        if face_color == "none" or black_no_effect:
            border_fill["fill"] = {"type": "none"}
    return semantics


def _fit_paragraph_styles(values: list[dict[str, Any]], paragraph_count: int) -> list[dict[str, Any]]:
    fitted = [_normalize_paragraph_style(index, item) for index, item in enumerate(values[:paragraph_count])]
    while len(fitted) < paragraph_count:
        fitted.append(_empty_paragraph_style(len(fitted)))
    return fitted


def _fit_line_segment_semantics(value: Any, paragraph_count: int) -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    raw_paragraphs = source.get("paragraphs", []) if isinstance(source.get("paragraphs"), list) else []
    paragraphs = []
    declared_total = 0
    segment_total = 0
    mismatch_count = 0
    for index in range(paragraph_count):
        raw = raw_paragraphs[index] if index < len(raw_paragraphs) and isinstance(raw_paragraphs[index], dict) else {}
        segments = [
            _normalize_line_segment(item)
            for item in raw.get("segments", [])
            if isinstance(item, dict)
        ]
        declared = _as_int(raw.get("declared_count"))
        declared_total += declared
        segment_total += len(segments)
        mismatch_count += int(declared != len(segments))
        paragraphs.append(
            {
                "paragraph_index": index,
                "declared_count": declared,
                "segments": segments,
            }
        )
    remainder_bytes = _as_int(source.get("counts", {}).get("remainder_bytes"))
    status = "parsed"
    if remainder_bytes:
        status = "trailing_bytes"
    elif mismatch_count:
        status = "declared_count_mismatch"
    return {
        "status": status,
        "paragraphs": paragraphs,
        "counts": {
            "paragraph_count": len(paragraphs),
            "declared_segment_count": declared_total,
            "segment_count": segment_total,
            "declared_count_mismatch_count": mismatch_count,
            "remainder_bytes": remainder_bytes,
        },
    }


def _normalize_line_segment(value: dict[str, Any]) -> dict[str, int]:
    return {
        "textpos": _as_int(value.get("textpos")),
        "vertpos": _signed_int(value.get("vertpos")),
        "vertsize": _signed_int(value.get("vertsize")),
        "textheight": _signed_int(value.get("textheight")),
        "baseline": _signed_int(value.get("baseline")),
        "spacing": _signed_int(value.get("spacing")),
        "horzpos": _signed_int(value.get("horzpos")),
        "horzsize": _signed_int(value.get("horzsize")),
        "flags": _as_int(value.get("flags")),
    }


def _fit_page_definitions(values: Any, page_def_count: int) -> list[dict[str, Any]]:
    raw_values = values if isinstance(values, list) else []
    fitted = [_normalize_page_definition(index, item) for index, item in enumerate(raw_values[:page_def_count])]
    while len(fitted) < page_def_count:
        fitted.append(_default_page_definition(len(fitted)))
    return fitted


def _normalize_page_definition(index: int, value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    margin = value.get("margin", {}) if isinstance(value.get("margin"), dict) else {}
    return {
        "page_def_index": index,
        "width": _bounded_hwpunit(value.get("width"), 59528),
        "height": _bounded_hwpunit(value.get("height"), 84188),
        "margin": {
            "left": _bounded_hwpunit(margin.get("left"), 8504),
            "right": _bounded_hwpunit(margin.get("right"), 8504),
            "top": _bounded_hwpunit(margin.get("top"), 8504),
            "bottom": _bounded_hwpunit(margin.get("bottom"), 8504),
            "header": _bounded_hwpunit(margin.get("header"), 5668),
            "footer": _bounded_hwpunit(margin.get("footer"), 5668),
            "gutter": _bounded_hwpunit(margin.get("gutter"), 0),
        },
    }


def _default_page_definition(index: int) -> dict[str, Any]:
    return {
        "page_def_index": index,
        "width": 59528,
        "height": 84188,
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


def _fit_table_shapes(values: Any, table_count: int) -> list[dict[str, Any]]:
    raw_values = values if isinstance(values, list) else []
    shapes = [_normalize_table_shape(index, item) for index, item in enumerate(raw_values[:table_count])]
    while len(shapes) < table_count:
        shapes.append(_normalize_table_shape(len(shapes), {}))
    return shapes


def _apply_table_compatibility_profile(
    shapes: list[dict[str, Any]],
    compatibility_profile: str,
) -> None:
    if compatibility_profile != "portable":
        return
    for table in shapes:
        cells = [cell for cell in table.get("cells", []) if isinstance(cell, dict)]
        table["repeat_header"] = bool(table.get("repeat_header")) and any(
            bool(cell.get("header")) for cell in cells
        )
        object_value = dict(table.get("object", {})) if isinstance(table.get("object"), dict) else {}
        position = (
            dict(object_value.get("position", {}))
            if isinstance(object_value.get("position"), dict)
            else {}
        )
        if bool(position.get("treat_as_char")):
            position["flow_with_text"] = False
            position["horz_rel_to"] = "COLUMN"
        object_value["position"] = position
        table["object"] = object_value


def _apply_object_compatibility_profile(
    shapes: list[dict[str, Any]],
    compatibility_profile: str,
) -> None:
    if compatibility_profile == "portable":
        _canonicalize_portable_large_group_geometry(shapes)
    for shape in shapes:
        element = shape.get("element") if isinstance(shape.get("element"), dict) else {}
        common = shape.get("common") if isinstance(shape.get("common"), dict) else None
        position = (
            common.get("position")
            if common is not None and isinstance(common.get("position"), dict)
            else {}
        )
        if (
            compatibility_profile == "portable"
            and common is None
            and str(shape.get("kind", "")).lower() == "line"
            and isinstance(shape.get("specific"), dict)
        ):
            shape["specific"]["reverse"] = False
        if (
            common is not None
            and compatibility_profile == "hancom"
            and _as_int(element.get("group_level")) == 0
            and str(common.get("text_wrap", "")).upper() == "TIGHT"
        ):
            common["text_wrap"] = "TOP_AND_BOTTOM"
        elif (
            common is not None
            and _as_int(element.get("group_level")) == 0
            and str(common.get("text_wrap", "")).upper() == "TOP_AND_BOTTOM"
            and not bool(position.get("treat_as_char"))
        ):
            common["text_wrap"] = "IN_FRONT_OF_TEXT"
            if compatibility_profile == "portable":
                position["allow_overlap"] = False
        if compatibility_profile != "hancom":
            continue
        current_size = (
            element.get("current_size")
            if isinstance(element.get("current_size"), dict)
            else {}
        )
        original_size = (
            element.get("original_size")
            if isinstance(element.get("original_size"), dict)
            else {}
        )
        if (
            str(shape.get("kind", "")).lower() != "ole"
            and current_size
            and current_size == original_size
        ):
            element["current_size"] = {"width": 0, "height": 0}


def _canonicalize_portable_large_group_geometry(
    shapes: list[dict[str, Any]],
) -> None:
    children_by_parent: dict[int, list[dict[str, Any]]] = {}
    for shape in shapes:
        parent_index = _signed_int(shape.get("parent_shape_index"), -1)
        if parent_index >= 0:
            children_by_parent.setdefault(parent_index, []).append(shape)
    for children in children_by_parent.values():
        affine_children = [
            shape
            for shape in children
            if len(_shape_matrices(shape)) == 5
        ]
        has_extreme_affine = any(
            _large_group_affine_is_extreme(_shape_matrices(shape)[3])
            for shape in affine_children
        )
        if (
            len(children) < 20
            or len(affine_children) != len(children)
            or not has_extreme_affine
        ):
            continue
        for shape in affine_children:
            _canonicalize_portable_group_child(shape)


def _shape_matrices(shape: dict[str, Any]) -> list[dict[str, Any]]:
    element = shape.get("element") if isinstance(shape.get("element"), dict) else {}
    values = element.get("matrices", []) if isinstance(element, dict) else []
    return [value for value in values if isinstance(value, dict)]


def _large_group_affine_is_extreme(matrix: dict[str, Any]) -> bool:
    values = matrix.get("values", []) if isinstance(matrix.get("values"), list) else []
    scale_x = _float_at(values, 0)
    scale_y = _float_at(values, 4)
    return (
        scale_x < 0
        or scale_y < 0
        or abs(scale_x) > 100
        or abs(scale_y) > 100
    )


def _canonicalize_portable_group_child(shape: dict[str, Any]) -> None:
    element = shape.get("element") if isinstance(shape.get("element"), dict) else {}
    matrices = _shape_matrices(shape)
    if len(matrices) != 5:
        return
    translation = matrices[0].get("values", [])
    scaling = matrices[3].get("values", [])
    scale_x = _float_at(scaling, 0)
    scale_y = _float_at(scaling, 4)
    original = element.get("original_size", {})
    current = element.get("current_size", {})
    width = _portable_geometry_size(_as_int(original.get("width")), scale_x)
    height = _portable_geometry_size(_as_int(original.get("height")), scale_y)
    current_width = _portable_geometry_size(_as_int(current.get("width")), scale_x)
    current_height = _portable_geometry_size(_as_int(current.get("height")), scale_y)
    offset_x = _float_at(translation, 2) + _float_at(scaling, 2)
    offset_y = _float_at(translation, 5) + _float_at(scaling, 5)
    if scale_x < 0:
        offset_x -= width
    if scale_y < 0:
        offset_y -= height
    x = _portable_geometry_round(offset_x)
    y = _portable_geometry_round(offset_y)
    flip_x = scale_x < 0
    flip_y = scale_y < 0
    element["offset"] = {"x": x, "y": y}
    element["original_size"] = {"width": width, "height": height}
    element["current_size"] = {
        "width": current_width,
        "height": current_height,
    }
    element["flip"] = {"horizontal": flip_y, "vertical": flip_x}
    rotation = (
        dict(element.get("rotation", {}))
        if isinstance(element.get("rotation"), dict)
        else {}
    )
    rotation.update(
        {
            "angle": 180 if flip_x or flip_y else 0,
            "center_x": _nearest_int(x + width / 2.0),
            "center_y": _nearest_int(y + height / 2.0),
        }
    )
    element["rotation"] = rotation
    flip_matrix = [
        -1.0 if flip_x else 1.0,
        0.0,
        float(width) if flip_x else 0.0,
        0.0,
        -1.0 if flip_y else 1.0,
        float(height) if flip_y else 0.0,
    ]
    identity = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    element["matrices"] = [
        {"type": "transMatrix", "values": [1.0, 0.0, float(x), 0.0, 1.0, float(y)]},
        {"type": "scaMatrix", "values": list(identity)},
        {"type": "rotMatrix", "values": flip_matrix},
        {"type": "scaMatrix", "values": list(identity)},
        {"type": "rotMatrix", "values": list(identity)},
    ]
    kind = str(shape.get("kind", "")).lower()
    specific = shape.get("specific") if isinstance(shape.get("specific"), dict) else {}
    if kind == "rect":
        specific["points"] = [
            {"x": 0, "y": 0},
            {"x": width, "y": 0},
            {"x": width, "y": height},
            {"x": 0, "y": height},
        ]
    elif kind == "line":
        specific.update(
            {
                "start": {"x": 0, "y": 0},
                "end": {"x": width, "y": height},
                "reverse": False,
            }
        )
        element["instance_id"] = 0
    elif kind == "polygon":
        specific["points"] = [
            {
                "x": _portable_geometry_round(_signed_int(point.get("x")) * abs(scale_x)),
                "y": _portable_geometry_round(_signed_int(point.get("y")) * abs(scale_y)),
            }
            for point in specific.get("points", [])
            if isinstance(point, dict)
        ]
    if isinstance(shape.get("line_shape"), dict):
        line_shape = shape["line_shape"]
        line_shape["width"] = _portable_geometry_round(_signed_int(line_shape.get("width")))
        line_shape["head_fill"] = False
        line_shape["tail_fill"] = False
        line_shape["head_size"] = "SMALL_SMALL"
        line_shape["tail_size"] = "SMALL_SMALL"


def _portable_geometry_size(value: int, scale: float) -> int:
    if value <= 0:
        return 0
    return max(1, abs(_portable_geometry_round(value * abs(scale))))


def _portable_geometry_round(value: float) -> int:
    sign = -1 if value < 0 else 1
    return sign * int(abs(value) / 5.0 + 0.5) * 5


def _nearest_int(value: float) -> int:
    sign = -1 if value < 0 else 1
    return sign * int(abs(value) + 0.5)


def _float_at(values: Any, index: int) -> float:
    if not isinstance(values, list) or index >= len(values):
        return 0.0
    try:
        return float(values[index])
    except (TypeError, ValueError):
        return 0.0


def _apply_section_compatibility_profile(
    value: dict[str, Any],
    compatibility_profile: str,
) -> dict[str, Any]:
    semantics = dict(value)
    page_borders = [
        dict(item) for item in semantics.get("page_borders", []) if isinstance(item, dict)
    ]
    if compatibility_profile == "portable" and page_borders:
        while len(page_borders) < 3:
            page_borders.append({})
        page_borders[1] = _portable_page_border("EVEN")
        page_borders[2] = _portable_page_border("ODD")
    semantics["page_borders"] = page_borders
    return semantics


def _apply_style_compatibility_profile(
    value: Any,
    compatibility_profile: str,
) -> dict[str, Any]:
    semantics = dict(value) if isinstance(value, dict) else {}
    para_shapes = [
        dict(item)
        for item in semantics.get("para_shapes", [])
        if isinstance(item, dict)
    ]
    if compatibility_profile == "portable":
        for shape in para_shapes:
            shape["snap_to_grid"] = True
    hft_faces = (
        _PORTABLE_HFT_FACES
        if compatibility_profile == "portable"
        else _HANCOM_HFT_FACES
    )
    font_faces = []
    for group in semantics.get("font_faces", []):
        if not isinstance(group, dict):
            continue
        rendered_group = dict(group)
        language = str(group.get("language", "")).lower()
        rendered_group["fonts"] = [
            {
                **font,
                "type": "HFT"
                if str(font.get("face", "")) in hft_faces
                or (
                    compatibility_profile == "hancom"
                    and (language, str(font.get("face", "")))
                    in _HANCOM_HFT_LANGUAGE_FACES
                )
                else str(font.get("type", "TTF")),
            }
            for font in group.get("fonts", [])
            if isinstance(font, dict)
        ]
        font_faces.append(rendered_group)
    semantics["para_shapes"] = para_shapes
    semantics["font_faces"] = font_faces
    return semantics


def _portable_page_border(border_type: str) -> dict[str, Any]:
    return {
        "type": border_type,
        "border_fill_id_ref": 0,
        "text_border": "CONTENT",
        "header_inside": False,
        "footer_inside": False,
        "fill_area": "PAPER",
        "offset": {"left": 0, "right": 0, "top": 0, "bottom": 0},
    }


def _normalize_table_shape(index: int, value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    row_count = max(1, _as_int(value.get("row_count")))
    column_count = max(1, _as_int(value.get("column_count")))
    raw_counts = [
        max(0, _as_int(item))
        for item in value.get("row_cell_counts", [])
    ] if isinstance(value.get("row_cell_counts"), list) else []
    row_cell_counts = raw_counts[:row_count]
    while len(row_cell_counts) < row_count:
        row_cell_counts.append(column_count)
    if sum(row_cell_counts) <= 0:
        row_cell_counts = [column_count for _ in range(row_count)]
    normalized = {
        "table_index": index,
        "row_count": row_count,
        "column_count": column_count,
        "cell_count": sum(row_cell_counts),
        "sub_list_count": sum(row_cell_counts),
        "row_cell_counts": row_cell_counts,
        "parse_status": str(value.get("parse_status", "model_normalized")),
    }
    if isinstance(value.get("cells"), list):
        normalized.update(
            {
                key: item
                for key, item in value.items()
                if key not in {"table_index", "row_count", "column_count", "cell_count", "row_cell_counts"}
            }
        )
        normalized["table_index"] = index
        normalized["row_count"] = row_count
        normalized["column_count"] = column_count
        normalized["cell_count"] = sum(row_cell_counts)
        normalized["row_cell_counts"] = row_cell_counts
        normalized["cells"] = [dict(cell) for cell in value.get("cells", []) if isinstance(cell, dict)]
        if isinstance(value.get("caption"), dict):
            normalized["caption"] = dict(value["caption"])
    return normalized


def _assign_sub_lists(shapes: list[dict[str, Any]], sub_list_count: int) -> None:
    if not shapes:
        return
    total_cells = sum(_as_int(shape.get("cell_count")) for shape in shapes)
    total_captions = sum(int(isinstance(shape.get("caption"), dict)) for shape in shapes)
    primary_count = total_cells + total_captions
    target = max(primary_count, _as_int(sub_list_count))
    extras = max(0, target - primary_count)
    for index, shape in enumerate(shapes):
        cells = _as_int(shape.get("cell_count"))
        captions = int(isinstance(shape.get("caption"), dict))
        extra = extras // len(shapes) + (1 if index < extras % len(shapes) else 0)
        shape["sub_list_count"] = cells + captions + extra
        shape["extra_sub_list_count"] = extra


def _normalize_embedded_sub_lists(
    values: Any,
    paragraph_count: int,
) -> list[dict[str, Any]]:
    result = []
    for value in values if isinstance(values, list) else []:
        if not isinstance(value, dict):
            continue
        anchor = _signed_int(value.get("anchor_paragraph_index"), -1)
        indexes = [
            _as_int(paragraph_index)
            for paragraph_index in value.get("paragraph_indexes", [])
            if 0 <= _as_int(paragraph_index) < paragraph_count
        ]
        if anchor < 0 or not indexes:
            continue
        result.append(
            {
                "anchor_paragraph_index": anchor,
                "paragraph_indexes": indexes,
                "record_level": _as_int(value.get("record_level")),
                "order_key": min(indexes),
            }
        )
    return result


def _normalize_count_map(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): _as_int(count)
        for key, count in sorted(value.items())
        if _as_int(count) > 0
    }


def _normalize_paragraph_style(index: int, value: dict[str, Any]) -> dict[str, Any]:
    declared_runs = _as_int(value.get("declared_char_shape_run_count"))
    actual_runs = _as_int(value.get("actual_char_shape_run_count"))
    runs = [
        {
            "start": _as_int(item.get("start")),
            "char_shape_id": _as_int(item.get("char_shape_id")),
        }
        for item in value.get("char_shape_runs", [])
        if isinstance(item, dict)
    ]
    return {
        "paragraph_index": index,
        "record_level": _as_int(value.get("record_level")),
        "declared_char_count": _as_int(value.get("declared_char_count")),
        "char_count_high_bit": bool(value.get("char_count_high_bit")),
        "merged": bool(value.get("merged")),
        "section_break": bool(value.get("section_break")),
        "column_definition_break": bool(value.get("column_definition_break")),
        "page_break": bool(value.get("page_break")),
        "column_break": bool(value.get("column_break")),
        "para_shape_id": _as_int(value.get("para_shape_id")),
        "style_id": _as_int(value.get("style_id")),
        "paragraph_id": _as_int(value.get("paragraph_id")),
        "control_mask_nonzero": bool(value.get("control_mask_nonzero")),
        "declared_char_shape_run_count": declared_runs,
        "actual_char_shape_run_count": actual_runs,
        "char_shape_runs": runs,
    }


def _empty_paragraph_style(index: int) -> dict[str, Any]:
    return {
        "paragraph_index": index,
        "record_level": 0,
        "declared_char_count": 0,
        "char_count_high_bit": False,
        "merged": False,
        "section_break": False,
        "column_definition_break": False,
        "page_break": False,
        "column_break": False,
        "para_shape_id": 0,
        "style_id": 0,
        "paragraph_id": 0,
        "control_mask_nonzero": False,
        "declared_char_shape_run_count": 1,
        "actual_char_shape_run_count": 0,
        "char_shape_runs": [],
    }


def _paragraph_run_count(value: dict[str, Any]) -> int:
    return max(
        1,
        len(value.get("char_shape_runs", [])),
        _as_int(value.get("actual_char_shape_run_count")),
        _as_int(value.get("declared_char_shape_run_count")),
    )


def _summarize_sections(sections: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "section_count": len(sections),
        "paragraph_count": sum(_as_int(section.get("paragraph_count")) for section in sections),
        "char_shape_run_count": sum(_as_int(section.get("char_shape_run_count")) for section in sections),
        "line_segment_count": sum(_as_int(section.get("line_segment_count")) for section in sections),
        "table_count": sum(_as_int(section.get("table_count")) for section in sections),
        "table_row_count": sum(_as_int(section.get("table_row_count")) for section in sections),
        "table_cell_count": sum(_as_int(section.get("table_cell_count")) for section in sections),
        "sub_list_count": sum(_as_int(section.get("sub_list_count")) for section in sections),
        "picture_count": sum(_as_int(section.get("picture_count")) for section in sections),
        "shape_count": sum(_as_int(section.get("shape_count")) for section in sections),
        "root_object_count": sum(_as_int(section.get("root_object_count")) for section in sections),
        "shape_draw_text_count": sum(_as_int(section.get("shape_draw_text_count")) for section in sections),
        "page_def_count": sum(_as_int(section.get("page_def_count")) for section in sections),
        "bullet_count": sum(_as_int(section.get("bullet_count")) for section in sections),
        "numbering_count": sum(_as_int(section.get("numbering_count")) for section in sections),
        "control_anchor_count": sum(_as_int(section.get("control_anchor_count")) for section in sections),
        "known_layout_control_count": sum(_as_int(section.get("known_layout_control_count")) for section in sections),
        "candidate_col_pr_control_count": sum(
            _as_int(section.get("candidate_col_pr_control_count")) for section in sections
        ),
    }


def _dig(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
    cursor: Any = payload
    for key in path:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return cursor


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


def _bounded_hwpunit(value: Any, fallback: int) -> int:
    parsed = _as_int(value)
    if parsed <= 0:
        return fallback
    return min(parsed, 1_000_000)


def _style_count(
    id_mappings: dict[str, Any],
    tag_counts: dict[str, Any],
    mapping_key: str,
    tag_key: str,
    *,
    minimum: int = 1,
) -> int:
    return max(minimum, _as_int(id_mappings.get(mapping_key)), _as_int(tag_counts.get(tag_key)))
