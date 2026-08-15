"""Rota de análise: upload de .csv/.json que aciona o sistema multiagente."""

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from ollama import ResponseError
from sqlalchemy.orm import Session

from db import get_db
from file_input import FileInputError
from graph.builder import compiled_graph
from models import Client, Meeting
from prepare_analysis_input import prepare_graph_input
from schemas.clients import MeetingDetail
from schemas.intelligence_card import parse_intelligence_card
from security import get_current_user

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/upload", response_model=MeetingDetail)
def upload(
    file: UploadFile,
    client_id: int = Form(...),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeetingDetail:
    del current_user
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado.",
        )

    content = file.file.read()

    try:
        entrada = prepare_graph_input(file.filename, content)
    except FileInputError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        resultado = compiled_graph.invoke({"input": entrada, "reports": []})
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha inesperada na análise: {exc}",
        ) from exc

    meeting = Meeting(
        client_id=client.id,
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
        client_id=client.id,
        client_name=client.name,
        source_filename=meeting.source_filename,
        created_at=meeting.created_at,
        triage=meeting.triage,
        selected_agents=list(meeting.selected_agents or []),
        final_report=meeting.final_report or {},
    )
