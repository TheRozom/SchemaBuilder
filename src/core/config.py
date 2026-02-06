from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    ENABLE_AI: bool = False
    AI_MODEL: str = "gpt-3.5-turbo"
    AI_MAX_TOKENS: int = 200
    AI_TEMPERATURE: float = 0.0
    AI_SCHEMA_TRUNCATE_LENGTH: int = 3000
    SECURITY_MAX_STRING_LENGTH: int = 256
    SECURITY_MAX_NESTING_DEPTH: int = 20
    SECURITY_MAX_INTEGER_DIGITS: int = 18
    INFERENCE_MAX_SAMPLES: int = 20
    # SECURITY WARNING: Default CORS_ORIGINS allows all origins (["*"])
    # In production, set explicit origins via environment variable:
    # CORS_ORIGINS='["https://your-domain.com", "https://app.your-domain.com"]'
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    LOG_LEVEL: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
