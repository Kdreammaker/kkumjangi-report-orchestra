from __future__ import annotations

from typing import Mapping


FONT_STACK = '"Pretendard", "Malgun Gothic", "Noto Sans KR", Arial, sans-serif'

REPORT_COLORS = {
    "primary": "#1F6FEB",
    "point": "#3485FF",
    "dark": "#172033",
    "ink": "#1f2933",
    "muted": "#616670",
    "line": "#CFD0D3",
    "soft": "#EEF4FB",
    "bg": "#F7F8FA",
    "risk": "#B8567A",
    "ok": "#167A5B",
}

DEFAULT_COVER_PALETTE = {
    "cover_blue": "#006BD6",
    "cover_dark": "#062554",
    "cover_soft": "#EEF4FB",
    "cover_line": "#CFD0D3",
    "cover_alert": "#DC2626",
    "cover_ink": "#1F2933",
    "cover_muted": "#616670",
}


def css(declarations: Mapping[str, str]) -> str:
    return "; ".join(f"{key}: {value}" for key, value in declarations.items() if value) + ";"


def style_attr(style: str) -> str:
    return f' style="{style}"' if style else ""


def cover_palette(preset: Mapping[str, object] | None = None) -> dict[str, str]:
    palette = dict(DEFAULT_COVER_PALETTE)
    preset_palette = preset.get("palette", {}) if isinstance(preset, Mapping) else {}
    if isinstance(preset_palette, Mapping):
        aliases = {
            "cover_blue": "cover_blue",
            "cover_dark": "cover_dark",
            "cover_soft": "cover_soft",
            "cover_line": "cover_line",
            "cover_alert": "cover_alert",
            "cover_ink": "cover_ink",
            "cover_muted": "cover_muted",
        }
        for source, target in aliases.items():
            value = str(preset_palette.get(source, "")).strip()
            if value:
                palette[target] = value
    return palette


def cover_styles(preset: Mapping[str, object] | None = None) -> dict[str, str]:
    colors = cover_palette(preset)
    dark = colors["cover_dark"]
    blue = colors["cover_blue"]
    line = colors["cover_line"]
    soft = colors["cover_soft"]
    alert = colors["cover_alert"]
    ink = colors["cover_ink"]
    muted = colors["cover_muted"]
    return {
        "cover_page": css(
            {
                "box-sizing": "border-box",
                "display": "block",
                "background": "#FFFFFF",
                "color": ink,
                "font-family": FONT_STACK,
                "border-top": f"6px solid {dark}",
                "padding": "30px 34px 32px",
                "page-break-after": "always",
            }
        ),
        "cover_topline": css(
            {
                "display": "table",
                "width": "100%",
                "border-bottom": f"2px solid {dark}",
                "padding-bottom": "14px",
                "margin-bottom": "0",
            }
        ),
        "cover_classification_group": css(
            {
                "display": "table-cell",
                "vertical-align": "middle",
                "text-align": "left",
            }
        ),
        "classification": css(
            {
                "display": "inline-block",
                "background": dark,
                "border": f"1px solid {dark}",
                "color": "#FFFFFF",
                "font-size": "13px",
                "font-weight": "700",
                "letter-spacing": "0",
                "padding": "7px 10px",
                "margin-right": "8px",
            }
        ),
        "report_type": css(
            {
                "display": "table-cell",
                "vertical-align": "middle",
                "text-align": "right",
                "color": dark,
                "font-size": "13px",
                "font-weight": "700",
                "letter-spacing": "0",
                "padding": "7px 10px",
            }
        ),
        "cover_security_tag": css(
            {
                "display": "inline-block",
                "background": "#FFF5F5",
                "border": f"2px solid {alert}",
                "color": "#B91C1C",
                "font-size": "12.5px",
                "font-weight": "900",
                "letter-spacing": "0",
                "padding": "7px 10px",
                "margin-right": "8px",
            }
        ),
        "cover_status_tag": css(
            {
                "display": "inline-block",
                "background": "#F8FAFC",
                "border": f"1px solid {line}",
                "color": muted,
                "font-size": "12.5px",
                "font-weight": "800",
                "letter-spacing": "0",
                "padding": "7px 10px",
                "margin-right": "8px",
            }
        ),
        "cover_logo": css(
            {
                "display": "block",
                "text-align": "right",
                "margin-top": "22px",
            }
        ),
        "cover_logo_img": css(
            {
                "display": "inline-block",
                "max-height": "58px",
                "max-width": "220px",
                "height": "auto",
                "object-fit": "contain",
            }
        ),
        "cover_hero": css(
            {
                "display": "block",
                "margin": "42px 0 26px",
                "max-width": "920px",
            }
        ),
        "kicker": css(
            {
                "color": blue,
                "font-size": "14px",
                "font-weight": "700",
                "letter-spacing": "0.02em",
                "margin": "0 0 16px",
                "text-transform": "uppercase",
            }
        ),
        "cover_title": css(
            {
                "color": dark,
                "font-size": "30px",
                "font-weight": "800",
                "line-height": "1.28",
                "letter-spacing": "0",
                "margin": "0 0 18px",
                "max-width": "860px",
                "overflow-wrap": "break-word",
            }
        ),
        "subtitle": css(
            {
                "border-left": f"4px solid {blue}",
                "color": "#3F4855",
                "font-size": "16px",
                "line-height": "1.62",
                "margin": "0",
                "max-width": "780px",
                "padding-left": "16px",
            }
        ),
        "meta_table": css(
            {
                "background": "#FFFFFF",
                "border-collapse": "collapse",
                "border": f"1px solid {line}",
                "border-top": f"3px solid {dark}",
                "margin": "0 0 22px",
                "width": "100%",
            }
        ),
        "meta_th": css(
            {
                "background": soft,
                "border-bottom": f"1px solid {line}",
                "color": dark,
                "font-size": "13.5px",
                "font-weight": "800",
                "padding": "12px 13px",
                "text-align": "left",
                "vertical-align": "top",
                "width": "120px",
            }
        ),
        "meta_td": css(
            {
                "border-bottom": f"1px solid {line}",
                "color": ink,
                "font-size": "13.5px",
                "padding": "12px 13px",
                "text-align": "left",
                "vertical-align": "top",
            }
        ),
        "approval_table": css(
            {
                "border-collapse": "separate",
                "border-spacing": "10px 0",
                "margin": "20px 0 24px",
                "width": "100%",
            }
        ),
        "approval_card": css(
            {
                "background": "#FFFFFF",
                "border": f"1px solid {line}",
                "border-top": f"3px solid {blue}",
                "min-height": "74px",
                "padding": "12px",
                "vertical-align": "top",
            }
        ),
        "approval_label": css(
            {
                "color": muted,
                "display": "block",
                "font-size": "12px",
                "margin-bottom": "10px",
            }
        ),
        "approval_name": css(
            {
                "color": dark,
                "font-size": "15px",
                "font-weight": "700",
            }
        ),
        "cover_purpose": css(
            {
                "background": soft,
                "border-left": f"4px solid {blue}",
                "color": "#3F4855",
                "font-size": "14px",
                "line-height": "1.62",
                "margin": "26px 0 0",
                "padding": "12px 14px",
            }
        ),
        "confidential_notice": css(
            {
                "background": "#FFF7ED",
                "border": "1px solid #FED7AA",
                "border-left": f"4px solid {alert}",
                "color": "#7F1D1D",
                "font-size": "12px",
                "line-height": "1.65",
                "margin": "18px 0 0",
                "padding": "10px 12px",
            }
        ),
    }


REPORT_INLINE_STYLES = {
    "report_page": css(
        {
            "box-sizing": "border-box",
            "max-width": "210mm",
            "margin": "0 auto",
            "padding": "24mm 18mm 28mm",
            "background": "#FFFFFF",
            "color": REPORT_COLORS["ink"],
            "font-family": FONT_STACK,
            "font-size": "16px",
            "line-height": "1.82",
            "word-break": "keep-all",
            "overflow-wrap": "normal",
        }
    ),
    "report_cover": css(
        {
            "border-bottom": f"3px solid {REPORT_COLORS['dark']}",
            "margin-bottom": "28px",
            "padding-bottom": "24px",
        }
    ),
    "report_label": css(
        {
            "color": REPORT_COLORS["primary"],
            "font-size": "14px",
            "font-weight": "700",
            "margin": "0 0 8px",
        }
    ),
    "h1": css(
        {
            "color": REPORT_COLORS["dark"],
            "font-size": "30px",
            "font-weight": "800",
            "line-height": "1.35",
            "letter-spacing": "0",
            "margin": "54px 0 18px",
            "overflow-wrap": "break-word",
            "page-break-after": "avoid",
        }
    ),
    "h2": css(
        {
            "border-bottom": f"1px solid {REPORT_COLORS['line']}",
            "color": REPORT_COLORS["dark"],
            "font-size": "22px",
            "font-weight": "800",
            "line-height": "1.35",
            "margin": "38px 0 16px",
            "padding-bottom": "8px",
            "overflow-wrap": "break-word",
            "page-break-after": "avoid",
        }
    ),
    "h3": css(
        {
            "color": REPORT_COLORS["dark"],
            "font-size": "18px",
            "font-weight": "700",
            "line-height": "1.35",
            "margin": "22px 0 8px",
            "overflow-wrap": "break-word",
            "page-break-after": "avoid",
        }
    ),
    "paragraph": css({"margin": "12px 0", "max-width": "174mm"}),
    "lead": css(
        {
            "color": "#344054",
            "font-size": "16px",
            "font-weight": "500",
            "line-height": "1.7",
            "margin": "12px 0",
            "max-width": "174mm",
        }
    ),
    "callout": css(
        {
            "background": "#FFFFFF",
            "border-left": f"4px solid {REPORT_COLORS['primary']}",
            "margin": "18px 0",
            "padding": "13px 15px",
            "break-inside": "avoid",
            "page-break-inside": "avoid",
        }
    ),
    "table": css(
        {
            "background": "#FFFFFF",
            "border-collapse": "collapse",
            "border-top": f"2px solid {REPORT_COLORS['dark']}",
            "margin": "12px 0 6px",
            "max-width": "174mm",
            "width": "100%",
            "break-inside": "avoid",
            "page-break-inside": "avoid",
        }
    ),
    "caption": css(
        {
            "color": REPORT_COLORS["muted"],
            "font-size": "12.5px",
            "line-height": "1.55",
            "margin": "10px 0 0",
            "max-width": "174mm",
        }
    ),
    "table_caption": css(
        {
            "color": REPORT_COLORS["dark"],
            "font-size": "15px",
            "font-weight": "700",
            "margin-bottom": "8px",
            "text-align": "left",
        }
    ),
    "th": css(
        {
            "background": "#EDF3FA",
            "border-bottom": f"1px solid {REPORT_COLORS['line']}",
            "color": REPORT_COLORS["dark"],
            "font-size": "13.5px",
            "font-weight": "700",
            "line-height": "1.55",
            "overflow-wrap": "break-word",
            "padding": "10px 12px",
            "text-align": "left",
            "vertical-align": "top",
            "word-break": "normal",
        }
    ),
    "td": css(
        {
            "border-bottom": f"1px solid {REPORT_COLORS['line']}",
            "color": REPORT_COLORS["ink"],
            "font-size": "13.5px",
            "line-height": "1.55",
            "overflow-wrap": "break-word",
            "padding": "10px 12px",
            "text-align": "left",
            "vertical-align": "top",
            "word-break": "normal",
        }
    ),
    "figure": css(
        {
            "background": "#FFFFFF",
            "border": "1px solid #D8E0EB",
            "border-radius": "8px",
            "margin": "26px 0",
            "max-width": "174mm",
            "padding": "18px 18px 14px",
            "break-inside": "avoid",
            "page-break-inside": "avoid",
        }
    ),
    "figure_caption": css(
        {
            "color": "#344054",
            "font-size": "14px",
            "font-weight": "700",
            "line-height": "1.58",
            "margin": "0 0 10px",
        }
    ),
    "figure_img": css(
        {
            "display": "block",
            "height": "auto",
            "max-width": "100%",
            "width": "100%",
        }
    ),
    "source_note": css(
        {
            "border-top": "1px solid #E3E8EF",
            "color": "#344054",
            "display": "block",
            "font-size": "13px",
            "font-weight": "600",
            "line-height": "1.58",
            "margin-top": "10px",
            "padding-top": "8px",
        }
    ),
    "appendix_note": css(
        {
            "color": "#344054",
            "font-size": "14px",
            "line-height": "1.65",
            "margin": "12px 0",
            "max-width": "174mm",
        }
    ),
}
