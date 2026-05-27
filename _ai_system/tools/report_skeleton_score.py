from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def find_skeleton_files(project: Path) -> list[Path]:
    candidates: list[Path] = []
    for folder in ["drafts", "notes"]:
        base = project / folder
        if not base.exists():
            continue
        for path in base.glob("*.md"):
            name = path.name.lower()
            text_head = read_text(path)[:2000].lower()
            if (
                "skeleton" in name
                or "scaffold" in name
                or "골조" in path.name
                or "주요 골조" in text_head
                or "chapter skeleton" in text_head
            ):
                candidates.append(path)
    return sorted(candidates)


def heading_count(text: str) -> int:
    return len(re.findall(r"(?m)^#{1,4}\s+\S+", text))


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.I) for pattern in patterns)


def has_scope_driven_coverage(text: str) -> bool:
    chapter_or_section_plan = bool(
        re.search(
            r"(?mi)^#{1,4}\s+(?:제\s*\d+\s*장|chapter\s*\d+|ch\s*0*\d+|\d+(?:\.\d+)?[.)]\s+)",
            text,
        )
    ) or has_any(text, [r"대목차", r"중목차", r"소목차", r"챕터별", r"장별", r"section[- ]by[- ]section"])
    coverage_axes = [
        has_any(text, [r"독자", r"reader", r"의사결정", r"decision", r"검토\s*질문", r"핵심\s*질문"]),
        has_any(text, [r"증거", r"evidence", r"source", r"원문", r"공식\s*url", r"capture"]),
        has_any(text, [r"리스크", r"risk", r"반론", r"counter", r"대안"]),
        has_any(text, [r"데이터", r"data_sources", r"\.csv", r"\.xlsx", r"시나리오", r"scenario"]),
        has_any(text, [r"표", r"그래프", r"차트", r"figure", r"chart", r"diagram", r"흐름도"]),
    ]
    return chapter_or_section_plan and sum(1 for matched in coverage_axes if matched) >= 3


def score_skeleton(path: Path) -> dict[str, object]:
    text = read_text(path)
    lower = text.lower()
    categories: list[dict[str, object]] = []
    deductions: list[dict[str, object]] = []

    def add(name: str, points: int, earned: bool, note: str) -> int:
        categories.append({"name": name, "points": points if earned else 0, "max_points": points, "note": note})
        return points if earned else 0

    def deduct(points: int, reason: str) -> None:
        deductions.append({"points": points, "reason": reason})

    score = 0
    score += add(
        "scope-driven coverage",
        15,
        has_scope_driven_coverage(text),
        "장 수를 고정하지 말고 PRD, 독자 의사결정, 근거, 리스크, 데이터/시각자료 범위를 덮는 골조가 필요합니다.",
    )
    score += add(
        "decision question",
        10,
        has_any(text, [r"의사결정", r"decision", r"검토\s*질문", r"핵심\s*질문"]),
        "보고서가 답해야 할 의사결정 질문이 필요합니다.",
    )
    score += add(
        "core thesis",
        10,
        has_any(text, [r"핵심\s*논지", r"business thesis", r"가설", r"thesis"]),
        "풀버전으로 확장할 중심 논지나 가설이 필요합니다.",
    )
    score += add(
        "evidence needs",
        15,
        has_any(text, [r"필요\s*자료", r"증거", r"source", r"원문", r"공식\s*url", r"capture"]),
        "각 장에 필요한 원문/증거 유형이 있어야 합니다.",
    )
    score += add(
        "claim and uncertainty plan",
        10,
        has_any(text, [r"claim", r"주장", r"미해결", r"unresolved", r"불확실", r"counsel"]),
        "주장, 해석, 미해결 쟁점을 분리할 계획이 필요합니다.",
    )
    score += add(
        "data and scenario plan",
        10,
        has_any(text, [r"data_sources", r"\.csv", r"\.xlsx", r"시나리오", r"scenario", r"민감도"]),
        "표/그래프를 만들 데이터와 시나리오 계획이 필요합니다.",
    )
    score += add(
        "visual plan",
        10,
        has_any(text, [r"그래프", r"차트", r"figure", r"chart", r"diagram", r"흐름도"]),
        "어느 장에서 어떤 표/그래프를 만들지 계획해야 합니다.",
    )
    score += add(
        "counterargument and risk plan",
        10,
        has_any(text, [r"반론", r"counter", r"risk", r"리스크", r"red\s*team", r"대안"]),
        "반론, 리스크, 대안 구조가 있어야 풀버전 밀도가 올라갑니다.",
    )
    score += add(
        "chapter expansion sequence",
        5,
        has_any(text, [r"챕터별", r"장별", r"순차", r"section[- ]by[- ]section"]),
        "풀 텍스트를 장별로 확장하는 순서가 있으면 좋습니다.",
    )
    score += add(
        "docx design readiness",
        5,
        has_any(text, [r"docx", r"pdf", r"템플릿", r"template", r"디자인"]),
        "DOCX/PDF 전환과 디자인 템플릿 고려가 필요합니다.",
    )

    if re.search(r"<table\b|<figure\b|<svg\b|<canvas\b|!\[", text, flags=re.I):
        deduct(15, "skeleton contains reader-facing table/figure/image markup; move visuals to the full-version stage")
    if len(text) < 3000:
        deduct(10, "skeleton is too short to guide a substantial full-version report")
    if re.search(r"(?:목차|대목차|챕터|chapter|장\s*수).{0,32}(?:고정|제한|기본|default)", text, flags=re.I):
        deduct(10, "skeleton treats chapter count as fixed/default; choose chapter count from PRD scope")
    if "0장" not in text and "제0장" not in text and "chapter 0" not in lower:
        deduct(8, "skeleton does not reserve Chapter 0 for the final summary")

    deduction_total = sum(item["points"] for item in deductions)
    final_score = max(0, min(100, score - deduction_total))
    blocked_next_actions: list[str] = []
    if final_score < 70:
        blocked_next_actions.append("chapter_full_text_expansion")
    if final_score < 80:
        blocked_next_actions.append("delivery_style_report_claims")

    return {
        "file": path.as_posix(),
        "skeleton_score": final_score,
        "bonus_score_before_deductions": score,
        "deduction_points": deduction_total,
        "categories": categories,
        "deductions": deductions,
        "blocked_next_actions": blocked_next_actions,
        "score_lift_opportunities": [
            category["note"] for category in categories if category["points"] == 0
        ][:8],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Score major report skeleton readiness before full drafting.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--file", help="Specific skeleton file path relative to project folder")
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2

    files = [project / args.file] if args.file else find_skeleton_files(project)
    results = [score_skeleton(path) for path in files if path.exists()]
    payload = {
        "project": project.name,
        "skeletons_checked": len(results),
        "results": results,
        "best_score": max((item["skeleton_score"] for item in results), default=0),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if not results or payload["best_score"] < 70 else 0


if __name__ == "__main__":
    raise SystemExit(main())
