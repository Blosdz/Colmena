from datetime import datetime, timezone

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.export_artifact import ExportArtifact
from app.models.form import Form
from app.models.form_instrument import FormInstrument
from app.models.scale import Scale
from app.schemas.instrument_sheet import (
    InstrumentMetadataRead,
    InstrumentSheetDimensionRead,
    InstrumentSheetRead,
)
from app.schemas.normality import NormalityTestResultRead
from app.services.advanced_scoring_service import AdvancedScoringService
from app.services.export_utils import build_export_artifact
from app.services.normality_service import NormalityService
from app.services.reliability_service import ReliabilityService

_SCALE_KIND_LABELS = {
    "frecuencia": "Frecuencia",
    "intensidad": "Intensidad",
    "acuerdo": "Acuerdo",
    "dificultad": "Dificultad",
    "satisfaccion": "Satisfaccion",
    "personalizada": "Personalizada",
}


class InstrumentSheetService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.exports_dir = self.settings.backend_dir / "data" / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.reliability_service = ReliabilityService(db)
        self.normality_service = NormalityService(db)
        self.advanced_scoring_service = AdvancedScoringService(db)

    def _get_form(self, form_id: str) -> Form:
        form = self.db.get(Form, form_id)
        if form is None or form.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
        return form

    def _active_instruments(self, form: Form) -> list[FormInstrument]:
        return sorted(
            (instrument for instrument in form.instruments if instrument.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )

    def _resolve_instrument(self, form: Form, instrument_id: str | None) -> FormInstrument:
        instruments = self._active_instruments(form)
        if not instruments:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form has no instruments")
        if instrument_id is None:
            return instruments[0]
        instrument = next((item for item in instruments if item.id == instrument_id), None)
        if instrument is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instrument not found for form")
        return instrument

    def _active_dimensions(self, instrument: FormInstrument):
        return sorted(
            (dimension for dimension in instrument.dimensions if dimension.deleted_at is None),
            key=lambda item: (item.sort_order, item.created_at),
        )

    def _scale_for_instrument(self, instrument: FormInstrument) -> Scale | None:
        if instrument.default_scale_id is None:
            return None
        return self.db.get(Scale, instrument.default_scale_id)

    def _build_metadata(self, instrument: FormInstrument) -> InstrumentMetadataRead:
        questions = [q for q in instrument.questions if q.deleted_at is None]
        dimensions = self._active_dimensions(instrument)
        scale = self._scale_for_instrument(instrument)
        scale_label: str | None = None
        if scale is not None:
            kind_label = _SCALE_KIND_LABELS.get(scale.scale_kind, scale.scale_kind)
            scale_label = f"Likert de {scale.points} puntos ({kind_label})"
        elif instrument.response_scale_name:
            scale_label = instrument.response_scale_name

        return InstrumentMetadataRead(
            instrument_id=instrument.id,
            name=instrument.name,
            acronym=instrument.acronym,
            author=instrument.author,
            year=instrument.year,
            objective=instrument.objective,
            application_mode=instrument.application_mode,
            response_scale_name=instrument.response_scale_name,
            scale_kind=scale.scale_kind if scale is not None else None,
            scale_points=scale.points if scale is not None else None,
            scale_label=scale_label,
            n_items=len(questions),
            n_dimensions=len(dimensions),
            dimension_names=[dimension.name for dimension in dimensions],
        )

    def _normality_pair(
        self,
        results_by_method: dict[str, list[NormalityTestResultRead]],
        *,
        target_type: str,
        target_id: str,
    ) -> tuple[NormalityTestResultRead | None, NormalityTestResultRead | None]:
        def _find(method: str) -> NormalityTestResultRead | None:
            return next(
                (
                    item
                    for item in results_by_method.get(method, [])
                    if item.target_type == target_type and item.target_id == target_id
                ),
                None,
            )

        return _find("shapiro"), _find("lilliefors")

    def get_instrument_sheet(
        self,
        form_id: str,
        *,
        instrument_id: str | None = None,
        decimals: int = 3,
        include_discarded: bool = False,
    ) -> InstrumentSheetRead:
        form = self._get_form(form_id)
        instrument = self._resolve_instrument(form, instrument_id)
        dimensions = self._active_dimensions(instrument)
        warnings: list[str] = []

        alpha = self.reliability_service.get_instrument_reliability(
            form_id, instrument.id, decimals=decimals, include_discarded=include_discarded
        )
        composite = self.reliability_service.get_instrument_composite_reliability(
            form_id, instrument.id, decimals=decimals, include_discarded=include_discarded
        )

        normality_by_method: dict[str, list[NormalityTestResultRead]] = {}
        for method in ("shapiro", "lilliefors"):
            report = self.normality_service.get_normality_report(
                form_id,
                method=method,
                decimals=decimals,
                include_discarded=include_discarded,
            )
            normality_by_method[method] = report.results

        instrument_shapiro, instrument_ks = self._normality_pair(
            normality_by_method, target_type="instrument", target_id=instrument.id
        )

        dimension_reads: list[InstrumentSheetDimensionRead] = []
        for dimension in dimensions:
            dim_alpha = self.reliability_service.get_dimension_reliability(
                form_id, dimension.id, decimals=decimals, include_discarded=include_discarded
            )
            dim_composite = self.reliability_service.get_dimension_composite_reliability(
                form_id, dimension.id, decimals=decimals, include_discarded=include_discarded
            )
            dim_shapiro, dim_ks = self._normality_pair(
                normality_by_method, target_type="dimension", target_id=dimension.id
            )
            dimension_reads.append(
                InstrumentSheetDimensionRead(
                    dimension_id=dimension.id,
                    dimension_name=dimension.name,
                    alpha=dim_alpha,
                    composite=dim_composite,
                    normality_shapiro=dim_shapiro,
                    normality_ks=dim_ks,
                )
            )

        baremo_resolution = self.advanced_scoring_service.resolve_variable_baremos(form_id)
        dimension_names = {dimension.name for dimension in dimensions}
        baremos = [
            item
            for item in baremo_resolution.items
            if (item.scoring_level == "instrument" and item.variable_label == instrument.name)
            or (item.scoring_level == "dimension" and item.variable_label in dimension_names)
        ]
        warnings.extend(baremo_resolution.warnings)

        return InstrumentSheetRead(
            form_id=form.id,
            project_id=form.project_id,
            metadata=self._build_metadata(instrument),
            alpha=alpha,
            composite=composite,
            normality_shapiro=instrument_shapiro,
            normality_ks=instrument_ks,
            dimensions=dimension_reads,
            baremos=baremos,
            warnings=list(dict.fromkeys(warnings)),
        )

    def export_instrument_sheet_excel(
        self,
        form_id: str,
        *,
        instrument_id: str | None = None,
    ) -> ExportArtifact:
        sheet = self.get_instrument_sheet(form_id, instrument_id=instrument_id)
        form = self._get_form(form_id)

        metadata_df = pd.DataFrame(
            [
                {"Campo": "Nombre", "Valor": sheet.metadata.name},
                {"Campo": "Acronimo", "Valor": sheet.metadata.acronym},
                {"Campo": "Autor", "Valor": sheet.metadata.author},
                {"Campo": "Anio", "Valor": sheet.metadata.year},
                {"Campo": "Objetivo", "Valor": sheet.metadata.objective},
                {"Campo": "Modo de aplicacion", "Valor": sheet.metadata.application_mode},
                {"Campo": "Tipo de escala", "Valor": sheet.metadata.scale_label},
                {"Campo": "N. de items", "Valor": sheet.metadata.n_items},
                {"Campo": "N. de dimensiones", "Valor": sheet.metadata.n_dimensions},
                {"Campo": "Dimensiones", "Valor": ", ".join(sheet.metadata.dimension_names)},
            ]
        )

        reliability_rows = [
            {
                "Nivel": "Instrumento",
                "Nombre": sheet.metadata.name,
                "N items": sheet.alpha.item_count,
                "Alfa de Cronbach": sheet.alpha.result.alpha,
                "Clasificacion alfa": sheet.alpha.result.classification,
                "Fiabilidad compuesta (CR)": sheet.composite.result.composite_reliability,
                "AVE": sheet.composite.result.ave,
                "Clasificacion CR/AVE": sheet.composite.result.classification,
            }
        ]
        for dimension in sheet.dimensions:
            reliability_rows.append(
                {
                    "Nivel": "Dimension",
                    "Nombre": dimension.dimension_name,
                    "N items": dimension.alpha.item_count,
                    "Alfa de Cronbach": dimension.alpha.result.alpha,
                    "Clasificacion alfa": dimension.alpha.result.classification,
                    "Fiabilidad compuesta (CR)": dimension.composite.result.composite_reliability,
                    "AVE": dimension.composite.result.ave,
                    "Clasificacion CR/AVE": dimension.composite.result.classification,
                }
            )
        reliability_df = pd.DataFrame(reliability_rows)

        def _normality_row(level: str, name: str, shapiro, ks) -> dict:
            return {
                "Nivel": level,
                "Nombre": name,
                "Shapiro-Wilk (estadistico)": shapiro.statistic if shapiro else None,
                "Shapiro-Wilk (p-valor)": shapiro.p_value if shapiro else None,
                "Shapiro-Wilk (clasificacion)": shapiro.classification if shapiro else None,
                "Kolmogorov-Smirnov (estadistico)": ks.statistic if ks else None,
                "Kolmogorov-Smirnov (p-valor)": ks.p_value if ks else None,
                "Kolmogorov-Smirnov (clasificacion)": ks.classification if ks else None,
            }

        normality_rows = [_normality_row("Instrumento", sheet.metadata.name, sheet.normality_shapiro, sheet.normality_ks)]
        for dimension in sheet.dimensions:
            normality_rows.append(
                _normality_row("Dimension", dimension.dimension_name, dimension.normality_shapiro, dimension.normality_ks)
            )
        normality_df = pd.DataFrame(normality_rows)

        baremo_rows = []
        for item in sheet.baremos:
            for level in item.levels:
                baremo_rows.append(
                    {
                        "Variable": item.variable_label,
                        "Nivel de scoring": item.scoring_level,
                        "Categoria": level.label,
                        "Minimo": level.min_value,
                        "Maximo": level.max_value,
                        "N": level.n,
                        "Porcentaje": level.percent,
                        "Interpretacion": level.interpretation,
                    }
                )
        baremo_df = pd.DataFrame(baremo_rows)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_name = f"form_{form.id}_ficha_tecnica_{timestamp}.xlsx"
        file_path = self.exports_dir / file_name

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            metadata_df.to_excel(writer, sheet_name="FichaTecnica", index=False)
            reliability_df.to_excel(writer, sheet_name="Fiabilidad", index=False)
            normality_df.to_excel(writer, sheet_name="Normalidad", index=False)
            (baremo_df if not baremo_df.empty else pd.DataFrame([{"Info": "Sin baremos configurados"}])).to_excel(
                writer, sheet_name="Baremos", index=False
            )

            for sheet_name in ("FichaTecnica", "Fiabilidad", "Normalidad", "Baremos"):
                worksheet = writer.book[sheet_name]
                worksheet.freeze_panes = "A2"
                if worksheet.dimensions and worksheet.dimensions != "A1:A1":
                    worksheet.auto_filter.ref = worksheet.dimensions
                for column_cells in worksheet.columns:
                    max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 50)

        return build_export_artifact(
            self.db,
            settings=self.settings,
            form=form,
            artifact_type="instrument_sheet_excel",
            file_name=file_name,
            file_path=file_path,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            metadata_json={"instrument_id": sheet.metadata.instrument_id},
        )
