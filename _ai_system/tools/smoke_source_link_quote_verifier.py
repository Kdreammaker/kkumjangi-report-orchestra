from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_source_link_quote_verifier"
QUOTE = "This exact official document contains a quote for URL validation."


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


def write_project(project: Path, url: str, quote: str) -> None:
    remove_project(project)
    write_text(
        project / "source_index" / "source_master_index.md",
        "| source_id | title | status | original_verified | url_or_path |\n"
        "|---|---|---|---|---|\n"
        f"| src_url | Exact official document | report_citable | yes | {url} |\n",
    )
    record_body = (
        "# Source Record\n\n"
        "- source_id: src_url\n"
        "- title: Exact official document\n"
        "- publisher: Example\n"
        "- evidence_class: original_official\n"
        "- source_readiness_status: report_citable\n"
        "- original_verified: yes\n"
        f"- url_or_path: {url}\n"
        "- exact_quote_location: exact URL section\n\n"
        "## 2. Exact Quotes\n\n"
        f"> {quote}\n\n"
        "## 3. Notes\n\n"
        "This long record is intentionally over one kilobyte so the integrity checker can audit it. "
        * 20
    )
    write_text(project / "references" / "source_records" / "src_url.md", record_body)
    write_text(
        project / "references" / "source_link_register.csv",
        "source_id,file_name,title,url,publisher,accessed_at_kst,url_status,download_status,capture_status,use_level,original_path,capture_path,notes\n"
        f"src_url,exact-document.html,Exact official document,{url},Example,2026-05-24 18:00 KST,200,not_attempted,not_attempted,url_only,,,\n",
    )
    write_text(project / "reports" / "report_claim_register.md", "| claim_id | source_ids | status |\n|---|---|---|\n")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    project = PROJECT_ROOT / SMOKE_PROJECT
    webroot = Path.cwd() / "00_사용자_작업공간" / "_smoke_http_source"
    results: list[dict[str, object]] = []
    server: ThreadingHTTPServer | None = None
    try:
        if webroot.exists():
            shutil.rmtree(webroot)
        write_text(webroot / "exact-document.txt", f"Official page text. {QUOTE} End of page.")

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(webroot), **kwargs)

            def log_message(self, format: str, *args) -> None:  # noqa: A002
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/exact-document.txt"
        write_project(project, url, QUOTE)

        verifier_proc = run(
            [
                "_ai_system/tools/verify_source_link_quotes.py",
                "--project",
                SMOKE_PROJECT,
                "--write-capture",
                "--update-register",
            ]
        )
        verifier_payload = parse_json(verifier_proc)
        capture_paths = [
            str(item.get("capture_path", ""))
            for item in verifier_payload.get("results", [])
            if isinstance(item, dict)
        ]
        results.append(
            {
                "case": "url_quote_verifier_fetches_and_captures_matching_quote",
                "exit_code": verifier_proc.returncode,
                "passed": verifier_proc.returncode == 0 and any(capture_paths),
                "payload": verifier_payload,
            }
        )

        integrity_proc = run(["_ai_system/tools/validate_research_integrity.py", "--project", SMOKE_PROJECT])
        integrity_payload = parse_json(integrity_proc)
        results.append(
            {
                "case": "captured_link_register_evidence_satisfies_research_integrity",
                "exit_code": integrity_proc.returncode,
                "passed": integrity_proc.returncode == 0,
                "payload": integrity_payload,
            }
        )

        write_project(project, url, "This quote is not present in the fetched page.")
        missing_proc = run(["_ai_system/tools/verify_source_link_quotes.py", "--project", SMOKE_PROJECT])
        missing_payload = parse_json(missing_proc)
        results.append(
            {
                "case": "url_quote_verifier_rejects_missing_quote",
                "exit_code": missing_proc.returncode,
                "passed": missing_proc.returncode != 0
                and any("Exact Quotes not found" in error for error in missing_payload.get("errors", [])),
                "payload": missing_payload,
            }
        )

        write_project(project, url, "법령")
        weak_proc = run(["_ai_system/tools/verify_source_link_quotes.py", "--project", SMOKE_PROJECT])
        weak_payload = parse_json(weak_proc)
        results.append(
            {
                "case": "url_quote_verifier_rejects_weak_generic_quote",
                "exit_code": weak_proc.returncode,
                "passed": weak_proc.returncode != 0
                and any("weak/generic" in error for error in weak_payload.get("errors", [])),
                "payload": weak_payload,
            }
        )
    finally:
        if server:
            server.shutdown()
            server.server_close()
        remove_project(project)
        if webroot.exists():
            shutil.rmtree(webroot)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
