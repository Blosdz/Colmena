from __future__ import annotations

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User


class AuthService:
    """Cross-login con AppThesis (thesis-backend).

    Recibe un JWT emitido por AppThesis, lo valida llamando a ``GET /auth/me``
    de thesis-backend y, si es valido, crea o actualiza el usuario espejo en
    Colmena. Tambien consulta ``GET /tesis/mis-tesis`` para enlazar la tesis
    activa del estudiante.
    """

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    @property
    def _thesis_base_url(self) -> str:
        return self.settings.thesis_api_base_url.rstrip("/")

    def _fetch_appthesis_identity(self, token: str) -> tuple[dict, str | None]:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            with httpx.Client(timeout=10.0) as client:
                me_resp = client.get(f"{self._thesis_base_url}/auth/me", headers=headers)
                if me_resp.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token de AppThesis invalido o expirado.",
                    )
                me_resp.raise_for_status()
                usuario = (me_resp.json() or {}).get("usuario")
                if not usuario or not usuario.get("id"):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="AppThesis no devolvio un usuario valido.",
                    )

                thesis_id: str | None = None
                try:
                    tesis_resp = client.get(
                        f"{self._thesis_base_url}/tesis/mis-tesis", headers=headers
                    )
                    if tesis_resp.status_code == 200:
                        data = (tesis_resp.json() or {}).get("data") or []
                        if data:
                            thesis_id = data[0].get("id")
                except httpx.HTTPError:
                    # La tesis es opcional (asesores/admin no tienen): no bloquea el login.
                    thesis_id = None

                return usuario, thesis_id
        except HTTPException:
            raise
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"No se pudo contactar a AppThesis: {exc}",
            ) from exc

    def _upsert_user(
        self, usuario: dict, thesis_id: str | None
    ) -> tuple[User, bool]:
        appthesis_user_id = str(usuario["id"])
        email = (usuario.get("email") or "").strip().lower()
        local_part = email.split("@")[0] if email else appthesis_user_id
        name = usuario.get("nombre") or local_part or "Usuario AppThesis"
        username = local_part or appthesis_user_id

        existing = self.db.scalar(
            select(User).where(User.appthesis_user_id == appthesis_user_id)
        )
        created = existing is None

        if existing is None:
            user = User(
                name=name,
                username=username,
                email=email,
                status="active",
                appthesis_user_id=appthesis_user_id,
                thesis_id=thesis_id,
            )
            self.db.add(user)
        else:
            user = existing
            user.email = email or user.email
            user.name = name or user.name
            user.username = username or user.username
            user.status = "active"
            user.deleted_at = None
            if thesis_id:
                user.thesis_id = thesis_id

        self.db.commit()
        self.db.refresh(user)
        return user, created

    def link_appthesis_account(self, token: str) -> tuple[User, bool]:
        usuario, thesis_id = self._fetch_appthesis_identity(token)
        return self._upsert_user(usuario, thesis_id)

    def resolve_current_user(self, token: str) -> User:
        """Valida el JWT de AppThesis y devuelve (creando/actualizando) el usuario local."""
        usuario, thesis_id = self._fetch_appthesis_identity(token)
        user, _ = self._upsert_user(usuario, thesis_id)
        return user
