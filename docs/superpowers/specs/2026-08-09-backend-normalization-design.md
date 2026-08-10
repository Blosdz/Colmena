# Normalización del backend COLMENA — versionado, auditoría y consistencia de esquema

**Fecha:** 2026-08-09
**Alcance:** `COLMENA/backend` (FastAPI + SQLAlchemy + Alembic)
**Estado:** aprobado por el usuario, pendiente de plan de implementación

## Contexto

El usuario compartió una propuesta genérica de arquitectura (users/projects/variables/dimensions/items/form_versions/form_responses/analysis_results/audit_log) generada en otra conversación, sin conocimiento del código real. Al auditar `app/models/` se confirmó que el esquema real de COLMENA ya es más granular y normalizado que esa propuesta: separa `forms` → `form_sections`/`form_instruments` → `form_dimensions` → `form_questions` → `form_question_options`, tiene `scoring_configs`/`score_bands`/`response_scores` como equivalente resuelto de "baremos", y `analysis_runs` como equivalente de "analysis_results" genérico.

Tras comparar la propuesta contra el código real, se identificaron **tres huecos reales** y, en una auditoría adicional de los 25 modelos existentes, **diez inconsistencias concretas** de normalización. Este documento cubre ambos.

No aplica: roles de usuario (admin/researcher/participant) — descartado explícitamente; el modelo actual de "owner de proyecto" es suficiente y no se toca.

## Parte 1 — Versionado de formularios

**Problema:** `publish_form()` (`app/services/public_form_service.py:200`) solo cambia `form.status = "published"`. No existe congelado de qué preguntas/opciones vio un participante. Editar una pregunta tras publicar corrompe silenciosamente la trazabilidad histórica de las respuestas ya recolectadas.

**Diseño:**

- Tabla nueva `form_versions`: `id, form_id (FK forms, RESTRICT), version_number int, status (draft|published|archived), snapshot_json JSONB, published_at, archived_at` + `TimestampMixin`.
  - `snapshot_json` se genera a partir de las tablas normalizadas (secciones, instrumentos, dimensiones, preguntas, opciones) en el momento de publicar. Es una copia de lectura para exportes/reportes (mismo patrón que `chart_editor_state`/`baremo_table_state`), **no** la fuente de verdad — las tablas normalizadas siguen siéndolo.
- `forms` gana `current_version_id` (FK nullable a `form_versions`, RESTRICT).
- `form_responses` gana `form_version_id` (FK nullable a `form_versions`, RESTRICT). Nullable para no romper respuestas ya existentes en desarrollo; los servicios nuevos siempre lo setean.
- Regla de negocio en `form_service.py`: si un `Form` tiene una versión `published` con al menos una `FormResponse` asociada, cualquier PATCH que modifique contenido (no reordenar) de `FormQuestion`/`FormQuestionOption`/`FormInstrument`/`FormDimension`/`FormSection` de ese form debe fallar con un error claro indicando que hay que crear una nueva versión draft primero. Crear una versión draft clona el árbol de contenido actual (nuevas filas, no las mismas) para editar sin afectar la versión publicada.
- `publish_form()` pasa a: validar que existan preguntas activas (ya existe), generar `snapshot_json`, crear/actualizar `form_versions` con `version_number` incremental, apuntar `forms.current_version_id`.

## Parte 2 — `audit_log` genérico

**Problema:** no hay trazabilidad de quién creó/editó/borró/publicó qué. Necesario para auditoría de proyectos de tesis (integridad de datos de investigación).

**Diseño:**

- Tabla `audit_logs`: `id, user_id (FK users, nullable, SET NULL), project_id (FK projects, nullable, SET NULL), entity_type varchar(50), entity_id varchar(36), action varchar(20), old_data JSONB nullable, new_data JSONB nullable, created_at`. Sin `SoftDeleteMixin` ni `updated_at` — es un log inmutable de solo inserción.
- `action` ∈ `create|update|delete|publish|archive|close|reopen`.
- Nuevo `app/services/audit_service.py` con `record(db, *, user_id, project_id, entity_type, entity_id, action, old_data=None, new_data=None)`.
- Se invoca explícitamente desde los servicios existentes en los puntos que ya mutan estado de forma significativa: `project_service` (create/delete de `Project`), `project_variable_service` (create/delete), `form_service` (create/delete/publish nueva versión), `public_form_service` (publish/close/reopen), `scoring_config_service` (create/update/delete de `ScoringConfig`/`ScoreBand`). No se instrumenta cada PATCH trivial (p. ej. reordenar `sort_order`) para evitar ruido.
- Sin hooks automáticos de SQLAlchemy (`after_insert`/`after_update`) — decisión explícita del usuario para mantener control manual sobre qué es "auditable".

## Parte 3 — Fixes de consistencia de esquema

Hallazgos de la auditoría de los 25 modelos actuales, con su fix:

**Integridad de datos:**

1. Falta `UniqueConstraint` real (hoy solo `index=True`) en: `project_variables(project_id, code)`, `form_questions(form_id, code)`, `form_dimensions(instrument_id, code)`, condicionado a `code IS NOT NULL`.
2. `ScoreBand` no impide rangos `min_value`/`max_value` solapados dentro del mismo `scoring_config_id`. Fix a nivel de servicio (`scoring_config_service`): validar solapamiento antes de insertar/actualizar una banda (no constraint de BD, para evitar dependencia de `btree_gist`).
3. `ResponseScore`/`ResponseControlFlag` no tienen soft-delete y cuelgan de `FormResponse` que sí lo tiene. Fix: no agregar el mixin (evita doble fuente de verdad); en su lugar, las queries de reportes/exports (`analysis_orchestrator_service`, `apa_table_service`, endpoints de export) deben unir siempre con `FormResponse.deleted_at IS NULL`.
4. ~15 FKs sin `ondelete` explícito. Fix: estandarizar a `ondelete="RESTRICT"` explícito en todas las FKs internas de Colmena (documenta la intención: nunca hay hard-delete en el flujo normal).

**Diseño:**

5. `measurement_level`/`data_type` duplicados entre `ProjectVariable` y `FormQuestion` sin sincronización. Fix en `form_question_service`: al crear/actualizar una pregunta con `project_variable_id` seteado, copiar esos dos campos desde la variable (la pregunta no puede divergir silenciosamente de su variable).
6. Mixins de soft-delete inconsistentes. Criterio adoptado: tablas de **estado editable por el usuario** (`BaremoTableState`, `ChartEditorState`, `ChartPalette`) ganan `SoftDeleteMixin` (paridad con `ScoringConfig`/`ControlScale`); tablas de **resultado derivado/inmutable** (`AnalysisRun`, `ExportArtifact`) se quedan sin él intencionalmente.
7. `Form.metadata_json` es `Text`, inconsistente con el resto de columnas `*_json` que son `JSON`. Fix: cambiar a `JSON`.
8. (Descartado como hallazgo) `response_score.band_label` "desincronizado" del catálogo activo tras soft-delete de una `ScoreBand` es comportamiento **intencional**: es una foto congelada al momento de puntuar, mismo principio que `form_versions.snapshot_json` en la Parte 1. Se documenta aquí, no se corrige.

**Nits:**

9. Agregar `back_populates` faltante en `app/models/control_scale_item.py` (relaciones `question`/`expected_option`).
10. Agregar `ResponseControlFlag` al `__all__` de `app/models/__init__.py`.

## Migraciones Alembic

Todo lo anterior requiere migraciones nuevas (no se edita ninguna de las 18 existentes). Migraciones separadas por tema para poder aplicar/revertir independientemente:

1. `form_versions` + `forms.current_version_id` + `form_responses.form_version_id`.
2. `audit_logs`.
3. Constraints de unicidad (#1) + `ondelete` estandarizado (#4) + `Form.metadata_json` a `JSON` (#7).
4. `SoftDeleteMixin` en `BaremoTableState`/`ChartEditorState`/`ChartPalette` (#6) — agrega columna `deleted_at`.

Los fixes #2, #3, #5, #9, #10 son cambios de servicio/modelo sin migración de esquema (excepto #9/#10 que no tocan BD en absoluto).

## Testing

- Tests unitarios de `form_service`: publicar genera versión + snapshot correcto; PATCH de contenido tras publicar con respuestas existentes falla y exige nueva versión draft; clonar versión draft preserva árbol de contenido con nuevos IDs.
- Tests de `audit_service.record()` y de que cada servicio instrumentado efectivamente inserta el log esperado (create/update/delete/publish).
- Tests de `scoring_config_service` para el fix #2 (rechazar bandas solapadas).
- Test de regresión de queries de reporte/export para el fix #3 (respuesta soft-deleted no aparece).
- Migraciones probadas con `alembic upgrade head` / `downgrade -1` en base de datos de desarrollo.
