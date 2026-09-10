from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Kubernetes Incident Triage"
    log_tail_lines: int = 200
    restart_warning_threshold: int = 3
    restart_critical_threshold: int = 10
    kubernetes_context: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
