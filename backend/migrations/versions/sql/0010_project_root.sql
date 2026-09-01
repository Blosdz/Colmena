-- El proyecto es la única raíz visible de cada versión. Las variables
-- derivadas creadas por el constructor anterior dejan de formar parte del modelo.
SET search_path TO colmena, public;

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

ALTER TABLE constructs
    ADD CONSTRAINT ck_constructs_construct_type
    CHECK (construct_type IN ('PROJECT','DIMENSION','SUBDIMENSION','SCALE','FACTOR','INDEX'));

INSERT INTO constructs (
    instrument_version_id,
    parent_id,
    code,
    name,
    construct_type,
    sort_order,
    metadata
)
SELECT
    version.id,
    NULL,
    'project_root',
    COALESCE(project.name, instrument.name),
    'PROJECT',
    0,
    '{"node_kind":"PROJECT_ROOT"}'::jsonb
FROM instrument_versions AS version
JOIN instruments AS instrument ON instrument.id = version.instrument_id
LEFT JOIN projects AS project ON project.id = instrument.project_id
WHERE NOT EXISTS (
    SELECT 1
    FROM constructs AS existing
    WHERE existing.instrument_version_id = version.id
      AND existing.construct_type = 'PROJECT'
      AND existing.parent_id IS NULL
);

CREATE TEMP TABLE old_research_roots ON COMMIT DROP AS
SELECT DISTINCT old_root.id, project_root.id AS project_root_id
FROM constructs AS old_root
JOIN constructs AS project_root
  ON project_root.instrument_version_id = old_root.instrument_version_id
 AND project_root.construct_type = 'PROJECT'
 AND project_root.parent_id IS NULL
LEFT JOIN variables AS variable ON variable.construct_id = old_root.id
WHERE old_root.id <> project_root.id
  AND old_root.parent_id IS NULL
  AND (
      variable.id IS NOT NULL
      OR old_root.metadata ->> 'node_kind' = 'VARIABLE'
  );

UPDATE constructs AS child
SET parent_id = legacy.project_root_id
FROM old_research_roots AS legacy
WHERE child.parent_id = legacy.id;

INSERT INTO construct_items (
    construct_id,
    question_id,
    weight,
    item_role,
    scoring_direction,
    sort_order,
    metadata
)
SELECT
    legacy.project_root_id,
    item.question_id,
    item.weight,
    item.item_role,
    item.scoring_direction,
    item.sort_order,
    item.metadata
FROM old_research_roots AS legacy
JOIN construct_items AS item ON item.construct_id = legacy.id
ON CONFLICT (construct_id, question_id) DO NOTHING;

UPDATE constructs AS dimension
SET parent_id = project_root.id
FROM constructs AS project_root
WHERE dimension.instrument_version_id = project_root.instrument_version_id
  AND project_root.construct_type = 'PROJECT'
  AND project_root.parent_id IS NULL
  AND dimension.parent_id IS NULL
  AND dimension.id <> project_root.id
  AND NOT EXISTS (
      SELECT 1 FROM old_research_roots AS legacy WHERE legacy.id = dimension.id
  );

UPDATE analysis_results AS result
SET construct_id = legacy.project_root_id
FROM old_research_roots AS legacy
WHERE result.construct_id = legacy.id;

DELETE FROM construct_results
WHERE construct_id IN (SELECT id FROM old_research_roots);

UPDATE action_plan_items AS item
SET construct_id = legacy.project_root_id
FROM old_research_roots AS legacy
WHERE item.construct_id = legacy.id;

DELETE FROM variables
WHERE construct_id IN (SELECT id FROM old_research_roots);

DELETE FROM constructs
WHERE id IN (SELECT id FROM old_research_roots);

CREATE UNIQUE INDEX uq_constructs_project_root_per_version
ON constructs(instrument_version_id)
WHERE construct_type = 'PROJECT' AND parent_id IS NULL;
