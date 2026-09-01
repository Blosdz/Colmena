"""Roles de ítems, secciones, baremos multinivel y scoring por sesión.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

SCHEMA = "colmena"


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("question_role", sa.String(length=30), nullable=False, server_default="DESCRIPTIVE"),
        schema=SCHEMA,
    )
    op.execute(
        "UPDATE colmena.questions SET question_role = 'SCORED' "
        "WHERE is_scored IS TRUE OR question_type = 'LIKERT'"
    )
    op.create_check_constraint(
        "ck_questions_question_role",
        "questions",
        "question_role IN ('SCORED', 'EXOGENOUS', 'DESCRIPTIVE')",
        schema=SCHEMA,
    )

    op.add_column(
        "survey_sections",
        sa.Column("section_kind", sa.String(length=30), nullable=False, server_default="INSTRUMENT"),
        schema=SCHEMA,
    )

    op.create_table(
        "barem_bands",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("barem_id", sa.BigInteger(), nullable=False),
        sa.Column("construct_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("min_value", sa.Numeric(), nullable=False),
        sa.Column("max_value", sa.Numeric(), nullable=False),
        sa.Column("severity_order", sa.Integer(), nullable=False),
        sa.Column("interpretation", sa.Text()),
        sa.Column("color_hint", sa.String(length=30)),
        sa.Column("classification_code", sa.String(length=80)),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["barem_id"], ["colmena.barems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["construct_id"], ["colmena.constructs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("barem_id", "construct_id", "severity_order"),
        sa.CheckConstraint("min_value <= max_value", name="ck_barem_bands_range"),
        schema=SCHEMA,
    )

    # Conserva la configuración de tres niveles ya creada con cut_1/cut_2.
    op.execute(
        """
        INSERT INTO colmena.barem_bands
          (barem_id, construct_id, code, label, min_value, max_value,
           severity_order, color_hint, classification_code, metadata)
        SELECT barem_id, construct_id, 'NIVEL_1',
          CASE WHEN direction = 'LOWER_BETTER' THEN favorable_label ELSE unfavorable_label END,
          0, cut_1, 1, '#ef4444',
          CASE WHEN direction = 'LOWER_BETTER' THEN 'FAVORABLE' ELSE 'UNFAVORABLE' END,
          '{}'::jsonb
        FROM colmena.barem_cutoffs WHERE cut_1 IS NOT NULL AND cut_2 IS NOT NULL
        UNION ALL
        SELECT barem_id, construct_id, 'NIVEL_2', intermediate_label,
          cut_1, cut_2, 2, '#f59e0b', 'INTERMEDIATE', '{}'::jsonb
        FROM colmena.barem_cutoffs WHERE cut_1 IS NOT NULL AND cut_2 IS NOT NULL
        UNION ALL
        SELECT barem_id, construct_id, 'NIVEL_3',
          CASE WHEN direction = 'LOWER_BETTER' THEN unfavorable_label ELSE favorable_label END,
          cut_2, 100, 3, '#22c55e',
          CASE WHEN direction = 'LOWER_BETTER' THEN 'UNFAVORABLE' ELSE 'FAVORABLE' END,
          '{}'::jsonb
        FROM colmena.barem_cutoffs WHERE cut_1 IS NOT NULL AND cut_2 IS NOT NULL
        """
    )

    op.create_table(
        "construct_scores",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("study_id", sa.BigInteger(), nullable=False),
        sa.Column("analysis_run_id", sa.BigInteger(), nullable=False),
        sa.Column("response_session_id", sa.BigInteger(), nullable=False),
        sa.Column("construct_id", sa.BigInteger(), nullable=False),
        sa.Column("barem_id", sa.BigInteger()),
        sa.Column("band_id", sa.BigInteger()),
        sa.Column("n_answered", sa.Integer(), nullable=False),
        sa.Column("n_total", sa.Integer(), nullable=False),
        sa.Column("completion_pct", sa.Numeric(7, 4), nullable=False),
        sa.Column("raw_score", sa.Numeric()),
        sa.Column("score_0_100", sa.Numeric()),
        sa.Column("classification", sa.String(length=120)),
        sa.Column("algorithm_version", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["study_id"], ["colmena.studies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["colmena.analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["response_session_id"], ["colmena.response_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["construct_id"], ["colmena.constructs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["barem_id"], ["colmena.barems.id"]),
        sa.ForeignKeyConstraint(["band_id"], ["colmena.barem_bands.id"]),
        sa.UniqueConstraint("analysis_run_id", "response_session_id", "construct_id"),
        sa.CheckConstraint(
            "completion_pct >= 0 AND completion_pct <= 100",
            name="ck_construct_scores_completion",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_construct_scores_study_construct",
        "construct_scores",
        ["study_id", "construct_id"],
        schema=SCHEMA,
    )
    op.execute(
        """
        INSERT INTO colmena.analysis_methods (code, name, category, engine, enabled, config)
        VALUES
          ('NORMALITY', 'Pruebas de normalidad', 'DESCRIPTIVA', 'PYTHON', TRUE, '{}'::jsonb),
          ('SPEARMAN_MATRIX', 'Matriz de correlación de Spearman', 'INFERENCIAL', 'PYTHON', TRUE, '{}'::jsonb),
          ('CONSTRUCT_COMPARE_GROUPS', 'Comparación de constructos por grupos', 'INFERENCIAL', 'PYTHON', TRUE, '{}'::jsonb),
          ('LIKERT_SCORING', 'Puntuación Likert y baremos', 'PUNTUACIÓN', 'PYTHON', TRUE, '{}'::jsonb)
        ON CONFLICT (code) DO UPDATE SET
          name = EXCLUDED.name,
          category = EXCLUDED.category,
          enabled = TRUE
        """
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM colmena.analysis_methods WHERE code IN "
        "('NORMALITY', 'SPEARMAN_MATRIX', 'CONSTRUCT_COMPARE_GROUPS', 'LIKERT_SCORING')"
    )
    op.drop_index("ix_construct_scores_study_construct", table_name="construct_scores", schema=SCHEMA)
    op.drop_table("construct_scores", schema=SCHEMA)
    op.drop_table("barem_bands", schema=SCHEMA)
    op.drop_column("survey_sections", "section_kind", schema=SCHEMA)
    op.drop_constraint("ck_questions_question_role", "questions", type_="check", schema=SCHEMA)
    op.drop_column("questions", "question_role", schema=SCHEMA)
