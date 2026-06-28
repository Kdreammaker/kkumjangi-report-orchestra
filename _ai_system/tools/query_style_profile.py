from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


STYLE_ROOT = Path("_ai_system") / "style_profiles"
INDEX_PATH = STYLE_ROOT / "INDEX.json"
ROUTE_EXAMPLES_PATH = STYLE_ROOT / "ROUTE_EXAMPLES.md"

MIN_CUE_SCORE = 2.5
AMBIGUOUS_SCORE_MARGIN = 1.5
MAX_CANDIDATES = 3
TOKEN_STOPWORDS = {
    "있는",
    "없는",
    "하기",
    "하게",
    "위한",
    "해야",
    "싶다",
    "싶은",
    "문서",
    "문안",
    "준비",
    "읽는",
    "담은",
    "수",
}

COMMON_STYLE_WORKFLOW_ASSETS = [
    ("CODEMAP.md", "style profile codemap"),
    ("korean_tone_workflow_design_v1.md", "common Korean style-pass workflow guidance"),
    ("templates/style_risk_findings.json", "style-pass artifact template"),
    ("templates/protected_spans.json", "style-pass artifact template"),
    ("templates/style_rewrite_diff.md", "style-pass artifact template"),
    ("templates/style_fidelity_review.md", "style-pass artifact template"),
    ("templates/style_naturalness_review.md", "style-pass artifact template"),
]

PROTECTED_SPAN_POLICY = [
    "direct quotes and quoted translations",
    "numbers, units, dates, percentages, prices, financial metrics, and formulas",
    "law names, article numbers, regulation names, official program names, and court/regulator wording",
    "proper nouns, company names, product names, partner names, people names, and jurisdiction names",
    "source-backed claims in claim registers or reader-facing citations",
    "approved public statements, quotes, boilerplate, disclaimers, contact information, embargo text, and approval wording",
    "contract-like scope, responsibility, price, schedule, acceptance, exclusion, liability, confidentiality, or public-release wording",
]

OVERLAY_CUES = [
    {
        "overlay_id": "register_overlay",
        "label": "register / 말투 overlay",
        "cues": ["register", "말투", "어투", "문체만", "톤만", "정중하게", "공손하게", "딱딱하게", "부드럽게"],
        "question": "말투/register만 조정할까요, 아니면 독자와 용도에 맞는 style profile도 함께 선택해야 하나요?",
    },
    {
        "overlay_id": "honorific_overlay",
        "label": "honorific / 높임말 overlay",
        "cues": ["honorific", "높임말", "존댓말", "압존법", "경어", "높임 표현"],
        "question": "높임말/압존법은 별도 overlay로 다루고, 독자 유형은 따로 정할까요?",
    },
    {
        "overlay_id": "user_instructional_overlay",
        "label": "user-instructional overlay",
        "cues": ["사용자 안내", "사용자용", "절차 안내", "매뉴얼", "따라할 수", "단계 안내"],
        "question": "사용 절차 overlay가 필요한가요, 아니면 어린이/초보자·파트너/고객 같은 독자 profile도 정해야 하나요?",
    },
]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def normalize(value: str) -> str:
    return re.sub(r"[\s_-]+", "", value.casefold().strip())


def rel(path: Path) -> str:
    return path.as_posix()


def list_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str)]
    return []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        key = normalize(cleaned)
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def _cue_tokens(value: str) -> list[str]:
    raw_tokens = re.findall(r"[0-9A-Za-z가-힣]+", value.casefold())
    tokens: list[str] = []
    suffixes = ["처럼", "같이", "같은", "에게", "으로", "로", "하게", "하게끔", "답게", "형", "문서"]
    for token in raw_tokens:
        stripped = token
        for suffix in suffixes:
            if stripped.endswith(suffix) and len(stripped) > len(suffix) + 1:
                stripped = stripped[: -len(suffix)]
        if len(stripped) >= 2 and stripped not in TOKEN_STOPWORDS:
            tokens.append(stripped)
    return _unique(tokens)


def _cue_matches(query: str, cue: str) -> bool:
    query_norm = normalize(query)
    cue_norm = normalize(cue)
    if not query_norm or not cue_norm:
        return False
    if len(cue_norm) >= 2 and cue_norm in query_norm:
        return True
    if len(query_norm) >= 3 and query_norm in cue_norm:
        return True
    query_tokens = set(_cue_tokens(query))
    cue_tokens = set(_cue_tokens(cue))
    overlap = query_tokens.intersection(cue_tokens)
    strong_overlap = [token for token in overlap if len(token) >= 3]
    return len(strong_overlap) >= 1 or len(overlap) >= 2


def _matched_cues(query: str, cues: list[str]) -> list[str]:
    return [cue for cue in cues if _cue_matches(query, cue)]


def _load_route_examples(root: Path = STYLE_ROOT) -> dict[str, list[str]]:
    path = root / "ROUTE_EXAMPLES.md"
    if not path.exists():
        return {}
    examples: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "`" not in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2 or cells[0].casefold() == "user says":
            continue
        match = re.search(r"`([^`]+)`", cells[1])
        if not match:
            continue
        profile_id = match.group(1).strip()
        if not profile_id or profile_id.casefold() == "ask":
            continue
        user_says = cells[0].strip().strip('"')
        if user_says:
            examples.setdefault(profile_id, []).append(user_says)
    return examples


def overlay_candidates(query: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for overlay in OVERLAY_CUES:
        matched = _matched_cues(query, list_values(overlay.get("cues")))
        if matched:
            candidates.append(
                {
                    "overlay_id": overlay["overlay_id"],
                    "label": overlay["label"],
                    "matched_cues": matched,
                    "question": overlay["question"],
                    "automation_status": "guidance_only",
                    "note": "Overlay cues are not style profiles and must be applied only after profile selection or user confirmation.",
                }
            )
    return candidates


def include_language_guidance(output_language: str) -> bool:
    return output_language.strip().casefold() in {"en", "mixed"}


def load_index(root: Path = STYLE_ROOT) -> dict[str, Any]:
    index_path = root / "INDEX.json"
    if not index_path.exists():
        raise FileNotFoundError(f"missing style profile index: {index_path.as_posix()}")
    return read_json(index_path)


def load_profile(profile_id: str, root: Path = STYLE_ROOT) -> dict[str, Any]:
    path = root / profile_id / "profile.json"
    if not path.exists():
        return {}
    return read_json(path)


def automation_status(index_entry: dict[str, Any], profile: dict[str, Any]) -> dict[str, str]:
    index_status = str(index_entry.get("automation_status") or "").strip()
    profile_status = str(profile.get("automation_status") or "").strip()
    status = profile_status or index_status or "guidance_only"
    return {
        "automation_status": status,
        "rewrite_automation": "not_enabled",
        "workflow_automation": "not_enabled",
        "note": "Style profiles provide reader- and purpose-specific guidance only. They do not rewrite text automatically.",
    }


def _profile_match(query: str, index: dict[str, Any]) -> dict[str, Any] | None:
    normalized = normalize(query)
    exact_alias_match: dict[str, Any] | None = None
    for profile in index.get("profiles", []):
        if not isinstance(profile, dict):
            continue
        values = [
            str(profile.get("profile_id", "")),
            *[str(alias) for alias in profile.get("aliases", []) if isinstance(alias, str)],
        ]
        normalized_values = [normalize(value) for value in values if value]
        if normalized in normalized_values:
            exact_alias_match = profile
            break
    return exact_alias_match


def _profile_summary(index_entry: dict[str, Any], root: Path = STYLE_ROOT) -> dict[str, Any]:
    profile_id = str(index_entry.get("profile_id", "")).strip()
    profile = load_profile(profile_id, root)
    return {
        "profile_id": profile_id,
        "label": profile.get("label", ""),
        "label_ko": profile.get("label_ko", ""),
        "status": index_entry.get("status", ""),
        "risk_level": profile.get("risk_level", ""),
        "target_reader": profile.get("target_reader", ""),
        "primary_use": profile.get("primary_use", ""),
        "recommended_document_presets": index_entry.get("recommended_document_presets", []),
        "protected_span_priority": profile.get("protected_span_priority", ""),
    }


def _ambiguous_cue_hits(query: str, routing_cues: dict[str, Any]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    query_norm = normalize(query)
    for cue in routing_cues.get("ambiguous_cues", []):
        if not isinstance(cue, dict):
            continue
        cue_text = str(cue.get("cue", "")).strip()
        if cue_text and _cue_matches(query, cue_text):
            hits.append(
                {
                    "cue": cue_text,
                    "reason": str(cue.get("reason", "")).strip(),
                    "ask": str(cue.get("ask", "")).strip(),
                    "exact": "yes" if query_norm == normalize(cue_text) else "no",
                }
            )
    return hits


def _score_profile(query: str, entry: dict[str, Any], route_examples: dict[str, list[str]]) -> dict[str, Any]:
    profile_id = str(entry.get("profile_id", "")).strip()
    routing_cues = entry.get("routing_cues", {})
    if not isinstance(routing_cues, dict):
        routing_cues = {}

    score = 0.0
    reasons: list[str] = []

    route_hits = _matched_cues(query, route_examples.get(profile_id, []))
    if route_hits:
        score += 6.0 * len(route_hits)
        reasons.append("matched ROUTE_EXAMPLES.md example: " + ", ".join(route_hits[:2]))

    direct_cues = [
        *list_values(routing_cues.get("direct_names")),
        *list_values(entry.get("aliases")),
    ]
    direct_hits = _matched_cues(query, direct_cues)
    if direct_hits:
        score += 3.0 * len(direct_hits)
        reasons.append("matched direct name/alias cue: " + ", ".join(direct_hits[:3]))

    description_hits = _matched_cues(query, list_values(routing_cues.get("description_examples")))
    if description_hits:
        score += 4.0 * len(description_hits)
        reasons.append("matched descriptive cue: " + ", ".join(description_hits[:2]))

    positive_hits = _matched_cues(query, list_values(routing_cues.get("positive_cues")))
    if positive_hits:
        score += 2.0 * len(positive_hits)
        reasons.append("matched positive cue: " + ", ".join(positive_hits[:4]))

    negative_hits = _matched_cues(query, list_values(routing_cues.get("negative_cues")))
    if negative_hits:
        score -= 3.0 * len(negative_hits)
        reasons.append("suppressed by negative cue: " + ", ".join(negative_hits[:3]))

    ambiguous_hits = _ambiguous_cue_hits(query, routing_cues)
    if ambiguous_hits:
        reasons.append("matched ambiguous cue: " + ", ".join(hit["cue"] for hit in ambiguous_hits[:3]))

    return {
        "profile_id": profile_id,
        "score": round(score, 2),
        "reasons": reasons,
        "ambiguous_cues": ambiguous_hits,
        "ambiguous_query_exact": any(hit.get("exact") == "yes" for hit in ambiguous_hits),
        "ask_when_ambiguous": list_values(routing_cues.get("ask_when_ambiguous")),
        "recommended_document_preset_combinations": routing_cues.get("recommended_document_preset_combinations", []),
        "index_entry": entry,
    }


def _cue_candidates(query: str, index: dict[str, Any], root: Path = STYLE_ROOT) -> list[dict[str, Any]]:
    route_examples = _load_route_examples(root)
    candidates = [
        _score_profile(query, profile, route_examples)
        for profile in index.get("profiles", [])
        if isinstance(profile, dict)
    ]
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def _candidate_payload(candidate: dict[str, Any], root: Path = STYLE_ROOT) -> dict[str, Any]:
    entry = candidate["index_entry"]
    return {
        "profile": _profile_summary(entry, root),
        "score": candidate["score"],
        "reasons": candidate["reasons"],
        "ambiguity_prompts": [
            *(hit.get("ask", "") for hit in candidate.get("ambiguous_cues", []) if hit.get("ask")),
            *candidate.get("ask_when_ambiguous", []),
        ][:3],
        "recommended_document_preset_combinations": candidate.get("recommended_document_preset_combinations", []),
    }


def _confirmation_question(candidates: list[dict[str, Any]], overlays: list[dict[str, Any]]) -> str:
    for candidate in candidates:
        for prompt in candidate.get("ambiguity_prompts", []):
            if prompt:
                return str(prompt)
    if overlays:
        return str(overlays[0].get("question", "독자와 용도를 확인한 뒤 style profile을 선택할까요?"))
    names = [candidate.get("profile", {}).get("profile_id", "") for candidate in candidates[:2]]
    names = [name for name in names if name]
    if names:
        return "이 요청은 " + " / ".join(names) + " 중 어느 독자·용도에 더 가깝나요?"
    return "독자, 배포 대상, 문서 용도를 한 문장으로 더 알려주실 수 있나요?"


def style_profile_assets(index_entry: dict[str, Any], root: Path = STYLE_ROOT, output_language: str = "") -> list[dict[str, str]]:
    profile_id = str(index_entry.get("profile_id", "")).strip()
    assets: list[dict[str, str]] = []
    for asset in list_values(index_entry.get("read_first")):
        asset_path = root / asset
        assets.append(
            {
                "path": rel(asset_path),
                "role": "style profile guidance",
                "exists": "yes" if asset_path.exists() else "no",
                }
            )
    for asset, role in COMMON_STYLE_WORKFLOW_ASSETS:
        asset_path = root / asset
        assets.append(
            {
                "path": rel(asset_path),
                "role": role,
                "exists": "yes" if asset_path.exists() else "no",
            }
        )
    if include_language_guidance(output_language):
        for asset in list_values(index_entry.get("language_guidance")):
            asset_path = root / asset
            assets.append(
                {
                    "path": rel(asset_path),
                    "role": "style profile language guidance",
                    "exists": "yes" if asset_path.exists() else "no",
                }
            )
        if not list_values(index_entry.get("language_guidance")) and profile_id:
            language_path = root / profile_id / "language_guidance.md"
            if language_path.exists():
                assets.append(
                    {
                        "path": rel(language_path),
                        "role": "style profile language guidance",
                        "exists": "yes",
                    }
                )
    if profile_id and not assets:
        profile_json = root / profile_id / "profile.json"
        assets.append(
            {
                "path": rel(profile_json),
                "role": "style profile metadata",
                "exists": "yes" if profile_json.exists() else "no",
            }
        )
    return assets


def query_style_profile(query: str, root: Path = STYLE_ROOT, output_language: str = "") -> dict[str, Any]:
    index = load_index(root)
    match = _profile_match(query, index)
    overlays = overlay_candidates(query)

    if match:
        profile_id = str(match.get("profile_id", "")).strip()
        profile = load_profile(profile_id, root)
        return {
            "status": "matched",
            "match_type": "alias",
            "query": query,
            "supported_route": str(match.get("status", "")) == "supported",
            "profile": _profile_summary(match, root),
            "automation": automation_status(match, profile),
            "overlay_candidates": overlays,
            "style_assets": style_profile_assets(match, root, output_language),
            "language": {
                "output_language": output_language,
                "language_guidance_included": include_language_guidance(output_language),
                "note": "Language guidance adjusts reader-fit boundaries only. It does not enable automatic translation, humanization, or rewrite.",
            },
            "protected_span_policy": PROTECTED_SPAN_POLICY,
            "read_policy": "Read INDEX.json, then only the selected profile metadata and read_first guidance files. Do not perform automatic rewrite.",
        }

    scored = _cue_candidates(query, index, root)
    viable = [candidate for candidate in scored if candidate["score"] > 0 or candidate.get("ambiguous_cues")]
    top = viable[0] if viable else None
    close = [
        candidate
        for candidate in viable
        if top and candidate["score"] >= top["score"] - AMBIGUOUS_SCORE_MARGIN
    ]
    top_has_ambiguous_only = bool(
        top
        and top.get("ambiguous_cues")
        and (top.get("ambiguous_query_exact") or top["score"] < MIN_CUE_SCORE + 2.0)
    )

    if not top or top["score"] < MIN_CUE_SCORE:
        candidate_payloads = [_candidate_payload(candidate, root) for candidate in viable[:MAX_CANDIDATES]]
        if viable or overlays:
            return {
                "status": "ambiguous",
                "query": query,
                "supported_route": False,
                "candidates": candidate_payloads,
                "reasons": ["cue score is below the confident routing threshold"],
                "confirmation_question": _confirmation_question(candidate_payloads, overlays),
                "automation": {
                    "automation_status": "guidance_only",
                    "rewrite_automation": "not_enabled",
                    "workflow_automation": "not_enabled",
                    "note": "The router did not select a profile. Overlay cues do not enable automatic rewrite.",
                },
                "overlay_candidates": overlays,
                "style_assets": [],
                "protected_span_policy": PROTECTED_SPAN_POLICY,
                "read_policy": "Ask for the missing reader/use-case signal before selecting a style profile. Do not perform automatic rewrite.",
            }
        return {
            "status": "not_found",
            "query": query,
            "supported_route": False,
            "automation": {
                "automation_status": "guidance_only",
                "rewrite_automation": "not_enabled",
                "workflow_automation": "not_enabled",
                "note": "No matching style profile was found. No automatic rewrite is available.",
            },
            "style_assets": [],
            "protected_span_policy": PROTECTED_SPAN_POLICY,
        }

    if len(close) > 1 or top_has_ambiguous_only:
        candidate_payloads = [_candidate_payload(candidate, root) for candidate in close[:MAX_CANDIDATES]]
        reasons = ["multiple profiles are close in cue score"] if len(close) > 1 else []
        if top_has_ambiguous_only:
            reasons.append("the strongest cue is marked ambiguous in INDEX.json")
        return {
            "status": "ambiguous",
            "query": query,
            "supported_route": False,
            "candidates": candidate_payloads,
            "reasons": reasons,
            "confirmation_question": _confirmation_question(candidate_payloads, overlays),
            "automation": {
                "automation_status": "guidance_only",
                "rewrite_automation": "not_enabled",
                "workflow_automation": "not_enabled",
                "note": "No single style profile was selected. The router needs confirmation before loading guidance.",
            },
            "overlay_candidates": overlays,
            "style_assets": [],
            "protected_span_policy": PROTECTED_SPAN_POLICY,
            "read_policy": "Ask the confirmation question before selecting one profile. Do not perform automatic rewrite.",
        }

    match = top["index_entry"]
    profile_id = str(match.get("profile_id", "")).strip()
    profile = load_profile(profile_id, root)
    return {
        "status": "matched",
        "match_type": "cue",
        "query": query,
        "supported_route": str(match.get("status", "")) == "supported",
        "profile": _profile_summary(match, root),
        "cue_routing": {
            "score": top["score"],
            "reasons": top["reasons"],
            "ambiguous_cues": top.get("ambiguous_cues", []),
            "note": "Cue routing is advisory and uses INDEX.json routing_cues plus ROUTE_EXAMPLES.md. Alias matches still take priority.",
        },
        "automation": automation_status(match, profile),
        "overlay_candidates": overlays,
        "style_assets": style_profile_assets(match, root, output_language),
        "language": {
            "output_language": output_language,
            "language_guidance_included": include_language_guidance(output_language),
            "note": "Language guidance adjusts reader-fit boundaries only. It does not enable automatic translation, humanization, or rewrite.",
        },
        "protected_span_policy": PROTECTED_SPAN_POLICY,
        "read_policy": "Read INDEX.json, then only the selected profile metadata and read_first guidance files. Do not perform automatic rewrite.",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Route a tone or reader query to a guidance-only style profile.")
    parser.add_argument("query", nargs="?", default="", help="Profile id, Korean label, or alias to resolve.")
    parser.add_argument("--query", dest="query_flag", default="", help="Profile id, Korean label, or alias to resolve.")
    parser.add_argument("--output-language", default="", choices=["", "ko", "en", "mixed", "undecided"], help="Include language_guidance.md when the resolved output language is en or mixed.")
    args = parser.parse_args()
    query = args.query_flag or args.query
    if not query:
        parser.error("provide a query or --query")
    payload = query_style_profile(query, output_language=args.output_language)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] in {"matched", "ambiguous"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
