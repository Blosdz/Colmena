# Roadmap

## Fase 0: Bootstrap tecnico

Definicion de estructura base, documentacion fundacional, configuracion inicial del backend y validacion de arranque.

## Fase 1: Backend base

Consolidacion de configuracion, salud del servicio, manejo de entorno, persistencia inicial y convenciones del proyecto.

## Fase 2: Modelo de datos

Diseno y construccion del esquema inicial para proyectos, variables, formularios, preguntas y respuestas.

## Fase 3: Publicacion y recoleccion por link

Habilita formularios publicos con slug, lectura publica de estructura, validacion de respuestas y almacenamiento real de respuestas publicas.

Esta fase deja lista la transicion hacia:

- base de respuestas real por formulario
- construccion tabular de dataset
- exportaciones internas
- procesamiento descriptivo posterior

## Fase 4: Base de respuestas y dataset

Construccion de vistas tabulares por formulario, codificacion de respuestas y preparacion de dataset para Pandas.

Esta fase sirve como puente directo entre:

- la recoleccion real de respuestas de la fase anterior
- el motor descriptivo de la siguiente fase
- la exportacion Excel operativa que luego se ampliara en fases posteriores

## Fase 5: Motor descriptivo

Procesamiento de estadistica descriptiva sobre las respuestas recopiladas.

Esta fase completa la transicion hacia:

- Fase 6 de normalidad y decision estadistica inicial
- Fase 7 de inferencia basica
- fases futuras de graficos premium
- fases futuras de tablas APA 7

## Fase 6: Motor inferencial

Pruebas de normalidad, decisiones iniciales de ruta estadistica, correlaciones y comparaciones basicas.

Esta fase habilita:

- correlaciones
- comparaciones
- hipotesis
- tablas APA posteriores
- explicacion automatica de resultados

Con la capa actual de correlaciones ya queda habilitado el puente hacia:

- graficos de dispersion
- tablas APA de correlacion
- informes Word con resultados correlacionales
- auditoria estadistica futura

La capa inicial de comparaciones entre grupos habilita ademas:

- graficos comparativos
- tablas APA de comparacion
- informes Word con comparaciones
- post hoc en una fase posterior

La capa inicial de asociacion categorica habilita ademas:

- tablas APA de asociacion
- graficos de barras agrupadas
- graficos mosaico
- informes Word con tablas cruzadas inferenciales
- auditoria estadistica futura

La capa de orquestacion de analisis y resultados consolidados habilita:

- Prompt 12: tablas APA 7
- Prompt 13: graficos premium editables
- Prompt 14: informe Word
- Prompt 15: dashboard frontend de resultados

La capa inicial de tablas APA habilita ahora:

- Prompt 13: graficos premium editables
- Prompt 14: informe Word
- Prompt 15: dashboard frontend de resultados
- reutilizacion de tablas academicas desde `AnalysisRun`
- exportacion preliminar a Markdown y HTML para revision

La capa inicial de graficos premium editables habilita ahora:

- Prompt 14: informe Word
- Prompt 15: frontend dashboard
- Prompt 16: editor visual de graficos
- Prompt 17: exportacion de imagenes en una fase posterior
- reutilizacion de `chart_blocks` y `AnalysisRun` como contrato visual intermedio

## Fase 7: Graficos premium

Construccion de visualizaciones editables con estandar estetico academico.

## Fase 8: Reportes Word APA 7

Generacion de documentos estructurados con tablas, interpretacion y salidas listas para tesis.

## Fase 9: Exportacion Excel

Exportacion de bases, tablas y resultados para interoperabilidad y revision.

## Fase 10: Integracion con AppTesis

Sincronizacion de resultados, documentos y flujos de acompanamiento academico.

## Fase 11: Integracion con Micelio

Consumo de instrumentos validados y trazabilidad entre seleccion y aplicacion de instrumentos.

## Fase 12: Auditoria estadistica asistida

Incorporacion de reglas, validaciones y asistencia experta para revision de calidad estadistica.

## Habilitadores recientes

La capa inicial de informe Word habilita ahora:

- Prompt 15: frontend dashboard inicial
- Prompt 16: editor visual de resultados
- Prompt 17: exportacion de graficos como imagen
- Prompt 18: integracion con AppTesis

La capa frontend inicial ya implementada habilita ahora:

- navegacion web real sobre proyectos, formularios y resultados
- render de `ApaTableRead` y `ChartSpecRead` en interfaz React
- disparo de `WordReportRead` desde UI
- siguiente fase: editor visual de resultados y graficos

La capa inicial del editor visual de resultados y graficos habilita ahora:

- edicion local de titulo, subtitulo, ejes y preset visual
- persistencia temporal de preferencias en navegador
- preparacion para exportacion de graficos como imagen
- siguiente fase: integracion visual con Word y exportacion PNG o SVG

La capa de exportacion visual e integracion Word habilita ahora:

- exportacion real de graficos como PNG desde frontend
- guardado de recursos visuales como `ExportArtifact`
- insercion de imagenes PNG reales dentro del informe Word
- mantenimiento automatico de placeholders cuando no hay imagen compatible
- siguiente fase: constructor visual de formularios o integracion avanzada con AppTesis

La capa del sistema visual Colmena y flujo secuencial habilita ahora:

- branding base y shell visual premium
- dashboard orientado al camino de uso completo
- constructor guiado de formularios desde frontend
- progreso visible entre diseno, publicacion, recoleccion, resultados e informe
- preparacion UX para la formalizacion de baremos, scoring inverso y escalas de control en backend

La capa de scoring avanzado habilita ahora:

- configuraciones reales de scoring por instrumento y dimension
- baremos persistidos y reutilizables en resultados
- escalas de control con advertencia o invalidez
- dataset enriquecido con scores
- secciones de scoring en APA, charts y Word

Siguiente fase recomendada:

- Prompt 19: vista publica premium del formulario y experiencia de respuesta
