"""
Application configuration module.
All settings are loaded from environment variables via .env file.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "MyApp"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "myapp"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    REDIS_MAX_CONNECTIONS: int = 20

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-secure-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "DEBUG"

    # === 業務設定 ===

    # 台股開盤檢查：回溯補抓天數
    TWSE_OPEN_CHECK_BACKFILL_DAYS: int = 5

    # 三大法人買賣金額（上市）：回溯補抓天數
    TWSE_INSTITUTIONAL_BACKFILL_DAYS: int = 5

    # 三大法人買賣金額（上櫃）：回溯補抓天數
    TPEX_INSTITUTIONAL_BACKFILL_DAYS: int = 5

    # 融資融券餘額：回溯補抓天數
    MARGIN_TRADING_BACKFILL_DAYS: int = 5

    # 台指期未平倉：回溯補抓天數
    FUTURES_OI_BACKFILL_DAYS: int = 5

    # 期貨三大法人未平倉：回溯補抓天數
    FUTURES_INSTITUTIONAL_BACKFILL_DAYS: int = 5

    # FinMind API
    FINMIND_API_TOKEN: str = ""

    # 圖表預設顯示天數
    CHART_DEFAULT_DAYS: int = 30

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance (singleton pattern)."""
    return Settings()
