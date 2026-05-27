from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_reference_register_consistency"


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


def write_registers(project: Path, *, inventory: bool, pending_quote: bool = False, missing_capture: bool = False) -> None:
    quote_note = "Quote verification pending\n" if pending_quote else "검증된 원문 인용 문구입니다.\n"
    write_text(
        project / "source_index" / "source_master_index.md",
        "| source_id | status | used_in | url_or_path |\n"
        "|---|---|---|---|\n"
        "| src_001 | report_citable | reports/test.html | https://example.com/source/1 |\n",
    )
    write_text(
        project / "references" / "source_records" / "src_001.md",
        "# Source Record\n\n"
        "- source_id: src_001\n"
        "- title: Official source\n"
        "- url_or_path: https://example.com/source/1\n"
        "- capture_path: evidence/web_captures/src_001.html\n\n"
        "## 2. Exact Quotes\n\n"
        f"> {quote_note}\n",
    )
    if not missing_capture:
        write_text(project / "evidence" / "web_captures" / "src_001.html", "<html><body>검증된 원문 인용 문구입니다.</body></html>\n")
    write_text(
        project / "references" / "source_link_register.csv",
        "source_id,title,url,publisher,accessed_at_kst,url_status,download_status,capture_status,use_level,original_path,capture_path,notes\n"
        "src_001,Official source,https://example.com/source/1,Example,2026-05-25T00:00:00+09:00,ok,not_attempted,captured,report_citable,,evidence/web_captures/src_001.html,\n",
    )
    if inventory:
        write_text(
            project / "references" / "reference_inventory.csv",
            "reference_id,listed_at_kst,title,file_type,original_path,sha256,file_size_bytes,source_id,source_record_path,notes\n"
            "ref_001,2026-05-25T00:00:00+09:00,Official source,html,evidence/web_captures/src_001.html,aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,128,src_001,references/source_records/src_001.md,\n",
        )
    else:
        write_text(
            project / "references" / "reference_inventory.csv",
            "reference_id,listed_at_kst,title,file_type,original_path,sha256,file_size_bytes,source_id,source_record_path,notes\n",
        )


def result_errors(payload: dict[str, object]) -> list[str]:
    errors = payload.get("errors", [])
    return [str(error) for error in errors] if isinstance(errors, list) else []


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    project = PROJECT_ROOT / SMOKE_PROJECT
    results: list[dict[str, object]] = []
    try:
        remove_project(project)
        write_registers(project, inventory=False)
        missing_inventory_proc = run(["_ai_system/tools/validate_reference_register_consistency.py", "--project", SMOKE_PROJECT])
        missing_inventory_payload = parse_json(missing_inventory_proc)
        results.append(
            {
                "case": "source_records_without_reference_inventory_are_blocked",
                "exit_code": missing_inventory_proc.returncode,
                "passed": missing_inventory_proc.returncode != 0
                and any("reference_inventory.csv" in error for error in result_errors(missing_inventory_payload)),
                "payload": missing_inventory_payload,
            }
        )

        remove_project(project)
        write_registers(project, inventory=True, pending_quote=True)
        pending_quote_proc = run(["_ai_system/tools/validate_reference_register_consistency.py", "--project", SMOKE_PROJECT])
        pending_quote_payload = parse_json(pending_quote_proc)
        results.append(
            {
                "case": "report_used_pending_quote_marker_is_blocked",
                "exit_code": pending_quote_proc.returncode,
                "passed": pending_quote_proc.returncode != 0
                and any("quote verification pending" in error.lower() for error in result_errors(pending_quote_payload)),
                "payload": pending_quote_payload,
            }
        )

        remove_project(project)
        write_registers(project, inventory=True)
        pass_proc = run(["_ai_system/tools/validate_reference_register_consistency.py", "--project", SMOKE_PROJECT])
        pass_payload = parse_json(pass_proc)
        results.append(
            {
                "case": "complete_registers_pass",
                "exit_code": pass_proc.returncode,
                "passed": pass_proc.returncode == 0 and pass_payload.get("passed") is True,
                "payload": pass_payload,
            }
        )
    finally:
        remove_project(project)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
