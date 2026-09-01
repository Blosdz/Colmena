"""Cross-login con AppThesis (thesis-backend NestJS del monorepo `fullProyect`).

COLMENA no emite estos JWT: los emite AppThesis. Aquí se validan llamando a
`GET {THESIS_API_BASE_URL}/auth/me`; si son válidos se crea/actualiza un usuario
espejo local (`users.appthesis_user_id`). Puerto asíncrono del
`app/services/auth_service.py` del COLMENA anterior (SQLite/sync).

Standalone (`/auth/register` + `/auth/login`) sigue disponible para desarrollo:
un JWT propio de COLMENA se resuelve en `app/core/security.py` sin pasar por aquí.
"""

from __future__ import annotations

import time

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ColmenaDomainError, ConflictError
from app.models.user import User


class AppThesisUnavailableError(ColmenaDomainError):
    """No se pudo contactar a AppThesis para validar el token (502)."""

    http_status = 502
    error_code = "APPTHESIS_UNAVAILABLE"


# Cache en proceso token -> (user_id, expira_en). Evita llamar a thesis-backend en
# cada request. TTL corto: el coste de un token revocado es <30 s de acceso.
_IDENTITY_TTL_SECONDS = 30
_identity_cache: dict[str, tuple[int, float]] = {}


class AppThesisAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    @property
    def _base_url(self) -> str:
        return self.settings.thesis_api_base_url.rstrip("/")

    async def _fetch_identity(self, token: str) -> tuple[dict, str | None]:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                me = await client.get(f"{self._base_url}/auth/me", headers=headers)
                if me.status_code == 401:
                    raise AuthenticationError("Token de AppThesis inválido o expirado.")
                me.raise_for_status()
                usuario = (me.json() or {}).get("usuario")
                if not usuario or not usuario.get("id"):
                    raise AppThesisUnavailableError("AppThesis no devolvió un usuario válido.")

                thesis_id: str | None = None
                try:
                    tesis = await client.get(
                        f"{self._base_url}/tesis/mis-tesis", headers=headers
                    )
                    if tesis.status_code == 200:
                        data = (tesis.json() or {}).get("data") or []
                        if data:
                            thesis_id = data[0].get("id")
                except httpx.HTTPError:
                    thesis_id = None  # opcional (asesores/admin no tienen tesis)

                return usuario, thesis_id
        except (AuthenticationError, ColmenaDomainError):
            raise
        except httpx.HTTPError as exc:
            raise AppThesisUnavailableError(
                f"No se pudo contactar a AppThesis: {exc}"
            ) from exc

    async def _upsert_user(self, usuario: dict, thesis_id: str | None) -> tuple[User, bool]:
        appthesis_user_id = str(usuario["id"])
        email = (usuario.get("email") or "").strip().lower() or None
        local_part = email.split("@")[0] if email else appthesis_user_id
        full_name = (usuario.get("nombre") or "").strip()
        first_name, _, last_name = full_name.partition(" ")

        existing = (
            await self.session.execute(
                select(User).where(User.appthesis_user_id == appthesis_user_id)
            )
        ).scalar_one_or_none()

        # A user may have registered in Colmena before using AppThesis SSO.
        # Reuse that account by email instead of attempting an INSERT that
        # violates users.email's unique constraint.
        if existing is None and email:
            existing = (
                await self.session.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()

        if (
            existing is not None
            and existing.appthesis_user_id not in (None, appthesis_user_id)
        ):
            raise ConflictError("El correo ya está vinculado a otra cuenta de AppThesis.")

        created = existing is None

        if existing is None:
            user = User(
                appthesis_user_id=appthesis_user_id,
                email=email,
                username=(local_part or appthesis_user_id)[:120],
                first_name=first_name or local_part,
                last_name=last_name or None,
                status="ACTIVE",
                thesis_id=thesis_id,
                metadata_={"source": "appthesis", "appthesis_name": full_name},
            )
            self.session.add(user)
        else:
            user = existing
            user.appthesis_user_id = appthesis_user_id
            user.email = email or user.email
            user.status = "ACTIVE"
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if thesis_id:
                user.thesis_id = thesis_id
            user.metadata_ = {**(user.metadata_ or {}), "source": "appthesis", "appthesis_name": full_name}

        await self.session.commit()
        await self.session.refresh(user)
        return user, created

    async def link_account(self, token: str) -> tuple[User, bool]:
        usuario, thesis_id = await self._fetch_identity(token)
        user, created = await self._upsert_user(usuario, thesis_id)
        _identity_cache[token] = (user.id, time.monotonic() + _IDENTITY_TTL_SECONDS)
        return user, created

    async def resolve_user(self, token: str) -> User:
        cached = _identity_cache.get(token)
        if cached and cached[1] > time.monotonic():
            user = await self.session.get(User, cached[0])
            if user is not None:
                return user
        user, _ = await self.link_account(token)
        return user
