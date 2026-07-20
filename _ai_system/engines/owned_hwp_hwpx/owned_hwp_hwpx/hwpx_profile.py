"""Path-free structural profiling for HWPX packages."""

from __future__ import annotations

from collections import Counter
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from .border_fill_semantics import parse_hwpx_border_fill_root
from .compose_control_semantics import parse_hwpx_compose_root
from .footnote_control_semantics import parse_hwpx_footnote_root
from .inline_control_semantics import parse_hwpx_inline_control_root
from .line_segment_semantics import parse_hwpx_line_segment_root
from .list_section_semantics import parse_hwpx_list_root, parse_hwpx_section_root
from .object_binary_semantics import parse_hwpx_binary_package, parse_hwpx_object_root
from .page_hiding_semantics import parse_hwpx_page_hiding_root
from .render_compatibility_semantics import (
    parse_hwpx_header_compatibility_root,
    parse_hwpx_paragraph_render_root,
)
from .style_semantics import parse_hwpx_style_root
from .table_semantics import parse_hwpx_table_root


REQUIRED_ENTRIES = (
    "mimetype",
    "version.xml",
    "META-INF/manifest.xml",
    "Contents/content.hpf",
    "Contents/header.xml",
)

COUNTED_TAGS = {
    "p",
    "t",
    "run",
    "sec",
    "subList",
    "tbl",
    "tr",
    "tc",
    "charPr",
    "paraPr",
    "pagePr",
    "secPr",
    "fontface",
    "font",
    "style",
    "tabPr",
    "lineseg",
    "numbering",
    "bullet",
    "binData",
    "bindata",
    "pic",
    "img",
    "ctrl",
    "colPr",
    "pageHiding",
    "pageNum",
    "newNum",
    "header",
    "autoNum",
    "footNote",
    "footer",
    "fieldBegin",
    "fieldEnd",
    "container",
    "shape",
    "tab",
    "lineBreak",
    "hyphen",
    "nbSpace",
    "fwSpace",
}

REFERENCE_ATTRS = {
    "charPrIDRef",
    "paraPrIDRef",
    "styleIDRef",
}


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _entry_prefix(name: str) -> str:
    if "/" not in name:
        return "root"
    return name.split("/", 1)[0]


def _is_section_entry(name: str) -> bool:
    if not name.startswith("Contents/section") or not name.endswith(".xml"):
        return False
    middle = name[len("Contents/section") : -len(".xml")]
    return middle.isdigit()


def _safe_xml_role(name: str) -> str:
    if name == "Contents/header.xml":
        return "header"
    if _is_section_entry(name):
        return "section"
    if name == "Contents/content.hpf":
        return "content_hpf"
    if name == "META-INF/manifest.xml":
        return "manifest"
    if name == "version.xml":
        return "version"
    return "other_xml"


def _profile_xml_bytes(payload: bytes) -> dict[str, Any]:
    root = ElementTree.fromstring(payload)
    tag_counter: Counter[str] = Counter()
    counted_tags: Counter[str] = Counter()
    reference_counts: Counter[str] = Counter()
    reference_values: dict[str, set[str]] = defaultdict(set)
    ctrl_child_counts: Counter[str] = Counter()
    page_geometries: list[dict[str, Any]] = []
    text_char_count = 0

    for element in root.iter():
        local = _local_name(element.tag)
        tag_counter[local] += 1
        if local in COUNTED_TAGS:
            counted_tags[local] += 1
        if local == "t" and element.text:
            text_char_count += len(element.text)
        if local == "ctrl":
            children = list(element)
            if children:
                ctrl_child_counts[_local_name(children[0].tag)] += 1
        if local == "pagePr":
            page_geometries.append(_page_geometry_from_element(element))
        for attr_name, attr_value in element.attrib.items():
            local_attr = _local_name(attr_name)
            if local_attr in REFERENCE_ATTRS:
                reference_counts[local_attr] += 1
                reference_values[local_attr].add(str(attr_value))

    top_tags = dict(tag_counter.most_common(16))
    root_tag = _local_name(root.tag)
    return {
        "root_tag": _local_name(root.tag),
        "top_tags": top_tags,
        "counted_tags": dict(sorted(counted_tags.items())),
        "reference_counts": dict(sorted(reference_counts.items())),
        "reference_distinct_counts": {
            key: len(values) for key, values in sorted(reference_values.items())
        },
        "ctrl_child_counts": dict(sorted(ctrl_child_counts.items())),
        "page_geometries": page_geometries,
        "text_char_count": text_char_count,
        "style_semantics": parse_hwpx_style_root(root) if root_tag == "head" else {},
        "header_compatibility_semantics": parse_hwpx_header_compatibility_root(root)
        if root_tag == "head"
        else {},
        "list_semantics": parse_hwpx_list_root(root) if root_tag == "head" else {},
        "border_fill_semantics": parse_hwpx_border_fill_root(root) if root_tag == "head" else {},
        "section_semantics": parse_hwpx_section_root(root) if root_tag == "sec" else [],
        "line_segment_semantics": parse_hwpx_line_segment_root(root) if root_tag == "sec" else {},
        "inline_control_semantics": parse_hwpx_inline_control_root(root) if root_tag == "sec" else {},
        "compose_control_semantics": parse_hwpx_compose_root(root) if root_tag == "sec" else {},
        "page_hiding_semantics": parse_hwpx_page_hiding_root(root) if root_tag == "sec" else {},
        "footnote_control_semantics": parse_hwpx_footnote_root(root) if root_tag == "sec" else {},
        "paragraph_render_semantics": parse_hwpx_paragraph_render_root(root) if root_tag == "sec" else {},
        "table_semantics": parse_hwpx_table_root(root) if root_tag == "sec" else {},
        "object_semantics": parse_hwpx_object_root(root) if root_tag == "sec" else {},
    }


def profile_hwpx_file(path: Path) -> dict[str, Any]:
    """Return a structural profile without exposing paths or document text."""

    try:
        with ZipFile(path, "r") as package:
            names = sorted(package.namelist())
            name_set = set(names)
            section_entries = [name for name in names if _is_section_entry(name)]
            xml_entries = [
                name
                for name in names
                if name.endswith(".xml")
                and (
                    name == "Contents/header.xml"
                    or name == "Contents/content.hpf"
                    or name == "META-INF/manifest.xml"
                    or name == "version.xml"
                    or _is_section_entry(name)
                )
            ]

            prefix_counts = Counter(_entry_prefix(name) for name in names)
            aggregate_tags: Counter[str] = Counter()
            header_aggregate_tags: Counter[str] = Counter()
            section_aggregate_tags: Counter[str] = Counter()
            aggregate_reference_counts: Counter[str] = Counter()
            section_reference_counts: Counter[str] = Counter()
            aggregate_reference_distinct_counts: Counter[str] = Counter()
            section_reference_distinct_counts: Counter[str] = Counter()
            aggregate_ctrl_child_counts: Counter[str] = Counter()
            section_ctrl_child_counts: Counter[str] = Counter()
            aggregate_page_geometries: list[dict[str, Any]] = []
            section_page_geometries: list[dict[str, Any]] = []
            xml_roles: Counter[str] = Counter()
            parse_errors: list[dict[str, str]] = []
            text_char_count = 0
            section_text_char_count = 0
            producer_family = _producer_family(package)
            style_semantics: dict[str, Any] = {}
            header_compatibility_semantics: dict[str, Any] = {}
            list_semantics: dict[str, Any] = {}
            border_fill_semantics: dict[str, Any] = {}
            section_semantics: list[dict[str, Any]] = []
            line_segment_semantics: list[dict[str, Any]] = []
            inline_control_semantics: list[dict[str, Any]] = []
            compose_control_semantics: list[dict[str, Any]] = []
            page_hiding_semantics: list[dict[str, Any]] = []
            footnote_control_semantics: list[dict[str, Any]] = []
            paragraph_render_semantics: list[dict[str, Any]] = []
            table_semantics: list[dict[str, Any]] = []
            object_semantics: list[dict[str, Any]] = []

            for name in xml_entries:
                role = _safe_xml_role(name)
                xml_roles[role] += 1
                try:
                    parsed = _profile_xml_bytes(package.read(name))
                except ElementTree.ParseError as exc:
                    parse_errors.append({"role": role, "error": exc.__class__.__name__})
                    continue
                for tag, count in parsed["counted_tags"].items():
                    aggregate_tags[tag] += int(count)
                    if role == "header":
                        header_aggregate_tags[tag] += int(count)
                    if role == "section":
                        section_aggregate_tags[tag] += int(count)
                for attr, count in parsed["reference_counts"].items():
                    aggregate_reference_counts[attr] += int(count)
                    if role == "section":
                        section_reference_counts[attr] += int(count)
                for attr, count in parsed["reference_distinct_counts"].items():
                    aggregate_reference_distinct_counts[attr] += int(count)
                    if role == "section":
                        section_reference_distinct_counts[attr] += int(count)
                for child, count in parsed["ctrl_child_counts"].items():
                    aggregate_ctrl_child_counts[child] += int(count)
                    if role == "section":
                        section_ctrl_child_counts[child] += int(count)
                aggregate_page_geometries.extend(parsed["page_geometries"])
                if role == "section":
                    section_page_geometries.extend(parsed["page_geometries"])
                text_char_count += int(parsed["text_char_count"])
                if role == "section":
                    section_text_char_count += int(parsed["text_char_count"])
                if role == "header":
                    style_semantics = parsed.get("style_semantics", {})
                    header_compatibility_semantics = parsed.get("header_compatibility_semantics", {})
                    list_semantics = parsed.get("list_semantics", {})
                    border_fill_semantics = parsed.get("border_fill_semantics", {})
                if role == "section":
                    section_semantics.extend(parsed.get("section_semantics", []))
                    line_segment_semantics.append(parsed.get("line_segment_semantics", {}))
                    inline_control_semantics.append(parsed.get("inline_control_semantics", {}))
                    compose_control_semantics.append(parsed.get("compose_control_semantics", {}))
                    page_hiding_semantics.append(parsed.get("page_hiding_semantics", {}))
                    footnote_control_semantics.append(parsed.get("footnote_control_semantics", {}))
                    paragraph_render_semantics.append(parsed.get("paragraph_render_semantics", {}))
                    table_semantics.append(parsed.get("table_semantics", {}))
                    object_semantics.append(parsed.get("object_semantics", {}))

            missing_required = [entry for entry in REQUIRED_ENTRIES if entry not in name_set]
            status = "profiled" if not parse_errors else "profiled_with_xml_errors"
            if missing_required:
                status = "profiled_with_missing_required_entries"

            return {
                "status": status,
                "producer_family": producer_family,
                "is_zip": True,
                "entry_count": len(names),
                "entry_prefix_counts": dict(sorted(prefix_counts.items())),
                "required_entries_present": not missing_required,
                "missing_required_entry_count": len(missing_required),
                "section_count": len(section_entries),
                "bin_data_count": sum(1 for name in names if name.startswith("BinData/")),
                "xml_role_counts": dict(sorted(xml_roles.items())),
                "aggregate_tags": dict(sorted(aggregate_tags.items())),
                "header_aggregate_tags": dict(sorted(header_aggregate_tags.items())),
                "section_aggregate_tags": dict(sorted(section_aggregate_tags.items())),
                "aggregate_reference_counts": dict(sorted(aggregate_reference_counts.items())),
                "section_reference_counts": dict(sorted(section_reference_counts.items())),
                "aggregate_reference_distinct_counts": dict(sorted(aggregate_reference_distinct_counts.items())),
                "section_reference_distinct_counts": dict(sorted(section_reference_distinct_counts.items())),
                "aggregate_ctrl_child_counts": dict(sorted(aggregate_ctrl_child_counts.items())),
                "section_ctrl_child_counts": dict(sorted(section_ctrl_child_counts.items())),
                "aggregate_page_geometries": aggregate_page_geometries,
                "section_page_geometries": section_page_geometries,
                "aggregate_page_geometry_sums": _page_geometry_sums(aggregate_page_geometries),
                "section_page_geometry_sums": _page_geometry_sums(section_page_geometries),
                "text_char_count": text_char_count,
                "section_text_char_count": section_text_char_count,
                "style_semantics": style_semantics,
                "header_compatibility_semantics": header_compatibility_semantics,
                "list_semantics": list_semantics,
                "border_fill_semantics": border_fill_semantics,
                "section_semantics": section_semantics,
                "line_segment_semantics": line_segment_semantics,
                "inline_control_semantics": inline_control_semantics,
                "compose_control_semantics": compose_control_semantics,
                "page_hiding_semantics": page_hiding_semantics,
                "footnote_control_semantics": footnote_control_semantics,
                "paragraph_render_semantics": paragraph_render_semantics,
                "table_semantics": table_semantics,
                "object_semantics": object_semantics,
                "binary_semantics": parse_hwpx_binary_package(package),
                "parse_error_count": len(parse_errors),
                "parse_errors": parse_errors[:8],
            }
    except FileNotFoundError:
        return {
            "status": "missing",
            "is_zip": False,
        }
    except BadZipFile:
        return {
            "status": "bad_zip",
            "is_zip": False,
        }


def _producer_family(package: ZipFile) -> str:
    try:
        root = ElementTree.fromstring(package.read("version.xml"))
    except (KeyError, ElementTree.ParseError):
        return "unknown"
    application = str(root.attrib.get("application", ""))
    app_version = str(root.attrib.get("appVersion", ""))
    if "PolarisOffice" in app_version:
        return "portable"
    if application == "Hancom Office Hangul" and "WIN32LE" in app_version:
        return "hancom"
    if application in {"owned-hwp-hwpx", "owned-hwp-hwpx-dry-run"}:
        return "owned"
    return "unknown"


def _page_geometry_from_element(element: ElementTree.Element) -> dict[str, int]:
    margin: dict[str, int] = {}
    for child in list(element):
        if _local_name(child.tag) == "margin":
            margin = {
                "left": _as_int(child.attrib.get("left")),
                "right": _as_int(child.attrib.get("right")),
                "top": _as_int(child.attrib.get("top")),
                "bottom": _as_int(child.attrib.get("bottom")),
                "header": _as_int(child.attrib.get("header")),
                "footer": _as_int(child.attrib.get("footer")),
                "gutter": _as_int(child.attrib.get("gutter")),
            }
            break
    return {
        "width": _as_int(element.attrib.get("width")),
        "height": _as_int(element.attrib.get("height")),
        "margin": margin,
    }


def _page_geometry_sums(page_geometries: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "width": sum(_as_int(item.get("width")) for item in page_geometries if isinstance(item, dict)),
        "height": sum(_as_int(item.get("height")) for item in page_geometries if isinstance(item, dict)),
        "margin": sum(_page_margin_sum(item) for item in page_geometries if isinstance(item, dict)),
    }


def _page_margin_sum(page_geometry: dict[str, Any]) -> int:
    margin = page_geometry.get("margin", {}) if isinstance(page_geometry.get("margin"), dict) else {}
    return sum(_as_int(margin.get(key)) for key in ("left", "right", "top", "bottom", "header", "footer", "gutter"))


def _as_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
