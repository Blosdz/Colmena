"""Catálogo de planes analíticos, capacidades CENSOPAS y códigos de organización."""

from alembic import op
import sqlalchemy as sa


revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

SCHEMA = "colmena"

TOOLS = [
    ("FREQUENCY", "Frecuencias", "DESCRIPTIVE", "FREQUENCIES", 5, False, False, False),
    ("PERCENTAGE", "Porcentajes", "DESCRIPTIVE", "FREQUENCIES", 5, False, False, False),
    ("CENSOPAS_DISTRIBUTION", "Distribución CENSOPAS", "DESCRIPTIVE", "LIKERT_SCORING", 5, False, False, False),
    ("CONFIDENCE_INTERVAL", "Intervalos de confianza 95%", "INFERENTIAL", None, 25, False, True, False),
    ("CRONBACH_ALPHA", "Alfa de Cronbach", "RELIABILITY", "RELIABILITY", 25, False, True, False),
    ("MCDONALD_OMEGA", "Omega de McDonald", "RELIABILITY", "RELIABILITY", 25, False, True, False),
    ("CHI_SQUARE", "Chi-cuadrado", "INFERENTIAL", "CHI_SQUARE", 25, True, False, False),
    ("MANN_WHITNEY", "Mann-Whitney", "INFERENTIAL", "COMPARE_GROUPS", 25, True, True, False),
    ("KRUSKAL_WALLIS", "Kruskal-Wallis", "INFERENTIAL", "COMPARE_GROUPS", 25, True, True, False),
    ("SPEARMAN", "Spearman", "ASSOCIATION", "SPEARMAN_MATRIX", 25, False, True, False),
    ("EFFECT_SIZE", "Tamaño del efecto", "INFERENTIAL", "COMPARE_GROUPS", 25, True, True, False),
    ("BENJAMINI_HOCHBERG", "Corrección Benjamini-Hochberg", "INFERENTIAL", None, 25, False, False, False),
    ("KMEANS", "K-means / clustering", "MULTIVARIATE", "KMEANS", 50, False, True, False),
    ("SILHOUETTE", "Silhouette", "MULTIVARIATE", "KMEANS", 50, False, True, False),
    ("LOGISTIC_REGRESSION", "Regresión logística", "PREDICTIVE", "LOGISTIC_REGRESSION", 50, False, True, False),
    ("ODDS_RATIO", "Odds Ratio + IC95%", "PREDICTIVE", "LOGISTIC_REGRESSION", 50, False, True, False),
    ("ROC_AUC", "AUC ROC", "PREDICTIVE", "LOGISTIC_REGRESSION", 50, False, True, False),
    ("CALIBRATION", "Calibración del modelo", "PREDICTIVE", "LOGISTIC_REGRESSION", 50, False, True, False),
    ("BALANCED_SCORECARD", "Balanced Scorecard", "STRATEGIC", None, None, False, False, False),
    ("KPI", "KPI y metas", "STRATEGIC", None, None, False, False, False),
    ("ALERTS", "Alertas", "STRATEGIC", None, None, False, False, False),
    ("TEMPORAL_TRACKING", "Seguimiento temporal", "STRATEGIC", None, 2, False, False, False),
]


def upgrade() -> None:
    op.add_column("instrument_versions", sa.Column("instrument_kind", sa.String(20), nullable=True), schema=SCHEMA)
    op.add_column("instrument_versions", sa.Column("total_questions", sa.Integer(), nullable=True), schema=SCHEMA)
    op.add_column("instrument_versions", sa.Column("psychosocial_questions", sa.Integer(), nullable=True), schema=SCHEMA)
    op.add_column("instrument_versions", sa.Column("dimension_count", sa.Integer(), nullable=True), schema=SCHEMA)
    op.add_column("instrument_versions", sa.Column("subdimension_count", sa.Integer(), nullable=False, server_default="0"), schema=SCHEMA)

    op.create_table(
        "analytics_plans",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema=SCHEMA,
    )
    op.create_table(
        "statistical_tools",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("min_sample_size", sa.Integer()),
        sa.Column("requires_groups", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_numeric", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requires_medium", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("analysis_method_code", sa.String(100)),
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema=SCHEMA,
    )
    op.create_table(
        "analytics_plan_tools",
        sa.Column("plan_id", sa.BigInteger(), nullable=False),
        sa.Column("tool_id", sa.BigInteger(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("configuration", sa.JSON(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["plan_id"], [f"{SCHEMA}.analytics_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], [f"{SCHEMA}.statistical_tools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plan_id", "tool_id"),
        schema=SCHEMA,
    )
    op.create_table(
        "organization_collaborator_codes",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("code_prefix", sa.String(20), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["organization_id"], [f"{SCHEMA}.organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], [f"{SCHEMA}.users.id"]),
        schema=SCHEMA,
    )
    op.add_column("studies", sa.Column("analytics_plan_id", sa.BigInteger(), nullable=True), schema=SCHEMA)
    op.create_foreign_key(
        "fk_studies_analytics_plan_id", "studies", "analytics_plans", ["analytics_plan_id"], ["id"],
        source_schema=SCHEMA, referent_schema=SCHEMA,
    )
    op.create_index(
        "uq_organizations_tax_id_normalized", "organizations", [sa.text("lower(btrim(tax_id))")],
        unique=True, schema=SCHEMA, postgresql_where=sa.text("tax_id IS NOT NULL AND btrim(tax_id) <> ''"),
    )

    bind = op.get_bind()
    bind.exec_driver_sql(
        """UPDATE colmena.instrument_versions
        SET instrument_kind = 'SHORT', total_questions = 42, psychosocial_questions = 31,
            dimension_count = 6, subdimension_count = 0
        WHERE config->>'censopas_version_kind' = 'SHORT' OR version_code ILIKE '%%SHORT%%';
        UPDATE colmena.instrument_versions
        SET instrument_kind = 'MEDIUM', total_questions = 112, psychosocial_questions = 69,
            dimension_count = 6, subdimension_count = 20
        WHERE config->>'censopas_version_kind' = 'MEDIUM' OR version_code ILIKE '%%MEDIUM%%';"""
    )
    bind.exec_driver_sql(
        """INSERT INTO colmena.analytics_plans (code, name, description, level)
        VALUES ('STANDARD', 'Estándar', 'Resultados CENSOPAS y análisis descriptivo.', 1),
               ('ADVANCED', 'Avanzado', 'Inferencia, comparaciones y confiabilidad.', 2),
               ('PREMIUM', 'Premium', 'Analítica multivariada y gestión estratégica.', 3)
        ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description,
          level = EXCLUDED.level, is_active = TRUE;"""
    )
    for tool in TOOLS:
        code, name, category, method, minimum, groups, numeric, medium = tool
        bind.execute(
            sa.text("""INSERT INTO colmena.statistical_tools
                (code, name, category, analysis_method_code, min_sample_size,
                 requires_groups, requires_numeric, requires_medium, is_official)
                VALUES (:code, :name, :category, :method, :minimum, :groups, :numeric, :medium, TRUE)
                ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category,
                  analysis_method_code = EXCLUDED.analysis_method_code, min_sample_size = EXCLUDED.min_sample_size,
                  requires_groups = EXCLUDED.requires_groups, requires_numeric = EXCLUDED.requires_numeric,
                  requires_medium = EXCLUDED.requires_medium, is_active = TRUE""").bindparams(
                code=code, name=name, category=category, method=method, minimum=minimum,
                groups=groups, numeric=numeric, medium=medium,
            )
        )
    bind.exec_driver_sql(
        """INSERT INTO colmena.analytics_plan_tools (plan_id, tool_id)
        SELECT p.id, t.id FROM colmena.analytics_plans p CROSS JOIN colmena.statistical_tools t
        WHERE p.code = 'STANDARD' AND t.code IN ('FREQUENCY','PERCENTAGE','CENSOPAS_DISTRIBUTION')
        ON CONFLICT DO NOTHING;
        INSERT INTO colmena.analytics_plan_tools (plan_id, tool_id)
        SELECT p.id, t.id FROM colmena.analytics_plans p CROSS JOIN colmena.statistical_tools t
        WHERE p.code = 'ADVANCED' AND t.code NOT IN ('KMEANS','SILHOUETTE','LOGISTIC_REGRESSION','ODDS_RATIO','ROC_AUC','CALIBRATION','BALANCED_SCORECARD','KPI','ALERTS','TEMPORAL_TRACKING')
        ON CONFLICT DO NOTHING;
        INSERT INTO colmena.analytics_plan_tools (plan_id, tool_id)
        SELECT p.id, t.id FROM colmena.analytics_plans p CROSS JOIN colmena.statistical_tools t
        WHERE p.code = 'PREMIUM'
        ON CONFLICT DO NOTHING;
        UPDATE colmena.studies SET analytics_plan_id = (SELECT id FROM colmena.analytics_plans WHERE code = 'STANDARD')
        WHERE analytics_plan_id IS NULL;"""
    )
    op.alter_column("instrument_versions", "subdimension_count", server_default=None, schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("uq_organizations_tax_id_normalized", table_name="organizations", schema=SCHEMA)
    op.drop_constraint("fk_studies_analytics_plan_id", "studies", type_="foreignkey", schema=SCHEMA)
    op.drop_column("studies", "analytics_plan_id", schema=SCHEMA)
    op.drop_table("organization_collaborator_codes", schema=SCHEMA)
    op.drop_table("analytics_plan_tools", schema=SCHEMA)
    op.drop_table("statistical_tools", schema=SCHEMA)
    op.drop_table("analytics_plans", schema=SCHEMA)
    for column in ("subdimension_count", "dimension_count", "psychosocial_questions", "total_questions", "instrument_kind"):
        op.drop_column("instrument_versions", column, schema=SCHEMA)
