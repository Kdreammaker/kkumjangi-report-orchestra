from __future__ import annotations

import argparse
import csv
import html
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from record_source_link import FIELDS, read_rows, write_rows
from validate_research_integrity import (
    PROJECT_ROOT,
    clean_md_link,
    is_generic_url,
    is_weak_exact_quote,
    source_metadata_mismatch,
    parse_markdown_table,
    quote_candidates,
    strong_quote_candidates,
    source_record_section,
    source_records_by_id,
    text_is_too_generic_for_quote_verification,
    text_from_evidence,
)


def now_kst_compact() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d_%H%M%S")


def now_kst_label() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")


def source_index_statuses(project: Path) -> dict[str, str]:
    rows = parse_markdown_table(project / "source_index" / "source_master_index.md")
    result: dict[str, str] = {}
    for row in rows:
        source_id = (row.get("source_id") or "").strip()
        if source_id:
            result[source_id] = (row.get("status") or "").strip()
    return result


def read_link_register(project: Path) -> dict[str, dict[str, str]]:
    path = project / "references" / "source_link_register.csv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            (row.get("source_id") or "").strip(): {str(k or "").strip(): str(v or "").strip() for k, v in row.items()}
            for row in csv.DictReader(handle)
            if (row.get("source_id") or "").strip()
        }


def decode_text(raw: bytes, content_type: str) -> str:
    charset_match = re.search(r"charset=([^;\s]+)", content_type, flags=re.I)
    encodings = []
    if charset_match:
        encodings.append(charset_match.group(1).strip('"'))
    encodings.extend(["utf-8", "cp949", "euc-kr", "latin-1"])
    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def html_to_text(value: str) -> str:
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", value)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def pdf_to_text(raw: bytes) -> tuple[str, str]:
    try:
        import pypdf  # type: ignore[import-untyped]

        reader = pypdf.PdfReader(io.BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages), f"pdf_pages={len(reader.pages)}"
    except Exception as exc:
        return "", f"pdf_text_extract_failed:{type(exc).__name__}: {exc}"


def fetch_url_text(url: str, timeout: int = 12) -> tuple[bool, str, dict[str, str]]:
    parsed = urllib.parse.urlsplit(url)
    safe_path = urllib.parse.quote(parsed.path, safe="/%")
    safe_query = urllib.parse.quote_plus(parsed.query, safe="=&%")
    safe_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, safe_path, safe_query, parsed.fragment))
    request = urllib.request.Request(safe_url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = str(getattr(response, "status", 200))
            content_type = response.headers.get("Content-Type", "")
            raw = response.read()
    except Exception as exc:
        return False, "", {"error": f"{type(exc).__name__}: {exc}"}

    lowered_type = content_type.lower()
    lowered_path = parsed.path.lower()
    if "application/pdf" in lowered_type or lowered_path.endswith(".pdf"):
        text, detail = pdf_to_text(raw)
        return bool(text.strip()), text, {
            "status": status,
            "content_type": content_type,
            "bytes": str(len(raw)),
            "extract_detail": detail,
        }
    decoded = decode_text(raw, content_type)
    if "html" in lowered_type or re.search(r"<html|<!doctype", decoded[:500], flags=re.I):
        text = html_to_text(decoded)
    else:
        text = decoded
    return bool(text.strip()), text, {
        "status": status,
        "content_type": content_type,
        "bytes": str(len(raw)),
        "extract_detail": "text_or_html",
    }


def source_capture_path(project: Path, source_id: str) -> Path:
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", source_id).strip("_") or "source"
    return project / "evidence" / "web_captures" / f"{safe_id}_{now_kst_compact()}.txt"


def write_capture(path: Path, source_id: str, url: str, meta: dict[str, str], text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        f"source_id: {source_id}",
        f"url: {url}",
        f"accessed_at_kst: {now_kst_label()}",
        f"http_status: {meta.get('status', '')}",
        f"content_type: {meta.get('content_type', '')}",
        f"bytes: {meta.get('bytes', '')}",
        f"extract_detail: {meta.get('extract_detail', '')}",
        "",
        "----- extracted text -----",
        "",
    ]
    path.write_text("\n".join(header) + text, encoding="utf-8", newline="\n")


def upsert_register_capture(project: Path, source_id: str, url: str, capture_path: Path, meta: dict[str, str]) -> None:
    register = project / "references" / "source_link_register.csv"
    rows = read_rows(register)
    rel_capture = capture_path.relative_to(project).as_posix()
    updated = {
        "source_id": source_id,
        "url": url,
        "accessed_at_kst": now_kst_label(),
        "url_status": meta.get("status") or "verified",
        "download_status": "not_attempted",
        "capture_status": "captured",
        "use_level": "quote_verified",
        "capture_path": rel_capture,
        "notes": "exact quotes verified against fetched URL capture",
    }
    replaced = False
    for index, row in enumerate(rows):
        if row.get("source_id", "").strip() == source_id:
            rows[index] = {**row, **updated}
            replaced = True
            break
    if not replaced:
        rows.append({field: updated.get(field, "") for field in FIELDS})
    write_rows(register, rows)


def source_url(project: Path, source_id: str, record: dict[str, str], link_rows: dict[str, dict[str, str]]) -> str:
    link_url = link_rows.get(source_id, {}).get("url", "").strip()
    if link_url:
        return link_url
    return clean_md_link(record.get("url_or_path", ""))


def verify_project(args: argparse.Namespace) -> dict[str, object]:
    project = PROJECT_ROOT / args.project
    if not project.exists():
        return {"project": args.project, "errors": [f"project not found: {args.project}"], "results": []}

    records = source_records_by_id(project)
    statuses = source_index_statuses(project)
    link_rows = read_link_register(project)
    errors: list[str] = []
    warnings: list[str] = []
    results: list[dict[str, object]] = []
    wanted = {args.source_id} if args.source_id else set(records)

    for source_id in sorted(wanted):
        entry = records.get(source_id)
        if not entry:
            errors.append(f"{source_id}: source record not found")
            continue
        record_path, record = entry
        status = statuses.get(source_id) or record.get("status", "")
        readiness = record.get("source_readiness_status", "")
        if status != "report_citable" and readiness not in {"report_citable", "quote_verified"}:
            continue
        url = source_url(project, source_id, record, link_rows)
        if not re.match(r"https?://", url or ""):
            continue
        if is_generic_url(url):
            errors.append(f"{source_id}: generic URL cannot be quote-verified: {url}")
            continue
        mismatch = source_metadata_mismatch(
            record.get("title", ""),
            record.get("publisher", ""),
            url,
        )
        if mismatch:
            errors.append(f"{source_id}: source title/publisher/url mismatch ({mismatch}): {url}")
            results.append({"source_id": source_id, "url": url, "verified": False, "reason": "metadata_mismatch"})
            continue
        record_text = record_path.read_text(encoding="utf-8", errors="ignore")
        quote_section = source_record_section(record_text, r"\n##\s+2\.\s*Exact Quotes")
        raw_quotes = quote_candidates(quote_section)
        weak_quotes = [quote for quote in raw_quotes if is_weak_exact_quote(quote)]
        quotes = strong_quote_candidates(quote_section)
        if weak_quotes:
            errors.append(f"{source_id}: weak/generic Exact Quotes cannot be quote-verified")
            results.append(
                {
                    "source_id": source_id,
                    "url": url,
                    "verified": False,
                    "quote_candidates": len(raw_quotes),
                    "weak_quotes": len(weak_quotes),
                    "reason": "weak_exact_quotes",
                }
            )
            continue
        if not quotes:
            errors.append(f"{source_id}: no Exact Quotes candidates to verify")
            continue

        ok, fetched_text, meta = fetch_url_text(url, timeout=args.timeout)
        if not ok:
            errors.append(f"{source_id}: URL fetch/text extraction failed ({meta.get('error') or meta.get('extract_detail')})")
            results.append({"source_id": source_id, "url": url, "verified": False, "meta": meta})
            continue
        if text_is_too_generic_for_quote_verification(fetched_text):
            errors.append(f"{source_id}: fetched text is too short or generic for quote verification")
            results.append({"source_id": source_id, "url": url, "verified": False, "meta": meta, "reason": "generic_fetched_text"})
            continue
        missing = [quote for quote in quotes if quote not in fetched_text]
        capture = ""
        if args.write_capture:
            capture_path = source_capture_path(project, source_id)
            write_capture(capture_path, source_id, url, meta, fetched_text)
            capture = capture_path.relative_to(project).as_posix()
            if args.update_register and not missing:
                upsert_register_capture(project, source_id, url, capture_path, meta)
        if missing:
            errors.append(f"{source_id}: {len(missing)} Exact Quotes not found in fetched URL text")
        results.append(
            {
                "source_id": source_id,
                "url": url,
                "verified": not missing,
                "quote_candidates": len(quotes),
                "missing_quotes": len(missing),
                "capture_path": capture,
                "meta": meta,
            }
        )

    if not results and not errors:
        warnings.append("no report-citable HTTP(S) URL sources found to verify")
    return {
        "project": args.project,
        "errors": errors,
        "warnings": warnings,
        "results": results,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Fetch URL-only report sources and verify Exact Quotes against fetched text.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--source-id", default="")
    parser.add_argument("--write-capture", action="store_true", help="Save fetched text under evidence/web_captures/.")
    parser.add_argument("--update-register", action="store_true", help="When quotes match, update source_link_register.csv with capture_path and use_level=quote_verified.")
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args()

    payload = verify_project(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
