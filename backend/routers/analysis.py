"""Rota de análise: enfileira o upload e devolve um job para polling."""

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from analysis_jobs import enqueue
from db import SessionLocal, get_db
from file_input import FileInputError
from models import AnalysisJob, User
from ownership import get_owned_client, get_owned_job
from prepare_analysis_input import prepare_graph_input
from routers.clients import meeting_detail
from schemas.clients import AnalysisJobPublic
from security import get_current_user, get_current_user_id
from settings import get_settings
from uploads import raise_upload_too_large, read_upload_capped

router = APIRouter(prefix="/analysis", tags=["analysis"])


def job_public(job: AnalysisJob) -> AnalysisJobPublic:
    meeting = None
    if job.meeting_id and job.meeting is not None:
        meeting = meeting_detail(job.meeting)
    status_value = job.status if job.status in {"queued", "running", "done", "failed"} else "failed"
    return AnalysisJobPublic(
        id=job.id,
        status=status_value,
        source_filename=job.source_filename,
        created_at=job.created_at,
        error_detail=job.error_detail,
        meeting=meeting,
    )


@router.post("/upload", response_model=AnalysisJobPublic, status_code=status.HTTP_202_ACCEPTED)
def upload(
    file: UploadFile,
    client_id: int = Form(...),
    user_id: int = Depends(get_current_user_id),
) -> AnalysisJobPublic:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe o nome de um arquivo.",
        )

    max_bytes = get_settings().max_upload_bytes
    declared = getattr(file, "size", None)
    if isinstance(declared, int) and declared > max_bytes:
        raise_upload_too_large(max_bytes)

    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas ou token expirado.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        client = get_owned_client(db, user, client_id)
        client_pk = client.id

    content = read_upload_capped(file, max_bytes)

    try:
        entrada = prepare_graph_input(file.filename, content)
    except FileInputError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    with SessionLocal() as db:
        job = AnalysisJob(
            user_id=user_id,
            client_id=client_pk,
            source_filename=file.filename or "",
            input_text=entrada,
            status="queued",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        public = job_public(job)

    enqueue(job.id)
    return public


@router.get("/jobs/{job_id}", response_model=AnalysisJobPublic)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisJobPublic:
    job = get_owned_job(db, current_user, job_id)
    if job.meeting is not None:
        _ = job.meeting.client
    return job_public(job)
