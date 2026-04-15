"""
Parser Service — Configuration.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class ParserSettings(BaseSettings):
    """Настройки Parser Service"""

    # Environment
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://estet:estet_dev_password@localhost:5432/estet_platform"

    # Polza.ai (Gemini API)
    POLZA_API_KEY: str = "your_polza_api_key_here"
    POLZA_API_URL: str = "https://polza.ai/api/v2"
    GEMINI_MODEL: str = "google/gemini-2.5-flash-lite"
    GEMINI_MAX_TOKENS: int = 2048
    GEMINI_TEMPERATURE: float = 0.2

    # Parser
    PARSER_HEADLESS_BROWSER: bool = True
    PARSER_SCRAPING_DELAY: float = 2.0
    PARSER_MAX_RETRIES: int = 3
    PARSER_TIMEOUT: int = 60
    PARSER_IMAGES_PATH: str = "data/images"
    PARSER_JSON_OUTPUT_PATH: str = "data/processed"

    # Base URLs
    ESTET_BASE_URL: str = "https://moscow.estetdveri.ru"
    ESTET_CATALOG_URL: str = "https://moscow.estetdveri.ru/catalog"

    # Catalog categories (разделы каталога)
    ESTET_CATALOG_CATEGORIES: list = [
        "/catalog/mezhkomnatnye-dveri/",
        "/catalog/skrytye-dveri/",
        "/catalog/vkhodnye-dveri/",
        "/catalog/mezhkomnatnye-peregorodki/",
        "/catalog/mebel/",
        "/catalog/dekorativnye-reyki/",
        "/catalog/stenovye-paneli/",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = ParserSettings()
