from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="report_factory_config_smoke_") as tmp:
        tmp_path = Path(tmp)
        config = tmp_path / "workspace_config.json"
        shutil.copy2(ROOT / "_ai_system" / "workspace_config.json", config)

        list_proc = run(["_ai_system/tools/configure_workspace.py", "--config", str(config), "--list-domains"])
        dry_proc = run(["_ai_system/tools/configure_workspace.py", "--config", str(config), "--domain", "business_strategy", "--dry-run"])
        data_after_dry = json.loads(config.read_text(encoding="utf-8"))
        write_proc = run(["_ai_system/tools/configure_workspace.py", "--config", str(config), "--domain", "regulatory_review"])
        data_after_write = json.loads(config.read_text(encoding="utf-8"))
        bad_proc = run(["_ai_system/tools/configure_workspace.py", "--config", str(config), "--domain", "missing_domain"])

        checks = [
            {
                "name": "list_domains",
                "passed": list_proc.returncode == 0 and "business_strategy" in list_proc.stdout,
                "exit_code": list_proc.returncode,
            },
            {
                "name": "dry_run_does_not_write",
                "passed": dry_proc.returncode == 0 and data_after_dry.get("preset_domain") != "business_strategy",
                "exit_code": dry_proc.returncode,
            },
            {
                "name": "known_domain_writes",
                "passed": write_proc.returncode == 0 and data_after_write.get("preset_domain") == "regulatory_review",
                "exit_code": write_proc.returncode,
            },
            {
                "name": "unknown_domain_fails",
                "passed": bad_proc.returncode == 2,
                "exit_code": bad_proc.returncode,
            },
        ]
    failures = [check for check in checks if not check["passed"]]
    print(json.dumps({"passed": not failures, "checks": checks}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

