from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")

BENCHMARK_MARKERS = [
    "Robinhood",
    "Fidelity",
    "Interactive Brokers",
    "IBKR",
    "Paxos",
    "Webull",
    "Securitize",
    "Ondo",
    "Dinari",
    "Backed",
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
    "PDF",
    "PRD",
    "TOC",
    "Tier",
    "URL",
    "VASP",
}


def clean_cell(value: object) -> str:
    return str(value or "").strip().strip("`").strip("*").strip()


def normalize_header(value: str) -> str:
    text = clean_cell(value).lower()
    compact = re.sub(r"\s+", "_", text)
    if "source_id" in compact or "source id" in text:
        return "source_id"
    if "claim_id" in compact or "claim id" in text:
        return "claim_id"
    if "classification" in compact or "분류" in text:
        return "claim_type"
    if "exact_quote_location" in compact or "quote_location" in compact or "page_number" in compact:
        return "exact_quote_location"
    if "source_ids" in compact or "source ids" in text or "주요 증거" in text:
        return "source_ids"
    if text == "status" or "readiness" in text or "상태" in text:
        return "status"
    if "evidence_class" in compact:
        return "evidence_class"
    if "original_verified" in compact:
        return "original_verified"
    if "title" in compact or "자료명" in text:
        return "title"
    if "url_or_path" in compact or "local path" in text or "로컬 보관 경로" in text:
        return "url_or_path"
    return compact


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [{k: clean_cell(v) for k, v in row.items()} for row in csv.DictReader(f)]


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
            data[normalize_header(match.group(1))] = clean_cell(match.group(2))
    return data


def source_records_by_id(project: Path) -> dict[str, Path]:
    records: dict[str, Path] = {}
    for path in (project / "references" / "source_records").glob("*.md"):
        data = parse_source_record(path)
        source_id = clean_cell(data.get("source_id", ""))
        if source_id:
            records[source_id] = path
    return records


def source_record_section(text: str, heading_pattern: str) -> str:
    match = re.search(heading_pattern, text, flags=re.I)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"\n##\s+\d+\.", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def extract_benchmark_terms(text: str) -> set[str]:
    # Keep this conservative. Earlier versions treated any capitalized word near
    # "benchmark" as a named case, which let prompt/tool words such as
    # "Answer" or "Assumptions" masquerade as benchmark terms.
    return {term for term in BENCHMARK_MARKERS if term in text}


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


def project_text(project: Path) -> str:
    parts: list[str] = []
    for folder in ["report_prd", "drafts", "reports", "source_index", "benchmark_cases"]:
        base = project / folder
        if not base.exists():
            continue
        for suffix in ("*.md", "*.html"):
            for path in base.glob(suffix):
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts)


def load_manifest(project: Path) -> dict[str, object]:
    path = project / "project_state" / "report_stage_manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"stage": "invalid_manifest_json"}


def as_bool_yes(value: str) -> bool:
    return value.lower() in {"yes", "true", "y", "1", "original_verified"}


def find_ocr_citable(inventory_rows: list[dict[str, str]], citable_source_ids: set[str]) -> list[str]:
    offenders: list[str] = []
    for row in inventory_rows:
        source_id = row.get("source_id", "")
        if source_id not in citable_source_ids:
            continue
        ocr_status = row.get("ocr_status", "").lower()
        parse_status = row.get("parse_status", "").lower()
        if "needs" in ocr_status or "ocr" in parse_status and "need" in parse_status:
            offenders.append(source_id or row.get("reference_id", "unknown"))
    return offenders


def compute_gate(project: Path) -> dict[str, object]:
    manifest = load_manifest(project)
    manifest_stage = clean_cell(manifest.get("stage", "missing"))
    prds = list((project / "report_prd").glob("*.md"))
    tocs = list((project / "drafts").glob("*toc*.md"))
    source_plan_exists = any(
        path.exists()
        for folder in ["notes", "drafts"]
        for path in (project / folder).glob("*source*collection*plan*.md")
    )
    inventory_rows = read_csv_rows(project / "references" / "reference_inventory.csv")
    source_rows = parse_markdown_table(project / "source_index" / "source_master_index.md")
    claim_rows = parse_markdown_table(project / "reports" / "report_claim_register.md")
    source_records = source_records_by_id(project)
    reports = list((project / "reports").glob("*.html"))
    data_files = [
        path for path in (project / "data_sources").glob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls", ".tsv"}
    ]

    citable_sources = [
        row for row in source_rows
        if row.get("status") == "report_citable" or row.get("source_readiness_status") == "report_citable"
    ]
    citable_source_ids = {row.get("source_id", "") for row in citable_sources if row.get("source_id", "")}
    citable_claims = [row for row in claim_rows if row.get("status") == "report_citable"]

    blockers: list[str] = []
    warnings: list[str] = []
    not_tested: list[str] = []

    planning_gaps: list[str] = []
    if not prds:
        planning_gaps.append("report PRD has not been created yet")
    if not tocs:
        planning_gaps.append("detailed TOC has not been created yet")
    if not source_plan_exists and (prds or tocs):
        warnings.append("source collection plan not found; detailed TOC may still map evidence needs, but a separate plan is recommended for broad reports")

    missing_records = [
        row.get("source_id", "")
        for row in citable_sources
        if row.get("source_id", "") not in source_records
    ]
    if missing_records:
        blockers.append("report_citable sources missing source_records: " + ", ".join(sorted(filter(None, missing_records))))

    too_small_records = [
        source_id
        for source_id, record_path in source_records.items()
        if source_id in citable_source_ids and record_path.stat().st_size < 1024
    ]
    if too_small_records:
        blockers.append("report_citable source_records too small to audit: " + ", ".join(sorted(too_small_records)))

    ocr_citable = find_ocr_citable(inventory_rows, citable_source_ids)
    if ocr_citable:
        blockers.append("OCR-needed or unparsed sources marked report_citable: " + ", ".join(sorted(ocr_citable)))

    fact_claims_missing_location = [
        row.get("claim_id", "")
        for row in citable_claims
        if "fact" in row.get("claim_type", "").lower() and not row.get("exact_quote_location", "")
    ]
    if fact_claims_missing_location:
        blockers.append(
            "fact claims missing exact quote/page/section/URL location: "
            + ", ".join(sorted(filter(None, fact_claims_missing_location)))
        )

    benchmark_terms = sorted(extract_benchmark_terms(project_text(project)))
    missing_benchmarks = [
        term for term in benchmark_terms
        if not benchmark_term_has_original_support(term, source_records)
    ]
    if missing_benchmarks:
        blockers.append(
            "named benchmark terms lack original-backed source_records: "
            + ", ".join(missing_benchmarks)
        )

    external_or_public_rows = [
        row for row in inventory_rows
        if row.get("material_origin") in {"external", "partner", "user_provided"} or row.get("visibility") == "public"
    ]

    delivery_or_review_claimed = bool(reports) or manifest_stage in {"review_candidate", "internally_reviewable_draft", "final_candidate"}
    if delivery_or_review_claimed:
        if len(source_records) < 8:
            blockers.append(f"review-candidate gate requires at least 8 source_records for substantial reports; found {len(source_records)}")
        if len(citable_sources) < 8:
            blockers.append(f"review-candidate gate requires at least 8 report_citable sources for substantial reports; found {len(citable_sources)}")
        if len(external_or_public_rows) < 6:
            blockers.append(f"review-candidate gate requires at least 6 external/public inventoried originals for substantial reports; found {len(external_or_public_rows)}")

    if reports and len(data_files) == 0:
        warnings.append("report HTML exists but no CSV/XLSX data file was found under data_sources/")

    computed_gate = "planning"
    if prds and tocs:
        computed_gate = "planning_ready"
    if source_records or citable_sources or citable_claims:
        computed_gate = "evidence_mapping"
    if prds and tocs and citable_sources and citable_claims and not missing_records and not too_small_records and not ocr_citable:
        computed_gate = "writing_allowed"
    strict_ready = (
        len(source_records) >= 8
        and len(citable_sources) >= 8
        and len(external_or_public_rows) >= 6
        and len(data_files) >= 1
        and not blockers
    )
    if strict_ready:
        computed_gate = "review_candidate_possible"

    if manifest_stage in {"review_candidate", "internally_reviewable_draft", "final_candidate"} and computed_gate not in {"review_candidate_possible"}:
        blockers.append(
            f"stage manifest says {manifest_stage}, but computed gate is {computed_gate}; treat manifest as stale until blockers are resolved"
        )

    allowed_actions_by_gate = {
        "planning": [
            "create_or_update_report_prd",
            "create_or_update_detailed_toc",
            "create_source_collection_plan",
            "ask_and_log_clarifying_questions",
            "run_workspace_validation",
        ],
        "planning_ready": [
            "collect_user_provided_originals",
            "collect_external_originals_or_exact_urls",
            "create_source_records",
            "create_claim_register_rows",
            "create_data_source_files",
            "run_report_preflight_for_drafting",
        ],
        "evidence_mapping": [
            "repair_source_records_and_claim_locations",
            "collect_missing_external_originals",
            "resolve_OCR_or_mark_not_citable",
            "run_report_preflight_for_drafting",
        ],
        "writing_allowed": [
            "draft_report_sections_in_TOC_order",
            "create_footnotes_appendices_and_data_files",
            "write_executive_summary_last",
            "run_research_and_artifact_validation",
        ],
        "review_candidate_possible": [
            "prepare_internal_review_packet",
            "request_cross_thread_or_other_AI_audit",
            "record_residual_legal_business_risks",
        ],
    }

    blocked_actions = []
    if computed_gate in {"planning", "planning_ready", "evidence_mapping"}:
        blocked_actions.extend([
            "do_not_call_report_internally_reviewable",
            "do_not_write_final_recommendations",
            "do_not_treat_workspace_validation_as_report_quality",
        ])
    if computed_gate != "review_candidate_possible":
        blocked_actions.append("do_not_report_strict_delivery_as_passed")
    if blockers:
        blocked_actions.append("do_not_promote_report_stage_until_blockers_are_resolved")

    if blockers:
        effective_allowed_actions = [
            "repair_blockers_before_drafting_or_delivery",
            "collect_missing_original_sources",
            "repair_source_records_claim_locations_and_data_files",
            "rerun_report_gate_status_and_required_preflight",
        ]
    else:
        effective_allowed_actions = allowed_actions_by_gate.get(computed_gate, allowed_actions_by_gate["planning"])

    return {
        "project": project.name,
        "manifest_stage": manifest_stage,
        "computed_gate": "blocked" if blockers and computed_gate in {"writing_allowed", "review_candidate_possible"} else computed_gate,
        "computed_gate_before_blockers": computed_gate,
        "allowed_actions": effective_allowed_actions,
        "blocked_actions": sorted(set(blocked_actions)),
        "blockers": blockers,
        "warnings": warnings,
        "planning_gaps": planning_gaps,
        "not_tested": not_tested,
        "metrics": {
            "report_prds": len(prds),
            "detailed_tocs": len(tocs),
            "source_collection_plan_exists": source_plan_exists,
            "inventory_rows": len(inventory_rows),
            "external_or_public_inventory_rows": len(external_or_public_rows),
            "source_index_rows": len(source_rows),
            "report_citable_sources": len(citable_sources),
            "source_records": len(source_records),
            "claim_rows": len(claim_rows),
            "report_citable_claims": len(citable_claims),
            "report_html_files": len(reports),
            "data_files": len(data_files),
            "benchmark_terms_detected": benchmark_terms,
        },
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Report what actions are allowed or blocked for a project/report gate.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2

    payload = compute_gate(project)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
