from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")


def _env_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Settings:
    APP_NAME = os.getenv("APP_NAME", "CatTrace Agent")
    APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
    DEBUG = _env_bool("DEBUG", False)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    SQL_ECHO = _env_bool("SQL_ECHO", False)

    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'cattrace.db').as_posix()}")

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = _env_int("REDIS_PORT", 6379)

    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "visagent-images")
    MINIO_SECURE = _env_bool("MINIO_SECURE", False)

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = _env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    COOKIE_SECURE = _env_bool("COOKIE_SECURE", False)

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    LANGCHAIN_TRACING_V2 = _env_bool("LANGCHAIN_TRACING_V2", False)
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "cattrace")

    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080")

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = _env_int("PORT", 8888)
    BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000")

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def openai_base_url(self) -> str:
        return self.OPENAI_BASE_URL

    @property
    def openai_model(self) -> str:
        return self.OPENAI_MODEL

    @property
    def backend_api_base_url(self) -> str:
        return self.BACKEND_API_BASE_URL

    @property
    def host(self) -> str:
        return self.HOST

    @property
    def port(self) -> int:
        return self.PORT


settings = Settings()
