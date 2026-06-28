from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_source_link_register"


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


def write_url_only_project(project: Path) -> None:
    remove_project(project)
    write_text(
        project / "source_index" / "source_master_index.md",
        "| source_id | title | status | original_verified | url_or_path |\n"
        "|---|---|---|---|---|\n"
        "| src_url | Exact official document | report_citable | yes | https://example.com/reports/exact-document.pdf |\n",
    )
    record_body = (
        "# Source Record\n\n"
        "- source_id: src_url\n"
        "- title: Exact official document\n"
        "- publisher: Example\n"
        "- evidence_class: original_official\n"
        "- source_readiness_status: report_citable\n"
        "- original_verified: yes\n"
        "- url_or_path: https://example.com/reports/exact-document.pdf\n"
        "- exact_quote_location: exact URL section\n\n"
        "## 2. Exact Quotes\n\n"
        "> This exact official document contains a quote for URL validation.\n\n"
        "## 3. Notes\n\n"
        "This long record is intentionally over one kilobyte so the integrity checker can audit it. "
        * 20
    )
    write_text(project / "references" / "source_records" / "src_url.md", record_body)
    write_text(project / "reports" / "report_claim_register.md", "| claim_id | source_ids | status |\n|---|---|---|\n")


def write_capture(project: Path) -> None:
    write_text(
        project / "evidence" / "web_captures" / "src_url_capture.txt",
        "url: https://example.com/reports/exact-document.pdf\n"
        "accessed_at_kst: 2026-05-24 18:00 KST\n\n"
        "This exact official document contains a quote for URL validation.\n",
    )


def result_errors(payload: dict[str, object]) -> list[str]:
    collected: list[str] = []
    value = payload.get("errors")
    if isinstance(value, list):
        collected.extend(str(item) for item in value)
    results = payload.get("results")
    if isinstance(results, list):
        for result in results:
            if isinstance(result, dict) and isinstance(result.get("errors"), list):
                collected.extend(str(item) for item in result["errors"])
    return collected


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    project = PROJECT_ROOT / SMOKE_PROJECT
    results: list[dict[str, object]] = []
    try:
        write_url_only_project(project)
        no_link_proc = run(["_ai_system/tools/validate_research_integrity.py", "--project", SMOKE_PROJECT])
        no_link_payload = parse_json(no_link_proc)
        results.append(
            {
                "case": "report_citable_url_source_requires_link_register_row",
                "exit_code": no_link_proc.returncode,
                "passed": no_link_proc.returncode != 0
                and any("requires references/source_link_register.csv row" in error for error in result_errors(no_link_payload)),
                "payload": no_link_payload,
            }
        )

        blocked_proc = run(
            [
                "_ai_system/tools/record_source_link.py",
                "--project",
                SMOKE_PROJECT,
                "--source-id",
                "src_url",
                "--official-url",
                "https://example.com/reports/exact-document.pdf",
                "--title",
                "Exact official document",
                "--url-status",
                "failed",
                "--use-level",
                "collection_blocked",
                "--notes",
                "source stayed blocked in smoke",
            ]
        )
        blocked_payload = parse_json(blocked_proc)
        blocked_check_proc = run(["_ai_system/tools/validate_research_integrity.py", "--project", SMOKE_PROJECT])
        blocked_check_payload = parse_json(blocked_check_proc)
        results.append(
            {
                "case": "collection_blocked_link_does_not_allow_report_citable",
                "exit_code": blocked_check_proc.returncode,
                "passed": blocked_proc.returncode == 0
                and blocked_check_proc.returncode != 0
                and any("does not allow report_citable use" in error for error in result_errors(blocked_check_payload)),
                "payload": {"record": blocked_payload, "check": blocked_check_payload},
            }
        )

        verified_link_first_proc = run(
            [
                "_ai_system/tools/record_source_link.py",
                "--project",
                SMOKE_PROJECT,
                "--source-id",
                "src_url",
                "--official-url",
                "https://example.com/reports/exact-document.pdf",
                "--title",
                "Exact official document",
                "--url-status",
                "exact_url_verified",
                "--source-locator",
                "exact URL section",
                "--use-level",
                "quote_verified",
                "--claim-support-type",
                "direct_quote",
                "--notes",
                "exact URL and locator verified without AI download in smoke",
            ]
        )
        verified_link_first_payload = parse_json(verified_link_first_proc)
        verified_link_first_check_proc = run(["_ai_system/tools/validate_research_integrity.py", "--project", SMOKE_PROJECT])
        verified_link_first_check_payload = parse_json(verified_link_first_check_proc)
        results.append(
            {
                "case": "quote_verified_url_without_capture_passes_with_exact_link_and_locator",
                "exit_code": verified_link_first_check_proc.returncode,
                "passed": verified_link_first_proc.returncode == 0
                and verified_link_first_check_proc.returncode == 0,
                "payload": {"record": verified_link_first_payload, "check": verified_link_first_check_payload},
            }
        )

        missing_locator_proc = run(
            [
                "_ai_system/tools/record_source_link.py",
                "--project",
                SMOKE_PROJECT,
                "--source-id",
                "src_url",
                "--official-url",
                "https://example.com/reports/exact-document.pdf",
                "--title",
                "Exact official document",
                "--url-status",
                "exact_url_verified",
                "--use-level",
                "quote_verified",
                "--notes",
                "locator intentionally removed in smoke",
            ]
        )
        missing_locator_payload = parse_json(missing_locator_proc)
        missing_locator_check_proc = run(["_ai_system/tools/validate_research_integrity.py", "--project", SMOKE_PROJECT])
        missing_locator_check_payload = parse_json(missing_locator_check_proc)
        results.append(
            {
                "case": "quote_verified_url_requires_locator",
                "exit_code": missing_locator_check_proc.returncode,
                "passed": missing_locator_proc.returncode == 0
                and missing_locator_check_proc.returncode != 0
                and any("requires source_locator" in error for error in result_errors(missing_locator_check_payload)),
                "payload": {"record": missing_locator_payload, "check": missing_locator_check_payload},
            }
        )
    finally:
        remove_project(project)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
