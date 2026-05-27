from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


"""Optional audit hook for the visual review stage.

This script does not design charts, improve prose, or prove visual quality.
It only records hashes after the AI or human reviewer has already used the
chart_builder skill and a visual review checklist to revise visuals against
the drafted body chapters.
"""

PROJECT_ROOT = Path("00_사용자_작업공간")
DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".tsv"}
PLAN_DATA_FILENAMES = {"visual_plan.csv"}


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def rel(path: Path, project: Path) -> str:
    return path.relative_to(project).as_posix()


def artifact_info(path: Path, project: Path) -> dict[str, object]:
    return {
        "path": rel(path, project),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "mtime_ns": path.stat().st_mtime_ns,
    }


def is_backing_data_file(path: Path) -> bool:
    return path.suffix.lower() in DATA_SUFFIXES and path.name.lower() not in PLAN_DATA_FILENAMES


def validate_and_write(project_name: str) -> dict[str, object]:
    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"errors": [f"project not found: {project_name}"], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []
    chapter_dir = project / "reports" / "chapters"
    body_chapters = [
        path for path in sorted(chapter_dir.glob("ch*.html"))
        if not path.name.startswith("ch00")
    ] if chapter_dir.exists() else []
    summary_chapters = [
        path for path in sorted(chapter_dir.glob("ch00*.html"))
    ] if chapter_dir.exists() else []
    visual_plan = project / "data_sources" / "visual_plan.csv"
    visual_rows = read_csv(visual_plan)
    data_files = [
        path for path in sorted((project / "data_sources").glob("*"))
        if path.is_file() and is_backing_data_file(path)
    ]

    if not body_chapters:
        errors.append("visual pass requires body chapter fragments under reports/chapters/ch01+.html")
    if not visual_plan.exists():
        errors.append("visual pass requires data_sources/visual_plan.csv")
    elif not visual_rows:
        errors.append("visual pass requires at least one row in visual_plan.csv")
    if not data_files:
        errors.append("visual pass requires local CSV/XLSX/TSV backing files under data_sources/")

    missing_declared: list[str] = []
    for row in visual_rows:
        required = row.get("required", "").lower() in {"yes", "y", "true", "1", "required"}
        status = row.get("status", "").lower()
        if not required and status not in {"planned", "required", "implemented", "done"}:
            continue
        data_file = row.get("data_file", "") or row.get("source_data", "")
        if data_file and not data_file.startswith("http"):
            candidate = project / data_file
            if not candidate.exists():
                missing_declared.append(f"{row.get('visual_id') or row.get('title')}: {data_file}")
    if missing_declared:
        errors.append("declared visual data/source artifact is missing: " + " | ".join(missing_declared[:8]))

    if errors:
        return {"project": project_name, "errors": errors, "warnings": warnings}

    latest_body_mtime_ns = max(path.stat().st_mtime_ns for path in body_chapters)
    manifest = {
        "project": project_name,
        "finalized_at_kst": now_kst(),
        "purpose": "optional audit hook; records hashes after table/chart/diagram work was reviewed against drafted body chapters",
        "status": "visuals_reviewed_after_body_chapters",
        "latest_body_chapter_mtime_ns": latest_body_mtime_ns,
        "body_chapter_integrity": [artifact_info(path, project) for path in body_chapters],
        "summary_chapter_integrity": [artifact_info(path, project) for path in summary_chapters],
        "visual_plan_integrity": artifact_info(visual_plan, project),
        "data_artifacts": [artifact_info(path, project) for path in data_files],
        "visual_rows": len(visual_rows),
        "warnings": warnings,
    }
    out = project / "reports" / "visual_pass_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    manifest["manifest_path"] = rel(out, project)
    return {"project": project_name, "errors": [], "warnings": warnings, "manifest": manifest}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Optional audit hook for a completed visual review; this does not create or judge visual quality."
    )
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    args = parser.parse_args()
    payload = validate_and_write(args.project)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
