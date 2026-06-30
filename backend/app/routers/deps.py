from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Resuelve el usuario autenticado a partir del JWT de AppThesis (Bearer).

    Reutiliza ``AuthService`` para validar el token contra AppThesis y obtener
    (o crear) el usuario espejo local. 401 si falta o es invalido.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de autenticacion.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacion vacio.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthService(db).resolve_current_user(token)
