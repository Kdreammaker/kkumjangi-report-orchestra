from __future__ import annotations

import argparse
import csv
import html.parser
import json
import re
import sys
import zipfile
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
PLAN_DATA_FILENAMES = {"visual_plan.csv"}
SUSPICIOUS_TONE = [
    "완벽히",
    "완벽하게",
    "최고 수준",
    "압도적",
    "100% 보증",
    "무조건",
    "강행",
    "즉각 보고 가능",
    "최종 보고서",
    "완전 정착",
    "독보적 1위",
    # Residual over-certainty phrases found in Project 01 audit
    "100% 우선 변제",
    "100% 철저히 보호",
    "100% 보장",
    "100% 면제",
    "100% 압류",
    "100% 환급 보호",
    "100% 안전",
    "절대적으로",
    "압승",
    "끝까지 밀어붙",
    "완전 예방",
    "완전히 보호",
    "완전한 제어",
]

# Cover page required element patterns (must appear inside <header> or .report-cover)
# checked against the raw HTML, not visible text, to allow hidden spans etc.
COVER_REQUIRED_PATTERNS: list[tuple[str, str]] = [
    # (error_label, regex)
    (
        "보고서 번호 또는 분류 코드",
        r"(?:보고서\s*번호|보고서\s*분류|report\s*(?:no|number|id)|분류\s*(?:번호|코드))",
    ),
    (
        "기밀 / 보안 등급 라벨 (Confidential 또는 내부용 등)",
        r"(?:Confidential|내부용|대외비|보안\s*등급|기밀|Internal\s*Only)",
    ),
    (
        "발행일 또는 작성일",
        r"(?:\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}|\d{4}년\s*\d{1,2}월|작성일|발행일|date)",
    ),
]

PLACEHOLDER_PATTERNS: list[tuple[str, str]] = [
    ("unresolved CSS width placeholder", r"width\s*:\s*\{\{"),
    ("unresolved CSS height placeholder", r"height\s*:\s*\{\{"),
    ("unresolved SVG width placeholder", r"<svg\b[^>]*(?:width|height)=[\"']\{\{"),
    ("unresolved template token", r"\{\{[A-Za-z0-9_]+\}\}"),
]

LAYOUT_RISK_PATTERNS: list[tuple[str, str]] = [
    (
        "viewport-dependent CSS sizing",
        r"(?:width|min-width|max-width|height|min-height|max-height|margin|padding|top|right|bottom|left|font-size)\s*:"
        r"[^;{}]*(?:\d+(?:\.\d+)?(?:vh|vw|vmin|vmax|dvh|dvw|svh|svw|lvh|lvw))",
    ),
    ("absolute/fixed/sticky positioning", r"position\s*:\s*(?:absolute|fixed|sticky)\b"),
    (
        "interactive controls or event handlers",
        r"<(?:button|input|select|textarea)\b|contenteditable\s*=|on(?:click|change|input|submit|mouseover|keydown)\s*=",
    ),
    ("canvas-dependent visual", r"<canvas\b"),
]


class TextExtractor(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []

    def handle_data(self, data: str) -> None:
        self.text.append(data)

    def visible_text(self) -> str:
        return " ".join(part.strip() for part in self.text if part.strip())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def report_language(raw: str) -> str:
    if re.search(r"<html\b[^>]*\blang=[\"']en(?:[-_][A-Za-z0-9]+)?[\"']", raw, flags=re.I):
        return "en"
    if re.search(r"\bdata-output-language=[\"'](?:en|mixed)[\"']", raw, flags=re.I):
        return "en"
    if re.search(
        r"<meta\b[^>]*\bname=[\"'](?:output_language|output-language)[\"'][^>]*\bcontent=[\"'](?:en|mixed)[\"']",
        raw,
        flags=re.I,
    ):
        return "en"
    return "ko"


def count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.I))


def layout_risk_signals(text: str) -> list[str]:
    signals: list[str] = []
    for label, pattern in LAYOUT_RISK_PATTERNS:
        count = len(re.findall(pattern, text, flags=re.I | re.S))
        if count:
            signals.append(f"{label} ({count})")
    return signals


def strip_cover_component(text: str) -> str:
    return re.sub(
        r"<section\b[^>]*class=[\"'][^\"']*cover-page[^\"']*[\"'][^>]*>.*?</section>",
        "",
        text,
        flags=re.I | re.S,
    )


def source_ids_from_index(project: Path) -> set[str]:
    index = project / "source_index" / "source_master_index.md"
    if not index.exists():
        return set()
    ids: set[str] = set()
    for line in read_text(index).splitlines():
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [cell.strip(" `*") for cell in line.strip("|").split("|")]
        if not cells or cells[0] in {"source_id", "---"}:
            continue
        if re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]+$", cells[0]):
            ids.add(cells[0])
    return ids


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


def count_material_figures(fragment: str) -> int:
    figure_blocks = re.findall(r"<figure\b[^>]*>.*?</figure>", fragment, flags=re.I | re.S)
    remainder = re.sub(r"<figure\b[^>]*>.*?</figure>", "", fragment, flags=re.I | re.S)
    true_figure_blocks = [
        block
        for block in figure_blocks
        if re.search(r"<(?:svg|img|canvas)\b", block, flags=re.I)
        or re.search(r"class=[\"'][^\"']*(?:chart|graph|diagram|timeline|flow)[^\"']*[\"']", block, flags=re.I)
    ]
    standalone_media = re.findall(r"<(?:svg|img|canvas)\b", remainder, flags=re.I)
    visual_containers = re.findall(
        r"<(?:div|section|article)\b[^>]*class=[\"'][^\"']*(?:chart|graph|diagram|timeline|flow)[^\"']*[\"']",
        remainder,
        flags=re.I,
    )
    return len(true_figure_blocks) + len(standalone_media) + len(visual_containers)


def is_backing_data_file(path: Path) -> bool:
    return path.suffix.lower() in {".csv", ".xlsx", ".xls", ".tsv"} and path.name.lower() not in PLAN_DATA_FILENAMES


def validate_report(project: Path, report: Path, strict_delivery: bool = False) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    raw = read_text(report)
    visible_html = strip_comments(raw)
    visible_html_no_style = re.sub(r"<style\b[^>]*>.*?</style>", "", visible_html, flags=re.I | re.S)
    report_body_no_cover = strip_cover_component(visible_html_no_style)
    parser = TextExtractor()
    parser.feed(visible_html)
    visible_text = parser.visible_text()
    language = report_language(raw)
    english_label_allowed = language == "en"
    source_ids = source_ids_from_index(project)
    substantial = bool(
        re.search(
            r"(internal review|substantial|full report|strategy report|policy report|"
            r"내부\s*검토|종합\s*보고서|상세\s*보고서|전략\s*보고서|정책\s*보고서)",
            visible_text,
            flags=re.I,
        )
    )
    data_files = [
        path for path in (project / "data_sources").glob("*")
        if path.is_file() and is_backing_data_file(path)
    ]
    linked_template = bool(re.search(r"(report\.css|report-template|_ai_system/templates)", raw, flags=re.I))
    assembled_report = "data-assembled-report=\"true\"" in raw or "mode: concatenate_only_no_rewrite" in raw
    chapter_dir = project / "reports" / "chapters"
    chapter_fragments = sorted(chapter_dir.glob("ch*.html")) if chapter_dir.exists() else []
    substantial = substantial or bool(chapter_fragments) or assembled_report
    cover_component = "data-cover-component=\"report-cover-v1\"" in raw or "class=\"cover-page\"" in raw
    confidentiality_signal = bool(re.search(r"대외비|confidential", visible_text, flags=re.I))

    if re.search(r"\b(source_id|claim_id|assumption_id|data_file_id)\b", visible_text, flags=re.I):
        errors.append("internal audit identifiers are visible in reader-facing text")
    for source_id in sorted(source_ids):
        if source_id and source_id in visible_text:
            errors.append(f"internal source_id is visible in reader-facing text: {source_id}")

    if re.search(r"증거\s*자료\s*및\s*클레임\s*대장|Evidence\s*Table|Source ID", visible_text, flags=re.I):
        errors.append("internal evidence/claim table appears in the report body")
    if "실효적인 수준" in visible_text:
        errors.append("reader-facing report contains vague placeholder phrase: 실효적인 수준")
    for label, pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, raw, flags=re.I):
            errors.append(f"report contains unresolved layout/template placeholder: {label}")
    if re.search(r"word-break\s*:\s*break-all", visible_html, flags=re.I):
        message = "report CSS uses word-break: break-all; use scoped long-token wrapping for URLs, paths, code, and table cells instead"
        if strict_delivery:
            errors.append(message)
        else:
            warnings.append(message)
    risky_layout_signals = layout_risk_signals(visible_html)
    if risky_layout_signals:
        warnings.append(
            "DOCX/PDF layout risk signals found: "
            + "; ".join(risky_layout_signals)
            + "; confirm these are scoped and do not drive essential report layout"
        )
        if strict_delivery:
            warnings.append(
                "strict delivery should avoid interactive controls, canvas-only visuals, viewport-dependent sizing, and absolute/fixed/sticky layout unless separately export-verified"
            )

    footnote_count = len(re.findall(r"<sup\b|class=[\"'][^\"']*footnote|주석|참고문헌", visible_html, flags=re.I))
    if substantial and footnote_count == 0:
        errors.append("substantial report has no reader-facing footnotes/endnotes")

    table_count = len(re.findall(r"<table\b", report_body_no_cover, flags=re.I))
    figure_count = count_material_figures(report_body_no_cover)
    ko_source_caption_count = visible_text.count("자료:")
    ko_data_caption_count = visible_text.count("근거 데이터")
    en_source_caption_count = count_pattern(visible_text, r"\bSource\s*:")
    en_data_caption_count = count_pattern(visible_text, r"\b(?:Underlying data|Data basis)\s*:")
    source_caption_count = ko_source_caption_count + (en_source_caption_count if english_label_allowed else 0)
    data_caption_count = ko_data_caption_count + (en_data_caption_count if english_label_allowed else 0)
    data_caption_values = re.findall(
        r"(?:근거\s*데이터|Underlying data|Data basis)\s*:\s*([^<\n]+)",
        visible_html_no_style,
        flags=re.I,
    )
    if not english_label_allowed and (en_source_caption_count or en_data_caption_count):
        errors.append("English caption labels require html lang=\"en\" or an explicit output_language marker")

    # ------------------------------------------------------------------
    # NEW: Cover page element validation
    # ------------------------------------------------------------------
    # Locate the cover block in raw HTML (header.report-cover or similar).
    cover_block_match = re.search(
        r"<section\b[^>]*class=[\"'][^\"']*cover-page[^\"']*[\"'][^>]*>.*?</section>"
        r"|<(?:header|div)[^>]*class=[\"'][^\"']*report-cover[^\"']*[\"'][^>]*>.*?</(?:header|div)>",
        raw,
        flags=re.I | re.DOTALL,
    )
    cover_block = cover_block_match.group(0) if cover_block_match else ""
    cover_missing: list[str] = []
    for label, pattern in COVER_REQUIRED_PATTERNS:
        # Search in cover block first, then fall back to first 2000 chars of raw HTML
        # (to accommodate reports that embed metadata in a preamble comment or meta tag).
        search_zone = cover_block or raw[:2000]
        if not re.search(pattern, search_zone, flags=re.I):
            cover_missing.append(label)
    if cover_missing:
        errors.append(
            "cover page is missing required elements: " + "; ".join(cover_missing)
        )
    if confidentiality_signal:
        if not re.search(r"class=[\"'][^\"']*cover-security-tag[^\"']*[\"']", cover_block, flags=re.I):
            errors.append("confidential report cover lacks the reusable red confidential tag module")
        if not re.search(r"class=[\"'][^\"']*cover-confidential-notice[^\"']*[\"']", cover_block, flags=re.I):
            errors.append("confidential report cover lacks the reusable confidentiality warning module")
    if strict_delivery:
        script_dependent_visual = bool(
            re.search(
                r"<script\b|echarts\.init|data-echarts|class=[\"'][^\"']*(?:echarts|interactive-chart)[^\"']*[\"']",
                raw,
                flags=re.I,
            )
        )
        if script_dependent_visual:
            errors.append(
                "strict delivery reports must use static SVG/PNG/table visuals; JavaScript-dependent interactive charts are not DOCX/PDF conversion-ready"
            )
        empty_chart_blocks = re.findall(
            r"<(?:div|section|article)\b[^>]*class=[\"'][^\"']*(?:chart|graph)[^\"']*[\"'][^>]*>\s*</(?:div|section|article)>",
            raw,
            flags=re.I | re.S,
        )
        if empty_chart_blocks:
            errors.append("strict delivery report contains empty chart/graph placeholders instead of static rendered visuals")
    if strict_delivery and not cover_component:
        errors.append("strict delivery requires the reusable cover component (cover-page / report-cover-v1), not only a title header")
    if strict_delivery and substantial and not assembled_report:
        errors.append("strict delivery substantial reports must be assembled from chapter fragments by assemble_report.py")
    if strict_delivery and substantial and not chapter_fragments:
        errors.append("strict delivery substantial reports require source chapter fragments under reports/chapters/ch*.html")

    # ------------------------------------------------------------------
    # NEW: Minimum visual element standard
    # Substantial reports that discuss market/comparison/roadmap content
    # must have at least 1 chart or figure.  Data captions without a
    # matching figure/chart count as a partial fail.
    # ------------------------------------------------------------------
    if substantial and table_count == 0 and figure_count == 0:
        errors.append(
            "substantial report has no tables or charts/figures; use visuals when they clarify decisions, comparisons, flows, risks, or evidence"
        )
    elif substantial and table_count == 0:
        warnings.append("substantial report has charts/figures but no tables; confirm exact criteria or legal/data comparisons are not being hidden in prose")
    elif substantial and figure_count == 0:
        message = "substantial report has tables but no real charts/graphs/diagrams; table-wrapped figures do not count as graphs"
        if strict_delivery:
            errors.append(message)
        else:
            warnings.append(message)
    data_refs: list[str] = re.findall(r"data_sources[/\\][^\s<)]+?\.(?:csv|xlsx|xls|tsv)", raw, flags=re.I)
    if table_count and source_caption_count == 0:
        expected_source_label = "Source:" if english_label_allowed else "자료:"
        errors.append(f"tables exist without reader-facing {expected_source_label} source captions")
    if substantial and (table_count or figure_count) and not data_files:
        errors.append("tables/charts exist but no CSV/XLSX data file exists under data_sources/")
    if substantial and (table_count or figure_count) and data_caption_count == 0:
        expected_data_label = "Underlying data/Data basis" if english_label_allowed else "근거 데이터"
        errors.append(f"tables/charts exist without reader-facing {expected_data_label} caption")
    if re.search(r"자료:\s*(?:\.\./)?data_sources[/\\]|자료:\s*[A-Za-z0-9_./\\-]+\.csv", visible_text):
        errors.append("local CSV/data path is shown as the visible source instead of 근거 데이터")
    if re.search(r"\bSource\s*:\s*(?:\.\./)?data_sources[/\\]|\bSource\s*:\s*[A-Za-z0-9_./\\-]+\.csv", visible_text, flags=re.I):
        errors.append("local CSV/data path is shown as the visible source instead of a data-basis label")
    if re.search(r"근거\s*데이터\s*:\s*(?:\.\./)?data_sources[/\\]", visible_text):
        errors.append("raw local data_sources path is visible in reader-facing 근거 데이터 text; keep paths in comments, data indexes, or appendices")
    if re.search(r"\b(?:Underlying data|Data basis)\s*:\s*(?:\.\./)?data_sources[/\\]", visible_text, flags=re.I):
        errors.append("raw local data_sources path is visible in reader-facing data-basis text; keep paths in comments, data indexes, or appendices")
    if strict_delivery and table_count + figure_count:
        visual_count = table_count + figure_count
        if data_caption_count < visual_count:
            errors.append(
                f"strict delivery requires a {'Underlying data/Data basis' if english_label_allowed else '근거 데이터'} caption for each table/figure/chart; "
                f"found {data_caption_count} captions for {visual_count} visuals"
            )
        if len(data_refs) < visual_count:
            errors.append(
                f"strict delivery requires one explicit data_sources CSV/XLSX reference for each material table/figure/chart; "
                f"found {len(data_refs)} data file references for {visual_count} visuals"
            )
        missing_data_refs = []
        for ref in data_refs:
            candidate = (project / ref).resolve()
            try:
                candidate.relative_to(project.resolve())
            except ValueError:
                missing_data_refs.append(ref)
                continue
            if not candidate.exists():
                missing_data_refs.append(ref)
        if missing_data_refs:
            errors.append("strict delivery 근거 데이터 files do not exist: " + " | ".join(missing_data_refs[:5]))
        empty_data_notes = [value.strip() for value in data_caption_values if not value.strip()]
        if empty_data_notes:
            errors.append("strict delivery data-basis captions must name the dataset or qualitative evidence in reader-facing text")
    if re.search(r"[A-Za-z]:[\\/]|file:///", visible_text):
        errors.append("absolute local path is visible in reader-facing report text")
    if re.search(r"\baccessed\s+\d{4}", visible_text, flags=re.I) and not english_label_allowed:
        warnings.append("Korean reader-facing references should use `접근일: YYYY.MM.DD` instead of English `accessed YYYY-MM-DD`")

    if substantial and not re.search(r"\b(Appendix|부록)\b", visible_text, flags=re.I):
        errors.append("substantial report has no appendix section")
    if substantial and not re.search(r"id=[\"'](?:appendix-references|report-references)[\"']|<h1>\s*참고자료\s*</h1>|참고자료\s*목록|부록\s*A\.\s*참고자료", raw, flags=re.I):
        errors.append("substantial report lacks a reader-facing reference section/list with accessible source links")
    if strict_delivery:
        chapter0_summary = bool(
            re.search(
                r"(?:제\s*0\s*장|0\s*[.)]\s*|chapter\s*0)[^\n<]{0,80}(?:요약|executive\s*summary)"
                r"|(?:요약|executive\s*summary)[^\n<]{0,40}(?:제\s*0\s*장|chapter\s*0)",
                visible_text,
                flags=re.I,
            )
        )
        if not chapter0_summary:
            errors.append("strict delivery requires the final executive summary to appear as Chapter 0 / 제0장 요약")
        if data_files and table_count + figure_count >= 4 and len(data_files) < 2:
            warnings.append("strict delivery has multiple tables/charts but fewer than 2 local data files")
        if not linked_template:
            warnings.append("strict delivery report does not reference a reusable workspace report template/style system")
        visual_plan = project / "data_sources" / "visual_plan.csv"
        visual_rows = csv_rows(visual_plan)
        if not visual_rows:
            errors.append("strict delivery requires data_sources/visual_plan.csv so visuals are planned by chapter purpose, not by count")
        else:
            required_rows = [
                row for row in visual_rows
                if row.get("required", "").lower() in {"yes", "y", "true", "1", "required"}
            ]
            missing_visuals = []
            for row in required_rows:
                title = row.get("title", "")
                data_file = row.get("data_file", "") or row.get("source_data", "") or row.get("data_or_source_artifact", "")
                status = row.get("status", "").lower()
                if status in {"dropped", "cancelled", "not_applicable"}:
                    continue
                title_found = bool(title and title in visible_text)
                data_found = bool(data_file and data_file in raw)
                if not (title_found or data_found):
                    missing_visuals.append(row.get("visual_id") or title or "(unnamed visual)")
            if missing_visuals:
                errors.append("required visuals from visual_plan.csv are not implemented in the report: " + " | ".join(missing_visuals[:8]))
            chart_like = [
                row for row in required_rows
                if re.search(r"(chart|graph|diagram|flow|map|timeline|heatmap|matrix|도식|차트|그래프|흐름|로드맵|히트맵)", row.get("visual_type", ""), flags=re.I)
            ]
            if chart_like and figure_count == 0:
                errors.append("visual_plan.csv requires chart/diagram-type visuals, but the report contains no figure/chart")
    if substantial and figure_count == 0 and ("시장" in visible_text or "비교" in visible_text or "로드맵" in visible_text):
        warnings.append("report has market/comparison/roadmap content but no chart or figure")

    for term in SUSPICIOUS_TONE:
        if term in visible_text:
            warnings.append(f"suspicious certainty/tone term: {term}")

    docx_details = []
    for docx_path in sorted((project / "reports").glob("*.docx")):
        detail = {
            "path": docx_path.relative_to(project).as_posix(),
            "valid_zip": False,
            "parts": 0,
            "has_styles": False,
            "has_footnotes_or_endnotes": False,
            "has_numbering": False,
            "has_media": False,
        }
        try:
            with zipfile.ZipFile(docx_path) as zf:
                names = set(zf.namelist())
                detail["valid_zip"] = True
                detail["parts"] = len(names)
                detail["has_styles"] = "word/styles.xml" in names
                detail["has_footnotes_or_endnotes"] = "word/footnotes.xml" in names or "word/endnotes.xml" in names
                detail["has_numbering"] = "word/numbering.xml" in names
                detail["has_media"] = any(name.startswith("word/media/") for name in names)
        except zipfile.BadZipFile:
            errors.append(f"DOCX is not a valid zip package: {docx_path.name}")
        if strict_delivery and detail["valid_zip"] and not detail["has_styles"]:
            errors.append(f"DOCX lacks word/styles.xml and is not delivery-conversion ready: {docx_path.name}")
        if strict_delivery and detail["valid_zip"] and footnote_count and not detail["has_footnotes_or_endnotes"]:
            warnings.append(f"DOCX lacks footnotes/endnotes part despite report footnotes: {docx_path.name}")
        docx_details.append(detail)

    return {
        "report": report.relative_to(project).as_posix(),
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "visible_chars": len(visible_text),
            "tables": table_count,
            "figures_or_charts": figure_count,
            "source_captions": source_caption_count,
            "data_captions": data_caption_count,
            "report_language": language,
            "data_files": len(data_files),
            "footnote_markers": footnote_count,
            "substantial": substantial,
            "strict_delivery": strict_delivery,
            "uses_reusable_template": linked_template,
            "assembled_report": assembled_report,
            "chapter_fragments": len(chapter_fragments),
            "uses_cover_component": cover_component,
            "layout_risk_signals": risky_layout_signals,
            "docx_details": docx_details,
        },
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate reader-facing HTML report artifacts.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--report", help="Specific report path relative to the project folder")
    parser.add_argument("--strict-delivery", action="store_true", help="Apply stricter volume/depth checks for internally reviewable or delivery-stage reports.")
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2

    reports = [project / args.report] if args.report else sorted((project / "reports").glob("*.html"))
    results = []
    for report in reports:
        if report.exists() and report.suffix.lower() == ".html":
            results.append(validate_report(project, report, args.strict_delivery))
    payload = {
        "project": project.name,
        "reports_checked": len(results),
        "errors": sum(len(item["errors"]) for item in results),
        "warnings": sum(len(item["warnings"]) for item in results),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
