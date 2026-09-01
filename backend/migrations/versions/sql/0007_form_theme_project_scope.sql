-- Migración 0007: el estilo visual del formulario público (form_theme) pasa
-- a vivir en `projects.metadata`, no en `surveys.settings`.
--
-- Un proyecto acumula una fila de Survey nueva cada vez que se "crea el
-- formulario desde el instrumento" (POST /projects/{id}/surveys/from-
-- instrument), pero el Study ya abierto al público puede seguir apuntando a
-- una fila de Survey más vieja que la que el builder edita vía
-- `project.metadata.survey_id`. Guardar el estilo en `surveys.settings`
-- hacía que se guardara en un survey distinto al que realmente sirve el
-- enlace público — el cambio nunca se veía. Ver
-- app/services/public_survey_service.py.

SET search_path TO colmena, public;

-- Copia form_theme desde cualquier survey que lo tenga hacia el proyecto
-- dueño. Si más de un survey del mismo proyecto lo tuviera (no debería
-- pasar en la práctica: sólo hubo una skin editable, y sólo desde este
-- mismo cambio), se queda con el del survey de mayor id (el más reciente).
WITH latest_theme AS (
    SELECT DISTINCT ON (project_id)
        project_id,
        settings -> 'form_theme' AS form_theme
    FROM colmena.surveys
    WHERE settings ? 'form_theme'
    ORDER BY project_id, id DESC
)
UPDATE colmena.projects AS p
SET metadata = jsonb_set(p.metadata, '{form_theme}', latest_theme.form_theme, true)
FROM latest_theme
WHERE p.id = latest_theme.project_id;

UPDATE colmena.surveys
SET settings = settings - 'form_theme'
WHERE settings ? 'form_theme';
