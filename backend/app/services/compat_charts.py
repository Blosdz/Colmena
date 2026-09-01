"""Render de gráficas PNG para el shim de compatibilidad con AppThesis.

El COLMENA anterior tenía un almacén de `chart-images` (artefactos PNG subidos
por el editor de gráficas). COL2 no lo tiene: aquí se generan al vuelo, desde
los resultados de baremación del estudio (`ScoringService.get_overview`), las
dos gráficas que el editor de tesis de AppThesis sabe insertar.

`artifact_id` es un slug estable (no un UUID persistido) — el marcador que
`colmenaCharts.js` genera sólo admite `[A-Za-z0-9_-]+`.
"""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.scoring_service import ScoringService

# Colores por código de clasificación de banda (fallback si el baremo no trae color_hint).
_BAND_FALLBACK = {
    "FAVORABLE": "#22c55e",
    "INTERMEDIATE": "#f59e0b",
    "UNFAVORABLE": "#ef4444",
}

CHART_CATALOG = {
    "baremo_distribution": "Distribución por niveles del baremo",
    "mean_by_priority": "Puntaje promedio por variable (orden de prioridad)",
}


def _fig_to_png_bytes(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", facecolor="white", bbox_inches="tight", dpi=150)
    plt.close(fig)
    return buffer.getvalue()


def _band_color(band) -> str:
    if getattr(band, "color_hint", None):
        return band.color_hint
    return _BAND_FALLBACK.get(band.classification_code or "", "#94a3b8")


def _render_baremo_distribution(overview) -> bytes:
    rows = [r for r in overview.results if not r.suppressed and r.bands]
    if not rows:
        raise NotFoundError("El estudio no tiene resultados de baremación para graficar.")
    rows = rows[::-1]  # barh dibuja de abajo a arriba; se quiere prioridad 1 arriba
    labels = [r.construct_name for r in rows]
    band_labels: list[str] = []
    for r in rows:
        for b in r.bands:
            if b.label not in band_labels:
                band_labels.append(b.label)

    fig, ax = plt.subplots(figsize=(7.2, max(1.8, 0.5 * len(rows) + 1.0)))
    y = range(len(rows))
    left = [0.0] * len(rows)
    for band_label in band_labels:
        widths = []
        color = "#94a3b8"
        for r in rows:
            match = next((b for b in r.bands if b.label == band_label), None)
            widths.append(float(match.pct) if match and match.pct is not None else 0.0)
            if match:
                color = _band_color(match)
        ax.barh(list(y), widths, left=left, height=0.6, label=band_label, color=color)
        for yi, (w, l) in enumerate(zip(widths, left)):
            if w >= 8:
                ax.text(l + w / 2, yi, f"{w:.0f}%", ha="center", va="center",
                        fontsize=7, color="white", fontweight="bold")
        left = [a + b for a, b in zip(left, widths)]

    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12),
              ncol=min(len(band_labels), 4), fontsize=8, frameon=False)
    ax.set_title("Distribución por niveles (%)", fontsize=11, color="#0f172a")
    return _fig_to_png_bytes(fig)


def _render_mean_by_priority(overview) -> bytes:
    rows = [r for r in overview.results if not r.suppressed and r.mean_score is not None]
    if not rows:
        raise NotFoundError("El estudio no tiene puntajes promedio para graficar.")
    rows.sort(key=lambda r: (r.priority_rank or 9999, r.construct_id))
    labels = [r.construct_name for r in rows]
    values = [float(r.mean_score) for r in rows]

    fig, ax = plt.subplots(figsize=(7.2, max(2.0, 0.5 * len(rows) + 1.0)))
    colors = [
        _band_color(next((b for b in r.bands if b.label), r.bands[0])) if r.bands else "#F5B21A"
        for r in rows
    ]
    bars = ax.barh(range(len(rows)), values, height=0.6, color=colors)
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}", va="center", fontsize=8, color="#0f172a")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title("Puntaje promedio 0–100 por prioridad", fontsize=11, color="#0f172a")
    return _fig_to_png_bytes(fig)


_RENDERERS = {
    "baremo_distribution": _render_baremo_distribution,
    "mean_by_priority": _render_mean_by_priority,
}


async def list_available_charts(session: AsyncSession, study_id: int) -> list[dict]:
    """Artefactos disponibles para un estudio con scoring calculado."""
    overview = await ScoringService(session).get_overview(study_id)
    if not overview.results:
        return []
    return [
        {
            "artifact_id": slug,
            "form_id": str(study_id),
            "title": title,
            "chart_type": slug,
            "mime_type": "image/png",
            "status": "word_ready",
        }
        for slug, title in CHART_CATALOG.items()
    ]


async def render_chart_png(session: AsyncSession, study_id: int, artifact_id: str) -> bytes:
    renderer = _RENDERERS.get(artifact_id)
    if renderer is None:
        raise NotFoundError(f"Gráfica '{artifact_id}' no reconocida.")
    overview = await ScoringService(session).get_overview(study_id)
    return renderer(overview)


def png_to_payload(study_id: int, artifact_id: str, png: bytes) -> dict:
    b64 = base64.b64encode(png).decode("ascii")
    return {
        "artifact_id": artifact_id,
        "form_id": str(study_id),
        "mime_type": "image/png",
        "data_base64": b64,
        "data_url": f"data:image/png;base64,{b64}",
    }
