-- Migración 0008: el valor de tipo "CENSOPAS" pasa a llamarse "CENSO".
--
-- CENSOPAS es el nombre propio del instituto de salud peruano dueño del
-- instrumento COPSOQ (ver instrument.code='CENSOPAS_COPSOQ', que no se
-- toca aquí). Usarlo como valor genérico de project_type/study_type/
-- survey_type en una app multi-tenant confunde a cualquier organización
-- que use el flujo dimensional con otro instrumento. Se renombra a
-- "CENSO", manteniendo el instrumento sembrado intacto.

SET search_path TO colmena, public;

ALTER TABLE projects DROP CONSTRAINT projects_project_type_check;
UPDATE projects SET project_type = 'CENSO' WHERE project_type = 'CENSOPAS';
ALTER TABLE projects ADD CONSTRAINT projects_project_type_check
    CHECK (project_type IN ('ACADEMIC', 'CENSO', 'CUSTOM', 'RESEARCH'));

ALTER TABLE studies DROP CONSTRAINT studies_study_type_check;
UPDATE studies SET study_type = 'CENSO' WHERE study_type = 'CENSOPAS';
ALTER TABLE studies ADD CONSTRAINT studies_study_type_check
    CHECK (study_type IN ('ACADEMIC', 'CENSO', 'CUSTOM', 'RESEARCH'));

ALTER TABLE surveys DROP CONSTRAINT surveys_survey_type_check;
UPDATE surveys SET survey_type = 'CENSO' WHERE survey_type = 'CENSOPAS';
ALTER TABLE surveys ADD CONSTRAINT surveys_survey_type_check
    CHECK (survey_type IN ('CUSTOM', 'ACADEMIC', 'CENSO', 'INSTRUMENT'));
