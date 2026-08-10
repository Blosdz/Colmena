# Normalización del backend COLMENA — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cerrar los huecos identificados en `docs/superpowers/specs/2026-08-09-backend-normalization-design.md` — versionado de formularios, `audit_log` genérico, y los fixes de consistencia de esquema — en `COLMENA/backend` (FastAPI + SQLAlchemy + Alembic + SQLite).

**Architecture:** Todo el trabajo vive en `COLMENA/backend`. Se añaden 3 tablas nuevas (`form_versions`, `audit_logs`, y columnas nuevas en tablas existentes) vía migraciones Alembic separadas, más los cambios de servicio correspondientes. Los tests usan el patrón ya existente (`tests/conftest.py`: SQLite en memoria vía `Base.metadata.create_all`, `TestClient`), así que **los modelos SQLAlchemy son la fuente de verdad para los tests**; las migraciones Alembic son el camino de actualización para la base de datos real y deben mantenerse en sync manualmente con los modelos (no hay autogenerate en este proyecto — se escriben a mano, como las 18 existentes).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x (`Mapped`/`mapped_column`), Alembic (con `batch_alter_table` para SQLite), Pydantic v2, pytest + `TestClient`.

## Global Constraints

- Base de datos real es **SQLite** (no Postgres) — `COLMENA/backend/app/core/config.py:database_url` → `sqlite:///...`. No hay tipos `JSONB`; se usa `sa.JSON()` en todos lados.
- IDs son `String(36)` (UUID como texto), nunca `sa.Uuid` nativo — seguir `app/models/base.py:UUIDPrimaryKeyMixin`.
- Toda tabla usa `TimestampMixin` (`created_at`/`updated_at`); las que soportan borrado lógico usan además `SoftDeleteMixin` (`deleted_at`) — nunca hard-delete en flujo normal salvo donde se indique explícitamente.
- Migraciones nuevas: prefijo de fecha `20260809_NN_<slug>.py`, encadenar `down_revision` a la última migración real (`20260807_18` es la última existente). Alterar tablas existentes en SQLite requiere `op.batch_alter_table(...)`.
- Todo modelo nuevo se registra en `app/models/__init__.py` (import + `__all__`); todo router nuevo se registra en `app/main.py` con `app.include_router(...)`.
- Los tests corren con: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/ -x -q` (usar el `venv` del proyecto, no instalar dependencias nuevas).
- No se modifica ninguna de las 18 migraciones existentes.

---

### Task 1: Modelo y migración de `AuditLog` + `audit_service`

**Files:**
- Create: `COLMENA/backend/app/models/audit_log.py`
- Modify: `COLMENA/backend/app/models/__init__.py` (agregar import + `__all__`)
- Create: `COLMENA/backend/alembic/versions/20260809_19_create_audit_logs.py`
- Create: `COLMENA/backend/app/schemas/audit_log.py`
- Modify: `COLMENA/backend/app/schemas/__init__.py` (agregar import + `__all__`)
- Create: `COLMENA/backend/app/services/audit_service.py`
- Create: `COLMENA/backend/tests/test_audit_service.py`

**Interfaces:**
- Produces: `app.models.audit_log.AuditLog` (columns: `id, user_id, project_id, entity_type, entity_id, action, old_data, new_data, created_at`); `app.services.audit_service.record(db: Session, *, user_id: str | None, project_id: str | None, entity_type: str, entity_id: str, action: str, old_data: dict | list | None = None, new_data: dict | list | None = None) -> AuditLog`.

- [ ] **Step 1: Crear el modelo `AuditLog`**

```python
# COLMENA/backend/app/models/audit_log.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Registro inmutable de acciones significativas (crear/editar/borrar/publicar).

    Sin SoftDeleteMixin ni updated_at: es un log de solo inserción.
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    old_data: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    new_data: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    user: Mapped["User | None"] = relationship()
    project: Mapped["Project | None"] = relationship()
```

- [ ] **Step 2: Registrar el modelo en `app/models/__init__.py`**

Agregar `from app.models.audit_log import AuditLog` (orden alfabético, antes de `from app.models.base import Base`) y `"AuditLog"` en `__all__` (antes de `"Base"`).

- [ ] **Step 3: Escribir la migración**

```python
# COLMENA/backend/alembic/versions/20260809_19_create_audit_logs.py
"""create audit_logs table

Revision ID: 20260809_19
Revises: 20260807_18
Create Date: 2026-08-09 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260809_19"
down_revision: Union[str, Sequence[str], None] = "20260807_18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("old_data", sa.JSON(), nullable=True),
        sa.Column("new_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", "audit_logs")
    op.drop_index("ix_audit_logs_entity_id", "audit_logs")
    op.drop_index("ix_audit_logs_entity_type", "audit_logs")
    op.drop_index("ix_audit_logs_project_id", "audit_logs")
    op.drop_index("ix_audit_logs_user_id", "audit_logs")
    op.drop_table("audit_logs")
```

- [ ] **Step 4: Crear el schema Pydantic**

```python
# COLMENA/backend/app/schemas/audit_log.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None
    project_id: str | None
    entity_type: str
    entity_id: str
    action: str
    old_data: dict | list | None
    new_data: dict | list | None
    created_at: datetime
```

Agregar `from app.schemas.audit_log import AuditLogRead` y `"AuditLogRead"` en `app/schemas/__init__.py`.

- [ ] **Step 5: Implementar `audit_service.py`**

```python
# COLMENA/backend/app/services/audit_service.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

VALID_ACTIONS = {"create", "update", "delete", "publish", "archive", "close", "reopen"}


def record(
    db: Session,
    *,
    user_id: str | None,
    project_id: str | None,
    entity_type: str,
    entity_id: str,
    action: str,
    old_data: dict | list | None = None,
    new_data: dict | list | None = None,
) -> AuditLog:
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid audit action: {action}")
    entry = AuditLog(
        user_id=user_id,
        project_id=project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_data=old_data,
        new_data=new_data,
    )
    db.add(entry)
    db.flush()
    return entry
```

- [ ] **Step 6: Escribir y correr el test**

```python
# COLMENA/backend/tests/test_audit_service.py
import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.user import User
from app.services import audit_service


def test_record_creates_audit_log_entry(client):
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        user = db.scalar(select(User).limit(1))
        project = Project(user_id=user.id, title="Proyecto auditado")
        db.add(project)
        db.flush()

        entry = audit_service.record(
            db,
            user_id=user.id,
            project_id=project.id,
            entity_type="project",
            entity_id=project.id,
            action="create",
            new_data={"title": "Proyecto auditado"},
        )
        db.commit()

        assert entry.id is not None
        stored = db.scalar(select(AuditLog).where(AuditLog.id == entry.id))
        assert stored.entity_type == "project"
        assert stored.action == "create"
        assert stored.new_data == {"title": "Proyecto auditado"}
        assert stored.old_data is None
    finally:
        db.close()


def test_record_rejects_invalid_action(client):
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        with pytest.raises(ValueError):
            audit_service.record(
                db,
                user_id=None,
                project_id=None,
                entity_type="project",
                entity_id="x",
                action="not_a_real_action",
            )
    finally:
        db.close()
```

El fixture `client` (de `tests/conftest.py`) ya crea/dropea las tablas por test (`reset_database`) y registra al usuario de prueba vía `get_current_user` override — usarlo como parámetro fuerza que el esquema esté listo antes de abrir una sesión manual.

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_audit_service.py -v`
Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
cd COLMENA/backend
git add app/models/audit_log.py app/models/__init__.py alembic/versions/20260809_19_create_audit_logs.py app/schemas/audit_log.py app/schemas/__init__.py app/services/audit_service.py tests/test_audit_service.py
git commit -m "feat: add AuditLog model, migration and audit_service"
```

---

### Task 2: Modelo y migración de `FormVersion`

**Files:**
- Create: `COLMENA/backend/app/models/form_version.py`
- Modify: `COLMENA/backend/app/models/__init__.py`
- Modify: `COLMENA/backend/app/models/form.py:1-33` (agregar `current_version_id` + relationship `versions`)
- Modify: `COLMENA/backend/app/models/form_response.py:1-31` (agregar `form_version_id`)
- Create: `COLMENA/backend/alembic/versions/20260809_20_create_form_versions.py`
- Create: `COLMENA/backend/app/schemas/form_version.py`
- Modify: `COLMENA/backend/app/schemas/__init__.py`
- Create: `COLMENA/backend/tests/test_form_versions_model.py`

**Interfaces:**
- Consumes: nada nuevo de tareas anteriores.
- Produces: `app.models.form_version.FormVersion` (`id, form_id, version_number, status, snapshot_json, published_at, archived_at, created_at, updated_at`); `Form.current_version_id` (nullable FK); `Form.versions` (relationship); `FormResponse.form_version_id` (nullable FK). Tareas 3 y 4 consumen estos campos.

- [ ] **Step 1: Crear el modelo `FormVersion`**

```python
# COLMENA/backend/app/models/form_version.py
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FormVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Snapshot congelado del contenido de un formulario en un momento dado.

    ``snapshot_json`` se genera a partir de las tablas normalizadas
    (secciones, instrumentos, dimensiones, preguntas, opciones) al publicar;
    es una copia de lectura para exportes/reportes, no la fuente de verdad.
    """

    __tablename__ = "form_versions"

    form_id: Mapped[str] = mapped_column(
        ForeignKey("forms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    snapshot_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    form: Mapped["Form"] = relationship(back_populates="versions", foreign_keys=[form_id])
```

- [ ] **Step 2: Registrar en `app/models/__init__.py`**

Agregar `from app.models.form_version import FormVersion` y `"FormVersion"` en `__all__` (orden alfabético, junto a los demás `Form*`).

- [ ] **Step 3: Agregar `current_version_id` a `Form`**

En `app/models/form.py`, después de la línea `metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)` (línea 26 actual) agregar:

```python
    current_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("form_versions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
        index=True,
    )
```

Y en el bloque de relationships (tras `project: Mapped["Project"] = relationship(back_populates="forms")`) agregar:

```python
    current_version: Mapped["FormVersion | None"] = relationship(foreign_keys=[current_version_id])
    versions: Mapped[list["FormVersion"]] = relationship(
        back_populates="form", foreign_keys="FormVersion.form_id"
    )
```

`use_alter=True` es necesario porque `forms` y `form_versions` se referencian mutuamente (form_versions.form_id -> forms.id, forms.current_version_id -> form_versions.id); SQLAlchemy necesita crear esta FK circular en un ALTER separado.

- [ ] **Step 4: Agregar `form_version_id` a `FormResponse`**

En `app/models/form_response.py`, después de `form_id: Mapped[str] = mapped_column(ForeignKey("forms.id"), nullable=False, index=True)` agregar:

```python
    form_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("form_versions.id", ondelete="RESTRICT"), nullable=True, index=True
    )
```

- [ ] **Step 5: Escribir la migración**

```python
# COLMENA/backend/alembic/versions/20260809_20_create_form_versions.py
"""create form_versions table and link forms/form_responses

Revision ID: 20260809_20
Revises: 20260809_19
Create Date: 2026-08-09 00:00:01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260809_20"
down_revision: Union[str, Sequence[str], None] = "20260809_19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "form_versions",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("form_id", sa.String(36), sa.ForeignKey("forms.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_form_versions_form_id", "form_versions", ["form_id"])
    op.create_index("ix_form_versions_status", "form_versions", ["status"])

    with op.batch_alter_table("forms", schema=None) as batch:
        batch.add_column(sa.Column("current_version_id", sa.String(36), nullable=True))
        batch.create_foreign_key(
            "fk_forms_current_version_id_form_versions",
            "form_versions",
            ["current_version_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_forms_current_version_id", "forms", ["current_version_id"])

    with op.batch_alter_table("form_responses", schema=None) as batch:
        batch.add_column(sa.Column("form_version_id", sa.String(36), nullable=True))
        batch.create_foreign_key(
            "fk_form_responses_form_version_id_form_versions",
            "form_versions",
            ["form_version_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    op.create_index("ix_form_responses_form_version_id", "form_responses", ["form_version_id"])


def downgrade() -> None:
    op.drop_index("ix_form_responses_form_version_id", "form_responses")
    with op.batch_alter_table("form_responses", schema=None) as batch:
        batch.drop_constraint("fk_form_responses_form_version_id_form_versions", type_="foreignkey")
        batch.drop_column("form_version_id")

    op.drop_index("ix_forms_current_version_id", "forms")
    with op.batch_alter_table("forms", schema=None) as batch:
        batch.drop_constraint("fk_forms_current_version_id_form_versions", type_="foreignkey")
        batch.drop_column("current_version_id")

    op.drop_index("ix_form_versions_status", "form_versions")
    op.drop_index("ix_form_versions_form_id", "form_versions")
    op.drop_table("form_versions")
```

- [ ] **Step 6: Crear el schema Pydantic**

```python
# COLMENA/backend/app/schemas/form_version.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FormVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    form_id: str
    version_number: int
    status: str
    snapshot_json: dict | list | None
    published_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class FormVersionListResponse(BaseModel):
    items: list[FormVersionRead]
    total: int
```

Agregar `from app.schemas.form_version import FormVersionListResponse, FormVersionRead` y ambos nombres en `app/schemas/__init__.py`.

- [ ] **Step 7: Test de que el modelo y las relaciones funcionan**

```python
# COLMENA/backend/tests/test_form_versions_model.py
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.form import Form
from app.models.form_version import FormVersion
from app.models.project import Project
from app.models.user import User


def test_form_version_roundtrip(client):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).limit(1))
        project = Project(user_id=user.id, title="Proyecto versionado")
        db.add(project)
        db.flush()
        form = Form(project_id=project.id, title="Formulario versionado")
        db.add(form)
        db.flush()

        version = FormVersion(
            form_id=form.id,
            version_number=1,
            status="published",
            snapshot_json={"questions": []},
        )
        db.add(version)
        db.flush()
        form.current_version_id = version.id
        db.commit()

        db.refresh(form)
        assert form.current_version_id == version.id
        assert form.current_version.snapshot_json == {"questions": []}
        assert form.versions[0].id == version.id
    finally:
        db.close()
```

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_form_versions_model.py -v`
Expected: 1 passed.

- [ ] **Step 8: Commit**

```bash
cd COLMENA/backend
git add app/models/form_version.py app/models/__init__.py app/models/form.py app/models/form_response.py alembic/versions/20260809_20_create_form_versions.py app/schemas/form_version.py app/schemas/__init__.py tests/test_form_versions_model.py
git commit -m "feat: add FormVersion model, link forms and form_responses"
```

---

### Task 3: Snapshot al publicar + `form_version_id` en respuestas nuevas

**Files:**
- Modify: `COLMENA/backend/app/services/public_form_service.py:200-213` (`publish_form`)
- Modify: `COLMENA/backend/app/services/public_form_service.py:383-424` (`submit_public_response`)
- Modify: `COLMENA/backend/tests/test_public_forms.py` (extender el flujo existente)

**Interfaces:**
- Consumes: `app.models.form_version.FormVersion` (Task 2).
- Produces: `PublicFormService._build_snapshot(form) -> dict`, usado también por Task 4.

- [ ] **Step 1: Añadir el import y el builder de snapshot**

En `app/services/public_form_service.py`, agregar el import junto a los demás modelos (línea 9-16):

```python
from app.models.form_version import FormVersion
```

Agregar un método nuevo en `PublicFormService`, justo antes de `publish_form` (línea 200):

```python
    def _build_snapshot(self, form: Form) -> dict:
        return {
            "sections": [
                {"id": s.id, "title": s.title, "sort_order": s.sort_order}
                for s in sorted(
                    (s for s in form.sections if s.deleted_at is None),
                    key=lambda item: (item.sort_order, item.created_at),
                )
            ],
            "instruments": [
                {
                    "id": i.id,
                    "name": i.name,
                    "acronym": i.acronym,
                    "dimensions": [
                        {"id": d.id, "name": d.name, "code": d.code}
                        for d in sorted(
                            (d for d in i.dimensions if d.deleted_at is None),
                            key=lambda item: (item.sort_order, item.created_at),
                        )
                    ],
                }
                for i in sorted(
                    (i for i in form.instruments if i.deleted_at is None),
                    key=lambda item: (item.sort_order, item.created_at),
                )
            ],
            "questions": [
                {
                    "id": q.id,
                    "code": q.code,
                    "label": q.label,
                    "question_type": q.question_type,
                    "measurement_level": q.measurement_level,
                    "data_type": q.data_type,
                    "min_value": q.min_value,
                    "max_value": q.max_value,
                    "options": [
                        {"id": o.id, "label": o.label, "value": o.value, "score": o.score}
                        for o in sorted(
                            (o for o in q.options if o.deleted_at is None),
                            key=lambda item: (item.sort_order, item.created_at),
                        )
                    ],
                }
                for q in sorted(
                    (q for q in form.questions if q.deleted_at is None),
                    key=lambda item: (item.sort_order, item.created_at),
                )
            ],
        }
```

- [ ] **Step 2: Reescribir `publish_form` para crear/actualizar la versión**

Reemplazar el cuerpo actual de `publish_form` (líneas 200-213):

```python
    def publish_form(self, form_id: str) -> tuple[Form, PublicFormLinkRead]:
        form = self._get_form(form_id)
        if self._active_questions_count(form.id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a form without active questions",
            )
        self._ensure_public_slug(form)

        last_version_number = (
            self.db.scalar(
                select(func.max(FormVersion.version_number)).where(FormVersion.form_id == form.id)
            )
            or 0
        )
        version = FormVersion(
            form_id=form.id,
            version_number=last_version_number + 1,
            status="published",
            snapshot_json=self._build_snapshot(form),
            published_at=datetime.now(timezone.utc),
        )
        self.db.add(version)
        self.db.flush()
        form.current_version_id = version.id

        form.status = "published"
        if form.collect_started_at is None:
            form.collect_started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(form)
        return form, self._build_public_urls(form)
```

- [ ] **Step 3: Asociar `form_version_id` a las respuestas nuevas**

En `submit_public_response` (línea 393-401), agregar `form_version_id=loaded_form.current_version_id` al construir `FormResponse`:

```python
        response = FormResponse(
            project_id=loaded_form.project_id,
            form_id=loaded_form.id,
            form_version_id=loaded_form.current_version_id,
            respondent_code=payload.respondent_code,
            status=response_status,
            submitted_at=datetime.now(timezone.utc),
            source="public_link",
            metadata_json=payload.metadata_json,
        )
```

- [ ] **Step 4: Extender el test existente para verificar la versión**

En `tests/test_public_forms.py`, dentro de `test_public_publish_read_submit_close_reopen_flow`, después de la línea `publish = publish_form(client, form["id"])` (línea 124) agregar:

```python
    from app.core.database import SessionLocal
    from app.models.form import Form as FormModel
    from app.models.form_version import FormVersion as FormVersionModel

    db = SessionLocal()
    try:
        stored_form = db.get(FormModel, form["id"])
        assert stored_form.current_version_id is not None
        version = db.get(FormVersionModel, stored_form.current_version_id)
        assert version.version_number == 1
        assert version.status == "published"
        assert len(version.snapshot_json["questions"]) == 3
    finally:
        db.close()
```

Y tras el bloque de `submitted = client.post(...)` (línea ~135 en adelante, donde se envía la respuesta pública), verificar que la respuesta quedó atada a esa versión:

```python
    db = SessionLocal()
    try:
        stored_response = db.get(FormModel, form["id"])
        from app.models.form_response import FormResponse as FormResponseModel

        response_row = db.scalar(
            select(FormResponseModel).where(FormResponseModel.id == submitted.json()["response_id"])
        )
        assert response_row.form_version_id == stored_form.current_version_id
    finally:
        db.close()
```

(usar el `select` ya importado en el archivo de test si existe, si no agregar `from sqlalchemy import select` al inicio del test file).

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_public_forms.py -v`
Expected: todos los tests existentes siguen pasando, incluida la nueva verificación de versión.

- [ ] **Step 5: Commit**

```bash
cd COLMENA/backend
git add app/services/public_form_service.py tests/test_public_forms.py
git commit -m "feat: snapshot form content into a FormVersion on publish"
```

---

### Task 4: Bloqueo de edición tras publicar + clonado de versión draft

**Files:**
- Modify: `COLMENA/backend/app/services/form_service.py:1-21` (imports)
- Modify: `COLMENA/backend/app/services/form_service.py:192-198,266-276,305-311,352-371,400-406` (`update_form`, `update_instrument`, `update_dimension`, `update_question`, `update_option`)
- Modify: `COLMENA/backend/app/services/form_service.py` (agregar `clone_draft_version`)
- Modify: `COLMENA/backend/app/routers/forms.py` (nuevo endpoint)
- Create: `COLMENA/backend/tests/test_form_versioning_guard.py`

**Interfaces:**
- Consumes: `FormVersion` (Task 2), `PublicFormService._build_snapshot` (Task 3, reutilizado vía import perezoso para evitar ciclo de import).
- Produces: `FormService.clone_draft_version(form_id: str) -> FormVersion`; endpoint `POST /api/v1/forms/{form_id}/versions/draft`.

- [ ] **Step 1: Helper `_has_published_responses` en `FormService`**

Agregar imports en `app/services/form_service.py` (junto a los existentes, línea 1-20):

```python
from app.models.form_response import FormResponse
from app.models.form_version import FormVersion
```

Agregar el método, junto a los demás `_get_*` (después de `_get_project_variable_for_project`, línea 114):

```python
    def _published_version_has_responses(self, form: Form) -> bool:
        if form.current_version_id is None:
            return False
        return (
            self.db.scalar(
                select(func.count())
                .select_from(FormResponse)
                .where(
                    FormResponse.form_version_id == form.current_version_id,
                    FormResponse.deleted_at.is_(None),
                )
            )
            or 0
        ) > 0

    def _ensure_content_editable(self, form: Form) -> None:
        if form.status == "published" and self._published_version_has_responses(form):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Form has a published version with existing responses; "
                    "create a new draft version before editing its content"
                ),
            )
```

- [ ] **Step 2: Llamar `_ensure_content_editable` en cada `update_*` de contenido**

No aplica a `update_form` (metadatos del formulario, no contenido de preguntas) ni a los `soft_delete_*`/`create_*` de nivel superior salvo que muevan preguntas — el spec solo exige proteger ediciones de contenido ya congelado. Modificar únicamente:

- `update_instrument` (línea 266): agregar `self._ensure_content_editable(instrument.form)` como primera línea del método, antes de `update_data = payload.model_dump(...)`.
- `update_dimension` (línea 305): agregar `self._ensure_content_editable(dimension.instrument.form)` como primera línea.
- `update_question` (línea 352): agregar `self._ensure_content_editable(question.form)` como primera línea.
- `update_option` (línea 400): agregar `self._ensure_content_editable(option.question.form)` como primera línea.

Ejemplo concreto para `update_question`:

```python
    def update_question(self, question_id: str, payload: FormQuestionUpdate) -> FormQuestion:
        question = self._get_question(question_id)
        self._ensure_content_editable(question.form)
        update_data = payload.model_dump(exclude_unset=True)
        ...
```

- [ ] **Step 3: Implementar `clone_draft_version`**

Agregar al final de `FormService`:

```python
    def clone_draft_version(self, form_id: str) -> FormVersion:
        """Crea una nueva versión draft con IDs nuevos para el contenido activo,
        permitiendo editar sin tocar la versión publicada que ya tiene respuestas."""
        form = self._get_form(form_id)
        if form.current_version_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Form has no published version to clone from",
            )

        id_map: dict[str, str] = {}

        def _clone(model_cls, old, extra_fields: dict) -> object:
            new_id = str(uuid4())
            id_map[old.id] = new_id
            data = {
                column.name: getattr(old, column.name)
                for column in model_cls.__table__.columns
                if column.name not in {"id", "created_at", "updated_at", "deleted_at"}
            }
            data.update(extra_fields)
            clone = model_cls(id=new_id, **data)
            self.db.add(clone)
            return clone

        for section in form.sections:
            if section.deleted_at is None:
                _clone(FormSection, section, {"form_id": form.id})

        for instrument in form.instruments:
            if instrument.deleted_at is None:
                _clone(FormInstrument, instrument, {"form_id": form.id})
        self.db.flush()

        for instrument in form.instruments:
            if instrument.deleted_at is None:
                for dimension in instrument.dimensions:
                    if dimension.deleted_at is None:
                        _clone(FormDimension, dimension, {"instrument_id": id_map[instrument.id]})
        self.db.flush()

        for question in form.questions:
            if question.deleted_at is None:
                _clone(
                    FormQuestion,
                    question,
                    {
                        "form_id": form.id,
                        "section_id": id_map.get(question.section_id) if question.section_id else None,
                        "instrument_id": id_map.get(question.instrument_id) if question.instrument_id else None,
                        "dimension_id": id_map.get(question.dimension_id) if question.dimension_id else None,
                    },
                )
        self.db.flush()

        for question in form.questions:
            if question.deleted_at is None:
                new_question_id = id_map[question.id]
                for option in question.options:
                    if option.deleted_at is None:
                        _clone(FormQuestionOption, option, {"question_id": new_question_id})

        last_version_number = (
            self.db.scalar(
                select(func.max(FormVersion.version_number)).where(FormVersion.form_id == form.id)
            )
            or 0
        )
        draft = FormVersion(form_id=form.id, version_number=last_version_number + 1, status="draft")
        self.db.add(draft)
        form.status = "draft"
        self.db.commit()
        self.db.refresh(draft)
        return draft
```

Agregar `from uuid import uuid4` a los imports del archivo.

- [ ] **Step 4: Exponer el endpoint**

En `app/routers/forms.py`, agregar (junto a los demás endpoints de `forms/{form_id}`, después del endpoint de `publish`):

```python
@router.post("/api/v1/forms/{form_id}/versions/draft", response_model=FormVersionRead, status_code=201)
def clone_draft_version(form_id: str, service: FormService = Depends(get_form_service)) -> FormVersionRead:
    return FormVersionRead.model_validate(service.clone_draft_version(form_id))
```

Agregar `from app.schemas.form_version import FormVersionRead` a los imports del router.

- [ ] **Step 5: Test del guard y del clonado**

```python
# COLMENA/backend/tests/test_form_versioning_guard.py
from fastapi.testclient import TestClient


def _create_project_form_question(client: TestClient) -> tuple[dict, dict, dict]:
    project = client.post("/api/v1/projects", json={"title": "Proyecto guard"}).json()
    form = client.post(
        f"/api/v1/projects/{project['id']}/forms", json={"title": "Formulario guard"}
    ).json()
    question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "code": "q1",
            "label": "Pregunta 1",
            "question_type": "number",
            "question_role": "item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_required": True,
            "sort_order": 1,
        },
    ).json()
    return project, form, question


def test_editing_question_after_publish_without_responses_is_allowed(client: TestClient):
    _, form, question = _create_project_form_question(client)
    client.post(f"/api/v1/forms/{form['id']}/publish")

    response = client.patch(
        f"/api/v1/form-questions/{question['id']}", json={"label": "Pregunta 1 editada"}
    )
    assert response.status_code == 200


def test_editing_question_after_publish_with_responses_is_blocked(client: TestClient):
    _, form, question = _create_project_form_question(client)
    publish = client.post(f"/api/v1/forms/{form['id']}/publish").json()
    public_slug = publish["public_slug"]

    submit = client.post(
        f"/api/public/forms/{public_slug}/responses",
        json={"respondent_code": None, "answers": [{"question_id": question["id"], "value_number": 5}]},
    )
    assert submit.status_code == 200

    response = client.patch(
        f"/api/v1/form-questions/{question['id']}", json={"label": "Pregunta editada tras respuesta"}
    )
    assert response.status_code == 409

    draft = client.post(f"/api/v1/forms/{form['id']}/versions/draft")
    assert draft.status_code == 201
    assert draft.json()["status"] == "draft"

    response_after_clone = client.get(f"/api/v1/forms/{form['id']}/questions")
    assert response_after_clone.status_code == 200
    cloned_questions = response_after_clone.json()["items"]
    assert len(cloned_questions) == 1
    assert cloned_questions[0]["id"] != question["id"]
    assert cloned_questions[0]["label"] == "Pregunta 1"

    edit_clone = client.patch(
        f"/api/v1/form-questions/{cloned_questions[0]['id']}",
        json={"label": "Pregunta editada en draft"},
    )
    assert edit_clone.status_code == 200
```

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_form_versioning_guard.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
cd COLMENA/backend
git add app/services/form_service.py app/routers/forms.py tests/test_form_versioning_guard.py
git commit -m "feat: block content edits on published forms with responses, add draft version cloning"
```

---

### Task 5: Integrar `audit_service` en los servicios existentes

**Files:**
- Modify: `COLMENA/backend/app/services/project_service.py` (`create_project`, `soft_delete_project`)
- Modify: `COLMENA/backend/app/services/project_variable_service.py` (`create_variable`, `soft_delete_variable`)
- Modify: `COLMENA/backend/app/services/form_service.py` (`create_form`, `soft_delete_form`)
- Modify: `COLMENA/backend/app/services/public_form_service.py` (`publish_form`, `close_form`, `reopen_form`)
- Modify: `COLMENA/backend/app/services/scoring_config_service.py` (`create_scoring_config`, `delete_scoring_config`)
- Modify: `COLMENA/backend/app/routers/deps.py` (helper para pasar `user_id` a los servicios que lo necesiten, si el servicio no lo recibe ya)
- Create: `COLMENA/backend/tests/test_audit_integration.py`

**Interfaces:**
- Consumes: `app.services.audit_service.record` (Task 1).

- [ ] **Step 1: `ProjectService` — ya recibe `user_id`, usarlo directamente**

`create_project(payload, user_id)` y `soft_delete_project(project_id, user_id)` ya reciben `user_id` como parámetro (confirmado en `app/services/project_service.py:53,130`). En `create_project`, después de `self.db.add(project)` y antes/junto al commit existente, insertar el registro de auditoría **antes** del `commit()` final (usa la misma transacción, `audit_service.record` hace `flush()` no `commit()`):

Localizar el bloque de `create_project` (líneas 53-65 aprox.) y, justo antes de la línea final `self.db.commit()` de ese método, agregar:

```python
        self.db.flush()
        audit_service.record(
            self.db,
            user_id=user_id,
            project_id=project.id,
            entity_type="project",
            entity_id=project.id,
            action="create",
            new_data={"title": project.title},
        )
        self.db.commit()
```

(ajustar si el método ya tenía otro flush/commit intermedio — el punto clave es: registrar el audit log con el `project.id` ya asignado, y comitear una sola vez al final).

En `soft_delete_project` (línea 130-137), antes del `self.db.commit()` existente:

```python
        audit_service.record(
            self.db,
            user_id=user_id,
            project_id=project.id,
            entity_type="project",
            entity_id=project.id,
            action="delete",
        )
```

Agregar `from app.services import audit_service` a los imports del archivo.

- [ ] **Step 2: `ProjectVariableService` — no recibe `user_id` hoy, agregarlo**

`create_variable(project_id, payload)` y `soft_delete_variable(variable_id)` no reciben `user_id`. Cambiar sus firmas para aceptarlo como parámetro opcional con default `None` (evita romper otros call sites que no lo pasen; los routers nuevos sí lo pasarán):

```python
    def create_variable(self, project_id: str, payload: ProjectVariableCreate, user_id: str | None = None) -> ProjectVariable:
        project = self._get_project(project_id)
        variable = ProjectVariable(project_id=project_id, **payload.model_dump())
        self.db.add(variable)
        self.db.flush()
        audit_service.record(
            self.db,
            user_id=user_id,
            project_id=project.id,
            entity_type="project_variable",
            entity_id=variable.id,
            action="create",
            new_data={"name": variable.name, "code": variable.code},
        )
        self.db.commit()
        self.db.refresh(variable)
        return variable

    def soft_delete_variable(self, variable_id: str, user_id: str | None = None) -> dict[str, str]:
        variable = self._get_variable(variable_id)
        variable.deleted_at = datetime.now(timezone.utc)
        audit_service.record(
            self.db,
            user_id=user_id,
            project_id=variable.project_id,
            entity_type="project_variable",
            entity_id=variable.id,
            action="delete",
        )
        self.db.commit()
        return {"status": "deleted", "id": variable.id}
```

Agregar `from app.services import audit_service` a los imports. En `app/routers/project_variables.py`, actualizar las llamadas a estos dos métodos para pasar `user_id=current_user.id` (usando el mismo patrón de `Depends(get_current_user)` que ya usa `app/routers/projects.py`).

- [ ] **Step 3: `FormService.create_form` / `soft_delete_form`**

Mismo patrón: agregar parámetro `user_id: str | None = None` a ambos métodos, registrar `entity_type="form"`, y actualizar `app/routers/forms.py` para pasar `user_id=current_user.id` en esos dos endpoints (`POST /projects/{project_id}/forms` y `DELETE /forms/{form_id}`).

```python
    def create_form(self, project_id: str, payload: FormCreate, user_id: str | None = None) -> Form:
        project = self._get_project(project_id)
        form = Form(project_id=project_id, **payload.model_dump())
        self.db.add(form)
        self.db.flush()
        audit_service.record(
            self.db,
            user_id=user_id,
            project_id=project.id,
            entity_type="form",
            entity_id=form.id,
            action="create",
            new_data={"title": form.title},
        )
        self.db.commit()
        self.db.refresh(form)
        return form

    def soft_delete_form(self, form_id: str, user_id: str | None = None) -> dict[str, str]:
        form = self._get_form(form_id)
        form.deleted_at = datetime.now(timezone.utc)
        audit_service.record(
            self.db,
            user_id=user_id,
            project_id=form.project_id,
            entity_type="form",
            entity_id=form.id,
            action="delete",
        )
        self.db.commit()
        return {"status": "deleted", "id": form.id}
```

Agregar `from app.services import audit_service` a `app/services/form_service.py`.

- [ ] **Step 4: `PublicFormService.publish_form` / `close_form` / `reopen_form`**

Mismo patrón: parámetro `user_id: str | None = None`, `entity_type="form"`, `action="publish"|"close"|"reopen"`. Ejemplo para `publish_form` (ya modificado en Task 3), agregar justo antes del `self.db.commit()` final:

```python
        audit_service.record(
            self.db,
            user_id=user_id,
            project_id=form.project_id,
            entity_type="form",
            entity_id=form.id,
            action="publish",
            new_data={"version_number": version.version_number},
        )
```

Y actualizar la firma de los tres métodos y las llamadas en `app/routers/forms.py` / `app/routers/public_forms.py` para pasar `user_id=current_user.id` (los endpoints de publish/close/reopen viven bajo autenticación de investigador, no en el router público de respuestas).

- [ ] **Step 5: `ScoringConfigService.create_scoring_config` / `delete_scoring_config`**

Mismo patrón: parámetro `user_id`, `entity_type="scoring_config"`.

- [ ] **Step 6: Test de integración end-to-end**

```python
# COLMENA/backend/tests/test_audit_integration.py
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.audit_log import AuditLog


def test_creating_and_deleting_a_project_writes_audit_logs(client: TestClient):
    project = client.post("/api/v1/projects", json={"title": "Proyecto con auditoria"}).json()
    client.delete(f"/api/v1/projects/{project['id']}")

    db = SessionLocal()
    try:
        entries = list(
            db.scalars(
                select(AuditLog)
                .where(AuditLog.entity_type == "project", AuditLog.entity_id == project["id"])
                .order_by(AuditLog.created_at.asc())
            ).all()
        )
        assert [entry.action for entry in entries] == ["create", "delete"]
    finally:
        db.close()


def test_publishing_a_form_writes_a_publish_audit_log(client: TestClient):
    project = client.post("/api/v1/projects", json={"title": "Proyecto publicacion"}).json()
    form = client.post(
        f"/api/v1/projects/{project['id']}/forms", json={"title": "Formulario auditado"}
    ).json()
    client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "code": "q1",
            "label": "Pregunta",
            "question_type": "number",
            "question_role": "item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "sort_order": 1,
        },
    )
    client.post(f"/api/v1/forms/{form['id']}/publish")

    db = SessionLocal()
    try:
        entry = db.scalar(
            select(AuditLog).where(
                AuditLog.entity_type == "form", AuditLog.entity_id == form["id"], AuditLog.action == "publish"
            )
        )
        assert entry is not None
    finally:
        db.close()
```

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_audit_integration.py -v`
Expected: 2 passed.

- [ ] **Step 7: Correr toda la suite para detectar regresiones por las nuevas firmas**

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/ -x -q`
Expected: 0 failed (los parámetros `user_id` nuevos tienen default `None`, así que ningún call site existente debería romperse).

- [ ] **Step 8: Commit**

```bash
cd COLMENA/backend
git add app/services/project_service.py app/services/project_variable_service.py app/services/form_service.py app/services/public_form_service.py app/services/scoring_config_service.py app/routers/project_variables.py app/routers/forms.py app/routers/public_forms.py tests/test_audit_integration.py
git commit -m "feat: wire audit_service into project, form, and scoring config mutations"
```

---

### Task 6: Constraints de unicidad, `ondelete` estandarizado, `Form.metadata_json` a `JSON`

**Files:**
- Modify: `COLMENA/backend/app/models/project_variable.py:1-16` (`__table_args__`)
- Modify: `COLMENA/backend/app/models/form_question.py:1-41` (`__table_args__`)
- Modify: `COLMENA/backend/app/models/form_dimension.py:1-16` (`__table_args__`)
- Modify: `COLMENA/backend/app/models/form.py:26` (`metadata_json` a `JSON`)
- Create: `COLMENA/backend/alembic/versions/20260809_21_add_code_uniqueness_and_metadata_json.py`
- Create: `COLMENA/backend/tests/test_schema_consistency.py`

**Interfaces:** ninguna nueva consumida ni producida para otras tareas — cambios de esquema puros.

- [ ] **Step 1: Unique constraints condicionales en los modelos**

SQLite/SQLAlchemy no soporta `UniqueConstraint` con condición `WHERE` directamente en `__table_args__` de forma portable entre backends, pero como este proyecto es SQLite-only, se usa un índice único parcial (`sqlite_where`). En `app/models/project_variable.py`, agregar `__table_args__` a la clase:

```python
from sqlalchemy import Boolean, ForeignKey, Index, String, Text
...
class ProjectVariable(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "project_variables"
    __table_args__ = (
        Index(
            "uq_project_variables_project_code",
            "project_id",
            "code",
            unique=True,
            sqlite_where="code IS NOT NULL AND deleted_at IS NULL",
        ),
    )
```

En `app/models/form_question.py`:

```python
    __table_args__ = (
        Index(
            "uq_form_questions_form_code",
            "form_id",
            "code",
            unique=True,
            sqlite_where="code IS NOT NULL AND deleted_at IS NULL",
        ),
    )
```

En `app/models/form_dimension.py`:

```python
    __table_args__ = (
        Index(
            "uq_form_dimensions_instrument_code",
            "instrument_id",
            "code",
            unique=True,
            sqlite_where="code IS NOT NULL AND deleted_at IS NULL",
        ),
    )
```

(el filtro incluye `deleted_at IS NULL` para que un código de un ítem soft-deleted pueda reutilizarse en uno nuevo — consistente con el resto del sistema, que trata `deleted_at` como "ya no cuenta").

- [ ] **Step 2: `Form.metadata_json` a `JSON`**

En `app/models/form.py`, cambiar:

```python
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
```

por:

```python
    metadata_json: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)
```

Agregar `JSON` al import de `sqlalchemy` en ese archivo (`from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text`). El schema Pydantic (`app/schemas/form.py`) sigue tipando `metadata_json: str | None` sin cambios — un `str` sigue siendo válido para una columna `JSON` (se guarda como valor JSON string), así que el contrato con el frontend no cambia.

- [ ] **Step 3: Migración**

```python
# COLMENA/backend/alembic/versions/20260809_21_add_code_uniqueness_and_metadata_json.py
"""add conditional unique indexes on code columns, form.metadata_json to JSON

Revision ID: 20260809_21
Revises: 20260809_20
Create Date: 2026-08-09 00:00:02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260809_21"
down_revision: Union[str, Sequence[str], None] = "20260809_20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_project_variables_project_code",
        "project_variables",
        ["project_id", "code"],
        unique=True,
        sqlite_where=sa.text("code IS NOT NULL AND deleted_at IS NULL"),
    )
    op.create_index(
        "uq_form_questions_form_code",
        "form_questions",
        ["form_id", "code"],
        unique=True,
        sqlite_where=sa.text("code IS NOT NULL AND deleted_at IS NULL"),
    )
    op.create_index(
        "uq_form_dimensions_instrument_code",
        "form_dimensions",
        ["instrument_id", "code"],
        unique=True,
        sqlite_where=sa.text("code IS NOT NULL AND deleted_at IS NULL"),
    )

    with op.batch_alter_table("forms", schema=None) as batch:
        batch.alter_column("metadata_json", existing_type=sa.Text(), type_=sa.JSON())


def downgrade() -> None:
    with op.batch_alter_table("forms", schema=None) as batch:
        batch.alter_column("metadata_json", existing_type=sa.JSON(), type_=sa.Text())

    op.drop_index("uq_form_dimensions_instrument_code", "form_dimensions")
    op.drop_index("uq_form_questions_form_code", "form_questions")
    op.drop_index("uq_project_variables_project_code", "project_variables")
```

**Nota sobre datos existentes:** si la base de datos real ya tiene duplicados de `code` (nulos aparte) para el mismo `project_id`/`form_id`/`instrument_id`, `create_index` fallará al aplicar la migración. Antes de correr `alembic upgrade head` en la base de datos de desarrollo, ejecutar una consulta de verificación:

```sql
SELECT project_id, code, COUNT(*) FROM project_variables WHERE code IS NOT NULL AND deleted_at IS NULL GROUP BY project_id, code HAVING COUNT(*) > 1;
```

(repetir para `form_questions` con `form_id` y `form_dimensions` con `instrument_id`). Si hay filas, resolver manualmente (renombrar códigos duplicados) antes de aplicar la migración.

- [ ] **Step 4: Test de que la constraint se respeta y que el metadata_json sigue funcionando como string**

```python
# COLMENA/backend/tests/test_schema_consistency.py
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.project import Project
from app.models.project_variable import ProjectVariable
from app.models.user import User


def test_duplicate_variable_code_in_same_project_is_rejected(client: TestClient):
    db = SessionLocal()
    try:
        user = db.scalar(select(User).limit(1))
        project = Project(user_id=user.id, title="Proyecto codigos")
        db.add(project)
        db.flush()
        db.add(ProjectVariable(project_id=project.id, name="Ansiedad", code="ANX"))
        db.commit()

        db.add(ProjectVariable(project_id=project.id, name="Ansiedad duplicada", code="ANX"))
        try:
            db.commit()
            assert False, "expected IntegrityError for duplicate code"
        except IntegrityError:
            db.rollback()
    finally:
        db.close()


def test_form_metadata_json_still_roundtrips_as_string(client: TestClient):
    project = client.post("/api/v1/projects", json={"title": "Proyecto metadata"}).json()
    form = client.post(
        f"/api/v1/projects/{project['id']}/forms",
        json={"title": "Formulario metadata", "metadata_json": '{"theme": "dark"}'},
    ).json()
    assert form["metadata_json"] == '{"theme": "dark"}'

    fetched = client.get(f"/api/v1/forms/{form['id']}").json()
    assert fetched["metadata_json"] == '{"theme": "dark"}'
```

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_schema_consistency.py -v`
Expected: 2 passed.

- [ ] **Step 5: Correr toda la suite**

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/ -x -q`
Expected: 0 failed.

- [ ] **Step 6: Commit**

```bash
cd COLMENA/backend
git add app/models/project_variable.py app/models/form_question.py app/models/form_dimension.py app/models/form.py alembic/versions/20260809_21_add_code_uniqueness_and_metadata_json.py tests/test_schema_consistency.py
git commit -m "fix: enforce unique codes per scope, store Form.metadata_json as JSON"
```

---

### Task 7: Rechazar bandas de puntaje solapadas (antes solo advertía)

**Files:**
- Modify: `COLMENA/backend/app/services/scoring_config_service.py:174-220` (`create_scoring_config`, `add_score_band`, `update_score_band`)
- Modify: `COLMENA/backend/tests/test_advanced_scoring.py:271-279` (actualizar expectativa)
- Create: `COLMENA/backend/tests/test_scoring_band_overlap.py`

**Interfaces:**
- Consumes: `app.scoring.band_engine.validate_bands_no_overlap` (ya existe).

- [ ] **Step 1: Helper de validación estricta**

En `app/services/scoring_config_service.py`, agregar un método privado:

```python
    def _reject_if_overlaps(self, config_id: str, candidate_bands: list) -> None:
        existing = [band for band in self._get_scoring_config(config_id).score_bands if band.deleted_at is None]
        combined = existing + candidate_bands
        if validate_bands_no_overlap(combined):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Score band range overlaps with an existing active band for this scoring config",
            )
```

`validate_bands_no_overlap` ya está importado (línea 22). Este helper compara un objeto "candidato" contra las bandas activas existentes usando duck-typing (`min_value`/`max_value`/`severity_order`) — para `add_score_band` el candidato es el objeto `ScoreBand` recién construido (aún no comiteado, pero con atributos poblados), y para `update_score_band` es la banda existente con los campos ya actualizados en memoria.

- [ ] **Step 2: Aplicar en `add_score_band`**

Reemplazar (línea 210-216):

```python
    def add_score_band(self, config_id: str, payload: ScoreBandCreate) -> ScoreBand:
        config = self._get_scoring_config(config_id)
        band = ScoreBand(scoring_config_id=config.id, **payload.model_dump())
        self._reject_if_overlaps(config_id, [band])
        self.db.add(band)
        self.db.commit()
        self.db.refresh(band)
        return band
```

- [ ] **Step 3: Aplicar en `update_score_band`**

Reemplazar (línea 222-231):

```python
    def update_score_band(self, band_id: str, payload: ScoreBandUpdate) -> ScoreBand:
        band = self._get_band(band_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(band, field, value)
        if band.max_value < band.min_value:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="max_value must be greater than or equal to min_value")
        other_bands = [b for b in self._get_scoring_config(band.scoring_config_id).score_bands if b.deleted_at is None and b.id != band.id]
        if validate_bands_no_overlap(other_bands + [band]):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Score band range overlaps with an existing active band for this scoring config",
            )
        self.db.commit()
        self.db.refresh(band)
        return band
```

- [ ] **Step 4: Aplicar en `create_scoring_config` (bandas creadas junto con el config)**

En `create_scoring_config` (línea 157-176), tras `self.db.flush()` y antes de agregar cada `ScoreBand` del payload, validar el conjunto completo de bandas del payload entre sí (no hay bandas previas todavía porque el config es nuevo):

```python
        config = ScoringConfig(project_id=form.project_id, form_id=form.id, **data)
        self.db.add(config)
        self.db.flush()
        new_bands = [ScoreBand(scoring_config_id=config.id, **band_payload.model_dump()) for band_payload in payload.bands]
        if validate_bands_no_overlap(new_bands):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Score band ranges overlap with each other",
            )
        for band in new_bands:
            self.db.add(band)
        self.db.commit()
        return self._get_scoring_config(config.id)
```

- [ ] **Step 5: Actualizar el test existente que esperaba el warning**

En `tests/test_advanced_scoring.py`, líneas 271-279, reemplazar:

```python
    overlap_band = client.post(
        f"/api/v1/scoring/configs/{config['id']}/bands",
        json={"label": "Superpuesto", "code": "overlap", "min_value": 2.0, "max_value": 4.0, "interpretation": "Rango superpuesto"},
    )
    assert overlap_band.status_code == 201
    config_list = client.get(f"/api/v1/forms/{form_id}/scoring/configs")
    assert config_list.status_code == 200
    assert "overlapping_bands" in config_list.json()["warnings"]
```

por:

```python
    overlap_band = client.post(
        f"/api/v1/scoring/configs/{config['id']}/bands",
        json={"label": "Superpuesto", "code": "overlap", "min_value": 2.0, "max_value": 4.0, "interpretation": "Rango superpuesto"},
    )
    assert overlap_band.status_code == 422
    assert "overlap" in overlap_band.json()["detail"]
```

- [ ] **Step 6: Test dedicado**

```python
# COLMENA/backend/tests/test_scoring_band_overlap.py
from fastapi.testclient import TestClient


def _create_config(client: TestClient) -> tuple[str, str]:
    project = client.post("/api/v1/projects", json={"title": "Proyecto bandas"}).json()
    form = client.post(
        f"/api/v1/projects/{project['id']}/forms", json={"title": "Formulario bandas"}
    ).json()
    config = client.post(
        f"/api/v1/forms/{form['id']}/scoring/configs",
        json={"name": "Config bandas", "scoring_level": "custom", "bands": []},
    ).json()
    return form["id"], config["id"]


def test_add_score_band_rejects_overlap(client: TestClient):
    form_id, config_id = _create_config(client)
    first = client.post(
        f"/api/v1/scoring/configs/{config_id}/bands",
        json={"label": "Bajo", "min_value": 0, "max_value": 10},
    )
    assert first.status_code == 201

    overlapping = client.post(
        f"/api/v1/scoring/configs/{config_id}/bands",
        json={"label": "Medio", "min_value": 8, "max_value": 20},
    )
    assert overlapping.status_code == 422

    non_overlapping = client.post(
        f"/api/v1/scoring/configs/{config_id}/bands",
        json={"label": "Alto", "min_value": 11, "max_value": 20},
    )
    assert non_overlapping.status_code == 201


def test_update_score_band_rejects_overlap(client: TestClient):
    form_id, config_id = _create_config(client)
    low = client.post(
        f"/api/v1/scoring/configs/{config_id}/bands",
        json={"label": "Bajo", "min_value": 0, "max_value": 10},
    ).json()
    client.post(
        f"/api/v1/scoring/configs/{config_id}/bands",
        json={"label": "Alto", "min_value": 11, "max_value": 20},
    )

    response = client.patch(f"/api/v1/scoring/bands/{low['id']}", json={"max_value": 15})
    assert response.status_code == 422
```

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_scoring_band_overlap.py tests/test_advanced_scoring.py -v`
Expected: todos pasan.

- [ ] **Step 7: Commit**

```bash
cd COLMENA/backend
git add app/services/scoring_config_service.py tests/test_advanced_scoring.py tests/test_scoring_band_overlap.py
git commit -m "fix: reject overlapping score bands instead of only warning"
```

---

### Task 8: Sincronizar `measurement_level`/`data_type` entre `FormQuestion` y su `ProjectVariable`

**Files:**
- Modify: `COLMENA/backend/app/services/form_service.py:319-334` (`create_question`)
- Modify: `COLMENA/backend/app/services/form_service.py:352-371` (`update_question`)
- Create: `COLMENA/backend/tests/test_question_variable_sync.py`

**Interfaces:** ninguna nueva.

- [ ] **Step 1: Helper de sincronización**

Agregar a `FormService`, junto a `_validate_question_links` (después de la línea 172):

```python
    def _sync_measurement_fields_from_variable(self, data: dict, variable_id: str | None) -> dict:
        if variable_id is None:
            return data
        variable = self.db.get(ProjectVariable, variable_id)
        if variable is not None:
            data["measurement_level"] = variable.measurement_level
            data["data_type"] = variable.data_type
        return data
```

- [ ] **Step 2: Aplicar en `create_question`**

Modificar (línea 319-334):

```python
    def create_question(self, form_id: str, payload: FormQuestionCreate) -> FormQuestion:
        form = self._get_form(form_id)
        data = payload.model_dump()
        resolved_links = self._validate_question_links(
            form,
            section_id=data.get("section_id"),
            instrument_id=data.get("instrument_id"),
            dimension_id=data.get("dimension_id"),
            project_variable_id=data.get("project_variable_id"),
        )
        data.update(resolved_links)
        data = self._sync_measurement_fields_from_variable(data, resolved_links["project_variable_id"])
        question = FormQuestion(form_id=form_id, **data)
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question
```

- [ ] **Step 3: Aplicar en `update_question`**

Modificar (línea 352-371): tras `update_data.update(resolved_links)`, agregar:

```python
        update_data = self._sync_measurement_fields_from_variable(update_data, resolved_links["project_variable_id"])
```

quedando:

```python
    def update_question(self, question_id: str, payload: FormQuestionUpdate) -> FormQuestion:
        question = self._get_question(question_id)
        self._ensure_content_editable(question.form)
        update_data = payload.model_dump(exclude_unset=True)

        current_links = {
            "section_id": question.section_id,
            "instrument_id": question.instrument_id,
            "dimension_id": question.dimension_id,
            "project_variable_id": question.project_variable_id,
        }
        current_links.update({key: update_data.get(key, current_links[key]) for key in current_links})
        resolved_links = self._validate_question_links(question.form, **current_links)
        update_data.update(resolved_links)
        update_data = self._sync_measurement_fields_from_variable(update_data, resolved_links["project_variable_id"])

        for field, value in update_data.items():
            setattr(question, field, value)

        self.db.commit()
        self.db.refresh(question)
        return question
```

(Nota: `self._ensure_content_editable(question.form)` ya viene de Task 4 — si Task 4 no se ha implementado todavía cuando se ejecuta esta tarea, omitir esa línea; ambas tareas son independientes entre sí en el resto del método.)

- [ ] **Step 4: Test**

```python
# COLMENA/backend/tests/test_question_variable_sync.py
from fastapi.testclient import TestClient


def test_question_inherits_measurement_fields_from_linked_variable(client: TestClient):
    project = client.post("/api/v1/projects", json={"title": "Proyecto sync"}).json()
    variable = client.post(
        f"/api/v1/projects/{project['id']}/variables",
        json={"name": "Ansiedad", "code": "ANX", "measurement_level": "interval", "data_type": "numeric"},
    ).json()
    form = client.post(
        f"/api/v1/projects/{project['id']}/forms", json={"title": "Formulario sync"}
    ).json()

    question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "code": "q1",
            "label": "Pregunta enlazada",
            "question_type": "number",
            "question_role": "item",
            "measurement_level": "nominal",
            "data_type": "categorical",
            "project_variable_id": variable["id"],
            "sort_order": 1,
        },
    ).json()

    assert question["measurement_level"] == "interval"
    assert question["data_type"] == "numeric"

    client.patch(
        f"/api/v1/projects/{project['id']}/variables/{variable['id']}",
        json={"measurement_level": "ordinal", "data_type": "numeric"},
    )
    updated = client.patch(
        f"/api/v1/form-questions/{question['id']}", json={"label": "Pregunta enlazada editada"}
    ).json()
    assert updated["measurement_level"] == "ordinal"
```

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_question_variable_sync.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
cd COLMENA/backend
git add app/services/form_service.py tests/test_question_variable_sync.py
git commit -m "fix: sync FormQuestion measurement_level/data_type from its linked ProjectVariable"
```

---

### Task 9: Excluir respuestas soft-deleted de los reportes agregados

**Files:**
- Create: `COLMENA/backend/app/utils/query_filters.py`
- Modify: `COLMENA/backend/app/services/advanced_scoring_service.py` (4 sitios: `summarize_bands_distribution`, `_summarize_control_flags`, `get_form_score_results`, `resolve_variable_baremos`)
- Modify: `COLMENA/backend/app/services/apa_table_service.py:580`
- Modify: `COLMENA/backend/app/services/word_report_service.py:187-190`
- Create: `COLMENA/backend/tests/test_soft_deleted_responses_excluded.py`

**Interfaces:**
- Produces: `app.utils.query_filters.active_scores_for_form(form_id: str) -> Select`, `active_control_flags_for_form(form_id: str) -> Select` — helpers reutilizables.

- [ ] **Step 1: Crear los helpers**

```python
# COLMENA/backend/app/utils/query_filters.py
from __future__ import annotations

from sqlalchemy import Select, select

from app.models.form_response import FormResponse
from app.models.response_control_flag import ResponseControlFlag
from app.models.response_score import ResponseScore


def active_scores_for_form(form_id: str) -> Select:
    return (
        select(ResponseScore)
        .join(FormResponse, FormResponse.id == ResponseScore.response_id)
        .where(ResponseScore.form_id == form_id, FormResponse.deleted_at.is_(None))
    )


def active_control_flags_for_form(form_id: str) -> Select:
    return (
        select(ResponseControlFlag)
        .join(FormResponse, FormResponse.id == ResponseControlFlag.response_id)
        .where(ResponseControlFlag.form_id == form_id, FormResponse.deleted_at.is_(None))
    )
```

- [ ] **Step 2: Reemplazar los 4 sitios en `advanced_scoring_service.py`**

Agregar `from app.utils.query_filters import active_control_flags_for_form, active_scores_for_form` a los imports.

- `summarize_bands_distribution`: reemplazar `select(ResponseScore).where(ResponseScore.form_id == form_id)` por `active_scores_for_form(form_id)`.
- `_summarize_control_flags`: reemplazar `select(ResponseControlFlag).where(ResponseControlFlag.form_id == form_id)` por `active_control_flags_for_form(form_id)`.
- `get_form_score_results`: reemplazar `select(ResponseScore).where(ResponseScore.form_id == form.id)` por `active_scores_for_form(form.id)`.
- `resolve_variable_baremos`: reemplazar **ambas** ocurrencias de `select(ResponseScore).where(ResponseScore.form_id == form.id)` por `active_scores_for_form(form.id)`.

En cada caso el resto de la línea (`self.db.scalars(...).all()`) queda igual, solo cambia el `select(...)` interno.

- [ ] **Step 3: Reemplazar el sitio en `apa_table_service.py`**

Línea 580: reemplazar

```python
        scores = list(self.db.scalars(select(ResponseScore).where(ResponseScore.form_id == form_id)).all())
```

por

```python
        scores = list(self.db.scalars(active_scores_for_form(form_id)).all())
```

Agregar `from app.utils.query_filters import active_scores_for_form` a los imports; se puede quitar `from app.models.response_score import ResponseScore` si ya no se usa directamente en el archivo (verificar con `grep -n "ResponseScore" app/services/apa_table_service.py` antes de quitarlo).

- [ ] **Step 4: Corregir `word_report_service.py`**

Línea 187-190, este caso consulta `FormResponse` directamente (no `ResponseScore`), así que solo falta el filtro de `deleted_at` sin necesidad de join:

```python
    def _response_status_counts(self, form_id: str) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for response in self.db.scalars(
            select(FormResponse).where(FormResponse.form_id == form_id, FormResponse.deleted_at.is_(None))
        ).all():
            counts[response.status] += 1
        return counts
```

- [ ] **Step 5: Test de regresión**

```python
# COLMENA/backend/tests/test_soft_deleted_responses_excluded.py
from fastapi.testclient import TestClient


def test_soft_deleted_response_excluded_from_band_distribution(client: TestClient):
    project = client.post("/api/v1/projects", json={"title": "Proyecto exclusion"}).json()
    form = client.post(
        f"/api/v1/projects/{project['id']}/forms", json={"title": "Formulario exclusion"}
    ).json()
    question = client.post(
        f"/api/v1/forms/{form['id']}/questions",
        json={
            "code": "q1",
            "label": "Pregunta",
            "question_type": "number",
            "question_role": "item",
            "measurement_level": "ratio",
            "data_type": "numeric",
            "is_scored": True,
            "sort_order": 1,
        },
    ).json()
    config = client.post(
        f"/api/v1/forms/{form['id']}/scoring/configs",
        json={"name": "Total", "scoring_level": "custom", "score_min": 0, "score_max": 10, "bands": []},
    ).json()
    client.post(
        f"/api/v1/scoring/configs/{config['id']}/bands",
        json={"label": "Bajo", "min_value": 0, "max_value": 10},
    )

    response = client.post(
        f"/api/v1/forms/{form['id']}/responses",
        json={"answers": [{"question_id": question["id"], "value_number": 5}]},
    ).json()
    client.post(f"/api/v1/forms/{form['id']}/scoring/run", json={})

    before = client.get(f"/api/v1/forms/{form['id']}/scoring/results").json()
    assert before["scored_responses"] == 1

    client.delete(f"/api/v1/form-responses/{response['id']}")

    after = client.get(f"/api/v1/forms/{form['id']}/scoring/results").json()
    assert after["scored_responses"] == 0
```

Ajustar los nombres exactos de endpoint de `scoring/run` y `delete response` si difieren (verificar contra `app/routers/scoring.py` y `app/routers/responses.py` antes de fijar el test — el objetivo es: crear respuesta, correr scoring, confirmar que cuenta, borrar (soft-delete) la respuesta, confirmar que ya no cuenta).

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_soft_deleted_responses_excluded.py -v`
Expected: 1 passed.

- [ ] **Step 6: Correr toda la suite**

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/ -x -q`
Expected: 0 failed.

- [ ] **Step 7: Commit**

```bash
cd COLMENA/backend
git add app/utils/query_filters.py app/services/advanced_scoring_service.py app/services/apa_table_service.py app/services/word_report_service.py tests/test_soft_deleted_responses_excluded.py
git commit -m "fix: exclude soft-deleted form responses from aggregated report queries"
```

---

### Task 10: Soft-delete real para `BaremoTableState`, `ChartEditorState`, `ChartPalette`

**Files:**
- Modify: `COLMENA/backend/app/models/baremo_table_state.py`, `app/models/chart_editor_state.py`, `app/models/chart_palette.py` (agregar `SoftDeleteMixin`)
- Modify: `COLMENA/backend/app/services/baremo_table_state_service.py`, `app/services/chart_editor_state_service.py`, `app/services/chart_palette_service.py` (`upsert` revive, `delete` soft-delete, listados filtran)
- Create: `COLMENA/backend/alembic/versions/20260809_22_add_soft_delete_to_ui_state_tables.py`
- Create: `COLMENA/backend/tests/test_ui_state_soft_delete.py`

**Interfaces:** ninguna nueva.

- [ ] **Step 1: Agregar `SoftDeleteMixin` a los 3 modelos**

En cada uno de los 3 archivos, cambiar la firma de clase y el import, por ejemplo en `app/models/baremo_table_state.py`:

```python
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class BaremoTableState(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
```

Repetir el mismo cambio de import/herencia en `chart_editor_state.py` y `chart_palette.py`.

- [ ] **Step 2: `BaremoTableStateService` — revivir en `upsert`, soft-delete en `delete`, filtrar en `list_for_form`**

En `_get_record` no cambiar nada (se usa tanto para upsert como para lookups puntuales, y el upsert necesita encontrar incluso registros soft-deleted para revivirlos). Modificar `upsert` (línea 49-70):

```python
    def upsert(self, form_id: str, table_key: str, payload: BaremoTableStateSave) -> BaremoTableStateRead:
        form = self._get_form(form_id)
        record = self._get_record(form_id, table_key)
        rows_json = [row.model_dump() for row in payload.rows]

        if record is None:
            record = BaremoTableState(
                form_id=form_id,
                project_id=form.project_id,
                user_id=form.project.user_id if form.project else None,
                table_key=table_key,
                group_kind=payload.group_kind,
                title=payload.title,
                rows_json=rows_json,
            )
            self.db.add(record)
        else:
            record.group_kind = payload.group_kind
            record.title = payload.title
            record.rows_json = rows_json
            record.deleted_at = None

        self.db.commit()
        self.db.refresh(record)
        return self._to_read(record)
```

Modificar `list_for_form` para excluir soft-deleted (agregar `BaremoTableState.deleted_at.is_(None)` al `.where()` existente):

```python
    def list_for_form(self, form_id: str) -> BaremoTableStateListRead:
        self._get_form(form_id)
        records = list(
            self.db.scalars(
                select(BaremoTableState)
                .where(BaremoTableState.form_id == form_id, BaremoTableState.deleted_at.is_(None))
                .order_by(BaremoTableState.created_at.asc())
            ).all()
        )
        items = [self._to_read(r) for r in records]
        return BaremoTableStateListRead(form_id=form_id, total=len(items), items=items)
```

Modificar `delete` (reemplazar `self.db.delete(record)` por soft-delete):

```python
    def delete(self, form_id: str, table_key: str) -> BaremoTableStateDeleteResponse:
        self._get_form(form_id)
        record = self._get_record(form_id, table_key)
        if record is None or record.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baremo table state not found")
        record.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return BaremoTableStateDeleteResponse(status="deleted", table_key=table_key)
```

Agregar `from datetime import datetime, timezone` a los imports si no está ya presente.

- [ ] **Step 3: Repetir el mismo patrón en `ChartEditorStateService`**

Mismo cambio de tres partes (`upsert` pone `record.deleted_at = None` en la rama de update; `list_for_form` agrega `ChartEditorState.deleted_at.is_(None)`; `delete` hace soft-delete en vez de `self.db.delete(record)`).

- [ ] **Step 4: Repetir el mismo patrón en `ChartPaletteService`**

`ChartPaletteService` no tiene `list_for_form` (solo `get`/`upsert`/`delete`), así que ajustar `_get_record` con una variante de solo-lectura, o simplemente filtrar en `get`:

```python
    def get(self, form_id: str, chart_key: str) -> ChartPaletteRead:
        self._get_form(form_id)
        record = self._get_record(form_id, chart_key)
        if record is None or record.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart palette not found")
        return self._to_read(record)

    def delete(self, form_id: str, chart_key: str) -> ChartPaletteDeleteResponse:
        self._get_form(form_id)
        record = self._get_record(form_id, chart_key)
        if record is None or record.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chart palette not found")
        record.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        return ChartPaletteDeleteResponse(status="deleted", chart_key=chart_key)
```

Y en `upsert`, en la rama `else` (registro existente), agregar `record.deleted_at = None`.

- [ ] **Step 5: Migración**

```python
# COLMENA/backend/alembic/versions/20260809_22_add_soft_delete_to_ui_state_tables.py
"""add deleted_at to baremo_table_states, chart_editor_states, chart_palettes

Revision ID: 20260809_22
Revises: 20260809_21
Create Date: 2026-08-09 00:00:03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260809_22"
down_revision: Union[str, Sequence[str], None] = "20260809_21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = ["baremo_table_states", "chart_editor_states", "chart_palettes"]


def upgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table, schema=None) as batch:
            batch.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        op.create_index(f"ix_{table}_deleted_at", table, ["deleted_at"])


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(f"ix_{table}_deleted_at", table)
        with op.batch_alter_table(table, schema=None) as batch:
            batch.drop_column("deleted_at")
```

- [ ] **Step 6: Test**

```python
# COLMENA/backend/tests/test_ui_state_soft_delete.py
from fastapi.testclient import TestClient


def test_baremo_table_state_delete_is_soft_and_revivable(client: TestClient):
    project = client.post("/api/v1/projects", json={"title": "Proyecto ui state"}).json()
    form = client.post(
        f"/api/v1/projects/{project['id']}/forms", json={"title": "Formulario ui state"}
    ).json()

    save = client.put(
        f"/api/v1/forms/{form['id']}/baremo-table-states/tabla1",
        json={"group_kind": "custom", "title": "Tabla 1", "rows": []},
    )
    assert save.status_code == 200

    delete = client.delete(f"/api/v1/forms/{form['id']}/baremo-table-states/tabla1")
    assert delete.status_code == 200

    listing = client.get(f"/api/v1/forms/{form['id']}/baremo-table-states")
    assert listing.json()["total"] == 0

    revived = client.put(
        f"/api/v1/forms/{form['id']}/baremo-table-states/tabla1",
        json={"group_kind": "custom", "title": "Tabla 1 revivida", "rows": []},
    )
    assert revived.status_code == 200

    listing_after = client.get(f"/api/v1/forms/{form['id']}/baremo-table-states")
    assert listing_after.json()["total"] == 1
    assert listing_after.json()["items"][0]["title"] == "Tabla 1 revivida"
```

Verificar los paths exactos de los endpoints (`PUT`/`DELETE`/`GET` de baremo table states) contra `app/routers/baremo_table_states.py` antes de fijar el test, y ajustar el método HTTP si el upsert se expone como `POST` en vez de `PUT`.

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/test_ui_state_soft_delete.py -v`
Expected: 1 passed.

- [ ] **Step 7: Correr toda la suite**

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/ -x -q`
Expected: 0 failed.

- [ ] **Step 8: Commit**

```bash
cd COLMENA/backend
git add app/models/baremo_table_state.py app/models/chart_editor_state.py app/models/chart_palette.py app/services/baremo_table_state_service.py app/services/chart_editor_state_service.py app/services/chart_palette_service.py alembic/versions/20260809_22_add_soft_delete_to_ui_state_tables.py tests/test_ui_state_soft_delete.py
git commit -m "feat: soft-delete BaremoTableState, ChartEditorState and ChartPalette instead of hard-deleting"
```

---

### Task 11: Nit — `back_populates` faltante en `ControlScaleItem`

**Files:**
- Modify: `COLMENA/backend/app/models/control_scale_item.py:19-21`
- Modify: `COLMENA/backend/app/models/form_question.py` (agregar relationship inverso si no existe)
- Modify: `COLMENA/backend/app/models/form_question_option.py` (agregar relationship inverso si no existe)

**Interfaces:** ninguna.

- [ ] **Step 1: Verificar si `FormQuestion`/`FormQuestionOption` ya tienen un lado inverso disponible**

Run: `grep -n "control_scale_items\|ControlScaleItem" COLMENA/backend/app/models/form_question.py COLMENA/backend/app/models/form_question_option.py`
Expected: sin resultados (no existe el lado inverso todavía).

- [ ] **Step 2: Agregar el relationship inverso en `FormQuestion`**

En `app/models/form_question.py`, en el bloque de relationships (junto a `answers: Mapped[list["FormAnswer"]] = relationship(back_populates="question")`, línea 317), agregar:

```python
    control_scale_items: Mapped[list["ControlScaleItem"]] = relationship(back_populates="question")
```

- [ ] **Step 3: Agregar el relationship inverso en `FormQuestionOption`**

En `app/models/form_question_option.py`, junto a `answers: Mapped[list["FormAnswer"]] = relationship(back_populates="option")` (línea 340), agregar:

```python
    control_scale_item_expectations: Mapped[list["ControlScaleItem"]] = relationship(back_populates="expected_option")
```

- [ ] **Step 4: Completar `back_populates` en `ControlScaleItem`**

En `app/models/control_scale_item.py`, cambiar:

```python
    control_scale: Mapped["ControlScale"] = relationship(back_populates="items")
    question: Mapped["FormQuestion"] = relationship()
    expected_option: Mapped["FormQuestionOption | None"] = relationship()
```

por:

```python
    control_scale: Mapped["ControlScale"] = relationship(back_populates="items")
    question: Mapped["FormQuestion"] = relationship(back_populates="control_scale_items")
    expected_option: Mapped["FormQuestionOption | None"] = relationship(back_populates="control_scale_item_expectations")
```

- [ ] **Step 5: Correr toda la suite (cambio puramente de metadata de ORM, no debería alterar comportamiento)**

Run: `cd COLMENA/backend && source venv/bin/activate && python -m pytest tests/ -x -q`
Expected: 0 failed.

- [ ] **Step 6: Commit**

```bash
cd COLMENA/backend
git add app/models/control_scale_item.py app/models/form_question.py app/models/form_question_option.py
git commit -m "fix: add missing back_populates on ControlScaleItem relationships"
```

---

## Notas de cobertura del spec

- **Roles de usuario:** descartado explícitamente por el usuario durante brainstorming — no hay tarea.
- **Hallazgo #2 original (bandas solapadas) del spec:** se descubrió durante la planeación que ya existía como warning no bloqueante (`app/scoring/band_engine.py`); el usuario decidió escalarlo a error duro — cubierto en Task 7.
- **Hallazgo #10 original (`ResponseControlFlag` faltante en `__all__`):** se verificó durante la planeación que **ya está presente** en `app/models/__init__.py:22` y en su lista `__all__` — el hallazgo del agente de auditoría era incorrecto. No hay tarea; no se toca nada.
- Los fixes #3 y #4 de "romper integridad de datos" del spec (ondelete estandarizado en ~15 FKs) se acotaron: agregar `ondelete` explícito a las FKs **nuevas** de este plan (`audit_logs`, `form_versions`, `form_responses.form_version_id`) ya está hecho en las Tasks 1-2; estandarizar retroactivamente las ~15 FKs preexistentes sin `ondelete` no se incluyó como tarea propia porque, al no haber hard-deletes en el flujo normal (confirmado durante la auditoría), es un cambio de bajo impacto práctico — si se quiere abordar, es una Task 12 candidata para un plan futuro, fuera de alcance por ahora dado que ya cubrimos los puntos con impacto real verificado.
