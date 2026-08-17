"""Schema do Card de Inteligência — saída consolidada da síntese do manager."""

from __future__ import annotations

import json
import re
from typing import Any, TypedDict

DEFAULT_STATUS = "Pendente revisão humana"
DEFAULT_VALUE = "Não identificado"
DEFAULT_ANALISE = "Sem análise aprofundada disponível."

POINT_FIELDS = (
    "ecossistema_mapeado",
    "concorrente_citado",
    "oportunidade",
    "retencao_churn",
    "budget",
    "persona_detectada",
    "sentimento",
)

CARD_FIELDS = ("conta", *POINT_FIELDS, "status")


class CardPoint(TypedDict):
    valor: str
    analise: str
    evidencias: list[str]


class IntelligenceCard(TypedDict):
    conta: str
    ecossistema_mapeado: CardPoint
    concorrente_citado: CardPoint
    oportunidade: CardPoint
    retencao_churn: CardPoint
    budget: CardPoint
    persona_detectada: CardPoint
    sentimento: CardPoint
    status: str


def empty_card_point(valor: str = DEFAULT_VALUE) -> CardPoint:
    return {
        "valor": valor,
        "analise": DEFAULT_ANALISE,
        "evidencias": [],
    }


def empty_intelligence_card() -> IntelligenceCard:
    return {
        "conta": DEFAULT_VALUE,
        "ecossistema_mapeado": empty_card_point(),
        "concorrente_citado": empty_card_point(),
        "oportunidade": empty_card_point(),
        "retencao_churn": empty_card_point(),
        "budget": empty_card_point(),
        "persona_detectada": empty_card_point(),
        "sentimento": empty_card_point(),
        "status": DEFAULT_STATUS,
    }


def _strip_code_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text, count=1)
    return text.strip()


def loads_json_object(raw: str | None) -> dict[str, Any] | None:
    """Extrai um objeto JSON de texto que pode vir com fence, preâmbulo ou ruído."""
    if raw is None:
        return None
    text = _strip_code_fence(str(raw))
    if not text:
        return None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
    return data if isinstance(data, dict) else None


def _coerce_str(value: Any, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or default
    return str(value)


def _coerce_evidencias(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    evidencias: list[str] = []
    for item in value:
        text = _coerce_str(item, "")
        if text:
            evidencias.append(text)
    return evidencias


def parse_card_point(raw: Any) -> CardPoint:
    """Aceita CardPoint, dict parcial ou string plana (compatibilidade)."""
    if isinstance(raw, str):
        return empty_card_point(_coerce_str(raw, DEFAULT_VALUE))

    if not isinstance(raw, dict):
        return empty_card_point()

    valor = _coerce_str(raw.get("valor"), DEFAULT_VALUE)
    # Compat: alguns modelos usam "value" em vez de "valor"
    if valor == DEFAULT_VALUE and "value" in raw:
        valor = _coerce_str(raw.get("value"), DEFAULT_VALUE)

    return {
        "valor": valor,
        "analise": _coerce_str(raw.get("analise"), DEFAULT_ANALISE),
        "evidencias": _coerce_evidencias(raw.get("evidencias")),
    }


def parse_intelligence_card(raw: str | dict[str, Any] | None) -> IntelligenceCard:
    """Converte a resposta do LLM (string JSON ou dict) em IntelligenceCard."""
    card = empty_intelligence_card()

    if raw is None:
        return card

    if isinstance(raw, dict):
        data = raw
    else:
        data = loads_json_object(str(raw))
        if data is None:
            return card

    card["conta"] = _coerce_str(data.get("conta"), DEFAULT_VALUE)
    card["status"] = _coerce_str(data.get("status"), DEFAULT_STATUS)

    for field in POINT_FIELDS:
        card[field] = parse_card_point(data.get(field))

    return card
