$BASE = "http://localhost:8000"
$H = @{ "Content-Type" = "application/json" }
$formId = "587fe304-40d9-4ebd-9a6a-812424ff330c"
$slug = "escala-de-clima-organizacional-eco-15-247542"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " COLMENA - Corregir Options y Enviar Respuestas" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Get all questions
$questions = Invoke-RestMethod -Uri "$BASE/api/v1/forms/$formId/questions" -Method GET -Headers $H
Write-Host "Preguntas encontradas: $($questions.total)" -ForegroundColor Yellow

# Build option lookup: question_id -> { 1: optId, 2: optId, ... }
$optionMap = @{}

foreach ($q in $questions.items) {
  Write-Host "Creando opciones para: $($q.code)..." -ForegroundColor Yellow
  
  $likertOpts = @(
    @{ label = "Totalmente en desacuerdo"; value = "1"; score = 1.0; sort_order = 1 },
    @{ label = "En desacuerdo"; value = "2"; score = 2.0; sort_order = 2 },
    @{ label = "Ni de acuerdo ni en desacuerdo"; value = "3"; score = 3.0; sort_order = 3 },
    @{ label = "De acuerdo"; value = "4"; score = 4.0; sort_order = 4 },
    @{ label = "Totalmente de acuerdo"; value = "5"; score = 5.0; sort_order = 5 }
  )
  
  $qOptMap = @{}
  foreach ($opt in $likertOpts) {
    $created = Invoke-RestMethod -Uri "$BASE/api/v1/form-questions/$($q.id)/options" -Method POST -Headers $H -Body ($opt | ConvertTo-Json)
    $qOptMap[[int]$opt.value] = $created.id
    Write-Host "  $($opt.value): $($created.id)" -ForegroundColor Green
  }
  $optionMap[$q.id] = $qOptMap
}

# Now submit 12 responses using option_ids
Write-Host "`nEnviando 12 respuestas ficticias..." -ForegroundColor Yellow

$qIds = $questions.items | ForEach-Object { $_.id }

$patterns = @(
  @(4,5,4,5,4,3,4,4,5,3,5,4,4,5,4),
  @(3,3,2,3,3,2,3,2,3,2,3,3,2,3,2),
  @(5,5,4,5,5,4,5,5,4,4,5,5,5,4,5),
  @(2,1,2,2,1,2,1,2,1,2,2,1,2,2,1),
  @(4,4,3,4,4,3,4,3,4,3,4,4,3,4,4),
  @(3,4,3,3,4,3,3,4,3,3,4,3,4,3,3),
  @(5,4,5,4,5,4,5,4,5,5,4,5,5,4,5),
  @(2,3,2,3,2,3,2,3,2,2,3,2,2,3,2),
  @(4,4,4,4,3,4,4,4,3,4,5,4,4,3,4),
  @(1,2,1,1,2,1,2,1,2,1,1,2,1,1,2),
  @(4,5,4,4,5,4,5,4,5,4,4,5,5,4,5),
  @(3,3,3,3,3,3,3,3,3,3,3,3,3,3,3)
)

$respondentCodes = @("DOC001","DOC002","DOC003","DOC004","DOC005","DOC006","DOC007","DOC008","DOC009","DOC010","DOC011","DOC012")

for ($i = 0; $i -lt 12; $i++) {
  $p = $patterns[$i]
  $answers = @()
  for ($j = 0; $j -lt $qIds.Count; $j++) {
    $qId = $qIds[$j]
    $val = $p[$j]
    $optId = $optionMap[$qId][$val]
    $answers += @{ question_id = $qId; option_id = $optId }
  }
  $body = @{
    respondent_code = $respondentCodes[$i]
    answers = $answers
  } | ConvertTo-Json -Depth 5

  try {
    $resp = Invoke-RestMethod -Uri "$BASE/api/public/forms/$slug/responses" -Method POST -Headers $H -Body $body
    Write-Host "  $($respondentCodes[$i]) -> $($resp.id)" -ForegroundColor Green
  } catch {
    Write-Host "  ERROR $($respondentCodes[$i]): $($_.Exception.Message)" -ForegroundColor Red
    $errorBody = $_.ErrorDetails.Message
    if ($errorBody) { Write-Host "    Detail: $errorBody" -ForegroundColor Red }
  }
}

# Verify
Write-Host "`nVerificando..." -ForegroundColor Yellow
$responses = Invoke-RestMethod -Uri "$BASE/api/v1/forms/$formId/responses" -Method GET -Headers $H
Write-Host "Total respuestas: $($responses.total)" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " URLS PARA NAVEGAR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$projectId = "b83e3dbc-3b3d-491a-8de9-70f90253ec36"
Write-Host "  Workspace: http://localhost:5173/project/$projectId" -ForegroundColor Green
Write-Host "  Formulario: http://localhost:5173/project/$projectId/form" -ForegroundColor Green
Write-Host "  Telemetria: http://localhost:5173/project/$projectId/telemetry" -ForegroundColor Green
Write-Host "  Resultados: http://localhost:5173/project/$projectId/results" -ForegroundColor Green
Write-Host "  Reportes: http://localhost:5173/project/$projectId/reports" -ForegroundColor Green
Write-Host "  Link publico: http://localhost:5173/public/forms/$slug" -ForegroundColor Green
