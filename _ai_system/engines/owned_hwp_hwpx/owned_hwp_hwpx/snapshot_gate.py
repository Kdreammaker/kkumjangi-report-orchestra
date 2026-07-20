"""Deterministic structural snapshots for generated and gold HWPX profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any


SNAPSHOT_METRICS = (
    "section_count",
    "paragraph_count",
    "run_count",
    "line_segment_count",
    "table_count",
    "table_row_count",
    "table_cell_count",
    "sub_list_count",
    "picture_count",
    "page_property_count",
    "page_width_sum",
    "page_height_sum",
    "page_margin_sum",
    "binary_count",
)


def metrics_from_hwpx_profile(profile: dict[str, Any]) -> dict[str, int]:
    section_tags = profile.get("section_aggregate_tags", {})
    page_geometries = profile.get("section_page_geometries", [])
    return {
        "section_count": _as_int(profile.get("section_count")),
        "paragraph_count": _as_int(section_tags.get("p")),
        "run_count": _as_int(section_tags.get("run")),
        "line_segment_count": _as_int(section_tags.get("lineseg")),
        "table_count": _as_int(section_tags.get("tbl")),
        "table_row_count": _as_int(section_tags.get("tr")),
        "table_cell_count": _as_int(section_tags.get("tc")),
        "sub_list_count": _as_int(section_tags.get("subList")),
        "picture_count": _as_int(section_tags.get("pic")),
        "page_property_count": _as_int(section_tags.get("pagePr")),
        "page_width_sum": _page_geometry_sum(page_geometries, "width"),
        "page_height_sum": _page_geometry_sum(page_geometries, "height"),
        "page_margin_sum": _page_margin_sum(page_geometries),
        "binary_count": _as_int(profile.get("bin_data_count")),
    }


def compare_snapshot_metrics(gold_profile: dict[str, Any], generated_profile: dict[str, Any]) -> dict[str, Any]:
    gold = metrics_from_hwpx_profile(gold_profile)
    generated = metrics_from_hwpx_profile(generated_profile)
    metric_scores = {
        metric: _metric_score(gold[metric], generated[metric])
        for metric in SNAPSHOT_METRICS
    }
    score = round(sum(metric_scores.values()) / len(metric_scores), 4)
    return {
        "status": "compared",
        "score": score,
        "gold_metrics": gold,
        "generated_metrics": generated,
        "metric_scores": metric_scores,
    }


def write_snapshot_svgs(
    output_dir: Path,
    pair_ref: str,
    gold_profile: dict[str, Any],
    generated_profile: dict[str, Any],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    gold_metrics = metrics_from_hwpx_profile(gold_profile)
    generated_metrics = metrics_from_hwpx_profile(generated_profile)
    gold_path = output_dir / f"{pair_ref}-gold.svg"
    generated_path = output_dir / f"{pair_ref}-generated.svg"
    gold_path.write_text(_snapshot_svg("gold", gold_metrics), encoding="utf-8")
    generated_path.write_text(_snapshot_svg("generated", generated_metrics), encoding="utf-8")
    return {
        "status": "written",
        "snapshot_count": 2,
    }


def _snapshot_svg(label: str, metrics: dict[str, int]) -> str:
    width = 760
    height = 64 + (len(SNAPSHOT_METRICS) * 28)
    max_value = max(1, max(metrics.values()))
    bars = []
    for index, metric in enumerate(SNAPSHOT_METRICS):
        value = metrics[metric]
        bar_width = 1 + round((value / max_value) * 540)
        y = 46 + index * 28
        bars.append(
            f'<text x="24" y="{y + 14}" font-size="12" fill="#111827">{_escape(metric)}</text>'
            f'<rect x="210" y="{y}" width="{bar_width}" height="16" fill="#3b82f6"/>'
            f'<text x="{220 + bar_width}" y="{y + 13}" font-size="12" fill="#111827">{value}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" viewBox="0 0 760 {height}">'
        f'<rect x="0" y="0" width="760" height="{height}" fill="#ffffff"/>'
        f'<text x="24" y="28" font-size="16" font-weight="700" fill="#111827">owned-hwp-hwpx structural snapshot: {_escape(label)}</text>'
        + "".join(bars)
        + "</svg>\n"
    )


def _metric_score(gold_value: int, generated_value: int) -> float:
    if gold_value == generated_value:
        return 1.0
    scale = max(1, abs(gold_value), abs(generated_value))
    return round(max(0.0, 1.0 - (abs(gold_value - generated_value) / scale)), 4)


def _escape(value: Any) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _page_geometry_sum(page_geometries: Any, key: str) -> int:
    if not isinstance(page_geometries, list):
        return 0
    return sum(_as_int(item.get(key)) for item in page_geometries if isinstance(item, dict))


def _page_margin_sum(page_geometries: Any) -> int:
    if not isinstance(page_geometries, list):
        return 0
    total = 0
    for item in page_geometries:
        if not isinstance(item, dict):
            continue
        margin = item.get("margin", {})
        if isinstance(margin, dict):
            total += sum(_as_int(margin.get(key)) for key in ("left", "right", "top", "bottom", "header", "footer", "gutter"))
    return total


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
