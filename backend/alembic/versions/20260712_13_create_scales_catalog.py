"""create scales catalog (scales + scale_options) and seed system presets

Las escalas dejan de vivir copiadas en cada pregunta: pasan a ser un catálogo
que las preguntas referencian (form_questions.scale_id) y que el instrumento
puede fijar como global (form_instruments.default_scale_id). Se siembran los
presets del sistema (project_id NULL) que hoy están hardcodeados en el frontend.

Revision ID: 20260712_13
Revises: 20260712_12
Create Date: 2026-07-12 00:30:00
"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260712_13"
down_revision: Union[str, Sequence[str], None] = "20260712_12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NOW = datetime(2026, 7, 12, 0, 30, 0, tzinfo=timezone.utc)


# (id, name, scale_kind, render_style, [labels...])  → value = índice + 1 (salvo EVA/NPS)
_PRESETS = [
    ("sys_frecuencia_3", "Frecuencia · 3 puntos", "frecuencia", "radio",
     ["Nunca", "A veces", "Siempre"]),
    ("sys_frecuencia_5", "Frecuencia · 5 puntos", "frecuencia", "radio",
     ["Nunca", "Casi nunca", "A veces", "Casi siempre", "Siempre"]),
    ("sys_frecuencia_7", "Frecuencia · 7 puntos", "frecuencia", "radio",
     ["Nunca", "Muy pocas veces", "Pocas veces", "A veces", "Muchas veces", "Casi siempre", "Siempre"]),
    ("sys_intensidad_5", "Intensidad · 5 puntos", "intensidad", "radio",
     ["Nada", "Poco", "Moderadamente", "Bastante", "Muchísimo"]),
    ("sys_acuerdo_5", "Acuerdo · 5 puntos", "acuerdo", "radio",
     ["Totalmente en desacuerdo", "En desacuerdo", "Ni de acuerdo ni en desacuerdo",
      "De acuerdo", "Totalmente de acuerdo"]),
    ("sys_dificultad_5", "Dificultad · 5 puntos", "dificultad", "radio",
     ["Ninguna dificultad", "Poca dificultad", "Dificultad moderada",
      "Mucha dificultad", "No puedo hacerlo"]),
    ("sys_satisfaccion_5", "Satisfacción · 5 puntos", "satisfaccion", "radio",
     ["Muy insatisfecho", "Insatisfecho", "Neutral", "Satisfecho", "Muy satisfecho"]),
]

# Escalas numéricas (value = número mostrado, empieza en 0)
_NUMERIC_PRESETS = [
    ("sys_eva_0_10", "Escala Visual Análoga (EVA 0–10)", "intensidad", "slider_line", 0, 10,
     "Nada", "Máximo"),
    ("sys_nps_0_10", "NPS 0–10", "satisfaccion", "nps", 0, 10, "Nada probable", "Muy probable"),
]


def _scales_table() -> sa.Table:
    return sa.table(
        "scales",
        sa.column("id", sa.String),
        sa.column("project_id", sa.String),
        sa.column("name", sa.String),
        sa.column("scale_kind", sa.String),
        sa.column("render_style", sa.String),
        sa.column("points", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
        sa.column("deleted_at", sa.DateTime),
    )


def _options_table() -> sa.Table:
    return sa.table(
        "scale_options",
        sa.column("id", sa.String),
        sa.column("scale_id", sa.String),
        sa.column("value", sa.Integer),
        sa.column("label", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )


def upgrade() -> None:
    op.create_table(
        "scales",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("scale_kind", sa.String(length=30), nullable=False, server_default="personalizada"),
        sa.Column("render_style", sa.String(length=30), nullable=False, server_default="radio"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_scales_project_id", "scales", ["project_id"])
    op.create_index("ix_scales_deleted_at", "scales", ["deleted_at"])

    op.create_table(
        "scale_options",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "scale_id",
            sa.String(length=36),
            sa.ForeignKey("scales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scale_options_scale_id", "scale_options", ["scale_id"])

    # Columnas de referencia (planas: SQLite no soporta ADD COLUMN con FK constraint).
    op.add_column("form_questions", sa.Column("scale_id", sa.String(length=36), nullable=True))
    op.create_index("ix_form_questions_scale_id", "form_questions", ["scale_id"])
    op.add_column("form_instruments", sa.Column("default_scale_id", sa.String(length=36), nullable=True))
    op.create_index("ix_form_instruments_default_scale_id", "form_instruments", ["default_scale_id"])

    # ── Seed de presets del sistema ──
    scale_rows = []
    option_rows = []

    for scale_id, name, kind, render, labels in _PRESETS:
        scale_rows.append({
            "id": scale_id, "project_id": None, "name": name, "scale_kind": kind,
            "render_style": render, "points": len(labels),
            "created_at": _NOW, "updated_at": _NOW, "deleted_at": None,
        })
        for index, label in enumerate(labels):
            option_rows.append({
                "id": f"{scale_id}_o{index}", "scale_id": scale_id, "value": index + 1,
                "label": label, "sort_order": index, "created_at": _NOW, "updated_at": _NOW,
            })

    for scale_id, name, kind, render, lo, hi, low_label, high_label in _NUMERIC_PRESETS:
        points = hi - lo + 1
        scale_rows.append({
            "id": scale_id, "project_id": None, "name": name, "scale_kind": kind,
            "render_style": render, "points": points,
            "created_at": _NOW, "updated_at": _NOW, "deleted_at": None,
        })
        for offset, num in enumerate(range(lo, hi + 1)):
            if num == lo:
                label = f"{num} · {low_label}"
            elif num == hi:
                label = f"{num} · {high_label}"
            else:
                label = str(num)
            option_rows.append({
                "id": f"{scale_id}_o{offset}", "scale_id": scale_id, "value": num,
                "label": label, "sort_order": offset, "created_at": _NOW, "updated_at": _NOW,
            })

    op.bulk_insert(_scales_table(), scale_rows)
    op.bulk_insert(_options_table(), option_rows)


def downgrade() -> None:
    op.drop_index("ix_form_instruments_default_scale_id", table_name="form_instruments")
    op.drop_column("form_instruments", "default_scale_id")
    op.drop_index("ix_form_questions_scale_id", table_name="form_questions")
    op.drop_column("form_questions", "scale_id")
    op.drop_index("ix_scale_options_scale_id", table_name="scale_options")
    op.drop_table("scale_options")
    op.drop_index("ix_scales_deleted_at", table_name="scales")
    op.drop_index("ix_scales_project_id", table_name="scales")
    op.drop_table("scales")
