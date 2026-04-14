"""
Vision API Service — Configuration.
"""
from pydantic_settings import BaseSettings
from typing import List


class VisionSettings(BaseSettings):
    """Настройки Vision API Service"""

    # Environment
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://estet:estet_dev_password@localhost:5432/estet_platform"

    # Polza.ai (Gemini API)
    POLZA_API_KEY: str = "your_polza_api_key_here"
    POLZA_API_URL: str = "https://polza.ai/api/v2"
    GEMINI_MODEL: str = "google/gemini-2.0-flash-lite-001"
    GEMINI_MAX_TOKENS: int = 2048
    GEMINI_TEMPERATURE: float = 0.2

    # API
    VISION_API_KEY: str = "your_secret_api_key_for_n8n"
    VISION_MAX_IMAGE_SIZE_MB: int = 10
    VISION_MAX_RESULTS: int = 10
    VISION_AUTH_REQUIRED: bool = True
    VISION_ALLOWED_ORIGINS: str = "http://localhost:3000,https://your-n8n-instance.app"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.VISION_ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = VisionSettings()
