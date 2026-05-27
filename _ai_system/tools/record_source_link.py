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
    "url",
    "publisher",
    "accessed_at_kst",
    "url_status",
    "download_status",
    "capture_status",
    "use_level",
    "original_path",
    "capture_path",
    "notes",
]

URL_STATUSES = {"unverified", "ok", "verified", "200", "exact_url_verified", "failed", "blocked", "unknown"}
DOWNLOAD_STATUSES = {"not_attempted", "downloaded", "ok", "downloaded_original", "failed", "blocked"}
CAPTURE_STATUSES = {"not_attempted", "captured", "ok", "captured_html", "failed", "blocked"}
USE_LEVELS = {
    "lead",
    "not_collected",
    "collection_blocked",
    "url_only",
    "quote_verified",
    "report_citable",
}


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
    if not args.source_id.strip():
        errors.append("--source-id is required")
    if not args.url.strip():
        errors.append("--url is required")
    if normalize_status(args.url_status, "unverified") not in URL_STATUSES:
        errors.append("--url-status is invalid")
    if normalize_status(args.download_status, "not_attempted") not in DOWNLOAD_STATUSES:
        errors.append("--download-status is invalid")
    if normalize_status(args.capture_status, "not_attempted") not in CAPTURE_STATUSES:
        errors.append("--capture-status is invalid")
    if normalize_status(args.use_level, "lead") not in USE_LEVELS:
        errors.append("--use-level is invalid")
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
    row = {
        "source_id": source_id,
        "file_name": args.file_name.strip(),
        "title": args.title.strip(),
        "url": args.url.strip(),
        "publisher": args.publisher.strip(),
        "accessed_at_kst": args.accessed_at_kst.strip() or now_kst(),
        "url_status": normalize_status(args.url_status, "unverified"),
        "download_status": normalize_status(args.download_status, "not_attempted"),
        "capture_status": normalize_status(args.capture_status, "not_attempted"),
        "use_level": normalize_status(args.use_level, "lead"),
        "original_path": args.original_path.strip(),
        "capture_path": args.capture_path.strip(),
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
            "A source_link_register row records collection status; it does not make the source report_citable by itself.",
            "Use report_citable only when an exact URL and quote/location are verifiable; add user-requested files separately when file-level evidence is needed.",
        ],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Add or update a source_link_register.csv row for URL-only or external source collection status.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--file-name", default="", help="Official file or document name when known.")
    parser.add_argument("--title", default="")
    parser.add_argument("--publisher", default="")
    parser.add_argument("--accessed-at-kst", default="")
    parser.add_argument("--url-status", default="unverified", choices=sorted(URL_STATUSES))
    parser.add_argument("--download-status", default="not_attempted", choices=sorted(DOWNLOAD_STATUSES))
    parser.add_argument("--capture-status", default="not_attempted", choices=sorted(CAPTURE_STATUSES))
    parser.add_argument("--use-level", default="lead", choices=sorted(USE_LEVELS))
    parser.add_argument("--original-path", default="")
    parser.add_argument("--capture-path", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = upsert_link(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
