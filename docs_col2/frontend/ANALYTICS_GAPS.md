# ANALYTICS FRONTEND AUDIT

```
Frontend: frontend/src (Vite + React, recharts)
Backend:  backend/app (FastAPI + SQLAlchemy, app/analytics/*)
Branch:   main
Commit:   65642bb
Fecha:    2026-08-17
```

## 0. Resumen ejecutivo

El supuesto de partida del harness (backend mínimo, frontend por construir) **no aplica a este
repositorio**. Ya existe:

- Un paquete `backend/app/analytics/` completo: `normality.py`, `reliability.py`, `inferential.py`
  (chi², Mann-Whitney, Kruskal-Wallis), `multiple_testing.py` (Benjamini-Hochberg), `crosstabs.py`,
  `regression.py`.
- Modelos ricos: `Variable`, `Construct` (árbol variable→dimensión→subdimensión vía `parent_id`),
  `ConstructItem` (peso, rol, dirección de puntuación), `ResponseScore`, `ConstructScore`,
  `ConstructResult`, `Barem`/`BaremCutoff`/`BaremBand`, `AnalysisRun`.
- Endpoints reales en `api/v1/analytics.py` (`/describe`, `/frequencies`, `/crosstab`,
  `/compare-groups`, `/correlation`, `/reliability`, `/spearman-matrix`,
  `/construct-compare-groups`, `/logistic-regression`, `/kmeans`) y `api/v1/censopas.py`
  (barems, bandas, scoring, resultados, readiness).
- Un `PrivacyService` con supresión por n mínimo configurable **y protección de deducción
  secundaria** (agrupar unidades pequeñas bajo la unidad padre) — cubre exactamente la
  preocupación de la §36 del harness.
- Frontend con `recharts` (no Chart.js) ya integrado en `BaremResultsPanel.jsx` (barras
  apiladas por nivel, priorización, badge de supresión) y `SpearmanPanel.jsx` (matriz de
  correlación, p ajustado BH, magnitud, scatter **binned** por privacidad,
  `SegmentationPanel` para comparación de grupos).

Esto cambia la prioridad: el trabajo no es "construir el motor analítico en el frontend",
es **auditar/completar contratos, tipar, y decidir si consolidar la carpeta `telemetry/`
existente con la propuesta `features/analytics/`** — no reorganizar todo (regla §40/§102).

---

## 1. Tabla de gaps

| ID | Necesidad | Frontend existe | Backend existe | Datos suficientes | Estado | Acción |
|---|---|---:|---:|---:|---|---|
| GAP-001 | Descriptiva por variable (n, media, mediana, DE) | Parcial | Sí (`/analytics/describe`) | Sí | PARTIAL | Confirmar consumo real en `ProjectResultsPage`; tipar respuesta |
| GAP-002 | Distribución Likert (barra apilada 100%) | Sí | Sí (`/frequencies`) | Sí | READY | Verificar reuso en resultados académicos vs. solo telemetry |
| GAP-003 | Baremos (tabla + niveles) | Sí (`BaremResultsPanel`) | Sí (`Barem`/`BaremCutoff`/`BaremBand`) | Sí | READY | Extraer `BaremTable` genérico reutilizable fuera de CENSOPAS |
| GAP-004 | `BaremStatus` explícito (DRAFT/PROVISIONAL/VERIFIED/OFFICIAL) visible en UI | No | Sí (`Barem.status`) | Sí | TODO | Mapear `status` del backend a badge visible, no tooltip |
| GAP-005 | Comparación entre dimensiones (barra horizontal) | Parcial (`BaremResultsPanel` ordena árbol) | Sí (`ConstructResult`, `ConstructScore`) | Sí | PARTIAL | Extraer `DimensionComparisonChart` desacoplado de CENSOPAS |
| GAP-006 | Comparación entre variables (validar escalas) | No | Parcial (measurement_level existe, sin flag "escala comparable") | Revisar | PARTIAL | Backend no expone si dos variables son comparables; frontend debe bloquear o pedir criterio |
| GAP-007 | Correlación Spearman (resumen + tabla) | Sí (`SpearmanPanel`) | Sí (`/analytics/correlation`, BH ajustado) | Sí | READY | Reusar fuera del panel CENSOPAS para académico |
| GAP-008 | Matriz de correlaciones (heatmap) | Sí (`SpearmanPanel`) | Sí (`/spearman-matrix`) | Sí | READY | Generalizar componente a `CorrelationHeatmap` reusable |
| GAP-009 | Scatter de pares (x,y) por observación | No (por diseño) | **No, por diseño** — solo bins (`points_binned`, nunca coordenadas individuales) | No (bloqueado a propósito) | BLOCKED | No es un bug: es política de privacidad. Documentar y usar scatter **binned**/heatmap, nunca reconstruir pares — evita §22/§72 (`SCATTER_DATA_MISSING` aplica salvo que se acepte el binned) |
| GAP-010 | Comparaciones entre grupos (Mann-Whitney/Kruskal/Chi²) | Sí (`SegmentationPanel`) | Sí (`inferential.py`, `/compare-groups`, `/construct-compare-groups`) | Sí | READY | Generalizar tabla de resultados de prueba (§26 contrato) |
| GAP-011 | Intervalo de confianza (IC 95%) en correlación/comparaciones | No | **No** — ningún test devuelve CI | No | BLOCKED | Backend no calcula IC; no inventar en frontend. Registrar como bloqueo estadístico |
| GAP-012 | Tamaño de efecto separado de significancia | Sí (`SegmentationPanel`, y `GroupComparisonsPanel.jsx` corregido 2026-08-18: bloque "Inferencia" con método/estadístico/p/q BH si existe/effect_size/effect_label, antes descartaba estos 5 campos) | Sí (`effect_size`, `effect_label` en todas las pruebas) | Sí | READY | Regla §27 cumplida en las dos superficies de comparación de grupos conocidas |
| GAP-013 | Confiabilidad (alfa/omega) | Sí (`ReliabilityCard` en `ProjectPremiumDashboardPage.jsx`, 2026-08-18) | Sí (`reliability.py`, `/reliability`) | Sí | READY | Tabla por dimensión D1-D6 (ítems/alfa/omega/n), una llamada `POST /reliability` por constructo vía `Promise.allSettled`; nota fija "no representan diagnóstico ni validez individual" |
| GAP-014 | CENSOPAS: raw_code/risk_value/score_0_100/cut_1/cut_2 | Sí | Sí (`ResponseScore`, `BaremCutoff`) | Sí | READY | Ya integrado en `BaremResultsPanel` |
| GAP-015 | CENSOPAS: `traffic_light`/`group_level` como campos literales | N/A | No (equivalente vía `classification_status` + conteos fav/int/desfav) | Sí (equivalente) | NOT_APPLICABLE | No requiere cambio; los nombres de campo difieren pero el dato existe |
| GAP-016 | CENSOPAS: supresión n<5 + protección de deducción secundaria | Sí (badge `Privacy`) | Sí (`PrivacyService`, umbral configurable) | Sí | READY | Confirmar que exportaciones/tablas también respetan el flag `suppressed` (§37) |
| GAP-017 | Capabilities endpoint (`GET .../capabilities`) | No | **No existe en ningún router** | No | BLOCKED | Registrar como TECH_DEBT (§49): si se deriva client-side, debe marcarse explícitamente y no ser fuente de verdad |
| GAP-018 | Feature flags (`features.analytics`, `features.censopas`, etc.) | No existe ningún sistema de flags | N/A | N/A | MISSING | Crear antes de exponer módulos incompletos (correlación académica, confiabilidad) |
| GAP-019 | Tipos/contratos TS o JSDoc (`Variable`, `Dimension`, `CorrelationResult`, `StatisticalTestResult`, `BaremStatus`) | Sí, parcial — `frontend/src/api/generated/analytics.d.ts` (espejo manual) | Sí (schemas Pydantic en `app/schemas/analytics.py`, `variables.py`, `constructs.py`, `censopas.py`) | Sí | PARTIAL | El entorno de este cambio no tiene el backend instalable (`poetry.lock` sin resolver, sin `fastapi`/`sqlalchemy` en el Python disponible), así que no se pudo generar `openapi.json` real ni correr `openapi-typescript`. Se transcribieron los campos exactos leyendo el código fuente de los schemas (no inventados) y se documentó el reemplazo por generación real en `api/generated/README.md`. **No borrar `analytics.d.ts` hasta que exista `openapi.d.ts` generado de verdad** |
| GAP-020 | Trazabilidad de score (qué ítems/pesos participaron en el cálculo histórico) | No | Parcial — `algorithm_version` se guarda, pero pesos viven en `ConstructItem` (mutable, puede derivar) | Parcial | PARTIAL | Riesgo: un score antiguo puede no ser reproducible si los pesos cambiaron después. Registrar `SCORE_TRACEABILITY_GAP` parcial — **no implementar junto con GAP-011/017/021 en el mismo cambio** |
| GAP-021 | Trazabilidad de baremo (versión congelada en el resultado) | No | Parcial — resultados referencian `barem_id`, no una versión congelada | Parcial | PARTIAL | Si el barem se edita post-hoc, la procedencia de resultados históricos queda ambigua — **no implementar junto con GAP-011/017/020 en el mismo cambio** |
| GAP-022 | Método de correlación configurable (Pearson/Kendall además de Spearman) | No | No — `inferential.py` solo implementa Spearman | No | NOT_APPLICABLE (por ahora) | El tipo `CorrelationResult.method` en el harness admite 3 métodos; backend real solo soporta 1. No ofrecer selector de método hasta que exista |
| GAP-023 | Tests frontend de analítica | Parcial — Vitest + Testing Library configurados (`vitest.config.js`, `npm test`), 7 tests en `results/__tests__/` | N/A | N/A | PARTIAL | Cubierto: loading state, empty state, supresión n<5 (tabla de baremos y de segmentación), scatter binned presente/ausente (GAP-009), error de mutación. Pendiente del §5 del plan: loading *mid-flight* de una mutación (no solo el query inicial), y un test de "baremo ausente" (Caso C del dataset QA) |
| GAP-024 | Arquitectura `features/analytics/` vs. estructura actual | Existe estructura por dominio (`components/colmena/{results,telemetry,instruments,variables}`) + módulo `telemetry/` paralelo que se solapa conceptualmente | N/A | N/A | PARTIAL | **ADR propuesta en `docs/architecture/ADR-analytics-results-telemetry.md`** — no ejecutada todavía. Regla adoptada: `results/` = resultados estadísticos, `telemetry/` = operativo. 4 componentes a mover, 1 duplicado confirmado a deprecar (ver GAP-026), 1 componente a partir en dos |
| GAP-025 | Endpoint `results/overview` referenciado en tests de integración | Sin verificar en frontend | Mencionado en test pero no confirmado por grep de routers | Por verificar | TODO | Verificar existencia real antes de asumir disponible |
| GAP-026 | `TelemetryComparisonsTab.jsx` duplica `SegmentationPanel` (dentro de `SpearmanPanel.jsx`) | Sí, doble implementación confirmada | N/A (mismo endpoint `compareConstructGroups`) | N/A | CONFIRMED_DUPLICATE | Ambos llaman exactamente al mismo endpoint con el mismo payload. `TelemetryComparisonsTab` es la versión **menos completa**: no muestra `method`/`statistic`/`p_value`/`effect_size` aunque el backend ya los devuelve. Deprecar `TelemetryComparisonsTab` en favor de `SegmentationPanel` (ver ADR §4/§6) — verificar antes si su fuente de variables de grupo (`descriptives.questions`) aporta algo que `listExogenousFields` no cubra |
| GAP-027 | Regresión logística (predictor/OR/p) en el Dashboard Premium | Placeholder explícito en sección "Multivariado" (2026-08-18), sin valores simulados | Sí (`regression.py`, `/logistic-regression`) | Parcial — sin IC (ver GAP-011) | TODO | Backend existe pero no está consumido todavía. Cuando se implemente: rotular "Analítica complementaria — modelo ajustado", nunca resultado CENSOPAS, y no dibujar forest plot mientras GAP-011 siga BLOCKED |
| GAP-028 | `ProjectPremiumDashboardPage.jsx` mezclaba Confiabilidad/Comparaciones/Correlaciones/Segmentación en una sola vista sin separación visual | Corregido 2026-08-18 | N/A | N/A | READY | Se agregó `SectionHeading` y se reordenó la página en 5 secciones explícitas: Resumen, Confiabilidad, Comparaciones, Correlaciones, Segmentación, Multivariado (placeholder). Ningún componente se duplicó — se reordenaron `ReliabilityCard`/`GroupComparisonsPanel`/`SpearmanCard`/`SegmentationCard` ya existentes |

---

## 2. Bloqueos por categoría

**CENSOPAS BLOCKERS:**
- Ninguno estructural. El módulo CENSOPAS (barems, cutoffs, bandas, supresión, resultados) está
  más completo que lo que el harness asumía como punto de partida.

**ACADEMIC BLOCKERS:**
- GAP-006 (comparabilidad de escalas entre variables no está flageada por el backend).
- GAP-013 (confiabilidad no tiene UI aunque el backend la calcula).
- GAP-024 (ADR propuesta en `docs/architecture/ADR-analytics-results-telemetry.md`, migración
  de archivos aún sin ejecutar — todo componente analítico nuevo va directo a `results/`).

**STATISTICAL BLOCKERS:**
- GAP-011: no hay IC 95% en ningún resultado inferencial — no inventar en frontend (regla §97).
- GAP-022: solo Spearman está implementado; no ofrecer selector de método Pearson/Kendall.
- GAP-009: scatter de pares crudos está bloqueado **por diseño de privacidad**, no por falta de
  desarrollo — no intentar reconstruir pares desde bins.

**PRIVACY BLOCKERS:**
- Ninguno bloqueante — el `PrivacyService` ya cubre supresión + deducción secundaria. Pendiente
  solo confirmar que *todas* las superficies (export CSV/XLSX, tooltips, cache visual) respetan
  `suppressed` (GAP-016), por regla §85.

---

## 3. Changelog de este PR (ejecutado, no solo propuesto)

```text
[x] docs/architecture/ADR-analytics-results-telemetry.md — árbol actual, árbol objetivo,
    clasificación mantener/mover/extraer/deprecar de los 12 componentes de telemetry/+results/,
    incluyendo el duplicado confirmado GAP-026. Migración de archivos NO ejecutada todavía.
[x] frontend/src/api/generated/analytics.d.ts + README.md — espejo manual (no generado) de los
    schemas Pydantic reales de analítica/baremos/constructos. GAP-019: TODO -> PARTIAL.
[x] frontend/vitest.config.js, vitest.setup.js, npm test / npm run test:watch — primer test
    runner del frontend. GAP-023: MISSING -> PARTIAL.
[x] 7 tests en results/__tests__/: BaremResultsPanel (loading, empty, supresión n<5 en tabla de
    baremos) y SpearmanPanel/SegmentationPanel (scatter binned presente/ausente sin inventar
    pares, error de mutación, supresión n<5 en comparación de grupos). Todos pasan; lint y build
    de producción verificados sin regresión.
[ ] NO se movió ningún archivo de telemetry/ a results/ (la ADR es propuesta, no ejecutada).
[ ] NO se cambió Recharts por Chart.js.
[ ] NO se intentó exponer pares (x,y) crudos de scatter — el diseño binned se mantiene y quedó
    documentado explícitamente en el tipo SpearmanPointBin.
[ ] NO se implementaron GAP-011 (IC 95%), GAP-017 (capabilities), GAP-020 (score snapshot) ni
    GAP-021 (barem frozen version) en este cambio — quedan documentados por separado, cada uno
    como su propio PR futuro, tal como se pidió explícitamente.
```

## 4. Recommended next step (lo que sigue, no lo ya hecho arriba)

1. Decidir y ejecutar la migración de archivos de la ADR (§6 de
   `ADR-analytics-results-telemetry.md`) — mover 4 componentes, deprecar
   `TelemetryComparisonsTab.jsx` (GAP-026), extraer `SegmentationPanel` a archivo propio. Hacerlo
   en un PR mecánico separado, apoyado en los tests ya existentes como red de seguridad.
2. Cuando exista un entorno con el backend instalable (`poetry install` funcionando), reemplazar
   `analytics.d.ts` por generación real vía `openapi-typescript` — instrucciones en
   `frontend/src/api/generated/README.md`. No seguir ampliando el espejo manual a mano para
   endpoints nuevos; en cuanto se pueda generar de verdad, migrar.
3. Elegir **uno** de los cuatro gaps de backlog (GAP-011 IC 95%, GAP-017 capabilities, GAP-020
   score snapshot, GAP-021 barem frozen version) para el siguiente PR — no combinarlos. De los
   cuatro, GAP-017 (capabilities) probablemente desbloquea más UI (permite dejar de ocultar
   botones con lógica implícita) con el menor riesgo de cambio de esquema de base de datos.
4. Extraer `BaremTable`, `DimensionComparisonChart` (a partir de `DimensionChartCard.jsx`, tras
   la migración de la ADR) y `CorrelationHeatmap` como componentes genéricos reutilizables — son
   READY, no MISSING; no reescribirlos desde cero.
5. Ampliar la cobertura de tests de GAP-023: loading *mid-flight* de una mutación en curso, y el
   caso "baremo ausente" (Caso C de `COLMENA_QA_DATASET_TESIS_DOS_VARIABLES.md` §7).
