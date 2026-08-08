"""Etapa 4 — sumarização intermediária para reuniões longas (requer LlmClient)."""

from __future__ import annotations

import re
from typing import Any

from .llm import LlmClient
from .models import Turn
from .stage2_format import serialize_turns


def _parse_ts_seconds(value: str | None) -> int | None:
    if not value:
        return None
    match = re.match(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})$", value.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def estimate_tokens(text: str) -> int:
    # heurística simples ~4 chars/token para PT
    return max(1, len(text) // 4)


def meeting_duration_seconds(turns: list[Turn]) -> int | None:
    starts = [_parse_ts_seconds(t.get("start")) for t in turns]
    ends = [_parse_ts_seconds(t.get("end")) for t in turns]
    values = [v for v in starts + ends if v is not None]
    if len(values) < 2:
        return None
    return max(values) - min(values)


def should_summarize(
    turns: list[Turn],
    text: str,
    *,
    max_duration_seconds: int = 2 * 3600,
    max_tokens: int = 10_000,
) -> bool:
    duration = meeting_duration_seconds(turns)
    if duration is not None and duration > max_duration_seconds:
        return True
    return estimate_tokens(text) > max_tokens


def _partition_by_turns(turns: list[Turn], chunk_size: int) -> list[list[Turn]]:
    if chunk_size <= 0:
        return [turns]
    return [turns[i : i + chunk_size] for i in range(0, len(turns), chunk_size)]


def _partition_by_time(turns: list[Turn], window_seconds: int) -> list[list[Turn]]:
    if not turns:
        return []
    buckets: list[list[Turn]] = []
    current: list[Turn] = []
    anchor = _parse_ts_seconds(turns[0].get("start")) or 0
    for turn in turns:
        ts = _parse_ts_seconds(turn.get("start"))
        if ts is None:
            current.append(turn)
            continue
        if current and ts - anchor >= window_seconds:
            buckets.append(current)
            current = [turn]
            anchor = ts
        else:
            if not current:
                anchor = ts
            current.append(turn)
    if current:
        buckets.append(current)
    return buckets


def _summarize_block_prompt(block_text: str, speaker_map: dict[str, str]) -> str:
    speakers = "\n".join(f"{k}={v}" for k, v in speaker_map.items())
    return (
        "Resuma o bloco de reunião abaixo de forma densa para um LLM analítico.\n"
        "Mantenha: decisões, action items (quem / o quê / prazo), riscos e dissenso relevante.\n"
        "Descarte debate longo sem mudança de conclusão.\n"
        "Responda em texto curto, em português, sem introdução.\n\n"
        f"Speakers:\n{speakers}\n\n"
        f"Bloco:\n{block_text}"
    )


def summarize_turns(
    turns: list[Turn],
    speaker_map: dict[str, str],
    llm_client: LlmClient,
    *,
    chunk_turns: int = 40,
    window_seconds: int = 600,
    config: dict[str, Any] | None = None,
) -> str:
    cfg = config or {}
    window = int(cfg.get("stage4_window_seconds", window_seconds))
    chunk = int(cfg.get("stage4_chunk_turns", chunk_turns))

    if any(t.get("start") for t in turns):
        blocks = _partition_by_time(turns, window)
    else:
        blocks = _partition_by_turns(turns, chunk)

    summaries: list[str] = []
    for index, block in enumerate(blocks, start=1):
        block_text = serialize_turns(block, speaker_map)
        summary = llm_client.complete(_summarize_block_prompt(block_text, speaker_map)).strip()
        if summary:
            summaries.append(f"## Bloco {index}\n{summary}")

    header = ["# Speakers"] + [f"{k}={v}" for k, v in speaker_map.items()] + [""]
    return "\n".join(header + summaries).strip() + "\n"
