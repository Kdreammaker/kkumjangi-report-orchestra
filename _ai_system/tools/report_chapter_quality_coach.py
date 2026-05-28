from __future__ import annotations

import argparse
import html
import html.parser
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from report_quality_schema import REQUIRED_WORKPACK_MARKERS


PROJECT_ROOT = Path("00_사용자_작업공간")

DECISION_TERMS = ["의사결정", "판단", "선택", "대안", "권고", "실행", "implication", "decision"]
RISK_TERMS = ["리스크", "위험", "한계", "반론", "잔존", "불확실", "counter", "risk", "limitation"]
EVIDENCE_TERMS = ["자료:", "근거", "출처", "각주", "참고문헌", "source", "evidence"]
OVERCLAIM_TERMS = ["100% 보장", "완벽", "완전한 보호", "무조건", "절대", "압도적", "최고 수준"]
WORKPACK_SECTIONS = REQUIRED_WORKPACK_MARKERS
SECTION_RE = re.compile(r"^\s{0,3}(?:#{1,6}\s*)?([A-Za-z][A-Za-z ]{3,40})\s*:?\s*$", re.M)
CLAIM_ID_RE = re.compile(r"\b(?:claim|c)[-_]?\d{2,4}\b", re.I)
VISUAL_ID_RE = re.compile(r"\b(?:vis|fig|table|chart)[-_]?\d{2,4}\b", re.I)


class VisibleTextParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S KST")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def visible_text(raw_html: str) -> str:
    cleaned = re.sub(r"<!--.*?-->", "", raw_html, flags=re.S)
    cleaned = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", "", cleaned, flags=re.I | re.S)
    parser = VisibleTextParser()
    parser.feed(cleaned)
    return parser.text()


def strip_tags(fragment: str) -> str:
    text = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", "", fragment, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def thin_subsections(raw_html: str, threshold_chars: int = 260) -> list[str]:
    body = re.sub(r"<!--.*?-->", "", raw_html, flags=re.S)
    parts = re.split(r"(<h[23]\b[^>]*>.*?</h[23]>)", body, flags=re.I | re.S)
    thin: list[str] = []
    for index in range(1, len(parts), 2):
        heading_html = parts[index]
        content_html = parts[index + 1] if index + 1 < len(parts) else ""
        heading = strip_tags(heading_html)
        content = strip_tags(content_html)
        if heading and len(content) < threshold_chars:
            thin.append(f"{heading} ({len(content)} chars)")
    return thin[:12]


def has_any(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def normalized_tokens(text: str) -> set[str]:
    raw = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}|[가-힣]{2,}", text)
    stop = {
        "reader",
        "decision",
        "takeaway",
        "question",
        "required",
        "answer",
        "boundary",
        "claim",
        "register",
        "links",
        "counterarguments",
        "visuals",
        "chapter",
        "workpack",
        "자료",
        "근거",
        "출처",
    }
    return {item.lower() for item in raw if item.lower() not in stop}


def workpack_section_presence(workpack_text: str) -> dict[str, bool]:
    lowered = workpack_text.lower()
    return {section: section.lower() in lowered for section in WORKPACK_SECTIONS}


def workpack_alignment(project: Path, chapter: Path, raw_html: str, visible: str) -> dict[str, object]:
    workpack = matching_workpack(project, chapter)
    workpack_text = read_text(workpack)
    if not workpack_text:
        return {
            "workpack_sections_present": {},
            "workpack_section_coverage": 0.0,
            "workpack_term_overlap": 0.0,
            "claim_links_in_workpack": [],
            "claim_links_in_chapter": [],
            "missing_claim_links": [],
            "visual_links_in_workpack": [],
            "visual_links_in_chapter": [],
            "missing_visual_links": [],
        }
    section_presence = workpack_section_presence(workpack_text)
    section_coverage = sum(1 for value in section_presence.values() if value) / max(len(section_presence), 1)
    workpack_tokens = normalized_tokens(workpack_text)
    chapter_tokens = normalized_tokens(visible)
    useful_workpack_tokens = {token for token in workpack_tokens if len(token) >= 4 or re.search(r"[가-힣]", token)}
    overlap = len(useful_workpack_tokens & chapter_tokens) / max(len(useful_workpack_tokens), 1)
    claim_links = sorted({item.lower() for item in CLAIM_ID_RE.findall(workpack_text)})
    chapter_claim_links = sorted({item.lower() for item in CLAIM_ID_RE.findall(raw_html)})
    visual_links = sorted({item.lower() for item in VISUAL_ID_RE.findall(workpack_text)})
    chapter_visual_links = sorted({item.lower() for item in VISUAL_ID_RE.findall(raw_html)})
    return {
        "workpack_sections_present": section_presence,
        "workpack_section_coverage": round(section_coverage, 3),
        "workpack_term_overlap": round(overlap, 3),
        "claim_links_in_workpack": claim_links,
        "claim_links_in_chapter": chapter_claim_links,
        "missing_claim_links": [item for item in claim_links if item not in chapter_claim_links],
        "visual_links_in_workpack": visual_links,
        "visual_links_in_chapter": chapter_visual_links,
        "missing_visual_links": [item for item in visual_links if item not in chapter_visual_links],
    }


def count_figures(raw_html: str) -> int:
    figure_blocks = re.findall(r"<figure\b[^>]*>.*?</figure>", raw_html, flags=re.I | re.S)
    true_figure_blocks = [
        block
        for block in figure_blocks
        if re.search(r"<(?:svg|img|canvas)\b", block, flags=re.I)
        or re.search(r"class=[\"'][^\"']*(?:chart|graph|diagram|timeline|flow)[^\"']*[\"']", block, flags=re.I)
    ]
    remainder = re.sub(r"<figure\b[^>]*>.*?</figure>", "", raw_html, flags=re.I | re.S)
    media = len(re.findall(r"<(?:svg|img|canvas)\b", remainder, flags=re.I))
    chart_classes = len(re.findall(r"class=[\"'][^\"']*(?:chart|graph|diagram|timeline|flow)[^\"']*[\"']", remainder, flags=re.I))
    return len(true_figure_blocks) + media + chart_classes


def rel(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def matching_workpack(project: Path, chapter: Path) -> Path:
    if chapter.stem.startswith("ch00"):
        return project / "reports" / "chapter_workpacks" / "ch00_summary_workpack.md"
    return project / "reports" / "chapter_workpacks" / f"{chapter.stem}_workpack.md"


def advice_for(metrics: dict[str, object], is_summary: bool) -> list[str]:
    advice: list[str] = []
    if not metrics["workpack_exists"]:
        advice.append("Create the matching chapter workpack before revising prose.")
    elif float(metrics.get("workpack_section_coverage", 0.0)) < 0.7:
        advice.append("Complete the chapter workpack sections before judging the prose.")
    elif float(metrics.get("workpack_term_overlap", 0.0)) < 0.18 and not is_summary:
        advice.append("Revise the chapter so it answers the concrete questions and boundaries in the workpack.")
    if metrics.get("missing_claim_links"):
        advice.append("Add hidden claim-link comments or revise the prose so workpack claim links are traceable.")
    if metrics.get("missing_visual_links"):
        advice.append("Implement or explicitly retire required visual links from the workpack.")
    if int(metrics["visible_chars"]) < (900 if is_summary else 1200):
        advice.append("Expand the chapter around the reader decision, evidence, implications, and residual risks instead of padding generic prose.")
    if metrics.get("thin_subsections"):
        advice.append("Expand thin subsections so headings do not end after two or three sentences: " + " | ".join(list(metrics["thin_subsections"])[:3]))
    if not is_summary and not metrics["has_decision_signal"]:
        advice.append("Add a clear reader decision/use implication so the chapter does not become background-only.")
    if not is_summary and not metrics["has_risk_or_counterargument"]:
        advice.append("Add counterarguments, limitations, or residual risks before treating the chapter as analysis-complete.")
    if not metrics["has_evidence_signal"]:
        advice.append("Add source/citation language or table/figure source notes tied to source records.")
    if not metrics["has_data_caption"] and (int(metrics["tables"]) or int(metrics["figures"])):
        advice.append("Add visible 근거 데이터: captions for the chapter's tables/figures.")
    if metrics["overclaim_terms"]:
        advice.append("Remove or qualify overclaim language: " + ", ".join(metrics["overclaim_terms"]))
    return advice


def analyze_chapter(project: Path, chapter: Path) -> dict[str, object]:
    raw = read_text(chapter)
    text = visible_text(raw)
    workpack = matching_workpack(project, chapter)
    is_summary = chapter.stem.startswith("ch00")
    overclaims = [term for term in OVERCLAIM_TERMS if term in text]
    alignment = workpack_alignment(project, chapter, raw, text)
    metrics: dict[str, object] = {
        "chapter": rel(chapter, project),
        "workpack": rel(workpack, project),
        "workpack_exists": workpack.exists(),
        "is_summary": is_summary,
        "visible_chars": len(text),
        "thin_subsections": thin_subsections(raw),
        "tables": len(re.findall(r"<table\b", raw, flags=re.I)),
        "figures": count_figures(raw),
        "has_decision_signal": has_any(text, DECISION_TERMS),
        "has_risk_or_counterargument": has_any(text, RISK_TERMS),
        "has_evidence_signal": has_any(text, EVIDENCE_TERMS),
        "has_data_caption": "근거 데이터" in text,
        "overclaim_terms": overclaims,
        **alignment,
    }
    advice = advice_for(metrics, is_summary)
    if not chapter.exists():
        status = "missing"
    elif advice:
        status = "needs_attention"
    else:
        status = "strong_signal"
    metrics["status"] = status
    metrics["advice"] = advice
    return metrics


def analyze_project(project_name: str) -> dict[str, object]:
    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"error": f"project not found: {project_name}"}
    chapter_dir = project / "reports" / "chapters"
    chapters = sorted(chapter_dir.glob("ch*.html")) if chapter_dir.exists() else []
    rows = [analyze_chapter(project, chapter) for chapter in chapters]
    summary = {
        "chapters_checked": len(rows),
        "strong_signal": sum(1 for row in rows if row.get("status") == "strong_signal"),
        "needs_attention": sum(1 for row in rows if row.get("status") == "needs_attention"),
        "missing_workpacks": sum(1 for row in rows if not row.get("workpack_exists")),
        "weak_workpack_alignment": sum(
            1
            for row in rows
            if row.get("workpack_exists")
            and (
                float(row.get("workpack_section_coverage", 0.0)) < 0.7
                or float(row.get("workpack_term_overlap", 0.0)) < 0.18
                or bool(row.get("missing_claim_links"))
                or bool(row.get("missing_visual_links"))
            )
        ),
        "overclaim_chapters": sum(1 for row in rows if row.get("overclaim_terms")),
    }
    next_actions: list[str] = []
    if not rows:
        next_actions.append("Create chapter workpacks and chapter fragments before running chapter quality review.")
    for row in rows:
        if row.get("status") == "needs_attention":
            chapter = str(row.get("chapter"))
            first = row.get("advice", ["Improve chapter completeness."])[0]
            next_actions.append(f"{chapter}: {first}")
    return {
        "project": project_name,
        "generated_at_kst": now_kst(),
        "purpose": "chapter-level quality coach; this is not source-truth validation",
        "summary": summary,
        "chapters": rows,
        "next_actions": next_actions[:12],
        "notes": [
            "This coach favors decision usefulness, counterarguments, residual risks, evidence signals, and data captions over raw character count.",
            "It does not verify whether the cited source is true; run research integrity and artifact validators separately.",
        ],
    }


def render_html(payload: dict[str, object]) -> str:
    project = html.escape(str(payload.get("project", "")))
    summary = payload.get("summary", {})
    chapters = payload.get("chapters", [])
    actions = payload.get("next_actions", [])
    if not isinstance(summary, dict):
        summary = {}
    if not isinstance(chapters, list):
        chapters = []
    if not isinstance(actions, list):
        actions = []

    cards = "\n".join(
        f"<div class='metric'><strong>{html.escape(str(key))}</strong><span>{html.escape(str(value))}</span></div>"
        for key, value in summary.items()
    )
    action_items = "\n".join(f"<li>{html.escape(str(action))}</li>" for action in actions) or "<li>없음</li>"
    rows = []
    for row in chapters:
        if not isinstance(row, dict):
            continue
        advice = row.get("advice", [])
        advice_text = "; ".join(str(item) for item in advice) if isinstance(advice, list) else str(advice)
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('chapter', '')))}</td>"
            f"<td>{html.escape(str(row.get('status', '')))}</td>"
            f"<td>{html.escape(str(row.get('visible_chars', '')))}</td>"
            f"<td>{html.escape(str(row.get('tables', '')))} / {html.escape(str(row.get('figures', '')))}</td>"
            f"<td>{html.escape(str(row.get('workpack_section_coverage', '')))} / {html.escape(str(row.get('workpack_term_overlap', '')))}</td>"
            f"<td>{html.escape(advice_text)}</td>"
            "</tr>"
        )
    chapter_rows = "\n".join(rows) or "<tr><td colspan='5'>챕터 조각이 없습니다.</td></tr>"
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Chapter Quality Coach - {project}</title>
  <style>
    :root {{ --ink:#1f2933; --muted:#65707d; --line:#d8dee6; --soft:#f6f8fb; --accent:#1f6feb; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; color:var(--ink); background:#fff; }}
    main {{ max-width:1040px; margin:0 auto; padding:40px 28px 56px; }}
    header {{ border-bottom:2px solid var(--ink); margin-bottom:22px; padding-bottom:18px; }}
    h1 {{ margin:0 0 8px; font-size:30px; letter-spacing:0; }}
    .meta, .note {{ color:var(--muted); }}
    .grid {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; margin:18px 0; }}
    .metric {{ border:1px solid var(--line); background:var(--soft); padding:12px; }}
    .metric strong {{ display:block; font-size:13px; color:var(--muted); }}
    .metric span {{ display:block; margin-top:6px; font-size:22px; font-weight:700; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th, td {{ border:1px solid var(--line); padding:9px 10px; text-align:left; vertical-align:top; }}
    th {{ background:var(--soft); }}
    @media (max-width:820px) {{ .grid {{ grid-template-columns:1fr 1fr; }} main {{ padding:28px 18px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Chapter Quality Coach</h1>
    <p class="meta">{project} · {html.escape(str(payload.get("generated_at_kst", "")))} · 장별 품질 코치이며 원문 진위 검증이 아닙니다.</p>
  </header>
  <section class="grid">{cards}</section>
  <section>
    <h2>다음 보완 작업</h2>
    <ul>{action_items}</ul>
  </section>
  <section>
    <h2>챕터별 상태</h2>
    <table>
      <thead><tr><th>Chapter</th><th>Status</th><th>Visible chars</th><th>Tables/Figures</th><th>Workpack coverage/overlap</th><th>Advice</th></tr></thead>
      <tbody>{chapter_rows}</tbody>
    </table>
  </section>
  <p class="note">분량은 신호일 뿐입니다. 의사결정 유용성, 반론, 잔존 리스크, 근거 연결, 데이터 캡션을 우선 보완하세요.</p>
</main>
</body>
</html>
"""


def write_status(project_name: str, payload: dict[str, object]) -> dict[str, str]:
    project = PROJECT_ROOT / project_name
    status_dir = project / "reports" / "chapter_quality"
    status_dir.mkdir(parents=True, exist_ok=True)
    json_path = status_dir / "chapter_quality.json"
    html_path = status_dir / "chapter_quality.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    html_path.write_text(render_html(payload), encoding="utf-8", newline="\n")
    return {"json": rel(json_path, project), "html": rel(html_path, project)}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Coach chapter-level report quality beyond raw length.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--write-status", action="store_true", help="Write reports/chapter_quality/chapter_quality.json and .html")
    args = parser.parse_args()
    payload = analyze_project(args.project)
    if args.write_status and "error" not in payload:
        payload["status_files"] = write_status(args.project, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if "error" in payload else 0


if __name__ == "__main__":
    raise SystemExit(main())
