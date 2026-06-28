from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PRESET_ROOT = Path("_ai_system") / "document_presets"
INDEX_PATH = PRESET_ROOT / "INDEX.json"

STAGE_TO_PRESET_STAGE = {
    "interview": "prd",
    "architect": "toc",
    "source": "toc",
    "chapter": "workpack",
    "visual": "visual_data",
    "chart": "visual_data",
    "design": "design",
    "assemble": "review",
    "review": "review",
    "export": "review",
    "cloud": "review",
    "prd": "prd",
    "toc": "toc",
    "workpack": "workpack",
    "visual_data": "visual_data",
    "design": "design",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def normalize(value: str) -> str:
    return re.sub(r"[\s_-]+", "", value.casefold().strip())


def rel(path: Path) -> str:
    return path.as_posix()


def load_index(root: Path = PRESET_ROOT) -> dict[str, Any]:
    index_path = root / "INDEX.json"
    if not index_path.exists():
        raise FileNotFoundError(f"missing document preset index: {index_path.as_posix()}")
    return read_json(index_path)


def load_preset(preset_id: str, root: Path = PRESET_ROOT) -> dict[str, Any]:
    path = root / preset_id / "preset.json"
    if not path.exists():
        return {}
    return read_json(path)


def preset_stage_for_workflow_stage(stage: str) -> str:
    return STAGE_TO_PRESET_STAGE.get(stage, stage)


def _asset_items(preset_id: str, asset_paths: list[str], role: str, root: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for asset in asset_paths:
        asset_path = root / preset_id / asset
        items.append(
            {
                "path": rel(asset_path),
                "role": role,
                "exists": "yes" if asset_path.exists() else "no",
            }
        )
    return items


def _index_asset_items(asset_paths: list[str], role: str, root: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for asset in asset_paths:
        asset_path = root / asset
        items.append(
            {
                "path": rel(asset_path),
                "role": role,
                "exists": "yes" if asset_path.exists() else "no",
            }
        )
    return items


def include_language_guidance(output_language: str) -> bool:
    return output_language.strip().casefold() in {"en", "mixed"}


def stage_assets_for_preset(
    preset_id: str,
    stage: str,
    *,
    root: Path = PRESET_ROOT,
    include_metadata: bool = True,
    index_entry: dict[str, Any] | None = None,
    output_language: str = "",
) -> dict[str, Any]:
    preset = load_preset(preset_id, root)
    preset_stage = preset_stage_for_workflow_stage(stage)
    assets: list[dict[str, str]] = []
    if include_metadata:
        preset_json = root / preset_id / "preset.json"
        assets.append(
            {
                "path": rel(preset_json),
                "role": "document preset metadata",
                "exists": "yes" if preset_json.exists() else "no",
            }
        )
    overlays = preset.get("stage_overlays", {}) if isinstance(preset.get("stage_overlays"), dict) else {}
    listed = overlays.get(preset_stage, [])
    if isinstance(listed, str):
        listed = [listed]
    if not isinstance(listed, list):
        listed = []
    assets.extend(_asset_items(preset_id, [str(item) for item in listed], f"document preset {preset_stage} guidance", root))
    if preset_stage == "design":
        design_assets = []
        if isinstance(index_entry, dict):
            read_for_design = index_entry.get("read_for_design", [])
            if isinstance(read_for_design, str):
                design_assets = [read_for_design]
            elif isinstance(read_for_design, list):
                design_assets = [str(item) for item in read_for_design if isinstance(item, str)]
        if not design_assets:
            fallback = root / preset_id / "design_patterns.md"
            if fallback.exists():
                design_assets = [f"{preset_id}/design_patterns.md"]
        assets.extend(_index_asset_items(design_assets, "document preset design guidance", root))
    if include_language_guidance(output_language):
        language_assets: list[str] = []
        if isinstance(index_entry, dict):
            listed_language = index_entry.get("language_guidance", [])
            if isinstance(listed_language, str):
                language_assets = [listed_language]
            elif isinstance(listed_language, list):
                language_assets = [str(item) for item in listed_language if isinstance(item, str)]
        if not language_assets:
            fallback = root / preset_id / "language_guidance.md"
            if fallback.exists():
                language_assets = [f"{preset_id}/language_guidance.md"]
        assets.extend(_index_asset_items(language_assets, "document preset language guidance", root))
    return {
        "preset_stage": preset_stage,
        "assets": assets,
    }


def workflow_assets_for_preset(index_entry: dict[str, Any], root: Path = PRESET_ROOT) -> list[dict[str, str]]:
    asset_paths: list[str] = []
    listed = index_entry.get("read_for_workflow", [])
    if isinstance(listed, str):
        asset_paths = [listed]
    elif isinstance(listed, list):
        asset_paths = [str(item) for item in listed if isinstance(item, str)]
    preset_id = str(index_entry.get("preset_id", ""))
    if not asset_paths and preset_id:
        fallback = root / preset_id / "stage_overlays.md"
        if fallback.exists():
            asset_paths = [f"{preset_id}/stage_overlays.md"]
    return _index_asset_items(asset_paths, "document preset workflow guidance", root)


def automation_status(preset: dict[str, Any]) -> dict[str, str]:
    integration_status = str(preset.get("integration_status") or "workflow_supported").strip()
    if integration_status == "module_only":
        return {
            "integration_status": "module_only",
            "workflow_automation": "not_enabled",
            "note": "This preset can route read guidance, but it does not enable automatic workflow or tool execution.",
        }
    return {
        "integration_status": integration_status,
        "workflow_automation": "available_for_existing_base_flow",
        "note": "Use the existing report workflow; this preset does not add unsupported automatic actions.",
    }


def _hold_match(query: str, index: dict[str, Any]) -> dict[str, Any] | None:
    normalized = normalize(query)
    if not normalized:
        return None
    for candidate in index.get("hold_candidates", []):
        if not isinstance(candidate, dict):
            continue
        values = [
            str(candidate.get("candidate_id", "")),
            str(candidate.get("label_ko", "")),
            *[str(alias) for alias in candidate.get("aliases", []) if isinstance(alias, str)],
        ]
        normalized_values = [normalize(value) for value in values if value]
        if any(
            value == normalized or normalized in value or value in normalized
            for value in normalized_values
            if value
        ):
            return candidate
    return None


def _preset_match(query: str, index: dict[str, Any]) -> dict[str, Any] | None:
    normalized = normalize(query)
    exact_alias_match: dict[str, Any] | None = None
    contains_match: dict[str, Any] | None = None
    reverse_contains_match: dict[str, Any] | None = None
    reverse_contains_length = 0
    for preset in index.get("presets", []):
        if not isinstance(preset, dict):
            continue
        values = [
            str(preset.get("preset_id", "")),
            str(preset.get("label_ko", "")),
            *[str(alias) for alias in preset.get("aliases", []) if isinstance(alias, str)],
        ]
        normalized_values = [normalize(value) for value in values if value]
        if normalized in normalized_values:
            exact_alias_match = preset
            break
        if not contains_match and any(normalized and normalized in value for value in normalized_values):
            contains_match = preset
        for value in normalized_values:
            if len(value) >= 4 and value in normalized and len(value) > reverse_contains_length:
                reverse_contains_match = preset
                reverse_contains_length = len(value)
    return exact_alias_match or contains_match or reverse_contains_match


def query_document_preset(query: str, stage: str = "", root: Path = PRESET_ROOT, output_language: str = "") -> dict[str, Any]:
    index = load_index(root)
    hold = _hold_match(query, index)
    if hold:
        return {
            "status": "hold_candidate",
            "query": query,
            "candidate": hold,
            "supported_route": False,
            "automation": {
                "workflow_automation": "not_enabled",
                "note": "This document type is intentionally held out of supported preset routing.",
            },
            "stage_assets": [],
        }

    match = _preset_match(query, index)
    if not match:
        return {
            "status": "not_found",
            "query": query,
            "supported_route": False,
            "automation": {
                "workflow_automation": "not_enabled",
                "note": "No matching document preset was found.",
            },
            "stage_assets": [],
        }

    preset_id = str(match.get("preset_id", ""))
    preset = load_preset(preset_id, root)
    stage_payload = (
        stage_assets_for_preset(preset_id, stage, root=root, index_entry=match, output_language=output_language)
        if stage
        else {"preset_stage": "", "assets": []}
    )
    return {
        "status": "matched",
        "query": query,
        "supported_route": str(match.get("status", "")) == "supported",
        "preset": {
            "preset_id": preset_id,
            "label_ko": match.get("label_ko", ""),
            "status": match.get("status", ""),
            "base_flow": match.get("base_flow", ""),
            "default_artifact_workflow_mode": match.get("default_artifact_workflow_mode", ""),
            "module_path": match.get("module_path", ""),
            "recommended_cover_preset": preset.get("recommended_cover_preset", ""),
            "quality_emphasis": preset.get("quality_emphasis", []),
        },
        "automation": automation_status(preset),
        "workflow_assets": workflow_assets_for_preset(match, root),
        "workflow_note": "Use workflow assets to decide which stages are required, compressed, skipped, or replaced for the selected artifact type.",
        "preset_stage": stage_payload["preset_stage"],
        "stage_assets": stage_payload["assets"],
        "language": {
            "output_language": output_language,
            "language_guidance_included": include_language_guidance(output_language),
            "note": "Language guidance is a reader-fit layer over the same preset. It does not enable translation or rewrite automation.",
        },
        "read_policy": "Read INDEX.json, then only the selected preset metadata and current-stage assets.",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Route a document-type query to a document preset without opening every preset folder.")
    parser.add_argument("query", nargs="?", default="", help="Preset id, Korean label, or alias to resolve.")
    parser.add_argument("--query", dest="query_flag", default="", help="Preset id, Korean label, or alias to resolve.")
    parser.add_argument("--stage", default="", help="Report workflow stage or preset stage to include stage-specific assets.")
    parser.add_argument("--output-language", default="", choices=["", "ko", "en", "mixed", "undecided"], help="Include language_guidance.md when the resolved output language is en or mixed.")
    args = parser.parse_args()
    query = args.query_flag or args.query
    if not query:
        parser.error("provide a query or --query")
    payload = query_document_preset(query, args.stage, output_language=args.output_language)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "matched":
        return 0
    if payload["status"] == "hold_candidate":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
