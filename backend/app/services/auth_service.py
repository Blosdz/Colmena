from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import httpx
import jwt
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User

JWT_ALGORITHM = "HS256"


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

    # ── Login standalone de Colmena (email + contraseña) ──────────────────

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except ValueError:
            return False

    def _issue_token(self, user: User) -> str:
        return self._encode({"sub": user.id, "typ": "colmena"}, self.settings.jwt_expire_minutes)

    def _encode(self, claims: dict, expire_minutes: int) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {**claims, "iat": now, "exp": now + timedelta(minutes=expire_minutes)},
            self.settings.jwt_secret,
            algorithm=JWT_ALGORITHM,
        )

    def _find_by_email(self, email: str) -> User | None:
        return self.db.scalar(
            select(User).where(
                func.lower(User.email) == email.strip().lower(),
                User.deleted_at.is_(None),
            )
        )

    def register_local(self, name: str, email: str, password: str) -> tuple[User, str]:
        email = email.strip().lower()
        if self._find_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta con este correo.",
            )
        user = User(
            name=name.strip(),
            username=email.split("@")[0] or email,
            email=email,
            status="active",
            password_hash=self._hash_password(password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user, self._issue_token(user)

    def login_local(self, email: str, password: str) -> tuple[User, str]:
        user = self._find_by_email(email)
        if user is None or not user.password_hash or not self._verify_password(
            password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos.",
            )
        return user, self._issue_token(user)

    def request_password_reset(self, email: str) -> str | None:
        """Devuelve un enlace de reset si hay una cuenta local con ese correo; si no, None.

        El router nunca revela cuál de los dos casos ocurrió (no enumeración de cuentas).
        Sin servicio de correo: en desarrollo el enlace se devuelve directo.
        """
        user = self._find_by_email(email)
        if user is None or not user.password_hash:
            return None
        token = self._encode({"sub": user.id, "typ": "pwreset"}, 30)
        base = self.settings.frontend_base_url.rstrip("/")
        return f"{base}/reset-password?token={token}"

    def reset_password(self, token: str, new_password: str) -> tuple[User, str]:
        try:
            payload = jwt.decode(
                token, self.settings.jwt_secret, algorithms=[JWT_ALGORITHM]
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El enlace de recuperación no es válido o ya expiró.",
            )
        if payload.get("typ") != "pwreset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El enlace de recuperación no es válido.",
            )
        user = self.db.get(User, payload.get("sub"))
        if user is None or user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="La cuenta ya no existe."
            )
        user.password_hash = self._hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user, self._issue_token(user)

    def _resolve_local_token(self, token: str) -> User | None:
        """Devuelve el usuario si `token` es un JWT válido emitido por Colmena; si no, None."""
        try:
            payload = jwt.decode(
                token, self.settings.jwt_secret, algorithms=[JWT_ALGORITHM]
            )
        except jwt.PyJWTError:
            return None
        if payload.get("typ") != "colmena":
            return None
        user = self.db.get(User, payload.get("sub"))
        if user is None or user.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="La cuenta ya no existe.",
            )
        return user

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
        """Resuelve el usuario autenticado.

        Primero intenta como JWT propio de Colmena (login standalone). Si no lo es,
        cae al cross-login con AppThesis: valida el token contra ``/auth/me`` y
        crea/actualiza el usuario espejo.
        """
        local_user = self._resolve_local_token(token)
        if local_user is not None:
            return local_user

        usuario, thesis_id = self._fetch_appthesis_identity(token)
        user, _ = self._upsert_user(usuario, thesis_id)
        return user
