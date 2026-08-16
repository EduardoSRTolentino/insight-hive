"""Rota de análise: upload de .csv/.json que aciona o sistema multiagente."""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from ollama import ResponseError
from sqlalchemy.exc import IntegrityError

from db import SessionLocal
from file_input import FileInputError
from graph.builder import get_compiled_graph
from models import Client, Meeting
from prepare_analysis_input import prepare_graph_input
from schemas.clients import MeetingDetail
from schemas.intelligence_card import parse_intelligence_card
from security import get_current_user
from settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/upload", response_model=MeetingDetail)
def upload(
    file: UploadFile,
    client_id: int = Form(...),
    current_user: str = Depends(get_current_user),
) -> MeetingDetail:
    del current_user
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe o nome de um arquivo.",
        )

    with SessionLocal() as db:
        client = db.get(Client, client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado.",
            )
        client_pk = client.id
        client_name = client.name

    content = file.file.read()
    max_bytes = get_settings().max_upload_bytes
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite de {max_bytes} bytes.",
        )

    try:
        entrada = prepare_graph_input(file.filename, content)
    except FileInputError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        resultado = get_compiled_graph().invoke({"input": entrada, "reports": []})
    except (ResponseError, ConnectionError, TimeoutError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "O modelo local (Ollama) falhou durante a análise. "
                "Tente novamente em instantes; se persistir, reinicie o Ollama "
                "ou use um arquivo menor."
            ),
        ) from exc
    except Exception as exc:
        logger.exception("Falha inesperada na análise.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha inesperada na análise.",
        ) from exc

    try:
        with SessionLocal() as db:
            meeting = Meeting(
                client_id=client_pk,
                source_filename=file.filename or "",
                triage=resultado.get("triage") or "",
                selected_agents=list(resultado.get("selected_agents") or []),
                final_report=parse_intelligence_card(resultado.get("final_report")),
            )
            db.add(meeting)
            db.commit()
            db.refresh(meeting)
            return MeetingDetail(
                id=meeting.id,
                client_id=client_pk,
                client_name=client_name,
                source_filename=meeting.source_filename,
                created_at=meeting.created_at,
                triage=meeting.triage,
                selected_agents=list(meeting.selected_agents or []),
                final_report=meeting.final_report or {},
            )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        ) from exc
