from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "system_name": "Report Integrity Orchestrator",
    "workspace_display_name": "Report Factory Workspace",
    "preset_domain": "general_report",
    "domain_presets": {
        "general_report": {
            "label": "General report",
            "description": "Default evidence-backed report workflow.",
            "theme_tokens": {
                "primary": "#1F6FEB",
                "point": "#3485FF",
                "dark": "#172033",
                "ink": "#1F2933",
                "muted": "#616670",
                "line": "#CFD0D3",
                "soft": "#EEF4FB",
                "bg": "#F7F8FA",
                "risk": "#B8567A",
                "ok": "#167A5B",
            },
            "quality_profile": {
                "minimum_visuals": 4,
                "minimum_figures": 1,
                "visual_plan_required": True,
                "docx_expected_by_default": False,
            },
            "quality_emphasis": [
                "source-grounded conclusions",
                "chapter-complete analysis",
                "reader-useful visuals",
                "honest residual risks",
            ],
            "design_profile": "neutral_editorial",
        }
    },
    "legacy_report_factory_projects": [],
    "report_factory": {
        "substantial_markers": [
            "internal review",
            "full",
            "substantial",
            "report",
            "strategy",
            "market",
            "business",
            "legal",
            "policy",
            "regulatory",
            "risk",
            "investment",
            "내부 검토",
            "보고서",
            "전략",
            "시장",
            "사업성",
            "법률",
            "정책",
            "규제",
            "리스크",
            "투자",
        ]
    },
    "report_design": {
        "default_css": "_ai_system/templates/report_html/report.css",
        "theme_token_names": ["primary", "point", "dark", "ink", "muted", "line", "soft", "bg", "risk", "ok"],
        "template_markers": ["report-template", "_ai_system/templates", "report.css"],
        "cover_component_markers": ['data-cover-component="report-cover-v1"', 'class="cover-page"', 'class="report-cover"'],
    },
    "content_quality": {
        "minimum_visuals": 4,
        "minimum_figures": 1,
        "visual_plan_required": True,
    },
    "delivery": {
        "local_outbox_enabled": True,
        "default_outbox_dir": "reports/outbox",
        "cloud_bridge_default": "disabled",
        "cloud_upload_requires_explicit_user_approval": True,
        "include_originals_by_default": False,
        "public_safe_only_by_default": True,
    },
}


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(root: Path | None = None) -> dict[str, Any]:
    base = DEFAULT_CONFIG
    root = root or workspace_root()
    path = root / "_ai_system" / "workspace_config.json"
    if not path.exists():
        return base
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return base
    if not isinstance(data, dict):
        return base
    config = _deep_merge(base, data)
    local_path = root / "_ai_system" / "workspace_config.local.json"
    if local_path.exists():
        try:
            local_data = json.loads(local_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            local_data = {}
        if isinstance(local_data, dict):
            config = _deep_merge(config, local_data)
    return config


def get_path(config: dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    current: Any = config
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def list_value(config: dict[str, Any], dotted_path: str) -> list[str]:
    value = get_path(config, dotted_path, [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def active_domain_preset(config: dict[str, Any]) -> dict[str, Any]:
    requested_name = str(config.get("preset_domain") or "general_report")
    presets = config.get("domain_presets", {})
    if not isinstance(presets, dict):
        presets = {}
    preset_name = requested_name
    preset = presets.get(preset_name)
    if not isinstance(preset, dict):
        preset_name = "general_report"
        preset = presets.get("general_report", {})
    return {
        "name": preset_name,
        "requested_name": requested_name,
        "settings": preset if isinstance(preset, dict) else {},
    }


def int_value(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def bool_value(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return default


def active_quality_profile(config: dict[str, Any]) -> dict[str, Any]:
    preset = active_domain_preset(config)["settings"]
    base = {
        "minimum_visuals": int_value(get_path(config, "content_quality.minimum_visuals", 4), 4),
        "minimum_figures": int_value(get_path(config, "content_quality.minimum_figures", 1), 1),
        "visual_plan_required": bool_value(get_path(config, "content_quality.visual_plan_required", True), True),
        "docx_expected_by_default": bool_value(get_path(config, "content_quality.docx_expected_by_default", False), False),
    }
    override = preset.get("quality_profile", {}) if isinstance(preset, dict) else {}
    if isinstance(override, dict):
        base = _deep_merge(base, override)
    base["minimum_visuals"] = int_value(base.get("minimum_visuals"), 4)
    base["minimum_figures"] = int_value(base.get("minimum_figures"), 1)
    base["visual_plan_required"] = bool_value(base.get("visual_plan_required"), True)
    base["docx_expected_by_default"] = bool_value(base.get("docx_expected_by_default"), False)
    return base


def active_theme_tokens(config: dict[str, Any]) -> dict[str, str]:
    preset = active_domain_preset(config)["settings"]
    names = list_value(config, "report_design.theme_token_names")
    default_tokens = get_path(DEFAULT_CONFIG, "domain_presets.general_report.theme_tokens", {})
    tokens = dict(default_tokens if isinstance(default_tokens, dict) else {})
    override = preset.get("theme_tokens", {}) if isinstance(preset, dict) else {}
    if isinstance(override, dict):
        tokens.update({str(key): str(value) for key, value in override.items()})
    if names:
        tokens = {name: str(tokens.get(name, "")) for name in names if str(tokens.get(name, "")).strip()}
    return tokens


def css_variable_block(config: dict[str, Any]) -> str:
    preset = active_domain_preset(config)
    tokens = active_theme_tokens(config)
    lines = [
        "/* report-factory resolved domain preset */",
        f"/* preset_domain: {preset['name']} */",
        ":root {",
    ]
    for key, value in tokens.items():
        lines.append(f"  --rf-{key}: {value};")
    lines.append("}")
    return "\n".join(lines)


def resolved_domain_profile(config: dict[str, Any]) -> dict[str, Any]:
    preset = active_domain_preset(config)
    return {
        "preset_domain": preset["name"],
        "requested_preset_domain": preset["requested_name"],
        "label": preset["settings"].get("label", preset["name"]),
        "description": preset["settings"].get("description", ""),
        "design_profile": preset["settings"].get("design_profile", ""),
        "quality_emphasis": preset["settings"].get("quality_emphasis", []),
        "theme_tokens": active_theme_tokens(config),
        "quality_profile": active_quality_profile(config),
        "delivery": get_path(config, "delivery", {}),
    }


def validate_config_schema(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    preset = active_domain_preset(config)
    presets = config.get("domain_presets", {})
    if preset["requested_name"] != preset["name"]:
        errors.append(f"preset_domain '{preset['requested_name']}' is not defined in domain_presets")
    if not isinstance(presets, dict) or "general_report" not in presets:
        errors.append("domain_presets.general_report is required")
    tokens = active_theme_tokens(config)
    for key, value in tokens.items():
        if not str(value).strip():
            errors.append(f"theme token '{key}' is empty")
        elif not str(value).strip().startswith("#"):
            errors.append(f"theme token '{key}' should be a CSS hex color")
    quality = active_quality_profile(config)
    if quality["minimum_visuals"] < quality["minimum_figures"]:
        errors.append("minimum_visuals cannot be lower than minimum_figures")
    return errors
