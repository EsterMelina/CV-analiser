"""
Configuração da ligação à base de dados (SQLAlchemy 2.0 style).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True, future=True)

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
