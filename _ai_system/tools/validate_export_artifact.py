from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")


def check_docx(path: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "path": path.as_posix(),
        "type": "docx",
        "valid_package": False,
        "has_document": False,
        "has_styles": False,
        "has_numbering": False,
        "has_footnotes_or_endnotes": False,
        "has_media": False,
        "parts": 0,
    }
    try:
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            result["valid_package"] = True
            result["parts"] = len(names)
            result["has_document"] = "word/document.xml" in names
            result["has_styles"] = "word/styles.xml" in names
            result["has_numbering"] = "word/numbering.xml" in names
            result["has_footnotes_or_endnotes"] = "word/footnotes.xml" in names or "word/endnotes.xml" in names
            result["has_media"] = any(name.startswith("word/media/") for name in names)
    except PermissionError:
        result["error"] = "permission_denied_or_file_locked"
    except zipfile.BadZipFile:
        result["error"] = "not_a_valid_zip_package"
    return result


def check_pdf(path: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "path": path.as_posix(),
        "type": "pdf",
        "valid_header": False,
        "size_bytes": path.stat().st_size,
    }
    with path.open("rb") as handle:
        result["valid_header"] = handle.read(5) == b"%PDF-"
    return result


def check_hwpx(path: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "path": path.as_posix(),
        "type": "hwpx",
        "valid_package": False,
        "mimetype_exact": False,
        "native_contract_status": "not_run",
        "parts": 0,
    }
    try:
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            result["valid_package"] = True
            result["parts"] = len(names)
            result["mimetype_exact"] = zf.read("mimetype") == b"application/hwp+zip"
        engine_root = Path("_ai_system") / "engines" / "owned_hwp_hwpx"
        if engine_root.is_dir():
            if str(engine_root.resolve()) not in sys.path:
                sys.path.insert(0, str(engine_root.resolve()))
            from owned_hwp_hwpx import validate_hwpx_native_package_contract  # type: ignore[import-not-found]

            contract = validate_hwpx_native_package_contract(path)
            result["native_contract_status"] = str(contract.get("status", "fail"))
            result["native_contract_checks"] = contract.get("checks", {})
    except PermissionError:
        result["error"] = "permission_denied_or_file_locked"
    except (KeyError, zipfile.BadZipFile):
        result["error"] = "not_a_valid_hwpx_package"
    return result


def validate_export(project: Path, required: bool, strict: bool) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    reports = project / "reports"
    export_checks = reports / "export_checks"
    files = sorted(reports.glob("*.docx")) + sorted(reports.glob("*.pdf")) + sorted(reports.glob("*.hwpx"))
    details: list[dict[str, object]] = []

    if required and not files:
        errors.append("export artifact required but no DOCX/PDF/HWPX exists under reports/")
    elif not files:
        warnings.append("no DOCX/PDF/HWPX export artifact found; HTML remains the working report format")

    for path in files:
        rel = path.relative_to(project)
        if path.suffix.lower() == ".docx":
            detail = check_docx(path)
        elif path.suffix.lower() == ".hwpx":
            detail = check_hwpx(path)
        else:
            detail = check_pdf(path)
        detail["path"] = rel.as_posix()
        details.append(detail)
        if path.suffix.lower() == ".docx":
            if detail.get("error") == "permission_denied_or_file_locked":
                warnings.append(f"DOCX could not be opened for validation, possibly because it is open in Word: {rel.as_posix()}")
                continue
            if not detail.get("valid_package") or not detail.get("has_document"):
                errors.append(f"DOCX is not structurally valid: {rel.as_posix()}")
            if strict and not detail.get("has_styles"):
                errors.append(f"DOCX lacks styles.xml: {rel.as_posix()}")
        if path.suffix.lower() == ".pdf" and not detail.get("valid_header"):
            errors.append(f"PDF lacks %PDF header: {rel.as_posix()}")
        if path.suffix.lower() == ".hwpx":
            if not detail.get("valid_package") or not detail.get("mimetype_exact"):
                errors.append(f"HWPX is not structurally valid: {rel.as_posix()}")
            if strict and detail.get("native_contract_status") != "pass":
                errors.append(f"HWPX native package contract did not pass: {rel.as_posix()}")

    check_files = sorted(export_checks.glob("*")) if export_checks.exists() else []
    render_markers = [p for p in check_files if any(token in p.name.lower() for token in ["render", "screenshot", "page", "structure", "check"])]
    if files and not check_files:
        warnings.append("export files exist but reports/export_checks/ has no verification evidence")
        if strict:
            errors.append("strict export requires verification evidence under reports/export_checks/")
    elif files and not render_markers:
        warnings.append("export checks exist but no render/structure marker was found")

    return {
        "project": project.name,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "export_files": len(files),
            "export_check_files": len(check_files),
            "render_or_structure_markers": len(render_markers),
        },
        "details": details,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate DOCX/PDF/HWPX export artifacts and verification evidence.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--required", action="store_true", help="Fail when no DOCX/PDF/HWPX export exists.")
    parser.add_argument("--strict", action="store_true", help="Require export verification evidence.")
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2
    payload = validate_export(project, args.required, args.strict)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
