# MVP Scope

El MVP de Colmena se enfoca en resolver el flujo cuantitativo esencial para investigacion academica.

## Modulos del MVP inicial

### Modulo 1: Proyectos de investigacion

Estado: implementado tecnicamente en backend.

Creacion y gestion basica de proyectos, con metadatos minimos y organizacion del trabajo.

### Modulo 2: Constructor de formularios

Estado: implementado tecnicamente en su estructura base.

Definicion de formularios, instrumentos, dimensiones, preguntas, tipos de respuesta y opciones.

### Modulo 3: Recoleccion por link

Estado: iniciado tecnicamente.

Publicacion de formularios mediante enlace publico, consulta publica por slug y recepcion de respuestas publicas con validacion basica.

### Modulo 4: Base de respuestas

Estado: implementado tecnicamente en su estructura interna, publica y tabular.

Persistencia estructurada de respuestas y answers por pregunta, con fuente `internal` o `public_link`.

Incluye transformacion a dataset por formulario, diccionario de datos y resumen de completitud.

### Modulo 5: Procesamiento descriptivo

Estado: implementado tecnicamente en su primera capa.

Calculo de frecuencias, porcentajes, medidas de tendencia central, dispersion, percentiles, descriptivos por pregunta, dimension, instrumento y tabla cruzada descriptiva inicial.

### Modulo 6: Normalidad

Estado: implementado tecnicamente en su primera capa.

Aplicacion de Shapiro-Wilk, Lilliefors y D'Agostino-Pearson segun reglas de tamano muestral, con clasificacion de normalidad y advertencias de calidad.

### Modulo 7: Correlacion y comparacion basica

Estado: implementado tecnicamente en su primera capa de correlacion.

Incluye recomendacion inicial de ruta parametrica, no parametrica o categorica, ejecucion de Pearson, Spearman y Kendall, matrices de correlacion e interpretacion automatica inicial sin afirmar causalidad.

Tambien incluye una primera capa de comparacion entre grupos con t de Student independiente, Welch, Mann-Whitney, ANOVA, Kruskal-Wallis e interpretacion automatica prudente con tamanos de efecto iniciales.

Tambien incluye una primera capa de asociacion categorica con chi cuadrado, Fisher exacto para tablas 2x2, V de Cramer, Phi, tablas cruzadas inferenciales e interpretacion automatica inicial.

### Modulo 8: Tablas APA 7

Estado: implementado tecnicamente en su primera capa.

Generacion de tablas academicas iniciales para frecuencias, descriptivos, normalidad, correlacion, comparacion y asociacion categórica, con salida JSON, Markdown y HTML. Tambien reutiliza `AnalysisRun` y `apa_table_blocks` del orquestador como base de la futura capa Word.

### Modulo 9: Graficos editables

Estado: implementado tecnicamente en su primera capa.

Visualizaciones con calidad de presentacion y capacidad de ajuste posterior. En esta fase ya existen especificaciones JSON editables para barras, donut, histogramas, boxplots, dispersion, heatmap y barras agrupadas, con contrato inicial hacia Plotly y el futuro frontend React.

### Modulo 10: Exportacion Word y Excel

Estado: iniciado tecnicamente para Excel/CSV de dataset base.

Salida inicial de dataset hacia Excel y CSV, y posterior expansion hacia documentos Word y hojas listas para tesis.

### Modulo 11: Resultados consolidados y analisis guiado

Estado: implementado tecnicamente en su primera capa.

El sistema ya puede orquestar descriptivos, correlacion, comparacion y asociacion desde un endpoint guiado, con resumen ejecutivo, explicacion en lenguaje claro y bloques estructurados para futuras tablas APA, graficos e informe Word.

### Modulo 12: Informe Word

Estado: implementado tecnicamente en su primera capa.

Incluye:

- informe Word `.docx`
- tablas APA dentro del documento
- interpretaciones automaticas
- placeholders de graficos
- registro de `ExportArtifact`

### Modulo 13: Exportacion visual de graficos

Estado: implementado tecnicamente en su primera capa.

Incluye:

- exportacion PNG desde frontend
- guardado de SVG como artefacto auxiliar
- registro de imagenes de graficos en `ExportArtifact`
- reutilizacion de imagenes PNG en Word
- convivencia entre imagen real y placeholder segun disponibilidad o modo seleccionado

### Modulo 14: Sistema visual y constructor guiado

Estado: implementado tecnicamente en su primera capa frontend.

Incluye:

- sistema visual Colmena con branding y shell premium
- dashboard orientado a flujo secuencial
- constructor guiado de formularios desde frontend
- captura inicial de variables, instrumento, dimensiones, items y opciones
- estructura inicial para baremos, puntuacion inversa y escalas de control
- publicacion del formulario y acceso al link publico desde la misma experiencia

### Modulo 15: Scoring avanzado y baremos

Estado: implementado tecnicamente en su primera capa backend y conectado al frontend.

Incluye:

- `scoring_configs` por instrumento y dimension
- baremos persistidos en `score_bands`
- escalas de control persistidas en `control_scales`
- `response_scores` y `response_control_flags`
- ejecucion de scoring por formulario
- integracion con dataset, descriptivos, APA, charts y Word
