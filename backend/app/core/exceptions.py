"""Excepciones de dominio (harness §48) y su traducción centralizada a HTTP.

Los servicios lanzan estas excepciones; nunca deben construir `HTTPException`
directamente (harness §41: "no repetir validaciones manualmente en los
endpoints"). `register_exception_handlers` es el único lugar que las traduce.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class ColmenaDomainError(Exception):
    """Base de todas las excepciones de dominio de Colmena."""

    http_status: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "DOMAIN_ERROR"

    def __init__(self, message: str, **extra: object) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra


class NotFoundError(ColmenaDomainError):
    http_status = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class InstrumentLockedError(ColmenaDomainError):
    """Instrumento/versión protegido (`is_system` o estado ACTIVE/USED/CLOSED)."""

    http_status = status.HTTP_409_CONFLICT
    error_code = "SYSTEM_INSTRUMENT_LOCKED"


class InvalidInstrumentVersionError(ColmenaDomainError):
    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "INVALID_INSTRUMENT_VERSION"


class InvalidQuestionTypeError(ColmenaDomainError):
    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "INVALID_QUESTION_TYPE"


class VariableConversionError(ColmenaDomainError):
    """Cambio destructivo de `data_type` no permitido (harness §8)."""

    http_status = status.HTTP_409_CONFLICT
    error_code = "VARIABLE_CONVERSION_ERROR"


class ValidationDomainError(ColmenaDomainError):
    """Violación de una regla de negocio que no encaja en un tipo más específico."""

    http_status = 422
    error_code = "VALIDATION_ERROR"


class ConflictError(ColmenaDomainError):
    http_status = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"


class AuthenticationError(ColmenaDomainError):
    """Credenciales inválidas o token ausente/expirado/malformado."""

    http_status = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(ColmenaDomainError):
    """Usuario autenticado pero sin permisos suficientes sobre el recurso."""

    http_status = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"


class RateLimitExceededError(ColmenaDomainError):
    """Límite de solicitudes excedido (E-17, protección anti-abuso)."""

    http_status = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"


class UnsupportedAnalysisError(ColmenaDomainError):
    """`analysis_type` no reconocido o todavía no implementado (harness §48)."""

    http_status = status.HTTP_400_BAD_REQUEST
    error_code = "UNSUPPORTED_ANALYSIS"


class InvalidAnalysisAssumptionError(ColmenaDomainError):
    """Supuesto estadístico básico no cumplido (harness §47), p.ej. media sobre
    una variable NOMINAL, o crosstab sobre una variable SCALE."""

    http_status = 422
    error_code = "INVALID_ANALYSIS_ASSUMPTION"


class InsufficientSampleError(ColmenaDomainError):
    """No hay casos válidos suficientes para ejecutar el análisis (harness §48)."""

    http_status = 422
    error_code = "INSUFFICIENT_SAMPLE"


class PublicResourceUnavailableError(ColmenaDomainError):
    """Estudio inexistente o no OPEN, visto desde la URL pública. Se usa el
    mismo mensaje/código en ambos casos para no dejarle a un respondiente
    anónimo distinguir "el link está mal" de "todavía no está abierto"."""

    http_status = status.HTTP_404_NOT_FOUND
    error_code = "PUBLIC_RESOURCE_UNAVAILABLE"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ColmenaDomainError)
    async def _handle_domain_error(request: Request, exc: ColmenaDomainError) -> JSONResponse:
        del request
        body: dict[str, object] = {"error_code": exc.error_code, "message": exc.message}
        body.update(exc.extra)
        return JSONResponse(status_code=exc.http_status, content=body)
