from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
REPORT_USE_STATUSES = {"claim_ready", "quote_verified", "report_citable"}
LINK_USE_LEVELS = {"quote_verified", "report_citable"}
URL_STATUS_OK = {"ok", "verified", "200", "exact_url_verified"}
PENDING_QUOTE_RE = re.compile(r"quote\s+verification\s+pending|인용\s*검증\s*대기|인용\s*확인\s*대기", re.I)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def clean(value: object) -> str:
    return str(value or "").strip().strip("`").strip("*").strip()


def normalize_header(value: str) -> str:
    text = clean(value).lower()
    compact = re.sub(r"\s+", "_", text)
    if "source_id" in compact or "source id" in text:
        return "source_id"
    if text.startswith("원본 자료명") or "source title" in text or text == "title" or "자료명" in text:
        return "title"
    if text == "status" or "readiness" in text or "상태" in text:
        return "status"
    if "used_in" in compact or "used in" in text or "사용" in text:
        return "used_in"
    if "url_or_path" in compact or "local path" in text or "로컬 보관 경로" in text:
        return "url_or_path"
    if "capture_path" in compact or "capture path" in text:
        return "capture_path"
    if "local_original_path" in compact or "original_file_path" in compact or "original path" in text:
        return "local_original_path"
    if "source_record_path" in compact:
        return "source_record_path"
    if "original_path" in compact:
        return "original_path"
    if "use_level" in compact:
        return "use_level"
    if "url_status" in compact:
        return "url_status"
    if "download_status" in compact:
        return "download_status"
    if "capture_status" in compact:
        return "capture_status"
    if text in {"url", "official_url"}:
        return "url"
    if "source_locator" in compact or "quote_location" in compact or "exact_quote_location" in compact:
        return "source_locator"
    if "needs_user_file" in compact:
        return "needs_user_file"
    if "user_file_request_id" in compact:
        return "user_file_request_id"
    return compact


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {normalize_header(str(key or "")): clean(value) for key, value in row.items()}
            for row in reader
        ]


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    headers: list[str] | None = None
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if headers is None:
            headers = [normalize_header(cell) for cell in cells]
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if len(cells) == len(headers):
            rows.append({key: clean(value) for key, value in zip(headers, cells)})
    return rows


def parse_source_record(path: Path) -> dict[str, str]:
    data: dict[str, str] = {"_path": path.as_posix()}
    for line in read_text(path).splitlines():
        match = re.match(r"\s*[-*]\s*\*\*([^*]+)\*\*\s*:\s*(.*)", line)
        if not match:
            match = re.match(r"\s*[-*]\s*`?([A-Za-z0-9_ -]+)`?\s*:\s*(.*)", line)
        if match:
            data[normalize_header(match.group(1))] = clean(match.group(2))
    data.setdefault("source_id", path.stem)
    return data


def by_source(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        source_id = clean(row.get("source_id"))
        if source_id:
            result[source_id] = row
    return result


def source_ids_from_inventory(rows: list[dict[str, str]]) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        source_id = clean(row.get("source_id"))
        if source_id:
            ids.add(source_id)
            continue
        record_path = clean(row.get("source_record_path"))
        if record_path:
            ids.add(Path(record_path).stem)
    return ids


def resolve_project_path(project: Path, value: str) -> Path | None:
    value = clean(value)
    if not value or re.match(r"https?://", value):
        return None
    candidates = [project / value, project.parent / value, Path(value)]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return project / value


def path_exists(project: Path, value: str) -> bool:
    path = resolve_project_path(project, value)
    return bool(path and path.exists())


def link_has_verified_collection(link: dict[str, str]) -> bool:
    return clean(link.get("url_status")).lower() in URL_STATUS_OK


def source_is_report_used(row: dict[str, str], record: dict[str, str] | None = None, link: dict[str, str] | None = None) -> bool:
    values = [
        row.get("status", ""),
        row.get("source_readiness_status", ""),
        row.get("used_in", ""),
    ]
    if record:
        values.extend([record.get("status", ""), record.get("source_readiness_status", ""), record.get("used_in", "")])
    if link:
        values.append(link.get("use_level", ""))
    normalized = {clean(value).lower() for value in values if clean(value)}
    return bool(normalized & REPORT_USE_STATUSES) or any(clean(value) for value in [row.get("used_in", ""), record.get("used_in", "") if record else ""])


def validate_project(project: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []

    inventory_rows = read_csv_rows(project / "references" / "reference_inventory.csv")
    link_rows = read_csv_rows(project / "references" / "source_link_register.csv")
    index_rows = parse_markdown_table(project / "source_index" / "source_master_index.md")
    record_paths = sorted((project / "references" / "source_records").glob("*.md"))
    records = {clean(parse_source_record(path).get("source_id")): (path, parse_source_record(path)) for path in record_paths}

    inventory_ids = source_ids_from_inventory(inventory_rows)
    link_by_id = by_source(link_rows)
    index_by_id = by_source(index_rows)
    record_ids = {source_id for source_id in records if source_id}
    index_ids = set(index_by_id)
    link_ids = set(link_by_id)

    source_system_ids = record_ids | index_ids | link_ids
    if source_system_ids and not inventory_rows:
        errors.append(
            "references/reference_inventory.csv has no rows while source records/index/link register exist; "
            "the user-facing reference library is out of sync"
        )

    missing_inventory = sorted(source_system_ids - inventory_ids)
    if missing_inventory:
        errors.append(
            "source ids missing from references/reference_inventory.csv: "
            + ", ".join(missing_inventory[:20])
            + (" ..." if len(missing_inventory) > 20 else "")
        )

    missing_records = sorted((index_ids | link_ids) - record_ids)
    if missing_records:
        errors.append("source ids missing source_records/*.md: " + ", ".join(missing_records[:20]))

    missing_index = sorted((record_ids | link_ids) - index_ids)
    if missing_index:
        errors.append("source ids missing from source_index/source_master_index.md: " + ", ".join(missing_index[:20]))

    for source_id, row in index_by_id.items():
        record_tuple = records.get(source_id)
        record = record_tuple[1] if record_tuple else None
        link = link_by_id.get(source_id)
        report_used = source_is_report_used(row, record, link)

        if report_used and not link:
            url_or_path = clean((record or {}).get("url_or_path") or row.get("url_or_path"))
            if re.match(r"https?://", url_or_path):
                errors.append(f"{source_id}: report-used URL source lacks source_link_register.csv row")

        if report_used and link:
            use_level = clean(link.get("use_level")).lower()
            if use_level not in LINK_USE_LEVELS:
                errors.append(f"{source_id}: source_link_register use_level={use_level} cannot support report use")
            if not link_has_verified_collection(link):
                errors.append(f"{source_id}: source_link_register lacks verified exact URL status")
            if not clean(link.get("url")):
                errors.append(f"{source_id}: source_link_register lacks exact official URL")
            if use_level in LINK_USE_LEVELS and not clean(link.get("source_locator")):
                errors.append(f"{source_id}: quote/report-citable link row requires source_locator")
            if clean(link.get("needs_user_file")).lower() == "yes" and not clean(link.get("user_file_request_id")):
                warnings.append(f"{source_id}: needs_user_file=yes should reference user_requested_materials.md")
            evidence_paths = [clean(link.get("original_path")), clean(link.get("capture_path"))]
            for value in evidence_paths:
                if value and not path_exists(project, value):
                    errors.append(f"{source_id}: source_link_register evidence path does not exist: {value}")

        if report_used and record_tuple:
            path, record = record_tuple
            text = read_text(path)
            if PENDING_QUOTE_RE.search(text):
                errors.append(f"{source_id}: report-used source record still contains quote verification pending marker")
            for key in ("local_original_path", "capture_path", "original_path"):
                value = clean(record.get(key))
                if value and not path_exists(project, value):
                    errors.append(f"{source_id}: source record {key} does not exist: {value}")

    for source_id in sorted(link_ids - index_ids):
        warnings.append(f"{source_id}: source_link_register row exists before source_index registration")

    return {
        "project": project.name,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "reference_inventory_rows": len(inventory_rows),
            "reference_inventory_source_ids": len(inventory_ids),
            "source_link_register_rows": len(link_rows),
            "source_index_rows": len(index_rows),
            "source_records": len(record_paths),
            "missing_inventory_ids": missing_inventory,
            "missing_source_record_ids": missing_records,
            "missing_source_index_ids": missing_index,
        },
        "note": (
            "This validator checks register consistency only. It does not judge analysis depth, "
            "business merit, legal correctness, or writing quality."
        ),
    }


def iter_projects() -> list[Path]:
    if not PROJECT_ROOT.exists():
        return []
    return sorted(path for path in PROJECT_ROOT.iterdir() if path.is_dir())


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Validate consistency between reference inventory, source link register, source index, and source records."
    )
    parser.add_argument("--project", default="", help="Project folder under 00_사용자_작업공간")
    args = parser.parse_args()

    projects = [PROJECT_ROOT / args.project] if args.project else iter_projects()
    results = []
    errors: list[str] = []
    for project in projects:
        if not project.exists():
            payload = {"project": project.name, "passed": False, "errors": [f"project not found: {project}"], "warnings": [], "metrics": {}}
        else:
            payload = validate_project(project)
        results.append(payload)
        errors.extend(f"{payload['project']}: {error}" for error in payload.get("errors", []))

    output = {
        "projects_checked": len(results),
        "passed": not errors,
        "errors": errors,
        "results": results,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
