"""Rota de análise: upload de .csv/.json que aciona o sistema multiagente."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from ollama import ResponseError

from file_input import FileInputError, parse_file_content
from graph.builder import compiled_graph
from schemas.intelligence_card import parse_intelligence_card
from security import get_current_user

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/upload")
def upload(
    file: UploadFile,
    current_user: str = Depends(get_current_user),
) -> dict:
    content = file.file.read()

    try:
        entrada = parse_file_content(file.filename, content)
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

    return {
        "triage": resultado.get("triage", ""),
        "selected_agents": resultado.get("selected_agents", []),
        "final_report": parse_intelligence_card(resultado.get("final_report")),
    }
