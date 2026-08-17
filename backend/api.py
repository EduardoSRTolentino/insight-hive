"""Ponto de entrada da API web (FastAPI): login, clientes e upload de .csv/.json.

Rodar com: uvicorn api:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from analysis_jobs import start_analysis_worker
from db import init_db
from routers import analysis, auth, clients
from security import assert_secure_secrets
from settings import get_settings
from uploads import content_length_exceeds, upload_too_large_detail


@asynccontextmanager
async def lifespan(_app: FastAPI):
    assert_secure_secrets()
    init_db()
    start_analysis_worker()
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


@app.middleware("http")
async def reject_oversize_analysis_upload(request: Request, call_next):
    if request.method == "POST" and request.url.path.rstrip("/") == "/api/analysis/upload":
        max_bytes = get_settings().max_upload_bytes
        if content_length_exceeds(request.headers.get("content-length"), max_bytes):
            return JSONResponse(
                status_code=413,
                content={"detail": upload_too_large_detail(max_bytes)},
            )
    return await call_next(request)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
