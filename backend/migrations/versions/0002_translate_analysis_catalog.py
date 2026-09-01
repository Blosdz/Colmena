"""Traduce al español el catálogo expuesto por /analytics/methods.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-12
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


SPANISH_METHODS = {
    "DESCRIPTIVE": ("Estadística descriptiva", "DESCRIPTIVA"),
    "FREQUENCIES": ("Frecuencias y porcentajes", "DESCRIPTIVA"),
    "CHI_SQUARE": ("Chi-cuadrado de Pearson", "INFERENCIAL"),
    "MANN_WHITNEY": ("U de Mann-Whitney", "INFERENCIAL"),
    "KRUSKAL_WALLIS": ("Prueba de Kruskal-Wallis", "INFERENCIAL"),
    "SPEARMAN": ("Correlación de Spearman", "INFERENCIAL"),
    "BENJAMINI_HOCHBERG": ("Corrección de Benjamini-Hochberg", "INFERENCIAL"),
    "CRONBACH_ALPHA": ("Alfa de Cronbach", "PSICOMÉTRICA"),
    "MCDONALD_OMEGA": ("Omega de McDonald", "PSICOMÉTRICA"),
    "LOGISTIC_REGRESSION": ("Regresión logística", "MULTIVARIANTE"),
    "KMEANS": ("Agrupamiento K-medias", "MULTIVARIANTE"),
    "CENSOPAS_SCORING": ("Puntuación CENSOPAS-COPSOQ", "PUNTUACIÓN"),
}

ENGLISH_CATEGORIES = {
    "DESCRIPTIVE": "DESCRIPTIVE",
    "FREQUENCIES": "DESCRIPTIVE",
    "CHI_SQUARE": "INFERENTIAL",
    "MANN_WHITNEY": "INFERENTIAL",
    "KRUSKAL_WALLIS": "INFERENTIAL",
    "SPEARMAN": "INFERENTIAL",
    "BENJAMINI_HOCHBERG": "INFERENTIAL",
    "CRONBACH_ALPHA": "PSYCHOMETRIC",
    "MCDONALD_OMEGA": "PSYCHOMETRIC",
    "LOGISTIC_REGRESSION": "MULTIVARIATE",
    "KMEANS": "MULTIVARIATE",
    "CENSOPAS_SCORING": "SCORING",
}


def _update_catalog(values: dict[str, tuple[str, str]]) -> None:
    connection = op.get_bind()
    for code, (name, category) in values.items():
        connection.exec_driver_sql(
            "UPDATE colmena.analysis_methods SET name = %s, category = %s WHERE code = %s",
            (name, category, code),
        )


def upgrade() -> None:
    _update_catalog(SPANISH_METHODS)


def downgrade() -> None:
    previous_names = {
        code: (name, ENGLISH_CATEGORIES[code])
        for code, (name, _category) in SPANISH_METHODS.items()
    }
    previous_names["CHI_SQUARE"] = ("Chi-cuadrado", "INFERENTIAL")
    previous_names["MANN_WHITNEY"] = ("Mann-Whitney U", "INFERENTIAL")
    previous_names["KRUSKAL_WALLIS"] = ("Kruskal-Wallis", "INFERENTIAL")
    previous_names["BENJAMINI_HOCHBERG"] = (
        "Corrección Benjamini-Hochberg",
        "INFERENTIAL",
    )
    previous_names["KMEANS"] = ("K-means", "MULTIVARIATE")
    previous_names["CENSOPAS_SCORING"] = ("Scoring CENSOPAS-COPSOQ", "SCORING")
    _update_catalog(previous_names)
