from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
FIELDS = [
    "source_id",
    "file_name",
    "title",
    "official_url",
    "url",
    "publisher",
    "accessed_at_kst",
    "url_status",
    "source_locator",
    "use_level",
    "claim_support_type",
    "needs_user_file",
    "user_file_request_id",
    "notes",
]

URL_STATUSES = {"not_checked", "unverified", "ok", "verified", "200", "exact_url_verified", "failed", "blocked", "unknown"}
USE_LEVELS = {
    "lead",
    "lead_only",
    "not_collected",
    "collection_blocked",
    "url_only",
    "quote_verified",
    "report_citable",
}
CLAIM_SUPPORT_TYPES = {"none", "direct_quote", "paraphrase", "data_based", "inference", "analysis_context"}
YES_NO = {"yes", "no", "unknown"}


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_status(value: str, default: str) -> str:
    return (value or default).strip().lower()


def validate_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    official_url = (args.official_url or args.url or "").strip()
    if not args.source_id.strip():
        errors.append("--source-id is required")
    if not official_url:
        errors.append("--official-url or --url is required")
    if normalize_status(args.url_status, "not_checked") not in URL_STATUSES:
        errors.append("--url-status is invalid")
    if normalize_status(args.use_level, "lead") not in USE_LEVELS:
        errors.append("--use-level is invalid")
    if normalize_status(args.claim_support_type, "none") not in CLAIM_SUPPORT_TYPES:
        errors.append("--claim-support-type is invalid")
    if normalize_status(args.needs_user_file, "no") not in YES_NO:
        errors.append("--needs-user-file is invalid")
    return errors


def upsert_link(args: argparse.Namespace) -> dict[str, object]:
    errors = validate_args(args)
    if errors:
        return {"errors": errors}

    project = PROJECT_ROOT / args.project
    if not project.exists():
        return {"errors": [f"project not found: {args.project}"]}

    register = project / "references" / "source_link_register.csv"
    rows = read_rows(register)
    source_id = args.source_id.strip()
    official_url = (args.official_url or args.url or "").strip()
    row = {
        "source_id": source_id,
        "file_name": args.file_name.strip(),
        "title": args.title.strip(),
        "official_url": official_url,
        "url": official_url,
        "publisher": args.publisher.strip(),
        "accessed_at_kst": args.accessed_at_kst.strip() or now_kst(),
        "url_status": normalize_status(args.url_status, "not_checked"),
        "source_locator": args.source_locator.strip(),
        "use_level": normalize_status(args.use_level, "lead"),
        "claim_support_type": normalize_status(args.claim_support_type, "none"),
        "needs_user_file": normalize_status(args.needs_user_file, "no"),
        "user_file_request_id": args.user_file_request_id.strip(),
        "notes": args.notes.strip(),
    }
    replaced = False
    for index, existing in enumerate(rows):
        if existing.get("source_id", "").strip() == source_id:
            rows[index] = {**existing, **row}
            replaced = True
            break
    if not replaced:
        rows.append(row)
    if not args.dry_run:
        write_rows(register, rows)
    return {
        "project": args.project,
        "register": register.relative_to(project).as_posix(),
        "source_id": source_id,
        "action": "updated" if replaced else "created",
        "dry_run": args.dry_run,
        "row": row,
        "notes": [
            "A source_link_register row records exact official links and locator status; it does not make the source report_citable by itself.",
            "Do not attempt AI downloads for external references. Use report_citable only when an exact URL, source locator, and source record support reader-facing use.",
            "If file-level evidence is needed, set needs_user_file=yes and add the request to references/user_requested_materials.md.",
        ],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Add or update a source_link_register.csv row for exact official URL reference status.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--official-url", default="", help="Exact official URL. Preferred for new projects.")
    parser.add_argument("--url", default="", help="Legacy alias for --official-url.")
    parser.add_argument("--file-name", default="", help="Official file or document name when known.")
    parser.add_argument("--title", default="")
    parser.add_argument("--publisher", default="")
    parser.add_argument("--accessed-at-kst", default="")
    parser.add_argument("--url-status", default="not_checked", choices=sorted(URL_STATUSES))
    parser.add_argument("--source-locator", default="", help="Page, section, article, table, paragraph, or URL anchor used for quote/claim audit.")
    parser.add_argument("--use-level", default="lead", choices=sorted(USE_LEVELS))
    parser.add_argument("--claim-support-type", default="none", choices=sorted(CLAIM_SUPPORT_TYPES))
    parser.add_argument("--needs-user-file", default="no", choices=sorted(YES_NO))
    parser.add_argument("--user-file-request-id", default="")
    parser.add_argument("--download-status", default="", help="Deprecated legacy input; ignored for new link-first registers.")
    parser.add_argument("--capture-status", default="", help="Deprecated legacy input; ignored for new link-first registers.")
    parser.add_argument("--original-path", default="", help="Deprecated legacy input; use user_requested_materials.md for needed files.")
    parser.add_argument("--capture-path", default="", help="Deprecated legacy input; not written by the normal link-first workflow.")
    parser.add_argument("--notes", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = upsert_link(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
