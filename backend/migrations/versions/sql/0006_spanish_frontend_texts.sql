-- Migración 0006: textos persistidos que se muestran al usuario en español.
-- Los códigos técnicos (ACTIVE, DRAFT, KMEANS, etc.) no se traducen porque
-- forman parte del contrato de API y de restricciones CHECK.

SET search_path TO colmena, public;

ALTER TABLE colmena.barem_cutoffs
    ALTER COLUMN favorable_label SET DEFAULT 'FAVORABLE',
    ALTER COLUMN intermediate_label SET DEFAULT 'INTERMEDIO',
    ALTER COLUMN unfavorable_label SET DEFAULT 'DESFAVORABLE';

UPDATE colmena.barem_cutoffs
SET intermediate_label = 'INTERMEDIO'
WHERE intermediate_label = 'INTERMEDIATE';

UPDATE colmena.barem_cutoffs
SET unfavorable_label = 'DESFAVORABLE'
WHERE unfavorable_label = 'UNFAVORABLE';

UPDATE colmena.barem_bands
SET label = CASE label
    WHEN 'INTERMEDIATE' THEN 'INTERMEDIO'
    WHEN 'UNFAVORABLE' THEN 'DESFAVORABLE'
    ELSE label
END
WHERE label IN ('INTERMEDIATE', 'UNFAVORABLE');

UPDATE colmena.construct_scores
SET classification = CASE classification
    WHEN 'INTERMEDIATE' THEN 'INTERMEDIO'
    WHEN 'UNFAVORABLE' THEN 'DESFAVORABLE'
    ELSE classification
END
WHERE classification IN ('INTERMEDIATE', 'UNFAVORABLE');

UPDATE colmena.construct_results
SET classification = CASE classification
    WHEN 'INTERMEDIATE' THEN 'INTERMEDIO'
    WHEN 'UNFAVORABLE' THEN 'DESFAVORABLE'
    ELSE classification
END
WHERE classification IN ('INTERMEDIATE', 'UNFAVORABLE');

UPDATE colmena.analysis_methods AS method
SET name = translated.name,
    category = translated.category
FROM (VALUES
    ('DESCRIPTIVE', 'Estadística descriptiva', 'DESCRIPTIVA'),
    ('FREQUENCIES', 'Frecuencias y porcentajes', 'DESCRIPTIVA'),
    ('CHI_SQUARE', 'Chi-cuadrado de Pearson', 'INFERENCIAL'),
    ('MANN_WHITNEY', 'U de Mann-Whitney', 'INFERENCIAL'),
    ('KRUSKAL_WALLIS', 'Prueba de Kruskal-Wallis', 'INFERENCIAL'),
    ('SPEARMAN', 'Correlación de Spearman', 'INFERENCIAL'),
    ('BENJAMINI_HOCHBERG', 'Corrección de Benjamini-Hochberg', 'INFERENCIAL'),
    ('CRONBACH_ALPHA', 'Alfa de Cronbach', 'PSICOMÉTRICA'),
    ('MCDONALD_OMEGA', 'Omega de McDonald', 'PSICOMÉTRICA'),
    ('LOGISTIC_REGRESSION', 'Regresión logística', 'MULTIVARIANTE'),
    ('KMEANS', 'Agrupamiento K-medias', 'MULTIVARIANTE'),
    ('CENSOPAS_SCORING', 'Puntuación CENSOPAS-COPSOQ', 'PUNTUACIÓN'),
    ('NORMALITY', 'Pruebas de normalidad', 'DESCRIPTIVA'),
    ('SPEARMAN_MATRIX', 'Matriz de correlación de Spearman', 'INFERENCIAL'),
    ('CONSTRUCT_COMPARE_GROUPS', 'Comparación de constructos por grupos', 'INFERENCIAL'),
    ('LIKERT_SCORING', 'Puntuación Likert y baremos', 'PUNTUACIÓN')
) AS translated(code, name, category)
WHERE method.code = translated.code;
