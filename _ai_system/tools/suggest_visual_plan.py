from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
VISUAL_PLAN_HEADER = [
    "visual_id",
    "chapter",
    "visual_type",
    "title",
    "purpose",
    "decision_use",
    "expected_reader_takeaway",
    "required",
    "data_file",
    "source_data",
    "source_record",
    "status",
    "notes",
]

RULES = [
    (
        "flow_diagram",
        ["flow", "process", "settlement", "architecture", "역할", "흐름", "정산", "구조", "프로세스"],
        "역할과 흐름을 이해해야 하는 장입니다. 단계, 책임, 통제 지점을 보여주는 flow diagram이 적합합니다.",
    ),
    (
        "decision_matrix",
        ["option", "alternative", "compare", "tradeoff", "대안", "비교", "선택", "장단점"],
        "대안을 비교하는 장입니다. 기준별 강약과 잔존 리스크를 함께 보이는 decision matrix가 적합합니다.",
    ),
    (
        "timeline",
        ["timeline", "roadmap", "milestone", "schedule", "일정", "단계", "입법", "로드맵"],
        "순서와 마일스톤이 중요한 장입니다. timeline으로 의존관계와 지연 위험을 보이세요.",
    ),
    (
        "scenario_chart",
        ["scenario", "sensitivity", "projection", "revenue", "cost", "시장", "수익", "비용", "시나리오"],
        "시나리오나 규모 비교가 필요한 장입니다. bar/line/waterfall 중 수치 구조에 맞춰 선택하세요.",
    ),
    (
        "risk_heatmap",
        ["risk", "legal", "compliance", "approval", "리스크", "규제", "법률", "승인", "불확실"],
        "위험도를 비교해야 하는 장입니다. risk heatmap이나 legal matrix가 적합합니다.",
    ),
]


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S KST")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def chapter_id(path: Path) -> str:
    match = re.match(r"(ch\d{2})", path.stem, flags=re.I)
    return match.group(1).lower() if match else path.stem.lower()


def best_visual_type(text: str) -> tuple[str, str]:
    lowered = text.lower()
    scored: list[tuple[int, str, str]] = []
    for visual_type, terms, reason in RULES:
        score = sum(1 for term in terms if term.lower() in lowered)
        scored.append((score, visual_type, reason))
    score, visual_type, reason = max(scored, key=lambda item: item[0])
    if score == 0:
        return "evidence_table", "정확한 근거, 기준, 항목 비교가 필요한 장입니다. 먼저 evidence table을 제안합니다."
    return visual_type, reason


def title_from_workpack(chapter: str, text: str, visual_type: str) -> str:
    for pattern in [r"Reader Decision\s*\n+(.+)", r"Core Question\s*\n+(.+)", r"#\s+(.+)"]:
        match = re.search(pattern, text, flags=re.I)
        if match:
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            if value:
                return value[:80]
    return f"{chapter} {visual_type.replace('_', ' ')}"


def existing_visual_ids(project: Path) -> set[str]:
    path = project / "data_sources" / "visual_plan.csv"
    ids: set[str] = set()
    if not path.exists():
        return ids
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            value = (row.get("visual_id") or "").strip()
            if value:
                ids.add(value.lower())
    return ids


def suggest(project_name: str) -> dict[str, object]:
    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"error": f"project not found: {project_name}"}
    workpacks = sorted((project / "reports" / "chapter_workpacks").glob("ch*_workpack.md"))
    existing = existing_visual_ids(project)
    rows: list[dict[str, str]] = []
    for index, path in enumerate(workpacks, start=1):
        text = read_text(path)
        chapter = chapter_id(path)
        visual_type, reason = best_visual_type(text)
        visual_id = f"vis-{chapter}-{index:02d}"
        if visual_id.lower() in existing:
            continue
        rows.append(
            {
                "visual_id": visual_id,
                "chapter": chapter,
                "visual_type": visual_type,
                "title": title_from_workpack(chapter, text, visual_type),
                "purpose": reason,
                "decision_use": "Support the chapter decision rather than fill a visual quota.",
                "expected_reader_takeaway": "The reader can compare options, risks, flow, or evidence faster than prose alone.",
                "required": "yes",
                "data_file": f"data_sources/{visual_id}.csv",
                "source_data": "",
                "source_record": "",
                "status": "suggested",
                "notes": "Review and replace this suggestion with a concrete data-backed visual before assembly.",
            }
        )
    return {
        "project": project_name,
        "generated_at_kst": now_kst(),
        "purpose": "visual plan suggestions; this is not a finished chart or data file",
        "suggestions": rows,
        "notes": [
            "Choose visuals by reader decision, not by fixed quotas.",
            "Every accepted visual still needs a local CSV/XLSX or source-record-backed qualitative artifact.",
        ],
    }


def write_suggestions(project_name: str, payload: dict[str, object]) -> dict[str, str]:
    project = PROJECT_ROOT / project_name
    out_dir = project / "reports" / "visual_suggestions"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "visual_suggestions.json"
    csv_path = out_dir / "visual_suggestions.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    rows = payload.get("suggestions", [])
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VISUAL_PLAN_HEADER)
        writer.writeheader()
        for row in rows if isinstance(rows, list) else []:
            if isinstance(row, dict):
                writer.writerow({key: row.get(key, "") for key in VISUAL_PLAN_HEADER})
    return {
        "json": json_path.relative_to(project).as_posix(),
        "csv": csv_path.relative_to(project).as_posix(),
    }


def append_to_visual_plan(project_name: str, payload: dict[str, object]) -> str:
    project = PROJECT_ROOT / project_name
    path = project / "data_sources" / "visual_plan.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    rows = payload.get("suggestions", [])
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=VISUAL_PLAN_HEADER)
        if not exists:
            writer.writeheader()
        for row in rows if isinstance(rows, list) else []:
            if isinstance(row, dict):
                writer.writerow({key: row.get(key, "") for key in VISUAL_PLAN_HEADER})
    return path.relative_to(project).as_posix()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Suggest decision-useful visuals from chapter workpacks.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--write-status", action="store_true", help="Write reports/visual_suggestions outputs.")
    parser.add_argument("--append-visual-plan", action="store_true", help="Append suggestions to data_sources/visual_plan.csv.")
    args = parser.parse_args()
    payload = suggest(args.project)
    if "error" in payload:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    if args.write_status:
        payload["status_files"] = write_suggestions(args.project, payload)
    if args.append_visual_plan:
        payload["visual_plan"] = append_to_visual_plan(args.project, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
