from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECURITY_MAX_STRING_LENGTH: int = 256
    SECURITY_MAX_NESTING_DEPTH: int = 20
    SECURITY_MAX_INTEGER_DIGITS: int = 18
    INFERENCE_MAX_SAMPLES: int = 20
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    LOG_LEVEL: str = "INFO"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
