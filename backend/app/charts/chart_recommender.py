from __future__ import annotations


def chart_alternatives(chart_type: str) -> list[str]:
    mapping = {
        "bar": ["horizontal_bar", "donut", "pie"],
        "horizontal_bar": ["bar", "donut"],
        "grouped_bar": ["stacked_bar", "bar", "mosaic_future"],
        "stacked_bar": ["grouped_bar", "bar"],
        "pie": ["donut", "bar"],
        "donut": ["pie", "bar"],
        "histogram": ["boxplot", "bar"],
        "boxplot": ["histogram", "grouped_bar"],
        "scatter": ["heatmap"],
        "heatmap": ["scatter"],
        "line": ["bar"],
        "mosaic_future": ["grouped_bar", "stacked_bar"],
    }
    return mapping.get(chart_type, [])


def recommend_frequency_chart(labels: list[str]) -> str:
    if any(len(label or "") > 20 for label in labels):
        return "horizontal_bar"
    if 2 <= len(labels) <= 5:
        return "donut"
    return "bar"


def recommend_chart_types(analysis_goal: str, *, labels: list[str] | None = None) -> list[str]:
    labels = labels or []
    mapping = {
        "frequencies": [recommend_frequency_chart(labels), "bar", "donut", "pie"],
        "descriptives": ["histogram", "boxplot"],
        "normality": ["histogram", "boxplot"],
        "correlation": ["scatter", "heatmap"],
        "correlation_matrix": ["heatmap"],
        "group_comparison": ["boxplot", "grouped_bar", "stacked_bar"],
        "categorical_association": ["grouped_bar", "stacked_bar", "mosaic_future"],
        "orchestrated_summary": ["bar", "histogram", "heatmap"],
    }
    selected = mapping.get(analysis_goal, ["bar"])
    return list(dict.fromkeys(selected))
