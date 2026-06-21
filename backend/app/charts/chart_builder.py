from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.charts.chart_recommender import chart_alternatives
from app.charts.plotly_spec import (
    make_plotly_bar,
    make_plotly_boxplot,
    make_plotly_config,
    make_plotly_grouped_bar,
    make_plotly_heatmap,
    make_plotly_histogram,
    make_plotly_layout,
    make_plotly_pie,
    make_plotly_scatter,
)
from app.schemas.chart import ChartEditableOptionsRead, ChartSpecRead, ChartTargetInput


def build_editable_options(chart_type: str, *, groupable: bool = False) -> ChartEditableOptionsRead:
    alternatives = [chart_type, *chart_alternatives(chart_type)]
    return ChartEditableOptionsRead(
        can_change_chart_type=True,
        available_chart_types=list(dict.fromkeys(alternatives)),
        can_edit_title=True,
        can_edit_subtitle=True,
        can_edit_axis_labels=True,
        can_show_percentages=True,
        can_show_frequencies=True,
        can_show_values=True,
        can_show_legend=True,
        can_change_palette=True,
        can_change_orientation=chart_type in {"bar", "horizontal_bar"},
        can_group_by=groupable,
        can_export_future=True,
        notes=["La interfaz futura podra ajustar titulo, ejes, paleta y visibilidad de etiquetas."],
    )


def build_academic_note(chart_type: str) -> str:
    mapping = {
        "bar": "Grafico sugerido para resumir frecuencias observadas por categoria.",
        "horizontal_bar": "Grafico sugerido cuando las etiquetas categoricas son extensas.",
        "grouped_bar": "Grafico sugerido para comparar categorias entre grupos.",
        "stacked_bar": "Grafico sugerido para visualizar composicion relativa entre grupos.",
        "pie": "Grafico opcional para distribuciones simples; su interpretacion debe realizarse con cautela.",
        "donut": "Grafico de presentacion para distribuciones simples con pocas categorias.",
        "histogram": "Grafico sugerido para observar la distribucion de una variable numerica.",
        "boxplot": "Grafico sugerido para resumir mediana, dispersion y valores extremos potenciales.",
        "scatter": "Grafico sugerido para explorar asociacion entre dos variables numericas; no implica causalidad.",
        "heatmap": "Grafico sugerido para matrices de correlacion y patrones de intensidad.",
        "line": "Grafico reservado para series temporales o evolucion futura.",
        "mosaic_future": "Grafico reservado como recomendacion futura para asociacion categorica.",
    }
    return mapping.get(chart_type, "Grafico sugerido para visualizacion exploratoria del resultado.")


def build_plain_language_chart_explanation(chart_type: str) -> str:
    mapping = {
        "bar": "Este grafico muestra como se distribuyen las respuestas entre las categorias seleccionadas.",
        "horizontal_bar": "Este grafico muestra la distribucion de respuestas y ayuda cuando las categorias tienen nombres largos.",
        "grouped_bar": "Este grafico permite comparar categorias o grupos lado a lado de forma clara.",
        "stacked_bar": "Este grafico permite ver como se compone cada grupo a partir de sus categorias internas.",
        "pie": "Este grafico resume una distribucion simple por partes del total.",
        "donut": "Este grafico resume una distribucion simple y facilita la lectura del peso relativo de cada categoria.",
        "histogram": "Este grafico muestra como se concentran o dispersan los valores de una variable numerica.",
        "boxplot": "Este grafico resume la distribucion de los puntajes y permite observar medianas, dispersion y posibles valores extremos.",
        "scatter": "Este grafico permite observar si dos variables tienden a aumentar o disminuir juntas. La nube de puntos no demuestra causalidad.",
        "heatmap": "Este grafico ayuda a detectar rapidamente que relaciones son mas fuertes o mas debiles dentro de una matriz.",
        "line": "Este grafico se reserva para mostrar cambios a lo largo del tiempo en una fase futura.",
        "mosaic_future": "Este grafico se recomienda para una fase futura de asociacion categorica avanzada.",
    }
    return mapping.get(chart_type, "Este grafico resume visualmente el resultado seleccionado.")


def _base_chart_spec(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    chart_type: str,
    title: str,
    subtitle: str | None,
    description: str,
    source_type: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    data: dict[str, Any] | list[Any],
    encoding: dict[str, Any],
    plotly_data: list[dict[str, Any]],
    plotly_layout: dict[str, Any],
    plotly_config: dict[str, Any],
    theme: dict[str, Any],
    warnings: list[str],
    groupable: bool = False,
) -> ChartSpecRead:
    return ChartSpecRead(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type=chart_type,
        title=title,
        subtitle=subtitle,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        targets=targets,
        data=data,
        encoding=encoding,
        plotly_data=plotly_data,
        plotly_layout=plotly_layout,
        plotly_config=plotly_config,
        theme=theme,
        editable_options=build_editable_options(chart_type, groupable=groupable),
        recommended_alternatives=chart_alternatives(chart_type),
        academic_note=build_academic_note(chart_type),
        plain_language_explanation=build_plain_language_chart_explanation(chart_type),
        warnings=list(dict.fromkeys(warnings)),
        ready_for_frontend=not warnings or "no_responses" not in warnings,
        ready_for_export=True,
        created_at=datetime.now(timezone.utc),
    )


def build_bar_chart(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    title: str,
    source_type: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    labels: list[str],
    values: list[float | int],
    text: list[str] | None,
    theme: dict,
    warnings: list[str],
    description: str,
    orientation: str = "v",
) -> ChartSpecRead:
    plotly_data = make_plotly_bar(x=labels, y=values, text=text, orientation=orientation)
    return _base_chart_spec(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type="bar" if orientation == "v" else "horizontal_bar",
        title=title,
        subtitle=None,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        targets=targets,
        data={"labels": labels, "values": values, "text": text},
        encoding={"x": "category", "y": "value", "text": "label"},
        plotly_data=plotly_data,
        plotly_layout=make_plotly_layout(
            title=title,
            subtitle=None,
            theme=theme,
            xaxis_title=None if orientation == "h" else "Categorias",
            yaxis_title="Frecuencia" if orientation == "v" else "Categorias",
        ),
        plotly_config=make_plotly_config(),
        theme=theme,
        warnings=warnings,
    )


def build_horizontal_bar_chart(**kwargs: Any) -> ChartSpecRead:
    return build_bar_chart(**kwargs, orientation="h")


def build_grouped_bar_chart(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    chart_type: str,
    title: str,
    source_type: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    categories: list[str],
    series: list[dict[str, Any]],
    theme: dict,
    warnings: list[str],
    description: str,
) -> ChartSpecRead:
    plotly_data, barmode = make_plotly_grouped_bar(categories=categories, series=series, stacked=chart_type == "stacked_bar")
    return _base_chart_spec(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type=chart_type,
        title=title,
        subtitle=None,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        targets=targets,
        data={"categories": categories, "series": series},
        encoding={"x": "category", "y": "value", "color": "series"},
        plotly_data=plotly_data,
        plotly_layout=make_plotly_layout(title=title, subtitle=None, theme=theme, xaxis_title="Categorias", yaxis_title="Valor", barmode=barmode),
        plotly_config=make_plotly_config(),
        theme=theme,
        warnings=warnings,
        groupable=True,
    )


def build_stacked_bar_chart(**kwargs: Any) -> ChartSpecRead:
    return build_grouped_bar_chart(**kwargs, chart_type="stacked_bar")


def build_pie_chart(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    chart_type: str,
    title: str,
    source_type: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    labels: list[str],
    values: list[float | int],
    theme: dict,
    warnings: list[str],
    description: str,
) -> ChartSpecRead:
    plotly_data = make_plotly_pie(labels=labels, values=values, hole=0.45 if chart_type == "donut" else 0.0)
    return _base_chart_spec(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type=chart_type,
        title=title,
        subtitle=None,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        targets=targets,
        data={"labels": labels, "values": values},
        encoding={"label": "category", "value": "value"},
        plotly_data=plotly_data,
        plotly_layout=make_plotly_layout(title=title, subtitle=None, theme=theme, showlegend=True),
        plotly_config=make_plotly_config(),
        theme=theme,
        warnings=warnings,
    )


def build_donut_chart(**kwargs: Any) -> ChartSpecRead:
    return build_pie_chart(**kwargs, chart_type="donut")


def build_histogram_chart(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    title: str,
    source_type: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    values: list[float | int],
    theme: dict,
    warnings: list[str],
    description: str,
    xaxis_title: str,
) -> ChartSpecRead:
    plotly_data = make_plotly_histogram(values=values)
    return _base_chart_spec(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type="histogram",
        title=title,
        subtitle=None,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        targets=targets,
        data={"values": values},
        encoding={"x": "value", "y": "count"},
        plotly_data=plotly_data,
        plotly_layout=make_plotly_layout(title=title, subtitle=None, theme=theme, xaxis_title=xaxis_title, yaxis_title="Frecuencia"),
        plotly_config=make_plotly_config(),
        theme=theme,
        warnings=warnings,
    )


def build_boxplot_chart(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    title: str,
    source_type: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    y_values: list[float | int],
    x_values: list[str] | None,
    theme: dict,
    warnings: list[str],
    description: str,
    yaxis_title: str,
) -> ChartSpecRead:
    plotly_data = make_plotly_boxplot(y=y_values, x=x_values)
    return _base_chart_spec(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type="boxplot",
        title=title,
        subtitle=None,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        targets=targets,
        data={"x": x_values, "y": y_values},
        encoding={"x": "group", "y": "value"},
        plotly_data=plotly_data,
        plotly_layout=make_plotly_layout(title=title, subtitle=None, theme=theme, xaxis_title="Grupo", yaxis_title=yaxis_title),
        plotly_config=make_plotly_config(),
        theme=theme,
        warnings=warnings,
        groupable=x_values is not None,
    )


def build_scatter_chart(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    title: str,
    source_type: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    x_values: list[float | int],
    y_values: list[float | int],
    theme: dict,
    warnings: list[str],
    description: str,
    xaxis_title: str,
    yaxis_title: str,
) -> ChartSpecRead:
    plotly_data = make_plotly_scatter(x=x_values, y=y_values)
    return _base_chart_spec(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type="scatter",
        title=title,
        subtitle=None,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        targets=targets,
        data={"x": x_values, "y": y_values},
        encoding={"x": "value", "y": "value"},
        plotly_data=plotly_data,
        plotly_layout=make_plotly_layout(title=title, subtitle=None, theme=theme, xaxis_title=xaxis_title, yaxis_title=yaxis_title),
        plotly_config=make_plotly_config(),
        theme=theme,
        warnings=warnings,
    )


def build_heatmap_chart(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    title: str,
    source_type: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    x_labels: list[str],
    y_labels: list[str],
    z_values: list[list[float | None]],
    theme: dict,
    warnings: list[str],
    description: str,
) -> ChartSpecRead:
    plotly_data = make_plotly_heatmap(z=z_values, x=x_labels, y=y_labels)
    return _base_chart_spec(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type="heatmap",
        title=title,
        subtitle=None,
        description=description,
        source_type=source_type,
        source_reference=source_reference,
        targets=targets,
        data={"x": x_labels, "y": y_labels, "z": z_values},
        encoding={"x": "target", "y": "target", "color": "coefficient"},
        plotly_data=plotly_data,
        plotly_layout=make_plotly_layout(title=title, subtitle=None, theme=theme, xaxis_title=None, yaxis_title=None),
        plotly_config=make_plotly_config(),
        theme=theme,
        warnings=warnings,
    )


def build_chart_from_frequency_table(**kwargs: Any) -> ChartSpecRead:
    return build_bar_chart(**kwargs)


def build_chart_from_descriptives(**kwargs: Any) -> ChartSpecRead:
    return build_histogram_chart(**kwargs)


def build_chart_from_correlation(**kwargs: Any) -> ChartSpecRead:
    return build_scatter_chart(**kwargs)


def build_chart_from_correlation_matrix(**kwargs: Any) -> ChartSpecRead:
    return build_heatmap_chart(**kwargs)


def build_chart_from_group_comparison(**kwargs: Any) -> ChartSpecRead:
    return build_boxplot_chart(**kwargs)


def build_chart_from_categorical_association(**kwargs: Any) -> ChartSpecRead:
    return build_grouped_bar_chart(**kwargs)


def build_chart_from_orchestrated_result(
    *,
    chart_id: str,
    form_id: str,
    project_id: str,
    chart_type: str,
    title: str,
    source_reference: str | None,
    targets: list[ChartTargetInput],
    data: dict[str, Any],
    encoding: dict[str, Any],
    plotly_data: list[dict[str, Any]],
    plotly_layout: dict[str, Any],
    plotly_config: dict[str, Any],
    theme: dict,
    warnings: list[str],
    description: str,
) -> ChartSpecRead:
    return _base_chart_spec(
        chart_id=chart_id,
        form_id=form_id,
        project_id=project_id,
        chart_type=chart_type,
        title=title,
        subtitle=None,
        description=description,
        source_type="chart_block",
        source_reference=source_reference,
        targets=targets,
        data=data,
        encoding=encoding,
        plotly_data=plotly_data,
        plotly_layout=plotly_layout,
        plotly_config=plotly_config,
        theme=theme,
        warnings=warnings,
        groupable=True,
    )
