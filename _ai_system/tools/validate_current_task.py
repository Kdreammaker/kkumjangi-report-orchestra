from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
ALLOWED_STATUS = {"pending", "active", "done", "blocked", "skipped"}
REQUIRED_COLUMNS = [
    "stage_id",
    "status",
    "user_label",
    "ai_task",
    "read_before_work",
    "required_rules",
    "do_not_read_by_default",
    "completion_criteria",
    "next_stage",
]
REPORT_REGISTRY_FIELDS = [
    "report_id",
    "report_title",
    "document_classification",
    "confidentiality_status",
    "version",
    "stage",
    "owner",
    "practitioners",
    "reviewers",
    "latest_file",
    "prd_path",
    "updated_at_kst",
    "next_action",
    "notes",
]


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_task_table(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    in_table = False
    for line in lines:
        if not line.startswith("|"):
            if in_table and rows:
                break
            continue
        cells = split_row(line)
        if "stage_id" in cells and "status" in cells:
            header = cells
            in_table = True
            continue
        if in_table and re.fullmatch(r"[\s|:-]+", line):
            continue
        if in_table and header:
            if len(cells) < len(header):
                cells.extend([""] * (len(header) - len(cells)))
            rows.append(dict(zip(header, cells, strict=False)))
    return rows


def parse_current_stage(text: str) -> str:
    in_stage = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "## Current Stage":
            in_stage = True
            continue
        if in_stage and line.startswith("## "):
            break
        if in_stage and line.startswith("- `active_stage`:"):
            return line.split(":", 1)[1].strip().strip("`").strip()
    return ""


def read_report_registry(project: Path) -> list[dict[str, str]]:
    path = project / "reports" / "report_registry.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append({field: str(row.get(field, "") or "").strip() for field in REPORT_REGISTRY_FIELDS})
        return rows


def has_assembled_artifact(project: Path) -> bool:
    reports = project / "reports"
    if not reports.exists():
        return False
    for path in reports.glob("*.html"):
        name = path.name.lower()
        if any(skip in name for skip in ["workflow_status", "quality_status", "source_status", "cover_preview"]):
            continue
        return True
    return False


def unexpected_python_helpers(project: Path) -> list[str]:
    allowed_parts = {
        "_ai_system",
        "_internal",
        ".git",
        ".github",
    }
    hits: list[str] = []
    for path in project.rglob("*.py"):
        rel = path.relative_to(project).as_posix()
        first = rel.split("/", 1)[0]
        if first in allowed_parts:
            continue
        if "/archive/" in f"/{rel}/":
            continue
        hits.append(rel)
    return sorted(hits)


def render_status_html(project_name: str, rows: list[dict[str, str]], errors: list[str]) -> str:
    active = [row for row in rows if row.get("status") == "active"]
    current = active[0] if active else {}
    checklist = "\n".join(
        "<tr>"
        f"<td>{html.escape(row.get('stage_id', ''))}</td>"
        f"<td>{html.escape(row.get('status', ''))}</td>"
        f"<td>{html.escape(row.get('user_label', ''))}</td>"
        f"<td>{html.escape(row.get('next_stage', ''))}</td>"
        "</tr>"
        for row in rows
    )
    error_block = ""
    if errors:
        items = "".join(f"<li>{html.escape(error)}</li>" for error in errors)
        error_block = f'<section class="panel warn"><h2>주의</h2><ul>{items}</ul></section>'
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(project_name)} 작업 현황</title>
  <link rel="icon" href="data:,">
  <style>
    body {{ margin:0; font-family:"Malgun Gothic","Noto Sans KR",Arial,sans-serif; background:#F8FAFC; color:#1F2937; line-height:1.7; word-break:keep-all; }}
    main {{ max-width:980px; margin:0 auto; padding:34px 24px 64px; }}
    header {{ border-bottom:3px solid #0F172A; margin-bottom:22px; padding-bottom:18px; }}
    h1 {{ color:#0F172A; font-size:30px; margin:0 0 8px; }}
    h2 {{ color:#0F172A; font-size:20px; margin:26px 0 10px; }}
    .panel {{ background:#fff; border:1px solid #CBD5E1; padding:16px; margin:14px 0; }}
    .active {{ border-left:5px solid #2563EB; }}
    .warn {{ border-left:5px solid #B91C1C; }}
    table {{ width:100%; border-collapse:collapse; background:#fff; border-top:2px solid #0F172A; }}
    th, td {{ border-bottom:1px solid #CBD5E1; padding:9px 10px; text-align:left; vertical-align:top; font-size:14px; }}
    th {{ background:#F1F5F9; color:#0F172A; }}
    code {{ background:#F1F5F9; padding:2px 5px; }}
    a {{ color:#2563EB; font-weight:700; text-decoration:none; }}
  </style>
</head>
<body>
<main>
  <header>
    <p>프로젝트 대시보드는 프로젝트 폴더의 <code>프로젝트_대시보드_실행.vbs</code>로 엽니다.</p>
    <h1>작업 현황판</h1>
    <p>이 파일은 서버 없이 열리는 정적 상태판입니다. AI가 작업 단계를 마친 뒤 갱신해야 합니다.</p>
    <p>갱신 시각: {html.escape(now_kst())}</p>
  </header>
  {error_block}
  <section class="panel active">
    <h2>현재 작업</h2>
    <p><strong>{html.escape(current.get('user_label', 'active 단계 없음'))}</strong> · 상태: <code>{html.escape(current.get('status', 'missing'))}</code></p>
    <p>해야 할 일: {html.escape(current.get('ai_task', ''))}</p>
    <p>먼저 읽을 것: {html.escape(current.get('read_before_work', ''))}</p>
    <p>완료 기준: {html.escape(current.get('completion_criteria', ''))}</p>
  </section>
  <section class="panel">
    <h2>단계 체크리스트</h2>
    <table>
      <thead><tr><th>단계</th><th>상태</th><th>사용자용 이름</th><th>다음 단계</th></tr></thead>
      <tbody>{checklist}</tbody>
    </table>
  </section>
  <section class="panel">
    <h2>AI용 세부 지시</h2>
    <p>상세 읽기 범위, 금지 범위, 완료 기준은 <a href="current_task.md">current_task.md</a>를 확인합니다.</p>
  </section>
</main>
</body>
</html>
"""


def validate(project_name: str, write_status: bool = False) -> dict[str, object]:
    project = PROJECT_ROOT / project_name
    path = project / "tasks" / "current_task.md"
    status_path = project / "tasks" / "task_status.html"
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, str]] = []
    if not project.exists():
        return {"project": project_name, "passed": False, "errors": [f"project not found: {project_name}"]}
    if not path.exists():
        return {"project": project_name, "passed": False, "errors": ["missing tasks/current_task.md"]}
    text = path.read_text(encoding="utf-8", errors="ignore")
    rows = parse_task_table(text)
    declared_active_stage = parse_current_stage(text)
    legacy_agent_first_markers = [
        "Read `AGENTS.md` Fast Router only",
        "AGENTS.md Fast Router; 09 rules",
        "AGENTS.md Fast Router; _ai_system/governance/09_workspace_setup_and_migration_rules.md",
    ]
    if any(marker in text for marker in legacy_agent_first_markers):
        warnings.append(
            "legacy TASK routing text found; existing project work should read tasks/current_task.md first and use AGENTS.md only as a fallback/router"
        )
    if not rows:
        errors.append("stage checklist table not found or empty")
    for column in REQUIRED_COLUMNS:
        if rows and column not in rows[0]:
            errors.append(f"missing task table column: {column}")
    active_rows = [row for row in rows if row.get("status") == "active"]
    if len(active_rows) != 1:
        errors.append(f"expected exactly one active row, found {len(active_rows)}")
    elif declared_active_stage and declared_active_stage != active_rows[0].get("stage_id", ""):
        errors.append(
            f"Current Stage active_stage={declared_active_stage} disagrees with active table row={active_rows[0].get('stage_id', '')}"
        )
    seen_unfinished = False
    for index, row in enumerate(rows, 1):
        status = row.get("status", "")
        if status not in ALLOWED_STATUS:
            errors.append(f"row {index} has invalid status: {status}")
        if status in {"pending", "active", "blocked"}:
            seen_unfinished = True
        elif status in {"done", "skipped"} and seen_unfinished:
            errors.append(f"row {index} ({row.get('stage_id', '')}) is {status} after an unfinished earlier stage")
        for column in ["stage_id", "ai_task", "read_before_work", "required_rules", "completion_criteria", "next_stage"]:
            if not row.get(column, "").strip():
                errors.append(f"row {index} missing {column}")
        if status == "active" and row.get("stage_id") != "setup" and "AGENTS.md" in row.get("read_before_work", ""):
            warnings.append(
                f"row {index} active non-setup task lists AGENTS.md in Read Before Work; prefer tasks/current_task.md plus task-specific rules"
            )
    row_by_stage = {row.get("stage_id", ""): row for row in rows}
    if row_by_stage.get("style", {}).get("status") == "skipped" and row_by_stage.get("assembly", {}).get("status") in {"done", "active"}:
        warnings.append("style stage is skipped while assembly is active/done; prefer a no-change style pass artifact over skipping")
    if (project / "tasks" / "task.md").exists():
        warnings.append("tasks/task.md exists; tasks/current_task.md must remain the task authority")
    if has_assembled_artifact(project) and not read_report_registry(project):
        warnings.append("assembled artifact exists but reports/report_registry.csv has no rows")
    helper_hits = unexpected_python_helpers(project)
    if helper_hits:
        warnings.append("unexpected project-local Python helper files: " + ", ".join(helper_hits[:8]))
    if not status_path.exists():
        warnings.append("missing tasks/task_status.html; run with --write-status to create it")
    if write_status:
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(render_status_html(project_name, rows, errors), encoding="utf-8", newline="\n")
        warnings = [warning for warning in warnings if not warning.startswith("missing tasks/task_status.html")]
    return {
        "project": project_name,
        "generated_at_kst": now_kst(),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "rows": len(rows),
        "active_stage": active_rows[0].get("stage_id") if active_rows else "",
        "status_html": "tasks/task_status.html" if status_path.exists() or write_status else "",
        "notes": [
            "This validates the AI task manifest structure.",
            "It does not validate report content truth, analysis depth, or external sharing readiness.",
        ],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate project tasks/current_task.md and optionally refresh task_status.html.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--write-status", action="store_true", help="Regenerate tasks/task_status.html from current_task.md")
    args = parser.parse_args()
    payload = validate(args.project, args.write_status)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
