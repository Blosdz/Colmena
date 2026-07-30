from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.export_artifact import ExportArtifact
from app.models.form import Form


def build_export_artifact(
    db: Session,
    *,
    settings: Settings,
    form: Form,
    artifact_type: str,
    file_name: str,
    file_path: Path,
    mime_type: str,
    metadata_json: dict[str, Any],
) -> ExportArtifact:
    relative_path = file_path.relative_to(settings.backend_dir).as_posix()
    artifact = ExportArtifact(
        project_id=form.project_id,
        form_id=form.id,
        artifact_type=artifact_type,
        file_name=file_name,
        file_path=relative_path,
        mime_type=mime_type,
        file_size_bytes=file_path.stat().st_size,
        metadata_json=metadata_json,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact
