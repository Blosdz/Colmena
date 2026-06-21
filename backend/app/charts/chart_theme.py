from __future__ import annotations

from copy import deepcopy


CHART_THEMES = {
    "academic_light": {
        "palette": ["#2F3B45", "#687785", "#9BA7B1", "#C7D0D8", "#E3E8EC"],
        "background": "#FFFFFF",
        "text_color": "#2A2A2A",
        "grid_color": "#E6EAEE",
        "font_family": "Arial, Helvetica, sans-serif",
        "title_size": 18,
        "axis_size": 12,
        "legend_position": "right",
        "margin": {"l": 60, "r": 30, "t": 70, "b": 60},
        "template_name": "academic_light",
    },
    "colmena_premium": {
        "palette": ["#D08B00", "#E7B24A", "#A55C00", "#5C4528", "#F5D48B"],
        "background": "#FBF8F1",
        "text_color": "#342C22",
        "grid_color": "#E8E0D1",
        "font_family": "Arial, Helvetica, sans-serif",
        "title_size": 20,
        "axis_size": 12,
        "legend_position": "right",
        "margin": {"l": 60, "r": 30, "t": 72, "b": 60},
        "template_name": "colmena_premium",
    },
    "presentation_clean": {
        "palette": ["#1D4E89", "#4C78A8", "#72B7B2", "#F2CF5B", "#E45756"],
        "background": "#FFFFFF",
        "text_color": "#102030",
        "grid_color": "#D9E2EC",
        "font_family": "Arial, Helvetica, sans-serif",
        "title_size": 22,
        "axis_size": 13,
        "legend_position": "right",
        "margin": {"l": 60, "r": 30, "t": 74, "b": 60},
        "template_name": "presentation_clean",
    },
    "monochrome_apa": {
        "palette": ["#222222", "#555555", "#888888", "#BBBBBB", "#DDDDDD"],
        "background": "#FFFFFF",
        "text_color": "#1F1F1F",
        "grid_color": "#DADADA",
        "font_family": "Arial, Helvetica, sans-serif",
        "title_size": 18,
        "axis_size": 12,
        "legend_position": "right",
        "margin": {"l": 60, "r": 30, "t": 70, "b": 60},
        "template_name": "monochrome_apa",
    },
}


def get_chart_theme(theme_name: str | None) -> dict:
    key = (theme_name or "colmena_premium").strip().lower()
    if key not in CHART_THEMES:
        key = "colmena_premium"
    return deepcopy(CHART_THEMES[key])
