# Correr COLMENA (rama `main`) en el servidor, junto a AppThesis

Esta rama de COLMENA **NO es COL2**. Diferencias clave frente a lo que dice
`../INICIAR.md` / `../run.ps1`:

| | COL2 (lo que asumen los scripts viejos) | COLMENA `main` (esto) |
|---|---|---|
| Base de datos | Postgres (`DATABASE_URL_SYNC`) | **SQLite** — `backend/data/db/colmena.db`, ruta fija en el código |
| Redis | "ya no se usa" | **Sí se usa** — telemetría pub/sub, `:6379` |
| Login | solo SSO de AppThesis | SSO de AppThesis **+ login propio** (email/contraseña) |

`run.ps1` sigue sirviendo para AppThesis; para COLMENA hay que arrancarlo aparte
con estos comandos (o adaptar el bloque de `run.ps1`).

---

## 1. Traer el código

```powershell
cd <ruta>\fullProyect\COLMENA
git remote set-url origin git@github.com-johan:Blosdz/Colmena.git   # si hace falta
git fetch origin
git checkout main
git reset --hard origin/main    # passphrase de la clave: blink182
```

## 2. Dependencias

```powershell
# backend  (deps nuevas: bcrypt, PyJWT, pydantic[email])
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# frontend
cd ..\frontend
npm install
```

## 3. Configuración — enlace con AppThesis

`COLMENA/backend/.env`  (crear desde `.env.example`):

```ini
COLMENA_APP_NAME=Colmena
COLMENA_ENV=development
COLMENA_DB_PATH=./data/db/colmena.db
COLMENA_REDIS_URL=redis://127.0.0.1:6379/0

# Login propio de COLMENA — cambiar en producción
COLMENA_JWT_SECRET=<secreto-largo-aleatorio>
COLMENA_JWT_EXPIRE_MINUTES=10080

# URL pública desde la que se sirve el FRONTEND de COLMENA (para el link de reset).
COLMENA_FRONTEND_BASE_URL=https://<colmena-frontend-en-el-servidor>

# URL base pública de ESTE backend (para armar el enlace público del formulario).
COLMENA_PUBLIC_BASE_URL=https://<colmena-backend-en-el-servidor>

# Backend de AppThesis (NestJS) — COLMENA valida el JWT SSO llamando a /auth/me aquí.
THESIS_API_BASE_URL=http://127.0.0.1:3000

# Gateway público de AppThesis que expone los formularios como tenant /#/colmena/forms/:slug
APPTHESIS_PUBLIC_URL=https://<appthesis-frontend-en-el-servidor>
COLMENA_SLUG=colmena

# CORS: el backend NO tiene regex de túneles, hay que listar los orígenes exactos
# de AMBOS frontends (COLMENA y AppThesis), separados por coma, con esquema.
COLMENA_CORS_EXTRA_ORIGINS=https://<colmena-frontend>,https://<appthesis-frontend>
```

`COLMENA/frontend/.env`:

```ini
VITE_COLMENA_API_BASE_URL=https://<colmena-backend-en-el-servidor>
VITE_APPTHESIS_SSO_URL=https://<appthesis-frontend>/#/sso/colmena
VITE_APPTHESIS_PUBLIC_URL=https://<appthesis-frontend>
VITE_COLMENA_TENANT_SLUG=colmena
```

`thesis-assistantV2/.env` (frontend de AppThesis) — apuntar a este COLMENA:

```ini
VITE_COLMENA_API_BASE_URL=https://<colmena-backend-en-el-servidor>
VITE_COLMENA_PUBLIC_FORM_URL=https://<colmena-frontend-en-el-servidor>
VITE_COLMENA_CALLBACK_URL=https://<colmena-frontend-en-el-servidor>/auth/callback
```

> Tras editar cualquier `.env` hay que **reiniciar** Vite / uvicorn (no hay hot-reload de `.env`).

## 4. Migraciones (SQLite)

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic current      # debe estar en 20260807_18
.\.venv\Scripts\python.exe -m alembic upgrade head # aplica 20260904_19, 20260905_20, 20260905_21
```

> `20260905_20` **reescala las bandas de baremos a 0–100 y borra `response_scores`**
> (se recalculan solos). Si `alembic current` no está en `20260807_18`, parar y revisar.

## 5. Redis

COLMENA `main` necesita Redis en `:6379` (telemetría). En el servidor ya existe el
contenedor `colmena-redis`:

```powershell
docker start colmena-redis   # o: docker run -d --name colmena-redis -p 6379:6379 redis:7-alpine
```

## 6. Arrancar

```powershell
# backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# frontend (build + servir, o dev)
cd ..\frontend
npm run build
npx serve -s dist -l 5174          # o:  npx vite --host 0.0.0.0 --port 5174
```

## 7. Exponer (Tailscale / Cloudflare)

Mismo esquema que el resto del monorepo. Con Tailscale, si escuchan en `0.0.0.0`
ya entran por la IP del tailnet (`http://100.78.173.1:8080` / `:5174`). Para
HTTPS con el nombre del tailnet:

```powershell
tailscale serve --bg --set-path=/       http://localhost:5174
tailscale serve --bg --set-path=/api    http://localhost:8080
```

Con Cloudflare quick tunnels: tunelizar **backend Y frontend** de COLMENA (igual
que AppThesis) y poner esas URLs `https` en los `.env` de arriba.
