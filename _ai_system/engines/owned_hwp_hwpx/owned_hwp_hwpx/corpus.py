"""Public-safe corpus baseline for exact HWP/HWPX pairs."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from .hwp_probe import probe_hwp_file
from .hwpx_profile import profile_hwpx_file


@dataclass(frozen=True)
class ExactPair:
    pair_ref: str
    hwp_path: Path
    hwpx_path: Path


def _pair_ref(stem: str) -> str:
    digest = sha256(stem.lower().encode("utf-8")).hexdigest()
    return f"owned_hwp_pair_{digest[:24]}"


def _safe_size_bucket(size_bytes: int) -> str:
    if size_bytes < 16 * 1024:
        return "lt_16kb"
    if size_bytes < 128 * 1024:
        return "lt_128kb"
    if size_bytes < 1024 * 1024:
        return "lt_1mb"
    if size_bytes < 10 * 1024 * 1024:
        return "lt_10mb"
    return "gte_10mb"


def discover_exact_pairs(root: Path, *, recursive: bool = False) -> list[ExactPair]:
    """Find exact stem-matched HWP/HWPX pairs under a corpus root."""

    pattern_iter = root.rglob("*") if recursive else root.iterdir()
    hwp_by_stem: dict[str, Path] = {}
    hwpx_by_stem: dict[str, Path] = {}

    for path in pattern_iter:
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".hwp", ".hwpx"}:
            continue
        key = path.stem.lower()
        if suffix == ".hwp":
            hwp_by_stem.setdefault(key, path)
        else:
            hwpx_by_stem.setdefault(key, path)

    pairs: list[ExactPair] = []
    for stem in sorted(set(hwp_by_stem) & set(hwpx_by_stem)):
        pairs.append(
            ExactPair(
                pair_ref=_pair_ref(stem),
                hwp_path=hwp_by_stem[stem],
                hwpx_path=hwpx_by_stem[stem],
            )
        )
    return pairs


def _profile_pair(pair: ExactPair) -> dict[str, Any]:
    hwp_stat = pair.hwp_path.stat()
    hwpx_stat = pair.hwpx_path.stat()
    hwp_probe = probe_hwp_file(pair.hwp_path)
    hwpx_profile = profile_hwpx_file(pair.hwpx_path)

    return {
        "pair_ref": pair.pair_ref,
        "hwp_size_bucket": _safe_size_bucket(hwp_stat.st_size),
        "hwpx_size_bucket": _safe_size_bucket(hwpx_stat.st_size),
        "hwp_probe": {
            "status": hwp_probe["status"],
            "is_ole_cfb": hwp_probe["is_ole_cfb"],
            "size_bucket": hwp_probe["size_bucket"],
            "magic_probe": hwp_probe.get("magic_probe", "unknown"),
        },
        "hwpx_profile": hwpx_profile,
    }


def build_corpus_baseline(
    root: Path,
    *,
    recursive: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """Build a public-safe baseline report for exact HWP/HWPX pairs."""

    root = root.resolve()
    pairs = discover_exact_pairs(root, recursive=recursive)
    selected_pairs = pairs[:limit] if limit is not None else pairs
    pair_profiles = [_profile_pair(pair) for pair in selected_pairs]

    profiled_hwpx = sum(
        1
        for item in pair_profiles
        if str(item["hwpx_profile"].get("status", "")).startswith("profiled")
    )
    hwp_ole_count = sum(1 for item in pair_profiles if item["hwp_probe"]["is_ole_cfb"])
    xml_error_pairs = sum(
        1 for item in pair_profiles if item["hwpx_profile"].get("parse_error_count", 0)
    )

    return {
        "schema_version": "owned_hwp_hwpx_corpus_baseline.v1",
        "status": "baseline_built",
        "public_safety": {
            "paths_in_report": False,
            "filenames_in_report": False,
            "raw_document_text_in_report": False,
        },
        "corpus_root_digest": sha256(str(root).lower().encode("utf-8")).hexdigest()[:16],
        "recursive": recursive,
        "limit": limit,
        "summary": {
            "exact_pair_count": len(pairs),
            "evaluated_pair_count": len(pair_profiles),
            "profiled_hwpx_count": profiled_hwpx,
            "hwp_ole_cfb_count": hwp_ole_count,
            "hwpx_xml_error_pair_count": xml_error_pairs,
        },
        "pairs": pair_profiles,
    }
