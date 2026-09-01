# ADR — Dominio de `results/` vs `telemetry/` en el frontend de Colmena

- Estado: PROPUESTO (no ejecutar migración masiva hasta aceptarlo)
- Fecha: 2026-08-17
- Contexto previo: `docs/frontend/ANALYTICS_GAPS.md` (GAP-024)

## 1. Problema

La auditoría de `docs/frontend/ANALYTICS_GAPS.md` encontró que varios componentes que
calculan/muestran **resultados estadísticos de un estudio** (score de constructo, supresión de
privacidad n<5, comparación de grupos) viven físicamente bajo
`frontend/src/components/colmena/telemetry/`, mientras que el módulo
`frontend/src/components/colmena/results/` ya existe y es donde conceptualmente deberían estar.

Esto no es solo un problema de nombres de carpeta: si se sigue añadiendo funcionalidad analítica
nueva sin resolver esto primero, se corre el riesgo real de duplicar componentes (por ejemplo, un
futuro `DimensionComparisonChart` en `results/` que reimplemente lo que `DimensionChartCard.jsx`
ya hace en `telemetry/`).

## 2. Regla de dominio adoptada

```text
results/
= resultados estadísticos y metodológicos de un estudio
  (score, baremo, clasificación, comparación de grupos, correlación, confiabilidad)

telemetry/
= métricas operativas de la aplicación de la encuesta
  (convocados, recibidos, válidos, tasa de respuesta, completitud, calidad de captura)
```

Prueba de pertenencia: si el dato viene de `api/analytics.js` (o expone `p_value`, `rho`,
`alpha`, `suppressed` sobre un *construct*/dimensión), es `results/`. Si el dato describe el
avance de la recolección (sesiones iniciadas/completadas, tasa válida, tiempo de respuesta), es
`telemetry/`.

## 3. Árbol actual (verificado leyendo cada archivo, no solo por nombre)

```text
frontend/src/components/colmena/
├── telemetry/
│   ├── DimensionChartCard.jsx        [usa api/analytics.js: compareConstructGroups, group.suppressed]
│   ├── DimensionDashboardTab.jsx     [renderiza root.suppressed / root.mean_score de constructo]
│   ├── ResponseDistributionsTab.jsx  [frecuencias/porcentajes/missing_n por ítem]
│   ├── ResponseMatrixTab.jsx         [tabla ancha de dataset + trigger de exportación CSV/XLSX/JSON]
│   ├── TelemetryComparisonsTab.jsx   [usa compareConstructGroups: statistic/p_value/effect_size]
│   └── TelemetrySummaryTab.jsx       [valid_count, MetricCard operativos — MEZCLADO con 1 card de mean_score/suppressed de constructo raíz]
│
└── results/
    ├── BaremResultsPanel.jsx  [baremo, priorización, supresión — ya correcto]
    ├── SpearmanPanel.jsx      [matriz de correlación, scatter binned, BH, y contiene SegmentationPanel embebido — ya correcto]
    ├── NormalityPanel.jsx     [Shapiro-Wilk, histograma — ya correcto]
    ├── PriorityBarChart.jsx   [priorización CENSOPAS — ya correcto]
    ├── UnitResultsPanel.jsx   [resultados por unidad/área — ya correcto]
    └── EvolutionPanel.jsx     [comparación temporal de resultados — ya correcto]
```

## 4. Clasificación por componente

| Componente | Ubicación actual | Clasificación | Razón (evidencia leída) |
|---|---|---|---|
| `DimensionChartCard.jsx` | `telemetry/` | **MOVER** → `results/` | Importa `compareConstructGroups` de `api/analytics.js`, renderiza `suppressed`/`mean_score`/`median_score` de constructo — es resultado estadístico, no métrica operativa |
| `DimensionDashboardTab.jsx` | `telemetry/` | **MOVER** → `results/` | Compone `DimensionChartCard`; su card raíz muestra `root.suppressed` / `root.mean_score` de constructo |
| `TelemetryComparisonsTab.jsx` | `telemetry/` | **DUPLICADO** de `SegmentationPanel` (ver fila siguiente) — **deprecar** | Llama exactamente al mismo endpoint (`compareConstructGroups(studyId, {construct_id, group_variable_id})`) y renderiza la misma tabla grupo/n/media/mediana/supresión. Es la versión **menos completa**: no muestra `method`, `statistic`, `p_value` ni `effect_size`/`effect_label` aunque el backend ya los devuelve (`SegmentationPanel` sí los muestra). Único valor no cubierto por `SegmentationPanel`: obtiene las variables de grupo desde `descriptives.questions` en vez de `listExogenousFields(projectId)` — verificar si esa fuente de datos aporta algo antes de borrar, pero la UI en sí es redundante |
| `ResponseDistributionsTab.jsx` | `telemetry/` | **MOVER** → `results/descriptive` | Frecuencias/porcentajes por ítem con `missing_n` — es la distribución Likert descriptiva (harness §17), no calidad de captura |
| `ResponseMatrixTab.jsx` | `telemetry/` | **MOVER** (destino a decidir junto con Exportaciones) | Es una tabla de dataset ancho + disparador de exportación CSV/XLSX/JSON — no encaja limpio en `results/` (no es un resultado estadístico) ni en la telemetría operativa tal como se redefine aquí. Candidato natural: una futura sección `dataset/` o vivir junto a `Exportaciones` (ver `COLMENA_SECCIONES_CENSOPAS_SEGUN_PDFS.md` §13) |
| `TelemetrySummaryTab.jsx` | `telemetry/` | **MANTENER**, con **EXTRAER** de una parte | La mayoría del archivo (`valid_count`, conteos operativos) es telemetría legítima. La card que muestra `root.suppressed`/`root.mean_score` de un constructo (línea 111) debe extraerse a `results/` — es la única mezcla real encontrada |
| `BaremResultsPanel.jsx` | `results/` | **MANTENER** | Ya en el lugar correcto |
| `SpearmanPanel.jsx` → `SegmentationPanel` (export nombrado, mismo archivo) | `results/` | **MANTENER**, **EXTRAER** a archivo propio | Correcto de dominio y es la implementación **más completa** de comparación de grupos (muestra method/statistic/p/effect_size, que `TelemetryComparisonsTab` omite). Vive embebida en el mismo archivo que `SpearmanPanel`, lo que dificulta reutilizarla fuera de la vista de correlación y oculta que es la candidata a quedarse tras deprecar el duplicado |
| `NormalityPanel.jsx` | `results/` | **MANTENER** | Correcto |
| `PriorityBarChart.jsx` | `results/` | **MANTENER** | Correcto |
| `UnitResultsPanel.jsx` | `results/` | **MANTENER** | Correcto |
| `EvolutionPanel.jsx` | `results/` | **MANTENER** | Correcto |

**Sí se encontró un duplicado real** (no solo prospectivo): `TelemetryComparisonsTab.jsx` y
`SegmentationPanel` (dentro de `SpearmanPanel.jsx`) llaman al mismo endpoint con el mismo payload
y renderizan la misma tabla — ver detalle en la fila de la tabla de arriba. Esto confirma
exactamente el riesgo que motivó esta ADR: sin la regla de dominio de §2, seguir añadiendo
features analíticas nuevas sin mirar primero `telemetry/` sigue produciendo este patrón. El
riesgo con `DimensionComparisonChart` (que el backlog de `ANALYTICS_GAPS.md` proponía extraer
como componente nuevo) es del mismo tipo: `DimensionChartCard.jsx` ya cubre ese caso en
`telemetry/`, así que ese componente nuevo debe evitarse construyéndose desde cero.

## 5. Árbol objetivo (destino, sin ejecutar todavía)

```text
frontend/src/components/colmena/
├── telemetry/                         [solo operativo — participación y calidad de captura]
│   ├── TelemetrySummaryTab.jsx        [sin la card de mean_score/suppressed de constructo]
│   └── (futuro) CaptureQualityPanel.jsx
│
├── results/
│   ├── descriptive/
│   │   └── ResponseDistributionsTab.jsx      [movido]
│   ├── dimensions/
│   │   ├── DimensionChartCard.jsx            [movido]
│   │   └── DimensionDashboardTab.jsx         [movido]
│   ├── comparisons/
│   │   └── SegmentationPanel.jsx             [extraído de SpearmanPanel.jsx, renombrar a GroupComparisonsPanel.jsx]
│   │       (TelemetryComparisonsTab.jsx se elimina — duplicado estrictamente menos completo)
│   ├── correlations/
│   │   └── SpearmanPanel.jsx                 [sin SegmentationPanel embebido]
│   ├── barems/
│   │   └── BaremResultsPanel.jsx
│   ├── units/
│   │   └── UnitResultsPanel.jsx
│   ├── reliability/  (nuevo, vacío — GAP-013)
│   ├── advanced/
│   │   ├── NormalityPanel.jsx
│   │   └── EvolutionPanel.jsx
│   └── priority/
│       └── PriorityBarChart.jsx
│
└── dataset/ (o junto a exports/)
    └── ResponseMatrixTab.jsx              [movido, decisión de carpeta pendiente]
```

Esto es una **evolución** del árbol existente, no la reescritura `features/analytics/` propuesta
inicialmente — no se crean páginas nuevas, adapters nuevos, ni una jerarquía paralela. Ver
razonamiento del usuario: "la prioridad ya no es construir analytics, sino convertir lo que
tienes en una arquitectura estable, reproducible y testeada".

## 6. Lista de archivos afectados por una futura migración (no ejecutada en este cambio)

```text
MOVER:
  frontend/src/components/colmena/telemetry/DimensionChartCard.jsx
  frontend/src/components/colmena/telemetry/DimensionDashboardTab.jsx
  frontend/src/components/colmena/telemetry/ResponseDistributionsTab.jsx
  frontend/src/components/colmena/telemetry/ResponseMatrixTab.jsx

DEPRECAR (duplicado confirmado, no mover):
  frontend/src/components/colmena/telemetry/TelemetryComparisonsTab.jsx
  → reemplazar sus usos por SegmentationPanel (una vez extraída de SpearmanPanel.jsx)
  → antes de borrar, confirmar si su fuente de variables de grupo (descriptives.questions)
    aporta algo que listExogenousFields(projectId) no cubra

EXTRAER (split de archivo existente):
  frontend/src/components/colmena/results/SpearmanPanel.jsx → SegmentationPanel.jsx
  frontend/src/components/colmena/telemetry/TelemetrySummaryTab.jsx → card de constructo raíz

ACTUALIZAR IMPORTS (consumidores — buscar antes de mover/deprecar):
  frontend/src/pages/colmena/project/ProjectPremiumDashboardPage.jsx
  frontend/src/pages/colmena/project/ProjectResultsPage.jsx
  (grep de "telemetry/DimensionChartCard", "telemetry/TelemetryComparisonsTab", etc.)

SIN CAMBIOS:
  BaremResultsPanel.jsx, NormalityPanel.jsx, PriorityBarChart.jsx, UnitResultsPanel.jsx,
  EvolutionPanel.jsx
```

## 7. Decisión

1. Adoptar la regla de dominio de §2.
2. **No ejecutar la migración de archivos en este cambio.** Este ADR es la propuesta; la
   migración es un PR separado y mecánico (mover + actualizar imports + smoke test), una vez que
   exista cobertura de tests mínima sobre los componentes a mover (ver Fase 3 del plan del
   usuario — tests antes que reorganización, para tener red de seguridad).
3. Todo componente analítico **nuevo** que se escriba a partir de ahora va directo a `results/`,
   nunca a `telemetry/`, incluso mientras la migración de los 5 archivos existentes sigue
   pendiente.
4. `ResponseMatrixTab.jsx` queda con destino **abierto** (no forzar a `results/` solo por
   sacarlo de `telemetry/`) — decidir junto con el diseño de la sección `Exportaciones`.

## 8. Consecuencias

- Ganancia: evita que la próxima feature (p.ej. `DimensionComparisonChart` del backlog) duplique
  `DimensionChartCard.jsx`.
- Costo diferido: mientras la migración no se ejecute, un desarrollador nuevo seguirá
  encontrando resultados estadísticos bajo `telemetry/` — mitigado documentando este ADR y
  enlazándolo desde `docs/frontend/ANALYTICS_GAPS.md`.
- No afecta contratos de API ni comportamiento en runtime — es reorganización de archivos
  frontend únicamente.
