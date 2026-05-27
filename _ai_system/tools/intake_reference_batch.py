from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from pypdf import PdfReader


DOCLING_EXTENSIONS = {".pdf", ".pptx", ".docx", ".xlsx", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(name: str) -> dict[str, str]:
    lowered = name.lower()
    if any(term in lowered for term in ["official", "regulator", "ministry", "agency", "law", "act", "guideline"]) or any(
        term in name for term in ["공식", "보도자료", "법령", "가이드", "지침", "감독", "기관"]
    ):
        return {
            "material_origin": "external",
            "material_origin_ko": "외부자료",
            "visibility": "public",
            "visibility_ko": "외부공개",
            "source_tier": "Tier 1",
            "ai_tags": "공식자료;제도;규제;공개자료;원문확인필요",
            "tag_notes": "파일명 기준 공식/공개 자료로 추정되어 제도·규제 중심 태그를 부여.",
        }
    if any(term in lowered for term in ["internal", "strategy", "business", "board", "management"]) or any(
        term in name for term in ["내부", "사업", "경영", "전략", "기획", "운영"]
    ):
        return {
            "material_origin": "internal",
            "material_origin_ko": "내부자료",
            "visibility": "confidential",
            "visibility_ko": "비공개",
            "source_tier": "Tier 2",
            "ai_tags": "내부자료;사업전략;운영체계;리스크관리;원문확인필요",
            "tag_notes": "파일명 기준 내부 전략 또는 운영 문서로 추정되어 내부자료 중심 태그를 부여.",
        }
    return {
        "material_origin": "user_provided",
        "material_origin_ko": "사용자 제공자료",
        "visibility": "unknown",
        "visibility_ko": "확인필요",
        "source_tier": "확인필요",
        "ai_tags": "사용자제공;확인필요;참고자료",
        "tag_notes": "자료 성격이 불명확하여 확인필요 태그를 부여.",
    }


def project_code(project_dir: Path) -> str:
    first = project_dir.name.split("_", 1)[0]
    if first.isdigit():
        return f"p{int(first):02d}"
    return "".join(c.lower() for c in first if c.isalnum())[:8] or "proj"


def project_label(project_dir: Path) -> str:
    readme = project_dir / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return project_dir.name


def safe_stem(index: int, path: Path, prefix: str) -> str:
    ascii_slug = "".join(c.lower() if c.isalnum() else "_" for c in path.stem if ord(c) < 128)
    ascii_slug = "_".join(filter(None, ascii_slug.split("_")))[:48]
    return f"{prefix}_ref_{index:03d}" + (f"_{ascii_slug}" if ascii_slug else "")


def extract_pdf_text(path: Path) -> tuple[int, str, str]:
    reader = PdfReader(str(path))
    pages = len(reader.pages)
    parts: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # keep intake robust
            text = f"[page {i} extraction_error: {type(exc).__name__}: {exc}]"
        parts.append(f"\n\n--- page {i} ---\n{text.strip()}")
    full_text = "\n".join(parts).strip()
    parse_status = "parsed" if len(full_text) >= 500 else "needs_ocr"
    return pages, full_text, parse_status


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_text(text: str, max_chars: int = 4000) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + max_chars)
        if end < len(cleaned):
            split_at = cleaned.rfind("\n\n", start, end)
            if split_at > start + 800:
                end = split_at
        chunks.append(cleaned[start:end].strip())
        start = end
    return [chunk for chunk in chunks if chunk]


def docling_normalize(original_path: Path, project_dir: Path, reference_id: str, listed_at: str) -> dict[str, str]:
    result = {
        "normalized_status": "not_supported",
        "normalized_manifest_path": "",
        "normalized_text_path": "",
        "normalized_unit_index_path": "",
        "context_index_status": "not_indexed",
        "context_unit_count": "",
        "parse_status": "not_supported",
        "ocr_status": "not_required",
        "page_count": "",
        "derived_text_path": "",
    }
    if original_path.suffix.lower() not in DOCLING_EXTENSIONS:
        return result

    normalized_dir = project_dir / "references" / "normalized" / reference_id
    normalized_dir.mkdir(parents=True, exist_ok=True)
    normalized_md = normalized_dir / "normalized.md"
    normalized_json = normalized_dir / "docling.json"
    units_csv = normalized_dir / "units.csv"
    manifest_path = normalized_dir / "manifest.json"

    try:
        from docling.document_converter import DocumentConverter  # type: ignore[import-not-found]

        conversion = DocumentConverter().convert(str(original_path))
        document = conversion.document
        markdown = document.export_to_markdown()
        normalized_md.write_text(markdown, encoding="utf-8")
        if hasattr(document, "export_to_dict"):
            normalized_json.write_text(
                json.dumps(document.export_to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        units = chunk_text(markdown)
        unit_type = "slide" if original_path.suffix.lower() == ".pptx" else ("page" if original_path.suffix.lower() == ".pdf" else "chunk")
        with units_csv.open("w", encoding="utf-8-sig", newline="") as handle:
            fieldnames = ["reference_id", "unit_type", "unit_no", "heading", "text", "token_estimate"]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for idx, unit_text in enumerate(units, start=1):
                heading = next((line.strip("# ").strip() for line in unit_text.splitlines() if line.strip()), "")
                writer.writerow(
                    {
                        "reference_id": reference_id,
                        "unit_type": unit_type,
                        "unit_no": str(idx),
                        "heading": heading[:160],
                        "text": unit_text,
                        "token_estimate": str(estimate_tokens(unit_text)),
                    }
                )
        manifest = {
            "reference_id": reference_id,
            "engine": "docling",
            "created_at_kst": listed_at,
            "original_path": original_path.relative_to(project_dir).as_posix(),
            "normalized_text_path": normalized_md.relative_to(project_dir).as_posix(),
            "normalized_json_path": normalized_json.relative_to(project_dir).as_posix() if normalized_json.exists() else "",
            "normalized_unit_index_path": units_csv.relative_to(project_dir).as_posix(),
            "unit_count": len(units),
            "privacy_boundary": "local_only_no_external_upload_by_default",
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "normalized_status": "normalized",
            "normalized_manifest_path": manifest_path.relative_to(project_dir).as_posix(),
            "normalized_text_path": normalized_md.relative_to(project_dir).as_posix(),
            "normalized_unit_index_path": units_csv.relative_to(project_dir).as_posix(),
            "context_index_status": "pending_index",
            "context_unit_count": str(len(units)),
            "parse_status": "docling_parsed" if markdown.strip() else "needs_ocr",
            "ocr_status": "unknown" if original_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"} else "not_required",
            "page_count": str(len(units)) if unit_type in {"page", "slide"} else "",
            "derived_text_path": normalized_md.relative_to(project_dir).as_posix(),
        }
    except Exception as exc:  # noqa: BLE001
        manifest = {
            "reference_id": reference_id,
            "engine": "docling",
            "created_at_kst": listed_at,
            "original_path": original_path.relative_to(project_dir).as_posix(),
            "error": f"{type(exc).__name__}: {exc}",
            "privacy_boundary": "local_only_no_external_upload_by_default",
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        result.update(
            {
                "normalized_status": "error",
                "normalized_manifest_path": manifest_path.relative_to(project_dir).as_posix(),
                "parse_status": f"docling_error:{type(exc).__name__}",
                "ocr_status": "unknown",
            }
        )
        return result


def rel_url(from_file: Path, target: Path) -> str:
    rel = os.path.relpath(target.resolve(), from_file.parent.resolve())
    return quote(Path(rel).as_posix(), safe="/._-()[] ")


def read_inventory(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def row_needs_local_normalization(row: dict[str, str]) -> bool:
    parse_status = (row.get("parse_status") or "").strip()
    normalized_status = (row.get("normalized_status") or "").strip()
    if parse_status in {"parsed", "docling_parsed", "not_supported", "not_applicable"} and normalized_status in {
        "normalized",
        "not_supported",
    }:
        return False
    return parse_status in {"", "not_started", "copied", "needs_ocr"} or normalized_status in {"", "not_started", "error"}


def update_row_with_local_normalization(row: dict[str, str], original_path: Path, project_dir: Path, listed_at: str) -> bool:
    if not original_path.exists() or not original_path.is_file():
        return False
    if not row_needs_local_normalization(row):
        return False
    reference_id = row.get("reference_id") or safe_stem(1, original_path, project_code(project_dir))
    normalized = docling_normalize(original_path, project_dir, reference_id, listed_at)
    changed = False
    for key, value in normalized.items():
        if value and row.get(key, "") != value:
            row[key] = value
            changed = True
    if normalized.get("normalized_status") != "normalized" and original_path.suffix.lower() == ".pdf":
        try:
            page_count, text, parse_status = extract_pdf_text(original_path)
            text_dir = project_dir / "evidence" / "extracted_text" / "dashboard_existing"
            text_dir.mkdir(parents=True, exist_ok=True)
            text_path = text_dir / f"{reference_id}.txt"
            text_path.write_text(text, encoding="utf-8")
            updates = {
                "page_count": str(page_count),
                "parse_status": parse_status,
                "derived_text_path": text_path.relative_to(project_dir).as_posix(),
                "ocr_status": "needed" if parse_status == "needs_ocr" else "not_required",
            }
            for key, value in updates.items():
                if row.get(key, "") != value:
                    row[key] = value
                    changed = True
        except Exception as exc:  # noqa: BLE001
            value = f"error:{type(exc).__name__}"
            if row.get("parse_status", "") != value:
                row["parse_status"] = value
                changed = True
    return changed


def preserved_originals_by_hash(project_dir: Path) -> dict[str, Path]:
    """Find already preserved originals so intake can reuse instead of duplicating."""
    result: dict[str, Path] = {}
    originals_root = project_dir / "references" / "received_originals"
    if not originals_root.exists():
        return result
    for path in originals_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            result.setdefault(sha256(path), path)
        except OSError:
            continue
    return result


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: intake_reference_batch.py <source_dir> <project_dir> <batch_id>", file=sys.stderr)
        return 2

    source_dir = Path(sys.argv[1]).resolve()
    project_dir = Path(sys.argv[2]).resolve()
    batch_id = sys.argv[3]
    listed_at = datetime.now().strftime("%Y-%m-%d %H:%M KST")
    prefix = project_code(project_dir)
    label = project_label(project_dir)

    inbox_dir = project_dir / "references" / "inbox" / batch_id
    originals_dir = project_dir / "references" / "received_originals" / batch_id
    text_dir = project_dir / "evidence" / "extracted_text" / batch_id
    library_dir = project_dir / "reference_library"
    for d in [inbox_dir, originals_dir, text_dir, library_dir, project_dir / "references"]:
        d.mkdir(parents=True, exist_ok=True)

    inventory_path = project_dir / "references" / "reference_inventory.csv"
    existing_rows = read_inventory(inventory_path)
    existing_hashes = {r.get("sha256", "") for r in existing_rows if r.get("sha256")}
    existing_by_hash = {r.get("sha256", ""): r for r in existing_rows if r.get("sha256")}
    preserved_by_hash = preserved_originals_by_hash(project_dir)
    files = sorted(source_dir.glob("*"))
    rows: list[dict[str, str]] = []
    updated_existing = 0
    for idx, src in enumerate([p for p in files if p.is_file()], start=len(existing_rows) + 1):
        source_hash = sha256(src)
        if source_hash in existing_hashes:
            row = existing_by_hash.get(source_hash)
            if row:
                row_original = project_dir / row.get("original_path", "")
                original_for_parse = row_original if row_original.exists() else src
                if update_row_with_local_normalization(row, original_for_parse, project_dir, listed_at):
                    updated_existing += 1
            continue
        reference_id = safe_stem(idx, src, prefix)
        inbox_path = inbox_dir / src.name
        preserved_original = preserved_by_hash.get(source_hash)
        if preserved_original:
            original_path = preserved_original
            duplicate_note = "duplicate_hash_reused_existing_original"
        else:
            original_path = originals_dir / src.name
            shutil.copy2(src, original_path)
            preserved_by_hash[source_hash] = original_path
            duplicate_note = ""
        if not inbox_path.exists() and src.resolve() != inbox_path.resolve():
            shutil.copy2(src, inbox_path)

        file_type = src.suffix.upper().lstrip(".") or "UNKNOWN"
        c = classify(src.name)
        normalized = docling_normalize(original_path, project_dir, reference_id, listed_at)
        pages = normalized["page_count"]
        parse_status = normalized["parse_status"]
        derived_text_path = normalized["derived_text_path"]
        ocr_status = normalized["ocr_status"]
        if normalized["normalized_status"] != "normalized" and src.suffix.lower() == ".pdf":
            try:
                page_count, text, parse_status = extract_pdf_text(original_path)
                pages = str(page_count)
                text_path = text_dir / f"{reference_id}.txt"
                text_path.write_text(text, encoding="utf-8")
                derived_text_path = text_path.relative_to(project_dir).as_posix()
                ocr_status = "needed" if parse_status == "needs_ocr" else "not_required"
            except Exception as exc:
                parse_status = f"error:{type(exc).__name__}"
                ocr_status = "unknown"

        title = src.stem
        row = {
            "reference_id": reference_id,
            "listed_at_kst": listed_at,
            "title": title,
            "file_type": file_type,
            "material_origin": c["material_origin"],
            "material_origin_ko": c["material_origin_ko"],
            "visibility": c["visibility"],
            "visibility_ko": c["visibility_ko"],
            "source_tier": c["source_tier"],
            "ai_tags": c["ai_tags"],
            "tag_version": "tag-v1",
            "tagged_at_kst": listed_at,
            "tag_notes": c["tag_notes"],
            "original_path": original_path.relative_to(project_dir).as_posix(),
            "open_path": original_path.relative_to(project_dir).as_posix(),
            "sha256": sha256(original_path),
            "file_size_bytes": str(original_path.stat().st_size),
            "last_modified_kst": datetime.fromtimestamp(original_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M KST"),
            "intake_status": "parsed" if parse_status == "parsed" else ("needs_ocr" if parse_status == "needs_ocr" else "copied"),
            "parse_status": parse_status,
            "ocr_status": ocr_status,
            "page_count": pages,
            "derived_text_path": derived_text_path,
            "normalized_status": normalized["normalized_status"],
            "normalized_manifest_path": normalized["normalized_manifest_path"],
            "normalized_text_path": normalized["normalized_text_path"],
            "normalized_unit_index_path": normalized["normalized_unit_index_path"],
            "context_index_status": normalized["context_index_status"],
            "context_unit_count": normalized["context_unit_count"],
            "source_id": "",
            "source_record_path": "",
            "notes": duplicate_note,
        }
        rows.append(row)

    all_rows = existing_rows + rows
    standard_fieldnames = [
        "reference_id",
        "listed_at_kst",
        "title",
        "file_type",
        "material_origin",
        "material_origin_ko",
        "visibility",
        "visibility_ko",
        "source_tier",
        "ai_tags",
        "tag_version",
        "tagged_at_kst",
        "tag_notes",
        "original_path",
        "open_path",
        "sha256",
        "file_size_bytes",
        "last_modified_kst",
        "intake_status",
        "parse_status",
        "ocr_status",
        "page_count",
        "derived_text_path",
        "normalized_status",
        "normalized_manifest_path",
        "normalized_text_path",
        "normalized_unit_index_path",
        "context_index_status",
        "context_unit_count",
        "source_id",
        "source_record_path",
        "notes",
    ]
    extra_fieldnames = []
    for row in all_rows:
        for key in row:
            if key not in standard_fieldnames and key not in extra_fieldnames:
                extra_fieldnames.append(key)
    fieldnames = standard_fieldnames + extra_fieldnames
    with inventory_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    library_path = library_dir / "reference_library.html"
    table_rows = []
    for row in all_rows:
        original = project_dir / row["original_path"]
        href = rel_url(library_path, original)
        detail_bits = [
            f"신뢰도 tier: {row['source_tier']}",
            f"파싱 상태: {row['parse_status']}",
            f"OCR 상태: {row['ocr_status']}",
            f"페이지 수: {row['page_count'] or '-'}",
            f"정규화 상태: {row.get('normalized_status', '-')}",
            f"로컬 색인 상태: {row.get('context_index_status', '-')}",
        ]
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(row['title'])}</td>"
            f"<td>{html.escape(row['file_type'])}</td>"
            f"<td>{html.escape(row['material_origin_ko'])}</td>"
            f"<td>{html.escape(row['visibility_ko'])}</td>"
            f"<td>{html.escape(row['listed_at_kst'])}</td>"
            f"<td><a href=\"{href}\">열기</a></td>"
            "</tr>"
            "<tr class=\"detail\"><td colspan=\"6\"><details><summary>상세 정보</summary>"
            f"<p>{html.escape(' / '.join(detail_bits))}</p>"
            "</details></td></tr>"
        )

    library_html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{html.escape(label)} 참고자료 대장</title>
  <style>
    :root {{ --blue:#006BD6; --dark:#062554; --line:#CFD0D3; --bg:#EEEFF0; --text:#1f2933; --muted:#616670; }}
    body {{ font-family: 'Malgun Gothic', 'Noto Sans CJK KR', Arial, sans-serif; margin: 0; background: #f7f8fa; color: var(--text); }}
    main {{ max-width: 1120px; margin: 32px auto; padding: 0 24px 40px; }}
    .label {{ color: var(--blue); font-size: 13px; font-weight: 700; margin: 0 0 8px; }}
    h1 {{ font-size: 26px; margin: 0 0 10px; color: var(--dark); }}
    .note {{ color: var(--muted); font-size: 13px; line-height: 1.6; margin-bottom: 22px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-top: 2px solid var(--dark); }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px 12px; font-size: 13px; text-align: left; vertical-align: top; }}
    th {{ background: var(--bg); font-weight: 700; }}
    a {{ color: var(--blue); font-weight: 700; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    tr.detail td {{ background: #fbfcfd; padding-top: 6px; padding-bottom: 8px; }}
    details summary {{ cursor: pointer; color: var(--muted); font-size: 12px; }}
    details p {{ color: var(--muted); font-size: 12px; margin: 8px 0 0; }}
  </style>
</head>
<body>
<main>
  <p class="label">내부 참고자료 대장</p>
  <h1>{html.escape(label)} 참고자료 대장</h1>
  <p class="note">기본 화면은 원본 자료를 빠르게 찾기 위한 목록입니다. 파싱/OCR 결과물은 내부 evidence로 관리하며 기본 화면에는 노출하지 않습니다.</p>
  <table>
    <thead>
      <tr><th>자료명</th><th>파일 유형</th><th>자료 구분</th><th>공개 범위</th><th>리스트업 일시</th><th>원본 파일</th></tr>
    </thead>
    <tbody>
      {''.join(table_rows)}
    </tbody>
  </table>
</main>
</body>
</html>
"""
    library_path.write_text(library_html, encoding="utf-8")
    print(
        f"intake_complete new_rows={len(rows)} updated_existing={updated_existing} "
        f"total_rows={len(all_rows)} inventory={inventory_path} library={library_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
