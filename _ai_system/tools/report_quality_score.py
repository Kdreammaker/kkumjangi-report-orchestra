from __future__ import annotations

import argparse
import csv
import html.parser
import json
import re
import zipfile
from pathlib import Path

from workspace_config import active_domain_preset, active_quality_profile, get_path, load_config


PROJECT_ROOT = Path("00_사용자_작업공간")

GENERIC_URL_RE = re.compile(r"^https?://[^/]+/?(?:#.*)?$")
DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".tsv"}
PLAN_DATA_FILENAMES = {"visual_plan.csv"}
REQUIRED_WORKPACK_MARKERS = [
    "Reader Decision",
    "Reader Takeaway",
    "Core Question",
    "Required Answer Boundary",
    "Paragraph Plan",
    "Evidence Inputs",
    "Claim Register Links",
    "Counterarguments",
    "Required Visuals",
    "Forbidden Claims",
    "Completion Checklist",
]
WEAK_WORKPACK_PATTERNS = [
    r"-\s*chapter_id:\s*$",
    r"\|\s*\|\s*\|\s*\|",
    r"\|\s*1\s*\|\s*\|\s*\|\s*\|",
]


class VisibleTextParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def clean(value: object) -> str:
    return str(value or "").strip().strip("`").strip("*").strip()


def normalize_header(value: str) -> str:
    text = clean(value).lower()
    compact = re.sub(r"\s+", "_", text)
    if "source_id" in compact or "source id" in text:
        return "source_id"
    if "source_ids" in compact or "source ids" in text or "주요 증거" in text:
        return "source_ids"
    if "claim_id" in compact or "claim id" in text:
        return "claim_id"
    if "claim_type" in compact or "classification" in compact or "분류" in text:
        return "claim_type"
    if text == "status" or "readiness" in text or "상태" in text:
        return "status"
    if "evidence_class" in compact:
        return "evidence_class"
    if "original_verified" in compact:
        return "original_verified"
    if "exact_quote_location" in compact or "quote_location" in compact or "page_number" in compact:
        return "exact_quote_location"
    if "url_or_path" in compact or "local path" in text or "로컬 보관 경로" in text:
        return "url_or_path"
    if "title" in compact or "자료명" in text:
        return "title"
    return compact


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


def read_inventory(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def parse_source_record(path: Path) -> dict[str, str]:
    data: dict[str, str] = {"_path": str(path)}
    if not path.exists():
        return data
    for line in read_text(path).splitlines():
        match = re.match(r"\s*[-*]\s*\*\*([^*]+)\*\*\s*:\s*(.*)", line)
        if not match:
            match = re.match(r"\s*[-*]\s*`?([A-Za-z0-9_ -]+)`?\s*:\s*(.*)", line)
        if match:
            data[normalize_header(match.group(1))] = clean(match.group(2))
    return data


def source_record_section(text: str, heading_pattern: str) -> str:
    match = re.search(heading_pattern, text, flags=re.I)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"\n##\s+\d+\.", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def quote_lines(section: str) -> list[str]:
    lines: list[str] = []
    for raw in section.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*>\d.\s]+", "", line).strip().strip('"').strip("'")
        if len(line) >= 18 and not re.fullmatch(r"[A-Za-z0-9_,;:/(). -]+", line):
            lines.append(line)
        elif len(line) >= 40 and " " in line:
            lines.append(line)
    return lines


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


def strip_cover_component(fragment: str) -> str:
    return re.sub(
        r"<section\b[^>]*class=[\"'][^\"']*cover-page[^\"']*[\"'][^>]*>.*?</section>",
        "",
        fragment,
        flags=re.I | re.S,
    )


def html_metrics(path: Path) -> dict[str, int | bool]:
    config = load_config()
    template_markers = [str(item) for item in get_path(config, "report_design.template_markers", [])]
    cover_markers = [str(item) for item in get_path(config, "report_design.cover_component_markers", [])]
    if not path.exists():
        return {
            "visible_chars": 0,
            "tables": 0,
            "figures": 0,
            "source_captions": 0,
            "data_captions": 0,
            "appendix": False,
            "footnotes": 0,
            "uses_template": False,
            "assembled_report": False,
            "uses_cover_component": False,
            "chapter0_summary": False,
        }
    raw = read_text(path)
    visible_html = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
    visible_html_no_style = re.sub(r"<style\b[^>]*>.*?</style>", "", visible_html, flags=re.I | re.S)
    material_html = strip_cover_component(visible_html_no_style)
    parser = VisibleTextParser()
    parser.feed(visible_html)
    visible = parser.text()
    chapter0_summary = bool(
        re.search(
            r"(?:제\s*0\s*장|0\s*[.)]\s*|chapter\s*0)[^\n<]{0,80}(?:요약|executive\s*summary)"
            r"|(?:요약|executive\s*summary)[^\n<]{0,40}(?:제\s*0\s*장|chapter\s*0)",
            visible,
            flags=re.I,
        )
    )
    return {
        "visible_chars": len(visible),
        "tables": len(re.findall(r"<table\b", material_html, flags=re.I)),
        "figures": count_material_figures(material_html),
        "source_captions": visible.count("자료:"),
        "data_captions": visible.count("근거 데이터"),
        "appendix": bool(re.search(r"\b(Appendix|부록)\b", visible, flags=re.I)),
        "footnotes": len(re.findall(r"<sup\b|footnote|주석|참고문헌", raw, flags=re.I)),
        "uses_template": any(marker in raw for marker in template_markers),
        "assembled_report": ('data-assembled-report="true"' in raw or "mode: concatenate_only_no_rewrite" in raw),
        "uses_cover_component": any(marker in raw for marker in cover_markers),
        "chapter0_summary": chapter0_summary,
    }


def docx_metrics(project: Path) -> dict[str, object]:
    docx_files = sorted((project / "reports").glob("*.docx"))
    details = []
    for path in docx_files:
        item: dict[str, object] = {
            "path": path.relative_to(project).as_posix(),
            "valid_zip": False,
            "parts": 0,
            "has_styles": False,
            "has_numbering": False,
            "has_footnotes": False,
            "has_media": False,
            "render_verified": False,
        }
        try:
            with zipfile.ZipFile(path) as zf:
                names = set(zf.namelist())
                item["valid_zip"] = True
                item["parts"] = len(names)
                item["has_styles"] = "word/styles.xml" in names
                item["has_numbering"] = "word/numbering.xml" in names
                item["has_footnotes"] = "word/footnotes.xml" in names or "word/endnotes.xml" in names
                item["has_media"] = any(name.startswith("word/media/") for name in names)
        except zipfile.BadZipFile:
            pass
        rendered_markers = list(project.glob("reports/*docx*render*")) + list(project.glob("evidence/**/*docx*render*"))
        item["render_verified"] = bool(rendered_markers)
        details.append(item)
    return {"docx_files": len(docx_files), "details": details}


def workpack_quality_issues(path: Path) -> list[str]:
    text = read_text(path)
    issues: list[str] = []
    if len(text.strip()) < 900:
        issues.append("too short to guide rich chapter writing")
    missing = [marker for marker in REQUIRED_WORKPACK_MARKERS if marker.lower() not in text.lower()]
    if missing:
        issues.append("missing required workpack sections: " + ", ".join(missing[:6]))
    for pattern in WEAK_WORKPACK_PATTERNS:
        if re.search(pattern, text, flags=re.I | re.M):
            issues.append("contains unfilled template placeholders")
            break
    return issues


def chapter_factory_metrics(project: Path, report_html: dict[str, int | bool]) -> dict[str, object]:
    chapter_dir = project / "reports" / "chapters"
    workpack_dir = project / "reports" / "chapter_workpacks"
    chapter_fragments = sorted(chapter_dir.glob("ch*.html")) if chapter_dir.exists() else []
    chapter_workpacks = sorted(workpack_dir.glob("ch*_workpack.md")) if workpack_dir.exists() else []
    missing_workpacks: list[str] = []
    wrapper_chapters: list[str] = []
    weak_workpacks: list[str] = []
    for chapter in chapter_fragments:
        expected_name = "ch00_summary_workpack.md" if chapter.stem == "ch00_summary" else f"{chapter.stem}_workpack.md"
        if not (workpack_dir / expected_name).exists():
            missing_workpacks.append(chapter.relative_to(project).as_posix())
        text = read_text(chapter)
        if re.search(r"</?(?:html|head|body)\b", text, flags=re.I):
            wrapper_chapters.append(chapter.relative_to(project).as_posix())
    for workpack in chapter_workpacks:
        issues = workpack_quality_issues(workpack)
        if issues:
            weak_workpacks.append(f"{workpack.relative_to(project).as_posix()}: {'; '.join(issues)}")
    ok = bool(
        chapter_fragments
        and chapter_workpacks
        and not missing_workpacks
        and not wrapper_chapters
        and not weak_workpacks
        and bool(report_html.get("assembled_report"))
        and bool(report_html.get("uses_cover_component"))
    )
    return {
        "ok": ok,
        "chapter_fragments": chapter_fragments,
        "chapter_workpacks": chapter_workpacks,
        "missing_workpacks": missing_workpacks,
        "wrapper_chapters": wrapper_chapters,
        "weak_workpacks": weak_workpacks,
    }


def path_exists(project: Path, value: str) -> bool:
    value = clean(value)
    if not value or re.match(r"https?://", value):
        return False
    candidates = [project / value, project.parent / value, Path(value)]
    return any(path.exists() for path in candidates)


def is_backing_data_file(path: Path) -> bool:
    return path.suffix.lower() in DATA_SUFFIXES and path.name.lower() not in PLAN_DATA_FILENAMES


def project_quality(project: Path) -> dict[str, object]:
    config = load_config()
    active_preset = active_domain_preset(config)
    quality_profile = active_quality_profile(config)
    minimum_visuals = int(quality_profile["minimum_visuals"])
    minimum_figures = int(quality_profile["minimum_figures"])
    visual_plan_required = bool(quality_profile["visual_plan_required"])
    inventory = read_inventory(project / "references" / "reference_inventory.csv")
    sources = parse_markdown_table(project / "source_index" / "source_master_index.md")
    claims = parse_markdown_table(project / "reports" / "report_claim_register.md")
    source_record_paths = sorted((project / "references" / "source_records").glob("*.md"))
    source_records = {clean(parse_source_record(path).get("source_id", "")): path for path in source_record_paths}
    reports = sorted((project / "reports").glob("*.html"))
    html = html_metrics(reports[-1]) if reports else html_metrics(Path("__missing__"))
    data_files = [path for path in (project / "data_sources").glob("*") if is_backing_data_file(path)]
    visual_plan = project / "data_sources" / "visual_plan.csv"
    visual_plan_rows = read_inventory(visual_plan)
    chapter_factory = chapter_factory_metrics(project, html)
    chapter_fragments = list(chapter_factory["chapter_fragments"])
    chapter_workpacks = list(chapter_factory["chapter_workpacks"])
    docx = docx_metrics(project)

    hard_blockers: list[str] = []
    opportunities: list[str] = []
    deductions: list[dict[str, object]] = []

    def deduct(points: int, reason: str) -> None:
        deductions.append({"points": points, "reason": reason})

    citable_sources = [row for row in sources if clean(row.get("status") or row.get("source_readiness_status")) == "report_citable"]
    for row in citable_sources:
        source_id = clean(row.get("source_id"))
        if source_id not in source_records:
            hard_blockers.append(f"{source_id}: report_citable source has no source_record")

    original_rows = 0
    exact_url_rows = 0
    preserved_files = 0
    generic_url_rows = 0
    for row in inventory:
        row_has_original = False
        url_or_path = clean(row.get("original_path") or row.get("url_or_path") or row.get("open_path"))
        if row.get("sha256") and row.get("file_size_bytes"):
            preserved_files += 1
            row_has_original = True
        if re.match(r"https?://", url_or_path):
            if GENERIC_URL_RE.match(url_or_path.rstrip("/")):
                generic_url_rows += 1
            else:
                exact_url_rows += 1
                row_has_original = True
        if row_has_original:
            original_rows += 1

    source_score = min(20, preserved_files * 2 + exact_url_rows * 2 + max(0, len(inventory) - generic_url_rows) // 2)
    if generic_url_rows:
        hard_blockers.append(f"{generic_url_rows} inventoried source URLs look like generic homepages")
        deduct(10, "generic homepage URLs reduce source originality and cannot support citable status")

    trace_score = 0
    fake_quote_markers = {"Antigravity", "Answer", "Assumptions", "Implementation Plan"}
    for path in source_record_paths:
        data = parse_source_record(path)
        source_id = clean(data.get("source_id"))
        record_text = read_text(path)
        section = source_record_section(record_text, r"\n##\s+2\.\s*Exact Quotes")
        if source_id:
            trace_score += 1
        if path.stat().st_size >= 1024:
            trace_score += 1
        if clean(data.get("exact_quote_location") or data.get("url_or_path")):
            trace_score += 1
        if any(marker in section for marker in fake_quote_markers):
            hard_blockers.append(f"{source_id or path.name}: Exact Quotes section contains prompt/tool tokens")
            deduct(20, "Exact Quotes contains prompt/tool tokens rather than preserved source text")
    trace_score = min(15, trace_score)
    if len(source_record_paths) < 8 and reports:
        opportunities.append("Add at least 8 auditable source records for a substantial report.")
        deduct(8, "substantial reports earn less when fewer than 8 source records exist")

    claim_score = 0
    for row in claims:
        if clean(row.get("claim_id")):
            claim_score += 1
        if clean(row.get("source_ids") or row.get("source_id")):
            claim_score += 1
        if clean(row.get("exact_quote_location")):
            claim_score += 1
        if "estimate" in clean(row.get("claim_type")).lower() and clean(row.get("data_file_ids")):
            claim_score += 1
    claim_score = min(15, claim_score)
    if claims and claim_score < 10:
        opportunities.append("Raise claim quality by adding exact source locations, assumptions, and data_file_ids.")
        deduct(8, "claim register lacks enough exact locations, assumptions, or data file links")

    depth_score = 0
    visible_chars = int(html["visible_chars"])
    if chapter_factory["ok"]:
        depth_score += 6
    elif chapter_fragments and chapter_workpacks:
        depth_score += 3
    if source_record_paths and claims:
        depth_score += 2
    if visual_plan_rows and data_files:
        depth_score += 2
    if bool(html["appendix"]):
        depth_score += 2
    if bool(html["chapter0_summary"]):
        depth_score += 3
    depth_score = min(15, depth_score)
    if reports and not chapter_factory["ok"]:
        opportunities.append("Improve chapter workpacks and fragments so each chapter answers its own question with evidence, counterarguments, residual risks, visuals, and decision implications.")
    if reports and not bool(html["chapter0_summary"]):
        opportunities.append("Write the final executive summary as Chapter 0 after body sections and visuals are stable.")
        deduct(8, "final report does not include a Chapter 0 summary")

    visual_score = 0
    visuals = int(html["tables"]) + int(html["figures"])
    visual_score += min(5, visuals)
    visual_score += min(5, len(data_files) * 2)
    if int(html["figures"]) >= 1:
        visual_score += 3
    if visual_plan_rows:
        visual_score += 2
    if int(html["source_captions"]) >= visuals and int(html["data_captions"]) >= visuals and visuals:
        visual_score += 2
    visual_score = min(15, visual_score)
    if reports and int(html["figures"]) < minimum_figures:
        opportunities.append("Add real charts, graphs, diagrams, timelines, or flow visuals; a table inside a figure wrapper does not count.")
        deduct(8, f"report has fewer real charts/figures than the active preset expects ({minimum_figures})")
    if reports and visuals and len(data_files) < visuals:
        opportunities.append("Create a separate CSV/XLSX backing file for each material table, graph, figure, or diagram.")
        deduct(10, "tables/figures outnumber local data files; each material visual should have its own dataset")
    visual_plan_ok = (not visual_plan_required) or bool(visual_plan_rows)
    figures_ok = int(html["figures"]) >= minimum_figures
    visuals_ok = visuals >= minimum_visuals
    chapter_factory_ok = bool(chapter_factory["ok"])

    if reports and visual_plan_required and not visual_plan_rows:
        opportunities.append("Create data_sources/visual_plan.csv so visuals are chosen by chapter purpose, not by quota.")
        deduct(4, "active preset expects a visual plan")
    if reports and not chapter_factory_ok:
        opportunities.append("Use chapter workpacks, chapter HTML fragments, reusable cover data, and assemble_report.py before treating the report as internally reviewable.")
        deduct(8, "substantial reports need the chapter factory flow: workpacks, fragments, reusable cover, and assembled report marker")

    template_score = 0
    if html["uses_template"]:
        template_score += 4
    if html.get("uses_cover_component"):
        template_score += 2
    if html.get("assembled_report"):
        template_score += 2
    if chapter_fragments and chapter_workpacks:
        template_score += 2
    if reports and not html["uses_template"]:
        template_score = max(template_score, 4)
    template_score = min(10, template_score)
    if reports and not html["uses_template"]:
        opportunities.append("Use the workspace report template/CSS to make the visual format reproducible.")
        deduct(5, "report does not use or reference the reusable report template/style system")

    docx_score = 0
    if docx["docx_files"]:
        for item in docx["details"]:
            if item["valid_zip"]:
                docx_score += 2
            if item["has_styles"]:
                docx_score += 2
            if item["has_numbering"]:
                docx_score += 1
            if item["has_footnotes"]:
                docx_score += 2
            if item["has_media"]:
                docx_score += 1
            if item["render_verified"]:
                docx_score += 2
        docx_score = min(10, docx_score)
        if docx_score < 8:
            hard_blockers.append("DOCX exists but lacks enough structure/render evidence for delivery-candidate status")
            deduct(10, "DOCX exists but conversion quality is not structurally/render verified")
    else:
        opportunities.append("If DOCX conversion is expected, create and render-check DOCX before delivery.")
        if bool(quality_profile.get("docx_expected_by_default")) and reports:
            deduct(5, "active preset expects a verified DOCX/PDF export path")

    scores = {
        "source_originality": source_score,
        "source_traceability": trace_score,
        "claim_readiness": claim_score,
        "analytical_depth": depth_score,
        "data_visuals": visual_score,
        "template_reproducibility": template_score,
        "docx_pdf_readiness": docx_score,
    }
    raw_bonus_total = sum(scores.values())
    deduction_total = min(60, sum(int(item["points"]) for item in deductions))
    raw_total = max(0, min(100, raw_bonus_total - deduction_total))
    total = min(raw_total, 59) if hard_blockers else raw_total

    level = 0
    if (project / "report_prd").exists() and (project / "drafts").exists() and any((project / "report_prd").glob("*.md")) and any((project / "drafts").glob("*toc*.md")):
        level = 1
    if len(inventory) or source_record_paths or claims:
        level = 2
    if len(source_record_paths) >= 6 and preserved_files >= 3 and not any("Exact Quotes section contains" in b for b in hard_blockers):
        level = 3
    level_constraints = {
        "chapter_depth_ok": chapter_factory_ok,
        "minimum_visuals_ok": visuals_ok,
        "minimum_figures_ok": figures_ok,
        "visual_plan_ok": visual_plan_ok,
        "chapter_factory_ok": chapter_factory_ok,
        "chapter0_summary_ok": bool(html["chapter0_summary"]),
    }
    if (
        total >= 75
        and level_constraints["chapter_depth_ok"]
        and level_constraints["minimum_visuals_ok"]
        and level_constraints["minimum_figures_ok"]
        and level_constraints["visual_plan_ok"]
        and level_constraints["chapter_factory_ok"]
        and not hard_blockers
        and level_constraints["chapter0_summary_ok"]
    ):
        level = 4
    if level >= 4 and docx_score >= 8:
        level = 5
    if hard_blockers and level > 2:
        level = 2

    return {
        "project": project.name,
        "active_domain_preset": {
            "name": active_preset["name"],
            "requested_name": active_preset["requested_name"],
            "label": active_preset["settings"].get("label", active_preset["name"]),
        },
        "active_quality_profile": quality_profile,
        "current_level": f"Level {level}",
        "quality_score": total,
        "bonus_score_before_deductions": raw_bonus_total,
        "deduction_points": deduction_total,
        "raw_quality_score_before_hard_blocker_cap": raw_total,
        "scores": scores,
        "level_constraints": level_constraints,
        "deductions": deductions,
        "hard_blockers": hard_blockers,
        "score_lift_opportunities": opportunities[:10],
        "metrics": {
            "inventory_rows": len(inventory),
            "source_records": len(source_record_paths),
            "claims": len(claims),
            "reports": len(reports),
            "visible_chars": visible_chars,
            "tables": html["tables"],
            "figures_or_charts": html["figures"],
            "data_files": len(data_files),
            "visual_plan_rows": len(visual_plan_rows),
            "chapter_fragments": len(chapter_fragments),
            "chapter_workpacks": len(chapter_workpacks),
            "chapter_factory_missing_workpacks": chapter_factory["missing_workpacks"],
            "chapter_factory_wrapper_chapters": chapter_factory["wrapper_chapters"],
            "chapter_factory_weak_workpacks": chapter_factory["weak_workpacks"],
            "docx": docx,
        },
    }


def render_quality_status_html(payload: dict[str, object]) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value if value is not None else ""), quote=True)

    def list_items(values: object, empty: str) -> str:
        if not isinstance(values, list) or not values:
            return f"<li>{esc(empty)}</li>"
        return "".join(f"<li>{esc(item)}</li>" for item in values)

    scores = payload.get("scores", {})
    metrics = payload.get("metrics", {})
    active_preset = payload.get("active_domain_preset", {})
    deductions = payload.get("deductions", [])
    if isinstance(scores, dict):
        score_rows = "".join(
            f"<tr><th>{esc(key)}</th><td>{esc(value)}</td></tr>" for key, value in scores.items()
        )
    else:
        score_rows = ""
    if isinstance(metrics, dict):
        metric_rows = "".join(
            f"<tr><th>{esc(key)}</th><td>{esc(json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value)}</td></tr>"
            for key, value in metrics.items()
        )
    else:
        metric_rows = ""
    if isinstance(deductions, list) and deductions:
        deduction_rows = "".join(
            f"<tr><td>{esc(item.get('points') if isinstance(item, dict) else '')}</td><td>{esc(item.get('reason') if isinstance(item, dict) else item)}</td></tr>"
            for item in deductions
        )
    else:
        deduction_rows = "<tr><td colspan=\"2\">감점 없음</td></tr>"

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(payload.get("project"))} 품질 상태</title>
  <style>
    body {{ margin:0; font-family:"Malgun Gothic","Noto Sans KR",Arial,sans-serif; color:#111827; background:#fff; line-height:1.65; }}
    main {{ max-width:1040px; margin:32px auto; padding:0 24px 56px; }}
    header {{ border-bottom:3px solid #111827; padding-bottom:18px; margin-bottom:20px; }}
    h1 {{ margin:0 0 8px; font-size:30px; }}
    h2 {{ margin:26px 0 10px; font-size:18px; }}
    .summary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin:18px 0; }}
    .tile {{ border:1px solid #d1d5db; padding:14px; }}
    .label {{ color:#6b7280; font-size:13px; }}
    .value {{ font-size:24px; font-weight:800; }}
    table {{ width:100%; border-collapse:collapse; border-top:2px solid #111827; }}
    th, td {{ border-bottom:1px solid #e5e7eb; padding:9px 10px; text-align:left; vertical-align:top; font-size:14px; }}
    th {{ width:260px; background:#f9fafb; }}
    ul {{ margin:8px 0 0 20px; padding:0; }}
    .note {{ color:#4b5563; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>{esc(payload.get("project"))} 품질 상태</h1>
    <p class="note">이 패널은 보고서 품질 점수의 사람이 읽기 쉬운 요약입니다. 환경 검증이나 법률 의견을 대체하지 않습니다.</p>
  </header>
  <section class="summary">
    <div class="tile"><div class="label">현재 레벨</div><div class="value">{esc(payload.get("current_level"))}</div></div>
    <div class="tile"><div class="label">품질 점수</div><div class="value">{esc(payload.get("quality_score"))}</div></div>
    <div class="tile"><div class="label">감점</div><div class="value">{esc(payload.get("deduction_points"))}</div></div>
    <div class="tile"><div class="label">하드 블로커</div><div class="value">{esc(len(payload.get("hard_blockers", [])) if isinstance(payload.get("hard_blockers"), list) else 0)}</div></div>
  </section>
  <p class="note">활성 프리셋: {esc(active_preset.get("name") if isinstance(active_preset, dict) else "")}</p>
  <h2>하드 블로커</h2>
  <ul>{list_items(payload.get("hard_blockers"), "없음")}</ul>
  <h2>점수 상승 기회</h2>
  <ul>{list_items(payload.get("score_lift_opportunities"), "없음")}</ul>
  <h2>세부 점수</h2>
  <table>{score_rows}</table>
  <h2>감점 사유</h2>
  <table><thead><tr><th>점수</th><th>사유</th></tr></thead><tbody>{deduction_rows}</tbody></table>
  <h2>주요 지표</h2>
  <table>{metric_rows}</table>
</main>
</body>
</html>
"""


def write_quality_status(project: Path, payload: dict[str, object], status_dir: str) -> dict[str, str]:
    output_dir = project / status_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "quality_status.json"
    html_path = output_dir / "quality_status.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_quality_status_html(payload), encoding="utf-8")
    return {
        "json": json_path.relative_to(project).as_posix(),
        "html": html_path.relative_to(project).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score report quality and report level.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--write-status", action="store_true", help="Write reports/quality_status/quality_status.json and .html.")
    parser.add_argument("--status-dir", default="reports/quality_status", help="Project-relative output directory for --write-status.")
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2
    payload = project_quality(project)
    if args.write_status:
        payload["quality_status_written"] = write_quality_status(project, payload, args.status_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["hard_blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
