"""Public-safe HWPX corpus inventory for HTML/HWPX reverse engineering."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

from .corpus import ExactPair, discover_exact_pairs
from .hwpx_profile import profile_hwpx_file


INVENTORY_SCHEMA_VERSION = "owned_html_hwpx_corpus_inventory.v1"
PILOT_SIZE = 10


def build_html_hwpx_corpus_inventory(
    root: Path,
    *,
    visual_pairs: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Path]]:
    """Return a path-free inventory and an in-memory ref-to-path lookup."""

    root = root.resolve()
    exact_pairs = discover_exact_pairs(root, recursive=True)
    pair_by_hwpx = {pair.hwpx_path.resolve(): pair for pair in exact_pairs}
    visual_pairs = visual_pairs or {}
    documents: list[dict[str, Any]] = []
    path_lookup: dict[str, Path] = {}

    for path in sorted(root.rglob("*.hwpx"), key=lambda item: str(item).lower()):
        resolved = path.resolve()
        pair = pair_by_hwpx.get(resolved)
        document_ref = pair.pair_ref if pair else _standalone_ref(path)
        profile = profile_hwpx_file(path)
        features = _feature_flags(profile)
        visual = visual_pairs.get(document_ref, {})
        document = {
            "document_ref": document_ref,
            "paired_hwp_available": pair is not None,
            "producer_family": str(profile.get("producer_family", "unknown")),
            "status": str(profile.get("status", "unknown")),
            "section_count": int(profile.get("section_count", 0)),
            "text_char_count_bucket": _count_bucket(int(profile.get("section_text_char_count", 0))),
            "bin_data_count_bucket": _count_bucket(int(profile.get("bin_data_count", 0))),
            "feature_count": sum(1 for value in features.values() if value),
            "features": features,
            "native_gold_page_count": int(visual.get("gold_page_count", 0)),
        }
        documents.append(document)
        path_lookup[document_ref] = path

    ordered_for_split = sorted(
        documents,
        key=lambda item: sha256(str(item["document_ref"]).encode("utf-8")).hexdigest(),
    )
    discovery_count = round(len(ordered_for_split) * 0.7)
    discovery_refs = {str(item["document_ref"]) for item in ordered_for_split[:discovery_count]}
    for document in documents:
        document["split"] = "discovery" if document["document_ref"] in discovery_refs else "holdout"

    pilot_refs = _select_pilot_documents(documents, limit=min(PILOT_SIZE, discovery_count))
    for document in documents:
        document["pilot_selected"] = document["document_ref"] in pilot_refs

    feature_counts: Counter[str] = Counter()
    for document in documents:
        feature_counts.update(name for name, present in document["features"].items() if present)

    checks = {
        "fixture_count_is_61": len(documents) == 61,
        "all_packages_profiled": all(str(item["status"]).startswith("profiled") for item in documents),
        "all_document_refs_unique": len(path_lookup) == len(documents),
        "discovery_and_holdout_present": len(discovery_refs) > 0 and len(discovery_refs) < len(documents),
        "pilot_count_is_10": len(pilot_refs) == PILOT_SIZE,
        "pilot_uses_discovery_only": all(
            item["split"] == "discovery" for item in documents if item["pilot_selected"]
        ),
        "pilot_has_native_visual_baseline": all(
            item["native_gold_page_count"] > 0 for item in documents if item["pilot_selected"]
        ),
    }
    report = {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "status": "pass" if all(checks.values()) else "fail",
        "summary": {
            "document_count": len(documents),
            "exact_pair_count": len(exact_pairs),
            "standalone_hwpx_count": len(documents) - len(exact_pairs),
            "discovery_count": len(discovery_refs),
            "holdout_count": len(documents) - len(discovery_refs),
            "pilot_count": len(pilot_refs),
            "producer_family_counts": dict(sorted(Counter(
                str(item["producer_family"]) for item in documents
            ).items())),
            "feature_counts": dict(sorted(feature_counts.items())),
        },
        "checks": checks,
        "pilot_document_refs": pilot_refs,
        "documents": sorted(documents, key=lambda item: str(item["document_ref"])),
        "artifact_policy": {
            "paths_in_report": False,
            "filenames_in_report": False,
            "raw_document_text_in_report": False,
            "path_lookup_returned_in_memory_only": True,
        },
    }
    return report, path_lookup


def _standalone_ref(path: Path) -> str:
    digest = sha256(path.read_bytes()).hexdigest()
    return f"owned_hwpx_doc_{digest[:24]}"


def _feature_flags(profile: dict[str, Any]) -> dict[str, bool]:
    tags = profile.get("section_aggregate_tags", {})
    control_counts = profile.get("section_ctrl_child_counts", {})
    style_semantics = profile.get("style_semantics", {})
    style_counts = style_semantics.get("counts", {}) if isinstance(style_semantics, dict) else {}
    table_semantics = profile.get("table_semantics", [])
    object_semantics = profile.get("object_semantics", [])
    footnote_semantics = profile.get("footnote_control_semantics", [])
    compose_semantics = profile.get("compose_control_semantics", [])
    page_hiding_semantics = profile.get("page_hiding_semantics", [])
    return {
        "multi_section": int(profile.get("section_count", 0)) > 1,
        "long_text": int(profile.get("section_text_char_count", 0)) >= 5000,
        "rich_character_styles": int(style_counts.get("char_shape_count", 0)) >= 24,
        "rich_paragraph_styles": int(style_counts.get("para_shape_count", 0)) >= 24,
        "lists": int(tags.get("numbering", 0)) > 0 or int(tags.get("bullet", 0)) > 0,
        "tables": _semantic_count(table_semantics, "table_count") > 0,
        "merged_or_nested_tables": (
            _semantic_count(table_semantics, "merged_cell_count") > 0
            or _semantic_count(table_semantics, "nested_table_count") > 0
        ),
        "table_captions": _semantic_count(table_semantics, "caption_count") > 0,
        "binary_data": int(profile.get("bin_data_count", 0)) > 0,
        "pictures": _semantic_count(object_semantics, "picture_count") > 0,
        "shapes": _semantic_count(object_semantics, "shape_count") > 0,
        "columns": int(tags.get("colPr", 0)) > 0,
        "headers_or_footers": int(control_counts.get("header", 0)) > 0 or int(control_counts.get("footer", 0)) > 0,
        "footnotes": _semantic_count(footnote_semantics, "footnote_count") > 0,
        "fields": int(tags.get("fieldBegin", 0)) > 0 or int(tags.get("fieldEnd", 0)) > 0,
        "page_numbering": int(tags.get("pageNum", 0)) > 0 or int(tags.get("autoNum", 0)) > 0,
        "inline_controls": any(int(tags.get(name, 0)) > 0 for name in ("tab", "lineBreak", "hyphen", "nbSpace", "fwSpace")),
        "compose_controls": _semantic_count(compose_semantics, "compose_count") > 0,
        "page_hiding": _semantic_count(page_hiding_semantics, "page_hiding_count") > 0,
    }


def _semantic_count(value: Any, key: str) -> int:
    if isinstance(value, list):
        return sum(_semantic_count(item, key) for item in value)
    if not isinstance(value, dict):
        return 0
    counts = value.get("counts", {})
    return int(counts.get(key, 0)) if isinstance(counts, dict) else 0


def _select_pilot_documents(documents: list[dict[str, Any]], *, limit: int) -> list[str]:
    eligible = [
        item for item in documents
        if item["split"] == "discovery"
        and item["paired_hwp_available"]
        and item["native_gold_page_count"] > 0
    ]
    selected: list[dict[str, Any]] = []
    covered: set[str] = set()

    for family in ("hancom", "portable"):
        family_items = [item for item in eligible if item["producer_family"] == family]
        if family_items:
            choice = max(family_items, key=_pilot_sort_key)
            selected.append(choice)
            covered.update(name for name, present in choice["features"].items() if present)

    while len(selected) < limit:
        candidates = [item for item in eligible if item not in selected]
        if not candidates:
            break
        choice = max(
            candidates,
            key=lambda item: (
                sum(1 for name, present in item["features"].items() if present and name not in covered),
                *_pilot_sort_key(item),
            ),
        )
        selected.append(choice)
        covered.update(name for name, present in choice["features"].items() if present)

    return [str(item["document_ref"]) for item in selected]


def _pilot_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(item["feature_count"]),
        int(item["native_gold_page_count"]),
        str(item["document_ref"]),
    )


def _count_bucket(value: int) -> str:
    if value <= 0:
        return "none"
    if value < 100:
        return "small"
    if value < 1000:
        return "medium"
    if value < 10000:
        return "large"
    return "very_large"
