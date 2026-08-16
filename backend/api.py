"""Ponto de entrada da API web (FastAPI): login, clientes e upload de .csv/.json.

Rodar com: uvicorn api:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routers import analysis, auth, clients
from security import assert_secure_secrets
from settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    assert_secure_secrets()
    init_db()
    yield


app = FastAPI(title="Sistema Multiagente API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
