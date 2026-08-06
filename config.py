import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_ROOT = BASE_DIR / "data"


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    DATA_ROOT = Path(os.getenv("DATA_ROOT", DEFAULT_DATA_ROOT)).expanduser().resolve()
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DATA_ROOT / 'pythonstudy.db'}",
    ).replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "connect_args": {"timeout": 30},
    }
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))
    UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", DATA_ROOT / "uploads")).expanduser().resolve()
    GENERATED_ROOT = Path(os.getenv("GENERATED_ROOT", DATA_ROOT / "generated")).expanduser().resolve()
    TEMP_ROOT = Path(os.getenv("TEMP_ROOT", DATA_ROOT / "temp")).expanduser().resolve()
    CODE_EXECUTION_ENABLED = env_flag("CODE_EXECUTION_ENABLED", True)
    CODE_TIMEOUT_SECONDS = float(os.getenv("CODE_TIMEOUT_SECONDS", "3"))
    CODE_MEMORY_MB = int(os.getenv("CODE_MEMORY_MB", "256"))
    CODE_OUTPUT_LIMIT = int(os.getenv("CODE_OUTPUT_LIMIT", "20000"))
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False
    PREFERRED_URL_SCHEME = "https"
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        unsafe_values = {"", "dev-change-me", "change-this-secret", "replace-with-random-secret"}
        if cls.SECRET_KEY in unsafe_values:
            raise RuntimeError("Для production необходимо задать надежный SECRET_KEY.")


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
