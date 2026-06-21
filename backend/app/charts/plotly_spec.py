from __future__ import annotations

from typing import Any


def make_plotly_layout(
    *,
    title: str,
    subtitle: str | None,
    theme: dict,
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
    barmode: str | None = None,
    showlegend: bool = True,
) -> dict[str, Any]:
    layout: dict[str, Any] = {
        "title": {
            "text": title if subtitle is None else f"{title}<br><sup>{subtitle}</sup>",
            "font": {"size": theme["title_size"], "color": theme["text_color"]},
        },
        "paper_bgcolor": theme["background"],
        "plot_bgcolor": theme["background"],
        "font": {"family": theme["font_family"], "color": theme["text_color"]},
        "xaxis": {
            "title": {"text": xaxis_title},
            "gridcolor": theme["grid_color"],
            "tickfont": {"size": theme["axis_size"]},
        },
        "yaxis": {
            "title": {"text": yaxis_title},
            "gridcolor": theme["grid_color"],
            "tickfont": {"size": theme["axis_size"]},
        },
        "legend": {"orientation": "v", "x": 1.02, "y": 1.0},
        "margin": theme["margin"],
        "showlegend": showlegend,
    }
    if barmode:
        layout["barmode"] = barmode
    return layout


def make_plotly_config() -> dict[str, Any]:
    return {
        "responsive": True,
        "displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    }


def make_plotly_bar(
    *,
    x: list[Any],
    y: list[Any],
    text: list[str] | None = None,
    name: str | None = None,
    orientation: str = "v",
    color: str | None = None,
) -> list[dict[str, Any]]:
    trace = {
        "type": "bar",
        "x": x if orientation == "v" else y,
        "y": y if orientation == "v" else x,
        "text": text,
        "textposition": "auto",
        "orientation": orientation,
    }
    if name:
        trace["name"] = name
    if color:
        trace["marker"] = {"color": color}
    return [trace]


def make_plotly_grouped_bar(
    *,
    categories: list[Any],
    series: list[dict[str, Any]],
    stacked: bool = False,
) -> tuple[list[dict[str, Any]], str]:
    traces: list[dict[str, Any]] = []
    for item in series:
        traces.append(
            {
                "type": "bar",
                "name": item["name"],
                "x": categories,
                "y": item["values"],
                "text": item.get("text"),
                "textposition": "auto",
            }
        )
    return traces, "stack" if stacked else "group"


def make_plotly_pie(
    *,
    labels: list[Any],
    values: list[Any],
    hole: float = 0.0,
) -> list[dict[str, Any]]:
    return [
        {
            "type": "pie",
            "labels": labels,
            "values": values,
            "hole": hole,
            "textinfo": "label+percent",
        }
    ]


def make_plotly_histogram(*, values: list[Any], name: str | None = None) -> list[dict[str, Any]]:
    trace = {"type": "histogram", "x": values}
    if name:
        trace["name"] = name
    return [trace]


def make_plotly_boxplot(
    *,
    y: list[Any] | None = None,
    x: list[Any] | None = None,
    name: str | None = None,
) -> list[dict[str, Any]]:
    trace = {"type": "box"}
    if y is not None:
        trace["y"] = y
    if x is not None:
        trace["x"] = x
    if name:
        trace["name"] = name
    return [trace]


def make_plotly_scatter(
    *,
    x: list[Any],
    y: list[Any],
    name: str | None = None,
) -> list[dict[str, Any]]:
    trace = {"type": "scatter", "mode": "markers", "x": x, "y": y}
    if name:
        trace["name"] = name
    return [trace]


def make_plotly_heatmap(
    *,
    z: list[list[Any]],
    x: list[Any],
    y: list[Any],
) -> list[dict[str, Any]]:
    return [
        {
            "type": "heatmap",
            "z": z,
            "x": x,
            "y": y,
            "colorscale": "YlOrBr",
            "hoverongaps": False,
        }
    ]
