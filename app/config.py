from pydantic_settings import BaseSettings
import os
import warnings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./attendence.db"
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str = "redis://localhost:6379/0"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "attendence-files"

    model_config = {"env_file": ".env"}


settings = Settings()

# Env override: env vars take precedence over defaults
_env_key = os.environ.get("SECRET_KEY")
if _env_key:
    settings.SECRET_KEY = _env_key

if not settings.SECRET_KEY:
    warnings.warn(
        "SECRET_KEY is not set! Using INSECURE dev default. "
        "Set SECRET_KEY environment variable or add to .env file.",
        RuntimeWarning,
        stacklevel=2,
    )
    settings.SECRET_KEY = "dev-insecure-change-me-in-production"
