"""Renders export-ready (matplotlib, 'estilo tesis') chart PNGs.

Each render_* method reads exclusively from the same service that already
feeds the on-screen chart (AdvancedScoringService, NormalityService,
CorrelationService), so the exported figure and the screen never disagree.
matplotlib only draws — no statistic is recomputed here.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.charts.export_renderer import (
    render_baremo_levels_chart,
    render_correlation_scatter_chart,
    render_dimension_coefficient_bars_chart,
    render_normality_histogram_chart,
)
from app.core.config import get_settings
from app.models.form_dimension import FormDimension
from app.schemas.correlation import CorrelationMatrixRequest, CorrelationRequest, CorrelationTargetInput
from app.services.advanced_scoring_service import AdvancedScoringService
from app.services.correlation_service import CorrelationService
from app.services.normality_service import NormalityService


class ChartExportService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.advanced_scoring_service = AdvancedScoringService(db)
        self.normality_service = NormalityService(db)
        self.correlation_service = CorrelationService(db)
        self.renders_dir = (self.settings.backend_dir / "data" / "exports" / "chart_renders").resolve()
        self.renders_dir.mkdir(parents=True, exist_ok=True)

    def _output_path(self, prefix: str) -> Path:
        return self.renders_dir / f"{prefix}-{uuid4().hex[:8]}.png"

    def render_baremo_levels_png(self, form_id: str, scoring_config_id: str) -> Path:
        resolution = self.advanced_scoring_service.resolve_variable_baremos(form_id)
        item = next((entry for entry in resolution.items if entry.scoring_config_id == scoring_config_id), None)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay un baremo resuelto para ese scoring_config_id en este formulario.",
            )
        if not item.levels:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"'{item.variable_label}' no tiene niveles de baremo resueltos todavia.",
            )

        return render_baremo_levels_chart(
            variable_label=item.variable_label,
            levels=[level.model_dump() for level in item.levels],
            output_path=self._output_path(f"baremo-levels-{scoring_config_id}"),
        )

    def render_normality_histogram_png(
        self,
        form_id: str,
        *,
        target_type: str,
        target_id: str,
        bins: int = 10,
    ) -> Path:
        histogram = self.normality_service.get_histogram(form_id, target_type=target_type, target_id=target_id, bins=bins)
        if not histogram.bins:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No hay suficientes datos para construir el histograma (se requieren al menos 5 casos validos).",
            )
        return render_normality_histogram_chart(
            target_name=histogram.target_name,
            bins=[bin_.model_dump() for bin_ in histogram.bins],
            curve=[point.model_dump() for point in histogram.curve],
            mean=histogram.mean,
            std=histogram.std,
            valid_n=histogram.valid_n,
            output_path=self._output_path(f"normality-histogram-{target_id}"),
        )

    def render_correlation_scatter_png(
        self,
        form_id: str,
        *,
        x_type: str,
        x_id: str,
        y_type: str,
        y_id: str,
    ) -> Path:
        run = self.correlation_service.run_pair_correlation(
            form_id,
            CorrelationRequest(
                x=CorrelationTargetInput(target_type=x_type, target_id=x_id),
                y=CorrelationTargetInput(target_type=y_type, target_id=y_id),
                method="auto",
                store_result=False,
            ),
        )
        result = run.result
        if not result.x_values or not result.y_values:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No hay suficientes pares validos para graficar la dispersion.",
            )
        return render_correlation_scatter_chart(
            x_label=result.x_target.label,
            y_label=result.y_target.label,
            x_values=result.x_values,
            y_values=result.y_values,
            output_path=self._output_path(f"correlation-scatter-{x_id}-{y_id}"),
        )

    def render_dimension_coefficient_bars_png(
        self,
        form_id: str,
        *,
        instrument_id: str,
        y_type: str,
        y_id: str,
    ) -> Path:
        dimensions = list(
            self.db.scalars(
                select(FormDimension)
                .where(FormDimension.instrument_id == instrument_id, FormDimension.deleted_at.is_(None))
                .order_by(FormDimension.sort_order)
            ).all()
        )
        dimension_targets = [
            CorrelationTargetInput(target_type="dimension", target_id=dimension.id, label=dimension.name)
            for dimension in dimensions
        ]
        if not dimension_targets:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Este instrumento no tiene dimensiones para desglosar.",
            )
        matrix = self.correlation_service.run_correlation_matrix(
            form_id,
            CorrelationMatrixRequest(
                targets=[*dimension_targets, CorrelationTargetInput(target_type=y_type, target_id=y_id)],
                method="auto",
                store_result=False,
            ),
        )
        y_target_id = next((target.target_id for target in matrix.targets if target.target_id == y_id), y_id)
        rows = [
            {
                "dimension_label": cell.row_label if cell.column_target_id == y_target_id else cell.column_label,
                "coefficient": cell.coefficient,
                "p_value": cell.p_value,
            }
            for cell in matrix.cells
            if cell.row_target_id != cell.column_target_id
            and (cell.row_target_id == y_target_id or cell.column_target_id == y_target_id)
        ]
        # Each dimension appears twice in a symmetric matrix (once per triangle); keep one row per dimension.
        seen: set[str] = set()
        deduped_rows = []
        for row in rows:
            if row["dimension_label"] in seen:
                continue
            seen.add(row["dimension_label"])
            deduped_rows.append(row)
        if not deduped_rows:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se encontraron celdas de correlacion para esta combinacion.",
            )
        y_label = next((target.label for target in matrix.targets if target.target_id == y_id), y_id)
        return render_dimension_coefficient_bars_chart(
            y_label=y_label,
            rows=deduped_rows,
            output_path=self._output_path(f"dimension-bars-{instrument_id}-{y_id}"),
        )
