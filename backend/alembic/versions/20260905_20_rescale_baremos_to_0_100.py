"""rescale scoring_configs + score_bands to the 0-100 scale (estilo COLMENA 2.0)

Antes cada config vivía en la escala cruda (suma de ítems, p.ej. 4-16) y sus
bandas estaban en esos números. Ahora los puntajes se normalizan a 0-100, así
que las bandas existentes se reescalan linealmente desde [score_min, score_max]
a [0, 100] y el rango del config pasa a 0-100.

Revision ID: 20260905_20
Revises: 20260904_19
Create Date: 2026-09-05 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260905_20"
down_revision: Union[str, Sequence[str], None] = "20260904_19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, score_min, score_max FROM scoring_configs "
            "WHERE score_max IS NOT NULL AND score_min IS NOT NULL "
            "AND NOT (score_min = 0 AND score_max = 100)"
        )
    ).fetchall()
    for config_id, score_min, score_max in rows:
        span = float(score_max) - float(score_min)
        if span <= 0:
            continue
        bands = conn.execute(
            sa.text("SELECT id, min_value, max_value FROM score_bands WHERE scoring_config_id = :c"),
            {"c": config_id},
        ).fetchall()
        for band_id, bmin, bmax in bands:
            new_min = round((float(bmin) - float(score_min)) / span * 100, 3)
            new_max = round((float(bmax) - float(score_min)) / span * 100, 3)
            conn.execute(
                sa.text("UPDATE score_bands SET min_value = :mn, max_value = :mx WHERE id = :i"),
                {"mn": new_min, "mx": new_max, "i": band_id},
            )
        conn.execute(
            sa.text("UPDATE scoring_configs SET score_min = 0, score_max = 100 WHERE id = :i"),
            {"i": config_id},
        )
    # Las puntuaciones ya calculadas quedan obsoletas (estaban en escala cruda);
    # se recalculan solas la próxima vez que se abra Resultados.
    conn.execute(sa.text("DELETE FROM response_scores"))


def downgrade() -> None:
    # Reescalado con pérdida: no se revierte automáticamente.
    pass
