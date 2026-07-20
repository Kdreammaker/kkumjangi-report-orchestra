from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import sys
from pathlib import Path


REQUIRED_PACKAGES = {
    "pypdf": "pypdf",
    "docling": "docling",
    "duckdb": "duckdb",
    "docx": "python-docx",
}
RUNTIME = Path("_ai_system") / "runtime"
RUNTIME_ASSETS = {
    "echarts": RUNTIME / "vendor" / "echarts" / "echarts.min.js",
    "pretendard_regular": RUNTIME / "fonts" / "pretendard" / "Pretendard-Regular.woff2",
    "pretendard_semibold": RUNTIME / "fonts" / "pretendard" / "Pretendard-SemiBold.woff2",
    "pretendard_bold": RUNTIME / "fonts" / "pretendard" / "Pretendard-Bold.woff2",
    "pretendard_css": RUNTIME / "fonts" / "pretendard" / "pretendard.css",
}
ENGINE_ROOT = Path("_ai_system") / "engines" / "owned_hwp_hwpx"


def package_status(import_name: str, distribution_name: str) -> dict[str, object]:
    available = importlib.util.find_spec(import_name) is not None
    version = ""
    if available:
        try:
            version = importlib.metadata.version(distribution_name)
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return {"available": available, "version": version}


def duckdb_smoke() -> dict[str, object]:
    try:
        import duckdb  # type: ignore[import-not-found]

        value = duckdb.sql("select 1 + 1").fetchone()[0]
        return {"ok": value == 2, "result": value}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def docling_smoke() -> dict[str, object]:
    try:
        from docling.document_converter import DocumentConverter  # type: ignore[import-not-found]

        return {
            "ok": DocumentConverter is not None,
            "mode": "import_only",
            "note": "Document conversion is tested during reference intake to avoid creating synthetic documents at install time.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def runtime_asset_status() -> dict[str, object]:
    assets: dict[str, object] = {}
    ok = True
    for name, path in RUNTIME_ASSETS.items():
        exists = path.exists() and path.stat().st_size > 0
        assets[name] = {
            "available": exists,
            "path": path.as_posix(),
            "size_bytes": path.stat().st_size if exists else 0,
        }
        ok = ok and exists
    return {
        "ok": ok,
        "assets": assets,
        "note": "ECharts and Pretendard are local runtime assets. Run install_runtime_dependencies.py to download them.",
    }


def embedded_engine_status() -> dict[str, object]:
    package_root = ENGINE_ROOT / "owned_hwp_hwpx"
    metadata_path = ENGINE_ROOT / "ENGINE.json"
    provenance_path = ENGINE_ROOT / "IMPORT_PROVENANCE.json"
    checks = {
        "package_present": (package_root / "__init__.py").is_file(),
        "metadata_present": metadata_path.is_file(),
        "provenance_present": provenance_path.is_file(),
    }
    version = ""
    engine_id = ""
    try:
        if str(ENGINE_ROOT.resolve()) not in sys.path:
            sys.path.insert(0, str(ENGINE_ROOT.resolve()))
        from owned_hwp_hwpx import ENGINE_ID, ENGINE_VERSION  # type: ignore[import-not-found]

        engine_id = str(ENGINE_ID)
        version = str(ENGINE_VERSION)
        checks["importable"] = True
    except Exception:  # noqa: BLE001
        checks["importable"] = False
    return {
        "ok": all(checks.values()) and engine_id == "owned_hwp_hwpx_python" and version == "0.2.0",
        "distribution_status": "embedded",
        "engine_id": engine_id,
        "engine_version": version,
        "runtime_dependency_mode": "embedded_system_core",
        "checks": checks,
    }


def main() -> int:
    packages = {
        name: package_status(import_name, distribution_name)
        for name, (import_name, distribution_name) in {
            name: (name, distribution)
            for name, distribution in REQUIRED_PACKAGES.items()
        }.items()
    }
    python_ok = sys.version_info >= (3, 11)
    engine_status = embedded_engine_status()
    engine_privacy_note = "The embedded owned engine writes local HWPX packages."
    payload: dict[str, object] = {
        "python_version": sys.version.split()[0],
        "python_minimum": "3.11",
        "python_ok": python_ok,
        "packages": packages,
        "duckdb_smoke": duckdb_smoke() if packages["duckdb"]["available"] else {"ok": False, "error": "duckdb not installed"},
        "docling_smoke": docling_smoke() if packages["docling"]["available"] else {"ok": False, "error": "docling not installed"},
        "runtime_assets": runtime_asset_status(),
        "embedded_hwp_hwpx_engine": engine_status,
        "privacy_boundary": {
            "default_mode": "local_only",
            "external_upload": "disabled_by_default",
            "note": "Docling converts local reference files, DuckDB indexes local project metadata, python-docx writes local DOCX export packages, ECharts renders charts locally, and Pretendard is served from the local runtime folder. " + engine_privacy_note + " Do not enable external OCR/VLM/cloud upload without explicit user approval.",
        },
    }
    ok = (
        python_ok
        and all(bool(item["available"]) for item in packages.values())
        and bool(payload["duckdb_smoke"]["ok"])  # type: ignore[index]
        and bool(payload["docling_smoke"]["ok"])  # type: ignore[index]
        and bool(payload["runtime_assets"]["ok"])  # type: ignore[index]
        and bool(payload["embedded_hwp_hwpx_engine"]["ok"])  # type: ignore[index]
    )
    payload["ok"] = ok
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
