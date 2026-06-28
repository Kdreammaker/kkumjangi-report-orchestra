from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# PDF authenticity thresholds
# ---------------------------------------------------------------------------
# Real PDFs are almost always larger than 4 KB. Shell / placeholder PDFs
# created solely to satisfy path-existence checks are typically < 1 KB.
PDF_MIN_GENUINE_BYTES = 4096
# Comment strings that appear in AI-generated placeholder PDFs.
DUMMY_PDF_MARKERS = [
    b"% Dummy PDF",
    b"% Placeholder PDF",
    b"% AI-generated",
    b"research integrity verification",
    b"Used for Benchmark",
]
# Heading-style patterns in the first 300 bytes of a .txt file indicate
# an AI-authored summary rather than a verbatim PDF extraction.
AI_SUMMARY_HEADING_RE = re.compile(
    r"^\s*\[\s*[A-Z][A-Za-z0-9 ]{4,}\s*\]",
    re.MULTILINE,
)


PROJECT_ROOT = Path("00_사용자_작업공간")
SOURCE_READINESS_GOOD = {"claim_ready", "report_citable", "quote_verified"}
REPORT_CITABLE = {"report_citable", "quote_verified"}
REPORT_USE_STATUSES = {"claim_ready", "report_citable", "quote_verified"}
GENERIC_URL_HOSTS = {
    "https://www.fsc.go.kr",
    "https://fsc.go.kr",
    "https://www.fss.or.kr",
    "https://fss.or.kr",
    "https://www.law.go.kr",
    "https://law.go.kr",
    "https://www.samsungpop.com",
    "https://samsungpop.com",
}
ORIGINAL_CLASSES = {
    "original_official",
    "original_commercial",
    "original_secondary",
    "captured_webpage",
}
DERIVATIVE_CLASSES = {
    "ai_working_summary",
    "analysis_note",
    "working_translation",
    "unknown_origin",
}
SUSPICIOUS_TONE = [
    "완벽히",
    "완벽하게",
    "무력화",
    "완전 분쇄",
    "원천 차단",
    "무조건",
    "최고 수준",
    "압도적",
    "전 세계에 입증",
    "합법성 확보",
    "완전히 증명",
    "무결한 최종",
]
SUMMARY_MARKERS = [
    "요약",
    "분석",
    "핵심 요지",
    "업무상 해석",
    "AI",
    "정리",
]
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
MIN_EXACT_QUOTE_CHARS = 18
GENERIC_CAPTURE_TEXT_PATTERNS = [
    r"^\s*국가법령정보센터\s*\|\s*법령\s*국가법령정보센터\s*법령\s*$",
    r"^\s*국가법령정보센터\s*\|\s*법령\s*$",
    r"^\s*홈\s*>\s*",
]
GENERIC_QUOTE_FRAGMENTS = {
    "국가법령정보센터",
    "법령",
    "홈페이지",
    "보도자료",
    "정책자료",
    "자료실",
    "메인",
}
LAW_PORTAL_HOSTS = {"law.go.kr", "www.law.go.kr"}
LAW_TITLE_TERMS = ("법", "법률", "시행령", "시행규칙", "규칙", "고시", "예규", "조례")
NON_LAW_DOCUMENT_TERMS = (
    "보도자료",
    "설명자료",
    "공약",
    "공약집",
    "정책공약",
    "실태조사",
    "조사 결과",
    "보고서",
    "백서",
    "가이드라인",
    "컨설팅",
    "자료집",
    "발표",
    "간담회",
)
NON_LAW_PUBLISHER_TERMS = ("금융위원회", "금감원", "금융감독원", "개인정보보호위원회", "국민의힘", "더불어민주당", "정책위원회")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip("*").strip()


def normalize_header(value: str) -> str:
    text = clean_cell(value).lower()
    compact = re.sub(r"\s+", "_", text)
    if "source_id" in compact or "source id" in text:
        return "source_id"
    if "source_ids" in compact or "source ids" in text or "주요 증거" in text:
        return "source_ids"
    if text.startswith("원본 자료명") or "source title" in text or text == "title":
        return "title"
    if "발행" in text or "publisher" in text:
        return "publisher"
    if "신뢰도" in text or "tier" in text or "reliability" in text:
        return "reliability_tier"
    if text == "status" or "readiness" in text:
        return "status"
    if "capture_path" in compact or "capture path" in text:
        return "capture_path"
    if "local_original_path" in compact or "original_file_path" in compact or "original path" in text or "original_path" in compact:
        return "local_original_path"
    if "local path" in text or "로컬 보관 경로" in text or "url_or_path" in compact:
        return "url_or_path"
    if text == "official_url":
        return "url"
    if "source_locator" in compact:
        return "source_locator"
    if "claim_id" in compact or "claim id" in text:
        return "claim_id"
    if "claim_type" in compact or "주장 유형" in text or text == "type":
        return "claim_type"
    if "classification" in compact or "분류" in text:
        return "claim_type"
    if "evidence_class" in compact:
        return "evidence_class"
    if "original_verified" in compact:
        return "original_verified"
    if "exact_quote_location" in compact:
        return "exact_quote_location"
    if "report_use_allowed" in compact:
        return "report_use_allowed"
    return compact


def iter_projects(root: Path) -> Iterable[Path]:
    if not PROJECT_ROOT.exists():
        return []
    return sorted(p for p in PROJECT_ROOT.iterdir() if p.is_dir())


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    lines = [line.strip() for line in read_text(path).splitlines()]
    headers: list[str] | None = None
    for line in lines:
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
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
    for line in read_text(path).splitlines():
        match = re.match(r"\s*[-*]\s*\*\*([^*]+)\*\*\s*:\s*(.*)", line)
        if not match:
            match = re.match(r"\s*[-*]\s*`?([A-Za-z0-9_ -]+)`?\s*:\s*(.*)", line)
        if match:
            key = normalize_header(match.group(1))
            value = clean_cell(match.group(2))
            data[key] = value
    return data


def clean_md_link(value: str) -> str:
    match = re.search(r"\]\(([^)]+)\)", value)
    if match:
        return match.group(1)
    return value.strip("` ")


def is_generic_url(value: str) -> bool:
    cleaned = value.rstrip("/").strip()
    if cleaned in GENERIC_URL_HOSTS:
        return True
    # Generic homepages or search portals are not enough for report citation.
    return bool(re.match(r"^https?://[^/]+/?(?:#.*)?$", value.strip()))


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def is_weak_exact_quote(value: str) -> bool:
    text = compact_text(value).strip('"').strip("'")
    if len(text) < MIN_EXACT_QUOTE_CHARS:
        return True
    if text in GENERIC_QUOTE_FRAGMENTS:
        return True
    if any(re.fullmatch(pattern, text, flags=re.I) for pattern in GENERIC_CAPTURE_TEXT_PATTERNS):
        return True
    # A quote should normally contain a source-specific noun, clause, number, or sentence.
    if len(set(text)) <= 6:
        return True
    return False


def text_is_too_generic_for_quote_verification(text: str) -> bool:
    body = compact_text(text)
    if len(body) < 80:
        return True
    return any(re.fullmatch(pattern, body, flags=re.I) for pattern in GENERIC_CAPTURE_TEXT_PATTERNS)


def source_metadata_mismatch(title: str, publisher: str, url: str) -> str:
    """Catch obvious source ledger mismatches before quote verification.

    This is deliberately conservative: it blocks cases where a non-law document
    such as a press release, manifesto, survey, or policy paper points to a law
    portal page merely because that page returns HTTP 200.
    """
    if not re.match(r"https?://", url or ""):
        return ""
    parsed = urllib.parse.urlsplit(url)
    host = parsed.netloc.lower()
    normalized_title = compact_text(title)
    normalized_publisher = compact_text(publisher)
    title_is_law = any(term in normalized_title for term in LAW_TITLE_TERMS)
    title_is_non_law_doc = any(term in normalized_title for term in NON_LAW_DOCUMENT_TERMS)
    publisher_is_non_law = any(term in normalized_publisher for term in NON_LAW_PUBLISHER_TERMS)
    if host in LAW_PORTAL_HOSTS and title_is_non_law_doc and not title_is_law:
        return "non-law document title points to law.go.kr statute portal"
    if host in LAW_PORTAL_HOSTS and publisher_is_non_law and not title_is_law:
        return "non-law publisher/title points to law.go.kr statute portal"
    return ""


def url_status_ok(url: str, timeout: int = 8) -> tuple[bool, str]:
    parsed = urllib.parse.urlsplit(url)
    safe_path = urllib.parse.quote(parsed.path, safe="/%")
    safe_query = urllib.parse.quote_plus(parsed.query, safe="=&%")
    safe_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, safe_path, safe_query, parsed.fragment))
    request = urllib.request.Request(safe_url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            return status < 400, f"status={status}"
    except urllib.error.HTTPError as exc:
        return False, f"status={exc.code}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def likely_source_file_matches(source_id: str, title: str, url_or_path: str) -> bool:
    """Catch obvious synthetic source ids pointing at unrelated local files."""
    lowered = " ".join([source_id, title, Path(url_or_path).name]).lower()
    red_flags = {
        "goldman": ["goldman"],
        "robinhood": ["robinhood", "sec", "10-k", "10k"],
        "samsung": ["samsung", "삼성", "bithumb", "빗썸"],
        "regulator": ["regulator", "agency", "authority", "감독기관", "규제기관", "실태조사"],
    }
    for marker, accepted in red_flags.items():
        if marker in source_id.lower():
            return any(token in lowered for token in accepted)
    return True


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def source_records_by_id(project: Path) -> dict[str, tuple[Path, dict[str, str]]]:
    records: dict[str, tuple[Path, dict[str, str]]] = {}
    for path in (project / "references" / "source_records").glob("*.md"):
        data = parse_source_record(path)
        source_id = clean_cell(data.get("source_id", ""))
        if source_id:
            records[source_id] = (path, data)
    return records


def source_record_section(text: str, heading_pattern: str) -> str:
    """Return one markdown section so benchmark terms in analysis do not masquerade as original proof."""
    match = re.search(heading_pattern, text, flags=re.I)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"\n##\s+\d+\.", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def quote_candidates(section: str) -> list[str]:
    candidates: list[str] = []
    for raw in section.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*>\d.\s]+", "", line).strip().strip('"').strip("'")
        if line:
            candidates.append(line)
    return candidates


def strong_quote_candidates(section: str) -> list[str]:
    return [quote for quote in quote_candidates(section) if not is_weak_exact_quote(quote)]


def resolve_project_path(project: Path, value: str) -> Path | None:
    value = clean_md_link(value)
    if not value or re.match(r"https?://", value):
        return None
    candidates = [project / value, project.parent / value, Path(value)]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return project / value


def local_evidence_paths(project: Path, record: dict[str, str], fallback_url_or_path: str) -> list[Path]:
    values = [
        record.get("local_original_path", ""),
        record.get("capture_path", ""),
        record.get("url_or_path", ""),
        fallback_url_or_path,
    ]
    paths: list[Path] = []
    for value in values:
        path = resolve_project_path(project, value)
        if path and path.exists() and path.is_file():
            paths.append(path)
    # Preserve order and remove duplicates.
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def append_link_register_evidence(project: Path, paths: list[Path], link_row: dict[str, str]) -> list[Path]:
    values = [
        link_row.get("original_path", ""),
        link_row.get("capture_path", ""),
    ]
    combined = list(paths)
    seen = {p.resolve() for p in combined if p.exists()}
    for value in values:
        path = resolve_project_path(project, value)
        if path and path.exists() and path.is_file() and path.resolve() not in seen:
            combined.append(path)
            seen.add(path.resolve())
    return combined


def text_from_evidence(path: Path) -> str:
    if path.suffix.lower() in {".txt", ".md", ".html", ".htm", ".csv"}:
        return read_text(path)
    return ""


PROMPT_OR_TOOL_TOKENS = {
    "Antigravity",
    "Implementation Plan",
    "Assumptions",
    "Answer",
    "Wake-up timer",
    "Auto-proceeded",
}

INTERNAL_QUOTE_TOKEN_RE = re.compile(
    r"\b(?:CLAIM|DATA|SOURCES|SOURCE|C\d{2,4}|claim-\d{2,4}|source_id|claim_id)\b",
    re.I,
)


def extract_benchmark_terms(text: str) -> set[str]:
    """Find likely named benchmark cases without making the rule Project-01-specific."""
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


def benchmark_term_has_original_support(term: str, records: dict[str, tuple[Path, dict[str, str]]]) -> bool:
    """Require a benchmark term to appear in a source's original evidence, not only in source-index titles."""
    lowered_term = term.lower()
    for path, data in records.values():
        record_text = read_text(path)
        exact_quotes = source_record_section(record_text, r"\n##\s+2\.\s*Exact Quotes")
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


def inventory_by_source(project: Path) -> dict[str, dict[str, str]]:
    inventory = project / "references" / "reference_inventory.csv"
    result: dict[str, dict[str, str]] = {}
    if not inventory.exists():
        return result
    with inventory.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            source_id = (row.get("source_id") or "").strip()
            if source_id:
                result[source_id] = row
    return result


def source_link_register_by_source(project: Path) -> dict[str, dict[str, str]]:
    register = project / "references" / "source_link_register.csv"
    result: dict[str, dict[str, str]] = {}
    if not register.exists():
        return result
    with register.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            source_id = (row.get("source_id") or "").strip()
            if source_id:
                normalized = {normalize_header(str(k or "").strip()): str(v or "").strip() for k, v in row.items()}
                if not normalized.get("url") and row.get("official_url"):
                    normalized["url"] = str(row.get("official_url") or "").strip()
                result[source_id] = normalized
    return result


def inspect_original_file(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "missing"
    if path.suffix.lower() != ".txt":
        return True, "non_txt_original"
    if "received_originals" in path.parts and path.stat().st_size < 1024:
        return False, f"received_original_txt_too_small_{path.stat().st_size}_bytes"
    text = read_text(path)[:1200]
    marker_hits = sum(1 for marker in SUMMARY_MARKERS if marker in text)
    has_url = bool(re.search(r"https?://", text))
    has_article_marker = bool(re.search(r"(제\d+조|Article\s+\d+|Form\s+10-K|SEC|regulator|agency|authority|위원회|부처|기관)", text, flags=re.I))
    if marker_hits >= 2 and not has_url:
        return False, "txt_looks_like_summary_without_url"
    if "출처:" in text and "요약" in text and not has_url:
        return False, "txt_looks_like_rewritten_source_note"
    if has_article_marker and has_url:
        return True, "txt_with_source_markers_and_url"
    return False, "txt_requires_manual_original_check"


# ---------------------------------------------------------------------------
# New: PDF / evidence authenticity helpers
# ---------------------------------------------------------------------------

def pdf_is_genuine(path: Path) -> tuple[bool, str]:
    """Return (genuine, reason).

    A PDF is considered NOT genuine if any of:
    - file size < PDF_MIN_GENUINE_BYTES (4 KB)
    - first 4 KB of raw bytes contain a known dummy-marker string
    - pypdf (if available) raises PdfReadError when trying to open it
    """
    if not path.exists():
        return False, "file_missing"
    size = path.stat().st_size
    if size < PDF_MIN_GENUINE_BYTES:
        return False, f"pdf_too_small_{size}_bytes"
    try:
        raw = path.read_bytes()[:4096]
    except OSError:
        return False, "pdf_unreadable"
    for marker in DUMMY_PDF_MARKERS:
        if marker in raw:
            return False, f"dummy_marker_found: {marker.decode('ascii', 'replace')}"
    # Try pypdf if available; failure means the file is a malformed placeholder.
    try:
        import pypdf  # type: ignore[import-untyped]
        r = pypdf.PdfReader(path)
        _ = len(r.pages)  # triggers full parse
    except Exception as exc:
        return False, f"pypdf_parse_error: {exc}"
    return True, "ok"


def evidence_txt_is_ai_summary(path: Path) -> bool:
    """Return True if a .txt evidence file looks like an AI-authored placeholder
    rather than a verbatim PDF extraction.

    Heuristic: the first 300 bytes contain bracket-headed section labels
    (e.g. "[Dinari Whitepaper Overview]") which are a telltale pattern of
    AI-generated stub text rather than raw PDF text extraction.
    """
    if not path.exists() or path.suffix.lower() != ".txt":
        return False
    try:
        head = path.read_bytes()[:300].decode("utf-8", "replace")
    except OSError:
        return False
    return bool(AI_SUMMARY_HEADING_RE.search(head))


def quote_found_in_genuine_evidence(quote: str, evidence_paths: list[Path]) -> bool:
    """Return True only if the quote text appears verbatim in a non-AI-summary
    evidence file.  AI-authored .txt stubs are excluded from the search so that
    a quote planted in a stub cannot satisfy the check.
    """
    for path in evidence_paths:
        if evidence_txt_is_ai_summary(path):
            continue  # skip AI-authored stubs
        text = text_from_evidence(path)
        if quote in text:
            return True
    return False


def validate_project(project: Path, check_urls: bool = False) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    source_index = project / "source_index" / "source_master_index.md"
    claim_register = project / "reports" / "report_claim_register.md"
    records = source_records_by_id(project)
    inventory = inventory_by_source(project)
    link_register = source_link_register_by_source(project)

    source_rows = parse_markdown_table(source_index)
    source_ids = set()
    for row in source_rows:
        source_id = clean_cell(row.get("source_id", ""))
        if not source_id:
            continue
        source_ids.add(source_id)
        record_entry = records.get(source_id)
        source_status = clean_cell(row.get("status") or row.get("source_readiness_status") or "")
        if record_entry is None:
            if source_status == "report_citable":
                errors.append(f"source_index:{source_id}: report_citable source is missing source record")
            else:
                warnings.append(f"source_index:{source_id}: missing source record")
            continue

        record_path, record = record_entry
        if source_status == "report_citable" and record_path.stat().st_size < 1024:
            errors.append(f"{source_id}: report_citable source record is too small for verification (<1KB)")
        link_row = link_register.get(source_id, {})
        if link_row:
            url_status = link_row.get("url_status", "").lower()
            use_level = link_row.get("use_level", "").lower()
            link_url = link_row.get("url", "").strip()
            source_locator = link_row.get("source_locator", "").strip()
            if source_status == "report_citable" and (not link_url or is_generic_url(link_url)):
                errors.append(f"{source_id}: report_citable source_link_register row requires an exact non-generic URL")
            if source_status == "report_citable" and use_level not in {"report_citable", "quote_verified"}:
                errors.append(f"{source_id}: source_link_register use_level={use_level or '(blank)'} does not allow report_citable use")
            if source_status == "report_citable" and not (
                url_status in {"ok", "verified", "200", "exact_url_verified"}
            ):
                errors.append(f"{source_id}: report_citable source lacks verified exact URL status in source_link_register.csv")
            if source_status == "report_citable" and use_level in {"report_citable", "quote_verified"} and not source_locator:
                errors.append(f"{source_id}: report_citable URL source requires source_locator in source_link_register.csv")
        url_or_path = clean_md_link(record.get("url_or_path") or row.get("url_or_path", ""))
        evidence_class = (record.get("evidence_class") or row.get("evidence_class") or "").strip("` ")
        readiness = (record.get("source_readiness_status") or row.get("source_readiness_status") or "").strip("` ")
        original_verified = (record.get("original_verified") or row.get("original_verified") or "").lower().strip("` ")
        reliability = row.get("reliability_tier", "")
        title = row.get("title", "") or record.get("title", "")
        record_title = record.get("title", "")
        publisher = row.get("publisher", "") or record.get("publisher", "")
        source_status = clean_cell(row.get("status") or record.get("status") or "")
        capture_path = clean_md_link(record.get("capture_path", ""))
        local_original_path = clean_md_link(record.get("local_original_path", ""))
        metadata_mismatch = source_metadata_mismatch(record_title or title, publisher, url_or_path)
        if source_status == "report_citable" and metadata_mismatch:
            errors.append(f"{source_id}: source title/publisher/url mismatch ({metadata_mismatch}): {url_or_path}")

        if source_status == "report_citable" and not url_or_path:
            errors.append(f"{source_id}: report_citable source record requires url_or_path or original_path")
        if source_status == "report_citable" and url_or_path and re.match(r"https?://", url_or_path) and source_id not in link_register:
            errors.append(f"{source_id}: report_citable URL-only source requires references/source_link_register.csv row with verified URL status")
        if source_status == "report_citable" and evidence_class == "captured_webpage" and not (capture_path or local_original_path):
            errors.append(f"{source_id}: captured_webpage report_citable source requires capture_path or local_original_path")
        local_original_candidate = resolve_project_path(project, local_original_path) if local_original_path else None
        if (
            source_status == "report_citable"
            and local_original_candidate
            and local_original_candidate.exists()
            and local_original_candidate.suffix.lower() == ".txt"
        ):
            ok, reason = inspect_original_file(local_original_candidate)
            if not ok:
                errors.append(
                    f"{source_id}: report_citable local_original_path failed originality check ({reason}); "
                    "use source_link_register.csv for URL-only sources or preserve a real capture/original"
                )

        local_candidate = (project / url_or_path).resolve()
        if url_or_path.startswith("../"):
            local_candidate = (source_index.parent / url_or_path).resolve()
        if url_or_path and not re.match(r"https?://", url_or_path):
            if not local_candidate.exists():
                warnings.append(f"{source_id}: url_or_path does not resolve locally: {url_or_path}")
            elif is_within(local_candidate, project):
                ok, reason = inspect_original_file(local_candidate)
                if not ok and "Tier 1" in reliability:
                    errors.append(f"{source_id}: Tier 1 source path appears non-original or unverified ({reason})")
                elif not ok:
                    warnings.append(f"{source_id}: source path needs manual original check ({reason})")
                if not likely_source_file_matches(source_id, title, url_or_path):
                    errors.append(f"{source_id}: source_id/title does not match local original path: {url_or_path}")
                # -------------------------------------------------------
                # NEW: PDF authenticity check for report_citable sources
                # -------------------------------------------------------
                if local_candidate.suffix.lower() == ".pdf" and source_status == "report_citable":
                    genuine, reason = pdf_is_genuine(local_candidate)
                    if not genuine:
                        errors.append(
                            f"{source_id}: report_citable PDF failed authenticity check ({reason}): "
                            f"{url_or_path} — original_verified=yes cannot be accepted for a dummy/shell PDF"
                        )
                if local_candidate.suffix.lower() == ".txt" and source_status == "report_citable":
                    ok, reason = inspect_original_file(local_candidate)
                    if not ok:
                        errors.append(
                            f"{source_id}: report_citable received_originals TXT failed originality check ({reason}); "
                            "use source_link_register.csv for URL-only sources or preserve a real capture/original"
                        )
        elif url_or_path and is_generic_url(url_or_path) and (readiness in REPORT_USE_STATUSES or source_status == "report_citable"):
            errors.append(f"{source_id}: report-citable source uses only a generic homepage URL: {url_or_path}")
        elif check_urls and url_or_path and re.match(r"https?://", url_or_path) and source_status == "report_citable":
            ok, detail = url_status_ok(url_or_path)
            if not ok:
                has_preserved_capture = any(path.exists() for path in local_evidence_paths(project, record, url_or_path))
                if has_preserved_capture and detail.startswith("TimeoutError"):
                    warnings.append(
                        f"{source_id}: live URL check timed out, but preserved local evidence exists ({detail}): {url_or_path}"
                    )
                else:
                    errors.append(f"{source_id}: report-citable URL check failed ({detail}): {url_or_path}")

        if evidence_class in DERIVATIVE_CLASSES and "Tier 1" in reliability:
            errors.append(f"{source_id}: derivative evidence_class cannot be Tier 1")
        if source_status == "report_citable" and record_title:
            row_title_terms = {term.lower() for term in extract_benchmark_terms(title)}
            record_title_terms = {term.lower() for term in extract_benchmark_terms(record_title)}
            if row_title_terms - record_title_terms:
                errors.append(
                    f"{source_id}: source index title adds benchmark terms not present in source record title: "
                    + ", ".join(sorted(row_title_terms - record_title_terms))
                )
        if readiness in REPORT_USE_STATUSES and original_verified == "yes":
            if url_or_path and re.match(r"https?://", url_or_path) and is_generic_url(url_or_path):
                errors.append(f"{source_id}: original_verified=yes requires an exact document URL or capture, not a homepage")
        if readiness and readiness not in SOURCE_READINESS_GOOD and row.get("used_in", "").strip():
            warnings.append(f"{source_id}: used in report before claim/report readiness ({readiness})")
        if original_verified == "no" and row.get("used_in", "").strip():
            warnings.append(f"{source_id}: used in report with original_verified=no")

        if source_status == "report_citable":
            record_text = read_text(record_path)
            exact_quote_section = source_record_section(record_text, r"\n##\s+2\.\s*Exact Quotes")
            weak_quotes = [quote for quote in quote_candidates(exact_quote_section) if is_weak_exact_quote(quote)]
            if weak_quotes:
                errors.append(
                    f"{source_id}: Exact Quotes section contains weak/generic quote candidates; "
                    "use source-specific text of at least "
                    f"{MIN_EXACT_QUOTE_CHARS} characters"
                )
            suspicious_tokens = sorted(token for token in PROMPT_OR_TOOL_TOKENS if token in exact_quote_section)
            if suspicious_tokens:
                errors.append(
                    f"{source_id}: Exact Quotes section contains prompt/tool tokens, not source text: "
                    + ", ".join(suspicious_tokens)
                )
            if INTERNAL_QUOTE_TOKEN_RE.search(exact_quote_section):
                errors.append(
                    f"{source_id}: Exact Quotes section contains internal audit/validator tokens rather than source text"
                )
            evidence_paths = append_link_register_evidence(project, local_evidence_paths(project, record, url_or_path), link_row)
            quote_lines = strong_quote_candidates(exact_quote_section)

            # -------------------------------------------------------
            # NEW: Detect AI-authored evidence stubs; flag and skip
            # -------------------------------------------------------
            ai_stub_paths = [p for p in evidence_paths if evidence_txt_is_ai_summary(p)]
            genuine_evidence_paths = [p for p in evidence_paths if p not in ai_stub_paths]
            if ai_stub_paths:
                errors.append(
                    f"{source_id}: evidence file(s) appear to be AI-authored summaries, not PDF extractions "
                    f"— cannot serve as original verification: "
                    + ", ".join(p.name for p in ai_stub_paths)
                )

            # -------------------------------------------------------
            # NEW: Verify quotes exist in genuine (non-stub) evidence
            # -------------------------------------------------------
            evidence_text = "\n".join(text_from_evidence(path) for path in genuine_evidence_paths)
            if (
                source_status == "report_citable"
                and genuine_evidence_paths
                and text_is_too_generic_for_quote_verification(evidence_text)
            ):
                errors.append(
                    f"{source_id}: preserved evidence text is too short or generic to support quote_verified/report_citable use"
                )
            if quote_lines and genuine_evidence_paths:
                missing_quotes = [
                    quote for quote in quote_lines
                    if not quote_found_in_genuine_evidence(quote, genuine_evidence_paths)
                ]
                if missing_quotes:
                    errors.append(
                        f"{source_id}: Exact Quotes not found in genuine (non-AI-stub) evidence — "
                        "claim cannot be treated as a delivery-stage verified fact"
                    )
            elif quote_lines and not genuine_evidence_paths:
                # Fall back to old check only if no stubs either
                if not ai_stub_paths and not re.match(r"https?://", url_or_path):
                    errors.append(f"{source_id}: Exact Quotes exist but no preserved evidence file can be checked")
                elif not ai_stub_paths and re.match(r"https?://", url_or_path) and source_status == "report_citable":
                    if not (link_row.get("source_locator") or record.get("source_locator") or record.get("exact_quote_location")):
                        errors.append(f"{source_id}: URL-only Exact Quotes require source_locator or exact_quote_location")

    claim_rows = parse_markdown_table(claim_register)
    for row in claim_rows:
        claim_id = row.get("claim_id", "").strip("` ")
        claim_type = (row.get("claim_type") or row.get("classification") or row.get("type") or "").lower()
        citation_type = (row.get("citation_type") or "").lower().strip("` ")
        status = (row.get("status") or row.get("claim_status") or "").lower()
        source_field = row.get("source_id") or row.get("source_ids") or ""
        evidence_class = (row.get("evidence_class") or "").strip("` ")
        original_verified = (row.get("original_verified") or "").lower().strip("` ")
        report_use_allowed = (row.get("report_use_allowed") or "").lower().strip("` ")
        source_list = [s.strip("` ") for s in re.split(r"[,;]", source_field) if s.strip()]

        if not claim_id or claim_id == "claim_id":
            continue
        for source_id in source_list:
            if source_id and source_id not in source_ids and source_id not in records:
                warnings.append(f"{claim_id}: source_id not found in source index/records: {source_id}")

        is_fact = claim_type in {"fact", "confirmed_fact"} or "fact" in claim_type
        if status in {"report_citable", "cited"} and not citation_type:
            warnings.append(f"{claim_id}: report-used claim should declare citation_type")
        if citation_type == "direct_quote" and not (row.get("exact_quote_location") or "").strip():
            errors.append(f"{claim_id}: direct_quote requires exact_quote_location/page/section/URL")
        if citation_type == "inference" and not (row.get("notes") or row.get("assumption_ids") or "").strip():
            warnings.append(f"{claim_id}: inference should include reasoning notes or assumption_ids")
        if is_fact:
            if evidence_class in DERIVATIVE_CLASSES:
                errors.append(f"{claim_id}: fact claim uses derivative evidence_class={evidence_class}")
            if original_verified == "no":
                errors.append(f"{claim_id}: fact claim has original_verified=no")
            if not (row.get("exact_quote_location") or "").strip():
                errors.append(f"{claim_id}: confirmed fact requires exact_quote_location/page/section/URL")
            if not (row.get("evidence_paths") or "").strip():
                errors.append(f"{claim_id}: fact claim requires evidence_paths to a source record or original")
            if status in {"cited", "source_backed"}:
                warnings.append(f"{claim_id}: legacy status {status} does not prove quote/original verification")
        if report_use_allowed == "no" and status in {"cited", "report_citable"}:
            errors.append(f"{claim_id}: report_use_allowed=no but claim is cited/report_citable")

    report_dir = project / "reports"
    for report in report_dir.glob("*.html"):
        text = read_text(report)
        visible_or_raw = text
        for term in SUSPICIOUS_TONE:
            if term in text:
                warnings.append(f"{report.relative_to(project)}: suspicious certainty/tone term: {term}")
        if re.search(r"자료:\s*data_sources[/\\]", text):
            warnings.append(f"{report.relative_to(project)}: local data_sources path is shown as visible source")
        benchmark_terms = sorted(extract_benchmark_terms(visible_or_raw))
        if benchmark_terms:
            missing_terms = [
                term for term in benchmark_terms
                if not benchmark_term_has_original_support(term, records)
            ]
            if missing_terms:
                errors.append(
                    f"{report.relative_to(project)}: benchmark terms lack original-backed source records: "
                    + ", ".join(sorted(set(missing_terms)))
                )

    if source_rows:
        info.append(f"sources_checked={len(source_rows)}")
    if claim_rows:
        info.append(f"claims_checked={len(claim_rows)}")

    return {
        "project": project.name,
        "errors": errors,
        "warnings": warnings,
        "info": info,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate research source and claim integrity.")
    parser.add_argument("--project", help="Project folder name to validate. Defaults to all projects.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--check-urls", action="store_true", help="Actively fetch report-citable HTTP(S) URLs and require a successful response.")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    projects = list(iter_projects(root))
    if args.project:
        projects = [p for p in projects if p.name == args.project]
        if not projects:
            print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
            return 2

    results = [validate_project(project, args.check_urls) for project in projects]
    total_errors = sum(len(r["errors"]) for r in results)
    total_warnings = sum(len(r["warnings"]) for r in results)
    payload = {
        "projects_checked": len(results),
        "errors": total_errors,
        "warnings": total_warnings,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
