"""Schema do Card de Inteligência — saída consolidada da síntese do manager."""

from __future__ import annotations

import json
import re
from typing import Any, TypedDict

DEFAULT_STATUS = "Pendente revisão humana"
DEFAULT_VALUE = "Não identificado"

CARD_FIELDS = (
    "conta",
    "ecossistema_mapeado",
    "concorrente_citado",
    "oportunidade",
    "persona_detectada",
    "sentimento",
    "status",
)


class IntelligenceCard(TypedDict):
    conta: str
    ecossistema_mapeado: str
    concorrente_citado: str
    oportunidade: str
    persona_detectada: str
    sentimento: str
    status: str


def empty_intelligence_card() -> IntelligenceCard:
    return {
        "conta": DEFAULT_VALUE,
        "ecossistema_mapeado": DEFAULT_VALUE,
        "concorrente_citado": DEFAULT_VALUE,
        "oportunidade": DEFAULT_VALUE,
        "persona_detectada": DEFAULT_VALUE,
        "sentimento": DEFAULT_VALUE,
        "status": DEFAULT_STATUS,
    }


def _strip_code_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text, count=1)
    return text.strip()


def _coerce_field(value: Any, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or default
    return str(value)


def parse_intelligence_card(raw: str | dict[str, Any] | None) -> IntelligenceCard:
    """Converte a resposta do LLM (string JSON ou dict) em IntelligenceCard."""
    card = empty_intelligence_card()

    if raw is None:
        return card

    if isinstance(raw, dict):
        data = raw
    else:
        try:
            data = json.loads(_strip_code_fence(str(raw)))
        except (json.JSONDecodeError, TypeError, ValueError):
            return card

    if not isinstance(data, dict):
        return card

    for field in CARD_FIELDS:
        default = DEFAULT_STATUS if field == "status" else DEFAULT_VALUE
        card[field] = _coerce_field(data.get(field), default)

    return card
