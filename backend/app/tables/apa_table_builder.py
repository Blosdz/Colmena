from __future__ import annotations

import hashlib
from typing import Any

from app.schemas.apa_table import (
    ApaTableCellRead,
    ApaTableColumnRead,
    ApaTableNoteRead,
    ApaTableRead,
    ApaTableRowRead,
)
from app.tables.apa_formatter import (
    format_decimal,
    format_effect_size,
    format_missing,
    format_n,
    format_p_value,
    format_percentage,
    format_statistic,
    safe_text,
)
from app.tables.apa_html import render_apa_html
from app.tables.apa_markdown import render_apa_markdown


def build_table_id(table_type: str, title: str) -> str:
    digest = hashlib.md5(f"{table_type}:{title}".encode("utf-8")).hexdigest()[:10]
    return f"{table_type}_{digest}"


def build_table_title(table_type: str, context: str | None = None) -> str:
    defaults = {
        "frequencies": "Tabla de frecuencias",
        "descriptives": "Descriptivos numericos",
        "normality": "Pruebas de normalidad",
        "correlation": "Correlacion entre variables",
        "correlation_matrix": "Matriz de correlaciones",
        "group_comparison": "Comparacion entre grupos",
        "categorical_association": "Asociacion entre variables categoricas",
        "scoring_summary": "Resumen de scoring",
        "score_band_distribution": "Distribucion por baremos",
        "control_scale_flags": "Resumen de escalas de control",
        "orchestrated_summary": "Resumen de analisis orquestado",
    }
    base = defaults.get(table_type, "Tabla APA")
    return f"{base}: {context}" if context else base


def build_table_notes(table_type: str, extra_notes: list[str] | None = None) -> list[ApaTableNoteRead]:
    base_notes = {
        "frequencies": ["Los porcentajes validos se calcularon excluyendo los casos perdidos."],
        "descriptives": ["M = media; DE = desviacion estandar; Mdn = mediana."],
        "normality": ["La decision se basa en el nivel de significancia configurado."],
        "correlation": ["La correlacion no implica causalidad."],
        "correlation_matrix": ["La matriz presenta coeficientes por pares y debe interpretarse sin asumir causalidad."],
        "group_comparison": ["La interpretacion debe considerar el diseno de investigacion y el tamano del efecto."],
        "categorical_association": ["Los resultados indican asociacion estadistica entre categorias, no causalidad."],
        "scoring_summary": ["Los niveles obtenidos deben interpretarse segun la ficha tecnica del instrumento y el contexto de aplicacion."],
        "score_band_distribution": ["Los niveles corresponden a los rangos configurados para el instrumento y no implican diagnostico por si mismos."],
        "control_scale_flags": ["Las escalas de control apoyan la revision de validez de respuesta, pero no sustituyen el juicio metodologico."],
        "orchestrated_summary": ["Tabla generada a partir de bloques consolidados del analisis guiado."],
    }
    notes = [ApaTableNoteRead(note_type="general", text=text) for text in base_notes.get(table_type, [])]
    for text in extra_notes or []:
        notes.append(ApaTableNoteRead(note_type="caution", text=text))
    return notes


def _format_value(value: Any, format_type: str | None, decimals: int) -> str:
    if format_type == "integer":
        return format_n(value if value is not None else None)
    if format_type == "decimal":
        return format_decimal(value, decimals=decimals)
    if format_type == "p_value":
        return format_p_value(value)
    if format_type == "percentage":
        return format_percentage(value, decimals=1)
    if format_type == "statistic":
        return format_statistic(value, decimals=decimals)
    return format_missing(value)


def _column_align(format_type: str | None) -> str:
    if format_type in {"integer", "decimal", "p_value", "percentage", "statistic"}:
        return "right"
    return "left"


def _cell_from_column(
    column: ApaTableColumnRead,
    raw_value: Any,
    *,
    decimals: int,
) -> ApaTableCellRead:
    return ApaTableCellRead(
        value=_format_value(raw_value, column.format_type, decimals),
        raw_value=raw_value,
        align=column.align,
        format_type=column.format_type,
    )


def build_table(
    *,
    table_type: str,
    title: str,
    columns: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    notes: list[str] | None = None,
    warnings: list[str] | None = None,
    subtitle: str | None = None,
    source: dict[str, Any] | None = None,
    decimals: int = 3,
    table_number: int | None = None,
    ready_for_word: bool = False,
) -> ApaTableRead:
    column_models = [
        ApaTableColumnRead(
            key=item["key"],
            label=item["label"],
            align=item.get("align", _column_align(item.get("format_type"))),
            format_type=item.get("format_type"),
        )
        for item in columns
    ]
    row_models = [
        ApaTableRowRead(
            row_type=row.get("row_type", "body"),
            cells=[
                _cell_from_column(column, row.get(column.key), decimals=decimals)
                for column in column_models
            ],
        )
        for row in rows
    ]
    note_models = build_table_notes(table_type, notes)
    table = ApaTableRead(
        table_id=build_table_id(table_type, title),
        table_number=table_number,
        table_type=table_type,
        title=title,
        subtitle=subtitle,
        columns=column_models,
        rows=row_models,
        notes=note_models,
        markdown="",
        html="",
        ready_for_word=ready_for_word,
        ready_for_frontend=True,
        warnings=list(dict.fromkeys(warnings or [])),
        source=source,
    )
    markdown = render_apa_markdown(table)
    html = render_apa_html(table)
    return table.model_copy(update={"markdown": markdown, "html": html})


def build_frequency_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
    include_variable_column: bool,
) -> ApaTableRead:
    columns: list[dict[str, Any]] = []
    if include_variable_column:
        columns.append({"key": "variable", "label": "Variable", "format_type": "text"})
    columns.extend(
        [
            {"key": "category", "label": "Categoria", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "percent", "label": "%", "format_type": "percentage"},
            {"key": "valid_percent", "label": "% valido", "format_type": "percentage"},
            {"key": "cumulative_percent", "label": "% acumulado", "format_type": "percentage"},
        ]
    )
    extra_notes = []
    if "expected_counts_low" in warnings:
        extra_notes.append("La interpretacion debe realizarse con cautela debido a frecuencias esperadas bajas.")
    return build_table(
        table_type="frequencies",
        title=title,
        columns=columns,
        rows=rows,
        notes=extra_notes,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_descriptive_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    return build_table(
        table_type="descriptives",
        title=title,
        columns=[
            {"key": "variable", "label": "Variable", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "mean", "label": "M", "format_type": "decimal"},
            {"key": "sd", "label": "DE", "format_type": "decimal"},
            {"key": "median", "label": "Mdn", "format_type": "decimal"},
            {"key": "minimum", "label": "Min.", "format_type": "decimal"},
            {"key": "maximum", "label": "Max.", "format_type": "decimal"},
            {"key": "skewness", "label": "Asimetria", "format_type": "decimal"},
            {"key": "kurtosis", "label": "Curtosis", "format_type": "decimal"},
        ],
        rows=rows,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_normality_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    return build_table(
        table_type="normality",
        title=title,
        columns=[
            {"key": "variable", "label": "Variable", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "test", "label": "Prueba", "format_type": "text"},
            {"key": "statistic", "label": "Estadistico", "format_type": "statistic"},
            {"key": "p_value", "label": "p", "format_type": "p_value"},
            {"key": "decision", "label": "Decision", "format_type": "text"},
        ],
        rows=rows,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_correlation_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    return build_table(
        table_type="correlation",
        title=title,
        columns=[
            {"key": "variable_1", "label": "Variable 1", "format_type": "text"},
            {"key": "variable_2", "label": "Variable 2", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "method", "label": "Metodo", "format_type": "text"},
            {"key": "coefficient", "label": "Coeficiente", "format_type": "decimal"},
            {"key": "p_value", "label": "p", "format_type": "p_value"},
            {"key": "magnitude", "label": "Magnitud", "format_type": "text"},
        ],
        rows=rows,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_correlation_matrix_table(
    *,
    title: str,
    columns_labels: list[str],
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    columns = [{"key": "variable", "label": "Variable", "format_type": "text"}]
    columns.extend({"key": label, "label": label, "format_type": "decimal"} for label in columns_labels)
    return build_table(
        table_type="correlation_matrix",
        title=title,
        columns=columns,
        rows=rows,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_group_comparison_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    return build_table(
        table_type="group_comparison",
        title=title,
        columns=[
            {"key": "group", "label": "Grupo", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "mean", "label": "M", "format_type": "decimal"},
            {"key": "sd", "label": "DE", "format_type": "decimal"},
            {"key": "statistic", "label": "Estadistico", "format_type": "statistic"},
            {"key": "degrees_of_freedom", "label": "gl", "format_type": "text"},
            {"key": "p_value", "label": "p", "format_type": "p_value"},
            {"key": "effect_size", "label": "Tamano del efecto", "format_type": "text"},
        ],
        rows=rows,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_categorical_association_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    extra_notes = []
    if "expected_counts_low" in warnings:
        extra_notes.append("La interpretacion debe realizarse con cautela debido a frecuencias esperadas bajas.")
    return build_table(
        table_type="categorical_association",
        title=title,
        columns=[
            {"key": "categories", "label": "Categorias", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "row_percent", "label": "% fila", "format_type": "percentage"},
            {"key": "column_percent", "label": "% columna", "format_type": "percentage"},
            {"key": "statistic", "label": "Estadistico", "format_type": "statistic"},
            {"key": "degrees_of_freedom", "label": "gl", "format_type": "text"},
            {"key": "p_value", "label": "p", "format_type": "p_value"},
            {"key": "effect_size", "label": "Tamano del efecto", "format_type": "text"},
        ],
        rows=rows,
        notes=extra_notes,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_scoring_summary_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    return build_table(
        table_type="scoring_summary",
        title=title,
        columns=[
            {"key": "score_name", "label": "Puntaje", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "mean", "label": "M", "format_type": "decimal"},
            {"key": "sd", "label": "DE", "format_type": "decimal"},
            {"key": "minimum", "label": "Min.", "format_type": "decimal"},
            {"key": "maximum", "label": "Max.", "format_type": "decimal"},
            {"key": "predominant_level", "label": "Nivel predominante", "format_type": "text"},
        ],
        rows=rows,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_score_band_distribution_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    return build_table(
        table_type="score_band_distribution",
        title=title,
        columns=[
            {"key": "level", "label": "Nivel", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "percent", "label": "%", "format_type": "percentage"},
            {"key": "interpretation", "label": "Interpretacion", "format_type": "text"},
        ],
        rows=rows,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_control_scale_flags_table(
    *,
    title: str,
    rows: list[dict[str, Any]],
    warnings: list[str],
    source: dict[str, Any] | None,
    decimals: int,
) -> ApaTableRead:
    return build_table(
        table_type="control_scale_flags",
        title=title,
        columns=[
            {"key": "control_scale", "label": "Escala de control", "format_type": "text"},
            {"key": "status", "label": "Estado", "format_type": "text"},
            {"key": "n", "label": "n", "format_type": "integer"},
            {"key": "percent", "label": "%", "format_type": "percentage"},
        ],
        rows=rows,
        warnings=warnings,
        source=source,
        decimals=decimals,
    )


def build_from_orchestrated_analysis(
    *,
    table_type: str,
    title: str,
    rows: list[dict[str, Any]],
    columns: list[str],
    source: dict[str, Any] | None,
    warnings: list[str],
    decimals: int,
    source_result: str | None,
) -> ApaTableRead:
    return build_table(
        table_type=table_type,
        title=title,
        columns=[{"key": column, "label": column, "format_type": "text"} for column in columns],
        rows=rows,
        warnings=warnings,
        source={**(source or {}), "source_result": source_result},
        decimals=decimals,
    )
