from functools import lru_cache

from loguru import logger
from pydantic import BaseSettings


class Settings(BaseSettings):
    port: str = "5001"
    env_name: str = "Local"
    base_url: str = f"http://localhost:{port}"
    db_url: str = "sqlite:///./shortener.db"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    logger.debug(f"Loading settings for: {settings.env_name}")
    return settings
