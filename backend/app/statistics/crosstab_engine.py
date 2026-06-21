import pandas as pd

from app.schemas.descriptive import CrosstabCellRead


def _round(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    return round(float(value), decimals)


def build_crosstab(
    dataframe: pd.DataFrame,
    row_column: str,
    column_column: str,
    *,
    decimals: int = 3,
) -> tuple[list[str | None], list[str | None], list[CrosstabCellRead], int]:
    filtered = dataframe[[row_column, column_column]].copy()
    filtered = filtered.dropna(subset=[row_column, column_column], how="any")
    total_n = int(len(filtered))
    if total_n == 0:
        return [], [], [], 0

    filtered[row_column] = filtered[row_column].astype(object)
    filtered[column_column] = filtered[column_column].astype(object)
    table = pd.crosstab(filtered[row_column], filtered[column_column], dropna=False)

    row_labels = table.index.tolist()
    column_labels = table.columns.tolist()
    cells: list[CrosstabCellRead] = []

    for row_label in row_labels:
        row_total = int(table.loc[row_label].sum())
        for column_label in column_labels:
            column_total = int(table[column_label].sum())
            count = int(table.loc[row_label, column_label])
            cells.append(
                CrosstabCellRead(
                    row_value=row_label,
                    column_value=column_label,
                    count=count,
                    total_percent=_round((count / total_n) * 100 if total_n else 0.0, decimals),
                    row_percent=_round((count / row_total) * 100 if row_total else 0.0, decimals),
                    column_percent=_round((count / column_total) * 100 if column_total else 0.0, decimals),
                )
            )

    return row_labels, column_labels, cells, total_n
