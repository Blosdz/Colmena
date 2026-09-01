"""Autoridad única para el estado del Plan Preventivo (harness Punto 4, Fase 6).

`OVERDUE` nunca se guarda en `action_plan_items.status` — es un estado
derivado (`due_date` vencido y `status` no terminal) que se calcula siempre
con esta misma función, tanto en `ActionPlanItemRead.effective_status` como
en `ReportService`. No reimplementar esta condición en otro lugar.
"""

from __future__ import annotations

from datetime import date

from app.models.bsc import KpiMeasurement

ACTION_PLAN_ITEM_STATUSES = ("PENDING", "IN_PROGRESS", "DONE", "BLOCKED", "CANCELLED")
_TERMINAL_STATUSES = frozenset({"DONE", "CANCELLED"})


def compute_effective_status(status: str, due_date: date | None, *, today: date | None = None) -> str:
    reference = today or date.today()
    if due_date is not None and due_date < reference and status not in _TERMINAL_STATUSES:
        return "OVERDUE"
    return status


def latest_measurement(measurements: list[KpiMeasurement]) -> KpiMeasurement | None:
    if not measurements:
        return None
    return max(measurements, key=lambda item: item.measured_at)
