from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from report_quality_schema import REQUIRED_WORKPACK_MARKERS, workpack_quality_issues
from workspace_config import list_value, load_config


PROJECT_ROOT = Path("00_사용자_작업공간")
DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".tsv"}
PLAN_DATA_FILENAMES = {"visual_plan.csv"}
REQUIRED_VISUAL_COLUMNS = {"visual_id", "chapter", "visual_type", "purpose", "decision_use", "status"}
INACTIVE_PRESET_VALUES = {"", "undecided", "none", "n/a", "na", "null", "-"}
EXTERNAL_SCRIPT_RE = re.compile(r"<script\b[^>]*\bsrc=[\"']https?://", flags=re.I)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def has_any(path: Path, pattern: str) -> bool:
    return path.exists() and any(path.glob(pattern))


def is_backing_data_file(path: Path) -> bool:
    return path.suffix.lower() in DATA_SUFFIXES and path.name.lower() not in PLAN_DATA_FILENAMES


def is_substantial_project(project: Path) -> bool:
    config = load_config()
    markers = list_value(config, "report_factory.substantial_markers")
    prd_text = " ".join(path.read_text(encoding="utf-8", errors="ignore") for path in (project / "report_prd").glob("*.md"))
    toc_text = " ".join(path.read_text(encoding="utf-8", errors="ignore") for path in (project / "drafts").glob("*.md"))
    combined = (prd_text + " " + toc_text).lower()
    return any(marker.lower() in combined for marker in markers)


def supported_preset_ids() -> set[str]:
    index_path = Path("_ai_system") / "document_presets" / "INDEX.json"
    payload = read_json(index_path)
    presets = payload.get("presets", [])
    if not isinstance(presets, list):
        return set()
    ids: set[str] = set()
    for entry in presets:
        if isinstance(entry, dict):
            preset_id = str(entry.get("preset_id", "")).strip()
            if preset_id:
                ids.add(preset_id)
    return ids


def extract_markdown_field_values(text: str, field: str) -> list[str]:
    values: list[str] = []
    pattern = re.compile(
        rf"(?im)^\s*(?:[-*]\s*)?`?{re.escape(field)}`?\s*[:：]\s*`?([A-Za-z0-9_.-]+)`?"
    )
    for match in pattern.finditer(text):
        value = match.group(1).strip().strip("`")
        if value:
            values.append(value)
    return values


def prd_field_values(project: Path, field: str) -> list[str]:
    values: list[str] = []
    for path in sorted((project / "report_prd").glob("*.md")):
        values.extend(extract_markdown_field_values(read_text(path), field))
    return values


def external_script_hits(paths: list[Path], project: Path) -> list[str]:
    hits: list[str] = []
    for path in paths:
        text = read_text(path)
        if EXTERNAL_SCRIPT_RE.search(text):
            hits.append(rel(path, project))
    return hits

def validate_project(project: Path, strict: bool, enforce_modern: bool) -> dict[str, object]:
    config = load_config()
    errors: list[str] = []
    warnings: list[str] = []
    substantial = is_substantial_project(project)
    legacy_project = project.name in set(list_value(config, "legacy_report_factory_projects"))

    def factory_gap(message: str) -> None:
        if legacy_project and strict and not enforce_modern:
            warnings.append("legacy migration required: " + message)
        else:
            errors.append(message)

    report_prd = has_any(project / "report_prd", "*.md")
    detailed_toc = bool(list((project / "drafts").glob("*toc*.md")) or list((project / "drafts").glob("*목차*.md")))
    skeleton = bool(
        list((project / "drafts").glob("*skeleton*.md"))
        or list((project / "drafts").glob("*골조*.md"))
        or list((project / "reports").glob("*skeleton*.md"))
        or list((project / "reports").glob("*골조*.md"))
        or (project / "reports" / "major_skeleton.md").exists()
    )

    workpack_dir = project / "reports" / "chapter_workpacks"
    chapter_dir = project / "reports" / "chapters"
    workpacks = sorted(workpack_dir.glob("ch*_workpack.md")) if workpack_dir.exists() else []
    chapters = sorted(chapter_dir.glob("ch*.html")) if chapter_dir.exists() else []
    cover_data = project / "reports" / "cover.data.json"
    cover_payload = read_json(cover_data)
    current_pointer = read_json(project / "reports" / "current" / "version_pointer.json")
    visual_review_note = project / "reports" / "visual_review.md"
    visual_pass_manifest = project / "reports" / "visual_pass_manifest.json"
    assembly_manifest_path = project / "reports" / "report_assembly_manifest.json"
    assembly_manifest = read_json(assembly_manifest_path)
    visual_plan = project / "data_sources" / "visual_plan.csv"
    visual_rows = read_csv(visual_plan)
    data_files = [p for p in (project / "data_sources").glob("*") if is_backing_data_file(p)]
    assembled_reports = []
    for report in (project / "reports").glob("*.html"):
        text = report.read_text(encoding="utf-8", errors="ignore")
        if "data-assembled-report=\"true\"" in text or "mode: concatenate_only_no_rewrite" in text:
            assembled_reports.append(report)

    if substantial and not report_prd:
        factory_gap("substantial report factory requires a report PRD under report_prd/")
    if report_prd:
        supported_ids = supported_preset_ids()
        preset_values = prd_field_values(project, "document_type_preset")
        invalid_presets = sorted(
            {
                value
                for value in preset_values
                if value.strip().lower() not in INACTIVE_PRESET_VALUES and supported_ids and value not in supported_ids
            }
        )
        if invalid_presets:
            factory_gap(
                "report PRD contains unsupported document_type_preset id(s): "
                + ", ".join(invalid_presets)
                + "; use an indexed preset_id from _ai_system/document_presets/INDEX.json or undecided"
            )
    if substantial and not detailed_toc:
        factory_gap("substantial report factory requires a detailed TOC under drafts/")
    if substantial and strict and not skeleton:
        factory_gap("strict report factory requires a major skeleton before chapter drafting")
    elif substantial and not skeleton:
        warnings.append("major skeleton not found; full chapter drafting may be premature")

    if chapters and not workpacks:
        factory_gap("chapter fragments exist but reports/chapter_workpacks/ch*_workpack.md is missing")
    if strict:
        for workpack in workpacks:
            for issue in workpack_quality_issues(workpack):
                factory_gap(f"chapter workpack is not substantive enough: {workpack.relative_to(project).as_posix()} ({issue})")
    for chapter in chapters:
        stem = chapter.stem
        if stem == "ch00_summary":
            expected = workpack_dir / "ch00_summary_workpack.md"
        else:
            expected = workpack_dir / f"{stem}_workpack.md"
        if not expected.exists():
            factory_gap(f"chapter fragment has no matching workpack: {chapter.relative_to(project).as_posix()}")
        text = chapter.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"</?(?:html|head|body)\b", text, flags=re.I):
            factory_gap(f"chapter fragment contains full-document wrapper tags: {chapter.relative_to(project).as_posix()}")

    if substantial and strict and not chapters:
        factory_gap("strict report factory requires chapter fragments under reports/chapters/ch*.html")
    if substantial and strict and not cover_data.exists():
        factory_gap("strict report factory requires reports/cover.data.json for the reusable cover component")
    if strict and assembled_reports:
        pointer_version = str(current_pointer.get("version", "") or "").strip()
        pointer_key = str(current_pointer.get("version_key", "") or "").strip()
        cover_version = str(cover_payload.get("version", "") or "").strip()
        if pointer_version and cover_version and cover_version not in {pointer_version, pointer_key}:
            factory_gap(
                "reader-facing cover version is stale: "
                f"reports/cover.data.json version={cover_version}, current pointer={pointer_version}/{pointer_key}"
            )
    if assembled_reports and not chapters:
        factory_gap("assembled report exists but no source chapter fragments were found")
    if strict and assembled_reports:
        cdn_hits = external_script_hits([*assembled_reports, *chapters], project)
        if cdn_hits:
            factory_gap(
                "strict/versioned report HTML must not depend on external script/CDN assets; "
                "use local ECharts as a render aid or static SVG/PNG before assembly: "
                + ", ".join(cdn_hits[:8])
            )
        if not assembly_manifest_path.exists():
            factory_gap("assembled report exists but reports/report_assembly_manifest.json is missing")
        elif assembly_manifest.get("assembly_mode") != "concatenate_only_no_rewrite":
            factory_gap("assembly manifest must declare assembly_mode=concatenate_only_no_rewrite")
        report_text = assembled_reports[-1].read_text(encoding="utf-8", errors="ignore")
        chapter_integrity = assembly_manifest.get("chapter_integrity")
        if not isinstance(chapter_integrity, list) or not chapter_integrity:
            factory_gap("assembly manifest lacks chapter_integrity hashes")
        else:
            recorded = {
                str(item.get("path", "")): str(item.get("sha256", ""))
                for item in chapter_integrity
                if isinstance(item, dict)
            }
            for chapter in chapters:
                rel_path = rel(chapter, project)
                raw = chapter.read_text(encoding="utf-8", errors="ignore")
                if recorded.get(rel_path) != sha256_file(chapter):
                    factory_gap(f"chapter changed after assembly or hash missing: {rel_path}")
                if raw not in report_text:
                    factory_gap(f"assembled report does not contain the exact chapter fragment: {rel_path}")

    if substantial and not visual_plan.exists():
        factory_gap("substantial reports require data_sources/visual_plan.csv")
    elif visual_plan.exists():
        headers = set(visual_rows[0].keys()) if visual_rows else set()
        missing = sorted(REQUIRED_VISUAL_COLUMNS - headers)
        if missing:
            factory_gap("visual_plan.csv is missing role-based columns: " + ", ".join(missing))
        role_fields = ["purpose", "decision_use"]
        weak_role_rows = [
            row.get("visual_id") or f"row_{idx + 1}"
            for idx, row in enumerate(visual_rows)
            if any(not row.get(field) for field in role_fields)
        ]
        if weak_role_rows:
            message = "visual_plan rows lack purpose or decision_use: " + " | ".join(weak_role_rows[:8])
            if strict:
                factory_gap(message)
            else:
                warnings.append(message)
        weak_takeaway_rows = [
            row.get("visual_id") or f"row_{idx + 1}"
            for idx, row in enumerate(visual_rows)
            if not row.get("expected_reader_takeaway")
        ]
        if weak_takeaway_rows:
            warnings.append("visual_plan rows lack expected_reader_takeaway: " + " | ".join(weak_takeaway_rows[:8]))
        required_rows = [
            row
            for row in visual_rows
            if (row.get("required", "").lower() in {"yes", "y", "true", "1", "required"} or row.get("status", "").lower() in {"required", "planned"})
        ]
        for row in required_rows:
            data_file = row.get("data_file") or row.get("source_data") or row.get("data_or_source_artifact")
            visual_id = row.get("visual_id") or row.get("title") or "(unnamed visual)"
            if not data_file and not row.get("source_record"):
                message = f"planned visual lacks data_file/source_data or source_record: {visual_id}"
                if strict:
                    factory_gap(message)
                else:
                    warnings.append(message)
            elif data_file and not re.match(r"https?://", data_file):
                candidate = project / data_file
                if not candidate.exists():
                    message = f"planned visual data/source artifact is missing for {visual_id}: {data_file}"
                    if strict:
                        factory_gap(message)
                    else:
                        warnings.append(message)
    if strict and visual_plan.exists() and visual_rows and not data_files:
        factory_gap("strict report factory has a visual plan but no local CSV/XLSX data files")
    if strict and chapters and visual_plan.exists() and visual_rows and data_files:
        if not visual_pass_manifest.exists() and not visual_review_note.exists():
            warnings.append(
                "visual review record not found; use the chart_builder skill after body chapters "
                "and record reports/visual_review.md or the optional visual_pass_manifest.json hook before final handoff"
            )
        if visual_pass_manifest.exists():
            visual_pass = read_json(visual_pass_manifest)
            body_chapters = [path for path in chapters if not path.name.startswith("ch00")]
            recorded = {
                str(item.get("path", "")): str(item.get("sha256", ""))
                for item in visual_pass.get("body_chapter_integrity", [])
                if isinstance(item, dict)
            }
            for chapter in body_chapters:
                rel_path = rel(chapter, project)
                if recorded.get(rel_path) != sha256_file(chapter):
                    factory_gap(f"visual pass is missing or stale for body chapter: {rel_path}")
            if assembled_reports and assembly_manifest.get("visual_pass_manifest") not in {"", "reports/visual_pass_manifest.json"}:
                factory_gap("assembly manifest references an unexpected visual pass manifest")
            if assembled_reports and assembly_manifest.get("visual_pass_manifest") == "":
                warnings.append("assembly manifest does not reference the optional visual_pass_manifest.json hook")
        elif assembled_reports and assembly_manifest.get("visual_pass_manifest"):
            factory_gap("assembly manifest claims a visual pass manifest that is not present")

    return {
        "project": project.name,
        "substantial_detected": substantial,
        "legacy_project": legacy_project,
        "modern_enforced": enforce_modern,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "report_prd": report_prd,
            "detailed_toc": detailed_toc,
            "major_skeleton": skeleton,
            "workpacks": len(workpacks),
            "chapter_fragments": len(chapters),
            "assembled_reports": len(assembled_reports),
            "cover_data": cover_data.exists(),
            "visual_review_note": visual_review_note.exists(),
            "visual_pass_manifest": visual_pass_manifest.exists(),
            "visual_plan_rows": len(visual_rows),
            "data_files": len(data_files),
        },
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate report factory production artifacts.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--strict", action="store_true", help="Require full substantial-report factory artifacts.")
    parser.add_argument(
        "--enforce-modern",
        action="store_true",
        help="Fail legacy projects that have not yet been migrated to chapter-workpack/assembly factory artifacts.",
    )
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2
    payload = validate_project(project, args.strict, args.enforce_modern)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
