-- ============================================================================
-- VARIABLES (harness backend §7)
-- Ausente en colmena_postgresql_schema.sql: se añade aquí siguiendo
-- exactamente la forma descrita en la especificación.
-- ============================================================================

SET search_path TO colmena, public;

CREATE TABLE IF NOT EXISTS variables (
    id                     BIGSERIAL PRIMARY KEY,
    public_id              UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    project_id             BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    study_id               BIGINT REFERENCES studies(id) ON DELETE SET NULL,
    instrument_version_id  BIGINT REFERENCES instrument_versions(id) ON DELETE SET NULL,
    question_id            BIGINT REFERENCES questions(id) ON DELETE SET NULL,
    code                   VARCHAR(120) NOT NULL,
    name                   VARCHAR(255) NOT NULL,
    label                  TEXT,
    variable_type          VARCHAR(40) NOT NULL,
    data_type              VARCHAR(40) NOT NULL,
    measurement_level      VARCHAR(40) NOT NULL,
    role                   VARCHAR(40) NOT NULL DEFAULT 'NONE',
    is_editable            BOOLEAN NOT NULL DEFAULT TRUE,
    formula                TEXT,
    metadata               JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, code),
    CHECK (variable_type IN ('QUESTION','DERIVED','DEMOGRAPHIC','EXOGENOUS','CONSTRUCT_SCORE','SYSTEM')),
    CHECK (data_type IN ('INTEGER','DECIMAL','TEXT','BOOLEAN','DATE','DATETIME','CATEGORY')),
    CHECK (measurement_level IN ('NOMINAL','ORDINAL','SCALE','BINARY','TEXT')),
    CHECK (role IN ('INDEPENDENT','DEPENDENT','CONTROL','EXOGENOUS','DESCRIPTIVE','OUTCOME','NONE'))
);

CREATE INDEX IF NOT EXISTS idx_variables_project ON variables(project_id);
CREATE INDEX IF NOT EXISTS idx_variables_study ON variables(study_id);
CREATE INDEX IF NOT EXISTS idx_variables_instrument_version ON variables(instrument_version_id);
CREATE INDEX IF NOT EXISTS idx_variables_question ON variables(question_id);

DROP TRIGGER IF EXISTS trg_variables_updated_at ON variables;
CREATE TRIGGER trg_variables_updated_at
BEFORE UPDATE ON variables
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
