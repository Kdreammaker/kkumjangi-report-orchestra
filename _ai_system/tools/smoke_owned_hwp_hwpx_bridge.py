from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


TOOL = Path(__file__).with_name("convert_hwp_to_hwpx.py")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], check=False, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )


def payload(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(completed.stdout)


def main() -> int:
    probe = run("--probe")
    with tempfile.TemporaryDirectory(prefix="report-orchestra-owned-hwp-") as temp:
        root = Path(temp)
        source = root / "invalid.hwp"
        output = root / "output.hwpx"
        source.write_bytes(b"not-an-ole-hwp")
        rejected = run(str(source), str(output))
        checks = {
            "embedded_probe_available": probe.returncode == 0 and payload(probe).get("status") == "available",
            "probe_reports_version": payload(probe).get("engine_version") == "0.2.0",
            "embedded_runtime_reported": payload(probe).get("runtime_dependency_mode") == "embedded_system_core",
            "invalid_hwp_rejected": rejected.returncode != 0 and payload(rejected).get("status") == "failed",
            "invalid_input_created_no_output": not output.exists(),
            "public_result_path_free": str(root) not in rejected.stdout,
        }
    result = {
        "schema_version": "report_orchestra_owned_hwp_hwpx_embedded_smoke.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
