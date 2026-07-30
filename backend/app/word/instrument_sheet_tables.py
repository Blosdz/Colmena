from __future__ import annotations

import uuid

from app.schemas.apa_table import (
    ApaTableCellRead,
    ApaTableColumnRead,
    ApaTableNoteRead,
    ApaTableRead,
    ApaTableRowRead,
)
from app.schemas.instrument_sheet import InstrumentSheetRead


def _cell(value, *, align: str = "left") -> ApaTableCellRead:
    return ApaTableCellRead(value="" if value is None else str(value), raw_value=value, align=align)


def _row(*values, align: str = "left") -> ApaTableRowRead:
    return ApaTableRowRead(cells=[_cell(value, align=align) for value in values])


def build_metadata_table(sheet: InstrumentSheetRead) -> ApaTableRead:
    metadata = sheet.metadata
    rows = [
        _row("Nombre", metadata.name),
        _row("Acronimo", metadata.acronym or "N/A"),
        _row("Autor(es)", metadata.author or "N/A"),
        _row("Anio", metadata.year or "N/A"),
        _row("Objetivo", metadata.objective or "N/A"),
        _row("Modo de aplicacion", metadata.application_mode or "N/A"),
        _row("Tipo de escala", metadata.scale_label or "N/A"),
        _row("Numero de items", metadata.n_items),
        _row("Numero de dimensiones", metadata.n_dimensions),
        _row("Dimensiones", ", ".join(metadata.dimension_names) or "N/A"),
    ]
    return ApaTableRead(
        table_id=str(uuid.uuid4()),
        table_type="instrument_metadata",
        title=f"Ficha tecnica del instrumento {metadata.name}",
        columns=[
            ApaTableColumnRead(key="field", label="Campo"),
            ApaTableColumnRead(key="value", label="Valor"),
        ],
        rows=rows,
        notes=[ApaTableNoteRead(text="Metadata descriptiva del instrumento aplicado en el estudio.")],
        markdown="",
        html="",
        ready_for_word=True,
        ready_for_frontend=True,
        warnings=[],
    )


def build_reliability_table(sheet: InstrumentSheetRead) -> ApaTableRead:
    rows = [
        _row(
            "Instrumento",
            sheet.metadata.name,
            sheet.alpha.item_count,
            sheet.alpha.result.alpha,
            sheet.alpha.result.classification,
            sheet.composite.result.composite_reliability,
            sheet.composite.result.ave,
            sheet.composite.result.classification,
        )
    ]
    for dimension in sheet.dimensions:
        rows.append(
            _row(
                "Dimension",
                dimension.dimension_name,
                dimension.alpha.item_count,
                dimension.alpha.result.alpha,
                dimension.alpha.result.classification,
                dimension.composite.result.composite_reliability,
                dimension.composite.result.ave,
                dimension.composite.result.classification,
            )
        )
    return ApaTableRead(
        table_id=str(uuid.uuid4()),
        table_type="reliability",
        title="Fiabilidad del instrumento (Alfa de Cronbach, Fiabilidad Compuesta y AVE)",
        columns=[
            ApaTableColumnRead(key="level", label="Nivel"),
            ApaTableColumnRead(key="name", label="Nombre"),
            ApaTableColumnRead(key="items", label="N. items", align="right"),
            ApaTableColumnRead(key="alpha", label="Alfa de Cronbach", align="right"),
            ApaTableColumnRead(key="alpha_class", label="Clasificacion"),
            ApaTableColumnRead(key="cr", label="Fiabilidad compuesta (CR)", align="right"),
            ApaTableColumnRead(key="ave", label="AVE", align="right"),
            ApaTableColumnRead(key="cr_class", label="Clasificacion CR/AVE"),
        ],
        rows=rows,
        notes=[
            ApaTableNoteRead(
                text=sheet.alpha.result.interpretation,
                note_type="statistical",
            ),
            ApaTableNoteRead(
                text=sheet.composite.result.interpretation,
                note_type="statistical",
            ),
        ],
        markdown="",
        html="",
        ready_for_word=True,
        ready_for_frontend=True,
        warnings=[],
    )


def build_normality_table(sheet: InstrumentSheetRead) -> ApaTableRead:
    def _row_for(level: str, name: str, shapiro, ks):
        return _row(
            level,
            name,
            shapiro.statistic if shapiro else None,
            shapiro.p_value if shapiro else None,
            shapiro.classification if shapiro else "not_applicable",
            ks.statistic if ks else None,
            ks.p_value if ks else None,
            ks.classification if ks else "not_applicable",
        )

    rows = [_row_for("Instrumento", sheet.metadata.name, sheet.normality_shapiro, sheet.normality_ks)]
    for dimension in sheet.dimensions:
        rows.append(
            _row_for("Dimension", dimension.dimension_name, dimension.normality_shapiro, dimension.normality_ks)
        )
    return ApaTableRead(
        table_id=str(uuid.uuid4()),
        table_type="normality",
        title="Pruebas de normalidad: Shapiro-Wilk y Kolmogorov-Smirnov (Lilliefors)",
        columns=[
            ApaTableColumnRead(key="level", label="Nivel"),
            ApaTableColumnRead(key="name", label="Nombre"),
            ApaTableColumnRead(key="shapiro_stat", label="Shapiro-Wilk (W)", align="right"),
            ApaTableColumnRead(key="shapiro_p", label="p", align="right"),
            ApaTableColumnRead(key="shapiro_class", label="Clasificacion"),
            ApaTableColumnRead(key="ks_stat", label="Kolmogorov-Smirnov (D)", align="right"),
            ApaTableColumnRead(key="ks_p", label="p", align="right"),
            ApaTableColumnRead(key="ks_class", label="Clasificacion"),
        ],
        rows=rows,
        notes=[
            ApaTableNoteRead(
                text="Se reporta el estadistico de Kolmogorov-Smirnov con correccion de Lilliefors "
                "(parametros estimados de la muestra), procedimiento adecuado cuando la media y desviacion "
                "estandar no se conocen a priori.",
                note_type="statistical",
            )
        ],
        markdown="",
        html="",
        ready_for_word=True,
        ready_for_frontend=True,
        warnings=[],
    )


def build_baremo_table(sheet: InstrumentSheetRead) -> ApaTableRead | None:
    rows = []
    for item in sheet.baremos:
        for level in item.levels:
            rows.append(
                _row(
                    item.variable_label,
                    item.scoring_level,
                    level.label,
                    level.min_value,
                    level.max_value,
                    level.n,
                    level.percent,
                )
            )
    if not rows:
        return None
    return ApaTableRead(
        table_id=str(uuid.uuid4()),
        table_type="baremo_variables",
        title="Baremos (rangos de interpretacion) del instrumento",
        columns=[
            ApaTableColumnRead(key="variable", label="Variable"),
            ApaTableColumnRead(key="level", label="Nivel de scoring"),
            ApaTableColumnRead(key="category", label="Categoria"),
            ApaTableColumnRead(key="min", label="Minimo", align="right"),
            ApaTableColumnRead(key="max", label="Maximo", align="right"),
            ApaTableColumnRead(key="n", label="N", align="right"),
            ApaTableColumnRead(key="percent", label="%", align="right"),
        ],
        rows=rows,
        notes=[ApaTableNoteRead(text="Rangos de interpretacion (baremos) vigentes para el instrumento.")],
        markdown="",
        html="",
        ready_for_word=True,
        ready_for_frontend=True,
        warnings=[],
    )


def build_instrument_sheet_tables(sheet: InstrumentSheetRead) -> list[ApaTableRead]:
    tables = [build_metadata_table(sheet), build_reliability_table(sheet), build_normality_table(sheet)]
    baremo_table = build_baremo_table(sheet)
    if baremo_table is not None:
        tables.append(baremo_table)
    return tables
