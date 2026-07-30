# Qué hacen `/results` y `/reports` y a qué llama en el backend

Rutas: `/project/:projectId/results` → `ProjectResultsPage.tsx`
       `/project/:projectId/reports` → `ProjectReportsPage.tsx`

Ambas páginas resuelven primero `formId`/`instrumentId` con:
- `getProject(projectId)` → `GET /api/v1/projects/{projectId}`
- `listProjectForms(projectId)` → `GET /api/v1/projects/{projectId}/forms`
- `listInstruments(formId)` → `GET /api/v1/forms/{formId}/instruments`

---

## `/results` — `ProjectResultsPage.tsx`

Pipeline de 4 etapas en tabs (`PipelineStepper`), con un selector de variable global (`VariableSelector` + `useVariableSelection`, que carga `getAnalysisOptions` → `GET /api/v1/forms/{formId}/analysis/options`, resuelto por `AnalysisOrchestratorService`).

Acciones de cabecera:
- **Calcular resultados** → `runScoring(formId, {...})` → `POST /api/v1/forms/{formId}/scoring/run` (`AdvancedScoringService` vía `scoring.py`)
- **Configurar baremo** (`CreateBaremoModal`) → `getScoringOptions` (`GET .../scoring/options`) y `createScoringConfig` (`POST .../scoring/configs`) — `ScoringConfigService`

### Etapa 1 — Fiabilidad (`ReliabilityStage.tsx`)
- `getInstrumentSheet(formId, instrumentId)` → `GET /api/v1/forms/{formId}/instrument-sheet?instrument_id=...`
  → router `instrument_sheet.py` → `InstrumentSheetService` (agrega alfa de Cronbach, fiabilidad compuesta, normalidad y baremos del instrumento en un solo payload)
- Render: `ReliabilityPanel` (tabla + semáforo, sin llamadas propias, usa el `sheet` ya cargado)

### Etapa 2 — Descriptivos (`DescriptiveStage.tsx`)
- `getDescriptives(formId)` → `GET /api/v1/forms/{formId}/descriptives` (`DescriptiveService`)
- `listScoringConfigs(formId)` → `GET /api/v1/forms/{formId}/scoring/configs`
- `getBaremoResolution(formId)` → `GET /api/v1/forms/{formId}/scoring/baremos/resolution?levels_count=...`
- Banner `ReliabilityWarningBanner` reutiliza `getInstrumentSheet` (misma query cacheada) para avisar si el alfa es bajo o aún no calculado.
- Render: `EditableBaremoTable` (+ `createScoreBand`/`updateScoreBand`/`deleteScoreBand` sobre `/api/v1/scoring/bands*`), `BaremoLevelsChart`, `FrequencyDistributionBlock` (sin fetch propio, usa el reporte descriptivo).

### Etapa 3 — Normalidad (`NormalityStage.tsx`)
- Bloque de decisión: `getNormalityReport(formId, "auto")` → `GET /api/v1/forms/{formId}/normality?method=auto`, o `getQuestionNormality` → `GET .../normality/questions/{questionId}` si la variable X es una pregunta suelta. Ambos resueltos por `NormalityService`, que decide Shapiro-Wilk (N≤50) o Kolmogorov-Smirnov/Lilliefors (N>50).
- Tabla + histograma (reutilizados de Reportes): `NormalityPanel` (usa el `sheet` de `getInstrumentSheet`) y `NormalityHistogramChart` → `getNormalityHistogram` → `GET .../normality/histogram`.

### Etapa 4 — Inferencial (`InferentialStage.tsx`)
- `runPairCorrelation(formId, {x, y, method:"auto"})` → `POST /api/v1/forms/{formId}/correlations/pair` (`CorrelationService.choose_auto_method` decide Pearson/Spearman/Kendall/punto-biserial según normalidad y tipo de variable)
- Si X es un instrumento completo: `getInstrumentSheet` (dimensiones) + `runCorrelationMatrix(formId, {targets: dimensiones + Y})` → `POST /api/v1/forms/{formId}/correlations/matrix`, para el desglose de hipótesis específicas por dimensión (reutiliza `BarsFromCells` de `DimensionCorrelationBarsChart`).

---

## `/reports` — `ProjectReportsPage.tsx`

Es más una "caja de herramientas" con secciones independientes (no un pipeline guiado):

### Ficha técnica del instrumento
- `getInstrumentSheet(formId, instrumentId)` (misma llamada que Etapa 1/3 de resultados)
- `InstrumentMetadataCard` → `updateInstrument(instrumentId, payload)` → `PATCH /api/v1/form-instruments/{instrumentId}`
- `NormalityPanel` + `NormalityHistogramChart` (mismos componentes que Etapa 3)
- `InstrumentSheetExportBar`:
  - `exportInstrumentSheetExcel` → `POST /api/v1/forms/{formId}/instrument-sheet/exports/excel`
  - `exportInstrumentSheetWord` → llama a `generateWordReport` con `include_instrument_sheet: true` → `POST /api/v1/forms/{formId}/word-reports/generate`

### Importancia vs. Desempeño (Stewart)
- `StewartChart` → `getStewartMatrix(formId, instrumentId)` → `GET /api/v1/forms/{formId}/descriptives/stewart` (`StewartService`)

### Correlaciones entre variables
- `CorrelationScatterChart`: `getAnalysisOptions` (selector X/Y propio) + `runPairCorrelation` → `POST .../correlations/pair`
- `DimensionCorrelationBarsChart`:
  - Modo "entre dimensiones del instrumento": `getInstrumentDimensionsCorrelations(formId, instrumentId)` → `GET /api/v1/forms/{formId}/correlations/instruments/{instrumentId}/dimensions`
  - Modo "dimensiones vs. variable externa": `getScoringOptions` + `getAnalysisOptions` + `runCorrelationMatrix` → `POST .../correlations/matrix`

### Análisis guiado (`AnalysisRunner`)
- `getAnalysisOptions` → `GET .../analysis/options`
- `runAnalysis(formId, payload)` → `POST /api/v1/forms/{formId}/analysis/run`
- `runFullScan(formId, payload)` → `POST /api/v1/forms/{formId}/analysis/full-scan`
- Todo resuelto por `AnalysisOrchestratorService`, que internamente reusa `DescriptiveService`, `NormalityService`, `CorrelationService`, `GroupComparisonService`, `CategoricalAssociationService`, `StatisticalDecisionService` y devuelve bloques de resultado + tablas APA + gráficos sugeridos + interpretación en lenguaje llano, todo en un solo payload (`OrchestratedAnalysisRead`).

### Editor de gráficos (`ChartViewer`)
- `getRecommendedCharts(formId)` → `GET /api/v1/forms/{formId}/charts/recommended` (`ChartService`)
- (no incluido en este archivo pero disponible en `api/charts.ts`: `generateChart`, `getChartOptions`, `generateChartsFromAnalysisRun/OrchestratedRun`, `exportChartSpecs`)

### Tablas APA (`ApaTableViewer`)
- `generateApaBatch(formId, payload)` → `POST /api/v1/forms/{formId}/apa-tables/batch` (`ApaTableService`)

### Reporte Word (`WordReportPanel`)
- `listChartImages(formId)` → `GET /api/v1/forms/{formId}/chart-images`
- `getWordReportOptions(formId)` → `GET /api/v1/forms/{formId}/word-reports/options`
- `listWordReports(formId)` → `GET /api/v1/forms/{formId}/word-reports`
- `generateWordReport(formId, payload)` → `POST /api/v1/forms/{formId}/word-reports/generate` (`WordReportService`)

---

## Tabla resumen de endpoints usados por estas dos páginas

| Endpoint | Método | Router | Service |
|---|---|---|---|
| `/projects/{projectId}` | GET | `projects.py` | `ProjectService` |
| `/projects/{projectId}/forms` | GET | `forms.py` | — |
| `/forms/{formId}/instruments` | GET | `forms.py` | — |
| `/forms/{formId}/instrument-sheet` | GET | `instrument_sheet.py` | `InstrumentSheetService` |
| `/forms/{formId}/instrument-sheet/exports/excel` | POST | `instrument_sheet.py` | `InstrumentSheetService` |
| `/forms/{formId}/descriptives` | GET | `descriptives.py` | `DescriptiveService` |
| `/forms/{formId}/descriptives/stewart` | GET | `stewart.py` | `StewartService` |
| `/forms/{formId}/normality` | GET | `normality.py` | `NormalityService` |
| `/forms/{formId}/normality/questions/{id}` | GET | `normality.py` | `NormalityService` |
| `/forms/{formId}/normality/histogram` | GET | `normality.py` | `NormalityService` |
| `/forms/{formId}/correlations/pair` | POST | `correlations.py` | `CorrelationService` |
| `/forms/{formId}/correlations/matrix` | POST | `correlations.py` | `CorrelationService` |
| `/forms/{formId}/correlations/instruments/{id}/dimensions` | GET | `correlations.py` | `CorrelationService` |
| `/forms/{formId}/analysis/options` | GET | `analysis_orchestrator.py` | `AnalysisOrchestratorService` |
| `/forms/{formId}/analysis/run` | POST | `analysis_orchestrator.py` | `AnalysisOrchestratorService` |
| `/forms/{formId}/analysis/full-scan` | POST | `analysis_orchestrator.py` | `AnalysisOrchestratorService` |
| `/forms/{formId}/scoring/run` | POST | `scoring.py` | `AdvancedScoringService` |
| `/forms/{formId}/scoring/configs` | GET/POST | `scoring.py` | `ScoringConfigService` |
| `/forms/{formId}/scoring/options` | GET | `scoring.py` | `AdvancedScoringService` |
| `/forms/{formId}/scoring/baremos/resolution` | GET | `scoring.py` | `AdvancedScoringService` |
| `/scoring/configs/{id}/bands`, `/scoring/bands/{id}` | GET/POST/PATCH/DELETE | `scoring.py` | `ScoringConfigService` |
| `/form-instruments/{id}` | PATCH | `forms.py` | — |
| `/forms/{formId}/charts/recommended` | GET | `charts.py` | `ChartService` |
| `/forms/{formId}/apa-tables/batch` | POST | `apa_tables.py` | `ApaTableService` |
| `/forms/{formId}/chart-images` | GET | `chart_images.py` | `ChartImageService` |
| `/forms/{formId}/word-reports*` | GET/POST | `word_reports.py` | `WordReportService` |

> Nota: `AnalysisOrchestratorService` no es un motor estadístico propio — orquesta y reempaqueta los resultados de `DescriptiveService`, `NormalityService`, `CorrelationService`, `GroupComparisonService`, `CategoricalAssociationService` y `StatisticalDecisionService`, que son los mismos motores que consumen las Etapas 1-4 de `/results` por separado.
