"""Dry-run generation and snapshot comparison pipeline."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .border_fill_semantics import compare_border_fill_semantics
from .corpus import discover_exact_pairs
from .document_model import build_document_model_from_hwp
from .hwpx_profile import profile_hwpx_file
from .hwpx_writer import write_dry_run_hwpx
from .list_section_semantics import compare_list_semantics, compare_section_semantics
from .object_binary_semantics import (
    compare_binary_semantics,
    compare_object_semantics,
    compare_ordered_object_semantics,
)
from .snapshot_gate import compare_snapshot_metrics, write_snapshot_svgs
from .style_semantics import compare_style_semantics
from .table_semantics import compare_table_semantics
from .text_fidelity import compare_texts, extract_hwpx_text


def build_dry_run_writer_report(
    pairs_root: Path,
    output_root: Path,
    *,
    limit: int | None = None,
    recursive: bool = False,
    snapshot_limit: int | None = None,
    include_text: bool = False,
    compatibility_profile: str = "portable",
) -> dict[str, Any]:
    pairs = discover_exact_pairs(pairs_root.resolve(), recursive=recursive)
    selected_pairs = pairs[:limit] if limit is not None else pairs
    generated_root = output_root / "generated"
    snapshot_root = output_root / "snapshots"
    pair_results = []
    status_counts: Counter[str] = Counter()
    generated_profile_counts: Counter[str] = Counter()
    snapshot_scores: list[float] = []
    hwp_generated_coverages: list[float] = []
    generated_gold_coverages: list[float] = []
    generated_gold_target_coverages: list[float] = []
    model_generated_pass_count = 0
    style_control_pass_count = 0
    object_layout_pass_count = 0
    style_rich_pair_count = 0
    layout_rich_pair_count = 0
    source_style_parse_complete_count = 0
    model_generated_style_semantics_pass_count = 0
    model_gold_style_semantics_exact_count = 0
    run_boundary_pass_count = 0
    source_para_extension_count = 0
    source_para_extension_nonzero_count = 0
    source_font_alternate_face_count = 0
    source_font_default_face_unmapped_count = 0
    source_font_type_info_count = 0
    source_font_serif_style_unmapped_count = 0
    resolved_profile_counts: Counter[str] = Counter()
    gold_producer_family_counts: Counter[str] = Counter()
    model_gold_style_status_counts: Counter[str] = Counter()
    source_list_parse_complete_count = 0
    model_generated_list_semantics_pass_count = 0
    model_generated_section_semantics_pass_count = 0
    model_gold_list_semantics_exact_count = 0
    model_gold_section_semantics_exact_count = 0
    model_gold_list_status_counts: Counter[str] = Counter()
    model_gold_section_status_counts: Counter[str] = Counter()
    source_tab_definition_count = 0
    source_tab_item_count = 0
    source_numbering_count = 0
    source_numbering_level_count = 0
    source_numbering_extended_level_count = 0
    source_bullet_count = 0
    source_section_semantic_count = 0
    source_section_extension_nonzero_byte_count = 0
    source_border_fill_parse_complete_count = 0
    source_table_parse_complete_count = 0
    model_generated_border_fill_semantics_pass_count = 0
    model_generated_table_semantics_pass_count = 0
    model_gold_border_fill_semantics_exact_count = 0
    model_gold_table_semantics_exact_count = 0
    model_gold_border_fill_status_counts: Counter[str] = Counter()
    model_gold_table_status_counts: Counter[str] = Counter()
    source_border_fill_count = 0
    source_fill_type_counts: Counter[str] = Counter()
    source_table_count = 0
    source_table_cell_count = 0
    source_merged_table_cell_count = 0
    source_nested_table_count = 0
    source_table_caption_count = 0
    source_table_zone_count = 0
    source_embedded_sub_list_count = 0
    source_generic_embedded_sub_list_count = 0
    source_shape_draw_text_count = 0
    source_shape_draw_text_paragraph_count = 0
    source_object_parse_complete_count = 0
    source_object_section_count = 0
    source_shape_count = 0
    source_root_object_count = 0
    source_group_child_count = 0
    source_picture_count = 0
    source_object_kind_counts: Counter[str] = Counter()
    model_generated_object_semantics_pass_count = 0
    model_generated_object_section_pass_count = 0
    model_gold_object_semantics_exact_count = 0
    model_gold_object_status_counts: Counter[str] = Counter()
    source_binary_parse_complete_count = 0
    source_binary_count = 0
    source_binary_image_count = 0
    source_binary_ole_count = 0
    source_binary_payload_bytes = 0
    source_binary_format_counts: Counter[str] = Counter()
    source_binary_encoding_counts: Counter[str] = Counter()
    model_generated_binary_semantics_pass_count = 0
    model_gold_binary_semantics_exact_count = 0
    model_gold_binary_status_counts: Counter[str] = Counter()
    model_gold_binary_payload_digest_match_count = 0
    model_gold_binary_image_payload_digest_match_count = 0
    hancom_ordered_object_structure_pass_count = 0
    hancom_ordered_source_shape_count = 0
    hancom_ordered_target_shape_count = 0
    hancom_ordered_kind_exact_count = 0
    hancom_parent_index_exact_count = 0
    hancom_source_root_object_count = 0
    hancom_target_root_object_count = 0
    hancom_root_kind_exact_count = 0
    hancom_root_anchor_exact_count = 0

    for index, pair in enumerate(selected_pairs):
        gold_profile = profile_hwpx_file(pair.hwpx_path)
        resolved_profile = _resolve_compatibility_profile(compatibility_profile, gold_profile)
        model = build_document_model_from_hwp(
            pair.hwp_path,
            include_text=include_text,
            compatibility_profile=resolved_profile,
        )
        generated_path = generated_root / f"{pair.pair_ref}.hwpx"
        write_result = write_dry_run_hwpx(generated_path, model)
        generated_profile = profile_hwpx_file(generated_path)
        snapshot_comparison = compare_snapshot_metrics(gold_profile, generated_profile)
        if snapshot_limit is None or index < snapshot_limit:
            write_snapshot_svgs(snapshot_root, pair.pair_ref, gold_profile, generated_profile)

        model_generated = _compare_model_to_generated(model, generated_profile)
        style_control = _compare_style_controls(model, generated_profile, gold_profile)
        object_layout = _compare_object_layout(model, generated_profile, gold_profile)
        source_style_semantics = model.get("style_semantics", {})
        generated_style_semantics = generated_profile.get("style_semantics", {})
        gold_style_semantics = gold_profile.get("style_semantics", {})
        model_generated_style_semantics = compare_style_semantics(
            source_style_semantics,
            generated_style_semantics,
        )
        model_gold_style_semantics = compare_style_semantics(
            source_style_semantics,
            gold_style_semantics,
        )
        source_list_semantics = model.get("list_semantics", {})
        model_generated_list_semantics = compare_list_semantics(
            source_list_semantics,
            generated_profile.get("list_semantics", {}),
        )
        model_gold_list_semantics = compare_list_semantics(
            source_list_semantics,
            gold_profile.get("list_semantics", {}),
        )
        source_section_semantics = [
            section.get("section_semantics", {})
            for section in model.get("sections", [])
            if isinstance(section, dict) and isinstance(section.get("section_semantics"), dict)
        ]
        model_generated_section_semantics = compare_section_semantics(
            source_section_semantics,
            generated_profile.get("section_semantics", []),
        )
        model_gold_section_semantics = compare_section_semantics(
            source_section_semantics,
            gold_profile.get("section_semantics", []),
        )
        source_border_fill_semantics = model.get("border_fill_semantics", {})
        model_generated_border_fill_semantics = compare_border_fill_semantics(
            source_border_fill_semantics,
            generated_profile.get("border_fill_semantics", {}),
        )
        model_gold_border_fill_semantics = compare_border_fill_semantics(
            source_border_fill_semantics,
            gold_profile.get("border_fill_semantics", {}),
        )
        source_table_sections = [
            {"tables": section.get("table_shapes", [])}
            for section in model.get("sections", [])
            if isinstance(section, dict)
        ]
        model_generated_table_semantics = _compare_table_sections(
            source_table_sections,
            generated_profile.get("table_semantics", []),
        )
        model_gold_table_semantics = _compare_table_sections(
            source_table_sections,
            gold_profile.get("table_semantics", []),
        )
        source_object_sections = [
            {"shapes": section.get("object_shapes", [])}
            for section in model.get("sections", [])
            if isinstance(section, dict)
        ]
        model_generated_object_semantics = _compare_object_sections(
            source_object_sections,
            generated_profile.get("object_semantics", []),
        )
        model_gold_object_semantics = _compare_object_sections(
            source_object_sections,
            gold_profile.get("object_semantics", []),
        )
        model_gold_ordered_object_semantics = _compare_ordered_object_sections(
            source_object_sections,
            gold_profile.get("object_semantics", []),
        )
        source_binary_items = [
            item for item in model.get("_binary_payloads", []) if isinstance(item, dict)
        ]
        source_binary_semantics = {"items": source_binary_items}
        model_generated_binary_semantics = compare_binary_semantics(
            source_binary_semantics,
            generated_profile.get("binary_semantics", {}),
        )
        model_gold_binary_semantics = compare_binary_semantics(
            source_binary_semantics,
            gold_profile.get("binary_semantics", {}),
        )
        run_boundaries = _validate_visible_run_boundaries(model)
        text_summary = None
        if include_text:
            hwp_text = _model_text_payload(model)
            generated_text = extract_hwpx_text(generated_path)
            gold_text = extract_hwpx_text(pair.hwpx_path)
            hwp_to_generated = compare_texts(hwp_text.get("text", ""), generated_text.get("text", ""))
            generated_to_gold = compare_texts(generated_text.get("text", ""), gold_text.get("text", ""))
            hwp_to_gold = compare_texts(hwp_text.get("text", ""), gold_text.get("text", ""))
            hwp_generated_coverages.append(float(hwp_to_generated["source_coverage"]))
            generated_gold_coverages.append(float(generated_to_gold["source_coverage"]))
            generated_gold_target_coverages.append(float(generated_to_gold["target_coverage"]))
            text_summary = {
                "hwp_text_status": hwp_text.get("status", "unknown"),
                "generated_text_status": generated_text.get("status", "unknown"),
                "gold_text_status": gold_text.get("status", "unknown"),
                "hwp_to_generated": hwp_to_generated,
                "generated_to_gold": generated_to_gold,
                "hwp_to_gold": hwp_to_gold,
                "hwp_control_summary": {
                    "control_count": _as_int(model.get("summary", {}).get("text_control_count")),
                    "control_payload_unit_count": _as_int(
                        model.get("summary", {}).get("text_control_payload_unit_count")
                    ),
                    "malformed_control_count": _as_int(
                        model.get("summary", {}).get("text_malformed_control_count")
                    ),
                    "control_code_counts": model.get("summary", {}).get("text_control_code_counts", {}),
                    "control_id_counts": model.get("summary", {}).get("text_control_id_counts", {}),
                },
            }
        if model_generated["status"] == "pass":
            model_generated_pass_count += 1
        if style_control["status"] == "pass":
            style_control_pass_count += 1
        if object_layout["status"] == "pass":
            object_layout_pass_count += 1
        if source_style_semantics.get("status") == "parsed":
            source_style_parse_complete_count += 1
        if source_list_semantics.get("status") == "parsed":
            source_list_parse_complete_count += 1
        if source_border_fill_semantics.get("status") == "parsed":
            source_border_fill_parse_complete_count += 1
        if all(
            str(section.get("table_semantics_status", "")) == "parsed"
            for section in model.get("sections", [])
            if isinstance(section, dict)
        ):
            source_table_parse_complete_count += 1
        if all(
            str(section.get("object_semantics_status", "")) == "parsed"
            for section in model.get("sections", [])
            if isinstance(section, dict)
        ):
            source_object_parse_complete_count += 1
        if str(model.get("binary_semantics", {}).get("status", "")) == "parsed":
            source_binary_parse_complete_count += 1
        list_counts = source_list_semantics.get("counts", {}) if isinstance(source_list_semantics, dict) else {}
        source_tab_definition_count += _as_int(list_counts.get("tab_definition_count"))
        source_tab_item_count += _as_int(list_counts.get("tab_item_count"))
        source_numbering_count += _as_int(list_counts.get("numbering_count"))
        source_numbering_level_count += _as_int(list_counts.get("numbering_level_count"))
        source_numbering_extended_level_count += _as_int(list_counts.get("numbering_extended_level_count"))
        source_bullet_count += _as_int(list_counts.get("bullet_count"))
        source_section_semantic_count += len(source_section_semantics)
        source_section_extension_nonzero_byte_count += sum(
            _as_int(section.get("source_only", {}).get("extension_nonzero_byte_count"))
            for section in source_section_semantics
            if isinstance(section, dict) and isinstance(section.get("source_only"), dict)
        )
        border_counts = (
            source_border_fill_semantics.get("counts", {})
            if isinstance(source_border_fill_semantics, dict)
            else {}
        )
        source_border_fill_count += _as_int(border_counts.get("border_fill_count"))
        source_fill_type_counts.update(
            {
                str(key): _as_int(value)
                for key, value in border_counts.get("fill_type_counts", {}).items()
            }
        )
        for section in model.get("sections", []):
            if not isinstance(section, dict):
                continue
            tables = [value for value in section.get("table_shapes", []) if isinstance(value, dict)]
            source_table_count += len(tables)
            source_table_cell_count += sum(len(table.get("cells", [])) for table in tables)
            source_merged_table_cell_count += sum(
                int(_as_int(cell.get("column_span")) > 1 or _as_int(cell.get("row_span")) > 1)
                for table in tables
                for cell in table.get("cells", [])
                if isinstance(cell, dict)
            )
            source_nested_table_count += sum(
                int(_signed_int(table.get("parent_table_index"), -1) >= 0)
                for table in tables
            )
            source_table_caption_count += sum(int(isinstance(table.get("caption"), dict)) for table in tables)
            source_table_zone_count += sum(len(table.get("zones", [])) for table in tables)
            generic_sub_lists = len(section.get("embedded_paragraph_groups", []))
            shape_values = [value for value in section.get("object_shapes", []) if isinstance(value, dict)]
            shape_draw_texts = [
                value.get("draw_text")
                for value in shape_values
                if isinstance(value.get("draw_text"), dict)
            ]
            source_generic_embedded_sub_list_count += generic_sub_lists
            source_shape_draw_text_count += len(shape_draw_texts)
            source_shape_draw_text_paragraph_count += sum(
                len(value.get("paragraph_indexes", [])) for value in shape_draw_texts
            )
            source_embedded_sub_list_count += generic_sub_lists + len(shape_draw_texts)
            source_object_section_count += 1
            source_shape_count += len(shape_values)
            source_root_object_count += sum(isinstance(value.get("common"), dict) for value in shape_values)
            source_group_child_count += sum(
                _signed_int(value.get("parent_shape_index"), -1) >= 0 for value in shape_values
            )
            source_picture_count += sum(value.get("kind") == "pic" for value in shape_values)
            source_object_kind_counts.update(str(value.get("kind", "unknown")) for value in shape_values)
        binary_counts = (
            model.get("binary_semantics", {}).get("counts", {})
            if isinstance(model.get("binary_semantics"), dict)
            else {}
        )
        source_binary_count += len(source_binary_items)
        source_binary_image_count += _as_int(binary_counts.get("image_count"))
        source_binary_ole_count += _as_int(binary_counts.get("ole_count"))
        source_binary_payload_bytes += sum(_as_int(item.get("payload_size")) for item in source_binary_items)
        source_binary_format_counts.update(str(item.get("format", "")) for item in source_binary_items)
        source_binary_encoding_counts.update(str(item.get("payload_encoding", "unknown")) for item in source_binary_items)
        source_para_extension_count += _as_int(
            model.get("summary", {}).get("style_semantic_para_extension_count")
        )
        source_para_extension_nonzero_count += _as_int(
            model.get("summary", {}).get("style_semantic_para_extension_nonzero_count")
        )
        source_font_alternate_face_count += _as_int(
            model.get("summary", {}).get("style_semantic_font_alternate_face_count")
        )
        source_font_default_face_unmapped_count += _as_int(
            model.get("summary", {}).get("style_semantic_font_default_face_unmapped_count")
        )
        source_font_type_info_count += _as_int(
            model.get("summary", {}).get("style_semantic_font_type_info_count")
        )
        source_font_serif_style_unmapped_count += _as_int(
            model.get("summary", {}).get("style_semantic_font_serif_style_unmapped_count")
        )
        if model_generated_style_semantics["status"] == "pass":
            model_generated_style_semantics_pass_count += 1
        if model_gold_style_semantics["status"] == "pass":
            model_gold_style_semantics_exact_count += 1
        if model_generated_list_semantics["status"] == "pass":
            model_generated_list_semantics_pass_count += 1
        if model_generated_section_semantics["status"] == "pass":
            model_generated_section_semantics_pass_count += 1
        if model_gold_list_semantics["status"] == "pass":
            model_gold_list_semantics_exact_count += 1
        if model_gold_section_semantics["status"] == "pass":
            model_gold_section_semantics_exact_count += 1
        if model_generated_border_fill_semantics["status"] == "pass":
            model_generated_border_fill_semantics_pass_count += 1
        if model_generated_table_semantics["status"] == "pass":
            model_generated_table_semantics_pass_count += 1
        if model_gold_border_fill_semantics["status"] == "pass":
            model_gold_border_fill_semantics_exact_count += 1
        if model_gold_table_semantics["status"] == "pass":
            model_gold_table_semantics_exact_count += 1
        if model_generated_object_semantics["status"] == "pass":
            model_generated_object_semantics_pass_count += 1
        model_generated_object_section_pass_count += _as_int(
            model_generated_object_semantics.get("section_pass_count")
        )
        if model_gold_object_semantics["status"] == "pass":
            model_gold_object_semantics_exact_count += 1
        if model_generated_binary_semantics["status"] == "pass":
            model_generated_binary_semantics_pass_count += 1
        if model_gold_binary_semantics["status"] == "pass":
            model_gold_binary_semantics_exact_count += 1
        model_gold_binary_payload_digest_match_count += _as_int(
            model_gold_binary_semantics.get("payload_digest_match_count")
        )
        model_gold_binary_image_payload_digest_match_count += _as_int(
            model_gold_binary_semantics.get("image_payload_digest_match_count")
        )
        if gold_profile.get("producer_family") == "hancom":
            hancom_ordered_object_structure_pass_count += int(
                model_gold_ordered_object_semantics.get("structure_status") == "pass"
            )
            hancom_ordered_source_shape_count += _as_int(
                model_gold_ordered_object_semantics.get("source_count")
            )
            hancom_ordered_target_shape_count += _as_int(
                model_gold_ordered_object_semantics.get("target_count")
            )
            hancom_ordered_kind_exact_count += _as_int(
                model_gold_ordered_object_semantics.get("ordered_kind_exact_count")
            )
            hancom_parent_index_exact_count += _as_int(
                model_gold_ordered_object_semantics.get("parent_index_exact_count")
            )
            hancom_source_root_object_count += _as_int(
                model_gold_ordered_object_semantics.get("source_root_count")
            )
            hancom_target_root_object_count += _as_int(
                model_gold_ordered_object_semantics.get("target_root_count")
            )
            hancom_root_kind_exact_count += _as_int(
                model_gold_ordered_object_semantics.get("root_kind_exact_count")
            )
            hancom_root_anchor_exact_count += _as_int(
                model_gold_ordered_object_semantics.get("root_anchor_exact_count")
            )
        if run_boundaries["status"] == "pass":
            run_boundary_pass_count += 1
        if style_control["source_rich_style_signal"]:
            style_rich_pair_count += 1
        if object_layout["source_rich_layout_signal"]:
            layout_rich_pair_count += 1
        snapshot_scores.append(float(snapshot_comparison["score"]))
        status_counts[str(model.get("status", "unknown"))] += 1
        generated_profile_counts[str(generated_profile.get("status", "unknown"))] += 1
        resolved_profile_counts[resolved_profile] += 1
        gold_producer_family_counts[str(gold_profile.get("producer_family", "unknown"))] += 1
        model_gold_style_status_counts[
            f'{gold_profile.get("producer_family", "unknown")}:{model_gold_style_semantics["status"]}'
        ] += 1
        model_gold_list_status_counts[
            f'{gold_profile.get("producer_family", "unknown")}:{model_gold_list_semantics["status"]}'
        ] += 1
        model_gold_section_status_counts[
            f'{gold_profile.get("producer_family", "unknown")}:{model_gold_section_semantics["status"]}'
        ] += 1
        model_gold_border_fill_status_counts[
            f'{gold_profile.get("producer_family", "unknown")}:{model_gold_border_fill_semantics["status"]}'
        ] += 1
        model_gold_table_status_counts[
            f'{gold_profile.get("producer_family", "unknown")}:{model_gold_table_semantics["status"]}'
        ] += 1
        model_gold_object_status_counts[
            f'{gold_profile.get("producer_family", "unknown")}:{model_gold_object_semantics["status"]}'
        ] += 1
        model_gold_binary_status_counts[
            f'{gold_profile.get("producer_family", "unknown")}:{model_gold_binary_semantics["status"]}'
        ] += 1
        pair_results.append(
            {
                "pair_ref": pair.pair_ref,
                "model_status": model.get("status", "unknown"),
                "write_status": write_result["status"],
                "generated_profile_status": generated_profile.get("status", "unknown"),
                "gold_profile_status": gold_profile.get("status", "unknown"),
                "compatibility_profile": resolved_profile,
                "gold_producer_family": gold_profile.get("producer_family", "unknown"),
                "model_generated": model_generated,
                "snapshot": {
                    "score": snapshot_comparison["score"],
                    "metric_scores": snapshot_comparison["metric_scores"],
                    "gold_metrics": snapshot_comparison["gold_metrics"],
                    "generated_metrics": snapshot_comparison["generated_metrics"],
                },
                "text": text_summary,
                "style_control": style_control,
                "object_layout": object_layout,
                "style_semantics": {
                    "model_to_generated": model_generated_style_semantics,
                    "model_to_gold": model_gold_style_semantics,
                },
                "list_section_semantics": {
                    "list_model_to_generated": model_generated_list_semantics,
                    "list_model_to_gold": model_gold_list_semantics,
                    "section_model_to_generated": model_generated_section_semantics,
                    "section_model_to_gold": model_gold_section_semantics,
                },
                "table_rendering_semantics": {
                    "border_fill_model_to_generated": model_generated_border_fill_semantics,
                    "border_fill_model_to_gold": model_gold_border_fill_semantics,
                    "table_model_to_generated": model_generated_table_semantics,
                    "table_model_to_gold": model_gold_table_semantics,
                },
                "object_binary_semantics": {
                    "object_model_to_generated": model_generated_object_semantics,
                    "object_model_to_gold": model_gold_object_semantics,
                    "object_model_to_gold_ordered": model_gold_ordered_object_semantics,
                    "binary_model_to_generated": model_generated_binary_semantics,
                    "binary_model_to_gold": model_gold_binary_semantics,
                },
                "run_boundaries": run_boundaries,
            }
        )

    average_score = round(sum(snapshot_scores) / len(snapshot_scores), 4) if snapshot_scores else 0.0
    min_score = round(min(snapshot_scores), 4) if snapshot_scores else 0.0
    average_hwp_generated = round(sum(hwp_generated_coverages) / len(hwp_generated_coverages), 4) if hwp_generated_coverages else None
    average_generated_gold = round(sum(generated_gold_coverages) / len(generated_gold_coverages), 4) if generated_gold_coverages else None
    min_hwp_generated = round(min(hwp_generated_coverages), 4) if hwp_generated_coverages else None
    min_generated_gold = round(min(generated_gold_coverages), 4) if generated_gold_coverages else None
    min_generated_gold_target = (
        round(min(generated_gold_target_coverages), 4) if generated_gold_target_coverages else None
    )
    output_ref = _safe_output_ref(output_root)
    return {
        "schema_version": "owned_hwp_hwpx_dry_run_writer.v1",
        "status": "dry_run_built",
        "public_safety": {
            "paths_in_report": False,
            "filenames_in_report": False,
            "raw_document_text_in_report": False,
        },
        "artifact_roots": {
            "generated_packages": f"{output_ref}/generated",
            "snapshots": f"{output_ref}/snapshots",
        },
        "summary": {
            "exact_pair_count": len(pairs),
            "evaluated_pair_count": len(pair_results),
            "model_status_counts": dict(sorted(status_counts.items())),
            "generated_profile_status_counts": dict(sorted(generated_profile_counts.items())),
            "model_generated_core_pass_count": model_generated_pass_count,
            "model_generated_style_control_pass_count": style_control_pass_count,
            "model_generated_object_layout_pass_count": object_layout_pass_count,
            "source_style_rich_pair_count": style_rich_pair_count,
            "source_layout_rich_pair_count": layout_rich_pair_count,
            "source_style_parse_complete_count": source_style_parse_complete_count,
            "model_generated_style_semantics_pass_count": model_generated_style_semantics_pass_count,
            "model_gold_style_semantics_exact_count": model_gold_style_semantics_exact_count,
            "model_gold_style_status_counts": dict(sorted(model_gold_style_status_counts.items())),
            "source_list_parse_complete_count": source_list_parse_complete_count,
            "model_generated_list_semantics_pass_count": model_generated_list_semantics_pass_count,
            "model_generated_section_semantics_pass_count": model_generated_section_semantics_pass_count,
            "model_gold_list_semantics_exact_count": model_gold_list_semantics_exact_count,
            "model_gold_section_semantics_exact_count": model_gold_section_semantics_exact_count,
            "model_gold_list_status_counts": dict(sorted(model_gold_list_status_counts.items())),
            "model_gold_section_status_counts": dict(sorted(model_gold_section_status_counts.items())),
            "source_border_fill_parse_complete_count": source_border_fill_parse_complete_count,
            "source_table_parse_complete_count": source_table_parse_complete_count,
            "model_generated_border_fill_semantics_pass_count": model_generated_border_fill_semantics_pass_count,
            "model_generated_table_semantics_pass_count": model_generated_table_semantics_pass_count,
            "model_gold_border_fill_semantics_exact_count": model_gold_border_fill_semantics_exact_count,
            "model_gold_table_semantics_exact_count": model_gold_table_semantics_exact_count,
            "model_gold_border_fill_status_counts": dict(sorted(model_gold_border_fill_status_counts.items())),
            "model_gold_table_status_counts": dict(sorted(model_gold_table_status_counts.items())),
            "source_border_fill_count": source_border_fill_count,
            "source_fill_type_counts": dict(sorted(source_fill_type_counts.items())),
            "source_table_count": source_table_count,
            "source_table_cell_count": source_table_cell_count,
            "source_merged_table_cell_count": source_merged_table_cell_count,
            "source_nested_table_count": source_nested_table_count,
            "source_table_caption_count": source_table_caption_count,
            "source_table_zone_count": source_table_zone_count,
            "source_embedded_sub_list_count": source_embedded_sub_list_count,
            "source_generic_embedded_sub_list_count": source_generic_embedded_sub_list_count,
            "source_shape_draw_text_count": source_shape_draw_text_count,
            "source_shape_draw_text_paragraph_count": source_shape_draw_text_paragraph_count,
            "source_object_parse_complete_count": source_object_parse_complete_count,
            "source_object_section_count": source_object_section_count,
            "source_shape_count": source_shape_count,
            "source_root_object_count": source_root_object_count,
            "source_group_child_count": source_group_child_count,
            "source_picture_count": source_picture_count,
            "source_object_kind_counts": dict(sorted(source_object_kind_counts.items())),
            "model_generated_object_semantics_pass_count": model_generated_object_semantics_pass_count,
            "model_generated_object_section_pass_count": model_generated_object_section_pass_count,
            "model_gold_object_semantics_exact_count": model_gold_object_semantics_exact_count,
            "model_gold_object_status_counts": dict(sorted(model_gold_object_status_counts.items())),
            "source_binary_parse_complete_count": source_binary_parse_complete_count,
            "source_binary_count": source_binary_count,
            "source_binary_image_count": source_binary_image_count,
            "source_binary_ole_count": source_binary_ole_count,
            "source_binary_payload_bytes": source_binary_payload_bytes,
            "source_binary_format_counts": dict(sorted(source_binary_format_counts.items())),
            "source_binary_encoding_counts": dict(sorted(source_binary_encoding_counts.items())),
            "model_generated_binary_semantics_pass_count": model_generated_binary_semantics_pass_count,
            "model_gold_binary_semantics_exact_count": model_gold_binary_semantics_exact_count,
            "model_gold_binary_status_counts": dict(sorted(model_gold_binary_status_counts.items())),
            "model_gold_binary_payload_digest_match_count": model_gold_binary_payload_digest_match_count,
            "model_gold_binary_image_payload_digest_match_count": model_gold_binary_image_payload_digest_match_count,
            "hancom_ordered_object_structure_pass_count": hancom_ordered_object_structure_pass_count,
            "hancom_ordered_source_shape_count": hancom_ordered_source_shape_count,
            "hancom_ordered_target_shape_count": hancom_ordered_target_shape_count,
            "hancom_ordered_kind_exact_count": hancom_ordered_kind_exact_count,
            "hancom_parent_index_exact_count": hancom_parent_index_exact_count,
            "hancom_source_root_object_count": hancom_source_root_object_count,
            "hancom_target_root_object_count": hancom_target_root_object_count,
            "hancom_root_kind_exact_count": hancom_root_kind_exact_count,
            "hancom_root_anchor_exact_count": hancom_root_anchor_exact_count,
            "source_tab_definition_count": source_tab_definition_count,
            "source_tab_item_count": source_tab_item_count,
            "source_numbering_count": source_numbering_count,
            "source_numbering_level_count": source_numbering_level_count,
            "source_numbering_extended_level_count": source_numbering_extended_level_count,
            "source_bullet_count": source_bullet_count,
            "source_section_semantic_count": source_section_semantic_count,
            "source_section_extension_nonzero_byte_count": source_section_extension_nonzero_byte_count,
            "run_boundary_pass_count": run_boundary_pass_count,
            "source_para_extension_count": source_para_extension_count,
            "source_para_extension_nonzero_count": source_para_extension_nonzero_count,
            "source_font_alternate_face_count": source_font_alternate_face_count,
            "source_font_default_face_unmapped_count": source_font_default_face_unmapped_count,
            "source_font_type_info_count": source_font_type_info_count,
            "source_font_serif_style_unmapped_count": source_font_serif_style_unmapped_count,
            "snapshot_average_score": average_score,
            "snapshot_min_score": min_score,
            "snapshot_artifact_pair_count": len(pair_results) if snapshot_limit is None else min(snapshot_limit, len(pair_results)),
            "text_mode": include_text,
            "requested_compatibility_profile": compatibility_profile,
            "resolved_compatibility_profile_counts": dict(sorted(resolved_profile_counts.items())),
            "gold_producer_family_counts": dict(sorted(gold_producer_family_counts.items())),
            "hwp_to_generated_text_average_coverage": average_hwp_generated,
            "hwp_to_generated_text_min_coverage": min_hwp_generated,
            "generated_to_gold_text_average_coverage": average_generated_gold,
            "generated_to_gold_text_min_source_coverage": min_generated_gold,
            "generated_to_gold_text_min_target_coverage": min_generated_gold_target,
        },
        "pairs": pair_results,
    }


def _compare_table_sections(
    source_sections: list[dict[str, Any]],
    target_sections: Any,
) -> dict[str, Any]:
    targets = target_sections if isinstance(target_sections, list) else []
    comparisons = [
        compare_table_semantics(
            source,
            targets[index] if index < len(targets) and isinstance(targets[index], dict) else {},
        )
        for index, source in enumerate(source_sections)
    ]
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    for comparison in comparisons:
        exact.update(
            {str(key): _as_int(value) for key, value in comparison.get("field_exact_counts", {}).items()}
        )
        total.update(
            {str(key): _as_int(value) for key, value in comparison.get("field_total_counts", {}).items()}
        )
    section_count_exact = len(source_sections) == len(targets)
    return {
        "status": "pass" if section_count_exact and all(value["status"] == "pass" for value in comparisons) else "fail",
        "checks": {
            "section_count": section_count_exact,
            "sections": all(value["status"] == "pass" for value in comparisons),
        },
        "source_section_count": len(source_sections),
        "target_section_count": len(targets),
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def _compare_object_sections(
    source_sections: list[dict[str, Any]],
    target_sections: Any,
) -> dict[str, Any]:
    targets = target_sections if isinstance(target_sections, list) else []
    comparisons = [
        compare_object_semantics(
            source,
            targets[index] if index < len(targets) and isinstance(targets[index], dict) else {},
        )
        for index, source in enumerate(source_sections)
    ]
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    for comparison in comparisons:
        exact.update(
            {str(key): _as_int(value) for key, value in comparison.get("field_exact_counts", {}).items()}
        )
        total.update(
            {str(key): _as_int(value) for key, value in comparison.get("field_total_counts", {}).items()}
        )
    section_count_exact = len(source_sections) == len(targets)
    section_pass_count = sum(comparison.get("status") == "pass" for comparison in comparisons)
    return {
        "status": "pass" if section_count_exact and section_pass_count == len(comparisons) else "fail",
        "checks": {
            "section_count": section_count_exact,
            "sections": section_pass_count == len(comparisons),
        },
        "source_section_count": len(source_sections),
        "target_section_count": len(targets),
        "section_pass_count": section_pass_count,
        "source_shape_count": sum(_as_int(value.get("source_count")) for value in comparisons),
        "target_shape_count": sum(_as_int(value.get("target_count")) for value in comparisons),
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def _compare_ordered_object_sections(
    source_sections: list[dict[str, Any]],
    target_sections: Any,
) -> dict[str, Any]:
    targets = target_sections if isinstance(target_sections, list) else []
    comparisons = [
        compare_ordered_object_semantics(
            source,
            targets[index] if index < len(targets) and isinstance(targets[index], dict) else {},
        )
        for index, source in enumerate(source_sections)
    ]
    exact: Counter[str] = Counter()
    total: Counter[str] = Counter()
    for comparison in comparisons:
        exact.update(
            {str(key): _as_int(value) for key, value in comparison.get("field_exact_counts", {}).items()}
        )
        total.update(
            {str(key): _as_int(value) for key, value in comparison.get("field_total_counts", {}).items()}
        )
    source_count = sum(_as_int(value.get("source_count")) for value in comparisons)
    target_count = sum(_as_int(value.get("target_count")) for value in comparisons)
    ordered_kind_exact_count = sum(
        _as_int(value.get("ordered_kind_exact_count")) for value in comparisons
    )
    parent_index_exact_count = sum(
        _as_int(value.get("parent_index_exact_count")) for value in comparisons
    )
    source_root_count = sum(_as_int(value.get("source_root_count")) for value in comparisons)
    target_root_count = sum(_as_int(value.get("target_root_count")) for value in comparisons)
    root_kind_exact_count = sum(_as_int(value.get("root_kind_exact_count")) for value in comparisons)
    root_anchor_exact_count = sum(_as_int(value.get("root_anchor_exact_count")) for value in comparisons)
    section_count_exact = len(source_sections) == len(targets)
    structure_checks = {
        "section_count": section_count_exact,
        "shape_count": source_count == target_count,
        "ordered_kind": ordered_kind_exact_count == source_count,
        "parent_index": parent_index_exact_count == source_count,
        "root_count": source_root_count == target_root_count,
        "root_kind": root_kind_exact_count == source_root_count,
        "root_anchor": root_anchor_exact_count == source_root_count,
    }
    return {
        "status": "pass" if section_count_exact and all(value.get("status") == "pass" for value in comparisons) else "diverged",
        "structure_status": "pass" if all(structure_checks.values()) else "fail",
        "structure_checks": structure_checks,
        "source_section_count": len(source_sections),
        "target_section_count": len(targets),
        "source_count": source_count,
        "target_count": target_count,
        "ordered_kind_exact_count": ordered_kind_exact_count,
        "parent_index_exact_count": parent_index_exact_count,
        "source_root_count": source_root_count,
        "target_root_count": target_root_count,
        "root_kind_exact_count": root_kind_exact_count,
        "root_anchor_exact_count": root_anchor_exact_count,
        "field_exact_counts": dict(sorted(exact.items())),
        "field_total_counts": dict(sorted(total.items())),
    }


def _validate_visible_run_boundaries(model: dict[str, Any]) -> dict[str, Any]:
    paragraph_count = 0
    run_count = 0
    out_of_range_count = 0
    non_monotonic_count = 0
    missing_zero_start_count = 0
    for section in model.get("sections", []):
        if not isinstance(section, dict):
            continue
        texts = section.get("paragraph_texts", [])
        styles = section.get("paragraph_styles", [])
        for index, style in enumerate(styles):
            if not isinstance(style, dict):
                continue
            paragraph_count += 1
            text_length = len(str(texts[index])) if index < len(texts) else 0
            starts = [
                _as_int(item.get("visible_start", item.get("start")))
                for item in style.get("char_shape_runs", [])
                if isinstance(item, dict)
            ]
            run_count += len(starts)
            out_of_range_count += sum(start > text_length for start in starts)
            non_monotonic_count += sum(left > right for left, right in zip(starts, starts[1:]))
            missing_zero_start_count += int(bool(starts) and starts[0] != 0)
    checks = {
        "all_in_range": out_of_range_count == 0,
        "monotonic": non_monotonic_count == 0,
        "first_run_starts_at_zero": missing_zero_start_count == 0,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "paragraph_count": paragraph_count,
            "run_count": run_count,
            "out_of_range_count": out_of_range_count,
            "non_monotonic_count": non_monotonic_count,
            "missing_zero_start_count": missing_zero_start_count,
        },
    }


def _resolve_compatibility_profile(requested: str, gold_profile: dict[str, Any]) -> str:
    normalized = str(requested or "portable").strip().lower()
    if normalized in {"hancom", "portable"}:
        return normalized
    if normalized != "oracle":
        raise ValueError(f"unsupported_dry_run_compatibility_profile:{normalized}")
    producer_family = str(gold_profile.get("producer_family", "unknown"))
    return "hancom" if producer_family == "hancom" else "portable"


def _compare_model_to_generated(model: dict[str, Any], generated_profile: dict[str, Any]) -> dict[str, Any]:
    summary = model.get("summary", {})
    header_tags = generated_profile.get("header_aggregate_tags", generated_profile.get("aggregate_tags", {}))
    section_tags = generated_profile.get("section_aggregate_tags", {})
    checks = {
        "section_count": _as_int(summary.get("section_count")) == _as_int(generated_profile.get("section_count")),
        "paragraph_count": _as_int(summary.get("paragraph_count")) == _as_int(section_tags.get("p")),
        "run_count": _as_int(summary.get("char_shape_run_count")) == _as_int(section_tags.get("run")),
        "line_segment_count": _as_int(summary.get("line_segment_count")) == _as_int(section_tags.get("lineseg")),
        "table_count": _as_int(summary.get("table_count")) == _as_int(section_tags.get("tbl")),
        "table_row_count": _as_int(summary.get("table_row_count")) == _as_int(section_tags.get("tr")),
        "table_cell_count": _as_int(summary.get("table_cell_count")) == _as_int(section_tags.get("tc")),
        "sub_list_count": _as_int(summary.get("sub_list_count")) == _as_int(section_tags.get("subList")),
        "picture_count": _as_int(summary.get("picture_count")) == _as_int(section_tags.get("pic")),
        "page_def_count": _as_int(summary.get("page_def_count")) == _as_int(section_tags.get("pagePr")),
        "known_layout_control_count": _as_int(summary.get("known_layout_control_count")) == _as_int(section_tags.get("ctrl")),
        "bin_data_count": _as_int(summary.get("bin_data_count")) == _as_int(generated_profile.get("bin_data_count")),
        "char_pr_count": _as_int(summary.get("char_pr_count")) == _as_int(header_tags.get("charPr")),
        "para_pr_count": _as_int(summary.get("para_pr_count")) == _as_int(header_tags.get("paraPr")),
        "style_count": _as_int(summary.get("style_count")) == _as_int(header_tags.get("style")),
        "tab_pr_count": _as_int(summary.get("tab_pr_count")) == _as_int(header_tags.get("tabPr")),
        "numbering_count": _as_int(summary.get("numbering_count")) == _as_int(header_tags.get("numbering")),
        "bullet_count": _as_int(summary.get("bullet_count")) == _as_int(header_tags.get("bullet")),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
    }


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


def _compare_style_controls(
    model: dict[str, Any],
    generated_profile: dict[str, Any],
    gold_profile: dict[str, Any],
) -> dict[str, Any]:
    summary = model.get("summary", {})
    generated_tags = generated_profile.get("header_aggregate_tags", generated_profile.get("aggregate_tags", {}))
    gold_tags = gold_profile.get("header_aggregate_tags", gold_profile.get("aggregate_tags", {}))
    generated_refs = generated_profile.get("section_reference_counts", {})
    generated_distinct_refs = generated_profile.get("section_reference_distinct_counts", {})
    style_counts = {
        "model_char_shape_run_count": _as_int(summary.get("char_shape_run_count")),
        "generated_run_count": _as_int(generated_profile.get("section_aggregate_tags", {}).get("run")),
        "model_char_pr_count": _as_int(summary.get("char_pr_count")),
        "generated_char_pr_count": _as_int(generated_tags.get("charPr")),
        "gold_char_pr_count": _as_int(gold_tags.get("charPr")),
        "model_para_pr_count": _as_int(summary.get("para_pr_count")),
        "generated_para_pr_count": _as_int(generated_tags.get("paraPr")),
        "gold_para_pr_count": _as_int(gold_tags.get("paraPr")),
        "model_style_count": _as_int(summary.get("style_count")),
        "generated_style_count": _as_int(generated_tags.get("style")),
        "gold_style_count": _as_int(gold_tags.get("style")),
        "model_numbering_count": _as_int(summary.get("numbering_count")),
        "generated_numbering_count": _as_int(generated_tags.get("numbering")),
        "gold_numbering_count": _as_int(gold_tags.get("numbering")),
        "model_bullet_count": _as_int(summary.get("bullet_count")),
        "generated_bullet_count": _as_int(generated_tags.get("bullet")),
        "gold_bullet_count": _as_int(gold_tags.get("bullet")),
        "generated_char_pr_ref_count": _as_int(generated_refs.get("charPrIDRef")),
        "generated_para_pr_ref_count": _as_int(generated_refs.get("paraPrIDRef")),
        "generated_style_ref_count": _as_int(generated_refs.get("styleIDRef")),
        "generated_distinct_char_pr_refs": _as_int(generated_distinct_refs.get("charPrIDRef")),
        "generated_distinct_para_pr_refs": _as_int(generated_distinct_refs.get("paraPrIDRef")),
        "generated_distinct_style_refs": _as_int(generated_distinct_refs.get("styleIDRef")),
    }
    source_rich_style_signal = any(
        style_counts[key] > 1
        for key in (
            "model_char_shape_run_count",
            "model_char_pr_count",
            "model_para_pr_count",
            "model_style_count",
            "model_numbering_count",
            "model_bullet_count",
        )
    )
    checks = {
        "run_count_preserved": style_counts["model_char_shape_run_count"] == style_counts["generated_run_count"],
        "char_pr_count_preserved": style_counts["model_char_pr_count"] == style_counts["generated_char_pr_count"],
        "para_pr_count_preserved": style_counts["model_para_pr_count"] == style_counts["generated_para_pr_count"],
        "style_count_preserved": style_counts["model_style_count"] == style_counts["generated_style_count"],
        "numbering_count_preserved": style_counts["model_numbering_count"] == style_counts["generated_numbering_count"],
        "bullet_count_preserved": style_counts["model_bullet_count"] == style_counts["generated_bullet_count"],
        "paragraph_style_refs_written": style_counts["generated_para_pr_ref_count"] >= _as_int(summary.get("paragraph_count")),
        "run_style_refs_written": style_counts["generated_char_pr_ref_count"] >= style_counts["generated_run_count"],
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "source_rich_style_signal": source_rich_style_signal,
        "checks": checks,
        "counts": style_counts,
    }


def _compare_object_layout(
    model: dict[str, Any],
    generated_profile: dict[str, Any],
    gold_profile: dict[str, Any],
) -> dict[str, Any]:
    summary = model.get("summary", {})
    generated_tags = generated_profile.get("section_aggregate_tags", {})
    gold_tags = gold_profile.get("section_aggregate_tags", {})
    generated_ctrl_children = generated_profile.get("section_ctrl_child_counts", {})
    gold_ctrl_children = gold_profile.get("section_ctrl_child_counts", {})
    model_page_geometries = _model_page_geometries(model)
    generated_page_geometries = generated_profile.get("section_page_geometries", [])
    gold_page_geometries = gold_profile.get("section_page_geometries", [])
    counts = {
        "model_page_def_count": _as_int(summary.get("page_def_count")),
        "generated_page_pr_count": _as_int(generated_tags.get("pagePr")),
        "gold_page_pr_count": _as_int(gold_tags.get("pagePr")),
        "model_table_count": _as_int(summary.get("table_count")),
        "generated_table_count": _as_int(generated_tags.get("tbl")),
        "gold_table_count": _as_int(gold_tags.get("tbl")),
        "model_table_row_count": _as_int(summary.get("table_row_count")),
        "generated_table_row_count": _as_int(generated_tags.get("tr")),
        "gold_table_row_count": _as_int(gold_tags.get("tr")),
        "model_table_cell_count": _as_int(summary.get("table_cell_count")),
        "generated_table_cell_count": _as_int(generated_tags.get("tc")),
        "gold_table_cell_count": _as_int(gold_tags.get("tc")),
        "model_sub_list_count": _as_int(summary.get("sub_list_count")),
        "generated_sub_list_count": _as_int(generated_tags.get("subList")),
        "gold_sub_list_count": _as_int(gold_tags.get("subList")),
        "model_picture_count": _as_int(summary.get("picture_count")),
        "generated_picture_count": _as_int(generated_tags.get("pic")),
        "gold_picture_count": _as_int(gold_tags.get("pic")),
        "model_known_layout_control_count": _as_int(summary.get("known_layout_control_count")),
        "generated_known_layout_control_count": _as_int(generated_tags.get("ctrl")),
        "gold_ctrl_count": _as_int(gold_tags.get("ctrl")),
        "generated_col_pr_count": _as_int(generated_ctrl_children.get("colPr")),
        "gold_col_pr_count": _as_int(gold_ctrl_children.get("colPr")),
        "generated_field_begin_count": _as_int(generated_ctrl_children.get("fieldBegin")),
        "gold_field_begin_count": _as_int(gold_ctrl_children.get("fieldBegin")),
        "generated_field_end_count": _as_int(generated_ctrl_children.get("fieldEnd")),
        "gold_field_end_count": _as_int(gold_ctrl_children.get("fieldEnd")),
    }
    checks = {
        "page_pr_count_preserved": counts["model_page_def_count"] == counts["generated_page_pr_count"],
        "table_count_preserved": counts["model_table_count"] == counts["generated_table_count"],
        "table_rows_preserved": counts["model_table_row_count"] == counts["generated_table_row_count"],
        "table_cells_preserved": counts["model_table_cell_count"] == counts["generated_table_cell_count"],
        "sub_lists_preserved": counts["model_sub_list_count"] == counts["generated_sub_list_count"],
        "picture_count_preserved": counts["model_picture_count"] == counts["generated_picture_count"],
        "known_layout_controls_preserved": (
            counts["model_known_layout_control_count"] == counts["generated_known_layout_control_count"]
        ),
        "page_geometry_preserved": _page_geometries_match(model_page_geometries, generated_page_geometries),
        "table_rows_match_gold": counts["generated_table_row_count"] == counts["gold_table_row_count"],
        "table_cells_match_gold": counts["generated_table_cell_count"] == counts["gold_table_cell_count"],
        "sub_lists_close_to_gold": _close_count(
            counts["generated_sub_list_count"],
            counts["gold_sub_list_count"],
            tolerance=2,
        ),
        "pictures_match_gold": counts["generated_picture_count"] == counts["gold_picture_count"],
        "page_pr_count_matches_gold": counts["generated_page_pr_count"] == counts["gold_page_pr_count"],
        "field_begin_matches_gold": counts["generated_field_begin_count"] == counts["gold_field_begin_count"],
        "field_end_matches_gold": counts["generated_field_end_count"] == counts["gold_field_end_count"],
        "conservative_col_pr_not_over_gold": counts["generated_col_pr_count"] <= counts["gold_col_pr_count"],
        "conservative_col_pr_present_when_gold_present": (
            counts["gold_col_pr_count"] == 0 or counts["generated_col_pr_count"] > 0
        ),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "source_rich_layout_signal": any(
            counts[key] > 0
            for key in (
                "model_table_count",
                "model_table_row_count",
                "model_table_cell_count",
                "model_picture_count",
                "model_page_def_count",
                "model_known_layout_control_count",
            )
        ),
        "checks": checks,
        "counts": counts,
        "generated_ctrl_child_counts": {
            key: _as_int(value) for key, value in sorted(generated_ctrl_children.items())
        },
        "gold_ctrl_child_counts": {
            key: _as_int(value) for key, value in sorted(gold_ctrl_children.items())
        },
        "page_geometry_counts": {
            "model": len(model_page_geometries),
            "generated": len(generated_page_geometries) if isinstance(generated_page_geometries, list) else 0,
            "gold": len(gold_page_geometries) if isinstance(gold_page_geometries, list) else 0,
        },
    }


def _model_page_geometries(model: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for section in model.get("sections", []):
        if not isinstance(section, dict):
            continue
        for page_definition in section.get("page_definitions", []):
            if isinstance(page_definition, dict):
                result.append(page_definition)
    return result


def _page_geometries_match(expected: list[dict[str, Any]], observed: Any) -> bool:
    if not isinstance(observed, list) or len(expected) != len(observed):
        return False
    for left, right in zip(expected, observed):
        if _as_int(left.get("width")) != _as_int(right.get("width")):
            return False
        if _as_int(left.get("height")) != _as_int(right.get("height")):
            return False
        left_margin = left.get("margin", {}) if isinstance(left.get("margin"), dict) else {}
        right_margin = right.get("margin", {}) if isinstance(right.get("margin"), dict) else {}
        for key in ("left", "right", "top", "bottom", "header", "footer", "gutter"):
            if _as_int(left_margin.get(key)) != _as_int(right_margin.get(key)):
                return False
    return True


def _close_count(left: int, right: int, *, tolerance: int) -> bool:
    return abs(left - right) <= tolerance


def _model_text_payload(model: dict[str, Any]) -> dict[str, Any]:
    paragraphs: list[str] = []
    for section in model.get("sections", []):
        if isinstance(section, dict):
            paragraphs.extend(str(item) for item in section.get("paragraph_texts", []))
    joined = "\n".join(item for item in paragraphs if item)
    return {
        "status": model.get("text_extraction_status", "unknown"),
        "text": joined,
        "paragraph_count": len(paragraphs),
        "text_char_count": model.get("summary", {}).get("text_char_count", 0),
    }


def _safe_output_ref(output_root: Path) -> str:
    parts = output_root.parts
    if "outputs" in parts:
        index = parts.index("outputs")
        return Path(*parts[index:]).as_posix()
    return "configured_output_root"
