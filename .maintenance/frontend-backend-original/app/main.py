"""
Ponto de entrada da API REST do sistema de recrutamento inteligente.

Correr em desenvolvimento:
    uvicorn app.main:app --reload

Documentação interativa:
    http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401  (garante que os modelos são registados em Base.metadata)

from app.api import (
    auth, companies, users, jobs, job_requirements, candidates,
    analysis, interviews, email, processing_logs, dashboard,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # NOTA: create_all() é conveniente em desenvolvimento. Em produção, usar
    # exclusivamente as migrations Alembic (ver database/migrations) para
    # controlar a evolução do esquema.
    if settings.ENVIRONMENT == "development":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sistema Inteligente de Análise e Recomendação de Candidatos",
    description=(
        "API REST para triagem de candidatos: gestão de vagas, requisitos, "
        "candidatos, candidaturas, motor de NLP/matching/scoring, ranking, "
        "entrevistas, feedback do recrutador e integração de e-mail."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(job_requirements.router)
app.include_router(candidates.router)
app.include_router(analysis.router)
app.include_router(interviews.router)
app.include_router(email.router)
app.include_router(processing_logs.router)
app.include_router(dashboard.router)


@app.get("/api/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
