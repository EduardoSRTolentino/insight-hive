from __future__ import annotations

from schemas.intelligence_card import (
    DEFAULT_ANALISE,
    DEFAULT_STATUS,
    DEFAULT_VALUE,
    is_empty_card,
    parse_intelligence_card,
)


def test_empty_input_returns_defaults() -> None:
    card = parse_intelligence_card(None)
    assert card["conta"] == DEFAULT_VALUE
    assert card["status"] == DEFAULT_STATUS
    assert card["oportunidade"]["analise"] == DEFAULT_ANALISE
    assert card["retencao_churn"]["valor"] == DEFAULT_VALUE
    assert card["budget"]["valor"] == DEFAULT_VALUE


def test_is_empty_card_true_for_all_defaults() -> None:
    assert is_empty_card(parse_intelligence_card(None)) is True
    assert is_empty_card(parse_intelligence_card("{not json, truncated")) is True


def test_is_empty_card_false_with_any_real_field() -> None:
    card = parse_intelligence_card({"conta": "Acme"})
    assert is_empty_card(card) is False
    card = parse_intelligence_card({"budget": "Aprovado para 2027"})
    assert is_empty_card(card) is False


def test_strips_markdown_fence() -> None:
    raw = """```json
    {"conta": "Acme", "status": "Pendente revisão humana"}
    ```"""
    card = parse_intelligence_card(raw)
    assert card["conta"] == "Acme"


def test_extracts_partial_json() -> None:
    raw = 'preamble {"conta": "Beta", "sentimento": "Receptivo"} trailing'
    card = parse_intelligence_card(raw)
    assert card["conta"] == "Beta"
    assert card["sentimento"]["valor"] == "Receptivo"


def test_plain_string_point() -> None:
    card = parse_intelligence_card({"oportunidade": "Cross-sell ERP"})
    assert card["oportunidade"]["valor"] == "Cross-sell ERP"
    assert card["oportunidade"]["evidencias"] == []


def test_compat_value_key() -> None:
    card = parse_intelligence_card(
        {"persona_detectada": {"value": "CFO", "analise": "Falou de budget."}}
    )
    assert card["persona_detectada"]["valor"] == "CFO"
    assert card["persona_detectada"]["analise"] == "Falou de budget."
