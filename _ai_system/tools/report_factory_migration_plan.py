from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")


CHECKS = [
    ("prd", "report_prd/*.md", "Create or refresh the report PRD."),
    ("toc", "drafts/*toc*.md", "Create or refresh the detailed TOC."),
    ("skeleton", "reports/major_skeleton.md", "Create a major skeleton and run report_skeleton_score.py."),
    ("workpacks", "reports/chapter_workpacks/ch*_workpack.md", "Create chapter workpacks before rewriting prose."),
    ("chapters", "reports/chapters/ch*.html", "Split or regenerate report body as chapter fragments."),
    ("cover_data", "reports/cover.data.json", "Create cover.data.json from the reusable cover component samples."),
    ("visual_plan", "data_sources/visual_plan.csv", "Create visual_plan.csv and map every material visual to data/evidence."),
    ("assembly_manifest", "reports/report_assembly_manifest.json", "Assemble the final HTML with assemble_report.py."),
]


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S KST")


def exists(project: Path, pattern: str) -> bool:
    return bool(list(project.glob(pattern)))


def analyze(project_name: str) -> dict[str, object]:
    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"error": f"project not found: {project_name}"}
    report_html = sorted((project / "reports").glob("*.html"))
    items: list[dict[str, object]] = []
    for key, pattern, action in CHECKS:
        present = exists(project, pattern)
        items.append(
            {
                "artifact": key,
                "pattern": pattern,
                "present": present,
                "action": "No action required." if present else action,
            }
        )
    missing = [item for item in items if not item["present"]]
    next_action = "ready_for_factory_validation" if not missing else str(missing[0]["action"])
    return {
        "project": project_name,
        "generated_at_kst": now_kst(),
        "purpose": "legacy-to-report-factory migration planning; this does not rewrite the report",
        "existing_report_html": [path.relative_to(project).as_posix() for path in report_html],
        "missing_count": len(missing),
        "items": items,
        "next_action": next_action,
        "recommended_order": [
            "Archive the legacy report as comparison material.",
            "Create PRD and detailed TOC if missing.",
            "Create major skeleton and score it.",
            "Create chapter workpacks.",
            "Regenerate chapter fragments from workpacks instead of editing one large HTML.",
            "Create visual_plan.csv and backing data files.",
            "Create cover.data.json and validate cover preview.",
            "Assemble without rewriting prose.",
            "Run closeout gates and compare against the archived legacy report.",
        ],
    }


def write_status(project_name: str, payload: dict[str, object]) -> dict[str, str]:
    project = PROJECT_ROOT / project_name
    out_dir = project / "reports" / "migration_plan"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report_factory_migration_plan.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return {"json": path.relative_to(project).as_posix()}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Plan how a legacy report project should migrate to Report Factory.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--write-status", action="store_true", help="Write reports/migration_plan/report_factory_migration_plan.json")
    args = parser.parse_args()
    payload = analyze(args.project)
    if args.write_status and "error" not in payload:
        payload["status_files"] = write_status(args.project, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2 if "error" in payload else 0


if __name__ == "__main__":
    raise SystemExit(main())
