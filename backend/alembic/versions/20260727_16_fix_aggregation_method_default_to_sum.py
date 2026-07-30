"""fix aggregation_method default from mean to sum

Migracion de datos (no de schema): el default de `aggregation_method` en
`ScoringConfig` cambio de "mean" a "sum" en el codigo (la regla estadistica
correcta para un puntaje de dimension/instrumento es la SUMA de items, no el
promedio, salvo que la tesis indique lo contrario). Las filas creadas antes
del fix tienen "mean" guardado explicitamente y no se actualizan solo por
cambiar el default de Python en un INSERT nuevo, por eso se necesita este
UPDATE retroactivo.

La reversion es aproximada: no distingue las filas que ya eran "sum" antes de
esta migracion de las que fueron migradas desde "mean", por lo que un
downgrade posterior a un upgrade con datos nuevos podria revertir filas que
nunca fueron "mean" originalmente.

Revision ID: 20260727_16
Revises: 20260726_15
Create Date: 2026-07-27 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260727_16"
down_revision: Union[str, Sequence[str], None] = "20260726_15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


scoring_configs = sa.table(
    "scoring_configs",
    sa.column("aggregation_method", sa.String),
)


def upgrade() -> None:
    op.execute(
        scoring_configs.update()
        .where(scoring_configs.c.aggregation_method == "mean")
        .values(aggregation_method="sum")
    )


def downgrade() -> None:
    op.execute(
        scoring_configs.update()
        .where(scoring_configs.c.aggregation_method == "sum")
        .values(aggregation_method="mean")
    )
