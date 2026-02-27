from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECURITY_MAX_STRING_LENGTH: int = 256
    SECURITY_MAX_NESTING_DEPTH: int = 20
    SECURITY_MAX_INTEGER_DIGITS: int = 18
    INFERENCE_MAX_SAMPLES: int = 20
    CORS_ORIGINS: list[str] = []
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "OPTIONS"]
    CORS_ALLOW_HEADERS: list[str] = ["Authorization", "Content-Type"]
    LOG_LEVEL: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
