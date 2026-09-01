# `api/generated/` — puente de tipos hacia los schemas Pydantic reales

## Qué es esto

`analytics.d.ts` en esta carpeta es un **espejo manual** de los schemas Pydantic reales en
`backend/app/schemas/analytics.py`, `variables.py`, `constructs.py` y `censopas.py` (campos
transcritos, no inventados — cada tipo referencia la clase Python exacta de la que viene).

## Por qué es manual y no generado

`frontend` es un proyecto **JavaScript puro** (no hay `tsconfig.json`, ni un solo archivo `.ts`
antes de este cambio, ni `typescript` en `package.json`). GAP-019 pedía generar tipos desde
OpenAPI en vez de escribirlos a mano, y ese sigue siendo el objetivo — pero no fue posible en
este cambio: el entorno de este runner no tiene el backend instalado (`poetry.lock` está sin
commitear y no hay un venv con `fastapi`/`sqlalchemy`/`asyncpg` resuelto), así que no se pudo
levantar `app.openapi()` para correr `openapi-typescript` contra un JSON real.

En vez de fingir que corrió una generación automática, este archivo es una transcripción fiel
del código fuente de los schemas (leído directamente, campo por campo). Es honesto pero **no
está protegido contra drift**: si alguien cambia un campo en `app/schemas/analytics.py` y no
actualiza `analytics.d.ts`, nadie se entera hasta que algo falla en runtime.

## Cómo reemplazar esto por generación real (siguiente PR, no este)

```bash
# 1. Con el backend instalable (poetry install funcionando):
cd backend
python -c "from app.main import app; import json; json.dump(app.openapi(), open('openapi.json','w'))"

# 2. En frontend:
npm install --save-dev openapi-typescript
npx openapi-typescript ../backend/openapi.json -o src/api/generated/openapi.d.ts

# 3. Añadir un script npm:
#    "gen:types": "openapi-typescript ../backend/openapi.json -o src/api/generated/openapi.d.ts"
#    e idealmente correrlo en CI para detectar drift (diff contra el committeado).
```

Una vez que `openapi.d.ts` generado exista, **borrar `analytics.d.ts`** (este archivo manual) y
migrar las referencias JSDoc que apunten a él hacia `openapi.d.ts`.

## Cómo se usa mientras tanto (sin introducir TypeScript al build)

No hace falta convertir ningún `.jsx` a `.tsx` ni añadir `tsconfig.json` para aprovechar estos
tipos — Vite/esbuild ignora los `.d.ts` en tiempo de build (no se importan en runtime, solo los
lee el editor/IDE vía JSDoc). Ejemplo de uso en un componente existente:

```js
/** @type {import('../../../api/generated/analytics').SpearmanCellRead} */
const cell = data.cells[0];
```

Esto da autocompletado y chequeo de tipos en el editor sin cambiar el pipeline de build. Si en
el futuro se decide adoptar TypeScript de verdad (convertir `.jsx` → `.tsx`), es una decisión de
stack aparte que no se toma en este cambio — no cambiar `.jsx` a `.tsx` sin acordarlo primero.
