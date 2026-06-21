"""create form domain

Revision ID: 20260505_02
Revises: 20260505_01
Create Date: 2026-05-05 21:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_02"
down_revision: Union[str, Sequence[str], None] = "20260505_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_variables",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("variable_role", sa.String(length=50), nullable=False, server_default="main"),
        sa.Column("measurement_level", sa.String(length=50), nullable=False, server_default="ordinal"),
        sa.Column("data_type", sa.String(length=50), nullable=False, server_default="numeric"),
        sa.Column("is_required_for_analysis", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_project_variables_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_variables")),
    )
    op.create_index(op.f("ix_project_variables_code"), "project_variables", ["code"], unique=False)
    op.create_index(op.f("ix_project_variables_deleted_at"), "project_variables", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_project_variables_name"), "project_variables", ["name"], unique=False)
    op.create_index(op.f("ix_project_variables_project_id"), "project_variables", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_variables_variable_role"), "project_variables", ["variable_role"], unique=False)

    op.create_table(
        "forms",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("public_slug", sa.String(length=255), nullable=True),
        sa.Column("allow_anonymous", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("collect_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collect_closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("thank_you_message", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_forms_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_forms")),
    )
    op.create_index(op.f("ix_forms_deleted_at"), "forms", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_forms_project_id"), "forms", ["project_id"], unique=False)
    op.create_index(op.f("ix_forms_public_slug"), "forms", ["public_slug"], unique=True)
    op.create_index(op.f("ix_forms_status"), "forms", ["status"], unique=False)

    op.create_table(
        "form_sections",
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_form_sections_form_id_forms")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_sections")),
    )
    op.create_index(op.f("ix_form_sections_deleted_at"), "form_sections", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_form_sections_form_id"), "form_sections", ["form_id"], unique=False)
    op.create_index(op.f("ix_form_sections_sort_order"), "form_sections", ["sort_order"], unique=False)

    op.create_table(
        "form_instruments",
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("project_variable_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("acronym", sa.String(length=50), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("response_scale_name", sa.String(length=255), nullable=True),
        sa.Column("scoring_method", sa.String(length=255), nullable=True),
        sa.Column("reverse_scoring_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_form_instruments_form_id_forms")),
        sa.ForeignKeyConstraint(
            ["project_variable_id"],
            ["project_variables.id"],
            name=op.f("fk_form_instruments_project_variable_id_project_variables"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_instruments")),
    )
    op.create_index(op.f("ix_form_instruments_deleted_at"), "form_instruments", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_form_instruments_form_id"), "form_instruments", ["form_id"], unique=False)
    op.create_index(op.f("ix_form_instruments_project_variable_id"), "form_instruments", ["project_variable_id"], unique=False)
    op.create_index(op.f("ix_form_instruments_sort_order"), "form_instruments", ["sort_order"], unique=False)

    op.create_table(
        "form_dimensions",
        sa.Column("instrument_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["form_instruments.id"],
            name=op.f("fk_form_dimensions_instrument_id_form_instruments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_dimensions")),
    )
    op.create_index(op.f("ix_form_dimensions_code"), "form_dimensions", ["code"], unique=False)
    op.create_index(op.f("ix_form_dimensions_deleted_at"), "form_dimensions", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_form_dimensions_instrument_id"), "form_dimensions", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_form_dimensions_sort_order"), "form_dimensions", ["sort_order"], unique=False)

    op.create_table(
        "form_questions",
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("section_id", sa.String(length=36), nullable=True),
        sa.Column("instrument_id", sa.String(length=36), nullable=True),
        sa.Column("dimension_id", sa.String(length=36), nullable=True),
        sa.Column("project_variable_id", sa.String(length=36), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column("question_type", sa.String(length=50), nullable=False),
        sa.Column("question_role", sa.String(length=50), nullable=False, server_default="item"),
        sa.Column("measurement_level", sa.String(length=50), nullable=False, server_default="ordinal"),
        sa.Column("data_type", sa.String(length=50), nullable=False, server_default="numeric"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_scored", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_reverse_scored", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("min_value", sa.Float(), nullable=True),
        sa.Column("max_value", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("validation_json", sa.JSON(), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dimension_id"], ["form_dimensions.id"], name=op.f("fk_form_questions_dimension_id_form_dimensions")),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_form_questions_form_id_forms")),
        sa.ForeignKeyConstraint(["instrument_id"], ["form_instruments.id"], name=op.f("fk_form_questions_instrument_id_form_instruments")),
        sa.ForeignKeyConstraint(["project_variable_id"], ["project_variables.id"], name=op.f("fk_form_questions_project_variable_id_project_variables")),
        sa.ForeignKeyConstraint(["section_id"], ["form_sections.id"], name=op.f("fk_form_questions_section_id_form_sections")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_questions")),
    )
    op.create_index(op.f("ix_form_questions_code"), "form_questions", ["code"], unique=False)
    op.create_index(op.f("ix_form_questions_deleted_at"), "form_questions", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_form_questions_dimension_id"), "form_questions", ["dimension_id"], unique=False)
    op.create_index(op.f("ix_form_questions_form_id"), "form_questions", ["form_id"], unique=False)
    op.create_index(op.f("ix_form_questions_instrument_id"), "form_questions", ["instrument_id"], unique=False)
    op.create_index(op.f("ix_form_questions_project_variable_id"), "form_questions", ["project_variable_id"], unique=False)
    op.create_index(op.f("ix_form_questions_question_type"), "form_questions", ["question_type"], unique=False)
    op.create_index(op.f("ix_form_questions_section_id"), "form_questions", ["section_id"], unique=False)
    op.create_index(op.f("ix_form_questions_sort_order"), "form_questions", ["sort_order"], unique=False)

    op.create_table(
        "form_question_options",
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["form_questions.id"],
            name=op.f("fk_form_question_options_question_id_form_questions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_question_options")),
    )
    op.create_index(op.f("ix_form_question_options_deleted_at"), "form_question_options", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_form_question_options_question_id"), "form_question_options", ["question_id"], unique=False)
    op.create_index(op.f("ix_form_question_options_sort_order"), "form_question_options", ["sort_order"], unique=False)

    op.create_table(
        "form_responses",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("form_id", sa.String(length=36), nullable=False),
        sa.Column("respondent_code", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="complete"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="internal"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["form_id"], ["forms.id"], name=op.f("fk_form_responses_form_id_forms")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name=op.f("fk_form_responses_project_id_projects")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_responses")),
    )
    op.create_index(op.f("ix_form_responses_deleted_at"), "form_responses", ["deleted_at"], unique=False)
    op.create_index(op.f("ix_form_responses_form_id"), "form_responses", ["form_id"], unique=False)
    op.create_index(op.f("ix_form_responses_project_id"), "form_responses", ["project_id"], unique=False)
    op.create_index(op.f("ix_form_responses_respondent_code"), "form_responses", ["respondent_code"], unique=False)
    op.create_index(op.f("ix_form_responses_status"), "form_responses", ["status"], unique=False)

    op.create_table(
        "form_answers",
        sa.Column("response_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("option_id", sa.String(length=36), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Float(), nullable=True),
        sa.Column("value_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("score_value", sa.Float(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["option_id"], ["form_question_options.id"], name=op.f("fk_form_answers_option_id_form_question_options")),
        sa.ForeignKeyConstraint(["question_id"], ["form_questions.id"], name=op.f("fk_form_answers_question_id_form_questions")),
        sa.ForeignKeyConstraint(["response_id"], ["form_responses.id"], name=op.f("fk_form_answers_response_id_form_responses")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_form_answers")),
    )
    op.create_index(op.f("ix_form_answers_option_id"), "form_answers", ["option_id"], unique=False)
    op.create_index(op.f("ix_form_answers_question_id"), "form_answers", ["question_id"], unique=False)
    op.create_index(op.f("ix_form_answers_response_id"), "form_answers", ["response_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_form_answers_response_id"), table_name="form_answers")
    op.drop_index(op.f("ix_form_answers_question_id"), table_name="form_answers")
    op.drop_index(op.f("ix_form_answers_option_id"), table_name="form_answers")
    op.drop_table("form_answers")

    op.drop_index(op.f("ix_form_responses_status"), table_name="form_responses")
    op.drop_index(op.f("ix_form_responses_respondent_code"), table_name="form_responses")
    op.drop_index(op.f("ix_form_responses_project_id"), table_name="form_responses")
    op.drop_index(op.f("ix_form_responses_form_id"), table_name="form_responses")
    op.drop_index(op.f("ix_form_responses_deleted_at"), table_name="form_responses")
    op.drop_table("form_responses")

    op.drop_index(op.f("ix_form_question_options_sort_order"), table_name="form_question_options")
    op.drop_index(op.f("ix_form_question_options_question_id"), table_name="form_question_options")
    op.drop_index(op.f("ix_form_question_options_deleted_at"), table_name="form_question_options")
    op.drop_table("form_question_options")

    op.drop_index(op.f("ix_form_questions_sort_order"), table_name="form_questions")
    op.drop_index(op.f("ix_form_questions_section_id"), table_name="form_questions")
    op.drop_index(op.f("ix_form_questions_question_type"), table_name="form_questions")
    op.drop_index(op.f("ix_form_questions_project_variable_id"), table_name="form_questions")
    op.drop_index(op.f("ix_form_questions_instrument_id"), table_name="form_questions")
    op.drop_index(op.f("ix_form_questions_form_id"), table_name="form_questions")
    op.drop_index(op.f("ix_form_questions_dimension_id"), table_name="form_questions")
    op.drop_index(op.f("ix_form_questions_deleted_at"), table_name="form_questions")
    op.drop_index(op.f("ix_form_questions_code"), table_name="form_questions")
    op.drop_table("form_questions")

    op.drop_index(op.f("ix_form_dimensions_sort_order"), table_name="form_dimensions")
    op.drop_index(op.f("ix_form_dimensions_instrument_id"), table_name="form_dimensions")
    op.drop_index(op.f("ix_form_dimensions_deleted_at"), table_name="form_dimensions")
    op.drop_index(op.f("ix_form_dimensions_code"), table_name="form_dimensions")
    op.drop_table("form_dimensions")

    op.drop_index(op.f("ix_form_instruments_sort_order"), table_name="form_instruments")
    op.drop_index(op.f("ix_form_instruments_project_variable_id"), table_name="form_instruments")
    op.drop_index(op.f("ix_form_instruments_form_id"), table_name="form_instruments")
    op.drop_index(op.f("ix_form_instruments_deleted_at"), table_name="form_instruments")
    op.drop_table("form_instruments")

    op.drop_index(op.f("ix_form_sections_sort_order"), table_name="form_sections")
    op.drop_index(op.f("ix_form_sections_form_id"), table_name="form_sections")
    op.drop_index(op.f("ix_form_sections_deleted_at"), table_name="form_sections")
    op.drop_table("form_sections")

    op.drop_index(op.f("ix_forms_status"), table_name="forms")
    op.drop_index(op.f("ix_forms_public_slug"), table_name="forms")
    op.drop_index(op.f("ix_forms_project_id"), table_name="forms")
    op.drop_index(op.f("ix_forms_deleted_at"), table_name="forms")
    op.drop_table("forms")

    op.drop_index(op.f("ix_project_variables_variable_role"), table_name="project_variables")
    op.drop_index(op.f("ix_project_variables_project_id"), table_name="project_variables")
    op.drop_index(op.f("ix_project_variables_name"), table_name="project_variables")
    op.drop_index(op.f("ix_project_variables_deleted_at"), table_name="project_variables")
    op.drop_index(op.f("ix_project_variables_code"), table_name="project_variables")
    op.drop_table("project_variables")
