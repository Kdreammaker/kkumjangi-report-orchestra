from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


TOOL = Path(__file__).with_name("convert_html_hwpx.py")


FAKE_ENGINE = '''from __future__ import annotations
import json
from pathlib import Path
import sys
if "--version" in sys.argv:
    print("0.2.0")
    raise SystemExit(0)
direction = sys.argv[1]
source = Path(sys.argv[2])
output = Path(sys.argv[3])
if direction == "hwpx-to-html":
    output.write_text('<!doctype html><meta name="hwpx-authoring-contract" content="hwpx-authoring-html.v1">', encoding="utf-8")
else:
    output.write_bytes(b"PK-owned-hwpx")
print(json.dumps({"status": "converted", "source_format": direction.split("-to-")[0], "target_format": direction.split("-to-")[1], "native_package_contract_status": "pass" if direction == "html-to-hwpx" else None}))
'''


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def payload(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(completed.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="report-orchestra-owned-html-hwpx-") as temp:
        root = Path(temp)
        engine = root / "engine.py"
        source_hwpx = root / "source.hwpx"
        authoring_html = root / "authoring.html"
        output_hwpx = root / "output.hwpx"
        engine.write_text(FAKE_ENGINE, encoding="utf-8")
        source_hwpx.write_bytes(b"PK-source")

        missing = run("hwpx-to-html", str(source_hwpx), str(authoring_html))
        probe = run("--engine-cli", str(engine), "--probe")
        to_html = run("hwpx-to-html", str(source_hwpx), str(authoring_html), "--engine-cli", str(engine))
        to_hwpx = run("html-to-hwpx", str(authoring_html), str(output_hwpx), "--engine-cli", str(engine))
        checks = {
            "missing_engine_blocked": missing.returncode == 2 and payload(missing).get("code") == "owned_html_hwpx_engine_not_configured",
            "probe_reports_version": probe.returncode == 0 and payload(probe).get("engine_version") == "0.2.0",
            "hwpx_to_html_passes": to_html.returncode == 0 and payload(to_html).get("status") == "converted",
            "html_to_hwpx_passes": to_hwpx.returncode == 0 and payload(to_hwpx).get("native_package_contract_status") == "pass",
            "outputs_created": authoring_html.is_file() and output_hwpx.is_file(),
            "public_results_path_free": str(root) not in to_html.stdout and str(root) not in to_hwpx.stdout,
            "visual_claim_remains_false": payload(to_html).get("visual_equivalence_claimed") is False and payload(to_hwpx).get("visual_equivalence_claimed") is False,
        }
    result = {
        "schema_version": "report_orchestra_owned_html_hwpx_bridge_smoke.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
