"""Pair-driven HWP to HWPX structural rule mining."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .corpus import discover_exact_pairs
from .hwp_profile import profile_hwp_file
from .hwpx_profile import profile_hwpx_file


RULE_DEFINITIONS = (
    {
        "rule_id": "sections.hwp_body_streams_to_hwpx_sections",
        "priority": "high",
        "hwp_path": ("body", "section_stream_count"),
        "hwpx_path": ("section_count",),
        "why": "Section count is a page-layout boundary and should map one-to-one.",
    },
    {
        "rule_id": "sections.hwp_doc_properties_to_hwpx_sections",
        "priority": "high",
        "hwp_path": ("doc_info", "doc_properties", "section_count"),
        "hwpx_path": ("section_count",),
        "why": "Document properties section count should agree with emitted HWPX sections.",
    },
    {
        "rule_id": "paragraphs.para_header_to_hwpx_p",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "para_header_signals", "paragraph_count"),
        "hwpx_path": ("section_aggregate_tags", "p"),
        "why": "Paragraph boundaries dominate visual text flow.",
    },
    {
        "rule_id": "text.para_declared_chars_to_hwpx_text_chars",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "para_header_signals", "declared_char_count"),
        "hwpx_path": ("section_text_char_count",),
        "why": "Text coverage is the first loss detector before style/layout parity.",
    },
    {
        "rule_id": "text.para_text_records_to_hwpx_text_nodes",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "tag_counts", "PARA_TEXT"),
        "hwpx_path": ("section_aggregate_tags", "t"),
        "why": "Text node granularity is needed for later run splitting rules.",
    },
    {
        "rule_id": "runs.para_char_shape_runs_to_hwpx_runs",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "para_header_signals", "char_shape_run_count"),
        "hwpx_path": ("section_aggregate_tags", "run"),
        "why": "Run splitting controls inline visual style fidelity.",
    },
    {
        "rule_id": "runs.para_char_shape_records_to_hwpx_runs",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "style_signals", "para_char_shape_run_count"),
        "hwpx_path": ("section_aggregate_tags", "run"),
        "why": "PARA_CHAR_SHAPE records provide direct run split positions for text-bearing output.",
    },
    {
        "rule_id": "layout.para_line_seg_to_hwpx_lineseg",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "line_segment_count"),
        "hwpx_path": ("section_aggregate_tags", "lineseg"),
        "why": "Line segments capture renderer-level line breaking and placement hints.",
    },
    {
        "rule_id": "tables.table_record_to_hwpx_tbl",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "table_record_count"),
        "hwpx_path": ("section_aggregate_tags", "tbl"),
        "why": "Table object count is a high-impact layout fidelity signal.",
    },
    {
        "rule_id": "tables.table_record_rows_to_hwpx_tr",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "table_row_count"),
        "hwpx_path": ("section_aggregate_tags", "tr"),
        "why": "TABLE row-count arrays map directly to HWPX table rows in the paired corpus.",
    },
    {
        "rule_id": "tables.table_record_cell_array_to_hwpx_tc",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "table_cell_count"),
        "hwpx_path": ("section_aggregate_tags", "tc"),
        "why": "TABLE row cell-count arrays map directly to HWPX table cells in the paired corpus.",
    },
    {
        "rule_id": "tables.list_header_to_hwpx_sub_list",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "list_header_record_count"),
        "hwpx_path": ("section_aggregate_tags", "subList"),
        "why": "LIST_HEADER records are the strongest source signal for HWPX subList flow.",
    },
    {
        "rule_id": "objects.picture_record_to_hwpx_bindata_entries",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "layout_signals", "picture_record_count"),
        "hwpx_path": ("bin_data_count",),
        "why": "Picture controls usually require paired binary data mapping.",
    },
    {
        "rule_id": "objects.picture_record_to_hwpx_pic_tags",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "layout_signals", "picture_record_count"),
        "hwpx_path": ("section_aggregate_tags", "pic"),
        "why": "Picture object records should eventually map to HWPX picture elements.",
    },
    {
        "rule_id": "objects.ctrl_header_to_hwpx_ctrl_tags",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "layout_signals", "ctrl_header_record_count"),
        "hwpx_path": ("section_aggregate_tags", "ctrl"),
        "why": "Control headers are object anchors that affect layout and wrapping.",
    },
    {
        "rule_id": "package.bindata_streams_to_hwpx_bindata_entries",
        "priority": "medium",
        "hwp_path": ("stream_inventory", "bin_data_stream_count"),
        "hwpx_path": ("bin_data_count",),
        "why": "Binary stream count is a package-level asset mapping signal.",
    },
    {
        "rule_id": "package.docinfo_bindata_records_to_hwpx_bindata_entries",
        "priority": "medium",
        "hwp_path": ("doc_info", "tag_counts", "BIN_DATA"),
        "hwpx_path": ("bin_data_count",),
        "why": "DocInfo binary-data records should explain HWPX asset entries.",
    },
    {
        "rule_id": "package.id_mapping_bindata_to_hwpx_bindata_entries",
        "priority": "medium",
        "hwp_path": ("doc_info", "id_mappings", "bin_data"),
        "hwpx_path": ("bin_data_count",),
        "why": "The ID mapping table should be the durable binary asset id bridge.",
    },
    {
        "rule_id": "page.page_def_to_section_layout",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "page_def_record_count"),
        "hwpx_path": ("section_count",),
        "why": "Page definition records drive page size and margin conversion.",
    },
    {
        "rule_id": "page.page_def_to_hwpx_page_pr",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "page_def_record_count"),
        "hwpx_path": ("section_aggregate_tags", "pagePr"),
        "why": "Page definitions should map to explicit HWPX page property elements.",
    },
    {
        "rule_id": "page.page_def_width_to_hwpx_page_pr_width",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "page_width_sum"),
        "hwpx_path": ("section_page_geometry_sums", "width"),
        "why": "PAGE_DEF width units map to HWPX pagePr width attributes.",
    },
    {
        "rule_id": "page.page_def_height_to_hwpx_page_pr_height",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "page_height_sum"),
        "hwpx_path": ("section_page_geometry_sums", "height"),
        "why": "PAGE_DEF height units map to HWPX pagePr height attributes.",
    },
    {
        "rule_id": "page.page_def_margins_to_hwpx_margin_attrs",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "page_margin_sum"),
        "hwpx_path": ("section_page_geometry_sums", "margin"),
        "why": "PAGE_DEF margin units map to HWPX margin attributes.",
    },
    {
        "rule_id": "page.page_def_to_hwpx_sec_pr",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_signals", "page_def_record_count"),
        "hwpx_path": ("section_aggregate_tags", "secPr"),
        "why": "Section properties are the HWPX home for page-level layout policy.",
    },
    {
        "rule_id": "lists.numbering_to_hwpx_numbering",
        "priority": "medium",
        "hwp_path": ("doc_info", "tag_counts", "NUMBERING"),
        "hwpx_path": ("aggregate_tags", "numbering"),
        "why": "Numbering rules need stable list style mapping.",
    },
    {
        "rule_id": "lists.bullet_to_hwpx_bullet",
        "priority": "medium",
        "hwp_path": ("doc_info", "tag_counts", "BULLET"),
        "hwpx_path": ("aggregate_tags", "bullet"),
        "why": "Bullet rules need stable list style mapping.",
    },
    {
        "rule_id": "styles.char_shape_to_hwpx_char_pr",
        "priority": "medium",
        "hwp_path": ("doc_info", "tag_counts", "CHAR_SHAPE"),
        "hwpx_path": ("aggregate_tags", "charPr"),
        "why": "Character styles are required for font/size/weight/color fidelity.",
    },
    {
        "rule_id": "styles.id_mapping_char_shape_to_hwpx_char_pr",
        "priority": "medium",
        "hwp_path": ("doc_info", "id_mappings", "char_shape"),
        "hwpx_path": ("aggregate_tags", "charPr"),
        "why": "Character-shape ID mappings are the durable bridge for inline style ids.",
    },
    {
        "rule_id": "styles.distinct_char_shape_refs_to_hwpx_char_pr",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "style_signals", "distinct_char_shape_ref_count"),
        "hwpx_path": ("aggregate_tags", "charPr"),
        "why": "Distinct paragraph run style references help determine the minimum generated charPr table.",
    },
    {
        "rule_id": "styles.para_shape_to_hwpx_para_pr",
        "priority": "medium",
        "hwp_path": ("doc_info", "tag_counts", "PARA_SHAPE"),
        "hwpx_path": ("aggregate_tags", "paraPr"),
        "why": "Paragraph styles are required for indent/spacing/alignment fidelity.",
    },
    {
        "rule_id": "styles.id_mapping_para_shape_to_hwpx_para_pr",
        "priority": "medium",
        "hwp_path": ("doc_info", "id_mappings", "para_shape"),
        "hwpx_path": ("aggregate_tags", "paraPr"),
        "why": "Paragraph-shape ID mappings are the durable bridge for paragraph layout ids.",
    },
    {
        "rule_id": "styles.distinct_para_shape_refs_to_hwpx_para_pr",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "style_signals", "distinct_para_shape_ref_count"),
        "hwpx_path": ("aggregate_tags", "paraPr"),
        "why": "Distinct paragraph shape references help determine the minimum generated paraPr table.",
    },
    {
        "rule_id": "styles.style_records_to_hwpx_style_tags",
        "priority": "low",
        "hwp_path": ("doc_info", "tag_counts", "STYLE"),
        "hwpx_path": ("aggregate_tags", "style"),
        "why": "Named style rules are useful but less stable than direct shape mappings.",
    },
    {
        "rule_id": "objects.page_hiding_ctrl_to_hwpx_page_hiding",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "layout_details", "layout_control_child_counts", "pageHiding"),
        "hwpx_path": ("section_ctrl_child_counts", "pageHiding"),
        "why": "The HWP page-hiding control id maps to HWPX pageHiding controls.",
    },
    {
        "rule_id": "objects.page_num_ctrl_to_hwpx_page_num",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "layout_details", "layout_control_child_counts", "pageNum"),
        "hwpx_path": ("section_ctrl_child_counts", "pageNum"),
        "why": "The HWP page-number control id maps to HWPX pageNum controls.",
    },
    {
        "rule_id": "objects.new_num_ctrl_to_hwpx_new_num",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "layout_details", "layout_control_child_counts", "newNum"),
        "hwpx_path": ("section_ctrl_child_counts", "newNum"),
        "why": "The HWP new-number control id maps to HWPX newNum controls.",
    },
    {
        "rule_id": "objects.header_ctrl_to_hwpx_header",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "layout_details", "layout_control_child_counts", "header"),
        "hwpx_path": ("section_ctrl_child_counts", "header"),
        "why": "The HWP header control id maps to HWPX header controls.",
    },
    {
        "rule_id": "objects.section_ctrl_to_conservative_hwpx_col_pr",
        "priority": "medium",
        "hwp_path": ("body", "aggregate", "layout_details", "control_id_counts", "dces"),
        "hwpx_path": ("section_ctrl_child_counts", "colPr"),
        "why": "The HWP section control id provides a conservative section-level HWPX colPr signal.",
    },
    {
        "rule_id": "objects.dloc_to_hwpx_col_pr_hancom_profile",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_details", "control_id_counts", "dloc"),
        "hwpx_path": ("section_ctrl_child_counts", "colPr"),
        "producer_family": "hancom",
        "why": "Hancom-produced HWPX preserves each HWP dloc column control as colPr.",
    },
    {
        "rule_id": "objects.dces_to_hwpx_col_pr_portable_profile",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_details", "control_id_counts", "dces"),
        "hwpx_path": ("section_ctrl_child_counts", "colPr"),
        "producer_family": "portable",
        "why": "Portable producer output keeps the conservative section-level dces column count.",
    },
    {
        "rule_id": "objects.field_ctrl_ids_to_hwpx_field_begin",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_details", "layout_control_child_counts", "fieldBegin"),
        "hwpx_path": ("section_ctrl_child_counts", "fieldBegin"),
        "why": "The HWP field-control id family maps exactly to HWPX fieldBegin controls in the paired corpus.",
    },
    {
        "rule_id": "objects.field_ctrl_ids_to_hwpx_field_end",
        "priority": "high",
        "hwp_path": ("body", "aggregate", "layout_details", "layout_control_child_counts", "fieldEnd"),
        "hwpx_path": ("section_ctrl_child_counts", "fieldEnd"),
        "why": "The HWP field-control id family maps exactly to HWPX fieldEnd controls in the paired corpus.",
    },
)


def build_rule_mining_report(
    root: Path,
    *,
    recursive: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """Mine public-safe paired HWP/HWPX structural rules."""

    pairs = discover_exact_pairs(root.resolve(), recursive=recursive)
    selected_pairs = pairs[:limit] if limit is not None else pairs
    pair_results = []
    rule_observations: dict[str, list[dict[str, Any]]] = {
        str(rule["rule_id"]): [] for rule in RULE_DEFINITIONS
    }
    hwp_status_counts: Counter[str] = Counter()
    hwpx_status_counts: Counter[str] = Counter()

    for pair in selected_pairs:
        hwp_profile = profile_hwp_file(pair.hwp_path)
        hwpx_profile = profile_hwpx_file(pair.hwpx_path)
        hwp_status_counts[str(hwp_profile.get("status", "unknown"))] += 1
        hwpx_status_counts[str(hwpx_profile.get("status", "unknown"))] += 1
        signals = _extract_pair_signals(hwp_profile, hwpx_profile)
        observations = []
        for rule in RULE_DEFINITIONS:
            observation = _evaluate_rule(rule, hwp_profile, hwpx_profile)
            rule_observations[str(rule["rule_id"])].append(observation)
            observations.append(observation)
        pair_results.append(
            {
                "pair_ref": pair.pair_ref,
                "hwp_status": hwp_profile.get("status", "unknown"),
                "hwpx_status": hwpx_profile.get("status", "unknown"),
                "signals": signals,
                "rule_observations": observations,
            }
        )

    rule_summaries = [
        _summarize_rule(rule, rule_observations[str(rule["rule_id"])])
        for rule in RULE_DEFINITIONS
    ]
    confidence_counts = Counter(summary["confidence_band"] for summary in rule_summaries)

    return {
        "schema_version": "owned_hwp_hwpx_rule_mining.v1",
        "status": "rule_mining_built",
        "public_safety": {
            "paths_in_report": False,
            "filenames_in_report": False,
            "raw_document_text_in_report": False,
        },
        "summary": {
            "exact_pair_count": len(pairs),
            "evaluated_pair_count": len(pair_results),
            "hwp_status_counts": dict(sorted(hwp_status_counts.items())),
            "hwpx_status_counts": dict(sorted(hwpx_status_counts.items())),
            "rule_count": len(rule_summaries),
            "confidence_band_counts": dict(sorted(confidence_counts.items())),
        },
        "rule_summaries": rule_summaries,
        "pairs": pair_results,
    }


def _extract_pair_signals(hwp_profile: dict[str, Any], hwpx_profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "hwp": {
            "section_stream_count": _get(hwp_profile, ("body", "section_stream_count")),
            "docinfo_section_count": _get(hwp_profile, ("doc_info", "doc_properties", "section_count")),
            "paragraph_count": _get(hwp_profile, ("body", "aggregate", "para_header_signals", "paragraph_count")),
            "declared_char_count": _get(
                hwp_profile,
                ("body", "aggregate", "para_header_signals", "declared_char_count"),
            ),
            "table_record_count": _get(hwp_profile, ("body", "aggregate", "layout_signals", "table_record_count")),
            "table_row_count": _get(hwp_profile, ("body", "aggregate", "layout_signals", "table_row_count")),
            "table_cell_count": _get(hwp_profile, ("body", "aggregate", "layout_signals", "table_cell_count")),
            "list_header_record_count": _get(
                hwp_profile,
                ("body", "aggregate", "layout_signals", "list_header_record_count"),
            ),
            "line_segment_count": _get(hwp_profile, ("body", "aggregate", "layout_signals", "line_segment_count")),
            "char_shape_run_count": _get(
                hwp_profile,
                ("body", "aggregate", "style_signals", "para_char_shape_run_count"),
            ),
            "distinct_char_shape_ref_count": _get(
                hwp_profile,
                ("body", "aggregate", "style_signals", "distinct_char_shape_ref_count"),
            ),
            "distinct_para_shape_ref_count": _get(
                hwp_profile,
                ("body", "aggregate", "style_signals", "distinct_para_shape_ref_count"),
            ),
            "page_def_record_count": _get(
                hwp_profile,
                ("body", "aggregate", "layout_signals", "page_def_record_count"),
            ),
            "page_width_sum": _get(hwp_profile, ("body", "aggregate", "layout_signals", "page_width_sum")),
            "page_height_sum": _get(hwp_profile, ("body", "aggregate", "layout_signals", "page_height_sum")),
            "page_margin_sum": _get(hwp_profile, ("body", "aggregate", "layout_signals", "page_margin_sum")),
            "bin_data_stream_count": _get(hwp_profile, ("stream_inventory", "bin_data_stream_count")),
        },
        "hwpx": {
            "section_count": _get(hwpx_profile, ("section_count",)),
            "paragraph_count": _get(hwpx_profile, ("section_aggregate_tags", "p")),
            "text_char_count": _get(hwpx_profile, ("section_text_char_count",)),
            "table_count": _get(hwpx_profile, ("section_aggregate_tags", "tbl")),
            "table_row_count": _get(hwpx_profile, ("section_aggregate_tags", "tr")),
            "table_cell_count": _get(hwpx_profile, ("section_aggregate_tags", "tc")),
            "sub_list_count": _get(hwpx_profile, ("section_aggregate_tags", "subList")),
            "line_segment_count": _get(hwpx_profile, ("section_aggregate_tags", "lineseg")),
            "run_count": _get(hwpx_profile, ("section_aggregate_tags", "run")),
            "char_pr_count": _get(hwpx_profile, ("aggregate_tags", "charPr")),
            "para_pr_count": _get(hwpx_profile, ("aggregate_tags", "paraPr")),
            "style_count": _get(hwpx_profile, ("aggregate_tags", "style")),
            "bin_data_count": _get(hwpx_profile, ("bin_data_count",)),
            "page_geometry_sums": _get(hwpx_profile, ("section_page_geometry_sums",)),
            "ctrl_child_counts": _get(hwpx_profile, ("section_ctrl_child_counts",)),
        },
    }


def _evaluate_rule(
    rule: dict[str, Any],
    hwp_profile: dict[str, Any],
    hwpx_profile: dict[str, Any],
) -> dict[str, Any]:
    producer_family = rule.get("producer_family")
    if producer_family and hwpx_profile.get("producer_family") != producer_family:
        return {
            "rule_id": rule["rule_id"],
            "hwp_value": None,
            "hwpx_value": None,
            "relation": "not_applicable",
            "delta": None,
        }
    hwp_value = _as_int(_get(hwp_profile, rule["hwp_path"]))
    hwpx_value = _as_int(_get(hwpx_profile, rule["hwpx_path"]))
    relation = _relation(hwp_value, hwpx_value)
    return {
        "rule_id": rule["rule_id"],
        "hwp_value": hwp_value,
        "hwpx_value": hwpx_value,
        "relation": relation,
        "delta": None if hwp_value is None or hwpx_value is None else hwpx_value - hwp_value,
    }


def _summarize_rule(rule: dict[str, Any], observations: list[dict[str, Any]]) -> dict[str, Any]:
    compared = [item for item in observations if item["hwp_value"] is not None and item["hwpx_value"] is not None]
    relation_counts = Counter(item["relation"] for item in observations)
    exact = relation_counts.get("exact", 0)
    close = relation_counts.get("close", 0)
    present = relation_counts.get("both_present", 0)
    compared_count = len(compared)
    score = 0.0
    if compared_count:
        score = round((exact + (0.7 * close) + (0.4 * present)) / compared_count, 4)
    confidence_band = "exploratory"
    if score >= 0.95:
        confidence_band = "high_confidence"
    elif score >= 0.75:
        confidence_band = "medium_confidence"
    elif score >= 0.45:
        confidence_band = "weak_signal"

    return {
        "rule_id": rule["rule_id"],
        "priority": rule["priority"],
        "why": rule["why"],
        "compared_pair_count": compared_count,
        "relation_counts": dict(sorted(relation_counts.items())),
        "confidence_score": score,
        "confidence_band": confidence_band,
        "sample_deltas": [item["delta"] for item in compared[:8]],
    }


def _relation(hwp_value: int | None, hwpx_value: int | None) -> str:
    if hwp_value is None or hwpx_value is None:
        return "missing_signal"
    if hwp_value == hwpx_value:
        return "exact"
    if hwp_value == 0 and hwpx_value == 0:
        return "exact"
    if hwp_value > 0 and hwpx_value > 0:
        tolerance = max(2, round(max(abs(hwp_value), abs(hwpx_value)) * 0.05))
        if abs(hwp_value - hwpx_value) <= tolerance:
            return "close"
        return "both_present"
    if hwp_value == 0 and hwpx_value > 0:
        return "hwpx_only"
    if hwp_value > 0 and hwpx_value == 0:
        return "hwp_only"
    return "mismatch"


def _get(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
    cursor: Any = payload
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            if len(path) >= 2 and path[-2] in {"layout_control_child_counts", "section_ctrl_child_counts"}:
                return 0
            return None
        cursor = cursor[key]
    return cursor


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
