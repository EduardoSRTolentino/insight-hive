"""Etapa 1 — limpeza textual superficial (regex + dicionários)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources
from typing import Iterable

from .models import Turn

_ASR_PATTERNS = [
    re.compile(r"\[inaud[ií]vel\]", re.IGNORECASE),
    re.compile(r"\(risos?\)", re.IGNORECASE),
    re.compile(r"\[silence\]", re.IGNORECASE),
    re.compile(r"<[^>]+>"),
]


def _load_json_list(name: str) -> list[str]:
    with resources.files(__package__).joinpath("data", name).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Arquivo de dados inválido: {name}")
    return [str(item) for item in data]


@lru_cache(maxsize=1)
def default_fillers() -> tuple[str, ...]:
    return tuple(_load_json_list("fillers_pt.json"))


def _filler_pattern(fillers: Iterable[str]) -> re.Pattern[str]:
    # multiword first (sorted by length desc)
    escaped = sorted((re.escape(f) for f in fillers if f.strip()), key=len, reverse=True)
    if not escaped:
        return re.compile(r"(?!)")  # never matches
    body = "|".join(escaped)
    return re.compile(rf"(?<!\w)(?:{body})(?!\w)", re.IGNORECASE)


def remove_fillers(text: str, fillers: Iterable[str] | None = None) -> str:
    patterns = fillers if fillers is not None else default_fillers()
    return _filler_pattern(patterns).sub(" ", text)


def collapse_stutters(text: str) -> str:
    # palavra repetida imediatamente (mas não números — "500 500 reais" não é gagueira)
    text = re.sub(
        r"\b(?!\d+\b)(\w+)(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE
    )
    # bigrama repetido (a gente a gente)
    text = re.sub(
        r"\b(\w+\s+\w+)(?:\s+\1\b)+",
        r"\1",
        text,
        flags=re.IGNORECASE,
    )
    return text


def remove_asr_artifacts(text: str, *, keep_inaudible: bool = False) -> str:
    for pattern in _ASR_PATTERNS:
        if keep_inaudible and "inaud" in pattern.pattern.lower():
            continue
        text = pattern.sub(" ", text)
    return text


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def cleanup_punctuation(text: str) -> str:
    """Remove artefatos deixados pela remoção de fillers."""
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r",\s*([?.!;:])", r"\1", text)
    text = re.sub(r"\s+([?.!;:])", r"\1", text)
    text = re.sub(r"^[,\s]+", "", text)
    text = re.sub(r"(?<=\w)\s{2,}(?=\w)", " ", text)
    return text.strip(" ,")


def clean_text(
    text: str,
    *,
    fillers: Iterable[str] | None = None,
    keep_inaudible: bool = False,
) -> str:
    text = remove_asr_artifacts(text, keep_inaudible=keep_inaudible)
    text = remove_fillers(text, fillers=fillers)
    text = collapse_stutters(text)
    text = cleanup_punctuation(text)
    return normalize_whitespace(text)


def clean_turns_text(
    turns: list[Turn],
    *,
    fillers: Iterable[str] | None = None,
    keep_inaudible: bool = False,
) -> list[Turn]:
    cleaned: list[Turn] = []
    for turn in turns:
        new_text = clean_text(
            turn["text"],
            fillers=fillers,
            keep_inaudible=keep_inaudible,
        )
        if not new_text:
            continue
        cleaned.append({**turn, "text": new_text})
    return cleaned
