# Architecture

Colmena se plantea con una arquitectura por capas de dominio para facilitar escalabilidad, mantenibilidad e integracion futura.

## Convencion de API

- La API interna versionada usa `api/v1`.
- Los endpoints publicos usan `api/public`.
- Los endpoints transversales de salud se mantienen en `api/health`.

## Separacion entre interno y publico

### Endpoints internos

Se usan para administrar proyectos, variables, formularios, secciones, instrumentos, preguntas, opciones y respuestas operativas:

- `api/v1/projects/...`
- `api/v1/forms/...`

### Endpoints publicos

Se usan para exponer formularios ya publicados y recibir respuestas por link:

- `GET /api/public/forms/{public_slug}`
- `POST /api/public/forms/{public_slug}/responses`

## Agregado raiz: Project

`Project` es la unidad raiz del sistema. Todo el dominio operativo se organiza a partir de un proyecto de investigacion.

## Cadena principal del modelo de datos

`Project -> ProjectVariable -> Form -> FormSection / FormInstrument / FormQuestion -> FormQuestionOption -> FormResponse -> FormAnswer`

## Capa de publicacion publica

En esta fase se agrega una capa de publicacion controlada basada en `Form.public_slug` y `Form.status`.

### Estados de Form

- `draft`: editable, no expuesto publicamente.
- `published`: visible por slug y habilitado para recibir respuestas.
- `closed`: no acepta respuestas publicas.
- `archived`: no expuesto y no acepta respuestas.

### Flujo de estados

`draft -> published -> closed -> reopened(published)`

La estrategia elegida para `reopen` conserva `collect_closed_at` como historial y reutiliza el mismo `public_slug` si ya existe.

## Publicacion y validacion de respuestas

La capa publica implementa:

- generacion de `public_slug` unico
- lectura publica de la estructura publicada
- validacion de preguntas requeridas
- validacion basica por tipo de pregunta
- validacion de pertenencia entre pregunta y opcion
- bloqueo de formularios `draft`, `closed` y `archived`
- persistencia de respuestas publicas en `form_responses` y `form_answers`
- calculo de `score_value` cuando corresponde

## Capa de dataset tabular

La nueva capa interna transforma `FormResponse` y `FormAnswer` en una tabla analitica estable por formulario.

### Transformacion base

- cada `FormResponse` se convierte en una fila
- cada `FormQuestion` se convierte en una o varias columnas
- las columnas pueden emitirse en modo `label`, `value`, `score` o `mixed`
- las preguntas `multiple_choice` pueden expandirse a columnas dummy por opcion
- las respuestas `discarded` se excluyen por defecto

### Metadatos incluidos

La vista tabular puede incluir `response_id`, `project_id`, `form_id`, `respondent_code`, `response_status`, `source`, `submitted_at` y `created_at`.

### Diccionario y completitud

Sobre el mismo modelo tabular se construyen:

- un diccionario de datos por pregunta y columna
- un resumen de completitud por item
- la base exportable para Pandas, CSV y Excel

## Capa estadistica descriptiva

La capa descriptiva usa `dataset_service` como fuente analitica principal y construye resultados JSON serializables sobre `pandas.DataFrame`.

### Separacion analitica

- `dataset_service`: construccion de base tabular y diccionario
- motor descriptivo: frecuencias, tendencia central, dispersion y agregados
- normalidad: evaluacion de distribucion y clasificacion inicial
- inferencia: fase posterior

### Salidas descriptivas

La fase actual entrega:

- descriptivos por pregunta
- descriptivos por dimension
- descriptivos por instrumento
- descriptivos por variable de proyecto
- tablas cruzadas descriptivas
- corridas descriptivas registrables para trazabilidad

## Capa de normalidad

La capa de normalidad reutiliza `dataset_service` y los agregados de dimensiones e instrumentos para ejecutar pruebas sobre series numericas ya limpias.

### Reglas de metodo

- `Shapiro-Wilk` para muestras entre 3 y 5000
- `Lilliefors` para muestras grandes o cuando se solicita expresamente
- `D'Agostino-Pearson` como alternativa configurable cuando el tamano muestral lo permite
- clasificacion en `normal`, `non_normal`, `inconclusive` o `not_applicable`

### Trazabilidad

Las corridas pueden registrarse en `AnalysisRun` con `analysis_type = normality`.

## Motor de decision estadistica inicial

Esta capa no ejecuta pruebas inferenciales. Solo recomienda la ruta metodologica inicial.

### Separacion de responsabilidades

- normalidad: evalua supuestos de distribucion
- decision estadistica: recomienda Pearson, Spearman, chi cuadrado, t, ANOVA, Mann-Whitney, Kruskal-Wallis o Wilcoxon segun corresponda
- inferencia: fase posterior donde recien se ejecutaran esas pruebas

## Capa de correlaciones

La capa de correlaciones reutiliza `dataset_service` para series limpias, `normality_service` para elegir metodos en `auto` y `AnalysisRun` para trazabilidad reproducible.

### Responsabilidades

- ejecutar `Pearson`, `Spearman` y `Kendall`
- resolver targets de tipo pregunta, dimension, instrumento y variable de proyecto
- construir correlaciones por pares y matrices
- calcular `coefficient`, `p_value`, `valid_n`, direccion, magnitud y significancia
- producir interpretaciones prudentes sin afirmar causalidad

### Separaciones clave

- correlacion y normalidad: relacionadas, pero separadas
- correlacion y decision metodologica: la decision orienta; la correlacion ejecuta
- correlacion y graficos: esta fase no genera dispersion ni visualizacion
- correlacion y tablas APA: la salida queda lista para fases posteriores

## Capa de comparacion de grupos

La capa de comparacion de grupos reutiliza `dataset_service` para series limpias, `normality_service` para revisar normalidad por grupo y `AnalysisRun` para trazabilidad de cada corrida.

### Responsabilidades

- ejecutar `t_student_independent`, `welch_t`, `mann_whitney_u`, `anova_one_way` y `kruskal_wallis`
- calcular descriptivos por grupo
- evaluar homogeneidad de varianzas con `Levene`
- producir tamanos de efecto iniciales
- recomendar rutas automaticas prudentes cuando `method=auto`

### Separaciones clave

- comparacion y decision metodologica: la decision sugiere; esta capa ejecuta
- comparacion y graficos: no produce boxplots ni comparativos visuales todavia
- comparacion y tablas APA: deja resultados estructurados para fases posteriores

## Capa de asociacion categorica

La capa de asociacion categorica reutiliza `dataset_service` para series categorizadas, `crosstab_engine` para porcentajes tabulares reutilizables y `AnalysisRun` para trazabilidad de cada corrida inferencial categorial.

### Responsabilidades

- ejecutar `chi_square` de independencia
- ejecutar `fisher_exact` en tablas `2x2`
- construir tablas observadas, esperadas y porcentajes por fila, columna y total
- calcular `phi`, `V de Cramer` y `odds_ratio` cuando corresponda
- producir interpretaciones prudentes sin afirmar causalidad

### Separaciones clave

- tablas cruzadas descriptivas e inferenciales: separadas
- asociacion categorica y graficos: no produce barras ni mosaicos todavia
- asociacion categorica y tablas APA: deja resultados estructurados para fases posteriores
- asociacion categorica y analisis multivariado: fuera de esta fase

## Capa de orquestacion

La capa de orquestacion coordina los motores estadisticos existentes sin reemplazarlos. Su funcion es convertir resultados tecnicos en una salida consolidada, comprensible y reutilizable para una futura interfaz premium.

### Diferencia entre motores y orquestador

- los motores estadisticos ejecutan calculos especificos
- los servicios especializados exponen esos calculos por endpoint tecnico
- el orquestador selecciona el flujo, ejecuta los servicios necesarios y consolida la salida

### Responsabilidades del orquestador

- recibir un objetivo analitico de alto nivel
- validar targets y roles
- coordinar descriptivos, normalidad, decision, correlacion, comparacion o asociacion
- producir `executive_summary`, `academic_interpretation` y `plain_language_explanation`
- preparar `apa_table_blocks`, `chart_blocks` y `export_blocks`
- registrar `AnalysisRun` consolidado con `analysis_type = orchestrated_analysis`

### Preparacion para capas futuras

- UI premium de resultados guiados
- tablas APA 7 automatizadas
- graficos premium editables
- informe Word consolidado

## Capa de tablas APA

La capa `app/tables` transforma resultados estadisticos ya calculados en estructuras de tabla academica reutilizables.

### Responsabilidades

- convertir descriptivos, normalidad, correlacion, comparacion y asociacion en tablas APA iniciales
- generar salidas `json`, `markdown` y `html`
- reutilizar `AnalysisRun` y `apa_table_blocks` del orquestador cuando corresponda
- preparar una estructura compatible con futura exportacion Word

### Relacion con otras capas

- `dataset_service` y los motores estadisticos no cambian; solo proveen datos fuente
- el orquestador sigue coordinando flujos; la capa APA solo formatea resultados
- `AnalysisRun` permite regenerar tablas desde corridas previas
- `ExportArtifact` registra exportaciones `.md`, `.html` y futuras salidas documentales

### Diferencia entre tabla APA estructural y documento Word

- la tabla APA estructural ya define titulo, columnas, filas, notas y formato de celdas
- el documento Word final quedara para una fase posterior
- esta capa deja la salida lista para que Word solo haga maquetacion final

### Preparacion para frontend

- cada tabla devuelve JSON listo para interfaz
- `markdown` permite revision rapida
- `html` permite futura previsualizacion web sobria sin acoplarse aun al frontend React

### Objetivos soportados

- correlacion
- comparacion de grupos independientes
- comparacion de medidas relacionadas
- asociacion categórica
- lectura descriptiva unicamente

### Preparacion para analisis bivariado

La tabla cruzada descriptiva sirve como base para decisiones futuras de chi cuadrado u otras pruebas, pero en esta fase solo expone conteos y porcentajes.

## Capa de exportacion de artefactos

Se agrega `ExportArtifact` para registrar salidas generadas dentro de `backend/data/exports`.

En esta fase la salida inicial incluye:

- dataset CSV
- dataset Excel

La misma capa servira despues para:

- tablas APA 7
- reportes Word
- graficos exportables

## Estado funcional por fases

- La base de proyectos ya esta implementada.
- La base de variables, formularios, instrumentos, preguntas y respuestas internas ya esta implementada.
- La publicacion y recoleccion publica por link ya esta iniciada tecnicamente.
- La base tabular de respuestas, el diccionario de datos y la exportacion inicial ya estan implementados tecnicamente.
- El motor descriptivo inicial ya esta implementado tecnicamente.
- La capa de normalidad y el motor de decision estadistica inicial ya estan implementados tecnicamente.
- La capa de correlaciones iniciales ya esta implementada tecnicamente.
- La capa inicial de comparaciones entre grupos ya esta implementada tecnicamente.
- La capa inicial de asociacion categorica ya esta implementada tecnicamente.
- La capa de orquestacion de analisis y resultados consolidados ya esta implementada tecnicamente.
- La capa inicial de graficos premium editables ya esta implementada tecnicamente.
- La estadistica descriptiva e inferencial quedara para las Fases 5 y 6.
- Los graficos premium, reportes Word y exportaciones quedaran para fases posteriores.

## Capas funcionales

### 1. Capa de proyectos

Gestiona la unidad principal de trabajo investigativo: proyecto, metadatos, estado y configuracion general del estudio.

### 2. Capa de variables

Modela variables del estudio con rol, nivel de medicion y tipo de dato.

### 3. Capa de formularios

Administra formularios, secciones, instrumentos, dimensiones y preguntas dinamicas.

### 4. Capa de publicacion

Expone formularios publicados por slug y controla el ciclo de apertura y cierre.

### 5. Capa de respuestas

Persiste respuestas completas y respuestas por item, tanto internas como publicas.

### 6. Capa de dataset

Convierte respuestas operativas en una tabla analitica con columnas estables, reglas de codificacion y resumen de completitud.

### 7. Capa estadistica

Procesa la base recolectada para obtener descriptivos, normalidad, recomendaciones metodologicas, correlaciones iniciales, comparaciones entre grupos, asociacion categorica y luego inferencia en fases posteriores.

### 8. Capa de graficos

Genera especificaciones JSON editables orientadas a tesis e informes. Esta capa no renderiza imagenes: construye `ChartSpec` con `plotly_data`, `plotly_layout`, `plotly_config`, metadatos de UX, alternativas recomendadas y presets visuales.

Se relaciona con:

- `dataset_service` para reconstruir series y distribuciones.
- `correlation_service`, `group_comparison_service` y `categorical_association_service` para reutilizar resultados estadisticos ya implementados.
- `analysis_orchestrator_service` para reutilizar `chart_blocks` y rutas guiadas.
- `ExportArtifact` para registrar exportaciones JSON de especificaciones visuales.

Esta capa separa claramente:

- especificacion JSON del grafico
- renderizado frontend posterior
- exportacion de imagenes futura
- integracion con tablas APA y Word en fases posteriores

### 9. Capa de reportes

Construira tablas APA 7, interpretaciones estructuradas y documentos finales.

### 10. Capa de exportacion

Producira artefactos descargables como Excel, Word e imagenes de salida.

### 11. Capa de orquestacion

Coordina motores estadisticos y transforma sus resultados en bloques de producto listos para interfaz, tablas APA, graficos e informe.

### 12. Capa de integracion futura

Preparara contratos y puntos de extension para interoperar con Micelio y AppTesis.

## Capa de generacion Word

La capa `app/word` ya esta implementada en una primera version para ensamblar informes `.docx` sobrios y reutilizables.

### Responsabilidades

- construir portada, resumen del estudio y secciones de resultados
- insertar tablas APA materializadas por `ApaTableService`
- insertar placeholders de graficos a partir de `ChartService`
- reutilizar `AnalysisRun` y corridas orquestadas sin duplicar calculos
- registrar el documento exportado en `ExportArtifact`

### Relaciones clave

- `ApaTableService`: provee tablas APA listas para Word
- `ChartService`: provee `ChartSpecRead` o recomendaciones para placeholders
- `AnalysisRun`: actua como fuente reutilizable para informes inferenciales y orquestados
- `ExportArtifact`: registra los `.docx` generados en `data/exports`

### Diferencia con el informe premium futuro

- esta capa genera `.docx` funcional y academico
- no inserta todavia imagenes reales de graficos
- no genera PDF
- deja la estructura preparada para integracion futura con AppTesis y render visual premium

## Capa frontend web

La carpeta `frontend` ya implementa el primer cliente web de Colmena con `React + TypeScript + Vite + Tailwind CSS`.

### Responsabilidades

- consumir el backend FastAPI real sin duplicar logica estadistica
- presentar proyectos, formularios, respuestas y resultados en una UI SaaS clara
- renderizar `ApaTableRead` como tablas navegables
- renderizar `ChartSpecRead` con Plotly en el navegador
- ejecutar `OrchestratedAnalysisRead` desde una capa guiada para usuarios no tecnicos
- disparar generacion de `WordReportRead` y visualizar exportaciones registradas

### Relacion React con FastAPI

- React actua como cliente visual y orquestador de interacciones
- FastAPI sigue concentrando dominio, validaciones y calculo estadistico
- el frontend solo envuelve contratos existentes: no recalcula normalidad, correlaciones ni inferencia
- se habilito `CORSMiddleware` de forma minima para `http://127.0.0.1:5173` y `http://localhost:5173`

### Contratos visuales clave

- `ApaTableRead`: puente entre salida estadistica y tabla academica renderizable
- `ChartSpecRead`: contrato visual inicial para Plotly y futura edicion premium
- `WordReportRead`: contrato de exportacion documental para listar y disparar informes Word
- `OrchestratedAnalysisRead`: capa de consolidacion que el frontend usa para explicar resultados sin exponer complejidad tecnica

### Separacion entre backend estadistico y frontend visual

- backend: dominio, dataset, estadistica, tablas APA, chart specs y Word
- frontend: navegacion, estados de carga, render tabular, render Plotly y experiencia de usuario
- esta separacion permite evolucionar el dashboard y el editor visual sin tocar calculos estadisticos

### Preparacion para fases siguientes

- editor visual de resultados y graficos
- dashboard premium con mas flujos guiados
- descarga segura de artefactos
- integracion futura con AppTesis

## Capa UX secuencial

La experiencia web ya no se organiza solo por pantallas aisladas. Ahora existe una capa de UX secuencial que guía al usuario por el camino natural del producto:

- `Project`
- constructor guiado de `Form`
- publicacion del formulario
- recoleccion de respuestas
- resultados
- tablas APA, graficos e informe

### Relacion Project -> Form Wizard -> Publicacion -> Resultados

- `Project` concentra el contexto academico general
- el frontend abre `/projects/:projectId/forms/new` como flujo guiado de construccion
- el wizard crea `Form`, variables, instrumento, dimensiones, preguntas y opciones mediante llamadas reales al backend
- al terminar, el usuario puede publicar el formulario y obtener el link publico
- luego el detalle del formulario se convierte en el centro para base, resultados, tablas, graficos e informe

### Tratamiento de baremos, puntuacion inversa y escalas de control

En la capa actual:

- el wizard captura reglas reales de scoring
- los items invertidos se guardan en preguntas y se usan en el motor de scoring
- los baremos se persisten como `score_bands`
- la escala de mentira o control se persiste como `control_scales` y `control_scale_items`
- el detalle del formulario ya puede ejecutar scoring y revisar resultados por baremo

### Separacion entre wizard frontend y backend estadistico

- frontend wizard: experiencia, secuencia, microcopy y armado progresivo del instrumento
- backend estadistico: dataset, scoring actual, descriptivos, inferencia, APA, chart specs y Word

Esto evita duplicar logica de resultados mientras permite que el usuario no tecnico recorra un flujo claro desde el diseno hasta la presentacion.

## Capa de scoring avanzado

La capa `app/scoring` formaliza el calculo de puntajes por instrumento, dimension y variable, junto con la clasificacion por baremos y la deteccion de respuestas con advertencias de control.

### Componentes principales

- `scoring_configs`: define como calcular el puntaje
- `score_bands`: define rangos interpretativos
- `control_scales`: define reglas de mentira, atencion, infrecuencia o consistencia
- `control_scale_items`: vincula preguntas a una regla de control
- `response_scores`: guarda el puntaje final por respuesta y configuracion
- `response_control_flags`: guarda advertencias o invalidez por respuesta y escala de control

### Integraciones

- `dataset_service`: agrega columnas de score, baremo, interpretacion y validez cuando `include_scores=true`
- `descriptive_service`: ya puede resumir puntajes calculados
- `analysis_orchestrator_service`: incorpora bloques `scoring` en el full scan
- `apa_table_service`: genera `scoring_summary`, `score_band_distribution` y `control_scale_flags`
- `chart_service`: recomienda donut y barras por baremo
- `word_report_service`: agrega seccion `Resultados por baremo` y advertencias de control

### Separacion entre frontend wizard y backend estadistico

- el wizard define reglas y contexto de instrumento
- el backend ejecuta scoring idempotente por respuesta
- los resultados quedan reutilizables por dataset, descriptivos, APA, charts y Word

## Capa de editor visual frontend

Sobre la capa frontend ya implementada se agrega un editor visual inicial para resultados y graficos.

### Responsabilidades

- recibir `ChartSpecRead` como contrato visual desde FastAPI
- transformar `plotly_data`, `plotly_layout` y `plotly_config` sin recalcular estadistica
- permitir cambios controlados de tipo, textos, preset, leyenda y visibilidad de etiquetas
- mostrar tabla de datos vinculada y advertencias metodologicas
- persistir preferencias temporalmente en `localStorage`

### Separacion entre calculo backend y edicion visual frontend

- backend: decide que grafico es recomendable y entrega el `ChartSpecRead`
- frontend: permite editar la presentacion dentro de limites seguros
- el frontend no recalcula correlaciones, comparaciones ni asociaciones
- la UI puede modificar apariencia y algunos mapeos visuales, pero no la conclusion estadistica

### Persistencia temporal

- se usa `localStorage` por `formId` y `chartId`
- no se persisten configuraciones en base de datos todavia
- la persistencia actual es local al navegador y sirve como puente hacia una fase posterior de guardado real

### Optimizacion de Plotly

- Plotly se carga en diferido mediante `React.lazy`
- Vite separa `plotly.js` y `react-plotly.js` en un chunk dedicado
- esto reduce el peso del chunk principal de la aplicacion y prepara una evolucion posterior del editor

### Preparacion para exportacion futura

- el editor ya expone estado editable, advertencias y tabla vinculada
- la siguiente fase podra reutilizar esta capa para exportacion PNG/SVG
- tambien queda preparado el reemplazo posterior de placeholders dentro de Word

## Flujo de exportacion visual y Word

La exportacion de imagenes de graficos se resuelve en frontend porque Plotly ya renderiza el resultado final con la configuracion editada por el usuario.

### Flujo

- `ChartSpecRead` sale del backend
- React renderiza Plotly en el navegador
- el usuario ajusta el grafico con el editor visual
- Plotly exporta `PNG` o `SVG` en frontend
- el frontend envia la imagen al backend como `data_url`
- backend guarda el archivo en `data/exports`
- backend registra `ExportArtifact`
- `WordReportService` reutiliza esos artefactos PNG para insertarlos en `.docx`

### Separacion de responsabilidades

- backend: calculo estadistico, contratos visuales, guardado seguro de archivos, armado Word
- frontend: edicion visual, exportacion de imagen desde el navegador, seleccion de recursos para Word

### Seguridad de archivos

- se aceptan solo `data:image/png;base64,...` y `data:image/svg+xml;base64,...`
- tamano maximo inicial por imagen: `5 MB`
- los archivos se guardan solo dentro de `E:\Colmena\backend\data\exports`
- el nombre enviado por cliente se sanea y no controla la ruta final

### Limitacion actual de SVG

- `SVG` puede guardarse como artefacto
- `python-docx` no lo usa para incrustacion en Word en esta fase
- Word inserta solo recursos `PNG`, o vuelve a placeholders cuando no hay imagen compatible

## Criterios de diseno

- Modulos desacoplados.
- Separacion clara entre infraestructura, dominio y exposicion HTTP.
- Soft delete en entidades configurables.
- Validaciones de pertenencia entre proyecto, formulario, instrumento, dimension, pregunta y opcion.
- Exposicion publica minima y controlada por `status`.
- Evolucion progresiva desde recoleccion hacia datasets, analitica, graficos y reportes.
