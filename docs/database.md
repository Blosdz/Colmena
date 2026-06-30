# Base de datos de Colmena

> Documento generado a partir del esquema **real** de la base SQLite
> (`backend/data/db/colmena.db`) y los modelos en `backend/app/models/`.
> Motor: **SQLite** (desarrollo) vía SQLAlchemy 2.0 + migraciones Alembic.

## Respuestas rápidas

| Pregunta | Respuesta |
|----------|-----------|
| **¿Tiene tabla de `users`?** | ✅ **SÍ.** Existe `users` (espejo de cuentas de AppThesis vía cross-login). |
| **¿Tiene backend de autenticación?** | ✅ **Parcial.** Cross-login: `POST /api/v1/auth/appthesis` valida un JWT de AppThesis y crea/actualiza el usuario local. No hay contraseñas propias. |
| **¿Quién es el "dueño" de un proyecto?** | El usuario autenticado que lo crea: `projects.user_id` (NOT NULL, FK → `users.id`). |

> ⚠️ **Estado de seguridad:** `POST /api/v1/projects` exige `Authorization: Bearer <JWT
> de AppThesis>` (se valida contra thesis-backend). Las lecturas (`GET`) siguen abiertas
> por ahora; el **owner-scoping** de listados (que cada usuario vea solo lo suyo) es un
> pendiente.

---

## Resumen del modelo

El agregado raíz es **`projects`**. Todo cuelga de un proyecto de investigación.
Las tablas usan **PK de tipo `VARCHAR(36)` (UUID)** y la mayoría incluye
`created_at`, `updated_at` y **soft delete** (`deleted_at`).

### Cadena principal de datos

```
projects
  └─ project_variables
  └─ forms
       ├─ form_sections
       ├─ form_instruments
       │     └─ form_dimensions
       ├─ form_questions
       │     └─ form_question_options
       └─ form_responses
             └─ form_answers
```

### Familia de scoring / control de calidad

```
scoring_configs ─ score_bands
control_scales ─ control_scale_items
response_scores         (puntaje por respuesta)
response_control_flags  (banderas de validez por respuesta)
```

### Familia de análisis / salidas

```
analysis_runs        (trazabilidad de cada corrida estadística)
chart_editor_states  (estado del editor visual de gráficos)
export_artifacts     (CSV, Excel, Word, imágenes generadas)
```

---

## Inventario de tablas (19)

| # | Tabla | Propósito |
|---|-------|-----------|
| 1 | `projects` | Proyecto de investigación (raíz) |
| 2 | `project_variables` | Variables del estudio (rol, nivel, tipo) |
| 3 | `forms` | Formularios/instrumentos publicables |
| 4 | `form_sections` | Secciones de un formulario |
| 5 | `form_instruments` | Instrumentos/escalas dentro del formulario |
| 6 | `form_dimensions` | Dimensiones de un instrumento |
| 7 | `form_questions` | Preguntas/ítems |
| 8 | `form_question_options` | Opciones de respuesta de cada pregunta |
| 9 | `form_responses` | Respuesta completa de un participante (1 fila = 1 persona) |
| 10 | `form_answers` | Respuesta por pregunta (1 fila = 1 celda) |
| 11 | `scoring_configs` | Reglas de cálculo de puntaje |
| 12 | `score_bands` | Baremos / rangos interpretativos |
| 13 | `control_scales` | Escalas de control (mentira, atención, consistencia) |
| 14 | `control_scale_items` | Ítems vinculados a una escala de control |
| 15 | `response_scores` | Puntaje calculado por respuesta y config |
| 16 | `response_control_flags` | Banderas de validez por respuesta |
| 17 | `analysis_runs` | Registro de corridas estadísticas |
| 18 | `chart_editor_states` | Estado persistido del editor de gráficos |
| 19 | `export_artifacts` | Archivos exportados (CSV/Excel/Word/imágenes) |
| – | `alembic_version` | Control interno de versión de migraciones |

---

## Esquema detallado

### `projects`
Unidad raíz. Tiene dueño (`user_id`) y los tipos normalizados como FK a catálogos.
La demografía se movió a `project_demographics` (1:1).

| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| user_id | VARCHAR(36) | **NOT NULL, FK → users.id** (dueño) |
| title | VARCHAR(255) | NOT NULL |
| subtitle | VARCHAR(255) | |
| type_research_id | VARCHAR(36) | FK → type_research.id |
| design_type_id | VARCHAR(36) | FK → design_type.id |
| approach_id | VARCHAR(36) | FK → approach.id |
| institution | VARCHAR(255) | |
| faculty | VARCHAR(255) | |
| career | VARCHAR(255) | |
| advisor_name | VARCHAR(255) | nombre del asesor (texto, no un usuario) |
| status | VARCHAR(50) | NOT NULL |
| notes | TEXT | |
| created_at / updated_at | DATETIME | |
| deleted_at | DATETIME | soft delete |

### Catálogos `type_research` / `design_type` / `approach`
Misma estructura los tres (normalizan los tipos que antes eran texto en `projects`).

| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| name | VARCHAR(150) | NOT NULL, UNIQUE |
| description | TEXT | |
| metadata_json | JSON | |
| is_active | BOOLEAN | NOT NULL, default TRUE |
| created_at / updated_at | DATETIME | |
| deleted_at | DATETIME | soft delete |

Endpoints de lectura: `GET /api/v1/catalogs/research-types|design-types|approaches`.

### `project_demographics`
Demografía del proyecto. **1:1 con `projects`** (UNIQUE en `project_id`).

| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id | VARCHAR(36) | NOT NULL, UNIQUE, FK → projects.id |
| population_description | TEXT | |
| sample_size_planned | INTEGER | |
| sample_size_current | INTEGER | NOT NULL, default 0 |
| sampling_method | VARCHAR(100) | |
| inclusion_criteria | TEXT | |
| exclusion_criteria | TEXT | |
| metadata_json | JSON | |
| created_at / updated_at | DATETIME | |
| deleted_at | DATETIME | soft delete |

### `project_variables`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id | VARCHAR(36) | FK → projects.id |
| name | VARCHAR(255) | NOT NULL |
| code | VARCHAR(100) | |
| description | TEXT | |
| variable_role | VARCHAR(50) | NOT NULL |
| measurement_level | VARCHAR(50) | NOT NULL |
| data_type | VARCHAR(50) | NOT NULL |
| is_required_for_analysis | BOOLEAN | NOT NULL |
| notes | TEXT | |
| created_at / updated_at / deleted_at | DATETIME | |

### `forms`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id | VARCHAR(36) | FK → projects.id |
| title | VARCHAR(255) | NOT NULL |
| description / instructions | TEXT | |
| status | VARCHAR(50) | NOT NULL (`draft`/`published`/`closed`/`archived`) |
| public_slug | VARCHAR(255) | slug del link público |
| allow_anonymous | BOOLEAN | NOT NULL |
| collect_started_at / collect_closed_at | DATETIME | |
| thank_you_message | TEXT | |
| metadata_json | TEXT | |
| created_at / updated_at / deleted_at | DATETIME | |

### `form_sections`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| form_id | VARCHAR(36) | FK → forms.id |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| sort_order | INTEGER | NOT NULL |
| created_at / updated_at / deleted_at | DATETIME | |

### `form_instruments`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| form_id | VARCHAR(36) | FK → forms.id |
| project_variable_id | VARCHAR(36) | FK → project_variables.id |
| name | VARCHAR(255) | NOT NULL |
| acronym | VARCHAR(50) | |
| author | VARCHAR(255) | autor del instrumento (texto) |
| year | INTEGER | |
| description | TEXT | |
| response_scale_name | VARCHAR(255) | |
| scoring_method | VARCHAR(255) | |
| reverse_scoring_enabled | BOOLEAN | NOT NULL |
| sort_order | INTEGER | NOT NULL |
| created_at / updated_at / deleted_at | DATETIME | |

### `form_dimensions`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| instrument_id | VARCHAR(36) | FK → form_instruments.id |
| name | VARCHAR(255) | NOT NULL |
| code | VARCHAR(100) | |
| description | TEXT | |
| sort_order | INTEGER | NOT NULL |
| created_at / updated_at / deleted_at | DATETIME | |

### `form_questions`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| form_id | VARCHAR(36) | FK → forms.id |
| section_id | VARCHAR(36) | FK → form_sections.id |
| instrument_id | VARCHAR(36) | FK → form_instruments.id |
| dimension_id | VARCHAR(36) | FK → form_dimensions.id |
| project_variable_id | VARCHAR(36) | FK → project_variables.id |
| code | VARCHAR(100) | |
| label | TEXT | NOT NULL |
| help_text | TEXT | |
| question_type | VARCHAR(50) | NOT NULL |
| question_role | VARCHAR(50) | NOT NULL |
| measurement_level | VARCHAR(50) | NOT NULL |
| data_type | VARCHAR(50) | NOT NULL |
| is_required | BOOLEAN | NOT NULL |
| is_scored | BOOLEAN | NOT NULL |
| is_reverse_scored | BOOLEAN | NOT NULL |
| min_value / max_value | FLOAT | |
| sort_order | INTEGER | NOT NULL |
| validation_json / config_json | JSON | |
| created_at / updated_at / deleted_at | DATETIME | |

### `form_question_options`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| question_id | VARCHAR(36) | FK → form_questions.id |
| label | VARCHAR(255) | NOT NULL |
| value | VARCHAR(255) | NOT NULL |
| score | FLOAT | |
| sort_order | INTEGER | NOT NULL |
| created_at / updated_at / deleted_at | DATETIME | |

### `form_responses`
1 fila = 1 participante. **`respondent_code` es un código, no un usuario autenticado.**

| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id | VARCHAR(36) | FK → projects.id |
| form_id | VARCHAR(36) | FK → forms.id |
| respondent_code | VARCHAR(100) | código opcional del respondiente |
| status | VARCHAR(50) | NOT NULL |
| submitted_at | DATETIME | |
| source | VARCHAR(50) | NOT NULL (público/interno) |
| metadata_json | JSON | |
| created_at / updated_at / deleted_at | DATETIME | |

### `form_answers`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| response_id | VARCHAR(36) | FK → form_responses.id |
| question_id | VARCHAR(36) | FK → form_questions.id |
| option_id | VARCHAR(36) | FK → form_question_options.id |
| value_text | TEXT | |
| value_number | FLOAT | |
| value_date | DATETIME | |
| value_json | JSON | |
| score_value | FLOAT | |
| created_at / updated_at | DATETIME | |

### `scoring_configs`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id / form_id | VARCHAR(36) | FK |
| instrument_id / dimension_id / project_variable_id | VARCHAR(36) | FK (opcionales) |
| name | VARCHAR(255) | NOT NULL |
| code | VARCHAR(100) | |
| scoring_level | VARCHAR(50) | NOT NULL |
| aggregation_method | VARCHAR(50) | NOT NULL |
| missing_policy | VARCHAR(50) | NOT NULL |
| min_answered_items | INTEGER | |
| min_completion_percent | FLOAT | |
| reverse_scoring_enabled | BOOLEAN | NOT NULL |
| score_min / score_max | FLOAT | |
| interpretation_enabled | BOOLEAN | NOT NULL |
| config_json | JSON | |
| is_active | BOOLEAN | NOT NULL |
| created_at / updated_at / deleted_at | DATETIME | |

### `score_bands`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| scoring_config_id | VARCHAR(36) | FK → scoring_configs.id |
| label | VARCHAR(100) | NOT NULL |
| code | VARCHAR(100) | |
| min_value / max_value | FLOAT | NOT NULL |
| interpretation / recommendation | TEXT | |
| severity_order | INTEGER | NOT NULL |
| color_hint | VARCHAR(50) | |
| created_at / updated_at / deleted_at | DATETIME | |

### `control_scales`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id / form_id | VARCHAR(36) | FK |
| instrument_id | VARCHAR(36) | FK (opcional) |
| name | VARCHAR(255) | NOT NULL |
| code | VARCHAR(100) | |
| control_type | VARCHAR(50) | NOT NULL (mentira/atención/…) |
| rule_type | VARCHAR(50) | NOT NULL |
| threshold | FLOAT | |
| comparison_operator | VARCHAR(10) | |
| flag_level | VARCHAR(20) | NOT NULL |
| message | TEXT | |
| config_json | JSON | |
| is_active | BOOLEAN | NOT NULL |
| created_at / updated_at / deleted_at | DATETIME | |

### `control_scale_items`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| control_scale_id | VARCHAR(36) | FK → control_scales.id |
| question_id | VARCHAR(36) | FK → form_questions.id |
| expected_option_id | VARCHAR(36) | FK → form_question_options.id |
| expected_value_text | TEXT | |
| expected_value_number | FLOAT | |
| fail_if_selected | BOOLEAN | NOT NULL |
| weight | FLOAT | NOT NULL |
| pair_group | VARCHAR(100) | |
| created_at / updated_at / deleted_at | DATETIME | |

### `response_scores`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id / form_id / response_id | VARCHAR(36) | FK |
| scoring_config_id | VARCHAR(36) | FK → scoring_configs.id |
| instrument_id / dimension_id / project_variable_id | VARCHAR(36) | FK (opcionales) |
| raw_score / mean_score / weighted_score / final_score | FLOAT | |
| answered_items / missing_items / total_items | INTEGER | NOT NULL |
| completion_percent | FLOAT | |
| band_id | VARCHAR(36) | FK → score_bands.id |
| band_label | VARCHAR(100) | |
| interpretation | TEXT | |
| validity_status | VARCHAR(20) | NOT NULL |
| warnings_json | JSON | |
| created_at / updated_at | DATETIME | |

### `response_control_flags`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id / form_id / response_id | VARCHAR(36) | FK |
| control_scale_id | VARCHAR(36) | FK → control_scales.id |
| score | FLOAT | |
| failed_items / total_items | INTEGER | NOT NULL |
| flag_status | VARCHAR(20) | NOT NULL |
| message | TEXT | |
| details_json | JSON | |
| created_at / updated_at | DATETIME | |

### `analysis_runs`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id / form_id | VARCHAR(36) | FK |
| analysis_type | VARCHAR(100) | NOT NULL (normality, correlation, …) |
| status | VARCHAR(50) | NOT NULL |
| params_json / result_json | JSON | |
| created_at | DATETIME | NOT NULL |

### `chart_editor_states`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| storage_key | TEXT | NOT NULL |
| form_id / project_id | VARCHAR(36) | FK |
| chart_id | VARCHAR(255) | NOT NULL |
| graphs_json / metadata_json | JSON | |
| created_at / updated_at | DATETIME | NOT NULL |
| | | UNIQUE (form_id, chart_id) |

### `export_artifacts`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | VARCHAR(36) | PK |
| project_id | VARCHAR(36) | FK → projects.id |
| form_id | VARCHAR(36) | FK → forms.id (opcional) |
| artifact_type | VARCHAR(100) | NOT NULL (csv/xlsx/docx/png/…) |
| file_name | VARCHAR(255) | NOT NULL |
| file_path | TEXT | NOT NULL |
| mime_type | VARCHAR(255) | |
| file_size_bytes | INTEGER | |
| metadata_json | JSON | |
| created_at / updated_at | DATETIME | NOT NULL |

---

## Conclusión sobre usuarios / autenticación

Colmena modela usuarios vía **cross-login con AppThesis**:

- Existe tabla `users` (espejo de cuentas de AppThesis; sin contraseñas propias).
- `POST /api/v1/auth/appthesis` valida un JWT de AppThesis y crea/actualiza el usuario.
- `projects.user_id` (NOT NULL) vincula cada proyecto a su dueño; se asigna desde el
  usuario autenticado al crear (`Authorization: Bearer`).

**Pendiente:** owner-scoping de las lecturas (que cada usuario vea solo sus proyectos)
y, opcionalmente, cachear la validación del JWT para no golpear a thesis-backend en cada
request.
