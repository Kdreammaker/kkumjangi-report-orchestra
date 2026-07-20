from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


TOOL = Path(__file__).with_name("convert_html_hwpx.py")
AUTHORING_HTML = '''<!doctype html><html><head><meta charset="utf-8"><title>Smoke</title></head>
<body data-hwpx-contract="hwpx-authoring-html.v1" data-hwpx-document-ref="smoke">
<section data-hwpx-section-ref="section-1"><h1 data-hwpx-block-ref="heading-1" style="font-size:18pt;font-weight:700">검증 문서</h1>
<p data-hwpx-block-ref="paragraph-1" style="font-size:10pt;line-height:160%">내장 엔진 왕복 변환 검증</p></section>
</body></html>'''


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], check=False, capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )


def payload(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(completed.stdout)


def main() -> int:
    probe = run("--probe")
    with tempfile.TemporaryDirectory(prefix="report-orchestra-owned-html-hwpx-") as temp:
        root = Path(temp)
        authoring_html = root / "authoring.html"
        output_hwpx = root / "output.hwpx"
        roundtrip_html = root / "roundtrip.html"
        authoring_html.write_text(AUTHORING_HTML, encoding="utf-8")
        to_hwpx = run("html-to-hwpx", str(authoring_html), str(output_hwpx))
        to_html = run("hwpx-to-html", str(output_hwpx), str(roundtrip_html))
        checks = {
            "embedded_probe_available": probe.returncode == 0 and payload(probe).get("status") == "available",
            "probe_reports_version": payload(probe).get("engine_version") == "0.2.0",
            "html_to_hwpx_passes": to_hwpx.returncode == 0 and payload(to_hwpx).get("native_package_contract_status") == "pass",
            "hwpx_to_html_passes": to_html.returncode == 0 and payload(to_html).get("status") == "converted",
            "outputs_created": output_hwpx.is_file() and roundtrip_html.is_file(),
            "roundtrip_contract_present": "hwpx-authoring-html.v1" in roundtrip_html.read_text(encoding="utf-8"),
            "public_results_path_free": str(root) not in to_html.stdout and str(root) not in to_hwpx.stdout,
            "visual_claim_remains_false": payload(to_html).get("visual_equivalence_claimed") is False and payload(to_hwpx).get("visual_equivalence_claimed") is False,
        }
    result = {
        "schema_version": "report_orchestra_owned_html_hwpx_embedded_smoke.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
