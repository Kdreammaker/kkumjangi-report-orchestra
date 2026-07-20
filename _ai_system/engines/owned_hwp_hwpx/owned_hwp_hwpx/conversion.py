"""Stable conversion API for the owned HWP-to-HWPX engine."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .document_model import COLUMN_COMPATIBILITY_PROFILES, build_document_model_from_hwp
from .hwpx_writer import write_hwpx_package
from .package_validation import validate_generated_hwpx
from .resource_limits import MAX_SOURCE_BYTES, ResourceLimitError


ENGINE_ID = "owned_hwp_hwpx_python"
ENGINE_VERSION = "0.2.0"
CONVERSION_SCHEMA_VERSION = "owned_hwp_hwpx_conversion_manifest.v1"
ERROR_SCHEMA_VERSION = "owned_hwp_hwpx_conversion_error.v1"
DEFAULT_COMPATIBILITY_PROFILE = "hancom"

ERROR_EXIT_CODES = {
    "invalid_argument": 2,
    "unsupported_profile": 2,
    "source_missing": 3,
    "source_not_file": 3,
    "output_exists": 4,
    "manifest_exists": 4,
    "conversion_failed": 5,
    "validation_failed": 6,
    "resource_limit_exceeded": 7,
}


class OwnedHwpConversionError(Exception):
    """Conversion failure with a stable public-safe code and message."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.public_message = message
        self.retryable = retryable
        self.exit_code = ERROR_EXIT_CODES.get(code, 5)

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": ERROR_SCHEMA_VERSION,
            "status": "failed",
            "error": {
                "code": self.code,
                "message": self.public_message,
                "retryable": self.retryable,
            },
        }


def convert_hwp_to_hwpx(
    source_path: Path | str,
    output_path: Path | str,
    *,
    compatibility_profile: str = DEFAULT_COMPATIBILITY_PROFILE,
    overwrite: bool = False,
    manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Convert one HWP file and return a deterministic path-free receipt."""

    source = Path(source_path)
    output = Path(output_path)
    manifest = Path(manifest_path) if manifest_path is not None else None
    profile = _validate_arguments(source, output, compatibility_profile, overwrite, manifest)
    temporary_output: Path | None = None
    try:
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            if manifest is not None:
                manifest.parent.mkdir(parents=True, exist_ok=True)
            temporary_output = _temporary_path(
                output.parent,
                ".owned-hwp-output-",
                ".hwpx.tmp",
            )
        except OSError:
            raise OwnedHwpConversionError(
                "conversion_failed",
                "The conversion output location is not writable.",
            ) from None
        try:
            model = build_document_model_from_hwp(
                source,
                include_text=True,
                compatibility_profile=profile,
            )
            if not str(model.get("source_profile_status", "")).startswith("profiled"):
                raise OwnedHwpConversionError(
                    "conversion_failed",
                    "The source is not a supported HWP 5.x document.",
                )
            writer_result = write_hwpx_package(temporary_output, model)
        except OwnedHwpConversionError:
            raise
        except ResourceLimitError:
            raise OwnedHwpConversionError(
                "resource_limit_exceeded",
                "The HWP source exceeds the owned engine resource limits.",
            ) from None
        except (OSError, ValueError, TypeError, KeyError, IndexError):
            raise OwnedHwpConversionError(
                "conversion_failed",
                "The HWP source could not be converted by the owned engine.",
            ) from None

        validation = validate_generated_hwpx(model, temporary_output)
        if validation.get("status") != "pass":
            raise OwnedHwpConversionError(
                "validation_failed",
                "The generated HWPX package did not pass owned-engine validation.",
            )

        receipt = _build_receipt(
            source,
            temporary_output,
            model,
            writer_result,
            validation,
            profile,
        )
        os.replace(temporary_output, output)
        temporary_output = None
        if manifest is not None:
            _write_manifest_atomic(manifest, receipt, overwrite=overwrite)
        return receipt
    except OwnedHwpConversionError:
        raise
    except OSError:
        raise OwnedHwpConversionError(
            "conversion_failed",
            "The converted HWPX package could not be committed.",
        ) from None
    finally:
        if temporary_output is not None:
            _remove_file(temporary_output)


def _validate_arguments(
    source: Path,
    output: Path,
    compatibility_profile: str,
    overwrite: bool,
    manifest: Path | None,
) -> str:
    profile = str(compatibility_profile or "").strip().lower()
    if profile not in COLUMN_COMPATIBILITY_PROFILES:
        raise OwnedHwpConversionError(
            "unsupported_profile",
            "Compatibility profile must be either 'hancom' or 'portable'.",
        )
    if _same_path(source, output):
        raise OwnedHwpConversionError(
            "invalid_argument",
            "Source and output must be different files.",
        )
    if source.suffix.lower() != ".hwp":
        raise OwnedHwpConversionError(
            "invalid_argument",
            "Source must use the HWP file format.",
        )
    if output.suffix.lower() != ".hwpx":
        raise OwnedHwpConversionError(
            "invalid_argument",
            "Output must use the HWPX file format.",
        )
    if not source.exists():
        raise OwnedHwpConversionError("source_missing", "The HWP source does not exist.")
    if not source.is_file():
        raise OwnedHwpConversionError("source_not_file", "The HWP source is not a file.")
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise OwnedHwpConversionError(
            "resource_limit_exceeded",
            "The HWP source exceeds the owned engine resource limits.",
        )
    if output.exists() and not overwrite:
        raise OwnedHwpConversionError("output_exists", "The HWPX output already exists.")
    if output.exists() and not output.is_file():
        raise OwnedHwpConversionError("invalid_argument", "The HWPX output is not a file.")
    if manifest is not None:
        if manifest.suffix.lower() != ".json":
            raise OwnedHwpConversionError(
                "invalid_argument",
                "Conversion manifest must use the .json extension.",
            )
        if _same_path(manifest, source) or _same_path(manifest, output):
            raise OwnedHwpConversionError(
                "invalid_argument",
                "Conversion manifest must be separate from source and output.",
            )
        if manifest.exists() and not overwrite:
            raise OwnedHwpConversionError(
                "manifest_exists",
                "The conversion manifest already exists.",
            )
        if manifest.exists() and not manifest.is_file():
            raise OwnedHwpConversionError(
                "invalid_argument",
                "The conversion manifest is not a file.",
            )
    return profile


def _build_receipt(
    source: Path,
    output: Path,
    model: dict[str, Any],
    writer_result: dict[str, Any],
    validation: dict[str, Any],
    compatibility_profile: str,
) -> dict[str, Any]:
    summary = model.get("summary", {}) if isinstance(model.get("summary"), dict) else {}
    warnings = {
        "malformed_text_control_count": _as_int(summary.get("text_malformed_control_count")),
        "list_parse_warning_count": _as_int(summary.get("list_parse_warning_count")),
        "border_fill_parse_warning_count": _as_int(summary.get("border_fill_parse_warning_count")),
        "paragraph_extension_nonzero_count": _as_int(
            summary.get("style_semantic_para_extension_nonzero_count")
        ),
        "font_default_face_unmapped_count": _as_int(
            summary.get("style_semantic_font_default_face_unmapped_count")
        ),
        "font_serif_style_unmapped_count": _as_int(
            summary.get("style_semantic_font_serif_style_unmapped_count")
        ),
    }
    document_counts = {
        key: _as_int(summary.get(key))
        for key in (
            "section_count",
            "paragraph_count",
            "char_shape_run_count",
            "table_count",
            "table_row_count",
            "table_cell_count",
            "picture_count",
            "shape_count",
            "bin_data_count",
        )
    }
    return {
        "schema_version": CONVERSION_SCHEMA_VERSION,
        "status": "converted",
        "engine": {
            "id": ENGINE_ID,
            "version": ENGINE_VERSION,
            "implementation": "python_standard_library",
            "third_party_hwp_conversion_library": False,
        },
        "compatibility_profile": compatibility_profile,
        "source": {
            "format": "hwp",
            "size_bucket": _size_bucket(source.stat().st_size),
            "profile_status": str(model.get("source_profile_status", "unknown")),
        },
        "output": {
            "format": "hwpx",
            "sha256": _file_sha256(output),
            "size_bytes": output.stat().st_size,
            "entry_count": _as_int(writer_result.get("entry_count")),
            "deterministic_zip_metadata": bool(
                writer_result.get("deterministic_zip_metadata")
            ),
        },
        "document_counts": document_counts,
        "validation": validation,
        "loss_report": {
            "status": "explicit_limitations_recorded" if any(warnings.values()) else "no_counted_warnings",
            "warning_counts": warnings,
            "native_rendered_visual_parity": "not_evaluated_in_work_item_6",
            "ole_application_behavior": "not_evaluated",
            "equation_and_chart_behavior": "not_claimed",
        },
        "public_safety": {
            "paths_in_manifest": False,
            "filenames_in_manifest": False,
            "raw_document_text_in_manifest": False,
            "binary_payloads_in_manifest": False,
            "exception_details_in_manifest": False,
        },
    }


def _write_manifest_atomic(path: Path, receipt: dict[str, Any], *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise OwnedHwpConversionError("manifest_exists", "The conversion manifest already exists.")
    temporary = _temporary_path(path.parent, ".owned-hwp-manifest-", ".json.tmp")
    try:
        temporary.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
        temporary = None
    except OSError:
        raise OwnedHwpConversionError(
            "conversion_failed",
            "The conversion manifest could not be written.",
        ) from None
    finally:
        if temporary is not None:
            _remove_file(temporary)


def _temporary_path(parent: Path, prefix: str, suffix: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=prefix,
        suffix=suffix,
        dir=parent,
        delete=False,
    )
    path = Path(handle.name)
    handle.close()
    return path


def _remove_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve(strict=False) == right.resolve(strict=False)
    except OSError:
        return os.path.abspath(left) == os.path.abspath(right)


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _size_bucket(size_bytes: int) -> str:
    if size_bytes < 128 * 1024:
        return "lt_128kb"
    if size_bytes < 1024 * 1024:
        return "lt_1mb"
    if size_bytes < 10 * 1024 * 1024:
        return "lt_10mb"
    if size_bytes < 100 * 1024 * 1024:
        return "lt_100mb"
    return "gte_100mb"


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
