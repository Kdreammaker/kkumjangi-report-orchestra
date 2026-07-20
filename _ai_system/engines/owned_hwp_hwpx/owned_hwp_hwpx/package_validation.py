"""Public-safe validation for HWPX packages emitted by the owned writer."""

from __future__ import annotations

from collections import Counter
from pathlib import Path, PurePosixPath
import re
from typing import Any, Callable
from zipfile import BadZipFile, ZIP_STORED, ZipFile
from xml.etree import ElementTree

from .border_fill_semantics import compare_border_fill_semantics
from .compose_control_semantics import (
    compare_compose_control_semantics,
    model_compose_control_semantics,
)
from .hwpx_profile import profile_hwpx_file
from .footnote_control_semantics import (
    compare_footnote_control_semantics,
    model_footnote_control_semantics,
)
from .hwpx_writer import DETERMINISTIC_ZIP_DATETIME
from .inline_control_semantics import (
    compare_inline_control_semantics,
    model_inline_control_semantics,
)
from .line_segment_semantics import compare_line_segment_semantics
from .list_section_semantics import compare_list_semantics, compare_section_semantics
from .object_binary_semantics import compare_binary_semantics, compare_object_semantics
from .page_hiding_semantics import (
    compare_page_hiding_semantics,
    model_page_hiding_semantics,
)
from .render_compatibility_semantics import (
    compare_header_compatibility_semantics,
    compare_paragraph_render_semantics,
    model_header_compatibility_semantics,
    model_paragraph_render_semantics,
)
from .style_semantics import compare_style_semantics
from .table_semantics import compare_table_semantics
from .text_fidelity import compare_texts, extract_hwpx_text, normalize_text


APP_NS = "http://www.hancom.co.kr/hwpml/2011/app"
CONFIG_NS = "urn:oasis:names:tc:opendocument:xmlns:config:1.0"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
CORE_NS = "http://www.hancom.co.kr/hwpml/2011/core"
MANIFEST_NS = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
OPF_NS = "http://www.idpf.org/2007/opf/"
PARAGRAPH_NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"
VERSION_NS = "http://www.hancom.co.kr/hwpml/2011/version"


def validate_generated_hwpx(model: dict[str, Any], path: Path) -> dict[str, Any]:
    """Validate package, model, semantic, binary, and normalized-text parity."""

    profile = profile_hwpx_file(path)
    core = _compare_core(model, profile)
    controls = _compare_controls(model, profile)
    style = compare_style_semantics(
        _mapping(model.get("style_semantics")),
        _mapping(profile.get("style_semantics")),
    )
    header_compatibility = compare_header_compatibility_semantics(
        model_header_compatibility_semantics(_mapping(model.get("style_semantics"))),
        _mapping(profile.get("header_compatibility_semantics")),
    )
    lists = compare_list_semantics(
        _mapping(model.get("list_semantics")),
        _mapping(profile.get("list_semantics")),
    )
    source_sections = [
        _mapping(section.get("section_semantics"))
        for section in model.get("sections", [])
        if isinstance(section, dict)
    ]
    sections = compare_section_semantics(source_sections, profile.get("section_semantics", []))
    line_segments = _compare_section_items(
        [section.get("line_segment_semantics", {}) for section in _sections(model)],
        profile.get("line_segment_semantics", []),
        compare_line_segment_semantics,
    )
    inline_controls = _compare_section_items(
        [model_inline_control_semantics(section) for section in _sections(model)],
        profile.get("inline_control_semantics", []),
        compare_inline_control_semantics,
    )
    compose_controls = _compare_section_items(
        [model_compose_control_semantics(section) for section in _sections(model)],
        profile.get("compose_control_semantics", []),
        compare_compose_control_semantics,
    )
    page_hiding_controls = _compare_section_items(
        [model_page_hiding_semantics(section) for section in _sections(model)],
        profile.get("page_hiding_semantics", []),
        compare_page_hiding_semantics,
    )
    footnote_controls = _compare_section_items(
        [model_footnote_control_semantics(section) for section in _sections(model)],
        profile.get("footnote_control_semantics", []),
        compare_footnote_control_semantics,
    )
    paragraph_render = _compare_section_items(
        [model_paragraph_render_semantics(section) for section in _sections(model)],
        profile.get("paragraph_render_semantics", []),
        compare_paragraph_render_semantics,
    )
    border_fills = compare_border_fill_semantics(
        _mapping(model.get("border_fill_semantics")),
        _mapping(profile.get("border_fill_semantics")),
    )
    tables = _compare_section_items(
        [{"tables": section.get("table_shapes", [])} for section in _sections(model)],
        profile.get("table_semantics", []),
        compare_table_semantics,
    )
    objects = _compare_section_items(
        [{"shapes": section.get("object_shapes", [])} for section in _sections(model)],
        profile.get("object_semantics", []),
        compare_object_semantics,
    )
    drawing_namespaces = _validate_drawing_namespaces(path)
    source_binary_items = [
        item for item in model.get("_binary_payloads", []) if isinstance(item, dict)
    ]
    binaries = compare_binary_semantics(
        {"items": source_binary_items},
        _mapping(profile.get("binary_semantics")),
    )
    runs = _validate_visible_run_boundaries(model)
    text = _compare_normalized_text(model, path)
    package = _validate_zip_contract(path)

    components = {
        "package": package,
        "core": core,
        "controls": controls,
        "style": _public_component(style),
        "header_compatibility": _public_component(header_compatibility),
        "lists": _public_component(lists),
        "sections": _public_component(sections),
        "line_segments": line_segments,
        "inline_controls": inline_controls,
        "compose_controls": compose_controls,
        "page_hiding_controls": page_hiding_controls,
        "footnote_controls": footnote_controls,
        "paragraph_render": paragraph_render,
        "border_fills": _public_component(border_fills),
        "tables": tables,
        "objects": objects,
        "drawing_namespaces": drawing_namespaces,
        "binaries": _public_component(binaries),
        "runs": runs,
        "text": text,
    }
    component_statuses = {
        key: str(value.get("status", "fail")) for key, value in components.items()
    }
    passed = all(status == "pass" for status in component_statuses.values())
    return {
        "schema_version": "owned_hwp_hwpx_generated_package_validation.v9",
        "status": "pass" if passed else "fail",
        "profile_status": str(profile.get("status", "unknown")),
        "producer_family": str(profile.get("producer_family", "unknown")),
        "component_statuses": component_statuses,
        "components": components,
    }


def _validate_drawing_namespaces(path: Path) -> dict[str, Any]:
    try:
        with ZipFile(path, "r") as package:
            section_names = sorted(
                (
                    name
                    for name in package.namelist()
                    if re.fullmatch(r"Contents/section\d+\.xml", name)
                ),
                key=_section_entry_index,
            )
            return _validate_drawing_namespaces_in_package(package, section_names)
    except (BadZipFile, OSError):
        return _drawing_namespace_result(
            {
                "section_count": 0,
                "matrix_count": 0,
                "core_point_count": 0,
                "line_point_count": 0,
                "invalid_matrix_namespace_count": 0,
                "invalid_core_point_namespace_count": 0,
                "invalid_line_point_namespace_count": 0,
                "invalid_line_point_parent_count": 0,
                "parse_error_count": 1,
            }
        )


def _validate_drawing_namespaces_in_package(
    package: ZipFile,
    section_names: list[str],
) -> dict[str, Any]:
    matrix_names = {"transMatrix", "scaMatrix", "rotMatrix"}
    core_point_names = {
        "pt",
        "pt0",
        "pt1",
        "pt2",
        "pt3",
        "center",
        "ax1",
        "ax2",
        "start1",
        "end1",
        "start2",
        "end2",
        "extent",
    }
    counts = {
        "section_count": 0,
        "matrix_count": 0,
        "core_point_count": 0,
        "line_point_count": 0,
        "invalid_matrix_namespace_count": 0,
        "invalid_core_point_namespace_count": 0,
        "invalid_line_point_namespace_count": 0,
        "invalid_line_point_parent_count": 0,
        "parse_error_count": 0,
    }
    counts["section_count"] = len(section_names)
    for name in section_names:
        try:
            root = ElementTree.fromstring(package.read(name))
        except (ElementTree.ParseError, KeyError):
            counts["parse_error_count"] += 1
            continue
        for parent in root.iter():
            parent_local = _xml_local_name(parent.tag)
            for child in parent:
                namespace, local_name = _xml_name(child.tag)
                if local_name in matrix_names:
                    counts["matrix_count"] += 1
                    counts["invalid_matrix_namespace_count"] += int(
                        namespace != CORE_NS
                    )
                elif local_name in core_point_names:
                    counts["core_point_count"] += 1
                    counts["invalid_core_point_namespace_count"] += int(
                        namespace != CORE_NS
                    )
                elif local_name in {"startPt", "endPt"}:
                    counts["line_point_count"] += 1
                    expected_namespace = {
                        "connectLine": PARAGRAPH_NS,
                        "line": CORE_NS,
                    }.get(parent_local)
                    if expected_namespace is None:
                        counts["invalid_line_point_parent_count"] += 1
                    elif namespace != expected_namespace:
                        counts["invalid_line_point_namespace_count"] += 1
    return _drawing_namespace_result(counts)


def _drawing_namespace_result(counts: dict[str, int]) -> dict[str, Any]:
    checks = {
        "section_xml_parseable": counts["parse_error_count"] == 0,
        "matrix_namespaces_valid": counts["invalid_matrix_namespace_count"] == 0,
        "core_point_namespaces_valid": (
            counts["invalid_core_point_namespace_count"] == 0
        ),
        "line_point_namespaces_valid": (
            counts["invalid_line_point_namespace_count"] == 0
        ),
        "line_point_parents_valid": counts["invalid_line_point_parent_count"] == 0,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": counts,
    }


def validate_hwpx_native_package_contract(path: Path | str) -> dict[str, Any]:
    """Validate the package graph required by native HWPX readers."""

    target = Path(path)
    graph = _empty_native_graph_contract()
    try:
        with ZipFile(target, "r") as package:
            graph = _validate_native_graph(package, set(package.namelist()))
    except (BadZipFile, KeyError, OSError):
        pass
    return {
        "schema_version": "owned_hwp_hwpx_native_package_contract.v2",
        "status": "pass" if all(graph["checks"].values()) else "fail",
        **graph,
    }


def _validate_zip_contract(path: Path) -> dict[str, Any]:
    checks = {
        "readable_zip": False,
        "mimetype_first": False,
        "mimetype_stored": False,
        "mimetype_exact": False,
        "no_duplicate_entries": False,
        "safe_entry_names": False,
        "fixed_entry_timestamps": False,
        "no_encrypted_entries": False,
    }
    entry_count = 0
    graph = _empty_native_graph_contract()
    try:
        with ZipFile(path, "r") as package:
            infos = package.infolist()
            names = [info.filename for info in infos]
            entry_count = len(infos)
            checks["readable_zip"] = True
            checks["mimetype_first"] = bool(infos) and infos[0].filename == "mimetype"
            checks["mimetype_stored"] = bool(infos) and infos[0].compress_type == ZIP_STORED
            checks["mimetype_exact"] = (
                bool(infos) and package.read("mimetype") == b"application/hwp+zip"
            )
            checks["no_duplicate_entries"] = len(names) == len(set(names))
            checks["safe_entry_names"] = all(_safe_entry_name(name) for name in names)
            checks["fixed_entry_timestamps"] = all(
                info.date_time == DETERMINISTIC_ZIP_DATETIME for info in infos
            )
            checks["no_encrypted_entries"] = all(not (info.flag_bits & 0x1) for info in infos)
            graph = _validate_native_graph(package, set(names))
    except (BadZipFile, KeyError, OSError):
        pass
    checks.update(graph["checks"])
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {"entry_count": entry_count, **graph["counts"]},
    }


def _validate_native_graph(package: ZipFile, names: set[str]) -> dict[str, Any]:
    checks = _empty_native_graph_contract()["checks"]
    required = {
        "mimetype",
        "version.xml",
        "META-INF/container.xml",
        "META-INF/manifest.xml",
        "settings.xml",
        "Contents/content.hpf",
        "Contents/header.xml",
    }
    checks["native_required_entries_present"] = required <= names
    xml_names = sorted(
        name
        for name in names
        if name.endswith((".xml", ".hpf")) and not name.endswith("/")
    )
    roots: dict[str, ElementTree.Element] = {}
    try:
        roots = {name: ElementTree.fromstring(package.read(name)) for name in xml_names}
        checks["native_package_xml_parseable"] = True
    except (ElementTree.ParseError, KeyError):
        return {"checks": checks, "counts": _native_graph_counts(names, 0, 0)}

    container = roots["META-INF/container.xml"]
    settings = roots["settings.xml"]
    manifest = roots["META-INF/manifest.xml"]
    version = roots["version.xml"]
    content = roots["Contents/content.hpf"]

    checks["native_container_root"] = container.tag == f"{{{CONTAINER_NS}}}container"
    rootfiles = container.findall(f".//{{{CONTAINER_NS}}}rootfile")
    checks["native_container_content_rootfile"] = any(
        item.get("full-path") == "Contents/content.hpf"
        and item.get("media-type") == "application/hwpml-package+xml"
        for item in rootfiles
    )
    checks["native_settings_root"] = (
        settings.tag == f"{{{APP_NS}}}HWPApplicationSetting"
    )
    caret = settings.find(f"{{{APP_NS}}}CaretPosition")
    checks["native_settings_caret"] = caret is not None
    checks["native_settings_caret_attributes"] = caret is not None and all(
        caret.get(key) is not None for key in ("listIDRef", "paraIDRef", "pos")
    )
    checks["native_settings_print_info"] = any(
        item.get("name") == "PrintInfo"
        for item in settings.findall(f"{{{CONFIG_NS}}}config-item-set")
    )
    checks["native_manifest_root"] = manifest.tag == f"{{{MANIFEST_NS}}}manifest"
    checks["native_version_root"] = version.tag == f"{{{VERSION_NS}}}HCFVersion"
    checks["native_version_identity"] = (
        version.get("tagetApplication") == "WORDPROCESSOR"
        and bool(version.get("application"))
        and bool(version.get("appVersion"))
    )
    checks["native_version_core_attributes"] = all(
        version.get(key) is not None
        for key in ("major", "minor", "micro", "buildNumber", "os", "xmlVersion")
    )
    checks["native_content_root"] = content.tag == f"{{{OPF_NS}}}package"
    checks["native_content_identity_attributes"] = all(
        key in content.attrib for key in ("version", "unique-identifier", "id")
    )

    manifest_node = content.find(f"{{{OPF_NS}}}manifest")
    spine_node = content.find(f"{{{OPF_NS}}}spine")
    items = (
        list(manifest_node.findall(f"{{{OPF_NS}}}item"))
        if manifest_node is not None
        else []
    )
    item_ids = [str(item.get("id", "")) for item in items]
    hrefs = [str(item.get("href", "")) for item in items]
    by_id = dict(zip(item_ids, hrefs))
    checks["native_manifest_item_ids_unique"] = (
        bool(item_ids) and all(item_ids) and len(item_ids) == len(set(item_ids))
    )
    checks["native_manifest_media_types_present"] = bool(items) and all(
        bool(item.get("media-type")) for item in items
    )
    checks["native_xml_manifest_media_types"] = all(
        item.get("media-type") == "application/xml"
        for item in items
        if str(item.get("href", "")).endswith((".xml", ".hpf"))
    )
    checks["native_manifest_hrefs_safe"] = all(_safe_entry_name(href) for href in hrefs)
    checks["native_manifest_hrefs_exist"] = bool(hrefs) and all(href in names for href in hrefs)
    checks["native_header_reference"] = by_id.get("header") == "Contents/header.xml"
    checks["native_settings_reference"] = by_id.get("settings") == "settings.xml"

    sections = sorted(
        (name for name in names if re.fullmatch(r"Contents/section\d+\.xml", name)),
        key=_section_entry_index,
    )
    drawing_namespaces = _validate_drawing_namespaces_in_package(package, sections)
    section_structure = _validate_native_section_structure(
        [roots[name] for name in sections if name in roots]
    )
    checks.update(
        {
            f"native_drawing_{key}": bool(value)
            for key, value in drawing_namespaces["checks"].items()
        }
    )
    checks.update(section_structure["checks"])
    checks["native_section_entries_present"] = bool(sections)
    section_items = sorted(
        (
            (item_id, href)
            for item_id, href in by_id.items()
            if re.fullmatch(r"Contents/section\d+\.xml", href)
        ),
        key=lambda item: _section_entry_index(item[1]),
    )
    checks["native_section_references_exact"] = [href for _item_id, href in section_items] == sections
    binaries = sorted(
        name
        for name in names
        if name.startswith("BinData/") and not name.endswith("/")
    )
    checks["native_binary_references_exact"] = sorted(
        href for href in hrefs if href.startswith("BinData/")
    ) == binaries
    binary_item_references = _binary_item_references(
        package,
        ["Contents/header.xml", *sections],
    )
    checks["native_binary_item_references_resolve"] = all(
        value in by_id for value in binary_item_references
    )

    refs = list(spine_node.findall(f"{{{OPF_NS}}}itemref")) if spine_node is not None else []
    ref_ids = [str(item.get("idref", "")) for item in refs]
    expected_section_ids = [item_id for item_id, _href in section_items]
    checks["native_spine_references_resolve"] = bool(ref_ids) and all(
        ref_id in by_id for ref_id in ref_ids
    )
    checks["native_spine_header_first"] = bool(ref_ids) and ref_ids[0] == "header"
    checks["native_section_spine_references_exact"] = [
        ref_id for ref_id in ref_ids if ref_id in expected_section_ids
    ] == expected_section_ids
    return {
        "checks": checks,
        "counts": {
            **_native_graph_counts(names, len(items), len(refs)),
            "native_binary_item_reference_count": len(binary_item_references),
            **{
                f"native_drawing_{key}": value
                for key, value in drawing_namespaces["counts"].items()
            },
            **section_structure["counts"],
        },
    }


def _empty_native_graph_contract() -> dict[str, Any]:
    return {
        "checks": {
            "native_required_entries_present": False,
            "native_package_xml_parseable": False,
            "native_container_root": False,
            "native_container_content_rootfile": False,
            "native_settings_root": False,
            "native_settings_caret": False,
            "native_settings_caret_attributes": False,
            "native_settings_print_info": False,
            "native_manifest_root": False,
            "native_version_root": False,
            "native_version_identity": False,
            "native_version_core_attributes": False,
            "native_content_root": False,
            "native_content_identity_attributes": False,
            "native_manifest_item_ids_unique": False,
            "native_manifest_media_types_present": False,
            "native_xml_manifest_media_types": False,
            "native_manifest_hrefs_safe": False,
            "native_manifest_hrefs_exist": False,
            "native_header_reference": False,
            "native_settings_reference": False,
            "native_drawing_section_xml_parseable": False,
            "native_drawing_matrix_namespaces_valid": False,
            "native_drawing_core_point_namespaces_valid": False,
            "native_drawing_line_point_namespaces_valid": False,
            "native_drawing_line_point_parents_valid": False,
            "native_footnote_ctrl_wrapper_valid": False,
            "native_footnote_sub_list_present": False,
            "native_footnote_autonum_hierarchy_valid": False,
            "native_section_entries_present": False,
            "native_section_references_exact": False,
            "native_binary_references_exact": False,
            "native_binary_item_references_resolve": False,
            "native_spine_references_resolve": False,
            "native_spine_header_first": False,
            "native_section_spine_references_exact": False,
        },
        "counts": {
            **_native_graph_counts(set(), 0, 0),
            "native_binary_item_reference_count": 0,
        },
    }


def _native_graph_counts(
    names: set[str], manifest_items: int, spine_items: int
) -> dict[str, int]:
    return {
        "native_section_entry_count": sum(
            bool(re.fullmatch(r"Contents/section\d+\.xml", name)) for name in names
        ),
        "native_binary_entry_count": sum(
            name.startswith("BinData/") and not name.endswith("/") for name in names
        ),
        "native_manifest_item_count": manifest_items,
        "native_spine_item_count": spine_items,
        "native_drawing_section_count": 0,
        "native_drawing_matrix_count": 0,
        "native_drawing_core_point_count": 0,
        "native_drawing_line_point_count": 0,
        "native_drawing_invalid_matrix_namespace_count": 0,
        "native_drawing_invalid_core_point_namespace_count": 0,
        "native_drawing_invalid_line_point_namespace_count": 0,
        "native_drawing_invalid_line_point_parent_count": 0,
        "native_drawing_parse_error_count": 0,
        "native_direct_run_sub_list_count": 0,
        "native_footnote_count": 0,
        "native_invalid_footnote_parent_count": 0,
        "native_footnote_without_sub_list_count": 0,
        "native_footnote_autonum_count": 0,
        "native_orphan_footnote_autonum_count": 0,
        "native_group_child_count": 0,
        "native_group_child_root_attribute_count": 0,
    }


def _validate_native_section_structure(
    section_roots: list[ElementTree.Element],
) -> dict[str, Any]:
    root_only_shape_attributes = {
        "id",
        "zOrder",
        "numberingType",
        "textWrap",
        "textFlow",
        "lock",
        "dropcapstyle",
    }
    counts = {
        "native_direct_run_sub_list_count": 0,
        "native_footnote_count": 0,
        "native_invalid_footnote_parent_count": 0,
        "native_footnote_without_sub_list_count": 0,
        "native_footnote_autonum_count": 0,
        "native_orphan_footnote_autonum_count": 0,
        "native_group_child_count": 0,
        "native_group_child_root_attribute_count": 0,
    }
    for root in section_roots:
        parent_by_id = {
            id(child): parent
            for parent in root.iter()
            for child in parent
        }
        for element in root.iter():
            local_name = _xml_local_name(element.tag)
            parent = parent_by_id.get(id(element))
            parent_name = _xml_local_name(parent.tag) if parent is not None else ""
            if local_name == "subList" and parent_name == "run":
                counts["native_direct_run_sub_list_count"] += 1
            if local_name == "footNote":
                counts["native_footnote_count"] += 1
                counts["native_invalid_footnote_parent_count"] += int(
                    parent_name != "ctrl"
                )
                counts["native_footnote_without_sub_list_count"] += int(
                    not any(_xml_local_name(child.tag) == "subList" for child in element)
                )
            if local_name == "autoNum" and element.get("numType") == "FOOTNOTE":
                counts["native_footnote_autonum_count"] += 1
                ancestor = parent
                inside_footnote = False
                while ancestor is not None:
                    if _xml_local_name(ancestor.tag) == "footNote":
                        inside_footnote = True
                        break
                    ancestor = parent_by_id.get(id(ancestor))
                counts["native_orphan_footnote_autonum_count"] += int(
                    not inside_footnote
                )
            if parent_name == "container":
                counts["native_group_child_count"] += 1
                counts["native_group_child_root_attribute_count"] += sum(
                    attribute in element.attrib
                    for attribute in root_only_shape_attributes
                )
    checks = {
        "native_footnote_ctrl_wrapper_valid": (
            counts["native_invalid_footnote_parent_count"] == 0
        ),
        "native_footnote_sub_list_present": (
            counts["native_footnote_without_sub_list_count"] == 0
        ),
        "native_footnote_autonum_hierarchy_valid": (
            counts["native_orphan_footnote_autonum_count"] == 0
        ),
    }
    return {"checks": checks, "counts": counts}


def _binary_item_references(package: ZipFile, xml_names: list[str]) -> list[str]:
    references = []
    pattern = re.compile(
        rb'<(?:[^\s>:]+:)?([^\s>/]+)[^>]*\bbinaryItemIDRef="([^"]+)"[^>]*>'
    )
    for name in xml_names:
        try:
            payload = package.read(name)
        except KeyError:
            continue
        for match in pattern.finditer(payload):
            if match.group(1) == b"binData":
                continue
            references.append(match.group(2).decode("utf-8", errors="replace"))
    return references


def _section_entry_index(name: str) -> int:
    match = re.search(r"section(\d+)\.xml$", name)
    return int(match.group(1)) if match else -1


def _xml_name(tag: str) -> tuple[str, str]:
    if tag.startswith("{") and "}" in tag:
        namespace, local_name = tag[1:].split("}", 1)
        return namespace, local_name
    return "", tag


def _xml_local_name(tag: str) -> str:
    return _xml_name(tag)[1]


def _safe_entry_name(name: str) -> bool:
    if not name or "\\" in name or "\x00" in name or name.startswith("/"):
        return False
    parts = PurePosixPath(name).parts
    return all(part not in {"", ".", ".."} and ":" not in part for part in parts)


def _compare_core(model: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    summary = _mapping(model.get("summary"))
    header_tags = _mapping(profile.get("header_aggregate_tags"))
    section_tags = _mapping(profile.get("section_aggregate_tags"))
    expected = {
        "section_count": (summary.get("section_count"), profile.get("section_count")),
        "paragraph_count": (summary.get("paragraph_count"), section_tags.get("p")),
        "run_count": (summary.get("char_shape_run_count"), section_tags.get("run")),
        "line_segment_count": (summary.get("line_segment_count"), section_tags.get("lineseg")),
        "table_count": (summary.get("table_count"), section_tags.get("tbl")),
        "table_row_count": (summary.get("table_row_count"), section_tags.get("tr")),
        "table_cell_count": (summary.get("table_cell_count"), section_tags.get("tc")),
        "sub_list_count": (summary.get("sub_list_count"), section_tags.get("subList")),
        "picture_count": (summary.get("picture_count"), section_tags.get("pic")),
        "page_def_count": (summary.get("page_def_count"), section_tags.get("pagePr")),
        "known_layout_control_count": (
            summary.get("known_layout_control_count"),
            section_tags.get("ctrl"),
        ),
        "bin_data_count": (summary.get("bin_data_count"), profile.get("bin_data_count")),
        "char_pr_count": (summary.get("char_pr_count"), header_tags.get("charPr")),
        "para_pr_count": (summary.get("para_pr_count"), header_tags.get("paraPr")),
        "style_count": (summary.get("style_count"), header_tags.get("style")),
        "tab_pr_count": (summary.get("tab_pr_count"), header_tags.get("tabPr")),
        "numbering_count": (summary.get("numbering_count"), header_tags.get("numbering")),
        "bullet_count": (summary.get("bullet_count"), header_tags.get("bullet")),
    }
    checks = {key: _as_int(left) == _as_int(right) for key, (left, right) in expected.items()}
    checks["profile_complete"] = (
        str(profile.get("status", "")) == "profiled"
        and bool(profile.get("required_entries_present"))
        and _as_int(profile.get("parse_error_count")) == 0
    )
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks}


def _compare_controls(model: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    expected: Counter[str] = Counter()
    for section in _sections(model):
        values = section.get("layout_control_child_counts", {})
        if isinstance(values, dict):
            expected.update({str(key): _as_int(value) for key, value in values.items()})
    actual = Counter(
        {str(key): _as_int(value) for key, value in _mapping(profile.get("section_ctrl_child_counts")).items()}
    )
    reference_counts = _mapping(profile.get("section_reference_counts"))
    summary = _mapping(model.get("summary"))
    checks = {
        "control_children_exact": expected == actual,
        "paragraph_style_refs_written": _as_int(reference_counts.get("paraPrIDRef"))
        >= _as_int(summary.get("paragraph_count")),
        "run_style_refs_written": _as_int(reference_counts.get("charPrIDRef"))
        >= _as_int(summary.get("char_shape_run_count")),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "expected_control_child_count": sum(expected.values()),
            "actual_control_child_count": sum(actual.values()),
        },
    }


def _compare_section_items(
    source: list[dict[str, Any]],
    target: Any,
    comparator: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    targets = target if isinstance(target, list) else []
    comparisons = [
        comparator(item, _mapping(targets[index]) if index < len(targets) else {})
        for index, item in enumerate(source)
    ]
    passed = len(source) == len(targets) and all(
        comparison.get("status") == "pass" for comparison in comparisons
    )
    return {
        "status": "pass" if passed else "fail",
        "checks": {
            "section_count": len(source) == len(targets),
            "all_sections": all(comparison.get("status") == "pass" for comparison in comparisons),
        },
        "counts": {
            "source_section_count": len(source),
            "target_section_count": len(targets),
            "passing_section_count": sum(
                comparison.get("status") == "pass" for comparison in comparisons
            ),
        },
    }


def _validate_visible_run_boundaries(model: dict[str, Any]) -> dict[str, Any]:
    paragraph_count = 0
    run_count = 0
    invalid_count = 0
    for section in _sections(model):
        texts = section.get("paragraph_texts", [])
        styles = section.get("paragraph_styles", [])
        for index, style in enumerate(styles if isinstance(styles, list) else []):
            if not isinstance(style, dict):
                continue
            paragraph_count += 1
            text_length = len(str(texts[index])) if isinstance(texts, list) and index < len(texts) else 0
            starts = [
                _as_int(item.get("visible_start", item.get("start")))
                for item in style.get("char_shape_runs", [])
                if isinstance(item, dict)
            ]
            run_count += len(starts)
            invalid_count += sum(start > text_length for start in starts)
            invalid_count += sum(left > right for left, right in zip(starts, starts[1:]))
            invalid_count += int(bool(starts) and starts[0] != 0)
    return {
        "status": "pass" if invalid_count == 0 else "fail",
        "checks": {"all_visible_run_boundaries_valid": invalid_count == 0},
        "counts": {
            "paragraph_count": paragraph_count,
            "run_count": run_count,
            "invalid_boundary_count": invalid_count,
        },
    }


def _compare_normalized_text(model: dict[str, Any], path: Path) -> dict[str, Any]:
    paragraphs: list[str] = []
    for section in _sections(model):
        values = section.get("paragraph_texts", [])
        if isinstance(values, list):
            paragraphs.extend(str(value) for value in values)
    source_text = "\n".join(value for value in paragraphs if value)
    target = extract_hwpx_text(path)
    comparison = compare_texts(source_text, str(target.get("text", "")))
    source_paragraphs = Counter(normalize_text(value) for value in paragraphs)
    target_paragraphs = Counter(
        normalize_text(str(value))
        for value in target.get("paragraphs", [])
        if isinstance(value, str)
    )
    checks = {
        "text_extracted": target.get("status") == "text_extracted",
        "paragraph_count": sum(source_paragraphs.values()) == sum(target_paragraphs.values()),
        "normalized_paragraph_multiset_equal": source_paragraphs == target_paragraphs,
        "normalized_char_count": _as_int(comparison.get("source_char_count"))
        == _as_int(comparison.get("target_char_count")),
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "counts": {
            "source_char_count": _as_int(comparison.get("source_char_count")),
            "target_char_count": _as_int(comparison.get("target_char_count")),
        },
    }


def _public_component(value: dict[str, Any]) -> dict[str, Any]:
    public_keys = {
        "status",
        "checks",
        "counts",
        "source_count",
        "target_count",
        "payload_digest_match_count",
        "image_payload_digest_match_count",
        "format_counts_equal",
    }
    return {
        key: nested
        for key, nested in value.items()
        if key in public_keys
    }


def _sections(model: dict[str, Any]) -> list[dict[str, Any]]:
    return [section for section in model.get("sections", []) if isinstance(section, dict)]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1] if "}" in value else value


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
