from typing import Optional
from functools import lru_cache
from pydantic import BaseSettings


class BotSettings(BaseSettings):
    token: str
    url: str
    secret: Optional[str] = None
    server_title: Optional[str] = None
    group_id: Optional[str] = None

    class Config:
        env_prefix = "BOT_"
        env_file = ".env"


class RedisSettings(BaseSettings):
    host: str
    port: int
    password: Optional[str] = None

    class Config:
        env_prefix = "REDIS_"
        env_file = ".env"


class APISetings(BaseSettings):
    host: str
    port: int = 8000

    class Config:
        env_prefix = "API_"
        env_file = ".env"


@lru_cache
def get_api_settings() -> APISetings:
    return APISetings()


@lru_cache
def get_redis_settings() -> RedisSettings:
    return RedisSettings()


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()
