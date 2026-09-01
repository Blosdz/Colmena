"""Tablas cruzadas (harness §23). Funciones puras.

Soporta COUNT, ROW_PERCENT, COLUMN_PERCENT, TOTAL_PERCENT.
"""

from __future__ import annotations

from collections import Counter, defaultdict

PERCENTAGE_MODES = ("COUNT", "ROW_PERCENT", "COLUMN_PERCENT", "TOTAL_PERCENT")


def compute_crosstab(pairs: list[tuple[str, str]], percentage_mode: str = "COUNT") -> dict:
    if percentage_mode not in PERCENTAGE_MODES:
        raise ValueError(f"percentage_mode inválido: {percentage_mode}")

    row_values = sorted({row for row, _ in pairs})
    col_values = sorted({col for _, col in pairs})

    counts: dict[tuple[str, str], int] = Counter(pairs)
    row_totals: dict[str, int] = defaultdict(int)
    col_totals: dict[str, int] = defaultdict(int)
    grand_total = len(pairs)

    for row, col in pairs:
        row_totals[row] += 1
        col_totals[col] += 1

    def cell_value(row: str, col: str) -> float:
        n = counts.get((row, col), 0)
        if percentage_mode == "COUNT":
            return n
        if percentage_mode == "ROW_PERCENT":
            return round((n / row_totals[row]) * 100, 2) if row_totals[row] else 0.0
        if percentage_mode == "COLUMN_PERCENT":
            return round((n / col_totals[col]) * 100, 2) if col_totals[col] else 0.0
        return round((n / grand_total) * 100, 2) if grand_total else 0.0

    table = [
        {
            "row": row,
            "cells": {col: cell_value(row, col) for col in col_values},
            "row_total": row_totals[row],
        }
        for row in row_values
    ]

    return {
        "n_valid": grand_total,
        "row_values": row_values,
        "column_values": col_values,
        "percentage_mode": percentage_mode,
        "table": table,
        # Conteos crudos por celda (independientes de percentage_mode): la
        # capa de privacidad (PrivacyService.suppress_crosstab_table) los
        # necesita para decidir supresión aunque el modo pintado sea un %.
        "raw_counts": {
            row: {col: counts.get((row, col), 0) for col in col_values} for row in row_values
        },
        "column_totals": dict(col_totals),
        "grand_total": grand_total,
    }
