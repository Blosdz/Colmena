"""create scoring advanced

Revision ID: 20260509_06
Revises: 20260506_05
Create Date: 2026-05-09 09:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260509_06"
down_revision: Union[str, Sequence[str], None] = "20260506_05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scoring_configs",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("instrument_id", sa.String(length=36), nullable=True),
        sa.Column("dimension_id", sa.String(length=36), nullable=True),
        sa.Column("project_variable_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("scoring_level", sa.String(length=50), nullable=False),
        sa.Column("aggregation_method", sa.String(length=50), nullable=False, server_default="mean"),
        sa.Column("missing_policy", sa.String(length=50), nullable=False, server_default="allow_partial"),
        sa.Column("min_answered_items", sa.Integer(), nullable=True),
        sa.Column("min_completion_percent", sa.Float(), nullable=True),
        sa.Column("reverse_scoring_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("score_min", sa.Float(), nullable=True),
        sa.Column("score_max", sa.Float(), nullable=True),
        sa.Column("interpretation_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dimension_id"], ["form_dimensions.id"], name=op.f("fk_scoring_configs_dimension_id_form_dimensions")),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_scoring_configs_form_id_forms")),
        sa.ForeignKeyConstraint(["instrument_id"], ["form_instruments.id"], name=op.f("fk_scoring_configs_instrument_id_form_instruments")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_scoring_configs_project_id_projects")),
        sa.ForeignKeyConstraint(["project_variable_id"], ["project_variables.id"], name=op.f("fk_scoring_configs_project_variable_id_project_variables")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scoring_configs")),
    )
    op.create_index(op.f("ix_scoring_configs_project_id"), "scoring_configs", ["project_id"], unique=False)
    op.create_index(op.f("ix_scoring_configs_form_id"), "scoring_configs", ["form_id"], unique=False)
    op.create_index(op.f("ix_scoring_configs_instrument_id"), "scoring_configs", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_scoring_configs_dimension_id"), "scoring_configs", ["dimension_id"], unique=False)
    op.create_index(op.f("ix_scoring_configs_project_variable_id"), "scoring_configs", ["project_variable_id"], unique=False)
    op.create_index(op.f("ix_scoring_configs_code"), "scoring_configs", ["code"], unique=False)
    op.create_index(op.f("ix_scoring_configs_scoring_level"), "scoring_configs", ["scoring_level"], unique=False)
    op.create_index(op.f("ix_scoring_configs_deleted_at"), "scoring_configs", ["deleted_at"], unique=False)

    op.create_table(
        "score_bands",
        sa.Column("scoring_config_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("min_value", sa.Float(), nullable=False),
        sa.Column("max_value", sa.Float(), nullable=False),
        sa.Column("interpretation", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("severity_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("color_hint", sa.String(length=50), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["scoring_config_id"], ["scoring_configs.id"], name=op.f("fk_score_bands_scoring_config_id_scoring_configs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_score_bands")),
    )
    op.create_index(op.f("ix_score_bands_scoring_config_id"), "score_bands", ["scoring_config_id"], unique=False)
    op.create_index(op.f("ix_score_bands_code"), "score_bands", ["code"], unique=False)
    op.create_index(op.f("ix_score_bands_deleted_at"), "score_bands", ["deleted_at"], unique=False)

    op.create_table(
        "control_scales",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("instrument_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("control_type", sa.String(length=50), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("comparison_operator", sa.String(length=10), nullable=True),
        sa.Column("flag_level", sa.String(length=20), nullable=False, server_default="warning"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_control_scales_form_id_forms")),
        sa.ForeignKeyConstraint(["instrument_id"], ["form_instruments.id"], name=op.f("fk_control_scales_instrument_id_form_instruments")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_control_scales_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_control_scales")),
    )
    op.create_index(op.f("ix_control_scales_project_id"), "control_scales", ["project_id"], unique=False)
    op.create_index(op.f("ix_control_scales_form_id"), "control_scales", ["form_id"], unique=False)
    op.create_index(op.f("ix_control_scales_instrument_id"), "control_scales", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_control_scales_code"), "control_scales", ["code"], unique=False)
    op.create_index(op.f("ix_control_scales_control_type"), "control_scales", ["control_type"], unique=False)
    op.create_index(op.f("ix_control_scales_deleted_at"), "control_scales", ["deleted_at"], unique=False)

    op.create_table(
        "control_scale_items",
        sa.Column("control_scale_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("expected_option_id", sa.String(length=36), nullable=True),
        sa.Column("expected_value_text", sa.Text(), nullable=True),
        sa.Column("expected_value_number", sa.Float(), nullable=True),
        sa.Column("fail_if_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("pair_group", sa.String(length=100), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["control_scale_id"], ["control_scales.id"], name=op.f("fk_control_scale_items_control_scale_id_control_scales")),
        sa.ForeignKeyConstraint(["expected_option_id"], ["form_question_options.id"], name=op.f("fk_control_scale_items_expected_option_id_form_question_options")),
        sa.ForeignKeyConstraint(["question_id"], ["form_questions.id"], name=op.f("fk_control_scale_items_question_id_form_questions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_control_scale_items")),
    )
    op.create_index(op.f("ix_control_scale_items_control_scale_id"), "control_scale_items", ["control_scale_id"], unique=False)
    op.create_index(op.f("ix_control_scale_items_question_id"), "control_scale_items", ["question_id"], unique=False)
    op.create_index(op.f("ix_control_scale_items_expected_option_id"), "control_scale_items", ["expected_option_id"], unique=False)
    op.create_index(op.f("ix_control_scale_items_pair_group"), "control_scale_items", ["pair_group"], unique=False)
    op.create_index(op.f("ix_control_scale_items_deleted_at"), "control_scale_items", ["deleted_at"], unique=False)

    op.create_table(
        "response_scores",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("response_id", sa.String(length=36), nullable=False),
        sa.Column("scoring_config_id", sa.String(length=36), nullable=False),
        sa.Column("instrument_id", sa.String(length=36), nullable=True),
        sa.Column("dimension_id", sa.String(length=36), nullable=True),
        sa.Column("project_variable_id", sa.String(length=36), nullable=True),
        sa.Column("raw_score", sa.Float(), nullable=True),
        sa.Column("mean_score", sa.Float(), nullable=True),
        sa.Column("weighted_score", sa.Float(), nullable=True),
        sa.Column("final_score", sa.Float(), nullable=True),
        sa.Column("answered_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_percent", sa.Float(), nullable=True),
        sa.Column("band_id", sa.String(length=36), nullable=True),
        sa.Column("band_label", sa.String(length=100), nullable=True),
        sa.Column("interpretation", sa.Text(), nullable=True),
        sa.Column("validity_status", sa.String(length=20), nullable=False, server_default="valid"),
        sa.Column("warnings_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["band_id"], ["score_bands.id"], name=op.f("fk_response_scores_band_id_score_bands")),
        sa.ForeignKeyConstraint(["dimension_id"], ["form_dimensions.id"], name=op.f("fk_response_scores_dimension_id_form_dimensions")),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_response_scores_form_id_forms")),
        sa.ForeignKeyConstraint(["instrument_id"], ["form_instruments.id"], name=op.f("fk_response_scores_instrument_id_form_instruments")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_response_scores_project_id_projects")),
        sa.ForeignKeyConstraint(["project_variable_id"], ["project_variables.id"], name=op.f("fk_response_scores_project_variable_id_project_variables")),
        sa.ForeignKeyConstraint(["response_id"], ["form_responses.id"], name=op.f("fk_response_scores_response_id_form_responses")),
        sa.ForeignKeyConstraint(["scoring_config_id"], ["scoring_configs.id"], name=op.f("fk_response_scores_scoring_config_id_scoring_configs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_response_scores")),
        sa.UniqueConstraint("response_id", "scoring_config_id", name="uq_response_score_config"),
    )
    op.create_index(op.f("ix_response_scores_project_id"), "response_scores", ["project_id"], unique=False)
    op.create_index(op.f("ix_response_scores_form_id"), "response_scores", ["form_id"], unique=False)
    op.create_index(op.f("ix_response_scores_response_id"), "response_scores", ["response_id"], unique=False)
    op.create_index(op.f("ix_response_scores_scoring_config_id"), "response_scores", ["scoring_config_id"], unique=False)
    op.create_index(op.f("ix_response_scores_instrument_id"), "response_scores", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_response_scores_dimension_id"), "response_scores", ["dimension_id"], unique=False)
    op.create_index(op.f("ix_response_scores_project_variable_id"), "response_scores", ["project_variable_id"], unique=False)
    op.create_index(op.f("ix_response_scores_band_id"), "response_scores", ["band_id"], unique=False)

    op.create_table(
        "response_control_flags",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("response_id", sa.String(length=36), nullable=False),
        sa.Column("control_scale_id", sa.String(length=36), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("flag_status", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["control_scale_id"], ["control_scales.id"], name=op.f("fk_response_control_flags_control_scale_id_control_scales")),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_response_control_flags_form_id_forms")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_response_control_flags_project_id_projects")),
        sa.ForeignKeyConstraint(["response_id"], ["form_responses.id"], name=op.f("fk_response_control_flags_response_id_form_responses")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_response_control_flags")),
        sa.UniqueConstraint("response_id", "control_scale_id", name="uq_response_control_scale"),
    )
    op.create_index(op.f("ix_response_control_flags_project_id"), "response_control_flags", ["project_id"], unique=False)
    op.create_index(op.f("ix_response_control_flags_form_id"), "response_control_flags", ["form_id"], unique=False)
    op.create_index(op.f("ix_response_control_flags_response_id"), "response_control_flags", ["response_id"], unique=False)
    op.create_index(op.f("ix_response_control_flags_control_scale_id"), "response_control_flags", ["control_scale_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_response_control_flags_control_scale_id"), table_name="response_control_flags")
    op.drop_index(op.f("ix_response_control_flags_response_id"), table_name="response_control_flags")
    op.drop_index(op.f("ix_response_control_flags_form_id"), table_name="response_control_flags")
    op.drop_index(op.f("ix_response_control_flags_project_id"), table_name="response_control_flags")
    op.drop_table("response_control_flags")

    op.drop_index(op.f("ix_response_scores_band_id"), table_name="response_scores")
    op.drop_index(op.f("ix_response_scores_project_variable_id"), table_name="response_scores")
    op.drop_index(op.f("ix_response_scores_dimension_id"), table_name="response_scores")
    op.drop_index(op.f("ix_response_scores_instrument_id"), table_name="response_scores")
    op.drop_index(op.f("ix_response_scores_scoring_config_id"), table_name="response_scores")
    op.drop_index(op.f("ix_response_scores_response_id"), table_name="response_scores")
    op.drop_index(op.f("ix_response_scores_form_id"), table_name="response_scores")
    op.drop_index(op.f("ix_response_scores_project_id"), table_name="response_scores")
    op.drop_table("response_scores")

    op.drop_index(op.f("ix_control_scale_items_deleted_at"), table_name="control_scale_items")
    op.drop_index(op.f("ix_control_scale_items_pair_group"), table_name="control_scale_items")
    op.drop_index(op.f("ix_control_scale_items_expected_option_id"), table_name="control_scale_items")
    op.drop_index(op.f("ix_control_scale_items_question_id"), table_name="control_scale_items")
    op.drop_index(op.f("ix_control_scale_items_control_scale_id"), table_name="control_scale_items")
    op.drop_table("control_scale_items")

    op.drop_index(op.f("ix_control_scales_deleted_at"), table_name="control_scales")
    op.drop_index(op.f("ix_control_scales_control_type"), table_name="control_scales")
    op.drop_index(op.f("ix_control_scales_code"), table_name="control_scales")
    op.drop_index(op.f("ix_control_scales_instrument_id"), table_name="control_scales")
    op.drop_index(op.f("ix_control_scales_form_id"), table_name="control_scales")
    op.drop_index(op.f("ix_control_scales_project_id"), table_name="control_scales")
    op.drop_table("control_scales")

    op.drop_index(op.f("ix_score_bands_deleted_at"), table_name="score_bands")
    op.drop_index(op.f("ix_score_bands_code"), table_name="score_bands")
    op.drop_index(op.f("ix_score_bands_scoring_config_id"), table_name="score_bands")
    op.drop_table("score_bands")

    op.drop_index(op.f("ix_scoring_configs_deleted_at"), table_name="scoring_configs")
    op.drop_index(op.f("ix_scoring_configs_scoring_level"), table_name="scoring_configs")
    op.drop_index(op.f("ix_scoring_configs_code"), table_name="scoring_configs")
    op.drop_index(op.f("ix_scoring_configs_project_variable_id"), table_name="scoring_configs")
    op.drop_index(op.f("ix_scoring_configs_dimension_id"), table_name="scoring_configs")
    op.drop_index(op.f("ix_scoring_configs_instrument_id"), table_name="scoring_configs")
    op.drop_index(op.f("ix_scoring_configs_form_id"), table_name="scoring_configs")
    op.drop_index(op.f("ix_scoring_configs_project_id"), table_name="scoring_configs")
    op.drop_table("scoring_configs")
