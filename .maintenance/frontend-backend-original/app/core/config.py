"""
Configuração central da aplicação.
Lê variáveis de ambiente (ficheiro .env) usando pydantic-settings.
"""
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base de dados — variáveis separadas (estilo Laravel), montadas numa
    # DATABASE_URL internamente. Também é aceite uma DATABASE_URL completa
    # diretamente, que tem prioridade se for definida explicitamente.
    DB_CONNECTION: str = "pgsql"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_DATABASE: str = "recruiter_db"
    DB_USERNAME: str = "recruiter_user"
    DB_PASSWORD: str = "recruiter_pass"

    DATABASE_URL: str | None = None

    # Segurança / JWT
    SECRET_KEY: str = "insecure-dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # App
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        """
        Retorna a DATABASE_URL a usar pelo SQLAlchemy.
        Se DATABASE_URL vier definida explicitamente no .env, usa-a tal e
        qual (permite continuar a suportar o formato antigo). Caso contrário,
        monta-a a partir das variáveis DB_* (estilo Laravel).
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        driver_by_connection = {
            "pgsql": "postgresql+psycopg2",
            "postgres": "postgresql+psycopg2",
            "postgresql": "postgresql+psycopg2",
            "mysql": "mysql+pymysql",
        }
        driver = driver_by_connection.get(self.DB_CONNECTION.lower(), "postgresql+psycopg2")
        password = quote_plus(self.DB_PASSWORD)
        return f"{driver}://{self.DB_USERNAME}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

