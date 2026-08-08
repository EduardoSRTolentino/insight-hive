"""Tipos públicos do pipeline de limpeza."""

from __future__ import annotations

from typing import Any, TypedDict


class Turn(TypedDict):
    id: str
    speaker: str
    text: str
    start: str | None
    end: str | None


class CleanStats(TypedDict):
    chars_before: int
    chars_after: int
    turns_before: int
    turns_after: int
    turns_dropped: int
    stage4_used: bool
    llm_used: bool


class CleanResult(TypedDict):
    cleaned_text: str
    cleaned_turns: list[Turn]
    speaker_map: dict[str, str]
    stats: CleanStats


def empty_stats() -> CleanStats:
    return {
        "chars_before": 0,
        "chars_after": 0,
        "turns_before": 0,
        "turns_after": 0,
        "turns_dropped": 0,
        "stage4_used": False,
        "llm_used": False,
    }


def as_config(config: dict[str, Any] | None) -> dict[str, Any]:
    return dict(config or {})
