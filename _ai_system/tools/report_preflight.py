from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
STAGE_ORDER = [
    "planning",
    "source_collecting",
    "source_verified",
    "claim_ready",
    "draft_allowed",
    "review_candidate",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip("*").strip()


def normalize_header(value: str) -> str:
    text = clean_cell(value).lower()
    compact = re.sub(r"\s+", "_", text)
    if "source_id" in compact or "source id" in text:
        return "source_id"
    if text.startswith("원본 자료명") or "source title" in text or text == "title":
        return "title"
    if "신뢰도" in text or "tier" in text or "reliability" in text:
        return "reliability_tier"
    if text == "status" or "readiness" in text:
        return "status"
    if "local path" in text or "로컬 보관 경로" in text or "url_or_path" in compact:
        return "url_or_path"
    if "claim_id" in compact or "claim id" in text:
        return "claim_id"
    if "classification" in compact or "분류" in text:
        return "claim_type"
    if "exact_quote_location" in compact or "quote_location" in compact or "page_number" in compact:
        return "exact_quote_location"
    if "source_ids" in compact or "source ids" in text or "주요 증거" in text:
        return "source_ids"
    return compact


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    headers: list[str] | None = None
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if headers is None:
            headers = [normalize_header(cell) for cell in cells]
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if headers and len(cells) == len(headers):
            rows.append({key: clean_cell(value) for key, value in zip(headers, cells)})
    return rows


def parse_source_record(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.match(r"\s*[-*]\s*\*\*([^*]+)\*\*\s*:\s*(.*)", line)
        if not match:
            match = re.match(r"\s*[-*]\s*`?([A-Za-z0-9_ -]+)`?\s*:\s*(.*)", line)
        if match:
            key = normalize_header(match.group(1))
            data[key] = clean_cell(match.group(2))
    return data


def source_records_by_id(project: Path) -> dict[str, Path]:
    records: dict[str, Path] = {}
    for path in (project / "references" / "source_records").glob("*.md"):
        data = parse_source_record(path)
        source_id = clean_cell(data.get("source_id", ""))
        if source_id:
            records[source_id] = path
    return records


BENCHMARK_MARKERS = [
    "Robinhood",
    "Fidelity",
    "Interactive Brokers",
    "IBKR",
    "Paxos",
]
BENCHMARK_CONTEXT = [
    "benchmark",
    "case",
    "precedent",
    "overseas",
    "global",
    "벤치마크",
    "선례",
    "사례",
    "해외",
    "글로벌",
]
BENCHMARK_EXCLUDE_TERMS = {
    "AI",
    "AML",
    "API",
    "CSV",
    "Fact",
    "HTML",
    "High",
    "Low",
    "Medium",
    "PDF",
    "PRD",
    "Strategy",
    "Track",
    "TOC",
    "URL",
    "VASP",
}


def source_record_section(text: str, heading_pattern: str) -> str:
    match = re.search(heading_pattern, text, flags=re.I)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"\n##\s+\d+\.", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def extract_benchmark_terms(text: str) -> set[str]:
    terms = {term for term in BENCHMARK_MARKERS if term in text}
    for line in text.splitlines():
        lowered = line.lower()
        if not any(marker.lower() in lowered for marker in BENCHMARK_CONTEXT):
            continue
        for match in re.findall(r"\b[A-Z][A-Za-z0-9&.-]{2,}(?:\s+[A-Z][A-Za-z0-9&.-]{2,}){0,2}\b", line):
            clean = match.strip()
            if clean not in BENCHMARK_EXCLUDE_TERMS:
                terms.add(clean)
    return terms


def benchmark_term_has_original_support(term: str, source_records: dict[str, Path]) -> bool:
    lowered_term = term.lower()
    for path in source_records.values():
        text = path.read_text(encoding="utf-8", errors="ignore")
        data = parse_source_record(path)
        exact_quotes = source_record_section(text, r"\n##\s+2\.\s*Exact Quotes")
        metadata_blob = " ".join(
            [
                data.get("title", ""),
                data.get("publisher", ""),
                data.get("url_or_path", ""),
                data.get("original_file_path", ""),
                data.get("original_path", ""),
                path.name,
            ]
        )
        if lowered_term in exact_quotes.lower() or lowered_term in metadata_blob.lower():
            return True
    return False


def ensure_stage_manifest(project: Path, report_id: str) -> Path:
    path = project / "project_state" / "report_stage_manifest.json"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "project": project.name,
            "report_id": report_id,
            "stage": "planning",
            "updated_at_kst": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
            "allowed_next_actions": [
                "create_or_update_report_prd",
                "create_detailed_toc",
                "collect_sources",
                "create_scaffold_only",
            ],
            "notes": "Draft prose beyond scaffold requires source and claim gates.",
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def stage_at_least(stage: str, required: str) -> bool:
    try:
        return STAGE_ORDER.index(stage) >= STAGE_ORDER.index(required)
    except ValueError:
        return False


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Preflight report workflow stage before drafting or delivery.")
    parser.add_argument("--project", required=True, help="Project folder name")
    parser.add_argument("--report-id", default="internal_review_report")
    parser.add_argument("--for-drafting", action="store_true", help="Require draft_allowed gate")
    parser.add_argument("--for-delivery", action="store_true", help="Require review_candidate gate")
    parser.add_argument("--strict-research", action="store_true", help="Require minimum source-record and data-artifact depth for substantial internal-review reports.")
    parser.add_argument("--init", action="store_true", help="Create stage manifest if missing")
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2

    manifest_path = ensure_stage_manifest(project, args.report_id) if args.init else project / "project_state" / "report_stage_manifest.json"
    errors: list[str] = []
    warnings: list[str] = []

    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        errors.append("missing report_stage_manifest.json")
    stage = str(manifest.get("stage", "unknown"))

    prds = list((project / "report_prd").glob("*.md"))
    tocs = list((project / "drafts").glob("*toc*.md"))
    inventory_rows = read_csv_rows(project / "references" / "reference_inventory.csv")
    source_rows = parse_markdown_table(project / "source_index" / "source_master_index.md")
    claim_rows = parse_markdown_table(project / "reports" / "report_claim_register.md")
    source_records = source_records_by_id(project)

    citable_sources = [
        row for row in source_rows
        if (row.get("status") == "report_citable" or row.get("source_readiness_status") == "report_citable")
    ]
    citable_claims = [row for row in claim_rows if row.get("status") == "report_citable"]

    if not prds:
        errors.append("missing report PRD under report_prd/")
    if not tocs:
        errors.append("missing detailed TOC under drafts/")
    if args.for_drafting:
        if not stage_at_least(stage, "draft_allowed"):
            errors.append(f"report stage is {stage}; draft prose beyond scaffold requires draft_allowed")
        if len(citable_sources) == 0:
            errors.append("no report_citable sources available for drafting")
        missing_records = [
            row.get("source_id", "")
            for row in citable_sources
            if row.get("source_id") not in source_records
        ]
        if missing_records:
            errors.append(
                "report_citable sources missing source_records: "
                + ", ".join(sorted(filter(None, missing_records)))
            )
        citable_source_ids = {row.get("source_id", "") for row in citable_sources}
        too_small_records = [
            source_id
            for source_id, record_path in source_records.items()
            if source_id in citable_source_ids and record_path.stat().st_size < 1024
        ]
        if too_small_records:
            errors.append(
                "source_records too small for report_citable use: "
                + ", ".join(sorted(too_small_records))
            )
        if len(citable_claims) == 0:
            errors.append("no report_citable claims available for drafting")
    if args.for_delivery and not stage_at_least(stage, "review_candidate"):
        errors.append(f"report stage is {stage}; delivery requires review_candidate")
    if len(inventory_rows) == 0:
        warnings.append("reference inventory has no rows; only scaffold/planning work should proceed")
    if args.strict_research:
        source_record_count = len(source_records)
        if source_record_count < 8:
            errors.append(f"strict research requires at least 8 source_records; found {source_record_count}")
        if len(citable_sources) < 8:
            errors.append(f"strict research requires at least 8 report_citable sources; found {len(citable_sources)}")
        external_or_public_rows = [
            row for row in inventory_rows
            if (row.get("material_origin") in {"external", "partner", "user_provided"} or row.get("visibility") == "public")
        ]
        if len(external_or_public_rows) < 6:
            errors.append(f"strict research requires at least 6 external/public inventoried originals; found {len(external_or_public_rows)}")
        data_files = [
            path for path in (project / "data_sources").glob("*")
            if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls", ".tsv"}
        ]
        if len(data_files) == 0:
            errors.append("strict research requires at least one CSV/XLSX under data_sources before delivery-stage report work")
        project_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for folder in ["reports", "drafts", "reports"]
            for path in (project / folder).glob("*.md")
        )
        project_text += "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (project / "reports").glob("*.html")
        )
        benchmark_terms = sorted(extract_benchmark_terms(project_text))
        missing_benchmark_terms = [
            term for term in benchmark_terms
            if not benchmark_term_has_original_support(term, source_records)
        ]
        if missing_benchmark_terms:
            errors.append(
                "strict research benchmark terms require original-backed source_records: "
                + ", ".join(missing_benchmark_terms)
            )
        fact_claims_missing_location = [
            row.get("claim_id", "")
            for row in citable_claims
            if "fact" in ((row.get("claim_type") or row.get("classification") or "").lower())
            and not row.get("exact_quote_location", "").strip()
        ]
        if fact_claims_missing_location:
            errors.append(
                "strict research fact claims require exact_quote_location/page/section/URL: "
                + ", ".join(sorted(filter(None, fact_claims_missing_location)))
            )
        citable_claims_missing_citation_type = [
            row.get("claim_id", "")
            for row in citable_claims
            if not (row.get("citation_type") or "").strip()
        ]
        if citable_claims_missing_citation_type:
            errors.append(
                "strict research report_citable claims require citation_type: "
                + ", ".join(sorted(filter(None, citable_claims_missing_citation_type)))
            )

    payload = {
        "project": project.name,
        "report_id": args.report_id,
        "stage": stage,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "report_prds": len(prds),
            "detailed_tocs": len(tocs),
            "inventory_rows": len(inventory_rows),
            "source_rows": len(source_rows),
            "report_citable_sources": len(citable_sources),
            "claim_rows": len(claim_rows),
            "report_citable_claims": len(citable_claims),
            "source_records": len(source_records),
        },
        "manifest_path": manifest_path.as_posix(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
