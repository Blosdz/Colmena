SET search_path TO colmena, public;

DROP INDEX IF EXISTS uq_constructs_project_root_per_version;

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    FOR constraint_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'constructs'::regclass
          AND contype = 'c'
          AND position('construct_type' in pg_get_constraintdef(oid)) > 0
    LOOP
        EXECUTE 'ALTER TABLE constructs DROP CONSTRAINT ' || quote_ident(constraint_name);
    END LOOP;
END $$;

UPDATE constructs
SET
    construct_type = 'VARIABLE',
    metadata = jsonb_set(
        jsonb_set(COALESCE(metadata, '{}'::jsonb), '{node_kind}', '"VARIABLE"'::jsonb),
        '{role}',
        to_jsonb(COALESCE(metadata ->> 'role', 'INDEPENDENT'))
    )
WHERE construct_type = 'PROJECT'
  AND parent_id IS NULL;

ALTER TABLE constructs
    ADD CONSTRAINT ck_constructs_construct_type
    CHECK (construct_type IN ('VARIABLE','DIMENSION','SUBDIMENSION','SCALE','FACTOR','INDEX'));

CREATE INDEX ix_constructs_structure_variables
ON constructs(instrument_version_id, sort_order, id)
WHERE construct_type = 'VARIABLE' AND parent_id IS NULL;
