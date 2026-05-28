from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
COVER_ROOT = Path("_ai_system") / "templates" / "report_html" / "cover"
REQUIRED_FIELDS = [
    "classification",
    "report_type",
    "report_title",
    "project_name",
    "report_no",
    "date",
    "version",
    "prepared_by",
    "prepared_for",
    "distribution",
    "approval_author",
    "approval_reviewer",
    "approval_approver",
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
    fields = [
        data.get("confidentiality_status", ""),
        data.get("classification", ""),
        data.get("security_level", ""),
        data.get("security_tag", ""),
    ]
    return bool(data.get("is_confidential")) or any("대외비" in str(value) or truthy(value) for value in fields)


def optional_cover_tokens(data: dict[str, object]) -> dict[str, str]:
    logo_path = str(data.get("logo_path", "")).strip()
    logo_alt = str(data.get("logo_alt", "회사 로고")).strip() or "회사 로고"
    logo_html = (
        f'<div class="cover-logo"><img src="{html.escape(logo_path, quote=True)}" '
        f'alt="{html.escape(logo_alt, quote=True)}"></div>'
        if logo_path
        else ""
    )
    is_confidential = confidential_from_cover_data(data)
    security_tag = str(data.get("security_tag", "")).strip()
    if is_confidential and not security_tag:
        security_tag = "대외비 / Confidential"
    security_tag_html = (
        f'<span class="cover-security-tag">{html.escape(security_tag, quote=False)}</span>'
        if security_tag
        else ""
    )
    notice = str(data.get("confidential_notice", "")).strip()
    if is_confidential and not notice:
        notice = DEFAULT_CONFIDENTIAL_NOTICE
    confidential_notice_html = (
        f'<p class="cover-confidential-notice">{html.escape(notice, quote=False)}</p>' if notice else ""
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
            cells.append(f"<th>{html.escape(label)}</th><td>{html.escape(value, quote=False)}</td>")
        if cells:
            if len(cells) == 1:
                cells[0] = cells[0].replace("<td>", '<td colspan="3">', 1)
            html_rows.append("<tr>" + "".join(cells) + "</tr>")
    if not html_rows:
        return ""
    return '<table class="cover-meta-table" aria-label="문서 관리 정보"><tbody>' + "".join(html_rows) + "</tbody></table>"


def render_approval(data: dict[str, object], preset: dict[str, object]) -> str:
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
            cards.append(f"<div><span>{html.escape(label)}</span><strong>{html.escape(value, quote=False)}</strong></div>")
    if not cards:
        return ""
    return f'<div class="cover-approval cover-approval-{len(cards)}">' + "".join(cards) + "</div>"


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S KST")


def render_cover(data: dict[str, object]) -> tuple[str, list[str]]:
    template = read_text(COVER_ROOT / "cover.html")
    preset = load_cover_preset(data)
    defaults = preset.get("defaults", {}) if isinstance(preset.get("defaults"), dict) else {}
    tokens: dict[str, object] = {
        **defaults,
        **data,
        **optional_cover_tokens(data),
        "meta_table_html": render_meta_table(data, preset),
        "approval_html": render_approval(data, preset),
    }
    for key, value in tokens.items():
        if key.endswith("_html"):
            template = template.replace("{{" + key + "}}", str(value))
        else:
            template = template.replace("{{" + key + "}}", escape_value(value))
    missing_tokens = sorted(set(re.findall(r"{{([a-zA-Z0-9_]+)}}", template)))
    template = re.sub(r"<p class=\"kicker\">\s*</p>\s*", "", template)
    template = re.sub(r"<p class=\"subtitle\">\s*</p>\s*", "", template)
    template = re.sub(r"<p class=\"cover-purpose\">\s*</p>\s*", "", template)
    return template, missing_tokens


def validate(project_name: str, cover_data: str, write_preview: bool) -> dict[str, object]:
    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"error": f"project not found: {project_name}"}
    data_path = project / cover_data
    if not data_path.exists():
        return {"error": f"cover data not found: {cover_data}"}
    try:
        data = json.loads(read_text(data_path))
    except json.JSONDecodeError as exc:
        return {"error": f"cover data is not valid JSON: {exc}"}
    if not isinstance(data, dict):
        return {"error": "cover data must be a JSON object"}
    preset = load_cover_preset(data)
    required_fields = preset.get("required_fields", REQUIRED_FIELDS)
    if not isinstance(required_fields, list) or not required_fields:
        required_fields = REQUIRED_FIELDS
    missing_fields = [
        str(field)
        for field in required_fields
        if not cover_field(data, preset, str(field))
    ]
    rendered, missing_tokens = render_cover(data)
    is_confidential = confidential_from_cover_data(data)
    classification_value = str(data.get("classification", "")).strip()
    approval_slots = preset.get("approval_slots")
    approval_optional = isinstance(approval_slots, list) and len(approval_slots) == 0
    visible_checks = {
        "has_report_no": bool(re.search(r"(?:보고서|문서|제안서)\s*번호|report no|REPORT-", rendered, flags=re.I)),
        "has_date": bool(re.search(r"\d{4}[-.년]\s*\d{1,2}|작성일|발행일", rendered)),
        "has_classification": bool(re.search(r"내부|상부|파트너|외부|공개|검토용|보고용|confidential", rendered, flags=re.I)),
        "has_approval": approval_optional or bool(re.search(r"class=\"cover-approval", rendered)),
    }
    errors: list[str] = []
    if missing_fields:
        errors.append("missing cover data fields: " + ", ".join(missing_fields))
    if missing_tokens:
        errors.append("unfilled cover template tokens: " + ", ".join(missing_tokens))
    if re.search(r"대외비|confidential|기밀", classification_value, flags=re.I):
        errors.append(
            "cover classification should contain only document class; put confidentiality in confidentiality_status/security_tag"
        )
    for key, passed in visible_checks.items():
        if not passed:
            errors.append(f"cover visible check failed: {key}")
    if is_confidential:
        if "cover-security-tag" not in rendered:
            errors.append("confidential cover requires visible cover-security-tag")
        if "cover-confidential-notice" not in rendered:
            errors.append("confidential cover requires visible confidential notice")
    preview_path = ""
    if write_preview:
        css = read_text(COVER_ROOT / "cover.css")
        out_dir = project / "reports" / "cover_preview"
        out_dir.mkdir(parents=True, exist_ok=True)
        preview = out_dir / "cover_preview.html"
        preview.write_text(
            "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
            "<title>Cover Preview</title><style>"
            + css
            + "</style></head><body>"
            + rendered
            + "</body></html>\n",
            encoding="utf-8",
            newline="\n",
        )
        preview_path = preview.relative_to(project).as_posix()
    return {
        "project": project_name,
        "generated_at_kst": now_kst(),
        "cover_data": cover_data,
        "passed": not errors,
        "errors": errors,
        "visible_checks": visible_checks,
        "preview": preview_path,
        "notes": [
            "This validates the reusable cover component and required visible fields.",
            "It does not validate the report body or source truth.",
        ],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate and optionally render the reusable report cover component.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--cover-data", default="reports/cover.data.json", help="Project-relative cover data JSON path.")
    parser.add_argument("--write-preview", action="store_true", help="Write reports/cover_preview/cover_preview.html")
    args = parser.parse_args()
    payload = validate(args.project, args.cover_data, args.write_preview)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if "error" in payload:
        return 2
    return 0 if payload.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
