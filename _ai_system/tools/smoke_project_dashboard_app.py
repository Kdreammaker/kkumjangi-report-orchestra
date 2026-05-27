from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")


def request_json(url: str, payload: object | None = None) -> dict[str, object]:
    if payload is None:
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=2.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_for(url: str) -> None:
    last = ""
    for _ in range(40):
        try:
            request_json(url)
            return
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            time.sleep(0.1)
    raise RuntimeError(last)


def main() -> int:
    source_dir = Path(__file__).resolve().parent
    results: dict[str, object] = {"checks": []}
    with tempfile.TemporaryDirectory(prefix="report_factory_dashboard_app_") as tmp:
        root = Path(tmp)
        (root / "_ai_system" / "tools").mkdir(parents=True)
        (root / PROJECT_ROOT).mkdir(parents=True)
        (root / "AGENTS.md").write_text("# Test Router\n", encoding="utf-8")
        shutil.copy2(source_dir / "init_project_workspace.py", root / "_ai_system" / "tools" / "init_project_workspace.py")
        shutil.copy2(source_dir / "intake_reference_batch.py", root / "_ai_system" / "tools" / "intake_reference_batch.py")
        shutil.copy2(source_dir / "build_project_context_db.py", root / "_ai_system" / "tools" / "build_project_context_db.py")
        shutil.copytree(source_dir / "project_dashboard_app", root / "_ai_system" / "tools" / "project_dashboard_app")

        slug = "smoke_dashboard_project"
        init = subprocess.run([sys.executable, "_ai_system/tools/init_project_workspace.py", slug], cwd=root, text=True, capture_output=True, check=False)
        project_dirs = sorted(p for p in (root / PROJECT_ROOT).iterdir() if p.is_dir())
        project = project_dirs[0] if project_dirs else root / PROJECT_ROOT / "missing"
        (project / "reports" / "internal_review_report.html").write_text("<!doctype html><html><body>report</body></html>", encoding="utf-8")
        app = root / "_ai_system" / "tools" / "project_dashboard_app" / "app.py"
        env = os.environ.copy()
        env["PROJECT_DASHBOARD_DISABLE_OPEN"] = "1"
        proc = subprocess.Popen(
            [
                sys.executable,
                str(app),
                "--project",
                str(project),
                "--port",
                "8897",
                "--idle-timeout-seconds",
                "60",
                "--shutdown-grace-seconds",
                "1",
                "--no-browser",
            ],
            cwd=root,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for("http://127.0.0.1:8897/api/heartbeat")
            profile = request_json("http://127.0.0.1:8897/api/profile")
            responsible = profile.get("responsible_people")
            if isinstance(responsible, list) and responsible and isinstance(responsible[0], dict):
                responsible[0]["name"] = "홍길동"
                responsible[0]["title"] = "팀장"
            practitioners = profile.get("practitioners")
            if isinstance(practitioners, list) and practitioners and isinstance(practitioners[0], dict):
                practitioners[0]["name"] = "김실무"
                practitioners[0]["title"] = "매니저"
            save_profile = request_json("http://127.0.0.1:8897/api/profile", profile)
            registry_payload = {
                "rows": [
                    {
                        "report_id": "RPT-001",
                        "report_title": "내부 검토용 보고서",
                        "document_classification": "내부 검토용",
                        "confidentiality_status": "대외비",
                        "version": "v0.1",
                        "stage": "기획",
                        "owner": "홍길동",
                        "latest_file": "reports/internal_review_report.html",
                    }
                ]
            }
            save_registry = request_json("http://127.0.0.1:8897/api/report-registry", registry_payload)
            report_open = request_json("http://127.0.0.1:8897/api/open-report", {"path": "reports/internal_review_report.html"})
            loaded_registry = request_json("http://127.0.0.1:8897/api/report-registry")
            references_payload = {
                "rows": [
                    {
                        "reference_id": "REF-001",
                        "title": "테스트 문서",
                        "file_type": "url",
                        "material_origin_ko": "사용자 제공",
                        "visibility_ko": "내부",
                        "source_tier": "primary",
                        "intake_status": "manual_lead",
                        "parse_status": "not_applicable",
                        "original_path": "https://example.com",
                    }
                ]
            }
            save_references = request_json("http://127.0.0.1:8897/api/references", references_payload)
            loaded_references = request_json("http://127.0.0.1:8897/api/references")
            (project / "01_자료_넣는_곳" / "smoke_material.txt").write_text("dashboard scan smoke\n", encoding="utf-8")
            scan_result = request_json("http://127.0.0.1:8897/api/scan-materials", {})
            loaded_after_scan = request_json("http://127.0.0.1:8897/api/references")
            normalization_start = request_json("http://127.0.0.1:8897/api/reference-normalization", {})
            normalization_status: dict[str, object] = {}
            for _ in range(30):
                normalization_status = request_json("http://127.0.0.1:8897/api/reference-normalization-status")
                if not normalization_status.get("running"):
                    break
                time.sleep(0.2)
            changes = request_json("http://127.0.0.1:8897/api/changes")
            heartbeat = request_json("http://127.0.0.1:8897/api/heartbeat")
            shutdown = request_json("http://127.0.0.1:8897/api/shutdown", {"reason": "smoke_test"})
            change_rows = changes.get("rows", [])
            if not isinstance(change_rows, list):
                change_rows = []
            results["checks"].append(
                {
                    "name": "project_dashboard_app_read_write",
                    "init_returncode": init.returncode,
                    "profile_saved": save_profile.get("path") == "project_profile.json",
                    "registry_saved": save_registry.get("path") == "reports/report_registry.csv",
                    "report_opened": report_open.get("ok") == "true",
                    "references_saved": save_references.get("path") == "references/reference_inventory.csv",
                    "registry_count": len(loaded_registry.get("rows", [])) if isinstance(loaded_registry.get("rows"), list) else -1,
                    "reference_count": int(loaded_references.get("count", -1)),
                    "scan_added": scan_result.get("added") == 1,
                    "reference_count_after_scan": int(loaded_after_scan.get("count", -1)),
                    "normalization_started": normalization_start.get("status") in {"running", "done", "partial"},
                    "normalization_finished": normalization_status.get("running") is False,
                    "normalization_log_exists": bool(normalization_status.get("log_path"))
                    and (project / str(normalization_status.get("log_path"))).exists(),
                    "context_index_exists": (project / "project_state" / "context_index.duckdb").exists(),
                    "context_index_manifest_exists": (project / "project_state" / "context_index_manifest.json").exists(),
                    "change_log_count": len(change_rows),
                    "heartbeat_ok": heartbeat.get("ok") is True,
                    "shutdown_ok": shutdown.get("shutting_down") is True,
                    "profile_file_contains_owner": "홍길동" in (project / "project_profile.json").read_text(encoding="utf-8"),
                    "registry_file_contains_report": "RPT-001" in (project / "reports" / "report_registry.csv").read_text(encoding="utf-8-sig"),
                    "inventory_file_contains_reference": "REF-001" in (project / "references" / "reference_inventory.csv").read_text(encoding="utf-8-sig"),
                    "inventory_file_contains_scanned_material": "smoke_material" in (project / "references" / "reference_inventory.csv").read_text(encoding="utf-8-sig"),
                    "jsonl_log_exists": (project / "project_state" / "dashboard_change_log.jsonl").exists(),
                    "csv_log_exists": (project / "worklogs" / "dashboard_change_log.csv").exists(),
                    "local_device_id_exists": (root / ".local_state" / "device_identity.json").exists(),
                }
            )
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

    failures = [
        item
        for item in results["checks"]
        if not (
            item["init_returncode"] == 0
            and item["profile_saved"]
            and item["registry_saved"]
            and item["report_opened"]
            and item["references_saved"]
            and item["registry_count"] == 1
            and item["reference_count"] == 1
            and item["scan_added"]
            and item["reference_count_after_scan"] == 2
            and item["normalization_started"]
            and item["normalization_finished"]
            and item["normalization_log_exists"]
            and item["context_index_exists"]
            and item["context_index_manifest_exists"]
            and item["change_log_count"] >= 3
            and item["heartbeat_ok"]
            and item["shutdown_ok"]
            and item["profile_file_contains_owner"]
            and item["registry_file_contains_report"]
            and item["inventory_file_contains_reference"]
            and item["inventory_file_contains_scanned_material"]
            and item["jsonl_log_exists"]
            and item["csv_log_exists"]
            and item["local_device_id_exists"]
        )
    ]
    results["failures"] = failures
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
