from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


TOOL = Path(__file__).with_name("convert_hwp_to_hwpx.py")


FAKE_ENGINE = '''from __future__ import annotations
import json
from pathlib import Path
import sys
import zipfile
if "--version" in sys.argv:
    print("0.2.0")
    raise SystemExit(0)
source = Path(sys.argv[1])
output = Path(sys.argv[2])
with zipfile.ZipFile(output, "w") as package:
    package.writestr("mimetype", "application/hwp+zip")
    package.writestr("Contents/section0.xml", "<hs:sec xmlns:hs='http://www.hancom.co.kr/hwpml/2011/section'/>")
print(json.dumps({"status": "converted", "engine": {"id": "owned_hwp_hwpx_python", "version": "0.2.0"}}))
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
    with tempfile.TemporaryDirectory(prefix="report-orchestra-owned-hwp-") as temp:
        root = Path(temp)
        engine = root / "engine.py"
        source = root / "source.hwp"
        output = root / "output.hwpx"
        engine.write_text(FAKE_ENGINE, encoding="utf-8")
        source.write_bytes(b"synthetic-hwp-contract-input")

        missing = run(str(source), str(output))
        probe = run("--engine-cli", str(engine), "--probe")
        converted = run(
            str(source),
            str(output),
            "--engine-cli",
            str(engine),
            "--profile",
            "hancom",
        )
        checks = {
            "missing_engine_blocked": missing.returncode == 2 and payload(missing).get("code") == "owned_hwp_hwpx_engine_not_configured",
            "probe_reports_version": probe.returncode == 0 and payload(probe).get("engine_version") == "0.2.0",
            "conversion_passes": converted.returncode == 0 and payload(converted).get("status") == "converted",
            "output_created": output.is_file() and output.stat().st_size > 0,
            "public_result_path_free": str(root) not in converted.stdout,
        }
    result = {
        "schema_version": "report_orchestra_owned_hwp_hwpx_bridge_smoke.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
