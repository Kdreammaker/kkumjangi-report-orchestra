from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_delivery_outbox"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *command],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def remove_smoke_project(project: Path) -> None:
    if not project.exists():
        return
    root = PROJECT_ROOT.resolve()
    target = project.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to remove path outside project root: {target}") from exc
    shutil.rmtree(target)


def write_minimal_project(project: Path, declare_active_report: bool) -> None:
    remove_smoke_project(project)
    (project / "reports").mkdir(parents=True, exist_ok=True)
    (project / "project_state").mkdir(parents=True, exist_ok=True)
    (project / "references").mkdir(parents=True, exist_ok=True)
    (project / "reports" / "internal_review_report.html").write_text(
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><title>Smoke</title></head>"
        "<body><main><h1>Smoke Report</h1><p>Outbox selection smoke test.</p></main></body></html>\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest: dict[str, object] = {"stage": "smoke"}
    if declare_active_report:
        manifest["active_report"] = "reports/internal_review_report.html"
    (project / "project_state" / "report_stage_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    (project / "references" / "source_link_register.csv").write_text(
        "source_id,file_name,title,url,publisher,accessed_at_kst,url_status,download_status,capture_status,use_level,original_path,capture_path,notes\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "source_index").mkdir(parents=True, exist_ok=True)
    (project / "source_index" / "source_master_index.md").write_text(
        "| source_id | title | status | original_verified | url_or_path |\n|---|---|---|---|---|\n",
        encoding="utf-8",
        newline="\n",
    )


def write_assembly_inputs(project: Path) -> None:
    remove_smoke_project(project)
    (project / "reports" / "chapters").mkdir(parents=True, exist_ok=True)
    (project / "reports" / "cover.data.json").write_text(
        json.dumps(
            {
                "classification": "Internal",
                "report_type": "Smoke Test",
                "kicker": "Assembler smoke",
                "report_title": "Delivery Outbox Smoke Report",
                "subtitle": "Active report routing check",
                "project_name": SMOKE_PROJECT,
                "report_no": "SMOKE-001",
                "date": "2026-05-24",
                "version": "v0",
                "prepared_by": "System",
                "prepared_for": "QA",
                "distribution": "Local test only",
                "approval_author": "-",
                "approval_reviewer": "-",
                "approval_approver": "-",
                "purpose": "Verify that assemble_report.py writes active_report metadata.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )
    (project / "reports" / "chapters" / "ch01.html").write_text(
        "<section><h2>제1장 테스트</h2><p>조립 후 active_report가 선언되어야 합니다.</p></section>\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "references").mkdir(parents=True, exist_ok=True)
    (project / "references" / "source_link_register.csv").write_text(
        "source_id,file_name,title,url,publisher,accessed_at_kst,url_status,download_status,capture_status,use_level,original_path,capture_path,notes\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "source_index").mkdir(parents=True, exist_ok=True)
    (project / "source_index" / "source_master_index.md").write_text(
        "| source_id | title | status | original_verified | url_or_path |\n|---|---|---|---|---|\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_payload(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout was not JSON:\n{proc.stdout}\n{proc.stderr}") from exc
    if not isinstance(payload, dict):
        raise AssertionError("payload was not a JSON object")
    return payload


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    project = PROJECT_ROOT / SMOKE_PROJECT
    results: list[dict[str, object]] = []
    try:
        write_minimal_project(project, declare_active_report=False)
        missing_proc = run(
            [
                "_ai_system/tools/build_delivery_outbox.py",
                "--project",
                SMOKE_PROJECT,
                "--dry-run",
                "--skip-validation-summary",
                "--require-active-report",
            ]
        )
        missing_payload = parse_payload(missing_proc)
        results.append(
            {
                "case": "missing_active_report_fails",
                "exit_code": missing_proc.returncode,
                "passed": missing_proc.returncode != 0 and "error" in missing_payload,
                "payload": missing_payload,
            }
        )

        write_minimal_project(project, declare_active_report=True)
        active_proc = run(
            [
                "_ai_system/tools/build_delivery_outbox.py",
                "--project",
                SMOKE_PROJECT,
                "--dry-run",
                "--skip-validation-summary",
                "--require-active-report",
            ]
        )
        active_payload = parse_payload(active_proc)
        selection = active_payload.get("selection") if isinstance(active_payload.get("selection"), dict) else {}
        results.append(
            {
                "case": "declared_active_report_passes",
                "exit_code": active_proc.returncode,
                "passed": active_proc.returncode == 0
                and active_payload.get("package_status") == "skipped"
                and selection.get("selected_report") == "reports/internal_review_report.html",
                "payload": active_payload,
            }
        )

        write_assembly_inputs(project)
        assemble_proc = run(["_ai_system/tools/assemble_report.py", "--project", SMOKE_PROJECT])
        assemble_payload = parse_payload(assemble_proc)
        assembled_outbox_proc = run(
            [
                "_ai_system/tools/build_delivery_outbox.py",
                "--project",
                SMOKE_PROJECT,
                "--dry-run",
                "--skip-validation-summary",
                "--require-active-report",
            ]
        )
        assembled_outbox_payload = parse_payload(assembled_outbox_proc)
        assembled_selection = (
            assembled_outbox_payload.get("selection")
            if isinstance(assembled_outbox_payload.get("selection"), dict)
            else {}
        )
        results.append(
            {
                "case": "assembler_declares_active_report",
                "exit_code": assemble_proc.returncode,
                "passed": assemble_proc.returncode == 0
                and assemble_payload.get("active_report") == "reports/internal_review_report.html"
                and assembled_outbox_proc.returncode == 0
                and assembled_selection.get("selected_report") == "reports/internal_review_report.html",
                "payload": {
                    "assemble": assemble_payload,
                    "outbox": assembled_outbox_payload,
                },
            }
        )

        write_minimal_project(project, declare_active_report=True)
        package_proc = run(
            [
                "_ai_system/tools/build_delivery_outbox.py",
                "--project",
                SMOKE_PROJECT,
                "--skip-validation-summary",
                "--require-active-report",
                "--include-status-panels",
            ]
        )
        package_payload = parse_payload(package_proc)
        copied_sources = [
            item.get("source")
            for item in package_payload.get("copied_files", [])
            if isinstance(item, dict)
        ]
        results.append(
            {
                "case": "actual_outbox_generates_requested_core_status_panels",
                "exit_code": package_proc.returncode,
                "passed": package_proc.returncode == 0
                and package_payload.get("status_panel_status") == "pass"
                and "reports/workflow_status/workflow_status.html" in copied_sources
                and "reports/source_status/source_status.html" in copied_sources,
                "payload": package_payload,
            }
        )
    finally:
        remove_smoke_project(project)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
