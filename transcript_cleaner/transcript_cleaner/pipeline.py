"""Orquestração do pipeline de limpeza."""

from __future__ import annotations

import os
from typing import Any

from .llm import LlmClient
from .models import CleanResult, Turn, empty_stats
from .normalize import NormalizeError, normalize_content, normalize_file
from .stage1_text import clean_turns_text
from .stage2_format import format_turns
from .stage3_filter import filter_turns
from .stage4_summarize import should_summarize, summarize_turns


def _chars(turns: list[Turn]) -> int:
    return sum(len(t["text"]) for t in turns)


def clean_turns(
    turns: list[Turn],
    *,
    llm_client: LlmClient | None = None,
    config: dict[str, Any] | None = None,
) -> CleanResult:
    cfg = dict(config or {})
    stats = empty_stats()
    stats["chars_before"] = _chars(turns)
    stats["turns_before"] = len(turns)

    # 1) limpeza textual → 2) filtro KEEP/DROP → 3) merge/speakers → 4) sumarização
    stage1 = clean_turns_text(
        turns,
        fillers=cfg.get("fillers"),
        keep_inaudible=bool(cfg.get("keep_inaudible", False)),
    )

    filtered, dropped, llm_used = filter_turns(
        stage1,
        llm_client=llm_client,
        edge_window=int(cfg.get("edge_window", 3)),
    )
    stats["turns_dropped"] = dropped
    stats["llm_used"] = llm_used

    formatted, speaker_map, cleaned_text = format_turns(filtered)

    if not formatted:
        # Filtro removeu tudo (reunião só de saudação/concordância): não há nada
        # substantivo para analisar. Deixa o chamador cair para o texto bruto,
        # em vez de mandar "# Speakers" sozinho para o grafo.
        raise NormalizeError(
            "A limpeza da transcrição removeu todos os turnos; nada substantivo restou."
        )

    stage4_used = False
    if llm_client is not None and should_summarize(
        formatted,
        cleaned_text,
        max_duration_seconds=int(cfg.get("max_duration_seconds", 2 * 3600)),
        max_tokens=int(cfg.get("max_tokens", 10_000)),
    ):
        cleaned_text = summarize_turns(
            formatted,
            speaker_map,
            llm_client,
            config=cfg,
        )
        stage4_used = True
        stats["llm_used"] = True

    stats["stage4_used"] = stage4_used
    stats["chars_after"] = len(cleaned_text)
    stats["turns_after"] = len(formatted)

    return {
        "cleaned_text": cleaned_text,
        "cleaned_turns": formatted,
        "speaker_map": speaker_map,
        "stats": stats,
    }


def clean_file(
    source: str | bytes,
    *,
    format: str | None = None,
    llm_client: LlmClient | None = None,
    config: dict[str, Any] | None = None,
    filename: str | None = None,
) -> CleanResult:
    """Limpa um arquivo (path) ou conteúdo em bytes/str."""
    if isinstance(source, str) and os.path.isfile(source):
        turns = normalize_file(source, format=format)
    else:
        turns = normalize_content(
            source,
            filename=filename,
            format=format,
        )
    return clean_turns(turns, llm_client=llm_client, config=config)
