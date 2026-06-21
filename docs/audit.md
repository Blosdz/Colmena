# Auditoría — Autenticación y gestión de usuarios

> **Fecha de auditoría:** 2026-06-21
> **Alcance:** backend FastAPI (`backend/app`), base de datos SQLite
> (`backend/data/db/colmena.db`) y frontend React (`frontend/src`).
> **Objetivo:** verificar si el sistema cuenta con tabla de usuarios y con un
> mecanismo de autenticación (login / signup).

---

## 1. Veredicto

| Componente | ¿Existe? | Evidencia |
|------------|----------|-----------|
| Tabla `users` (o equivalente) | ❌ **NO** | No aparece en el esquema real de la BD |
| Tablas de sesión / token / credenciales | ❌ **NO** | Ninguna tabla de auth en la BD |
| Modelo SQLAlchemy de usuario | ❌ **NO** | No existe en `backend/app/models/` |
| Endpoints de login / signup / logout | ❌ **NO** | No existen en `backend/app/routers/` |
| Hashing de contraseñas | ❌ **NO** | No hay `passlib`, `bcrypt` ni similares |
| JWT / OAuth2 / sesiones | ❌ **NO** | No hay `python-jose`, `OAuth2`, `HTTPBearer` |
| Login / registro en frontend | ❌ **NO** | No hay rutas ni páginas de auth en React |
| Propiedad de proyectos (`owner_id`) | ❌ **NO** | `projects` no tiene FK a usuario |

> **Conclusión:** el sistema **NO implementa autenticación ni gestión de usuarios**.
> Es un sistema **single-tenant abierto**: cualquier cliente con acceso de red a la
> API puede leer y modificar todos los proyectos, formularios y respuestas.

---

## 2. Evidencia recogida

### 2.1 Tablas reales en la base de datos (19 tablas)

```
alembic_version          form_questions           response_control_flags
analysis_runs            form_responses           response_scores
chart_editor_states      form_sections            score_bands
control_scale_items      forms                    scoring_configs
control_scales           project_variables
export_artifacts         projects
form_answers             response_*  (scores/flags)
form_dimensions
form_instruments
form_question_options
```

**Ninguna** corresponde a usuarios, cuentas, sesiones, tokens o credenciales.

Consulta de verificación ejecutada:

```sql
SELECT name FROM sqlite_master
WHERE type='table'
  AND ( name LIKE '%user%' OR name LIKE '%auth%' OR name LIKE '%login%'
     OR name LIKE '%account%' OR name LIKE '%session%' OR name LIKE '%token%'
     OR name LIKE '%password%' OR name LIKE '%credential%' );
-- Resultado: 0 filas
```

### 2.2 Modelos del backend

Archivos en `backend/app/models/`: `analysis_run`, `chart_editor_state`,
`control_scale`, `control_scale_item`, `export_artifact`, `form`, `form_answer`,
`form_dimension`, `form_instrument`, `form_question`, `form_question_option`,
`form_response`, `form_section`, `project`, `project_variable`,
`response_control_flag`, `response_score`, `score_band`, `scoring_config`.

→ **No existe `user.py` ni `account.py` ni `auth.py`.**

### 2.3 Búsqueda de lógica de autenticación (backend)

```bash
grep -rilE 'login|signup|register|jwt|oauth|password|authenticate|bearer' backend/app/*.py
# Resultado: sin coincidencias
```

Las únicas apariciones de `Depends(...)` en los routers corresponden a
**inyección de la sesión de base de datos** (`Depends(get_db)`), no a
verificación de identidad. No existe `get_current_user`, `OAuth2PasswordBearer`
ni `HTTPBearer`.

### 2.4 Dependencias declaradas (`requirements.txt`)

```
fastapi, uvicorn, sqlalchemy, pydantic, pydantic-settings, python-dotenv,
pandas, numpy, scipy, statsmodels, python-docx, openpyxl, alembic, pytest, httpx
```

→ **No hay ninguna librería de seguridad/auth** (sin `passlib`, `bcrypt`,
`python-jose`, `authlib`, `fastapi-users`, etc.).

### 2.5 Frontend (React)

- No existen rutas `/login`, `/signup`, `/register` en el router.
- No existen páginas ni componentes de autenticación.
- Las coincidencias de texto con `auth`/`register` resultaron ser
  **falsos positivos** (p. ej. `author` de instrumento, `addEventListener`).

### 2.6 Exposición de la API

`backend/app/main.py` habilita CORS para `http://localhost:5173` y
`http://127.0.0.1:5173`, pero **sin ninguna capa de autorización** detrás.
Todos los endpoints `api/v1/...` y `api/public/...` responden sin credenciales.

---

## 3. Riesgos identificados

| ID | Riesgo | Severidad | Descripción |
|----|--------|-----------|-------------|
| R1 | Acceso no autenticado a datos | 🔴 Alta | Cualquiera con acceso de red lee/edita proyectos y **respuestas de participantes** (datos potencialmente sensibles). |
| R2 | Sin aislamiento entre usuarios | 🔴 Alta | No hay multi-tenancy; un solo espacio compartido sin propietarios. |
| R3 | Exposición pública peligrosa | 🔴 Alta | Publicar la API (ngrok/servidor) la deja **abierta a internet** sin barrera. |
| R4 | Sin trazabilidad de autoría | 🟠 Media | No se registra **quién** crea o modifica cada entidad (no hay `created_by`). |
| R5 | Datos personales sin protección | 🟠 Media | Respuestas de encuestas sin control de acceso pueden implicar incumplimiento de protección de datos. |

---

## 4. Recomendaciones (qué falta implementar)

Para convertir Colmena en un sistema multiusuario seguro haría falta:

1. **Tabla `users`** con, al menos:
   `id`, `email` (único), `password_hash`, `full_name`, `role`,
   `is_active`, `created_at`, `updated_at`.
2. **Hashing de contraseñas** con `passlib[bcrypt]` (nunca texto plano).
3. **Autenticación**: `OAuth2PasswordBearer` + **JWT** (`python-jose`) o sesiones.
4. **Endpoints** `POST /api/v1/auth/register`, `POST /api/v1/auth/login`,
   `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`.
5. **Propiedad de datos**: columna `owner_id` (FK → `users.id`) en `projects`
   y filtrado por propietario en todas las consultas.
6. **Autorización**: dependencia `get_current_user` aplicada a los routers
   internos (`api/v1/...`); mantener `api/public/...` solo para responder formularios.
7. **Migración Alembic** que cree la tabla `users` y agregue `owner_id`.
8. **Frontend**: páginas de **login / signup**, almacenamiento seguro del token,
   guardas de ruta y cierre de sesión.
9. **Roles** (p. ej. `admin`, `researcher`, `viewer`) si se requiere granularidad.

> Mientras no se implemente lo anterior, se recomienda **no exponer la API a
> internet** y limitar su uso a entorno local de confianza.

---

## 5. Resumen ejecutivo

Colmena tiene un dominio de investigación maduro (proyectos, formularios,
estadística, reportes), pero **carece por completo de una capa de identidad**.
No existe tabla de usuarios ni mecanismo de login/registro en backend ni frontend.
Es una **brecha funcional y de seguridad conocida**, apropiada para un MVP de uso
local, pero **bloqueante antes de cualquier despliegue compartido o público**.
