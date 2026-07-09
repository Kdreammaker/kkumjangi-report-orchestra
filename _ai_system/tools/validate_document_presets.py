from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from query_document_preset import PRESET_ROOT, load_index, load_preset, normalize, query_document_preset


REQUIRED_PRESET_FILES = ["preset.json", "prd_questions.md", "stage_overlays.md", "validation_checklist.md"]
ALLOWED_PRESET_STATUS = {"supported"}
ALLOWED_INTEGRATION_STATUS = {"", "module_only", "workflow_supported"}
ALLOWED_ARTIFACT_WORKFLOW_MODES = {"brief", "standard", "substantial", "specialized"}
MODULE_ONLY_IDS = {
    "investor_brief",
    "equity_research",
    "business_proposal",
    "product_manual",
    "guide_document",
    "book_manuscript",
    "education_curriculum",
    "academic_paper",
    "press_release",
}
DESIGN_QUERY_CASES = {
    "IR 설명자료": "_ai_system/document_presets/investor_brief/design_patterns.md",
    "보도자료": "_ai_system/document_presets/press_release/design_patterns.md",
    "프로듀서 바이블": "_ai_system/document_presets/guide_document/design_patterns.md",
    "출판 원고": "_ai_system/document_presets/book_manuscript/design_patterns.md",
}
DESCRIPTIVE_QUERY_CASES = {
    "일반 사용자가 따라할 수 있는 설치 가이드": "product_manual",
    "세계관 프로듀서 바이블을 Word import용 가이드 문서로 정리": "guide_document",
    "소설 원고를 출판용 장 구조로 정리": "book_manuscript",
    "팀 내부 개발자와 PM에게 나눠줄 학습자 핸드아웃": "education_curriculum",
    "외부 언론에 배포할 공식 발표문": "press_release",
}
LIST_STYLE_REQUIRED_IDS = {
    "formal_outline",
    "guide_outline",
    "procedure_steps",
    "administrative_outline",
    "symbol_bullets",
}
LIST_STYLE_ALLOWED_PARENTHESES = {")", "()"}
LANGUAGE_GUIDANCE_IDS = {"business_proposal", "investor_brief", "equity_research", "press_release"}
LANGUAGE_GUIDANCE_TERMS = ["English", "Korean", "Protected Spans", "disclaimer", "Source:", "Accessed"]
PRESET_LANGUAGE_GUIDANCE_TERMS = {
    "investor_brief": [
        "forward-looking",
        "not an offer",
        "investment advice",
        "buy",
        "sell",
        "hold",
        "target price",
        "rating",
        "data as of",
        "currency",
        "unit",
        "source date",
        "jurisdiction",
        "distribution",
    ],
    "equity_research": [
        "forward-looking",
        "not an offer",
        "investment advice",
        "buy",
        "sell",
        "hold",
        "target price",
        "rating",
        "data as of",
        "currency",
        "unit",
        "source date",
        "jurisdiction",
        "distribution",
    ],
}
HOLD_QUERY_CASES = ["견적", "견적서", "뉴스레터", "이력서", "경력기술서", "이력서/경력기술서"]
DESIGN_EXPORT_REQUIRED_TERMS = {
    "investor_brief": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "KPI",
            "public",
            "confidential",
            "cap-table",
            "investor Q&A",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "public/confidential",
            "cap-table",
        ],
    },
    "equity_research": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "peer table",
            "valuation multiple",
            "sensitivity",
            "earnings bridge",
            "catalyst/risk",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "target price",
            "rating",
            "landscape candidate",
        ],
    },
    "business_proposal": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "milestone timeline",
            "scope matrix",
            "R&R",
            "SOW",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "quotation",
            "contract",
            "SOW",
        ],
    },
    "product_manual": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "warning",
            "caution",
            "note",
            "troubleshooting",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "warning",
            "caution",
            "note",
            "compatibility",
        ],
    },
    "guide_document": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "producer",
            "locked",
            "guide_outline",
            "symbol_bullets",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "producer-only",
            "locked",
            "list preset",
        ],
    },
    "book_manuscript": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "novels",
            "nonfiction",
            "formal_outline",
            "symbol_bullets",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "manuscript",
            "publishing",
            "list preset",
        ],
    },
    "education_curriculum": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "teacher guide",
            "student handout",
            "learning objective",
            "reflection",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "teacher guide",
            "student handout",
            "child-facing",
        ],
    },
    "academic_paper": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "abstract",
            "methodology",
            "results",
            "discussion",
            "references",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "SEQ captions",
            "PAGE/NUMPAGES",
            "DOI",
        ],
    },
    "press_release": {
        "design_patterns.md": [
            "Design Application Priorities",
            "AI Judgment Needed",
            "Deferred Export-Native Features",
            "FOR IMMEDIATE RELEASE",
            "EMBARGOED",
            "dateline",
            "approved quote",
        ],
        "validation_checklist.md": [
            "Design And Export-Safe Checkpoints",
            "AI judgment",
            "Deferred export-native features",
            "즉시 배포",
            "엠바고",
            "media contact",
        ],
    },
}


def rel(path: Path) -> str:
    return path.as_posix()


def list_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str)]
    return []


def validate_list_style_presets(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    path = root / "list_style_presets.json"
    doc_path = root / "LIST_STYLE_PRESETS.md"
    if not path.exists():
        return {
            "status": "fail",
            "preset_count": 0,
            "errors": [f"missing list style preset contract: {rel(path)}"],
            "warnings": warnings,
        }
    if not doc_path.exists():
        errors.append(f"missing list style preset documentation: {rel(doc_path)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "status": "fail",
            "preset_count": 0,
            "errors": [f"invalid list_style_presets.json: {exc}"],
            "warnings": warnings,
        }
    presets = payload.get("presets", [])
    if not isinstance(presets, list):
        errors.append("list_style_presets.json presets must be a list")
        presets = []
    constraints = payload.get("constraints", {})
    parenthesis_forms = set()
    if isinstance(constraints, dict):
        forms = constraints.get("parenthesis_forms", [])
        if isinstance(forms, list):
            parenthesis_forms = {str(item) for item in forms}
    if parenthesis_forms != LIST_STYLE_ALLOWED_PARENTHESES:
        errors.append("list style parenthesis_forms must be exactly ')' and '()'")

    seen_ids: set[str] = set()
    for preset in presets:
        if not isinstance(preset, dict):
            errors.append("list_style_presets.json contains a non-object preset")
            continue
        preset_id = str(preset.get("preset_id", "")).strip()
        if not preset_id:
            errors.append("list style preset missing preset_id")
            continue
        if preset_id in seen_ids:
            errors.append(f"duplicate list style preset_id: {preset_id}")
        seen_ids.add(preset_id)
        levels = preset.get("levels", [])
        if not isinstance(levels, list) or len(levels) != 4:
            errors.append(f"{preset_id}: list style preset must define exactly 4 levels")
            continue
        expected_level = 1
        for level in levels:
            if not isinstance(level, dict):
                errors.append(f"{preset_id}: level entry must be an object")
                continue
            try:
                actual_level = int(level.get("level", 0))
            except (TypeError, ValueError):
                actual_level = 0
            if actual_level != expected_level:
                errors.append(f"{preset_id}: expected level {expected_level}, got {level.get('level')}")
            for key in ["marker_sample", "html_list_style_type", "docx_numFmt", "docx_level_text"]:
                if not str(level.get(key, "")).strip():
                    errors.append(f"{preset_id}: level {expected_level} missing {key}")
            marker = str(level.get("marker_sample", ""))
            if any("가" <= ch <= "힣" for ch in marker):
                errors.append(f"{preset_id}: marker_sample must not use Korean alphabetic markers: {marker}")
            expected_level += 1

    missing = sorted(LIST_STYLE_REQUIRED_IDS - seen_ids)
    if missing:
        errors.append("missing required list style presets: " + ", ".join(missing))
    extra = sorted(seen_ids - LIST_STYLE_REQUIRED_IDS)
    if extra:
        warnings.append("additional list style presets present: " + ", ".join(extra))
    return {
        "status": "pass" if not errors else "fail",
        "preset_count": len(seen_ids),
        "required_preset_ids": sorted(LIST_STYLE_REQUIRED_IDS),
        "errors": errors,
        "warnings": warnings,
    }


def validate(root: Path = PRESET_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    list_style_result = validate_list_style_presets(root)
    errors.extend([f"list_style_presets: {error}" for error in list_style_result.get("errors", [])])
    warnings.extend([f"list_style_presets: {warning}" for warning in list_style_result.get("warnings", [])])
    index = load_index(root)
    presets = index.get("presets", [])
    hold_candidates = index.get("hold_candidates", [])
    if not isinstance(presets, list):
        errors.append("INDEX.json presets must be a list")
        presets = []
    if not isinstance(hold_candidates, list):
        errors.append("INDEX.json hold_candidates must be a list")
        hold_candidates = []

    seen_ids: set[str] = set()
    seen_aliases: dict[str, str] = {}
    module_only_count = 0
    validated_presets: list[dict[str, Any]] = []

    for entry in presets:
        if not isinstance(entry, dict):
            errors.append("INDEX.json contains a non-object preset entry")
            continue
        preset_id = str(entry.get("preset_id", "")).strip()
        if not preset_id:
            errors.append("INDEX.json preset entry is missing preset_id")
            continue
        if preset_id in seen_ids:
            errors.append(f"duplicate preset_id in INDEX.json: {preset_id}")
        seen_ids.add(preset_id)
        if str(entry.get("status", "")) not in ALLOWED_PRESET_STATUS:
            errors.append(f"{preset_id}: unsupported INDEX status: {entry.get('status', '')}")

        preset_dir = root / preset_id
        if not preset_dir.exists():
            errors.append(f"{preset_id}: missing preset folder: {rel(preset_dir)}")
            continue
        for filename in REQUIRED_PRESET_FILES:
            if not (preset_dir / filename).exists():
                errors.append(f"{preset_id}: missing required file: {filename}")

        preset = load_preset(preset_id, root)
        if not preset:
            errors.append(f"{preset_id}: preset.json could not be loaded")
            continue
        if str(preset.get("preset_id", "")) != preset_id:
            errors.append(f"{preset_id}: preset.json preset_id mismatch: {preset.get('preset_id', '')}")
        integration_status = str(preset.get("integration_status") or "")
        if integration_status not in ALLOWED_INTEGRATION_STATUS:
            errors.append(f"{preset_id}: invalid integration_status: {integration_status}")
        if integration_status == "module_only":
            module_only_count += 1
        if preset_id in MODULE_ONLY_IDS and integration_status != "module_only":
            errors.append(f"{preset_id}: new extension preset must keep integration_status=module_only")

        read_first = list_values(entry.get("read_first"))
        for asset in read_first:
            asset_path = root / asset
            if not asset_path.exists():
                errors.append(f"{preset_id}: INDEX read_first path missing: {asset}")
        default_workflow_mode = str(entry.get("default_artifact_workflow_mode", "")).strip()
        if default_workflow_mode not in ALLOWED_ARTIFACT_WORKFLOW_MODES:
            errors.append(f"{preset_id}: invalid or missing default_artifact_workflow_mode: {default_workflow_mode}")
        read_for_workflow = list_values(entry.get("read_for_workflow"))
        if not read_for_workflow:
            errors.append(f"{preset_id}: INDEX read_for_workflow must include stage_overlays.md")
        for asset in read_for_workflow:
            asset_path = root / asset
            if not asset_path.exists():
                errors.append(f"{preset_id}: INDEX read_for_workflow path missing: {asset}")
        expected_workflow_asset = f"{preset_id}/stage_overlays.md"
        if read_for_workflow and expected_workflow_asset not in read_for_workflow:
            errors.append(f"{preset_id}: INDEX read_for_workflow must include {expected_workflow_asset}")
        read_for_design = list_values(entry.get("read_for_design"))
        for asset in read_for_design:
            asset_path = root / asset
            if not asset_path.exists():
                errors.append(f"{preset_id}: INDEX read_for_design path missing: {asset}")
        language_guidance = list_values(entry.get("language_guidance"))
        if preset_id in LANGUAGE_GUIDANCE_IDS and not language_guidance:
            errors.append(f"{preset_id}: INDEX language_guidance must include language_guidance.md")
        for asset in language_guidance:
            asset_path = root / asset
            if not asset_path.exists():
                errors.append(f"{preset_id}: INDEX language_guidance path missing: {asset}")
            else:
                guidance_text = asset_path.read_text(encoding="utf-8", errors="ignore")
                missing_terms = [term for term in LANGUAGE_GUIDANCE_TERMS if term.casefold() not in guidance_text.casefold()]
                if missing_terms:
                    errors.append(f"{preset_id}: language_guidance.md missing terms: {', '.join(missing_terms)}")
                missing_preset_terms = [
                    term
                    for term in PRESET_LANGUAGE_GUIDANCE_TERMS.get(preset_id, [])
                    if term.casefold() not in guidance_text.casefold()
                ]
                if missing_preset_terms:
                    errors.append(f"{preset_id}: language_guidance.md missing preset boundary terms: {', '.join(missing_preset_terms)}")

        overlays = preset.get("stage_overlays", {})
        if not isinstance(overlays, dict) or not overlays:
            errors.append(f"{preset_id}: preset.json stage_overlays must be a non-empty object")
        elif "prd" not in overlays or "review" not in overlays:
            errors.append(f"{preset_id}: stage_overlays must include at least prd and review")
        if isinstance(overlays, dict):
            for stage, assets in overlays.items():
                for asset in list_values(assets):
                    if not (preset_dir / asset).exists():
                        errors.append(f"{preset_id}: stage overlay asset missing for {stage}: {asset}")

        for filename, required_terms in DESIGN_EXPORT_REQUIRED_TERMS.get(preset_id, {}).items():
            asset_path = preset_dir / filename
            if not asset_path.exists():
                errors.append(f"{preset_id}: missing design/export guidance file: {filename}")
                continue
            guidance_text = asset_path.read_text(encoding="utf-8", errors="ignore")
            missing_terms = [term for term in required_terms if term.casefold() not in guidance_text.casefold()]
            if missing_terms:
                errors.append(f"{preset_id}: {filename} missing design/export terms: {', '.join(missing_terms)}")

        for alias in [preset_id, str(entry.get("label_ko", "")), *list_values(entry.get("aliases"))]:
            key = normalize(alias)
            if not key:
                continue
            owner = seen_aliases.get(key)
            if owner and owner != preset_id:
                errors.append(f"alias collision between {owner} and {preset_id}: {alias}")
            seen_aliases[key] = preset_id

        validated_presets.append(
            {
                "preset_id": preset_id,
                "integration_status": integration_status or "workflow_supported",
                "default_artifact_workflow_mode": default_workflow_mode,
                "stage_overlay_count": len(overlays) if isinstance(overlays, dict) else 0,
            }
        )

    for candidate in hold_candidates:
        if not isinstance(candidate, dict):
            errors.append("INDEX.json contains a non-object hold_candidate entry")
            continue
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        label = str(candidate.get("label_ko", "")).strip()
        if not candidate_id or not label:
            errors.append("hold_candidate entry must include candidate_id and label_ko")
            continue
        if normalize(candidate_id) in seen_aliases:
            errors.append(f"hold candidate collides with supported preset alias/id: {candidate_id}")
        if normalize(label) in seen_aliases:
            errors.append(f"hold candidate collides with supported preset alias/label: {label}")
        for alias in list_values(candidate.get("aliases")):
            if normalize(alias) in seen_aliases:
                errors.append(f"hold candidate collides with supported preset alias: {alias}")
        query_payload = query_document_preset(label, "interview", root)
        if query_payload.get("status") != "hold_candidate" or query_payload.get("supported_route") is not False:
            errors.append(f"hold candidate routed as supported preset: {label}")

    for query, required_path in DESIGN_QUERY_CASES.items():
        query_payload = query_document_preset(query, "design", root)
        asset_paths = [
            str(asset.get("path", ""))
            for asset in query_payload.get("stage_assets", [])
            if isinstance(asset, dict)
        ]
        if query_payload.get("status") != "matched":
            errors.append(f"design query did not match a supported preset: {query}")
        if required_path not in asset_paths:
            errors.append(f"design query missing design_patterns asset for {query}: {required_path}")

    for query, required_preset_id in DESCRIPTIVE_QUERY_CASES.items():
        query_payload = query_document_preset(query, "prd", root)
        matched_preset = query_payload.get("preset", {}) if isinstance(query_payload.get("preset"), dict) else {}
        if matched_preset.get("preset_id") != required_preset_id:
            errors.append(f"descriptive query routed incorrectly: {query} -> {matched_preset.get('preset_id', '')}; expected {required_preset_id}")
        workflow_assets = [
            str(asset.get("path", ""))
            for asset in query_payload.get("workflow_assets", [])
            if isinstance(asset, dict)
        ]
        required_workflow_path = f"_ai_system/document_presets/{required_preset_id}/stage_overlays.md"
        if required_workflow_path not in workflow_assets:
            errors.append(f"descriptive query missing workflow guidance for {query}: {required_workflow_path}")

    for preset_id in LANGUAGE_GUIDANCE_IDS:
        query_payload = query_document_preset(preset_id, "prd", root, output_language="en")
        asset_paths = [
            str(asset.get("path", ""))
            for asset in query_payload.get("stage_assets", [])
            if isinstance(asset, dict)
        ]
        required_path = f"_ai_system/document_presets/{preset_id}/language_guidance.md"
        if required_path not in asset_paths:
            errors.append(f"English context query missing language guidance for {preset_id}: {required_path}")

    for query in HOLD_QUERY_CASES:
        query_payload = query_document_preset(query, "interview", root)
        if query_payload.get("status") != "hold_candidate":
            errors.append(f"hold alias was not routed as hold_candidate: {query}")
        if query_payload.get("supported_route") is not False:
            errors.append(f"hold alias must keep supported_route=false: {query}")

    if module_only_count < len(MODULE_ONLY_IDS):
        warnings.append(f"module_only extension preset count is {module_only_count}; expected at least {len(MODULE_ONLY_IDS)}")

    return {
        "status": "pass" if not errors else "fail",
        "preset_count": len(validated_presets),
        "module_only_count": module_only_count,
        "validated_presets": validated_presets,
        "hold_candidate_count": len(hold_candidates),
        "list_style_presets": list_style_result,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate document preset routing index, module files, and hold-candidate boundaries.")
    parser.parse_args()
    payload = validate()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
