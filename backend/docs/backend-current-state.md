# Estado actual del backend

## Plataforma y estructura

El backend es una aplicación Python 3.12 con FastAPI, Pydantic v2 y SQLAlchemy
2 async. PostgreSQL es la base de producción y los tests de integración usan
SQLite en memoria mediante `aiosqlite`. La estructura separa routers, schemas,
servicios, repositorios, modelos y métodos estadísticos. La lógica estadística
vive en `app/analytics`, no en los routers.

## Modelo de datos

Existe un único modelo para proyectos académicos, CENSOPAS y encuestas custom:

- usuarios, organizaciones, membresías y proyectos;
- instrumentos vinculables uno-a-muchos con proyectos, versiones, option sets,
  preguntas, constructos y variables;
- surveys, secciones, estudios, snapshots y unidades dinámicas;
- sesiones anónimas, respuestas largas y opciones múltiples seleccionadas;
- scoring, baremos, ejecuciones/resultados analíticos;
- exportaciones, reportes, BSC y auditoría.

Los modelos ORM reflejan el esquema `colmena`. La migración Alembic `0001`
instala el DDL acordado en `colmena_postgresql_schema.sql`; `0002` traduce el
catálogo estadístico y `0003` incorpora roles de pregunta, secciones, baremos
multinivel y puntajes inmutables por sesión. No se usa `metadata.create_all()`
en producción.

## Módulos reutilizables

- `InstrumentEditPolicy` centraliza el bloqueo por estado, instrumento de
  sistema y estudios abiertos.
- `DatasetService` produce las vistas long/wide y el diccionario de variables.
- `PrivacyService` contiene el umbral mínimo publicable.
- Los servicios de análisis persisten `analysis_runs` y `analysis_results`.
- El paquete `analytics/censopas` mantiene separados dato crudo, scoring,
  agregación y clasificación.
- `AuditService` registra las mutaciones principales.

## Auth y exposición pública

Hay registro, login JWT y `/auth/me`. Los endpoints de captura pública están
separados de la resolución pública del estudio. Queda pendiente aplicar
autorización y pertenencia de proyecto a todos los routers de negocio: hoy
estos aceptan IDs de propietario/creador en los cuerpos y no verifican que el
usuario autenticado tenga acceso al recurso.

## Surveys, questions y responses

Un survey referencia preguntas existentes mediante `survey_questions`; no las
duplica. Al abrir un estudio se valida la configuración y se crea un snapshot.
Las respuestas se guardan en formato largo. Las selecciones múltiples se
persisten en `response_selected_options`; las opciones simples conservan tanto
el ID como el `raw_code`/valor numérico canónico para que dataset y scoring no
reciban respuestas vacías.

Los ítems tienen rol `SCORED`, `EXOGENOUS` o `DESCRIPTIVE`. Todo ítem
`SCORED` debe ser Likert y tener al menos dos opciones activas con valores
numéricos únicos. Los exógenos se crean junto con su variable y aparecen en
una sección separada; sirven para perfilado, filtros y grupos, pero nunca
entran en el scoring.

## Baremos y analítica de tesis

- Las escalas Likert son `option_sets` reutilizables y editables mientras la
  versión del instrumento no esté bloqueada.
- `barem_bands` admite tres, cinco o más niveles por constructo. La propuesta
  de cortes iguales es siempre borrador y puede corregirse manualmente.
- Activar un baremo exige población, fuente, versión, cobertura 0–100 y
  niveles para todos los constructos; después queda inmutable.
- `construct_scores` conserva puntaje, completitud, banda, algoritmo y corrida
  por participante anónimo. Una nueva ejecución no sobrescribe la anterior.
- Normalidad usa Shapiro–Wilk hasta 5000 casos y D'Agostino–Pearson por encima.
  Es complementaria: la correlación de puntajes Likert usa Spearman siempre.
- La matriz de Spearman incluye p ajustado por Benjamini–Hochberg y pares para
  la gráfica de dispersión. Variables nominales se reservan para segmentación.
- Los resultados de baremos exponen tabla, distribución, prioridad y supresión
  de privacidad CENSOPAS desde el backend.

## Compatibilidad del editor

Variables, dimensiones/subdimensiones e ítems están representados por
`Variable`, `Construct` y `Question`. Hay CRUD, edición batch, asignación de
ítems, árbol, matriz y clonado de versiones. Las versiones metodológicamente
bloqueadas deben clonarse antes de editarse.

Desde la migración `0009`, un proyecto puede contener varios instrumentos.
Cada formulario y estudio conserva su `instrument_version_id`; telemetría y
resultados exponen además el instrumento para compararlo como unidad analítica.
Los nodos raíz del editor pueden ser dimensión, escala, factor o índice.

## Limitaciones comprobadas

- SPSS, Power BI y Parquet todavía devuelven error explícito; PDF/DOCX tampoco
  se renderizan.
- Las tareas pesadas siguen siendo síncronas y no existe una cola real.
- La autorización de recursos por usuario/proyecto está pendiente.
- La suite de integración no pudo ejecutarse en este entorno porque el
  `aiosqlite 0.22.1` instalado queda bloqueado incluso al abrir una conexión
  mínima. Las pruebas puras y la compilación sí funcionan.
