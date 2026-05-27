from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_cloud_handoff"


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


def remove_project(project: Path) -> None:
    if not project.exists():
        return
    target = project.resolve()
    root = PROJECT_ROOT.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to remove path outside project root: {target}") from exc
    shutil.rmtree(target)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    project = PROJECT_ROOT / SMOKE_PROJECT
    try:
        remove_project(project)
        outbox = project / "reports" / "outbox" / "smoke"
        (outbox / "reports").mkdir(parents=True, exist_ok=True)
        (outbox / "reports" / "internal_review_report.html").write_text("<html></html>", encoding="utf-8")
        (outbox / "references" / "received_originals").mkdir(parents=True, exist_ok=True)
        (outbox / "references" / "received_originals" / "original.pdf").write_text("original", encoding="utf-8")
        (outbox / "export_manifest.json").write_text("{}", encoding="utf-8")
        proc = run(
            [
                "_ai_system/tools/prepare_cloud_handoff.py",
                "--project",
                SMOKE_PROJECT,
                "--outbox",
                "reports/outbox/smoke",
                "--target",
                "google_drive",
                "--write-plan",
            ]
        )
        payload = json.loads(proc.stdout)
        plan = payload.get("plan_files") if isinstance(payload.get("plan_files"), dict) else {}
        passed = (
            proc.returncode == 0
            and payload.get("status") == "blocked_user_approval_required"
            and payload.get("default_upload_count") == 2
            and payload.get("blocked_count") == 1
            and (project / str(plan.get("html", ""))).exists()
        )
        print(json.dumps({"passed": passed, "exit_code": proc.returncode, "payload": payload}, ensure_ascii=False, indent=2))
        return 0 if passed else 1
    finally:
        remove_project(project)


if __name__ == "__main__":
    raise SystemExit(main())
