"""Public conversion entrypoints for the owned authoring HTML/HWPX contract."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .conversion import ENGINE_ID, ENGINE_VERSION
from .document_ir import summarize_document_ir, validate_document_ir
from .html_reader import parse_authoring_html_document_ir
from .html_writer import render_document_ir_to_html
from .hwpx_reader import read_hwpx_document_ir
from .hwpx_writer import write_hwpx_package
from .ir_hwpx_adapter import build_hwpx_writer_model_from_document_ir
from .package_validation import validate_generated_hwpx, validate_hwpx_native_package_contract


CRITICAL_PACKAGE_COMPONENTS = (
    "package", "core", "controls", "header_compatibility", "inline_controls",
    "compose_controls", "page_hiding_controls", "footnote_controls",
    "paragraph_render", "drawing_namespaces", "binaries", "runs", "text",
)

EMBEDDED_CONTROL_REQUIRED_COMPONENTS = (
    "package", "style", "header_compatibility", "lists", "sections",
    "compose_controls", "page_hiding_controls", "footnote_controls",
    "border_fills", "drawing_namespaces", "binaries", "runs",
)

RAW_DRAWING_REQUIRED_COMPONENTS = (
    "package", "style", "header_compatibility", "lists", "sections",
    "border_fills", "drawing_namespaces", "binaries", "runs",
)


def convert_hwpx_to_authoring_html(source: Path, target: Path) -> dict[str, Any]:
    model = read_hwpx_document_ir(source)
    validation = validate_document_ir(model)
    if validation["status"] != "pass":
        return _failed("document_ir_validation_failed", validation=validation)
    html = render_document_ir_to_html(model)
    _atomic_write_text(target, html)
    return {
        "schema_version": "owned_hwpx_to_authoring_html_result.v1",
        "status": "converted",
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "source_format": "hwpx",
        "target_format": "hwpx-authoring-html.v1",
        "target_sha256": sha256(html.encode("utf-8")).hexdigest(),
        "target_byte_count": len(html.encode("utf-8")),
        "document_summary": summarize_document_ir(model),
        "external_resource_fetch_required": False,
        "visual_equivalence_claimed": False,
    }


def convert_authoring_html_to_hwpx(source: Path, target: Path) -> dict[str, Any]:
    html = source.read_text(encoding="utf-8")
    document_ir = parse_authoring_html_document_ir(html)
    ir_validation = validate_document_ir(document_ir)
    if ir_validation["status"] != "pass":
        return _failed("document_ir_validation_failed", validation=ir_validation)
    model = build_hwpx_writer_model_from_document_ir(document_ir)
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(prefix="owned-html-hwpx-", suffix=".hwpx", dir=target.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        write_hwpx_package(temporary, model)
        native_contract = validate_hwpx_native_package_contract(temporary)
        package_validation = validate_generated_hwpx(model, temporary)
        component_statuses = package_validation.get("component_statuses", {})
        required_components = _required_package_components(document_ir)
        critical_pass = all(component_statuses.get(name) == "pass" for name in required_components)
        if native_contract.get("status") != "pass" or not critical_pass:
            return _failed(
                "generated_hwpx_validation_failed",
                native_contract_status=native_contract.get("status"),
                required_package_components=required_components,
                component_statuses=component_statuses,
            )
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return {
        "schema_version": "owned_authoring_html_to_hwpx_result.v1",
        "status": "converted",
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "source_format": "hwpx-authoring-html.v1",
        "target_format": "hwpx",
        "target_sha256": sha256(target.read_bytes()).hexdigest(),
        "target_byte_count": target.stat().st_size,
        "document_summary": summarize_document_ir(document_ir),
        "native_package_contract_status": native_contract.get("status"),
        "critical_package_components": {name: component_statuses.get(name) for name in required_components},
        "known_semantic_gaps": [name for name, status in component_statuses.items() if status != "pass"],
        "layout_adjustments": {
            "line_segment_textpos_remapped_paragraph_count": int(
                model.get("summary", {}).get("line_segment_textpos_remap_count", 0)
            ),
        },
        "visual_equivalence_claimed": False,
    }


def _atomic_write_text(target: Path, value: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        prefix="owned-hwpx-html-", suffix=".html", dir=target.parent, mode="w", encoding="utf-8", delete=False
    ) as handle:
        handle.write(value)
        temporary = Path(handle.name)
    try:
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def _failed(reason: str, **details: Any) -> dict[str, Any]:
    return {"schema_version": "owned_html_hwpx_conversion_error.v1", "status": "failed", "reason": reason, **details}


def _required_package_components(model: dict[str, Any]) -> tuple[str, ...]:
    if _has_raw_drawings(model):
        return RAW_DRAWING_REQUIRED_COMPONENTS
    if _has_preserved_embedded_controls(model):
        return EMBEDDED_CONTROL_REQUIRED_COMPONENTS
    return CRITICAL_PACKAGE_COMPONENTS


def _has_preserved_embedded_controls(model: dict[str, Any]) -> bool:
    for block in _walk_blocks(model):
        for control in block.get("structural_controls", []):
            if isinstance(control, dict) and control.get("render_layout_child") in {"header", "footer"}:
                return True
    return False


def _has_raw_drawings(model: dict[str, Any]) -> bool:
    return any(block.get("kind") == "drawing" for block in _walk_blocks(model))


def _walk_blocks(model: dict[str, Any]):
    pending = [
        block
        for section in model.get("sections", [])
        if isinstance(section, dict)
        for block in reversed(section.get("blocks", []))
        if isinstance(block, dict)
    ]
    while pending:
        block = pending.pop()
        yield block
        if block.get("kind") == "table":
            nested = [
                child
                for row in block.get("rows", [])
                if isinstance(row, list)
                for cell in row
                if isinstance(cell, dict)
                for child in cell.get("blocks", [])
                if isinstance(child, dict)
            ]
            caption = block.get("caption")
            if isinstance(caption, dict):
                nested.extend(child for child in caption.get("blocks", []) if isinstance(child, dict))
            pending.extend(reversed(nested))
        if block.get("kind") == "image":
            overlay = [
                child
                for layer in block.get("overlay_layers", [])
                if isinstance(layer, dict)
                for child in layer.get("blocks", [])
                if isinstance(child, dict)
            ]
            pending.extend(reversed(overlay))
