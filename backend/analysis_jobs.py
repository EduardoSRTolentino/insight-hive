"""Worker em thread: a análise do Ollama não bloqueia o request HTTP."""

from __future__ import annotations

import logging
from queue import Queue
from threading import Thread

import httpx
from ollama import ResponseError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db import SessionLocal
from graph.builder import get_compiled_graph
from models import AnalysisJob, Meeting
from schemas.intelligence_card import is_empty_card, parse_intelligence_card

logger = logging.getLogger(__name__)

OLLAMA_FAIL_DETAIL = (
    "O modelo local (Ollama) falhou durante a análise. "
    "Tente novamente em instantes; se persistir, reinicie o Ollama "
    "ou use um arquivo menor."
)

EMPTY_CARD_DETAIL = (
    "A síntese não retornou dados aproveitáveis (resposta do modelo vazia ou "
    "truncada). Tente novamente; se persistir, aumente NUM_PREDICT_SYNTHESIS "
    "ou reduza MAX_SPECIALISTS."
)

_queue: Queue[int] = Queue()
_started = False


def enqueue(job_id: int) -> None:
    _queue.put(job_id)


def start_worker() -> None:
    global _started
    if _started:
        return
    _started = True
    thread = Thread(target=_loop, daemon=True, name="analysis-worker")
    thread.start()


def recover_queued_jobs() -> None:
    """Reenfileira jobs interrompidos (queued/running) após restart."""
    with SessionLocal() as db:
        jobs = db.scalars(
            select(AnalysisJob).where(AnalysisJob.status.in_(("queued", "running")))
        ).all()
        ids: list[int] = []
        for job in jobs:
            job.status = "queued"
            job.error_detail = None
            ids.append(job.id)
        db.commit()
    for job_id in ids:
        enqueue(job_id)


def start_analysis_worker() -> None:
    start_worker()
    recover_queued_jobs()


def _fail(job_id: int, detail: str) -> None:
    with SessionLocal() as db:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            return
        job.status = "failed"
        job.error_detail = detail
        db.commit()


def process_job(job_id: int) -> None:
    with SessionLocal() as db:
        job = db.get(AnalysisJob, job_id)
        if job is None or job.status not in {"queued", "running"}:
            return
        job.status = "running"
        db.commit()
        input_text = job.input_text
        client_id = job.client_id
        filename = job.source_filename

    try:
        resultado = get_compiled_graph().invoke({"input": input_text, "reports": []})
    except (ResponseError, ConnectionError, TimeoutError, OSError, httpx.TimeoutException):
        logger.exception("Ollama falhou na análise job_id=%s", job_id)
        _fail(job_id, OLLAMA_FAIL_DETAIL)
        return
    except Exception:
        logger.exception("Falha inesperada na análise job_id=%s", job_id)
        _fail(job_id, "Falha inesperada na análise.")
        return

    card = parse_intelligence_card(resultado.get("final_report"))
    if is_empty_card(card):
        # manager_synthesis já logou o raw da resposta. Aqui a decisão de
        # produto: não salvar uma reunião com o card todo em "Não
        # identificado" como se fosse um resultado válido — melhor `failed`
        # com um detalhe acionável do que sucesso vazio.
        _fail(job_id, EMPTY_CARD_DETAIL)
        return

    try:
        with SessionLocal() as db:
            job = db.get(AnalysisJob, job_id)
            if job is None:
                return
            meeting = Meeting(
                client_id=client_id,
                source_filename=filename,
                triage=resultado.get("triage") or "",
                selected_agents=list(resultado.get("selected_agents") or []),
                final_report=card,
            )
            db.add(meeting)
            db.flush()
            job.meeting_id = meeting.id
            job.status = "done"
            job.error_detail = None
            db.commit()
    except IntegrityError:
        _fail(job_id, "Cliente não encontrado.")


def _loop() -> None:
    while True:
        job_id = _queue.get()
        try:
            process_job(job_id)
        except Exception:
            logger.exception("Worker falhou no job_id=%s", job_id)
            _fail(job_id, "Falha inesperada na análise.")
        finally:
            _queue.task_done()
