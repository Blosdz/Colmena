# Colmena Frontend

Frontend MVP de Colmena construido con React, TypeScript, Vite y Tailwind CSS.

## Stack

- React 19
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query
- Plotly con `react-plotly.js`

## Configuracion

1. Copia `.env.example` a `.env` si necesitas sobrescribir la URL del backend.
2. Variable disponible:

```env
VITE_COLMENA_API_BASE_URL=http://127.0.0.1:8080
```

Si no existe, el frontend usa `http://127.0.0.1:8080` como fallback.

## Desarrollo

```bash
cd E:\Colmena\frontend
npm install
npm run dev
```

Frontend esperado: [http://127.0.0.1:5173](http://127.0.0.1:5173)

Backend esperado:

```bash
cd E:\Colmena\backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Swagger: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)

## Rutas principales

- `/` dashboard inicial
- `/projects` lista y creacion de proyectos
- `/projects/:projectId` detalle de proyecto y formularios
- `/projects/:projectId/forms/new` constructor guiado de formularios
- `/forms/:formId` detalle de formulario y resultados
- `/results/:formId` acceso rapido a resultados

## Modulos implementados

- Dashboard general
- Proyectos
- Sistema visual Colmena con branding y flujo secuencial
- Constructor guiado de formularios
- Formularios por proyecto
- Dataset preview
- Descriptivos
- Analisis guiado
- Tablas APA
- Graficos Plotly desde `ChartSpecRead`
- Editor visual inicial de graficos
- Informes Word
- Exportaciones del formulario

## Sistema visual Colmena

La interfaz ahora usa una capa de marca y experiencia secuencial:

- logo y marca desde `public/brand`
- cards premium con glass suave
- stepper de progreso en formularios
- shell visual orientado a flujo
- microcopy pensada para usuarios no tecnicos

### Assets de marca

Ruta esperada:

- `frontend/public/brand/colmena-logo.svg`
- `frontend/public/brand/colmena-mark.svg`
- `frontend/public/brand/colmena-logo.png`
- `frontend/public/brand/colmena-mark.png`

Si no existe el logo final, el proyecto usa un fallback SVG temporal que debe reemplazarse luego por el asset oficial.

## Form wizard

Ruta:

- `/projects/:projectId/forms/new`

Pasos implementados:

1. Contexto del formulario
2. Variables
3. Instrumento
4. Dimensiones
5. Items
6. Opciones de respuesta
7. Scoring, baremos y escala de control
8. Revision y publicacion

### Alcance actual del wizard

- crea formulario real en backend
- crea variables del proyecto
- crea instrumento
- crea dimensiones
- crea items
- crea opciones de respuesta
- puede publicar el formulario y mostrar el link publico

### Baremos, scoring inverso y escalas especiales

En esta fase:

- la UI guarda configuraciones reales de scoring en backend
- la UI crea baremos por instrumento y por dimension cuando corresponde
- la UI marca items invertidos para el motor de scoring
- la UI permite definir una escala de control con umbral y accion
- el detalle del formulario ya incluye una pestana `Scoring` para ejecutar calculo y revisar resultados

## Scoring avanzado

### Que permite

- crear configuraciones de scoring reales desde el wizard
- guardar baremos Bajo / Medio / Alto o personalizados
- activar una escala de control o mentira
- ejecutar scoring del formulario desde la pestana `Scoring`
- revisar distribucion por baremo y flags de control
- alimentar descriptivos, tablas APA, graficos y Word desde backend

### Flujo recomendado

1. Configura scoring en el wizard del formulario.
2. Publica y recolecta respuestas.
3. Entra al formulario y abre la pestana `Scoring`.
4. Ejecuta el calculo.
5. Revisa niveles, advertencias e invalidez antes de interpretar resultados.

### Limitaciones actuales

- los baremos avanzados viven en backend, pero todavia no existe un editor visual dedicado para administrarlos fuera del wizard
- las escalas de control cubren reglas iniciales, no auditoria psicometrica completa
- el scoring ponderado ya se modela, pero la captura de pesos especificos por item sigue siendo una extension futura

## Editor de graficos

La pestana de graficos del formulario ahora usa un editor visual inicial sobre `ChartSpecRead`.

### Que permite

- cambiar tipo de grafico dentro de las alternativas compatibles
- editar titulo y subtitulo
- editar etiquetas de ejes
- cambiar preset visual
- mostrar u ocultar porcentajes, frecuencias, valores y leyenda
- ver tabla de datos vinculada
- ver JSON tecnico en panel avanzado
- restaurar la recomendacion original del backend

### Persistencia local

Las preferencias del editor se guardan en `localStorage` con la clave:

`colmena.chartEditor.{formId}.{chartId}`

Se persiste solo la configuracion editable, no el payload completo de Plotly.

### Carga de graficos recomendados

La interfaz usa:

- `GET /api/v1/forms/{form_id}/charts/recommended`

Luego renderiza el grafico activo con Plotly y aplica transformaciones locales sobre el `ChartSpecRead`.

### Rendimiento

Plotly ahora se carga de forma diferida mediante `React.lazy` y ademas se separa en un chunk dedicado en Vite.

## Limitaciones actuales

- Sin autenticacion
- El constructor guiado cubre el flujo principal, pero no reemplaza aun un editor avanzado completo
- Sin descarga segura de artefactos desde frontend
- Sin persistencia del editor en base de datos
- Algunas conversiones entre tipos de grafico siguen restringidas para no deformar el significado estadistico
- El scoring avanzado ya existe, pero su administracion visual avanzada fuera del wizard sigue pendiente

## Exportacion de graficos e integracion con Word

### Que permite el editor en esta fase

- descargar el grafico actual como PNG
- descargar el grafico actual como SVG cuando Plotly lo permita
- guardar PNG en backend para reutilizarlo en el informe Word
- guardar SVG como recurso adicional
- listar imagenes guardadas del formulario
- generar Word usando imagenes reales o placeholders

### Como funciona

1. El backend entrega `ChartSpecRead`.
2. El frontend renderiza el grafico con Plotly.
3. El usuario ajusta la apariencia localmente.
4. El navegador exporta la imagen.
5. El frontend envia la imagen al backend como `data_url`.
6. El backend la registra como `ExportArtifact`.
7. El panel Word puede insertar esas imagenes reales en el `.docx`.

### Persistencia local y recursos visuales

- la configuracion editable sigue guardandose en `localStorage`
- las imagenes guardadas para Word quedan en backend como artefactos reales
- esta fase no exporta todavia PNG o SVG desde backend, solo desde el navegador

### Limitaciones actuales

- Word usa PNG; SVG no se incrusta en `.docx` en esta fase
- no hay miniaturas en la galeria todavia
- no existe exportacion de imagen directa desde el backend
- la descarga segura de archivos sigue pendiente para una fase posterior
