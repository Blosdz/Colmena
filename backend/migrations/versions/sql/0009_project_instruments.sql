-- Instrumento pasa a ser una unidad repetible dentro del proyecto. Las
-- dimensiones/constructos continúan perteneciendo a cada versión.

SET search_path TO colmena, public;

ALTER TABLE instruments
    ADD COLUMN project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE;

CREATE INDEX ix_instruments_project_id ON instruments(project_id);

-- Compatibilidad: adopta el instrumento único guardado por el frontend
-- anterior en projects.metadata, siempre que el valor sea un entero válido.
UPDATE instruments AS instrument
SET project_id = project.id
FROM projects AS project
WHERE project.metadata ? 'instrument_id'
  AND (project.metadata ->> 'instrument_id') ~ '^[0-9]+$'
  AND instrument.id = (project.metadata ->> 'instrument_id')::BIGINT
  AND instrument.project_id IS NULL;
