from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import tempfile

from export_report_hwpx import export_hwpx


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="report-orchestra-native-hwpx-") as temp:
        project = Path(temp) / "smoke_project"
        chapters = project / "reports" / "chapters"
        figures = project / "reports" / "assets" / "figures"
        chapters.mkdir(parents=True)
        figures.mkdir(parents=True)
        cover = project / "reports" / "cover.data.json"
        cover.write_text(json.dumps({
            "report_title": "Native HWPX smoke",
            "subtitle": "Report Export IR verification",
            "version": "v0.1",
        }, ensure_ascii=False), encoding="utf-8")
        (figures / "pixel.png").write_bytes(PNG_1X1)
        (chapters / "ch01.html").write_text('''<section class="report-chapter" data-chapter-id="ch01">
<h1 style="font-size:20pt;font-weight:700">검증 장</h1><p>텍스트 보존 검증</p>
<ul><li>목록 항목</li></ul>
<table style="width:100%"><tr><th>항목</th><th>상태</th></tr><tr><td>HWPX</td><td>검증</td></tr></table>
<figure><img src="assets/figures/pixel.png" alt="pixel"><figcaption>그림 검증</figcaption></figure>
</section>''', encoding="utf-8")
        output_a = project / "reports" / "a.hwpx"
        output_b = project / "reports" / "b.hwpx"
        receipt_a = export_hwpx(project, cover, output_a)
        receipt_b = export_hwpx(project, cover, output_b)
        semantic = receipt_a.get("semantic_roundtrip", {})
        checks = {
            "first_export_created": output_a.is_file() and receipt_a.get("status") == "structure_checked",
            "second_export_created": output_b.is_file() and receipt_b.get("status") == "structure_checked",
            "deterministic_output": digest(output_a) == digest(output_b),
            "native_contract_pass": receipt_a.get("native_package_contract_status") == "pass",
            "semantic_roundtrip_pass": semantic.get("status") == "pass" and all(semantic.get("checks", {}).values()),
            "visual_claim_false": receipt_a.get("visual_equivalence_claimed") is False,
            "normalization_warning_free": not receipt_a.get("normalization_warnings"),
        }
    payload = {
        "schema_version": "report_orchestra_native_hwpx_export_smoke.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
