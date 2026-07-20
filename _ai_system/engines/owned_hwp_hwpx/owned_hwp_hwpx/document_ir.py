"""Canonical document IR contracts shared by HWPX and authoring HTML."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from typing import Any


DOCUMENT_IR_SCHEMA_VERSION = "owned_document_ir.v2"
AUTHORING_HTML_CONTRACT_VERSION = "hwpx-authoring-html.v1"


def validate_document_ir(model: dict[str, Any]) -> dict[str, Any]:
    sections = model.get("sections", [])
    resources = model.get("resources", [])
    errors: list[str] = []
    if model.get("schema_version") != DOCUMENT_IR_SCHEMA_VERSION:
        errors.append("document_ir_schema_version_invalid")
    if not isinstance(sections, list) or not sections:
        errors.append("document_ir_sections_required")
    if not isinstance(resources, list):
        errors.append("document_ir_resources_invalid")

    block_refs: list[str] = []
    referenced_resources: list[str] = []
    resource_refs: list[str] = []
    for section in sections if isinstance(sections, list) else []:
        if not isinstance(section, dict):
            errors.append("document_ir_section_invalid")
            continue
        blocks = section.get("blocks", [])
        if not isinstance(blocks, list):
            errors.append("document_ir_blocks_invalid")
            continue
        for block in _walk_blocks(blocks):
            if not isinstance(block, dict):
                errors.append("document_ir_block_invalid")
                continue
            block_ref = str(block.get("block_ref", ""))
            if not block_ref:
                errors.append("document_ir_block_ref_required")
            block_refs.append(block_ref)
            if block.get("kind") == "image":
                resource_ref = str(block.get("resource_ref", ""))
                if not resource_ref:
                    errors.append("document_ir_image_resource_ref_required")
                else:
                    referenced_resources.append(resource_ref)
    for resource in resources if isinstance(resources, list) else []:
        if not isinstance(resource, dict):
            errors.append("document_ir_resource_invalid")
            continue
        resource_ref = str(resource.get("resource_ref", ""))
        if not resource_ref:
            errors.append("document_ir_resource_ref_required")
        resource_refs.append(resource_ref)
        payload = str(resource.get("payload_base64", ""))
        if payload and not str(resource.get("sha256", "")):
            errors.append("document_ir_resource_digest_required")

    if len(block_refs) != len(set(block_refs)):
        errors.append("document_ir_duplicate_block_ref")
    if len(resource_refs) != len(set(resource_refs)):
        errors.append("document_ir_duplicate_resource_ref")
    if any(resource_ref not in set(resource_refs) for resource_ref in referenced_resources):
        errors.append("document_ir_image_resource_missing")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "section_count": len(sections) if isinstance(sections, list) else 0,
        "block_count": len(block_refs),
        "resource_count": len(resource_refs),
    }


def summarize_document_ir(model: dict[str, Any]) -> dict[str, Any]:
    sections = model.get("sections", []) if isinstance(model.get("sections"), list) else []
    top_level_blocks = [
        block
        for section in sections
        if isinstance(section, dict)
        for block in section.get("blocks", [])
        if isinstance(block, dict)
    ]
    blocks = [block for block in _walk_blocks(top_level_blocks) if isinstance(block, dict)]
    resources = model.get("resources", []) if isinstance(model.get("resources"), list) else []
    text = "\n".join(_block_text(block) for block in blocks)
    loss_report = model.get("loss_report", {}) if isinstance(model.get("loss_report"), dict) else {}
    return {
        "schema_version": "owned_document_ir_summary.v1",
        "status": "summarized",
        "source_format": model.get("source_format"),
        "section_count": len(sections),
        "block_count": len(blocks),
        "block_kind_counts": dict(sorted(Counter(str(block.get("kind", "unknown")) for block in blocks).items())),
        "resource_count": len(resources),
        "text_char_count": len(text),
        "normalized_text_sha256": sha256(" ".join(text.split()).encode("utf-8")).hexdigest(),
        "unsupported_feature_count": int(loss_report.get("unsupported_feature_count", 0)),
        "loss_event_counts": loss_report.get("event_counts", {}),
        "raw_text_included": False,
        "resource_payload_included": False,
        "local_path_included": False,
        "private_filename_included": False,
    }


def serializable_document_ir(model: dict[str, Any], *, include_resource_payloads: bool) -> dict[str, Any]:
    copy = _copy_value(model)
    if not include_resource_payloads:
        for resource in copy.get("resources", []):
            if isinstance(resource, dict):
                resource.pop("payload_base64", None)
    return copy


def _block_text(block: dict[str, Any]) -> str:
    return str(block.get("text", ""))


def _walk_blocks(blocks: list[Any]):
    for block in blocks:
        if not isinstance(block, dict):
            yield block
            continue
        yield block
        if block.get("kind") != "table":
            nested = [
                layer_block
                for layer in block.get("overlay_layers", [])
                if isinstance(layer, dict)
                for layer_block in layer.get("blocks", [])
            ] if block.get("kind") == "image" else []
        else:
            nested = [
                cell_block
                for row in block.get("rows", [])
                if isinstance(row, list)
                for cell in row
                if isinstance(cell, dict)
                for cell_block in cell.get("blocks", [])
            ]
            caption = block.get("caption")
            if isinstance(caption, dict):
                nested.extend(caption.get("blocks", []))
        yield from _walk_blocks(nested)


def _copy_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _copy_value(entry) for key, entry in value.items()}
    if isinstance(value, list):
        return [_copy_value(entry) for entry in value]
    return value
