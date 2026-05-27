from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from workspace_config import get_path, load_config, resolved_domain_profile


PROJECT_ROOT = Path("00_사용자_작업공간")
DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".tsv"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d_%H%M%S")


def safe_rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def copy_file(src: Path, dst: Path, project: Path, dry_run: bool) -> dict[str, object]:
    item = {
        "source": safe_rel(src, project),
        "outbox_path": safe_rel(dst, project),
        "bytes": src.stat().st_size,
        "sha256": sha256(src),
    }
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return item


def latest_report(project: Path) -> Path | None:
    candidates = [
        path
        for path in sorted((project / "reports").glob("*.html"))
        if "quality_status" not in path.as_posix().lower() and "outbox" not in path.as_posix().lower()
    ]
    return candidates[-1] if candidates else None


def configured_report(project: Path) -> tuple[Path | None, str]:
    manifests = [
        project / "reports" / "report_assembly_manifest.json",
        project / "project_state" / "report_stage_manifest.json",
    ]
    keys = ["active_report", "report_path", "current_report", "output"]
    for manifest in manifests:
        data = read_json(manifest)
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                path = project / value.strip()
                if path.exists() and path.is_file():
                    return path, f"{manifest.relative_to(project).as_posix()}:{key}"
    return None, ""


def selected_report(project: Path, report: str) -> tuple[Path | None, str, list[str]]:
    warnings: list[str] = []
    if report:
        report_path = project / report
        if not report_path.exists():
            warnings.append(f"requested report not found: {report}")
            return None, "cli_argument_missing", warnings
        return report_path, "cli_argument", warnings

    report_path, source = configured_report(project)
    if report_path:
        return report_path, source, warnings

    fallback = latest_report(project)
    if fallback:
        warnings.append("active report was not declared; used latest reports/*.html fallback")
        return fallback, "latest_html_fallback", warnings
    warnings.append("no report HTML selected for outbox")
    return None, "", warnings


def collect_files(project: Path, report: str, include_originals: bool) -> tuple[list[Path], dict[str, object]]:
    files: list[Path] = []
    report_path, report_selection_source, warnings = selected_report(project, report)
    if report_path and report_path.exists():
        files.append(report_path)

    fixed_candidates = [
        project / "reports" / "cover.data.json",
        project / "reports" / "report_assembly_manifest.json",
        project / "reports" / "report_claim_register.md",
        project / "source_index" / "source_master_index.md",
        project / "references" / "source_link_register.csv",
        project / "data_sources" / "visual_plan.csv",
    ]
    files.extend(path for path in fixed_candidates if path.exists())
    files.extend(path for path in sorted((project / "data_sources").glob("*")) if path.suffix.lower() in DATA_SUFFIXES)
    files.extend(path for path in sorted((project / "reports" / "workflow_status").glob("*")) if path.is_file())
    files.extend(path for path in sorted((project / "reports" / "chapter_quality").glob("*")) if path.is_file())
    files.extend(path for path in sorted((project / "reports" / "visual_suggestions").glob("*")) if path.is_file())
    files.extend(path for path in sorted((project / "reports" / "cover_preview").glob("*")) if path.is_file())
    files.extend(path for path in sorted((project / "reports" / "quality_status").glob("*")) if path.is_file())
    files.extend(path for path in sorted((project / "reports" / "source_status").glob("*")) if path.is_file())
    if include_originals:
        files.extend(path for path in sorted((project / "references" / "received_originals").rglob("*")) if path.is_file())

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.resolve()
        if resolved not in seen and path.exists() and path.is_file():
            seen.add(resolved)
            unique.append(path)

    source_link_register = project / "references" / "source_link_register.csv"
    if not source_link_register.exists():
        warnings.append("references/source_link_register.csv is missing; URL-only source status may be harder to audit")

    return unique, {
        "report_selection_source": report_selection_source,
        "selected_report": safe_rel(report_path, project) if report_path and report_path.exists() else "",
        "source_link_register_status": "present" if source_link_register.exists() else "missing",
        "warnings": warnings,
    }


def run_validator(command: list[str]) -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, *command],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": "python " + " ".join(command),
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-12000:],
        "stderr": proc.stderr[-4000:],
    }


def validation_summary(project_name: str) -> dict[str, object]:
    commands = [
        ["_ai_system/tools/report_gate_status.py", "--project", project_name],
        ["_ai_system/tools/validate_report_artifact.py", "--project", project_name, "--strict-delivery"],
        ["_ai_system/tools/validate_closeout.py", "--project", project_name],
    ]
    results = [run_validator(command) for command in commands]
    return {
        "status": "pass" if all(result["exit_code"] == 0 for result in results) else "has_failures",
        "results": results,
    }


def generate_status_panels(project_name: str, dry_run: bool, enabled: bool) -> dict[str, object]:
    if not enabled:
        return {"status": "disabled", "results": []}
    if dry_run:
        return {"status": "skipped_dry_run", "results": []}
    project = PROJECT_ROOT / project_name
    commands = [
        ["_ai_system/tools/report_workflow_next.py", "--project", project_name, "--write-status"],
        ["_ai_system/tools/build_source_status_panel.py", "--project", project_name, "--write-status"],
    ]
    if (project / "reports" / "cover.data.json").exists():
        commands.append(["_ai_system/tools/validate_cover_render.py", "--project", project_name, "--write-preview"])
    results = [run_validator(command) for command in commands]
    return {
        "status": "pass" if all(result["exit_code"] == 0 for result in results) else "has_failures",
        "results": results,
    }


def package_status(selection: dict[str, object], validation: dict[str, object]) -> str:
    if validation.get("status") == "has_failures":
        return "has_failures"
    if not selection.get("selected_report"):
        return "incomplete"
    warnings = selection.get("warnings")
    if isinstance(warnings, list) and warnings:
        return "needs_review"
    return str(validation.get("status") or "unknown")


def write_upload_readme(outbox: Path, dry_run: bool) -> Path:
    readme = outbox / "CLOUD_UPLOAD_README.md"
    text = """# Delivery Outbox

This folder is a local handoff package for review or optional cloud upload.

Default safety rule:

- Do not upload preserved source originals unless the user explicitly approved it.
- Prefer uploading the assembled report, source status panel when generated, source link register, claim register, source index, and backing CSV/XLSX files.
- Optional advisory panels such as chapter quality, visual suggestions, or quality score should be generated only when specifically useful; they are not report-quality proof.
- Google Drive or Notion upload is a separate step and must use explicit user approval. Prepare that step with `prepare_cloud_handoff.py` before using a connector.
- The workflow panel is a next-action guide, not proof of completion.
- The chapter quality and visual suggestion panels are coaching signals, not proof that the report is true.
- This outbox is not proof that the report content is true; use the validation summaries and source records for that.
"""
    if not dry_run:
        readme.write_text(text, encoding="utf-8", newline="\n")
    return readme


def build_outbox(
    project_name: str,
    report: str,
    include_originals: bool,
    dry_run: bool,
    include_validation_summary: bool,
    require_active_report: bool,
    include_status_panels: bool,
) -> dict[str, object]:
    root = Path.cwd()
    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"error": f"project not found: {project_name}"}

    config = load_config(root)
    base_outbox = str(get_path(config, "delivery.default_outbox_dir", "reports/outbox"))
    outbox = project / base_outbox / now_kst()
    try:
        outbox.resolve().relative_to(project.resolve())
    except ValueError:
        return {"error": "configured outbox path must stay inside the project folder"}

    status_panels = generate_status_panels(project_name, dry_run, include_status_panels)
    files, selection = collect_files(project, report, include_originals)
    if require_active_report:
        report_selection_source = str(selection.get("report_selection_source") or "")
        allowed_sources = ("cli_argument", "reports/report_assembly_manifest.json:", "project_state/report_stage_manifest.json:")
        if not any(report_selection_source.startswith(source) for source in allowed_sources):
            return {
                "error": "active report is required for verified handoff; run assemble_report.py or pass --report explicitly",
                "selection": selection,
            }
    validation = validation_summary(project_name) if include_validation_summary else {"status": "skipped"}
    status = package_status(selection, validation)
    copied = []
    for src in files:
        dst = outbox / safe_rel(src, project)
        copied.append(copy_file(src, dst, project, dry_run))

    upload_readme = write_upload_readme(outbox, dry_run)
    manifest = {
        "project": project_name,
        "created_at_kst": now_kst(),
        "dry_run": dry_run,
        "active_domain_profile": resolved_domain_profile(config),
        "include_originals": include_originals,
        "outbox": safe_rel(outbox, project),
        "selection": selection,
        "package_status": status,
        "status_panels": status_panels,
        "validation_summary": validation,
        "files": copied,
        "cloud_upload": {
            "status": "not_uploaded",
            "requires_explicit_user_approval": True,
            "recommended_mode": "public_safe_only_unless_user_approves_originals",
        },
        "notes": [
            "Local outbox packaging is a convenience step, not content validation.",
            "Run the report and research validators before describing a report as review-ready.",
        ],
    }
    manifest_path = project / "reports" / "export_manifest.json"
    outbox_manifest_path = outbox / "export_manifest.json"
    validation_summary_path = outbox / "handoff_validation_summary.json"
    if not dry_run:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        outbox_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        validation_summary_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    return {
        "project": project_name,
        "dry_run": dry_run,
        "outbox": safe_rel(outbox, project),
        "files_selected": len(files),
        "include_originals": include_originals,
        "manifest": safe_rel(manifest_path, project),
        "outbox_manifest": safe_rel(outbox_manifest_path, project),
        "validation_summary": safe_rel(validation_summary_path, project),
        "validation_status": validation.get("status"),
        "status_panel_status": status_panels.get("status"),
        "package_status": status,
        "selection": selection,
        "upload_readme": safe_rel(upload_readme, project),
        "copied_files": copied,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Build a local report delivery outbox without uploading to cloud.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--report", default="", help="Optional project-relative report HTML path.")
    parser.add_argument("--include-originals", action="store_true", help="Include preserved source originals. Off by default.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be packaged without writing files.")
    parser.add_argument(
        "--require-active-report",
        action="store_true",
        help="Fail unless the report is selected by --report or an active_report/report_path manifest field.",
    )
    parser.add_argument(
        "--skip-validation-summary",
        action="store_true",
        help="Do not run lightweight validation summary commands for the outbox manifest.",
    )
    parser.add_argument(
        "--include-status-panels",
        action="store_true",
        help="Generate optional user-facing status panels before packaging. Off by default.",
    )
    args = parser.parse_args()

    payload = build_outbox(
        args.project,
        args.report,
        args.include_originals,
        args.dry_run,
        include_validation_summary=not args.skip_validation_summary,
        require_active_report=args.require_active_report,
        include_status_panels=args.include_status_panels,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if "error" in payload else 0


if __name__ == "__main__":
    raise SystemExit(main())
