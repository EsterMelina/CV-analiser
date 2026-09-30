"""
Configuração da ligação à base de dados (SQLAlchemy 2.0 style).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.core.config import settings

engine_options = {"pool_pre_ping": True, "future": True}
if settings.sqlalchemy_database_url == "sqlite:///:memory:":
    # Partilhar a BD em memória entre a thread do TestClient e as fixtures.
    engine_options.update(poolclass=StaticPool, connect_args={"check_same_thread": False})
engine = create_engine(settings.sqlalchemy_database_url, **engine_options)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM."""
    pass


def get_db():
    """Dependência FastAPI que fornece uma sessão de BD por pedido."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
