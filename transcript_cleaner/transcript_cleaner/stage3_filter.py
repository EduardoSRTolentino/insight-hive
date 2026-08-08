"""Etapa 3 — filtragem de conteúdo não essencial (heurísticas + LLM opcional)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources
from typing import Iterable, Literal

from .llm import LlmClient
from .models import Turn

Label = Literal["KEEP", "DROP"]


def _load_json_list(name: str) -> list[str]:
    with resources.files(__package__).joinpath("data", name).open(encoding="utf-8") as handle:
        data = json.load(handle)
    return [str(item).lower() for item in data]


@lru_cache(maxsize=1)
def default_acknowledgements() -> tuple[str, ...]:
    return tuple(_load_json_list("acknowledgements_pt.json"))


@lru_cache(maxsize=1)
def default_greetings() -> tuple[str, ...]:
    return tuple(_load_json_list("greetings_pt.json"))


def _token_count(text: str) -> int:
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def _normalize_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def is_acknowledgement(text: str, phrases: Iterable[str] | None = None) -> bool:
    phrases = tuple(phrases) if phrases is not None else default_acknowledgements()
    normalized = _normalize_phrase(text)
    if _token_count(normalized) > 3:
        return False
    return normalized in set(phrases)


_TECH_NOISE = re.compile(
    r"\b(microfone|mute|mudo|sem [aá]udio|pode falar|n[aã]o te ou[cç]o|eco)\b",
    re.IGNORECASE,
)


def is_greeting_or_farewell(text: str, phrases: Iterable[str] | None = None) -> bool:
    phrases = tuple(phrases) if phrases is not None else default_greetings()
    normalized = _normalize_phrase(text)
    for phrase in phrases:
        if normalized == phrase or normalized.startswith(phrase + " ") or normalized.endswith(" " + phrase):
            return True
        if phrase in normalized and _token_count(normalized) <= 8:
            return True
    return False


def is_tech_noise(text: str) -> bool:
    return bool(_TECH_NOISE.search(text)) and _token_count(text) <= 12


def heuristic_labels(
    turns: list[Turn],
    *,
    edge_window: int = 3,
) -> dict[str, Label]:
    """Classifica turnos de forma determinística. Ambíguos não entram no dict."""
    labels: dict[str, Label] = {}
    n = len(turns)
    for index, turn in enumerate(turns):
        text = turn["text"]
        tid = turn["id"]
        if is_acknowledgement(text):
            labels[tid] = "DROP"
            continue
        if is_tech_noise(text):
            labels[tid] = "DROP"
            continue
        at_edge = index < edge_window or index >= max(0, n - edge_window)
        if at_edge and is_greeting_or_farewell(text):
            labels[tid] = "DROP"
            continue
        if _token_count(text) >= 12:
            labels[tid] = "KEEP"
    return labels


def _extract_json_array(raw: str) -> list[dict]:
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", raw)
        if not match:
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _build_classify_prompt(turns: list[Turn]) -> str:
    payload = [{"turn_id": t["id"], "speaker": t["speaker"], "text": t["text"]} for t in turns]
    return (
        "Classifique cada turno de reunião como KEEP ou DROP.\n"
        "KEEP = decisão, ação, risco, pergunta de negócio ou conteúdo substantivo.\n"
        "DROP = saudação, despedida, small talk, problema de áudio, concordância vazia "
        "(exceto voto/decisão formal).\n"
        "Responda APENAS com JSON array: "
        '[{"turn_id":"...","label":"KEEP"|"DROP"}, ...]\n\n'
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def classify_with_llm(
    turns: list[Turn],
    llm_client: LlmClient,
    *,
    edge_window: int = 3,
) -> dict[str, Label]:
    base = heuristic_labels(turns, edge_window=edge_window)
    ambiguous = [t for t in turns if t["id"] not in base]
    if not ambiguous:
        return base

    # inclui vizinhos para contexto
    by_id = {t["id"]: i for i, t in enumerate(turns)}
    context_ids: set[str] = set()
    for turn in ambiguous:
        i = by_id[turn["id"]]
        for j in (i - 1, i, i + 1):
            if 0 <= j < len(turns):
                context_ids.add(turns[j]["id"])
    batch = [t for t in turns if t["id"] in context_ids]

    raw = llm_client.complete(_build_classify_prompt(batch))
    for item in _extract_json_array(raw):
        tid = str(item.get("turn_id", ""))
        label = str(item.get("label", "")).upper()
        if tid in {t["id"] for t in ambiguous} and label in {"KEEP", "DROP"}:
            base[tid] = label  # type: ignore[assignment]

    # ambíguos sem label → KEEP (preferir ruído a apagar decisão)
    for turn in ambiguous:
        base.setdefault(turn["id"], "KEEP")
    return base


def filter_turns(
    turns: list[Turn],
    *,
    llm_client: LlmClient | None = None,
    edge_window: int = 3,
) -> tuple[list[Turn], int, bool]:
    if llm_client is None:
        labels = heuristic_labels(turns, edge_window=edge_window)
        # sem LLM: só remove DROPs heurísticos; resto KEEP implícito
        kept = [t for t in turns if labels.get(t["id"]) != "DROP"]
        dropped = len(turns) - len(kept)
        return kept, dropped, False

    labels = classify_with_llm(turns, llm_client, edge_window=edge_window)
    kept = [t for t in turns if labels.get(t["id"], "KEEP") != "DROP"]
    dropped = len(turns) - len(kept)
    return kept, dropped, True
