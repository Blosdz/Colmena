from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Colmena", alias="COLMENA_APP_NAME")
    environment: str = Field(default="development", alias="COLMENA_ENV")
    db_path: str = Field(default="./data/db/colmena.db", alias="COLMENA_DB_PATH")
    public_base_url: str = Field(default="http://127.0.0.1:8080", alias="COLMENA_PUBLIC_BASE_URL")
    api_v1_prefix: str = "/api/v1"
    thesis_api_base_url: str = Field(
        default="http://localhost:3000", alias="THESIS_API_BASE_URL"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def database_file(self) -> Path:
        db_file = Path(self.db_path)
        if not db_file.is_absolute():
            db_file = (self.backend_dir / db_file).resolve()
        return db_file

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_file.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
