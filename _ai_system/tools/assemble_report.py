from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from report_inline_styles import REPORT_INLINE_STYLES, cover_styles, style_attr
from workspace_config import active_domain_preset, css_variable_block, get_path, load_config


PROJECT_ROOT = Path("00_사용자_작업공간")
TEMPLATE_ROOT = Path("_ai_system") / "templates" / "report_html"
COVER_ROOT = TEMPLATE_ROOT / "cover"
DEFAULT_OUTPUT = Path("reports") / "internal_review_report.html"
RUNTIME_ROOT = Path("_ai_system") / "runtime"
STYLE_PASS_REQUIRED = [
    "style_risk_findings.json",
    "protected_spans.json",
    "style_rewrite_diff.md",
    "style_fidelity_review.md",
    "style_naturalness_review.md",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def escape_value(value: object) -> str:
    return html.escape(str(value), quote=False)


DEFAULT_CONFIDENTIAL_NOTICE = (
    "본 문서는 지정된 수신자에 한하여 제공되는 대외비 자료입니다. "
    "사전 승인 없이 문서의 전부 또는 일부를 복제, 배포, 전송, 공개하거나 제3자에게 제공할 수 없습니다. "
    "무단 사용 또는 유출이 확인될 경우 관련 법령 및 계약에 따라 필요한 조치를 취할 수 있습니다."
)


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "대외비", "confidential"}


def confidential_from_cover_data(data: dict[str, object]) -> bool:
    explicit = data.get("is_confidential")
    if isinstance(explicit, bool):
        return explicit
    if truthy(explicit):
        return True

    status = str(data.get("confidentiality_status", "")).strip().lower()
    if status in {"대외비", "confidential"}:
        return True
    if status in {"대외비 아님", "not_confidential", "not confidential", "public", "공개", ""}:
        return False

    fields = [data.get("security_level", ""), data.get("security_tag", "")]
    return any(truthy(value) for value in fields)


def display_classification(value: object) -> str:
    text = str(value).strip()
    if not text:
        return ""
    text = text.strip("[] ")
    text = re.sub(r"(?i)\bconfidential\b", "", text)
    text = text.replace("대외비", "").replace("기밀", "")
    text = re.sub(r"\s*(/|\\|\||·|-)+\s*", " / ", text)
    text = re.sub(r"^(?:/|\\|\||·|-|\s)+|(?:/|\\|\||·|-|\s)+$", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def optional_cover_tokens(data: dict[str, object], preset: dict[str, object]) -> dict[str, str]:
    styles = cover_styles(preset)
    logo_path = str(data.get("logo_path", "")).strip()
    logo_alt = str(data.get("logo_alt", "회사 로고")).strip() or "회사 로고"
    logo_html = (
        f'<div class="cover-logo"{style_attr(styles["cover_logo"])}>'
        f'<img class="cover-logo-image" src="{html.escape(logo_path, quote=True)}" '
        f'alt="{html.escape(logo_alt, quote=True)}"{style_attr(styles["cover_logo_img"])}></div>'
        if logo_path
        else ""
    )
    is_confidential = confidential_from_cover_data(data)
    security_tag = str(data.get("security_tag", "")).strip()
    if is_confidential and not security_tag:
        security_tag = "대외비 / Confidential"
    tag_class = "cover-security-tag" if is_confidential else "cover-status-tag"
    tag_style = styles["cover_security_tag"] if is_confidential else styles["cover_status_tag"]
    security_tag_html = (
        f'<span class="{tag_class}"{style_attr(tag_style)}>{html.escape(security_tag, quote=False)}</span>'
        if security_tag
        else ""
    )
    notice = str(data.get("confidential_notice", "")).strip()
    if is_confidential and not notice:
        notice = DEFAULT_CONFIDENTIAL_NOTICE
    confidential_notice_html = (
        f'<p class="cover-confidential-notice"{style_attr(styles["confidential_notice"])}>'
        f'{html.escape(notice, quote=False)}</p>'
        if notice
        else ""
    )
    return {
        "logo_html": logo_html,
        "security_tag_html": security_tag_html,
        "confidential_notice_html": confidential_notice_html,
    }


def load_cover_preset(data: dict[str, object]) -> dict[str, object]:
    preset_name = str(data.get("cover_preset", "")).strip()
    if not preset_name:
        return {}
    presets_path = COVER_ROOT / "cover.presets.json"
    if not presets_path.exists():
        return {}
    payload = json.loads(read_text(presets_path))
    presets = payload.get("presets", {}) if isinstance(payload, dict) else {}
    preset = presets.get(preset_name, {}) if isinstance(presets, dict) else {}
    return preset if isinstance(preset, dict) else {}


def cover_field(data: dict[str, object], preset: dict[str, object], field: str) -> str:
    value = str(data.get(field, "")).strip()
    if value:
        return value
    defaults = preset.get("defaults", {}) if isinstance(preset.get("defaults"), dict) else {}
    return str(defaults.get(field, "")).strip()


def render_meta_table(data: dict[str, object], preset: dict[str, object]) -> str:
    styles = cover_styles(preset)
    rows = preset.get("meta_rows")
    if not isinstance(rows, list) or not rows:
        rows = [
            [{"label": "프로젝트", "field": "project_name"}, {"label": "보고서 번호", "field": "report_no"}],
            [{"label": "작성일", "field": "date"}, {"label": "버전", "field": "version"}],
            [{"label": "작성 주체", "field": "prepared_by"}, {"label": "검토 대상", "field": "prepared_for"}],
            [{"label": "배포 범위", "field": "distribution"}],
        ]
    html_rows: list[str] = []
    for row in rows:
        if not isinstance(row, list):
            continue
        cells: list[str] = []
        for item in row:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "")).strip()
            field = str(item.get("field", "")).strip()
            value = cover_field(data, preset, field)
            if not label or not value:
                continue
            cells.append(
                f"<th{style_attr(styles['meta_th'])}>{html.escape(label)}</th>"
                f"<td{style_attr(styles['meta_td'])}>{html.escape(value, quote=False)}</td>"
            )
        if cells:
            if len(cells) == 1:
                cells[0] = cells[0].replace("<td", '<td colspan="3"', 1)
            html_rows.append("<tr>" + "".join(cells) + "</tr>")
    if not html_rows:
        return ""
    return (
        f'<table class="cover-meta-table" aria-label="문서 관리 정보"{style_attr(styles["meta_table"])}>'
        "<tbody>"
        + "".join(html_rows)
        + "</tbody></table>"
    )


def render_approval(data: dict[str, object], preset: dict[str, object]) -> str:
    styles = cover_styles(preset)
    slots = preset.get("approval_slots")
    if not isinstance(slots, list):
        slots = [
            {"label": "작성", "field": "approval_author"},
            {"label": "검토", "field": "approval_reviewer"},
            {"label": "승인", "field": "approval_approver"},
        ]
    cards: list[str] = []
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        label = str(slot.get("label", "")).strip()
        field = str(slot.get("field", "")).strip()
        value = cover_field(data, preset, field)
        if label and value:
            cards.append(
                f"<td{style_attr(styles['approval_card'])}>"
                f"<span{style_attr(styles['approval_label'])}>{html.escape(label)}</span>"
                f"<strong{style_attr(styles['approval_name'])}>{html.escape(value, quote=False)}</strong>"
                "</td>"
            )
    if not cards:
        return ""
    return (
        f'<table class="cover-approval cover-approval-{len(cards)}" aria-label="검토 및 승인"'
        f'{style_attr(styles["approval_table"])}><tbody><tr>'
        + "".join(cards)
        + "</tr></tbody></table>"
    )


def render_cover(data: dict[str, object]) -> str:
    template = read_text(COVER_ROOT / "cover.html")
    preset = load_cover_preset(data)
    defaults = preset.get("defaults", {}) if isinstance(preset.get("defaults"), dict) else {}
    styles = cover_styles(preset)
    tokens: dict[str, object] = {
        **defaults,
        **data,
        **optional_cover_tokens(data, preset),
        "meta_table_html": render_meta_table(data, preset),
        "approval_html": render_approval(data, preset),
        **{f"{key}_style_attr": style_attr(value) for key, value in styles.items()},
    }
    tokens["classification"] = display_classification(tokens.get("classification", ""))
    for key, value in tokens.items():
        if key.endswith("_html"):
            template = template.replace("{{" + key + "}}", str(value))
        else:
            template = template.replace("{{" + key + "}}", escape_value(value))
    missing = sorted(set(re.findall(r"{{([a-zA-Z0-9_]+)}}", template)))
    if missing:
        raise ValueError("cover data is missing required field(s): " + ", ".join(missing))
    template = re.sub(r"<p class=\"kicker\"[^>]*>\s*</p>\s*", "", template)
    template = re.sub(r"<p class=\"subtitle\"[^>]*>\s*</p>\s*", "", template)
    template = re.sub(r"<p class=\"cover-purpose\"[^>]*>\s*</p>\s*", "", template)
    return template


def load_manifest(project: Path) -> dict[str, object]:
    path = project / "reports" / "report_assembly_manifest.json"
    if not path.exists():
        return {}
    return json.loads(read_text(path))


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def link_label(url: str) -> str:
    if not url:
        return ""
    safe_url = html.escape(url, quote=True)
    return f'<a href="{safe_url}">원문 링크</a>'


def visual_data_labels(project: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for row in read_csv_rows(project / "data_sources" / "visual_plan.csv"):
        data_file = (
            row.get("data_file")
            or row.get("source_data")
            or row.get("data_or_source_artifact")
            or row.get("data_artifact")
            or ""
        ).strip()
        if not data_file:
            continue
        name = Path(data_file).name
        title = (row.get("title") or row.get("visual_title") or row.get("reader_decision") or "").strip()
        if title:
            labels[name] = title
    return labels


def build_reference_appendices(project: Path) -> str:
    styles = REPORT_INLINE_STYLES
    sections: list[str] = []
    source_rows = read_csv_rows(project / "references" / "source_link_register.csv")
    source_rows = [row for row in source_rows if (row.get("title") or row.get("official_url") or row.get("url") or row.get("publisher"))]
    if source_rows:
        rows_html = []
        for index, row in enumerate(source_rows, start=1):
            rows_html.append(
                "<tr>"
                f"<td{style_attr(styles['td'])}>{index}</td>"
                f"<td{style_attr(styles['td'])}>{html.escape(row.get('title', ''), quote=False)}</td>"
                f"<td{style_attr(styles['td'])}>{html.escape(row.get('publisher', ''), quote=False)}</td>"
                f"<td{style_attr(styles['td'])}>{link_label(row.get('official_url') or row.get('url', ''))}</td>"
                "</tr>"
            )
        sections.append(
            f"""
<section id="report-references" class="report-references">
  <h1{style_attr(styles["h1"])}>참고자료</h1>
  <p class="appendix-note"{style_attr(styles["appendix_note"])}>아래 목록은 독자가 원자료를 따라갈 수 있도록 정리한 reader-facing 참고자료입니다. 내부 추적 번호, 접근일, 사용 수준, 로컬 캡처 경로는 추적용 register에 보관합니다.</p>
  <table class="report-table appendix-table" aria-label="참고자료 목록"{style_attr(styles["table"])}>
    <thead><tr><th{style_attr(styles["th"])}>No.</th><th{style_attr(styles["th"])}>자료명</th><th{style_attr(styles["th"])}>발행기관</th><th{style_attr(styles["th"])}>원문</th></tr></thead>
    <tbody>
"""
            + "\n".join(rows_html)
            + f"""
    </tbody>
  </table>
  <p class="caption"{style_attr(styles["caption"])}>자료: 출처 링크 등록표와 source records. 근거 데이터: 참고자료 목록.</p>
</section>
"""
        )

    appendices_dir = project / "reports" / "appendices"
    if appendices_dir.exists():
        for appendix in sorted(appendices_dir.glob("*.html")):
            sections.append(read_text(appendix))

    labels = visual_data_labels(project)
    data_files = sorted(
        path for path in (project / "data_sources").glob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls", ".tsv"} and path.name != "visual_plan.csv"
    )
    if data_files:
        rows_html = []
        for index, path in enumerate(data_files, start=1):
            label = labels.get(path.name) or path.stem.replace("_", " ")
            rows_html.append(
                "<tr>"
                f"<td{style_attr(styles['td'])}>{index}</td>"
                f"<td{style_attr(styles['td'])}>{html.escape(label, quote=False)}</td>"
                f"<td{style_attr(styles['td'])}>{html.escape(path.name, quote=False)}<!-- {html.escape(path.relative_to(project).as_posix(), quote=False)} --></td>"
                f"<td{style_attr(styles['td'])}>{path.stat().st_size}</td>"
                "</tr>"
            )
        sections.append(
            f"""
<section id="appendix-data-artifacts" class="appendix report-appendix">
  <h1{style_attr(styles["h1"])}>부록. 분석 데이터 목록</h1>
  <p class="appendix-note"{style_attr(styles["appendix_note"])}>아래 파일은 표·그래프·다이어그램을 재현하거나 검토하기 위한 로컬 분석 데이터입니다. 원문 출처를 대체하지 않습니다.</p>
  <table class="report-table appendix-table" aria-label="분석 데이터 목록"{style_attr(styles["table"])}>
    <thead><tr><th{style_attr(styles["th"])}>No.</th><th{style_attr(styles["th"])}>데이터셋</th><th{style_attr(styles["th"])}>파일명</th><th{style_attr(styles["th"])}>크기(bytes)</th></tr></thead>
    <tbody>
"""
            + "\n".join(rows_html)
            + f"""
    </tbody>
  </table>
  <p class="caption"{style_attr(styles["caption"])}>자료: visual plan과 data_sources 등록 파일. 근거 데이터: 분석 데이터 목록.</p>
</section>
"""
        )
    return "\n".join(sections)


def copy_runtime_assets(project: Path) -> list[str]:
    copied: list[str] = []
    asset_pairs = [
        (RUNTIME_ROOT / "fonts" / "pretendard", project / "reports" / "assets" / "fonts" / "pretendard"),
    ]
    for source, target in asset_pairs:
        if source.exists() and source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            copied.append(target.relative_to(project).as_posix())
    return copied


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_integrity(path: Path, project: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(project).as_posix(),
        "sha256": sha256_bytes(data),
        "bytes": len(data),
        "mtime_ns": path.stat().st_mtime_ns,
    }


def update_workflow_status(project: Path, output_rel: str, chapters: list[Path]) -> None:
    out_dir = project / "reports" / "workflow_status"
    out_dir.mkdir(parents=True, exist_ok=True)
    visual_pass = project / "reports" / "visual_pass_manifest.json"
    visual_review = project / "reports" / "visual_review.md"
    payload = {
        "project": project.name,
        "generated_at_kst": now_kst(),
        "purpose": "assembly status; this is not content or source-truth validation",
        "current_step": "assembled_report_ready_for_review_gates" if (visual_pass.exists() or visual_review.exists()) else "assembled_report_exists_visual_review_missing",
        "next_action": "run_review_candidate_gates" if (visual_pass.exists() or visual_review.exists()) else "complete_visual_review_then_reassemble",
        "active_report": output_rel,
        "assembly_mode": "concatenate_only_no_rewrite",
        "assembled_chapters": [path.relative_to(project).as_posix() for path in chapters],
        "visual_pass_manifest": "reports/visual_pass_manifest.json" if visual_pass.exists() else "",
        "visual_review_note": "reports/visual_review.md" if visual_review.exists() else "",
        "note": "assemble_report.py concatenated cover and chapter fragments. It did not rewrite chapter prose.",
    }
    write_json(out_dir / "workflow_status.json", payload)
    rows = "\n".join(f"<li>{html.escape(chapter.relative_to(project).as_posix())}</li>" for chapter in chapters)
    html_payload = f"""<!doctype html>
<html lang="ko">
<head><meta charset="utf-8"><title>Workflow Status</title></head>
<body>
<main>
  <h1>Workflow Status</h1>
  <p>현재 단계: {html.escape(payload["current_step"])}</p>
  <p>다음 작업: {html.escape(payload["next_action"])}</p>
  <p>활성 보고서: {html.escape(output_rel)}</p>
  <p>조립 모드: concatenate_only_no_rewrite</p>
  <ul>{rows}</ul>
</main>
</body>
</html>
"""
    (out_dir / "workflow_status.html").write_text(html_payload, encoding="utf-8", newline="\n")


def update_active_report(project: Path, output_rel: str, chapters: list[Path], output_path: Path) -> None:
    assembled_at = now_kst()

    assembly_manifest_path = project / "reports" / "report_assembly_manifest.json"
    assembly_manifest = load_manifest(project)
    assembly_manifest["active_report"] = output_rel
    assembly_manifest["output"] = output_rel
    assembly_manifest["assembled_at_kst"] = assembled_at
    assembly_manifest["assembly_mode"] = "concatenate_only_no_rewrite"
    assembly_manifest["assembled_chapters"] = [path.relative_to(project).as_posix() for path in chapters]
    assembly_manifest["chapter_integrity"] = [file_integrity(path, project) for path in chapters]
    assembly_manifest["active_report_integrity"] = file_integrity(output_path, project)
    assembly_manifest["runtime_assets"] = copy_runtime_assets(project)
    visual_pass = project / "reports" / "visual_pass_manifest.json"
    visual_review = project / "reports" / "visual_review.md"
    style_pass_dir = project / "reports" / "style_pass"
    style_pass_artifacts = [
        file_integrity(style_pass_dir / filename, project)
        for filename in STYLE_PASS_REQUIRED
        if (style_pass_dir / filename).exists()
    ]
    assembly_manifest["visual_pass_manifest"] = (
        visual_pass.relative_to(project).as_posix() if visual_pass.exists() else ""
    )
    assembly_manifest["visual_review_note"] = (
        visual_review.relative_to(project).as_posix() if visual_review.exists() else ""
    )
    assembly_manifest["style_pass_artifacts"] = style_pass_artifacts
    write_json(assembly_manifest_path, assembly_manifest)

    stage_manifest_path = project / "project_state" / "report_stage_manifest.json"
    stage_manifest = {}
    if stage_manifest_path.exists():
        try:
            parsed = json.loads(read_text(stage_manifest_path))
            if isinstance(parsed, dict):
                stage_manifest = parsed
        except json.JSONDecodeError:
            stage_manifest = {}
    stage_manifest["active_report"] = output_rel
    stage_manifest["active_report_updated_at_kst"] = assembled_at
    write_json(stage_manifest_path, stage_manifest)
    update_workflow_status(project, output_rel, chapters)


def chapter_paths(project: Path, manifest: dict[str, object]) -> list[Path]:
    chapters_dir = project / "reports" / "chapters"
    if not chapters_dir.exists():
        raise FileNotFoundError("chapter directory not found: reports/chapters")
    ordered = manifest.get("chapters")
    if isinstance(ordered, list) and ordered:
        paths = [chapters_dir / str(item) for item in ordered]
    else:
        paths = sorted(chapters_dir.glob("ch*.html"))
    missing = [path.as_posix() for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("chapter file(s) missing: " + " | ".join(missing))
    if not paths:
        raise FileNotFoundError("no chapter files found under reports/chapters")
    return paths


def chapter_fragment(path: Path) -> str:
    raw = read_text(path)
    if re.search(r"<(?:html|head|body)\b", raw, flags=re.I):
        raise ValueError(f"{path.as_posix()} must be an HTML fragment, not a full document")
    return raw


def build_html(project: Path, cover_data: dict[str, object], chapters: list[Path]) -> str:
    config = load_config()
    preset = active_domain_preset(config)
    css_path = Path(str(get_path(config, "report_design.default_css", "_ai_system/templates/report_html/report.css")))
    theme_css = css_variable_block(config)
    css = read_text(css_path)
    cover_css = read_text(COVER_ROOT / "cover.css")
    cover = render_cover(cover_data)
    title = escape_value(cover_data.get("report_title", project.name))
    preset_name = html.escape(str(preset["name"]), quote=True)
    chapter_blocks = "\n\n".join(chapter_fragment(path) for path in chapters)
    appendix_blocks = build_reference_appendices(project)
    assembly_comment = "\n".join(
        [
            "<!-- report_assembly:",
            "  source: reports/chapters/*.html",
            f"  style: {css_path.as_posix()}",
            "  mode: concatenate_only_no_rewrite",
            "  chapters:",
            *[f"    - {path.relative_to(project).as_posix()}" for path in chapters],
            "-->",
        ]
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
{css}
{theme_css}
{cover_css}
  </style>
</head>
<body>
{assembly_comment}
<main class="report-page assembled-report" data-assembled-report="true" data-domain-preset="{preset_name}">
{cover}

{chapter_blocks}

{appendix_blocks}
</main>
</body>
</html>
"""


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Assemble a report by concatenating cover data and chapter fragments without rewriting prose."
    )
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument(
        "--cover-data",
        default="reports/cover.data.json",
        help="Cover data JSON path relative to the project folder.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT.as_posix(),
        help="Output HTML path relative to the project folder.",
    )
    args = parser.parse_args()

    project = PROJECT_ROOT / args.project
    if not project.exists():
        print(json.dumps({"error": f"project not found: {args.project}"}, ensure_ascii=False, indent=2))
        return 2

    cover_data_path = project / args.cover_data
    if not cover_data_path.exists():
        print(json.dumps({"error": f"cover data not found: {args.cover_data}"}, ensure_ascii=False, indent=2))
        return 2

    try:
        cover_data = json.loads(read_text(cover_data_path))
        manifest = load_manifest(project)
        chapters = chapter_paths(project, manifest)
        output = project / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(build_html(project, cover_data, chapters), encoding="utf-8", newline="\n")
        update_active_report(project, args.output, chapters, output)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    payload = {
        "project": project.name,
        "output": args.output,
        "active_report": args.output,
        "cover_data": args.cover_data,
        "chapters": [path.relative_to(project).as_posix() for path in chapters],
        "mode": "concatenate_only_no_rewrite",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
