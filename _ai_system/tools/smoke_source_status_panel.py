from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_source_status_panel"


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


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout was not JSON:\n{proc.stdout}\n{proc.stderr}") from exc
    if not isinstance(payload, dict):
        raise AssertionError("payload was not a JSON object")
    return payload


def remove_project(project: Path) -> None:
    if not project.exists():
        return
    root = PROJECT_ROOT.resolve()
    target = project.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to remove path outside project root: {target}") from exc
    shutil.rmtree(target)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_smoke_project(project: Path) -> None:
    remove_project(project)
    write_text(
        project / "source_index" / "source_master_index.md",
        "| source_id | title | status | original_verified | url_or_path |\n"
        "|---|---|---|---|---|\n"
        "| src_blocked | Blocked source | lead | no | https://example.com/blocked |\n"
        "| src_ready | Ready source | report_citable | yes | https://example.com/ready |\n"
        "| src_missing | Missing link row | report_citable | yes | https://example.com/missing |\n",
    )
    write_text(
        project / "references" / "source_link_register.csv",
        "source_id,file_name,title,official_url,url,publisher,accessed_at_kst,url_status,source_locator,use_level,claim_support_type,needs_user_file,user_file_request_id,notes\n"
        "src_blocked,blocked.pdf,Blocked source,https://example.com/blocked,https://example.com/blocked,Example,2026-05-24 18:00 KST,failed,,collection_blocked,none,yes,req-001,blocked in smoke\n"
        "src_ready,ready.pdf,Ready source,https://example.com/ready,https://example.com/ready,Example,2026-05-24 18:00 KST,200,section 1,quote_verified,direct_quote,no,,ready in smoke\n",
    )
    write_text(
        project / "references" / "source_records" / "src_ready.md",
        "# Source Record\n\n- source_id: src_ready\n- title: Ready source\n\n## 2. Exact Quotes\n\n> Ready quote appears here.\n",
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    project = PROJECT_ROOT / SMOKE_PROJECT
    results: list[dict[str, object]] = []
    try:
        write_smoke_project(project)
        proc = run(["_ai_system/tools/build_source_status_panel.py", "--project", SMOKE_PROJECT, "--write-status"])
        payload = parse_json(proc)
        written = payload.get("source_status_written") if isinstance(payload.get("source_status_written"), dict) else {}
        json_path = project / str(written.get("json", ""))
        html_path = project / str(written.get("html", ""))
        html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        states = summary.get("states") if isinstance(summary.get("states"), dict) else {}
        results.append(
            {
                "case": "source_status_panel_writes_json_and_html",
                "exit_code": proc.returncode,
                "passed": proc.returncode == 0
                and json_path.exists()
                and html_path.exists()
                and states.get("blocked") == 1
                and states.get("quote_verified") == 1
                and states.get("no_link_row") == 1
                and "링크/파일 요청 필요" in html_text
                and "정확 링크, 출처 위치, 사용자 제공 필요 자료" in html_text
                and "캡처/대조 필요" not in html_text,
                "payload": payload,
            }
        )
    finally:
        remove_project(project)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
