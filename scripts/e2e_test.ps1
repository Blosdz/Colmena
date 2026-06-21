$BASE = "http://localhost:8000"
$H = @{ "Content-Type" = "application/json" }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " COLMENA - Prueba E2E Completa" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Crear Proyecto
Write-Host "`n[1/10] Creando proyecto..." -ForegroundColor Yellow
$proj = Invoke-RestMethod -Uri "$BASE/api/v1/projects" -Method POST -Headers $H -Body (@{
  title = "Clima Organizacional - Universidad Nacional"
  research_type = "Cuantitativo"
  approach = "Investigacion Empirica"
  sample_size_planned = 150
} | ConvertTo-Json)
Write-Host "  Proyecto ID: $($proj.id)" -ForegroundColor Green
$projectId = $proj.id

# 2. Crear Formulario
Write-Host "`n[2/10] Creando formulario..." -ForegroundColor Yellow
$form = Invoke-RestMethod -Uri "$BASE/api/v1/projects/$projectId/forms" -Method POST -Headers $H -Body (@{
  title = "Escala de Clima Organizacional (ECO-15)"
  description = "Instrumento validado para medir la percepcion del clima laboral en instituciones educativas superiores."
  status = "draft"
} | ConvertTo-Json)
Write-Host "  Form ID: $($form.id)" -ForegroundColor Green
$formId = $form.id

# 3. Crear Instrumento
Write-Host "`n[3/10] Creando instrumento..." -ForegroundColor Yellow
$inst = Invoke-RestMethod -Uri "$BASE/api/v1/forms/$formId/instruments" -Method POST -Headers $H -Body (@{
  name = "Clima Organizacional"
  acronym = "ECO15"
  description = "Escala de 15 items con 3 dimensiones"
} | ConvertTo-Json)
Write-Host "  Instrumento ID: $($inst.id)" -ForegroundColor Green
$instId = $inst.id

# 4. Crear Dimensiones
Write-Host "`n[4/10] Creando dimensiones..." -ForegroundColor Yellow
$dims = @(
  @{ name = "Liderazgo"; description = "Percepcion sobre la calidad del liderazgo directivo" },
  @{ name = "Comunicacion"; description = "Eficacia de los canales de comunicacion interna" },
  @{ name = "Satisfaccion"; description = "Nivel de satisfaccion general con el entorno de trabajo" }
)
$dimIds = @()
foreach ($d in $dims) {
  $dim = Invoke-RestMethod -Uri "$BASE/api/v1/form-instruments/$instId/dimensions" -Method POST -Headers $H -Body ($d | ConvertTo-Json)
  $dimIds += $dim.id
  Write-Host "  Dimension: $($d.name) -> $($dim.id)" -ForegroundColor Green
}

# 5. Crear Questions (15 items - 5 por dimension)
Write-Host "`n[5/10] Creando 15 items psicometricos..." -ForegroundColor Yellow
$items = @(
  # Liderazgo
  @{ code = "ECO01"; label = "Mi jefe inmediato demuestra interes genuino por el bienestar del equipo"; dim = 0 },
  @{ code = "ECO02"; label = "Las decisiones de la direccion son justas y transparentes"; dim = 0 },
  @{ code = "ECO03"; label = "Recibo retroalimentacion constructiva sobre mi desempeno"; dim = 0 },
  @{ code = "ECO04"; label = "Mi supervisor promueve un ambiente de confianza"; dim = 0 },
  @{ code = "ECO05"; label = "La direccion establece metas claras y alcanzables"; dim = 0 },
  # Comunicacion
  @{ code = "ECO06"; label = "La informacion importante se comunica oportunamente"; dim = 1 },
  @{ code = "ECO07"; label = "Existen canales efectivos para expresar opiniones"; dim = 1 },
  @{ code = "ECO08"; label = "Las reuniones de equipo son productivas y bien organizadas"; dim = 1 },
  @{ code = "ECO09"; label = "Me siento escuchado cuando planteo sugerencias"; dim = 1 },
  @{ code = "ECO10"; label = "La comunicacion entre departamentos es fluida"; dim = 1 },
  # Satisfaccion
  @{ code = "ECO11"; label = "Me siento orgulloso de pertenecer a esta institucion"; dim = 2 },
  @{ code = "ECO12"; label = "Las condiciones fisicas de trabajo son adecuadas"; dim = 2 },
  @{ code = "ECO13"; label = "Tengo oportunidades de desarrollo profesional"; dim = 2 },
  @{ code = "ECO14"; label = "El ambiente laboral favorece la colaboracion entre colegas"; dim = 2 },
  @{ code = "ECO15"; label = "Recomendaria esta institucion como lugar de trabajo"; dim = 2 }
)

$qIds = @()
$order = 1
foreach ($item in $items) {
  $q = Invoke-RestMethod -Uri "$BASE/api/v1/forms/$formId/questions" -Method POST -Headers $H -Body (@{
    label = $item.label
    code = $item.code
    question_type = "likert"
    is_required = $true
    order_index = $order
    dimension_id = $dimIds[$item.dim]
  } | ConvertTo-Json)
  $qIds += $q.id
  Write-Host "  $($item.code): $($q.id)" -ForegroundColor Green
  $order++

  # Create 5 Likert options
  $likertOpts = @(
    @{ label = "Totalmente en desacuerdo"; value = 1; order_index = 1 },
    @{ label = "En desacuerdo"; value = 2; order_index = 2 },
    @{ label = "Ni de acuerdo ni en desacuerdo"; value = 3; order_index = 3 },
    @{ label = "De acuerdo"; value = 4; order_index = 4 },
    @{ label = "Totalmente de acuerdo"; value = 5; order_index = 5 }
  )
  foreach ($opt in $likertOpts) {
    Invoke-RestMethod -Uri "$BASE/api/v1/form-questions/$($q.id)/options" -Method POST -Headers $H -Body ($opt | ConvertTo-Json) | Out-Null
  }
}

# 6. Crear Scoring Config (baremos)
Write-Host "`n[6/10] Configurando baremos..." -ForegroundColor Yellow
$scoringConfig = Invoke-RestMethod -Uri "$BASE/api/v1/forms/$formId/scoring/configs" -Method POST -Headers $H -Body (@{
  name = "Baremo General ECO-15"
  scope = "total"
  method = "sum"
  question_ids = $qIds
} | ConvertTo-Json)
Write-Host "  Scoring Config ID: $($scoringConfig.id)" -ForegroundColor Green

$bands = @(
  @{ name = "Muy Bajo"; min_score = 15; max_score = 30; color = "#EF4444"; interpretation = "Clima organizacional critico. Requiere intervencion inmediata." },
  @{ name = "Bajo"; min_score = 31; max_score = 40; color = "#F97316"; interpretation = "Clima desfavorable. Se recomienda diagnostico profundo." },
  @{ name = "Medio"; min_score = 41; max_score = 50; color = "#EAB308"; interpretation = "Clima moderado. Existen areas de mejora significativas." },
  @{ name = "Alto"; min_score = 51; max_score = 60; color = "#22C55E"; interpretation = "Buen clima laboral. Mantener estrategias actuales." },
  @{ name = "Muy Alto"; min_score = 61; max_score = 75; color = "#10B981"; interpretation = "Clima excelente. Modelo de referencia institucional." }
)
foreach ($b in $bands) {
  Invoke-RestMethod -Uri "$BASE/api/v1/scoring/configs/$($scoringConfig.id)/bands" -Method POST -Headers $H -Body ($b | ConvertTo-Json) | Out-Null
  Write-Host "  Banda: $($b.name) [$($b.min_score)-$($b.max_score)]" -ForegroundColor Green
}

# 7. Publicar formulario
Write-Host "`n[7/10] Publicando formulario..." -ForegroundColor Yellow
$pubLink = Invoke-RestMethod -Uri "$BASE/api/v1/forms/$formId/publish" -Method POST -Headers $H
$publicUrl = "http://localhost:5173/public/forms/$($pubLink.public_slug)"
Write-Host "  Link publico: $publicUrl" -ForegroundColor Green
Write-Host "  Slug: $($pubLink.public_slug)" -ForegroundColor Green

# 8. Simular 12 respuestas ficticias
Write-Host "`n[8/10] Enviando 12 respuestas ficticias..." -ForegroundColor Yellow
$respondents = @(
  @{ code = "DOC001"; sex = "Femenino"; age = 34 },
  @{ code = "DOC002"; sex = "Masculino"; age = 45 },
  @{ code = "DOC003"; sex = "Femenino"; age = 28 },
  @{ code = "DOC004"; sex = "Masculino"; age = 52 },
  @{ code = "DOC005"; sex = "Femenino"; age = 39 },
  @{ code = "DOC006"; sex = "Masculino"; age = 41 },
  @{ code = "DOC007"; sex = "Femenino"; age = 36 },
  @{ code = "DOC008"; sex = "Masculino"; age = 48 },
  @{ code = "DOC009"; sex = "Femenino"; age = 31 },
  @{ code = "DOC010"; sex = "Masculino"; age = 55 },
  @{ code = "DOC011"; sex = "Femenino"; age = 29 },
  @{ code = "DOC012"; sex = "Masculino"; age = 43 }
)

# Seed random patterns per respondent for realistic variation
$patterns = @(
  @(4,5,4,5,4,3,4,4,5,3,5,4,4,5,4),  # Alto
  @(3,3,2,3,3,2,3,2,3,2,3,3,2,3,2),  # Medio-bajo
  @(5,5,4,5,5,4,5,5,4,4,5,5,5,4,5),  # Muy alto
  @(2,1,2,2,1,2,1,2,1,2,2,1,2,2,1),  # Muy bajo
  @(4,4,3,4,4,3,4,3,4,3,4,4,3,4,4),  # Alto
  @(3,4,3,3,4,3,3,4,3,3,4,3,4,3,3),  # Medio
  @(5,4,5,4,5,4,5,4,5,5,4,5,5,4,5),  # Muy alto
  @(2,3,2,3,2,3,2,3,2,2,3,2,2,3,2),  # Bajo
  @(4,4,4,4,3,4,4,4,3,4,5,4,4,3,4),  # Alto
  @(1,2,1,1,2,1,2,1,2,1,1,2,1,1,2),  # Muy bajo
  @(4,5,4,4,5,4,5,4,5,4,4,5,5,4,5),  # Muy alto
  @(3,3,3,3,3,3,3,3,3,3,3,3,3,3,3)   # Medio
)

for ($i = 0; $i -lt $respondents.Count; $i++) {
  $r = $respondents[$i]
  $p = $patterns[$i]
  $answers = @()
  for ($j = 0; $j -lt $qIds.Count; $j++) {
    $answers += @{ question_id = $qIds[$j]; value = $p[$j] }
  }
  $body = @{
    respondent_code = $r.code
    answers = $answers
  } | ConvertTo-Json -Depth 5

  $resp = Invoke-RestMethod -Uri "$BASE/api/public/forms/$($pubLink.public_slug)/responses" -Method POST -Headers $H -Body $body
  Write-Host "  $($r.code) ($($r.sex), $($r.age)a) -> $($resp.id)" -ForegroundColor Green
}

# 9. Verificar telemetria
Write-Host "`n[9/10] Verificando telemetria..." -ForegroundColor Yellow
$responses = Invoke-RestMethod -Uri "$BASE/api/v1/forms/$formId/responses" -Method GET -Headers $H
Write-Host "  Total respuestas: $($responses.total)" -ForegroundColor Green

# 10. Resumen final
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " RESUMEN DEL PROCESO COMPLETO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Proyecto: Clima Organizacional - Universidad Nacional" -ForegroundColor White
Write-Host "  Project ID: $projectId" -ForegroundColor White
Write-Host "  Form ID: $formId" -ForegroundColor White
Write-Host "  Instrumento: ECO-15 (15 items, 3 dimensiones)" -ForegroundColor White
Write-Host "  Baremos: 5 niveles (Muy Bajo a Muy Alto)" -ForegroundColor White
Write-Host "  Respuestas: $($responses.total)" -ForegroundColor White
Write-Host "  Link publico: $publicUrl" -ForegroundColor Green
Write-Host "  Workspace: http://localhost:5173/project/$projectId" -ForegroundColor Green
Write-Host "  Formulario: http://localhost:5173/project/$projectId/form" -ForegroundColor Green
Write-Host "  Telemetria: http://localhost:5173/project/$projectId/telemetry" -ForegroundColor Green
Write-Host "  Resultados: http://localhost:5173/project/$projectId/results" -ForegroundColor Green
Write-Host "  Reportes: http://localhost:5173/project/$projectId/reports" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
