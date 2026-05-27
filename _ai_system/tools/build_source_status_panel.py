from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from collections import Counter
from pathlib import Path

from validate_research_integrity import PROJECT_ROOT, parse_markdown_table, source_records_by_id


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def source_index_by_id(project: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in parse_markdown_table(project / "source_index" / "source_master_index.md"):
        source_id = (row.get("source_id") or "").strip()
        if source_id:
            result[source_id] = row
    return result


def classify_link(row: dict[str, str], source_status: str, has_record: bool) -> dict[str, object]:
    use_level = row.get("use_level", "").strip().lower()
    url_status = row.get("url_status", "").strip().lower()
    download_status = row.get("download_status", "").strip().lower()
    capture_status = row.get("capture_status", "").strip().lower()
    has_evidence_path = bool(row.get("original_path", "").strip() or row.get("capture_path", "").strip())
    failed = any(status in {"failed", "blocked"} for status in [url_status, download_status, capture_status])

    warnings: list[str] = []
    action = "추가 조치 없음"
    state = "ok"
    if use_level in {"lead", "not_collected", "collection_blocked", ""}:
        state = "blocked" if failed or use_level == "collection_blocked" else "lead"
        action = "원문 파일, 정확 URL 캡처, 또는 사용자 제공 자료가 필요합니다."
    elif use_level == "url_only":
        state = "needs_capture"
        action = "quote verifier로 URL 본문과 Exact Quotes를 대조하고 캡처를 남겨야 합니다."
    elif use_level in {"quote_verified", "report_citable"} and not has_evidence_path:
        state = "needs_capture"
        action = "quote_verified 상태에는 original_path 또는 capture_path가 필요합니다."
        warnings.append("quote_verified_without_evidence_path")
    elif use_level in {"quote_verified", "report_citable"}:
        state = "quote_verified"
        action = "source record와 claim register의 정확 위치까지 함께 확인하세요."

    if source_status == "report_citable" and not has_record:
        state = "risk"
        action = "report_citable 출처에는 source record가 필요합니다."
        warnings.append("report_citable_without_source_record")
    if source_status == "report_citable" and state in {"blocked", "lead", "needs_capture"}:
        warnings.append("report_citable_but_link_not_ready")

    return {
        "state": state,
        "action": action,
        "warnings": warnings,
        "has_evidence_path": has_evidence_path,
        "failed_or_blocked_status": failed,
    }


def panel_payload(project: Path) -> dict[str, object]:
    link_rows = read_csv_rows(project / "references" / "source_link_register.csv")
    index = source_index_by_id(project)
    records = source_records_by_id(project)
    source_ids = sorted(set(index) | set(records) | {row.get("source_id", "").strip() for row in link_rows if row.get("source_id", "").strip()})

    rows: list[dict[str, object]] = []
    use_counter: Counter[str] = Counter()
    state_counter: Counter[str] = Counter()
    warnings: list[str] = []
    link_by_id = {row.get("source_id", "").strip(): row for row in link_rows if row.get("source_id", "").strip()}

    for source_id in source_ids:
        link = link_by_id.get(source_id, {})
        index_row = index.get(source_id, {})
        source_status = (index_row.get("status") or "").strip()
        has_record = source_id in records
        if link:
            use_counter[(link.get("use_level") or "(blank)").strip().lower()] += 1
            classification = classify_link(link, source_status, has_record)
        else:
            classification = {
                "state": "no_link_row",
                "action": "URL-only 또는 수집 실패 출처라면 source_link_register.csv row가 필요합니다.",
                "warnings": [],
                "has_evidence_path": False,
                "failed_or_blocked_status": False,
            }
        state = str(classification["state"])
        state_counter[state] += 1
        for warning in classification.get("warnings", []):
            warnings.append(f"{source_id}: {warning}")
        rows.append(
            {
                "source_id": source_id,
                "file_name": link.get("file_name", ""),
                "title": link.get("title") or index_row.get("title") or "",
                "source_status": source_status,
                "has_source_record": has_record,
                "url": link.get("url", ""),
                "use_level": link.get("use_level", ""),
                "url_status": link.get("url_status", ""),
                "download_status": link.get("download_status", ""),
                "capture_status": link.get("capture_status", ""),
                "original_path": link.get("original_path", ""),
                "capture_path": link.get("capture_path", ""),
                "state": state,
                "action": classification["action"],
            }
        )

    return {
        "project": project.name,
        "summary": {
            "total_sources_seen": len(source_ids),
            "source_link_rows": len(link_rows),
            "source_records": len(records),
            "source_index_rows": len(index),
            "use_levels": dict(sorted(use_counter.items())),
            "states": dict(sorted(state_counter.items())),
            "warnings": len(warnings),
        },
        "warnings": warnings,
        "rows": rows,
    }


def render_html(payload: dict[str, object]) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value if value is not None else ""), quote=True)

    summary = payload.get("summary", {})
    rows = payload.get("rows", [])
    warnings = payload.get("warnings", [])
    if not isinstance(summary, dict):
        summary = {}
    if not isinstance(rows, list):
        rows = []
    if not isinstance(warnings, list):
        warnings = []

    state_labels = {
        "quote_verified": "인용 검증 근거 있음",
        "needs_capture": "캡처/대조 필요",
        "blocked": "수집 차단",
        "lead": "리드",
        "no_link_row": "링크 row 없음",
        "risk": "위험",
        "ok": "확인",
    }
    row_html = ""
    for item in rows:
        if not isinstance(item, dict):
            continue
        state = str(item.get("state", ""))
        row_html += (
            f"<tr class=\"state-{esc(state)}\">"
            f"<td><strong>{esc(item.get('source_id'))}</strong><br><span>{esc(item.get('file_name') or item.get('title'))}</span></td>"
            f"<td>{esc(state_labels.get(state, state))}</td>"
            f"<td>{esc(item.get('use_level'))}<br><span>{esc(item.get('url_status'))} / {esc(item.get('download_status'))} / {esc(item.get('capture_status'))}</span></td>"
            f"<td>{esc(item.get('source_status'))}<br><span>record: {esc('yes' if item.get('has_source_record') else 'no')}</span></td>"
            f"<td>{esc(item.get('capture_path') or item.get('original_path') or item.get('url'))}</td>"
            f"<td>{esc(item.get('action'))}</td>"
            "</tr>"
        )
    if not row_html:
        row_html = "<tr><td colspan=\"6\">등록된 출처 링크 상태가 없습니다.</td></tr>"

    warning_items = "".join(f"<li>{esc(item)}</li>" for item in warnings) or "<li>없음</li>"
    states = summary.get("states", {})
    if isinstance(states, dict):
        state_tiles = "".join(
            f"<div class=\"tile\"><div class=\"label\">{esc(state_labels.get(str(k), k))}</div><div class=\"value\">{esc(v)}</div></div>"
            for k, v in states.items()
        )
    else:
        state_tiles = ""

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(payload.get("project"))} 출처 상태</title>
  <style>
    body {{ margin:0; font-family:"Malgun Gothic","Noto Sans KR",Arial,sans-serif; color:#111827; background:#fff; line-height:1.65; }}
    main {{ max-width:1160px; margin:32px auto; padding:0 24px 56px; }}
    header {{ border-bottom:3px solid #111827; padding-bottom:18px; margin-bottom:20px; }}
    h1 {{ margin:0 0 8px; font-size:30px; }}
    h2 {{ margin:26px 0 10px; font-size:18px; }}
    .note, span {{ color:#4b5563; font-size:13px; }}
    .summary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; margin:18px 0; }}
    .tile {{ border:1px solid #d1d5db; padding:14px; }}
    .label {{ color:#6b7280; font-size:13px; }}
    .value {{ font-size:24px; font-weight:800; }}
    table {{ width:100%; border-collapse:collapse; border-top:2px solid #111827; }}
    th, td {{ border-bottom:1px solid #e5e7eb; padding:9px 10px; text-align:left; vertical-align:top; font-size:14px; }}
    th {{ background:#f9fafb; }}
    .state-quote_verified td:first-child {{ border-left:4px solid #167A5B; }}
    .state-needs_capture td:first-child, .state-blocked td:first-child, .state-risk td:first-child {{ border-left:4px solid #B8567A; }}
    .state-lead td:first-child, .state-no_link_row td:first-child {{ border-left:4px solid #D97706; }}
    ul {{ margin:8px 0 0 20px; padding:0; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>{esc(payload.get("project"))} 출처 상태</h1>
    <p class="note">이 패널은 source link register, source index, source records를 사람이 읽기 쉽게 합친 보기입니다. 원문 진위나 보고서 closeout을 대체하지 않습니다.</p>
  </header>
  <section class="summary">
    <div class="tile"><div class="label">전체 출처 ID</div><div class="value">{esc(summary.get("total_sources_seen", 0))}</div></div>
    <div class="tile"><div class="label">링크 row</div><div class="value">{esc(summary.get("source_link_rows", 0))}</div></div>
    <div class="tile"><div class="label">source record</div><div class="value">{esc(summary.get("source_records", 0))}</div></div>
    <div class="tile"><div class="label">경고</div><div class="value">{esc(summary.get("warnings", 0))}</div></div>
    {state_tiles}
  </section>
  <h2>주의 항목</h2>
  <ul>{warning_items}</ul>
  <h2>출처별 상태</h2>
  <table>
    <thead><tr><th>출처</th><th>상태</th><th>링크 수집</th><th>보고서 상태</th><th>근거 위치</th><th>다음 조치</th></tr></thead>
    <tbody>{row_html}</tbody>
  </table>
</main>
</body>
</html>
"""


def write_status(project: Path, payload: dict[str, object], output_dir: str) -> dict[str, str]:
    out_dir = project / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "source_status.json"
    html_path = out_dir / "source_status.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_html(payload), encoding="utf-8")
    return {
        "json": json_path.relative_to(project).as_posix(),
        "html": html_path.relative_to(project).as_posix(),
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Build a user-facing source/link status panel for a project.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--write-status", action="store_true")
    parser.add_argument("--status-dir", default="reports/source_status")
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2
    payload = panel_payload(project)
    if args.write_status:
        payload["source_status_written"] = write_status(project, payload, args.status_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
