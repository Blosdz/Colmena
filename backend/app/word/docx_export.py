from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.models.export_artifact import ExportArtifact


def ensure_exports_dir(exports_dir: Path) -> Path:
    exports_dir.mkdir(parents=True, exist_ok=True)
    return exports_dir


def build_report_file_name(form_id: str, report_type: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"form_{form_id}_report_{report_type}_{timestamp}.docx"


def save_docx(document, output_path: Path) -> None:
    document.save(output_path)


def get_file_size(path: Path) -> int:
    return path.stat().st_size


def create_export_artifact_for_docx(
    *,
    form,
    file_name: str,
    relative_path: str,
    file_size_bytes: int,
    metadata_json: dict[str, Any],
) -> ExportArtifact:
    return ExportArtifact(
        project_id=form.project_id,
        form_id=form.id,
        artifact_type="word_report_docx",
        file_name=file_name,
        file_path=relative_path,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_size_bytes=file_size_bytes,
        metadata_json=metadata_json,
    )
