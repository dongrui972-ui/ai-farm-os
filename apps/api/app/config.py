from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


API_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE = f"sqlite:///{(API_ROOT / 'data' / 'farm.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "一级芯界 AI Farm OS"
    database_url: str = DEFAULT_SQLITE
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    seed_on_empty: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
