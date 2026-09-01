from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Orígenes locales del monorepo `fullProyect` que consumen COLMENA: su propio
# frontend (5174), el frontend de AppThesis (5173) y su rango de puertos vecino.
_MONOREPO_LOCAL_ORIGINS = [
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1")
    for port in (5173, 5174, 5175)
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://colmena:colmena@localhost:5432/colmena"
    database_url_sync: str = "postgresql+psycopg://colmena:colmena@localhost:5432/colmena"

    api_v1_prefix: str = "/api/v1"

    default_page_size: int = 25
    max_page_size: int = 200

    export_storage_dir: str = "./exports_storage"

    jwt_secret_key: str = "dev-only-insecure-secret-change-me-in-production-please-1234567890"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # Monorepo: AppThesis (thesis-backend NestJS) valida el cross-login. COLMENA
    # espeja al usuario llamando GET {thesis_api_base_url}/auth/me.
    thesis_api_base_url: str = "http://localhost:3000"

    cors_origins: list[str] = _MONOREPO_LOCAL_ORIGINS
    # Orígenes extra separados por coma (p. ej. túneles Cloudflare de los
    # frontends). Se combinan con `cors_origins` en `all_cors_origins`.
    # Acepta tanto CORS_EXTRA_ORIGINS como COLMENA_CORS_EXTRA_ORIGINS (el nombre
    # que usan iniciar.sh / run.ps1 / INICIAR.md del monorepo).
    cors_extra_origins: str = Field(
        default="",
        validation_alias=AliasChoices("cors_extra_origins", "colmena_cors_extra_origins"),
    )
    # Túneles efímeros *.trycloudflare.com: se permiten por regex para no tener
    # que listarlos uno a uno en cada sesión.
    cors_allow_origin_regex: str = r"https://.*\.trycloudflare\.com"

    @property
    def all_cors_origins(self) -> list[str]:
        extra = [o.strip() for o in self.cors_extra_origins.split(",") if o.strip()]
        return [*dict.fromkeys([*self.cors_origins, *extra])]

    # E-17: protección anti-abuso mínima del formulario público (sin Redis —
    # limitación conocida en despliegues multi-worker, documentada en
    # app/core/rate_limit.py).
    public_session_rate_limit_max: int = 10
    public_session_rate_limit_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
