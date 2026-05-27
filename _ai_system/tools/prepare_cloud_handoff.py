from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
ALLOWED_TARGETS = {"google_drive", "notion", "manual"}
SAFE_EXTENSIONS = {".html", ".json", ".md", ".csv", ".xlsx", ".xls", ".tsv", ".pdf", ".docx"}


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S KST")


def read_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def safe_rel(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def file_rows(project: Path, outbox: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(outbox.rglob("*")):
        if not path.is_file():
            continue
        rel = safe_rel(path, project)
        lower = rel.lower()
        include = path.suffix.lower() in SAFE_EXTENSIONS
        sensitive_reason = ""
        if "received_originals" in lower or "preserved_originals" in lower:
            include = False
            sensitive_reason = "preserved originals require separate explicit approval"
        if any(part in lower for part in [".env", "cookie", "secret", "token"]):
            include = False
            sensitive_reason = "potential secret-like path"
        rows.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "include_by_default": include,
                "reason": "" if include else sensitive_reason or "file type is not in default cloud handoff allowlist",
            }
        )
    return rows


def render_html(payload: dict[str, object]) -> str:
    rows = payload.get("files", [])
    if not isinstance(rows, list):
        rows = []
    table_rows = "\n".join(
        "<tr>"
        f"<td>{str(row.get('path', ''))}</td>"
        f"<td>{'yes' if row.get('include_by_default') else 'no'}</td>"
        f"<td>{str(row.get('reason', ''))}</td>"
        "</tr>"
        for row in rows
        if isinstance(row, dict)
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Cloud Handoff Plan</title>
  <style>
    body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; margin:0; color:#1f2933; background:#fff; }}
    main {{ max-width:1040px; margin:0 auto; padding:40px 28px; }}
    header {{ border-bottom:2px solid #1f2933; margin-bottom:20px; padding-bottom:16px; }}
    h1 {{ margin:0 0 8px; font-size:30px; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th, td {{ border:1px solid #d8dee6; padding:9px 10px; text-align:left; vertical-align:top; }}
    th {{ background:#f6f8fb; }}
    .status {{ color:#8a4b00; font-weight:700; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Cloud Handoff Plan</h1>
    <p>{payload.get('project', '')} · {payload.get('target', '')} · <span class="status">{payload.get('status', '')}</span></p>
  </header>
  <p>클라우드 이동은 보고서 품질 증명이 아니라 공유 편의 기능입니다. 사용자가 명시 승인한 파일만 이동하세요.</p>
  <table>
    <thead><tr><th>File</th><th>Default upload</th><th>Reason</th></tr></thead>
    <tbody>{table_rows}</tbody>
  </table>
</main>
</body>
</html>
"""


def prepare(project_name: str, outbox_rel: str, target: str, approved: bool, write_plan: bool) -> dict[str, object]:
    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"error": f"project not found: {project_name}"}
    if target not in ALLOWED_TARGETS:
        return {"error": f"target must be one of: {', '.join(sorted(ALLOWED_TARGETS))}"}
    outbox = project / outbox_rel
    try:
        outbox.resolve().relative_to(project.resolve())
    except ValueError:
        return {"error": "outbox path must stay inside the project folder"}
    if not outbox.exists() or not outbox.is_dir():
        return {"error": f"outbox directory not found: {outbox_rel}"}
    manifest = read_json(outbox / "export_manifest.json")
    files = file_rows(project, outbox)
    status = "ready_for_manual_upload" if approved else "blocked_user_approval_required"
    payload: dict[str, object] = {
        "project": project_name,
        "generated_at_kst": now_kst(),
        "target": target,
        "outbox": outbox_rel,
        "status": status,
        "approved_by_user": approved,
        "export_manifest_status": "present" if manifest else "missing_or_unreadable",
        "files": files,
        "default_upload_count": sum(1 for row in files if row.get("include_by_default")),
        "blocked_count": sum(1 for row in files if not row.get("include_by_default")),
        "notes": [
            "This tool prepares a cloud handoff plan; it does not upload by itself.",
            "Use Google Drive or Notion connectors only after explicit user approval.",
            "Preserved originals are excluded by default.",
        ],
    }
    if write_plan:
        handoff_dir = outbox / "cloud_handoff"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        json_path = handoff_dir / "cloud_handoff_plan.json"
        html_path = handoff_dir / "cloud_handoff_plan.html"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        html_path.write_text(render_html(payload), encoding="utf-8", newline="\n")
        payload["plan_files"] = {
            "json": safe_rel(json_path, project),
            "html": safe_rel(html_path, project),
        }
    return payload


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Prepare an approval-gated cloud handoff plan for an existing local outbox.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--outbox", required=True, help="Project-relative reports/outbox/<timestamp> directory.")
    parser.add_argument("--target", default="manual", choices=sorted(ALLOWED_TARGETS))
    parser.add_argument("--approved-by-user", action="store_true", help="Record that the user explicitly approved upload planning.")
    parser.add_argument("--write-plan", action="store_true", help="Write cloud_handoff_plan.json/html inside the outbox.")
    args = parser.parse_args()
    payload = prepare(args.project, args.outbox, args.target, args.approved_by_user, args.write_plan)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 2 if "error" in payload else 0


if __name__ == "__main__":
    raise SystemExit(main())
