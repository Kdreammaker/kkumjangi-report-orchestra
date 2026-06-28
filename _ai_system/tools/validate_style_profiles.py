from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from query_style_profile import PROTECTED_SPAN_POLICY, STYLE_ROOT, load_index, load_profile, normalize, query_style_profile


REQUIRED_PROFILE_FILES = ["profile.json", "tone_rules.md", "forbidden_patterns.md", "rewrite_protocol.md", "examples.md"]
REQUIRED_COMMON_STYLE_FILES = [
    "CODEMAP.md",
    "korean_tone_workflow_design_v1.md",
    "templates/style_risk_findings.json",
    "templates/protected_spans.json",
    "templates/style_rewrite_diff.md",
    "templates/style_fidelity_review.md",
    "templates/style_naturalness_review.md",
]
ALLOWED_PROFILE_STATUS = {"supported"}
REQUIRED_AUTOMATION_STATUS = "guidance_only"
PROTECTED_POLICY_TERMS = {
    "direct_quotes": ["direct quotes", "quoted translations", "직접 인용"],
    "numbers": ["numbers", "units", "dates", "percentages", "prices", "수치"],
    "laws": ["law names", "article numbers", "regulation names", "법령"],
    "proper_nouns": ["proper nouns", "company names", "product names", "고유명사"],
    "source_claims": ["source-backed claims", "claim registers", "출처"],
    "approved_public": ["approved public statements", "boilerplate", "approval wording", "승인"],
    "contract_public": ["contract-like", "liability", "confidentiality", "public-release", "계약", "공개"],
}
QUERY_CASES = {
    "경영진 요약": "internal_executive_summary",
    "외부 파트너": "partner_business",
    "초보 학습자": "child_education",
    "보도자료": "press_public",
    "formal academic": "academic_formal",
}
DESCRIPTIVE_QUERY_CASES = {
    "논문처럼": "academic_formal",
    "공식 발표문처럼": "press_public",
    "아이들이 이해하게": "child_education",
    "임원에게 짧게": "internal_executive_summary",
    "파트너에게 정중하게": "partner_business",
}
AMBIGUOUS_QUERY_CASES = {
    "요약": "internal_executive_summary",
    "외부용": "press_public",
}
OVERLAY_ONLY_QUERY_CASES = {
    "높임말로": "honorific_overlay",
    "압존법 적용": "honorific_overlay",
    "일반 사용자가 따라할 수 있는 절차 안내": "user_instructional_overlay",
}
LANGUAGE_GUIDANCE_IDS = {"internal_executive_summary", "partner_business", "press_public"}
LANGUAGE_GUIDANCE_TERMS = ["Korean", "English", "Protected Spans", "rewrite", "Mechanical", "reader-fit", "translation"]
REQUIRED_ROUTING_CUE_FIELDS = ["description_examples", "positive_cues", "negative_cues", "ambiguous_cues", "ask_when_ambiguous"]


def rel(path: Path) -> str:
    return path.as_posix()


def list_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str)]
    return []


def text_has_any(text: str, terms: list[str]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def protected_policy_missing(text: str) -> list[str]:
    return [policy_id for policy_id, terms in PROTECTED_POLICY_TERMS.items() if not text_has_any(text, terms)]


def validate(root: Path = STYLE_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    index = load_index(root)
    profiles = index.get("profiles", [])
    if not isinstance(profiles, list):
        errors.append("INDEX.json profiles must be a list")
        profiles = []

    readme = root / "README.md"
    if not readme.exists():
        errors.append(f"missing style profile README: {rel(readme)}")
        readme_text = ""
    else:
        readme_text = readme.read_text(encoding="utf-8", errors="ignore")
        missing_readme_policy = protected_policy_missing(readme_text)
        if missing_readme_policy:
            errors.append("README.md missing protected span policy terms: " + ", ".join(missing_readme_policy))
    for asset in REQUIRED_COMMON_STYLE_FILES:
        if not (root / asset).exists():
            errors.append(f"missing common style-pass asset: {asset}")
    route_examples = root / "ROUTE_EXAMPLES.md"
    if not route_examples.exists():
        errors.append("missing style profile route examples: ROUTE_EXAMPLES.md")

    seen_ids: set[str] = set()
    seen_aliases: dict[str, str] = {}
    validated_profiles: list[dict[str, Any]] = []

    for entry in profiles:
        if not isinstance(entry, dict):
            errors.append("INDEX.json contains a non-object profile entry")
            continue
        profile_id = str(entry.get("profile_id", "")).strip()
        if not profile_id:
            errors.append("INDEX.json profile entry is missing profile_id")
            continue
        if profile_id in seen_ids:
            errors.append(f"duplicate profile_id in INDEX.json: {profile_id}")
        seen_ids.add(profile_id)

        if str(entry.get("status", "")) not in ALLOWED_PROFILE_STATUS:
            errors.append(f"{profile_id}: unsupported INDEX status: {entry.get('status', '')}")
        if str(entry.get("automation_status", "")) != REQUIRED_AUTOMATION_STATUS:
            errors.append(f"{profile_id}: INDEX automation_status must be guidance_only")

        aliases = list_values(entry.get("aliases"))
        if not aliases:
            errors.append(f"{profile_id}: INDEX aliases must be a non-empty list")

        routing_cues = entry.get("routing_cues", {})
        if not isinstance(routing_cues, dict):
            errors.append(f"{profile_id}: INDEX routing_cues must be an object")
            routing_cues = {}
        for cue_field in REQUIRED_ROUTING_CUE_FIELDS:
            if not list_values(routing_cues.get(cue_field)) and cue_field != "ambiguous_cues":
                errors.append(f"{profile_id}: routing_cues.{cue_field} must be a non-empty list")
            if cue_field == "ambiguous_cues" and not isinstance(routing_cues.get(cue_field), list):
                errors.append(f"{profile_id}: routing_cues.ambiguous_cues must be a list")

        profile_dir = root / profile_id
        if not profile_dir.exists():
            errors.append(f"{profile_id}: missing profile folder: {rel(profile_dir)}")
            continue
        for filename in REQUIRED_PROFILE_FILES:
            if not (profile_dir / filename).exists():
                errors.append(f"{profile_id}: missing required profile file: {filename}")

        read_first = list_values(entry.get("read_first"))
        if not read_first:
            errors.append(f"{profile_id}: INDEX read_first must be a non-empty list")
        for asset in read_first:
            asset_path = root / asset
            if not asset_path.exists():
                errors.append(f"{profile_id}: INDEX read_first path missing: {asset}")
        language_guidance = list_values(entry.get("language_guidance"))
        if profile_id in LANGUAGE_GUIDANCE_IDS and not language_guidance:
            errors.append(f"{profile_id}: INDEX language_guidance must include language_guidance.md")
        for asset in language_guidance:
            asset_path = root / asset
            if not asset_path.exists():
                errors.append(f"{profile_id}: INDEX language_guidance path missing: {asset}")
            else:
                guidance_text = asset_path.read_text(encoding="utf-8", errors="ignore")
                missing_terms = [term for term in LANGUAGE_GUIDANCE_TERMS if term.casefold() not in guidance_text.casefold()]
                if missing_terms:
                    errors.append(f"{profile_id}: language_guidance.md missing terms: {', '.join(missing_terms)}")

        profile = load_profile(profile_id, root)
        if not profile:
            errors.append(f"{profile_id}: profile.json could not be loaded")
            continue
        module_profile_id = str(profile.get("profile_id") or profile.get("id") or "").strip()
        if module_profile_id != profile_id:
            errors.append(f"{profile_id}: profile.json profile_id mismatch: {module_profile_id}")
        if str(profile.get("automation_status", "")) != REQUIRED_AUTOMATION_STATUS:
            errors.append(f"{profile_id}: profile.json automation_status must be guidance_only")

        rewrite_protocol = profile_dir / "rewrite_protocol.md"
        rewrite_text = rewrite_protocol.read_text(encoding="utf-8", errors="ignore") if rewrite_protocol.exists() else ""
        missing_profile_policy = protected_policy_missing(rewrite_text)
        if missing_profile_policy:
            errors.append(f"{profile_id}: rewrite_protocol.md missing protected span policy terms: {', '.join(missing_profile_policy)}")

        for alias in [profile_id, str(profile.get("label", "")), str(profile.get("label_ko", "")), *aliases]:
            key = normalize(alias)
            if not key:
                continue
            owner = seen_aliases.get(key)
            if owner and owner != profile_id:
                errors.append(f"alias collision between {owner} and {profile_id}: {alias}")
            seen_aliases[key] = profile_id

        query_payload = query_style_profile(profile_id, root)
        if query_payload.get("status") != "matched":
            errors.append(f"{profile_id}: query_style_profile did not match by profile_id")
        automation = query_payload.get("automation", {})
        if not isinstance(automation, dict) or automation.get("rewrite_automation") != "not_enabled":
            errors.append(f"{profile_id}: query payload must keep rewrite_automation=not_enabled")
        asset_paths = [
            str(asset.get("path", ""))
            for asset in query_payload.get("style_assets", [])
            if isinstance(asset, dict)
        ]
        for asset in REQUIRED_COMMON_STYLE_FILES:
            required_common_path = f"_ai_system/style_profiles/{asset}"
            if required_common_path not in asset_paths:
                errors.append(f"{profile_id}: query payload missing common style-pass asset: {required_common_path}")
        if profile_id in LANGUAGE_GUIDANCE_IDS:
            language_payload = query_style_profile(profile_id, root, output_language="en")
            language_asset_paths = [
                str(asset.get("path", ""))
                for asset in language_payload.get("style_assets", [])
                if isinstance(asset, dict)
            ]
            required_path = f"_ai_system/style_profiles/{profile_id}/language_guidance.md"
            if required_path not in language_asset_paths:
                errors.append(f"{profile_id}: English context query missing language guidance: {required_path}")

        validated_profiles.append(
            {
                "profile_id": profile_id,
                "automation_status": str(profile.get("automation_status", "")),
                "read_first_count": len(read_first),
                "protected_policy_terms": "present" if not missing_profile_policy else "missing",
            }
        )

    for query, expected_profile_id in QUERY_CASES.items():
        query_payload = query_style_profile(query, root)
        profile = query_payload.get("profile", {})
        actual_profile_id = profile.get("profile_id", "") if isinstance(profile, dict) else ""
        if actual_profile_id != expected_profile_id:
            errors.append(f"query did not route to expected style profile: {query} -> {actual_profile_id}")
        if query_payload.get("match_type") != "alias":
            errors.append(f"alias query did not keep alias priority: {query}")
        automation = query_payload.get("automation", {})
        if not isinstance(automation, dict) or automation.get("rewrite_automation") != "not_enabled":
            errors.append(f"query enabled rewrite automation unexpectedly: {query}")

    for query, expected_profile_id in DESCRIPTIVE_QUERY_CASES.items():
        query_payload = query_style_profile(query, root)
        profile = query_payload.get("profile", {})
        actual_profile_id = profile.get("profile_id", "") if isinstance(profile, dict) else ""
        if query_payload.get("status") != "matched" or actual_profile_id != expected_profile_id:
            errors.append(f"descriptive query did not route to expected style profile: {query} -> {actual_profile_id}")
        if query_payload.get("match_type") != "cue":
            errors.append(f"descriptive query did not use cue routing: {query}")
        cue_routing = query_payload.get("cue_routing", {})
        if not isinstance(cue_routing, dict) or not cue_routing.get("reasons"):
            errors.append(f"descriptive query missing cue routing reasons: {query}")
        automation = query_payload.get("automation", {})
        if not isinstance(automation, dict) or automation.get("automation_status") != REQUIRED_AUTOMATION_STATUS:
            errors.append(f"descriptive query changed automation boundary: {query}")
        if not isinstance(automation, dict) or automation.get("rewrite_automation") != "not_enabled":
            errors.append(f"descriptive query enabled rewrite automation unexpectedly: {query}")

    for query, expected_profile_id in AMBIGUOUS_QUERY_CASES.items():
        query_payload = query_style_profile(query, root)
        if query_payload.get("status") != "ambiguous":
            errors.append(f"ambiguous query was not returned as ambiguous: {query}")
        candidates = query_payload.get("candidates", [])
        candidate_ids = [
            candidate.get("profile", {}).get("profile_id", "")
            for candidate in candidates
            if isinstance(candidate, dict)
        ]
        if expected_profile_id not in candidate_ids:
            errors.append(f"ambiguous query missing expected candidate: {query} -> {candidate_ids}")
        if not query_payload.get("confirmation_question"):
            errors.append(f"ambiguous query missing confirmation question: {query}")
        automation = query_payload.get("automation", {})
        if not isinstance(automation, dict) or automation.get("rewrite_automation") != "not_enabled":
            errors.append(f"ambiguous query enabled rewrite automation unexpectedly: {query}")

    for query, expected_overlay_id in OVERLAY_ONLY_QUERY_CASES.items():
        query_payload = query_style_profile(query, root)
        if query_payload.get("status") != "ambiguous":
            errors.append(f"overlay-only query should require confirmation: {query}")
        if query_payload.get("profile"):
            errors.append(f"overlay-only query selected a profile unexpectedly: {query}")
        overlays = query_payload.get("overlay_candidates", [])
        overlay_ids = [
            overlay.get("overlay_id", "")
            for overlay in overlays
            if isinstance(overlay, dict)
        ]
        if expected_overlay_id not in overlay_ids:
            errors.append(f"overlay-only query missing overlay candidate: {query} -> {overlay_ids}")
        automation = query_payload.get("automation", {})
        if not isinstance(automation, dict) or automation.get("rewrite_automation") != "not_enabled":
            errors.append(f"overlay-only query enabled rewrite automation unexpectedly: {query}")

    return {
        "status": "pass" if not errors else "fail",
        "profile_count": len(validated_profiles),
        "validated_profiles": validated_profiles,
        "protected_span_policy": PROTECTED_SPAN_POLICY,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate guidance-only style profile routing, module files, and protected span policy.")
    parser.parse_args()
    payload = validate()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
