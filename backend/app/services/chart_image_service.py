from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.analysis_run import AnalysisRun
from app.models.export_artifact import ExportArtifact
from app.models.form import Form
from app.schemas.chart_image import (
    ChartImageBase64Read,
    ChartImageDeleteResponse,
    ChartImageListRead,
    ChartImageRead,
    ChartImageUploadRequest,
    ChartImageUploadResponse,
)
from app.services.dataset_service import DatasetService
from app.utils.file_safety import ensure_path_within, sanitize_file_name
from app.utils.image_data import PNG_PREFIX, SVG_PREFIX, decode_chart_data_url


class ChartImageService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.exports_dir = (self.settings.backend_dir / "data" / "exports").resolve()
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_service = DatasetService(db)

    def _get_form(self, form_id: str) -> Form:
        return self.dataset_service._get_form(form_id)

    def _get_artifact(self, form_id: str, artifact_id: str) -> ExportArtifact:
        artifact = self.db.scalar(
            select(ExportArtifact).where(
                ExportArtifact.id == artifact_id,
                ExportArtifact.form_id == form_id,
                ExportArtifact.artifact_type.in_(("chart_image_png", "chart_image_svg")),
            )
        )
        if artifact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart image not found for form")
        return artifact

    def _validate_analysis_run(self, form_id: str, analysis_run_id: str | None) -> None:
        if not analysis_run_id:
            return
        analysis_run = self.db.scalar(
            select(AnalysisRun).where(AnalysisRun.id == analysis_run_id, AnalysisRun.form_id == form_id)
        )
        if analysis_run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AnalysisRun not found for form")

    def _mime_type(self, image_format: str) -> str:
        return "image/png" if image_format == "png" else "image/svg+xml"

    def _artifact_type(self, image_format: str) -> str:
        return "chart_image_png" if image_format == "png" else "chart_image_svg"

    def _file_suffix(self, image_format: str) -> str:
        return ".png" if image_format == "png" else ".svg"

    def _metadata_summary(self, payload: ChartImageUploadRequest) -> dict[str, Any]:
        metadata = dict(payload.metadata_json or {})
        metadata.setdefault("created_from_frontend", True)
        metadata.setdefault("source_type", payload.source_type or "manual")
        metadata.setdefault("chart_id", payload.chart_id)
        metadata.setdefault("chart_type", payload.chart_type)
        metadata.setdefault("title", payload.title)
        metadata.setdefault("format", payload.format)
        metadata.setdefault("analysis_run_id", payload.analysis_run_id)
        return metadata

    def _target_file_path(self, form_id: str, payload: ChartImageUploadRequest) -> Path:
        suffix = self._file_suffix(payload.format)
        fallback_name = f"form_{form_id}_chart_{uuid4().hex[:12]}{suffix}"
        requested_name = payload.file_name or fallback_name
        if not requested_name.lower().endswith(suffix):
            requested_name = f"{requested_name}{suffix}"
        safe_name = sanitize_file_name(requested_name, fallback=fallback_name)
        return ensure_path_within(self.exports_dir, self.exports_dir / safe_name)

    def _artifact_to_read(self, artifact: ExportArtifact) -> ChartImageRead:
        metadata = artifact.metadata_json if isinstance(artifact.metadata_json, dict) else {}
        return ChartImageRead(
            artifact_id=artifact.id,
            form_id=artifact.form_id or "",
            project_id=artifact.project_id,
            chart_id=metadata.get("chart_id"),
            chart_type=metadata.get("chart_type"),
            title=metadata.get("title"),
            format=str(metadata.get("format", "png")),
            file_name=artifact.file_name,
            file_path=(self.settings.backend_dir / artifact.file_path).as_posix(),
            mime_type=artifact.mime_type or "image/png",
            file_size_bytes=artifact.file_size_bytes or 0,
            created_at=artifact.created_at,
            metadata_json=metadata,
        )

    def upload_chart_image(self, form_id: str, payload: ChartImageUploadRequest) -> ChartImageUploadResponse:
        form = self._get_form(form_id)
        self._validate_analysis_run(form_id, payload.analysis_run_id)

        try:
            image_bytes = decode_chart_data_url(payload.data_url, payload.format)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        output_path = self._target_file_path(form_id, payload)
        output_path.write_bytes(image_bytes)

        artifact = ExportArtifact(
            project_id=form.project_id,
            form_id=form.id,
            artifact_type=self._artifact_type(payload.format),
            file_name=output_path.name,
            file_path=output_path.relative_to(self.settings.backend_dir).as_posix(),
            mime_type=self._mime_type(payload.format),
            file_size_bytes=output_path.stat().st_size,
            data_base64=payload.data_url,
            metadata_json=self._metadata_summary(payload),
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)

        return ChartImageUploadResponse(
            status="created",
            image=self._artifact_to_read(artifact),
            message="Chart image saved successfully.",
        )

    def list_chart_images(self, form_id: str, *, png_only: bool = False) -> ChartImageListRead:
        self._get_form(form_id)
        artifact_types = ("chart_image_png",) if png_only else ("chart_image_png", "chart_image_svg")
        items = list(
            self.db.scalars(
                select(ExportArtifact)
                .where(
                    ExportArtifact.form_id == form_id,
                    ExportArtifact.artifact_type.in_(artifact_types),
                )
                .order_by(ExportArtifact.created_at.desc())
            ).all()
        )
        mapped = [self._artifact_to_read(item) for item in items]
        return ChartImageListRead(form_id=form_id, total=len(mapped), items=mapped)

    def get_chart_image(self, form_id: str, artifact_id: str) -> ChartImageRead:
        artifact = self._get_artifact(form_id, artifact_id)
        return self._artifact_to_read(artifact)

    def get_chart_image_base64(self, form_id: str, artifact_id: str) -> ChartImageBase64Read:
        artifact = self._get_artifact(form_id, artifact_id)
        data_base64 = artifact.data_base64
        if not data_base64:
            # Fallback para artefactos viejos: releer el archivo de disco y re-codificar.
            import base64

            file_path = ensure_path_within(
                self.exports_dir, self.settings.backend_dir / artifact.file_path
            )
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chart image data not available",
                )
            prefix = PNG_PREFIX if artifact.artifact_type == "chart_image_png" else SVG_PREFIX
            encoded = base64.b64encode(file_path.read_bytes()).decode("ascii")
            data_base64 = f"{prefix}{encoded}"
        return ChartImageBase64Read(
            artifact_id=artifact.id,
            form_id=artifact.form_id or "",
            mime_type=artifact.mime_type or "image/png",
            data_base64=data_base64,
        )

    def delete_chart_image(self, form_id: str, artifact_id: str) -> ChartImageDeleteResponse:
        artifact = self._get_artifact(form_id, artifact_id)
        file_path = ensure_path_within(self.exports_dir, self.settings.backend_dir / artifact.file_path)
        if file_path.exists():
            file_path.unlink()
        self.db.delete(artifact)
        self.db.commit()
        return ChartImageDeleteResponse(status="deleted", artifact_id=artifact_id)
