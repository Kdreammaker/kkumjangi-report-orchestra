from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ROOT / "00_사용자_작업공간"
ENGINE_ROOT = ROOT / "_ai_system" / "engines" / "owned_hwp_hwpx"
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from owned_hwp_hwpx import (  # noqa: E402
    ENGINE_ID,
    ENGINE_VERSION,
    build_hwpx_writer_model_from_document_ir,
    parse_authoring_html_document_ir,
    read_hwpx_document_ir,
    summarize_document_ir,
    validate_document_ir,
    validate_generated_hwpx,
    validate_hwpx_native_package_contract,
    write_hwpx_package,
)
from report_export_ir import (  # noqa: E402
    build_report_export_ir,
    render_hwpx_authoring_html,
    summarize_report_export_ir,
)


DEFAULT_OUTPUT = Path("reports") / "internal_review_report.hwpx"
CRITICAL_COMPONENTS = (
    "package", "core", "controls", "header_compatibility", "inline_controls",
    "compose_controls", "page_hiding_controls", "footnote_controls",
    "paragraph_render", "drawing_namespaces", "binaries", "runs", "text",
)


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def export_hwpx(
    project: Path,
    cover_data_path: Path,
    output_path: Path,
    *,
    emit_ir_path: Path | None = None,
) -> dict[str, Any]:
    report_ir = build_report_export_ir(project, cover_data_path)
    authoring_html = render_hwpx_authoring_html(report_ir, project)
    document_ir = parse_authoring_html_document_ir(authoring_html)
    ir_validation = validate_document_ir(document_ir)
    if ir_validation.get("status") != "pass":
        raise ValueError(f"owned document IR validation failed: {ir_validation.get('errors', [])}")

    model = build_hwpx_writer_model_from_document_ir(document_ir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(prefix="report-orchestra-", suffix=".hwpx", dir=output_path.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        write_hwpx_package(temporary, model)
        native_contract = validate_hwpx_native_package_contract(temporary)
        package_validation = validate_generated_hwpx(model, temporary)
        statuses = package_validation.get("component_statuses", {})
        critical_pass = all(statuses.get(name) == "pass" for name in CRITICAL_COMPONENTS)
        roundtrip_ir = read_hwpx_document_ir(temporary)
        roundtrip_validation = validate_document_ir(roundtrip_ir)
        source_summary = summarize_document_ir(document_ir)
        roundtrip_summary = summarize_document_ir(roundtrip_ir)
        structural_kinds = ("table", "image", "list_item")
        semantic_roundtrip_checks = {
            "document_ir_valid": roundtrip_validation.get("status") == "pass",
            "normalized_text_equal": source_summary.get("normalized_text_sha256") == roundtrip_summary.get("normalized_text_sha256"),
            "section_count_equal": source_summary.get("section_count") == roundtrip_summary.get("section_count"),
            "resource_count_equal": source_summary.get("resource_count") == roundtrip_summary.get("resource_count"),
            **{
                f"{kind}_count_equal": source_summary.get("block_kind_counts", {}).get(kind, 0)
                == roundtrip_summary.get("block_kind_counts", {}).get(kind, 0)
                for kind in structural_kinds
            },
        }
        if native_contract.get("status") != "pass" or not critical_pass or not all(semantic_roundtrip_checks.values()):
            raise ValueError("generated HWPX package validation failed")
        temporary.replace(output_path)
    finally:
        temporary.unlink(missing_ok=True)

    if emit_ir_path is not None:
        write_json(emit_ir_path, report_ir)

    receipt = {
        "schema_version": "report_orchestra_native_hwpx_export.v1",
        "status": "structure_checked",
        "generated_at_kst": now_kst(),
        "project": project.name,
        "export_type": "native_hwpx",
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "runtime_dependency_mode": "embedded_system_core",
        "source_cover_data": cover_data_path.relative_to(project).as_posix(),
        "source_chapters": [item.relative_to(project).as_posix() for item in sorted((project / "reports" / "chapters").glob("ch*.html"))],
        "output": output_path.relative_to(project).as_posix(),
        "sha256": sha256_file(output_path),
        "byte_count": output_path.stat().st_size,
        "report_export_ir": summarize_report_export_ir(report_ir),
        "owned_document_ir": source_summary,
        "semantic_roundtrip": {
            "status": "pass",
            "checks": semantic_roundtrip_checks,
            "roundtrip_summary": roundtrip_summary,
        },
        "native_package_contract_status": native_contract.get("status"),
        "critical_package_components": {name: statuses.get(name) for name in CRITICAL_COMPONENTS},
        "known_semantic_gaps": [name for name, status in statuses.items() if status != "pass"],
        "normalization_warnings": report_ir.get("warnings", []),
        "visual_equivalence_claimed": False,
        "native_render_review_status": "not_run",
        "limitations": [
            "Report HTML is normalized through Report Export IR; arbitrary DOM and CSS are not passed directly to the HWPX engine.",
            "Package and semantic structure checks do not prove visual identity in Hancom Office.",
            "Unsupported or missing local images are reported as normalization warnings and are not fetched externally.",
        ],
    }
    return receipt


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Export Report Orchestra chapter sources to native HWPX.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--cover-data", default="reports/cover.data.json", help="Cover JSON relative to the project")
    parser.add_argument("--output", default=DEFAULT_OUTPUT.as_posix(), help="HWPX output relative to the project")
    parser.add_argument("--emit-ir", default="", help="Optional Report Export IR JSON path relative to the project")
    parser.add_argument("--probe", action="store_true", help="Check the embedded exporter and engine without writing a document")
    args = parser.parse_args()

    if args.probe:
        print(json.dumps({
            "schema_version": "report_orchestra_native_hwpx_export_probe.v1",
            "status": "available",
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "runtime_dependency_mode": "embedded_system_core",
            "report_export_ir_schema": "report_export_ir.v1",
        }, ensure_ascii=False))
        return 0

    project = PROJECT_ROOT / args.project
    if not project.is_dir():
        print(json.dumps({"status": "failed", "reason": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2
    cover_data_path = project / args.cover_data
    if not cover_data_path.is_file():
        print(json.dumps({"status": "failed", "reason": f"cover data not found: {args.cover_data}"}, ensure_ascii=False, indent=2))
        return 2
    try:
        receipt = export_hwpx(
            project,
            cover_data_path,
            project / args.output,
            emit_ir_path=(project / args.emit_ir) if args.emit_ir else None,
        )
        write_json(project / "reports" / "export_checks" / "hwpx_structure_check.json", receipt)
    except Exception as exc:
        print(json.dumps({"status": "failed", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
