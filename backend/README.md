# Backend de Colmena

## Stack base

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- Pydantic + Pydantic Settings
- SQLite para desarrollo local
- Alembic para migraciones
- pytest + TestClient para pruebas

## Preparar entorno virtual

```powershell
cd E:\Colmena\backend
python -m venv .venv
.\.venv\Scripts\activate
```

## Instalar dependencias

```powershell
pip install -r requirements.txt
```

## Aplicar migraciones

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Ejecutar la API

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

## Flujo esperado completo

```powershell
cd E:\Colmena\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

## Base SQLite

- Ruta por defecto: `E:\Colmena\backend\data\db\colmena.db`
- La ruta efectiva se resuelve desde la carpeta `backend`.
- SQLite queda con `foreign_keys=ON` al abrir cada conexion.

## Endpoints disponibles

### Base

- `GET /`
- `GET /api/health`
- `GET /docs`

### Proyectos

- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`

### Variables de proyecto

- `POST /api/v1/projects/{project_id}/variables`
- `GET /api/v1/projects/{project_id}/variables`
- `GET /api/v1/project-variables/{variable_id}`
- `PATCH /api/v1/project-variables/{variable_id}`
- `DELETE /api/v1/project-variables/{variable_id}`

### Formularios internos

- `POST /api/v1/projects/{project_id}/forms`
- `GET /api/v1/projects/{project_id}/forms`
- `GET /api/v1/forms/{form_id}`
- `PATCH /api/v1/forms/{form_id}`
- `DELETE /api/v1/forms/{form_id}`
- `POST /api/v1/forms/{form_id}/publish`
- `POST /api/v1/forms/{form_id}/close`
- `POST /api/v1/forms/{form_id}/reopen`
- `GET /api/v1/forms/{form_id}/public-link`

### Secciones

- `POST /api/v1/forms/{form_id}/sections`
- `GET /api/v1/forms/{form_id}/sections`
- `PATCH /api/v1/form-sections/{section_id}`
- `DELETE /api/v1/form-sections/{section_id}`

### Instrumentos

- `POST /api/v1/forms/{form_id}/instruments`
- `GET /api/v1/forms/{form_id}/instruments`
- `PATCH /api/v1/form-instruments/{instrument_id}`
- `DELETE /api/v1/form-instruments/{instrument_id}`

### Dimensiones

- `POST /api/v1/form-instruments/{instrument_id}/dimensions`
- `GET /api/v1/form-instruments/{instrument_id}/dimensions`
- `PATCH /api/v1/form-dimensions/{dimension_id}`
- `DELETE /api/v1/form-dimensions/{dimension_id}`

### Preguntas

- `POST /api/v1/forms/{form_id}/questions`
- `GET /api/v1/forms/{form_id}/questions`
- `GET /api/v1/form-questions/{question_id}`
- `PATCH /api/v1/form-questions/{question_id}`
- `DELETE /api/v1/form-questions/{question_id}`

### Opciones

- `POST /api/v1/form-questions/{question_id}/options`
- `GET /api/v1/form-questions/{question_id}/options`
- `PATCH /api/v1/form-question-options/{option_id}`
- `DELETE /api/v1/form-question-options/{option_id}`

### Respuestas internas

- `POST /api/v1/forms/{form_id}/responses`
- `GET /api/v1/forms/{form_id}/responses`
- `GET /api/v1/form-responses/{response_id}`

### Dataset, completitud y exportaciones

- `GET /api/v1/forms/{form_id}/dataset`
- `GET /api/v1/forms/{form_id}/dataset/preview`
- `GET /api/v1/forms/{form_id}/data-dictionary`
- `GET /api/v1/forms/{form_id}/completeness`
- `POST /api/v1/forms/{form_id}/exports/excel`
- `POST /api/v1/forms/{form_id}/exports/csv`
- `GET /api/v1/forms/{form_id}/exports`
- `PATCH /api/v1/form-answers/{answer_id}`
- `PATCH /api/v1/form-responses/{response_id}/status`
- `POST /api/v1/form-responses/{response_id}/restore`

### Motor descriptivo

- `GET /api/v1/forms/{form_id}/descriptives/overview`
- `GET /api/v1/forms/{form_id}/descriptives`
- `GET /api/v1/forms/{form_id}/descriptives/questions/{question_id}`
- `GET /api/v1/forms/{form_id}/descriptives/dimensions`
- `GET /api/v1/forms/{form_id}/descriptives/instruments`
- `GET /api/v1/forms/{form_id}/descriptives/project-variables`
- `GET /api/v1/forms/{form_id}/descriptives/crosstab`
- `POST /api/v1/forms/{form_id}/descriptives/run`

### Normalidad y decision estadistica inicial

- `GET /api/v1/forms/{form_id}/normality`
- `GET /api/v1/forms/{form_id}/normality/questions/{question_id}`
- `GET /api/v1/forms/{form_id}/normality/dimensions`
- `GET /api/v1/forms/{form_id}/normality/instruments`
- `GET /api/v1/forms/{form_id}/normality/project-variables`
- `POST /api/v1/forms/{form_id}/normality/run`
- `POST /api/v1/forms/{form_id}/statistical-decision`

### Correlaciones iniciales

- `POST /api/v1/forms/{form_id}/correlations/pair`
- `POST /api/v1/forms/{form_id}/correlations/matrix`
- `GET /api/v1/forms/{form_id}/correlations/instruments/{instrument_id}/dimensions`
- `GET /api/v1/forms/{form_id}/correlations/instruments`
- `GET /api/v1/forms/{form_id}/correlations/project-variables`

### Comparaciones entre grupos

- `POST /api/v1/forms/{form_id}/group-comparisons`
- `GET /api/v1/forms/{form_id}/group-comparisons/options`

### Asociacion categorica

- `POST /api/v1/forms/{form_id}/categorical-associations`
- `GET /api/v1/forms/{form_id}/categorical-associations/options`

### Orquestador de analisis

- `POST /api/v1/forms/{form_id}/analysis/run`
- `POST /api/v1/forms/{form_id}/analysis/full-scan`
- `GET /api/v1/forms/{form_id}/analysis/options`
- `GET /api/v1/forms/{form_id}/analysis/summary`

### Tablas APA 7 iniciales

- `POST /api/v1/forms/{form_id}/apa-tables/generate`
- `POST /api/v1/forms/{form_id}/apa-tables/batch`
- `POST /api/v1/forms/{form_id}/apa-tables/from-analysis-run/{analysis_run_id}`
- `POST /api/v1/forms/{form_id}/apa-tables/from-orchestrated-run/{analysis_run_id}`
- `POST /api/v1/forms/{form_id}/apa-tables/export/markdown`
- `POST /api/v1/forms/{form_id}/apa-tables/export/html`
- `GET /api/v1/forms/{form_id}/apa-tables/options`

### Publicacion y respuestas publicas

- `GET /api/public/forms/{public_slug}`
- `POST /api/public/forms/{public_slug}/responses`

## Validar health

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/health" -Method GET
```

## Crear un proyecto

```powershell
$projectBody = @{
  title = "Relacion entre ansiedad academica y rendimiento en estudiantes universitarios"
  research_type = "correlacional"
  design_type = "no experimental transversal"
  approach = "cuantitativo"
  institution = "Universidad de prueba"
  faculty = "Facultad de Ciencias Sociales"
  career = "Psicologia"
  sample_size_planned = 120
} | ConvertTo-Json

$project = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/projects" -Method POST -Body $projectBody -ContentType "application/json"
```

## Crear una variable

```powershell
$variableBody = @{
  name = "Sexo"
  code = "sex"
  variable_role = "sociodemographic"
  measurement_level = "nominal"
  data_type = "categorical"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/projects/$($project.id)/variables" -Method POST -Body $variableBody -ContentType "application/json"
```

## Crear un formulario

```powershell
$formBody = @{
  title = "Formulario de investigacion"
  description = "Formulario inicial para recoleccion de datos."
  instructions = "Responda con sinceridad."
} | ConvertTo-Json

$form = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/projects/$($project.id)/forms" -Method POST -Body $formBody -ContentType "application/json"
```

## Crear una pregunta

```powershell
$questionBody = @{
  code = "sex"
  label = "Sexo"
  question_type = "single_choice"
  question_role = "sociodemographic"
  measurement_level = "nominal"
  data_type = "categorical"
  is_required = $true
} | ConvertTo-Json

$question = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/questions" -Method POST -Body $questionBody -ContentType "application/json"
```

## Crear una opcion

```powershell
$optionBody = @{
  label = "Femenino"
  value = "F"
  score = 2
  sort_order = 1
} | ConvertTo-Json

$option = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/form-questions/$($question.id)/options" -Method POST -Body $optionBody -ContentType "application/json"
```

## Publicar un formulario

```powershell
$published = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/publish" -Method POST
```

## Obtener link publico

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/public-link" -Method GET
```

## Consultar formulario publico por slug

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/public/forms/$($published.public_slug)" -Method GET
```

## Enviar respuesta publica

```powershell
$answerBody = @{
  respondent_code = $null
  answers = @(
    @{
      question_id = $question.id
      option_id = $option.id
      value_text = $null
      value_number = $null
      value_date = $null
      value_json = $null
    }
  )
  metadata_json = @{
    source = "manual-test"
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/public/forms/$($published.public_slug)/responses" -Method POST -Body $answerBody -ContentType "application/json"
```

## Cerrar y reabrir formulario

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/close" -Method POST
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/reopen" -Method POST
```

## Estrategia de reapertura

- `reopen` conserva `collect_closed_at` como historial de cierre.
- Si el formulario no tenia `public_slug`, se genera en la reapertura.
- Un formulario `draft` o `archived` no se expone publicamente.
- Un formulario `closed` devuelve error al intentar responder por endpoint publico.

## Enviar una respuesta interna

```powershell
$responseBody = @{
  respondent_code = "R-001"
  status = "complete"
  source = "internal"
  answers = @(
    @{
      question_id = $question.id
      value_text = "female"
    }
  )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/responses" -Method POST -Body $responseBody -ContentType "application/json"
```

## Consultar dataset tabular

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/dataset?mode=mixed" -Method GET
```

## Consultar vista previa

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/dataset/preview?mode=mixed" -Method GET
```

## Consultar diccionario de datos

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/data-dictionary" -Method GET
```

## Consultar completitud

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/completeness" -Method GET
```

## Exportar dataset a Excel

```powershell
$exportBody = @{
  mode = "mixed"
  include_metadata = $true
  include_discarded = $false
  expand_multiple_choice = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/exports/excel" -Method POST -Body $exportBody -ContentType "application/json"
```

## Exportar dataset a CSV

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/exports/csv" -Method POST -Body $exportBody -ContentType "application/json"
```

## Listar exportaciones del formulario

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/exports" -Method GET
```

## Editar una respuesta individual

```powershell
$answerUpdateBody = @{
  value_number = 29
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/form-answers/ANSWER_ID" -Method PATCH -Body $answerUpdateBody -ContentType "application/json"
```

## Descartar y restaurar una respuesta

```powershell
$statusBody = @{
  status = "discarded"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/form-responses/RESPONSE_ID/status" -Method PATCH -Body $statusBody -ContentType "application/json"
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/form-responses/RESPONSE_ID/restore" -Method POST
```

## Consultar overview descriptivo

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/descriptives/overview" -Method GET
```

## Consultar descriptivos completos

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/descriptives?decimals=3&score_aggregation=mean" -Method GET
```

## Consultar descriptivo por pregunta

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/descriptives/questions/QUESTION_ID" -Method GET
```

## Consultar descriptivos por dimension

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/descriptives/dimensions?score_aggregation=mean" -Method GET
```

## Consultar descriptivos por instrumento

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/descriptives/instruments?score_aggregation=mean" -Method GET
```

## Consultar tabla cruzada descriptiva

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/descriptives/crosstab?row_question_id=ROW_QUESTION_ID&column_question_id=COLUMN_QUESTION_ID" -Method GET
```

## Ejecutar corrida descriptiva

```powershell
$descriptiveRunBody = @{
  include_discarded = $false
  decimals = 3
  score_aggregation = "mean"
  store_result = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/descriptives/run" -Method POST -Body $descriptiveRunBody -ContentType "application/json"
```

## Consultar normalidad completa

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/normality?method=auto&alpha=0.05&decimals=3" -Method GET
```

## Consultar normalidad por pregunta

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/normality/questions/QUESTION_ID" -Method GET
```

## Ejecutar corrida de normalidad

```powershell
$normalityBody = @{
  method = "auto"
  alpha = 0.05
  decimals = 3
  include_discarded = $false
  score_aggregation = "mean"
  store_result = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/normality/run" -Method POST -Body $normalityBody -ContentType "application/json"
```

## Solicitar decision estadistica inicial

```powershell
$decisionBody = @{
  analysis_goal = "correlation"
  variables = @(
    @{
      question_id = "QUESTION_ID_1"
      role = "x"
    },
    @{
      question_id = "QUESTION_ID_2"
      role = "y"
    }
  )
  alpha = 0.05
  normality_method = "auto"
  score_aggregation = "mean"
  include_discarded = $false
  store_result = $true
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/statistical-decision" -Method POST -Body $decisionBody -ContentType "application/json"
```

## Ejecutar correlacion automatica entre dos targets

```powershell
$correlationBody = @"
{
  "x": {
    "target_type": "question",
    "target_id": "QUESTION_ID_1"
  },
  "y": {
    "target_type": "question",
    "target_id": "QUESTION_ID_2"
  },
  "method": "auto",
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "store_result": true
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/correlations/pair" -Method POST -Body $correlationBody -ContentType "application/json"
```

## Forzar Spearman, Pearson o Kendall

```powershell
$correlationBody = $correlationBody.Replace('"method": "auto"', '"method": "spearman"')
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/correlations/pair" -Method POST -Body $correlationBody -ContentType "application/json"
```

## Generar matriz de correlaciones

```powershell
$matrixBody = @"
{
  "targets": [
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_1"
    },
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_2"
    },
    {
      "target_type": "dimension",
      "target_id": "DIMENSION_ID"
    }
  ],
  "method": "auto",
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "store_result": true
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/correlations/matrix" -Method POST -Body $matrixBody -ContentType "application/json"
```

## Correlacionar dimensiones, instrumentos o variables de proyecto

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/correlations/instruments/INSTRUMENT_ID/dimensions?method=auto" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/correlations/instruments?method=auto" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/correlations/project-variables?method=auto" -Method GET
```

## Interpretar coefficient, p_value, magnitude y direction

- `coefficient`: intensidad y signo de la asociacion.
- `p_value`: evidencia estadistica frente al alpha definido.
- `direction`: `positive`, `negative` o `none`.
- `magnitude`: `negligible`, `weak`, `moderate`, `strong`, `very_strong` o `almost_perfect`.
- La interpretacion siempre describe asociacion, nunca causalidad.

## Ejecutar comparacion automatica entre grupos

```powershell
$comparisonBody = @"
{
  "outcome": {
    "target_type": "question",
    "target_id": "QUESTION_ID_OUTCOME"
  },
  "group": {
    "target_type": "question",
    "target_id": "QUESTION_ID_GROUP"
  },
  "method": "auto",
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "store_result": true
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/group-comparisons" -Method POST -Body $comparisonBody -ContentType "application/json"
```

## Forzar t de Student, Welch, Mann-Whitney, ANOVA o Kruskal-Wallis

```powershell
$comparisonBody = $comparisonBody.Replace('"method": "auto"', '"method": "t_student_independent"')
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/group-comparisons" -Method POST -Body $comparisonBody -ContentType "application/json"
```

## Consultar opciones para frontend

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/group-comparisons/options" -Method GET
```

## Interpretar statistic, p_value, effect_size y group_descriptives

- `statistic`: valor del estadistico principal de la prueba ejecutada.
- `p_value`: evidencia estadistica frente al alpha definido.
- `effect_size`: tamano del efecto inicial como `cohens_d`, `eta_squared`, `epsilon_squared` o `rank_biserial`.
- `group_descriptives`: resumen numerico por grupo para lectura comparativa.
- La interpretacion automatica describe diferencias estadisticas, nunca causalidad.

## Ejecutar asociacion categorica

```powershell
$associationBody = @"
{
  "row": {
    "target_type": "question",
    "target_id": "QUESTION_ID_ROW"
  },
  "column": {
    "target_type": "question",
    "target_id": "QUESTION_ID_COLUMN"
  },
  "method": "auto",
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "store_result": true
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/categorical-associations" -Method POST -Body $associationBody -ContentType "application/json"
```

## Forzar chi cuadrado o Fisher exacto

```powershell
$associationBody = $associationBody.Replace('"method": "auto"', '"method": "chi_square"')
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/categorical-associations" -Method POST -Body $associationBody -ContentType "application/json"
```

## Consultar opciones categoricas para frontend

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/categorical-associations/options" -Method GET
```

## Interpretar p_value, V de Cramer, Phi y odds_ratio

- `p_value`: evidencia estadistica frente al alpha definido.
- `V de Cramer`: tamano del efecto para tablas generales.
- `Phi`: tamano del efecto para tablas 2x2.
- `odds_ratio`: razon de momios reportada cuando `Fisher exacto` aplica en tablas 2x2.
- `expected_table`: frecuencias esperadas usadas para revisar la estabilidad de `chi_square`.
- La interpretacion automatica siempre describe asociacion estadistica, nunca causalidad.

## Ejecutar analisis guiado

```powershell
$analysisBody = @"
{
  "analysis_goal": "correlation",
  "targets": [
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_1",
      "role": "x"
    },
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_2",
      "role": "y"
    }
  ],
  "method": "auto",
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "store_result": true,
  "options": {
    "include_normality": true,
    "include_descriptives": true,
    "include_recommendations": true
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/analysis/run" -Method POST -Body $analysisBody -ContentType "application/json"
```

## Ejecutar resumen descriptivo guiado

```powershell
$descriptiveAnalysisBody = @"
{
  "analysis_goal": "descriptive_summary",
  "targets": [],
  "method": "auto",
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "store_result": true
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/analysis/run" -Method POST -Body $descriptiveAnalysisBody -ContentType "application/json"
```

## Ejecutar comparacion guiada

```powershell
$comparisonAnalysisBody = @"
{
  "analysis_goal": "group_comparison",
  "targets": [
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_OUTCOME",
      "role": "outcome"
    },
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_GROUP",
      "role": "group"
    }
  ],
  "method": "auto",
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "store_result": true
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/analysis/run" -Method POST -Body $comparisonAnalysisBody -ContentType "application/json"
```

## Ejecutar asociacion categorica guiada

```powershell
$associationAnalysisBody = @"
{
  "analysis_goal": "categorical_association",
  "targets": [
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_ROW",
      "role": "row"
    },
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_COLUMN",
      "role": "column"
    }
  ],
  "method": "auto",
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "store_result": true
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/analysis/run" -Method POST -Body $associationAnalysisBody -ContentType "application/json"
```

## Ejecutar full scan

```powershell
$fullScanBody = @"
{
  "alpha": 0.05,
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "store_result": true,
  "options": {
    "max_targets": 10,
    "max_pairwise_tests": 30
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/analysis/full-scan" -Method POST -Body $fullScanBody -ContentType "application/json"
```

## Consultar analysis options y summary

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/analysis/options" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/analysis/summary" -Method GET
```

## Interpretar executive_summary, result_blocks, apa_table_blocks y chart_blocks

- `executive_summary`: resumen breve para una futura pantalla principal de resultados.
- `result_blocks`: bloques reutilizables con descriptivos, normalidad, decisiones y pruebas aplicadas.
- `apa_table_blocks`: estructura base para futuras tablas APA 7, todavia no formateadas.
- `chart_blocks`: sugerencias de visualizacion premium para fases posteriores.
- `plain_language_explanation`: explicacion clara para usuarios no estadisticos.

## Generar tabla APA de frecuencias

```powershell
$apaFrequencyBody = @"
{
  "table_type": "frequencies",
  "source_type": "live",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {
    "question_ids": ["QUESTION_ID"]
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/generate" -Method POST -Body $apaFrequencyBody -ContentType "application/json"
```

## Generar tabla APA de descriptivos

```powershell
$apaDescriptivesBody = @"
{
  "table_type": "descriptives",
  "source_type": "live",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {}
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/generate" -Method POST -Body $apaDescriptivesBody -ContentType "application/json"
```

## Generar tabla APA de normalidad

```powershell
$apaNormalityBody = @"
{
  "table_type": "normality",
  "source_type": "live",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {}
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/generate" -Method POST -Body $apaNormalityBody -ContentType "application/json"
```

## Generar tabla APA de correlacion

```powershell
$apaCorrelationBody = @"
{
  "table_type": "correlation",
  "source_type": "live",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {
    "x": {
      "target_type": "question",
      "target_id": "QUESTION_ID_1"
    },
    "y": {
      "target_type": "question",
      "target_id": "QUESTION_ID_2"
    },
    "method": "auto"
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/generate" -Method POST -Body $apaCorrelationBody -ContentType "application/json"
```

## Generar tabla APA de comparacion

```powershell
$apaComparisonBody = @"
{
  "table_type": "group_comparison",
  "source_type": "live",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {
    "outcome": {
      "target_type": "question",
      "target_id": "QUESTION_ID_OUTCOME"
    },
    "group": {
      "target_type": "question",
      "target_id": "QUESTION_ID_GROUP"
    },
    "method": "auto"
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/generate" -Method POST -Body $apaComparisonBody -ContentType "application/json"
```

## Generar tabla APA de asociacion categorica

```powershell
$apaAssociationBody = @"
{
  "table_type": "categorical_association",
  "source_type": "live",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {
    "row": {
      "target_type": "question",
      "target_id": "QUESTION_ID_ROW"
    },
    "column": {
      "target_type": "question",
      "target_id": "QUESTION_ID_COLUMN"
    },
    "method": "auto"
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/generate" -Method POST -Body $apaAssociationBody -ContentType "application/json"
```

## Generar tablas APA desde AnalysisRun

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/from-analysis-run/ANALYSIS_RUN_ID" -Method POST
```

## Generar tablas APA desde corrida orquestada

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/from-orchestrated-run/ANALYSIS_RUN_ID" -Method POST
```

## Generar lote de tablas APA

```powershell
$apaBatchBody = @"
{
  "form_id": "FORM_ID",
  "table_types": ["frequencies", "descriptives", "normality"],
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {}
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/batch" -Method POST -Body $apaBatchBody -ContentType "application/json"
```

## Exportar tablas APA a Markdown y HTML

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/export/markdown" -Method POST -Body $apaBatchBody -ContentType "application/json"
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/export/html" -Method POST -Body $apaBatchBody -ContentType "application/json"
```

## Consultar opciones de tablas APA

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/apa-tables/options" -Method GET
```

## Generar grafico de barras

```powershell
$chartBody = @"
{
  "chart_type": "bar",
  "source_type": "live",
  "analysis_goal": "frequencies",
  "targets": [
    {
      "target_type": "question",
      "target_id": "QUESTION_ID",
      "role": "target"
    }
  ],
  "theme": "colmena_premium",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {
    "show_percentages": true,
    "show_frequencies": true
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/generate" -Method POST -Body $chartBody -ContentType "application/json"
```

## Generar grafico donut

```powershell
$chartBody = $chartBody -replace '"bar"', '"donut"'
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/generate" -Method POST -Body $chartBody -ContentType "application/json"
```

## Generar histograma o boxplot

```powershell
$numericChartBody = @"
{
  "chart_type": "histogram",
  "source_type": "live",
  "analysis_goal": "descriptives",
  "targets": [
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_NUMERIC",
      "role": "target"
    }
  ],
  "theme": "academic_light",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {}
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/generate" -Method POST -Body $numericChartBody -ContentType "application/json"
```

## Generar scatter o heatmap

```powershell
$scatterBody = @"
{
  "chart_type": "scatter",
  "source_type": "live",
  "analysis_goal": "correlation",
  "targets": [
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_X",
      "role": "x"
    },
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_Y",
      "role": "y"
    }
  ],
  "theme": "colmena_premium",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {
    "method": "pearson"
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/generate" -Method POST -Body $scatterBody -ContentType "application/json"
```

## Generar barras agrupadas

```powershell
$associationChartBody = @"
{
  "chart_type": "grouped_bar",
  "source_type": "live",
  "analysis_goal": "categorical_association",
  "targets": [
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_ROW",
      "role": "row"
    },
    {
      "target_type": "question",
      "target_id": "QUESTION_ID_COLUMN",
      "role": "column"
    }
  ],
  "theme": "presentation_clean",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {
    "method": "chi_square"
  }
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/generate" -Method POST -Body $associationChartBody -ContentType "application/json"
```

## Generar graficos desde AnalysisRun u orquestador

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/from-analysis-run/ANALYSIS_RUN_ID" -Method POST
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/from-orchestrated-run/ANALYSIS_RUN_ID" -Method POST
```

## Consultar graficos recomendados y opciones

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/recommended?theme=colmena_premium&max_charts=10" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/options" -Method GET
```

## Exportar especificaciones JSON

```powershell
$chartExportBody = @"
{
  "format": "json",
  "source_type": "live",
  "chart_types": ["bar", "histogram", "boxplot"],
  "theme": "colmena_premium",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "options": {}
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/charts/export/json" -Method POST -Body $chartExportBody -ContentType "application/json"
```

## Interpretar salidas de graficos

- `plotly_data`, `plotly_layout` y `plotly_config`: contrato visual inicial para el frontend React futuro.
- `editable_options`: controles que la UI premium podra activar despues.
- `recommended_alternatives`: tipos de grafico alternativos para el mismo resultado.
- `plain_language_explanation`: explicacion breve pensada para usuarios no estadisticos.
- `academic_note`: nota formal para presentaciones o documentos academicos.

## Interpretar salidas APA

- `markdown`: vista rapida para revision manual o control de cambios.
- `html`: estructura limpia para futura vista previa web.
- `notes`: notas automáticas segun tipo de tabla y supuestos relevantes.
- `warnings`: alertas metodologicas o de datos insuficientes.
- `ready_for_word`: indica si la tabla ya esta estructurada para una futura conversion a Word, aunque esa fase aun no se ejecuta.

## Correr tests

```powershell
pytest
```

## Alembic

- Configuracion principal: `E:\Colmena\backend\alembic.ini`
- Entorno de migraciones: `E:\Colmena\backend\alembic`
- Migraciones actuales:
  - `20260505_01_create_projects.py`
  - `20260505_02_create_form_domain.py`
  - `20260505_04_create_export_artifacts.py`
  - `20260506_05_create_analysis_runs.py`

## Informes Word APA 7 iniciales

### Generar informe Word completo

```powershell
$wordBody = @"
{
  "report_type": "full_form_report",
  "source_type": "mixed",
  "analysis_run_ids": [],
  "orchestrated_analysis_run_id": null,
  "title": "Informe de resultados estadisticos",
  "subtitle": "Reporte generado por Colmena",
  "decimals": 3,
  "include_discarded": false,
  "score_aggregation": "mean",
  "include_charts_placeholders": true,
  "include_plain_language_explanations": true,
  "include_technical_appendix": false,
  "include_cover": true,
  "include_methodology_summary": true,
  "options": {}
}
"@

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/word-reports/generate" -Method POST -Body $wordBody -ContentType "application/json"
```

### Generar desde AnalysisRun u orquestador

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/word-reports/from-analysis-run/ANALYSIS_RUN_ID" -Method POST
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/word-reports/from-orchestrated-run/ANALYSIS_RUN_ID" -Method POST
```

### Consultar opciones y listar informes

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/word-reports/options" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/$($form.id)/word-reports" -Method GET
```

### Que incluye el informe

- portada simple
- datos generales del proyecto y formulario
- resumen de base y muestra
- resultados descriptivos
- normalidad
- bloques inferenciales disponibles
- tablas APA ya generadas
- interpretaciones automaticas
- placeholders de graficos
- conclusiones estadisticas preliminares

### Que no incluye todavia

- PDF
- graficos renderizados como imagen
- exportacion PNG
- frontend
- maquetacion premium final

### Dondese guardan los .docx

- `E:\Colmena\backend\data\exports`

## Imagenes de graficos y Word con recursos reales

### Subir imagen de grafico

```powershell
$pngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
$body = @{
  chart_id = "manual-test"
  chart_type = "bar"
  title = "Grafico de prueba"
  format = "png"
  data_url = "data:image/png;base64,$pngBase64"
  file_name = "grafico_prueba.png"
  source_type = "chart_editor"
  analysis_run_id = $null
  metadata_json = @{ theme = "colmena_premium" }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/chart-images" -Method POST -Body $body -ContentType "application/json"
```

### Listar imagenes y recursos listos para Word

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/chart-images" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/chart-images/word-ready" -Method GET
```

### Generar Word con imagenes reales o solo placeholders

```powershell
$reportBody = @{
  report_type = "full_form_report"
  source_type = "mixed"
  analysis_run_ids = @()
  orchestrated_analysis_run_id = $null
  title = "Informe de resultados estadisticos"
  subtitle = "Reporte generado por Colmena"
  decimals = 3
  include_discarded = $false
  score_aggregation = "mean"
  include_charts_placeholders = $true
  include_chart_images = $true
  chart_image_mode = "images_if_available"
  chart_image_artifact_ids = @()
  include_plain_language_explanations = $true
  include_technical_appendix = $false
  include_cover = $true
  include_methodology_summary = $true
  options = @{}
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/word-reports/generate" -Method POST -Body $reportBody -ContentType "application/json"
```

### Limites actuales

- PNG es el formato principal para Word.
- SVG puede guardarse como artefacto, pero no se inserta en `.docx` en esta fase.
- Tamano maximo por imagen: `5 MB`.
- Los archivos se guardan solo en `E:\Colmena\backend\data\exports`.

## Scoring avanzado, baremos y escalas de control

### Endpoints principales

- `GET /api/v1/forms/{form_id}/scoring/configs`
- `POST /api/v1/forms/{form_id}/scoring/configs`
- `POST /api/v1/scoring/configs/{config_id}/bands`
- `GET /api/v1/forms/{form_id}/control-scales`
- `POST /api/v1/forms/{form_id}/control-scales`
- `POST /api/v1/forms/{form_id}/scoring/run`
- `GET /api/v1/forms/{form_id}/scoring/results`
- `GET /api/v1/forms/{form_id}/scoring/dataset`
- `GET /api/v1/forms/{form_id}/scoring/options`

### Que permite

- definir `ScoringConfig` por instrumento o dimension
- registrar baremos en `ScoreBand`
- registrar escalas de control en `ControlScale`
- calcular `ResponseScore` y `ResponseControlFlag`
- enriquecer dataset con columnas `score_*`, `band_*`, `interpretation_*` y `validity_*`
- alimentar descriptivos, APA, charts y Word con resultados scoreados

### Ejemplo PowerShell para crear scoring config

```powershell
$body = @{
  instrument_id = "INSTRUMENT_ID"
  name = "Puntaje total"
  code = "score_total"
  scoring_level = "instrument"
  aggregation_method = "mean"
  missing_policy = "allow_partial"
  min_completion_percent = 70
  reverse_scoring_enabled = $true
  interpretation_enabled = $true
  config_json = @{
    source = "wizard"
  }
  bands = @(
    @{ label = "Bajo"; code = "low"; min_value = 1.0; max_value = 2.4; interpretation = "Nivel bajo" }
    @{ label = "Medio"; code = "medium"; min_value = 2.5; max_value = 3.6; interpretation = "Nivel medio" }
    @{ label = "Alto"; code = "high"; min_value = 3.7; max_value = 5.0; interpretation = "Nivel alto" }
  )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/scoring/configs" -Method POST -Body $body -ContentType "application/json"
```

### Ejemplo PowerShell para crear escala de control

```powershell
$body = @{
  instrument_id = "INSTRUMENT_ID"
  name = "Escala de mentira"
  code = "lie_scale"
  control_type = "lie"
  rule_type = "mean_threshold"
  threshold = 4
  comparison_operator = "gte"
  flag_level = "warning"
  message = "Revisar consistencia de respuestas."
  items = @(
    @{ question_id = "QUESTION_ID_1"; weight = 1.0 }
    @{ question_id = "QUESTION_ID_2"; weight = 1.0 }
  )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/control-scales" -Method POST -Body $body -ContentType "application/json"
```

### Ejecutar scoring y consultar dataset enriquecido

```powershell
$runBody = @{
  include_discarded = $false
  recalculate = $true
  store_result = $true
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/scoring/run" -Method POST -Body $runBody -ContentType "application/json"
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/scoring/results" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/forms/FORM_ID/scoring/dataset" -Method GET
```
