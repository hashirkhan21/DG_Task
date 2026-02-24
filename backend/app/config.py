from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "PersonFinderTool"
    ddg_timeout_seconds: int = 15
    ddg_max_results: int = 20
    rate_limit_per_minute: int = 30
    enable_langchain_agent: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

