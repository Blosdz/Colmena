"""Server-side chart rendering for Word/ZIP export ("estilo tesis").

Uses matplotlib with Agg (headless) so it never needs a display. Charts here
must look like a printed thesis figure, not a web dashboard: white
background, black axes/text, no rounded corners, no shadows, no decorative
grid. They read from the same services that already feed the on-screen
charts (AdvancedScoringService, NormalityService, CorrelationService) so
there is a single source of truth between what the user sees and what gets
exported — matplotlib only draws, it never recomputes statistics.

Font: Liberation Sans (metric-compatible with Arial) is required and must
be installed system-wide (Debian/Ubuntu: `apt install fonts-liberation`).
We verify it via matplotlib.font_manager before rendering anything and
raise FontNotAvailableError if it's missing — silently falling back to
DejaVu Sans would make exported figures look different from what was
validated, so that fallback is intentionally not allowed.
"""

from __future__ import annotations

import textwrap
import unicodedata
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

FONT_FAMILY = "Liberation Sans"
DPI = 300

SEMAFORO_COLORS = ["#DC2626", "#F5B21A", "#059669"]
THREE_LEVEL_NAMES = ["Bajo", "Medio", "Alto"]


class FontNotAvailableError(RuntimeError):
    pass


def _normalize_label(label: str) -> str:
    decomposed = unicodedata.normalize("NFD", label)
    without_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return without_accents.strip().lower()


def ensure_thesis_font_available() -> None:
    available = {f.name for f in fm.fontManager.ttflist}
    if FONT_FAMILY not in available:
        raise FontNotAvailableError(
            f"La fuente '{FONT_FAMILY}' no esta instalada en este servidor. "
            "Instala el paquete del sistema 'fonts-liberation' "
            "(Debian/Ubuntu: apt install fonts-liberation) y reinicia el backend. "
            "No se genera el grafico con una fuente de reemplazo silenciosa."
        )


def configure_thesis_style() -> None:
    """Applies the shared 'estilo tesis' rcParams. Call once before rendering."""
    ensure_thesis_font_available()
    plt.rcdefaults()
    matplotlib.rcParams.update(
        {
            "font.family": FONT_FAMILY,
            "font.size": 12,
            "text.color": "#000000",
            "axes.facecolor": "#FFFFFF",
            "axes.edgecolor": "#000000",
            "axes.labelcolor": "#000000",
            "axes.linewidth": 1.0,
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "#FFFFFF",
            "savefig.facecolor": "#FFFFFF",
            "xtick.color": "#000000",
            "ytick.color": "#000000",
            "legend.frameon": False,
        }
    )


def _set_wrapped_title(ax, title: str, *, width: int = 56) -> None:
    """`tight_layout` does not account for title width, so a long title (a
    variable label plus stats) can run off the right edge of the figure
    instead of wrapping. Wrap it onto multiple lines ourselves instead."""
    ax.set_title(textwrap.fill(title, width=width), fontsize=12, pad=14)


def order_baremo_levels(levels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mirrors BaremoLevelsChart.tsx's orderLevels: Bajo/Medio/Alto by name
    when there are exactly 3 levels named that way, otherwise by severity_order."""
    if len(levels) == 3:
        by_label = {_normalize_label(level["label"]): level for level in levels}
        ordered = [by_label[_normalize_label(name)] for name in THREE_LEVEL_NAMES if _normalize_label(name) in by_label]
        if len(ordered) == 3:
            return ordered
    return sorted(levels, key=lambda level: level["severity_order"])


def render_baremo_levels_chart(
    *,
    variable_label: str,
    levels: list[dict[str, Any]],
    output_path: Path,
    figure_number: int | str | None = None,
) -> Path:
    """Renders 'Gráfico N. Niveles del baremo: <variable>' as a bar chart of
    percent per level, colored red/yellow/green low-to-high, with the percent
    printed above each bar. No legend (colors are self-explanatory via the
    x-axis labels), no grid."""
    configure_thesis_style()

    ordered = order_baremo_levels(levels)
    labels = [level["label"] for level in ordered]
    percents = [float(level["percent"]) for level in ordered]
    colors = [SEMAFORO_COLORS[index % len(SEMAFORO_COLORS)] for index in range(len(ordered))]

    fig, ax = plt.subplots(figsize=(6.0, 4.0), dpi=DPI)
    bars = ax.bar(labels, percents, color=colors, width=0.6, edgecolor="none")

    for bar, percent in zip(bars, percents):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{percent:.1f}%",
            ha="center",
            va="bottom",
            fontsize=12,
            color="#000000",
        )

    ax.set_ylim(0, max(100.0, max(percents, default=0) + 10))
    ax.set_ylabel("Porcentaje")
    ax.yaxis.set_major_formatter(lambda value, _pos: f"{value:.0f}%")

    title_prefix = f"Figura {figure_number}. " if figure_number is not None else ""
    _set_wrapped_title(ax, f"{title_prefix}Nivel de {variable_label}")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=DPI, facecolor="#FFFFFF")
    plt.close(fig)
    return output_path


def compute_linear_trend(x_values: list[float], y_values: list[float]) -> tuple[float, float] | None:
    """Simple least-squares fit y = intercept + slope * x. Mirrors
    utils/linearTrend.ts's computeLinearTrend exactly (same formula), moved
    server-side so scatter exports don't depend on a browser having run it."""
    n = min(len(x_values), len(y_values))
    if n < 2:
        return None
    xs = x_values[:n]
    ys = y_values[:n]
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_xx = sum(x * x for x in xs)
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        return None
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


CORRELATION_METHOD_SYMBOLS = {
    "pearson": "r",
    "spearman": "Rho",
    "kendall": "Tau",
    "point_biserial": "r_pb",
}


def render_correlation_scatter_chart(
    *,
    x_label: str,
    y_label: str,
    x_values: list[float],
    y_values: list[float],
    output_path: Path,
    method_used: str | None = None,
    coefficient: float | None = None,
    p_value: float | None = None,
    alpha: float = 0.05,
    figure_number: int | str | None = None,
) -> Path:
    """Scatter of paired (x, y) cases plus a least-squares trend line. Point
    count must equal N — that's the integrity check the thesis student runs
    against the reported n. When the coefficient is known, a boxed
    Rho/r + p-value + R² annotation is drawn top-left, matching the
    on-screen chart and the typical thesis figure style."""
    configure_thesis_style()

    fig, ax = plt.subplots(figsize=(6.0, 4.5), dpi=DPI)
    ax.scatter(x_values, y_values, color="#5B6C8F", s=28, alpha=0.85, edgecolors="none")

    trend = compute_linear_trend(x_values, y_values)
    if trend is not None and x_values:
        slope, intercept = trend
        x_min, x_max = min(x_values), max(x_values)
        ax.plot(
            [x_min, x_max],
            [intercept + slope * x_min, intercept + slope * x_max],
            color="#000000",
            linewidth=1.75,
            linestyle="-",
        )

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    if coefficient is not None:
        symbol = CORRELATION_METHOD_SYMBOLS.get(method_used or "", method_used or "r")
        p_text = "-"
        if p_value is not None:
            p_text = f"< {alpha}" if p_value < alpha else f"{p_value:.3f}"
        stats_text = f"{symbol} = {coefficient:.2f}\np-value {p_text}\n" + r"R$^2$" + f" = {coefficient ** 2:.2f}"
        ax.text(
            0.03,
            0.97,
            stats_text,
            transform=ax.transAxes,
            fontsize=11,
            va="top",
            ha="left",
            linespacing=1.6,
            bbox={"boxstyle": "square,pad=0.5", "facecolor": "#FFFFFF", "edgecolor": "#000000", "linewidth": 1.0},
        )

    title_prefix = f"Figura {figure_number}. " if figure_number is not None else ""
    _set_wrapped_title(ax, f"{title_prefix}Dispersión: {x_label} vs. {y_label} (n = {len(x_values)})")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=DPI, facecolor="#FFFFFF")
    plt.close(fig)
    return output_path


BUCKET_COLORS = {
    "sig_001": "#059669",
    "sig_005": "#F5B21A",
    "not_sig": "#9CA3AF",
    "inverse": "#DC2626",
}


def classify_significance_bucket(coefficient: float | None, p_value: float | None) -> str:
    """Mirrors DimensionCorrelationBarsChart.tsx's classifyBucket exactly."""
    if p_value is None or coefficient is None:
        return "not_sig"
    if p_value < 0.05 and coefficient < 0:
        return "inverse"
    if p_value < 0.01:
        return "sig_001"
    if p_value < 0.05:
        return "sig_005"
    return "not_sig"


def render_dimension_coefficient_bars_chart(
    *,
    y_label: str,
    rows: list[dict[str, Any]],
    output_path: Path,
    figure_number: int | str | None = None,
) -> Path:
    """Horizontal bars of r/rho per dimension vs. a reference variable,
    colored by significance bucket (same buckets/colors as the on-screen
    DimensionCorrelationBarsChart). Each bar is one specific-hypothesis test
    in the thesis (HE1, HE2, ...)."""
    configure_thesis_style()

    labels = [row["dimension_label"] for row in rows]
    coefficients = [float(row["coefficient"]) if row["coefficient"] is not None else 0.0 for row in rows]
    buckets = [classify_significance_bucket(row["coefficient"], row["p_value"]) for row in rows]
    colors = [BUCKET_COLORS[bucket] for bucket in buckets]

    fig, ax = plt.subplots(figsize=(6.4, max(3.0, 0.6 * len(rows) + 1.2)), dpi=DPI)
    y_positions = range(len(labels))
    bars = ax.barh(list(y_positions), coefficients, color=colors, height=0.55, edgecolor="none")
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(-1, 1)
    ax.axvline(0, color="#000000", linewidth=0.8)
    ax.set_xlabel("Coeficiente r")

    for bar, row in zip(bars, rows):
        coefficient = row["coefficient"]
        p_value = row["p_value"]
        label = f"r = {coefficient:.3f}" if coefficient is not None else "r = —"
        if p_value is not None:
            label += "**" if p_value < 0.01 else ("*" if p_value < 0.05 else "")
        x_pos = bar.get_width() + (0.03 if bar.get_width() >= 0 else -0.03)
        ax.text(x_pos, bar.get_y() + bar.get_height() / 2, label, va="center", ha="left" if bar.get_width() >= 0 else "right", fontsize=10)

    title_prefix = f"Figura {figure_number}. " if figure_number is not None else ""
    _set_wrapped_title(ax, f"{title_prefix}Coeficiente r por dimensión vs. {y_label}")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=DPI, facecolor="#FFFFFF")
    plt.close(fig)
    return output_path


def render_normality_histogram_chart(
    *,
    target_name: str,
    bins: list[dict[str, Any]],
    curve: list[dict[str, Any]],
    mean: float | None,
    std: float | None,
    valid_n: int,
    output_path: Path,
    figure_number: int | str | None = None,
) -> Path:
    """Renders the observed-frequency histogram with the theoretical normal
    curve overlaid, same data NormalityHistogramChart.tsx shows on screen."""
    configure_thesis_style()

    bin_labels = [f"{bin_['bin_start']:.1f}–{bin_['bin_end']:.1f}" for bin_ in bins]
    counts = [float(bin_["count"]) for bin_ in bins]

    fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=DPI)
    ax.bar(range(len(bin_labels)), counts, color="#5B6C8F", width=0.85, edgecolor="none")

    if curve:
        # Reindex the 100-point theoretical curve onto the histogram's N bins,
        # same approach as the on-screen chart, so both axes share categories.
        n_bins = len(bin_labels)
        max_count = max(counts, default=0.0)
        max_curve_y = max((point["y"] for point in curve), default=0.0)
        scale = (max_count / max_curve_y) if max_curve_y > 0 else 1.0
        curve_y = [
            curve[round((index / max(n_bins - 1, 1)) * (len(curve) - 1))]["y"] * scale for index in range(n_bins)
        ]
        ax.plot(range(n_bins), curve_y, color="#000000", linewidth=1.75, linestyle="--")

    ax.set_xticks(range(len(bin_labels)))
    ax.set_xticklabels(bin_labels, rotation=45, ha="right", fontsize=10)
    ax.set_ylabel("Frecuencia")

    subtitle = f" (M = {mean:.2f}, DE = {std:.2f}, n = {valid_n})" if mean is not None and std is not None else ""
    title_prefix = f"Figura {figure_number}. " if figure_number is not None else ""
    _set_wrapped_title(ax, f"{title_prefix}Distribución observada vs. curva normal: {target_name}{subtitle}")

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=DPI, facecolor="#FFFFFF")
    plt.close(fig)
    return output_path
