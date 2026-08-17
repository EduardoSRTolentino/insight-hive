from __future__ import annotations

import re
from pathlib import Path

import pytest

from transcript_cleaner import clean_file, clean_turns
from transcript_cleaner.normalize import NormalizeError, _decode, normalize_content, normalize_file
from transcript_cleaner.stage1_text import clean_text, collapse_stutters
from transcript_cleaner.stage2_format import format_turns, merge_consecutive, normalize_timestamp
from transcript_cleaner.stage3_filter import (
    heuristic_labels,
    is_acknowledgement,
    is_greeting_or_farewell,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalize_json_sample():
    turns = normalize_file(str(FIXTURES / "sample.json"))
    assert len(turns) == 8
    assert turns[0]["speaker"] == "João Silva"
    assert turns[0]["id"] == "0"


def test_normalize_csv_sample():
    turns = normalize_file(str(FIXTURES / "sample.csv"))
    assert len(turns) == 6
    assert turns[2]["text"].startswith("Hum")


def test_normalize_json_segments_envelope():
    payload = '{"segments":[{"falante":"A","texto":"Olá mundo"}]}'
    turns = normalize_content(payload, format="json")
    assert turns[0]["speaker"] == "A"
    assert turns[0]["text"] == "Olá mundo"


def test_normalize_requires_text():
    with pytest.raises(NormalizeError):
        normalize_content('[{"speaker":"A"}]', format="json")


def test_stage1_fillers_and_stutter():
    text = clean_text("Hum, tipo, nós nós vamos")
    assert "hum" not in text.lower()
    assert "tipo" not in text.lower()
    assert "nós nós" not in text.lower()
    assert "vamos" in text.lower()


def test_collapse_bigram():
    assert collapse_stutters("a gente a gente vai") == "a gente vai"


def test_timestamp_and_merge():
    assert normalize_timestamp("00:01:02.500") == "00:01:02"


def test_normalize_timestamp_pathological_value_does_not_raise():
    # "T" sozinho já derrubou o parser com IndexError; agora só devolve o raw.
    assert normalize_timestamp("T") == "T"
    turns = [
        {"id": "0", "speaker": "A", "text": "um", "start": "00:00:01", "end": None},
        {"id": "1", "speaker": "A", "text": "dois", "start": "00:00:02", "end": "00:00:03"},
        {"id": "2", "speaker": "B", "text": "três", "start": "00:00:04", "end": None},
    ]
    merged = merge_consecutive(turns)
    assert len(merged) == 2
    assert merged[0]["text"] == "um dois"


def test_format_speaker_map():
    turns = [
        {"id": "0", "speaker": "João Silva", "text": "olá", "start": None, "end": None},
        {"id": "1", "speaker": "Maria", "text": "oi", "start": None, "end": None},
    ]
    short, mapping, text = format_turns(turns)
    assert mapping["P1"] == "João Silva"
    assert short[0]["speaker"] == "P1"
    assert "# Speakers" in text
    assert "[P1]" in text


def test_acknowledgement_heuristic():
    assert is_acknowledgement("Sim")
    assert is_acknowledgement("Com certeza")
    assert not is_acknowledgement("Sim, vamos adiar o prazo para segunda")


def test_acknowledgement_after_question_is_kept():
    # "Sim"/"Não" respondendo a uma pergunta é decisão/atribuição, não concordância
    # vazia — não deve ser descartado.
    assert not is_acknowledgement("Sim", preceded_by_question=True)
    assert not is_acknowledgement("Não", preceded_by_question=True)
    turns = [
        {
            "id": "0",
            "speaker": "A",
            "text": "Bruno, você assume a integração?",
            "start": None,
            "end": None,
        },
        {"id": "1", "speaker": "B", "text": "Sim", "start": None, "end": None},
        {
            "id": "2",
            "speaker": "A",
            "text": "Alguém mais tem bloqueio?",
            "start": None,
            "end": None,
        },
        {"id": "3", "speaker": "B", "text": "Não", "start": None, "end": None},
        {"id": "4", "speaker": "A", "text": "Ok, seguimos então", "start": None, "end": None},
    ]
    labels, _overrides = heuristic_labels(turns)
    assert labels.get("1") != "DROP"
    assert labels.get("3") != "DROP"


def test_greeting_does_not_match_substring_inside_word():
    # "oi" e "ola" são saudações, mas não devem casar dentro de "dois"/"depois"/
    # "escola" — regressão do filtro que descartava conteúdo de negócio nas bordas.
    assert not is_greeting_or_farewell("dois milhões no orçamento")
    assert not is_greeting_or_farewell("depois a gente fecha o contrato")
    assert not is_greeting_or_farewell("na escola do cliente")
    assert not is_greeting_or_farewell("vamos controlar o escopo")
    # saudações de verdade continuam sendo pegas
    assert is_greeting_or_farewell("oi, tudo bem?")
    assert is_greeting_or_farewell("tchau pessoal")


def test_greeting_does_not_drop_long_substantive_turn():
    # Turno longo que só começa com uma cortesia não deve ser tratado como
    # small talk inteiro.
    long_turn = (
        "bom dia pessoal, hoje vamos revisar o contrato de dois milhões que "
        "fechamos semana passada e confirmar o cronograma de entrega"
    )
    assert not is_greeting_or_farewell(long_turn)


def test_edge_greeting_with_substantive_content_is_trimmed_not_dropped():
    turns = [
        {
            "id": "0",
            "speaker": "A",
            "text": "oi, dois milhões no orçamento deste trimestre",
            "start": None,
            "end": None,
        },
        {"id": "1", "speaker": "B", "text": "entendido", "start": None, "end": None},
    ]
    labels, overrides = heuristic_labels(turns)
    assert labels.get("0") != "DROP"
    assert "milhões" in overrides["0"]
    assert "oi" not in re.findall(r"\w+", overrides["0"].lower())


def test_decode_falls_back_to_cp1252():
    raw = "Reunião com acentuação".encode("cp1252")
    assert _decode(raw) == "Reunião com acentuação"


def test_clean_turns_raises_when_everything_is_filtered():
    turns = [
        {"id": "0", "speaker": "A", "text": "oi", "start": None, "end": None},
        {"id": "1", "speaker": "B", "text": "tudo bem", "start": None, "end": None},
        {"id": "2", "speaker": "A", "text": "tchau", "start": None, "end": None},
    ]
    with pytest.raises(NormalizeError):
        clean_turns(turns)


def test_clean_file_pipeline_reduces_noise():
    result = clean_file(str(FIXTURES / "sample.json"))
    text = result["cleaned_text"].lower()
    assert "p1=" in text
    assert result["stats"]["turns_after"] < result["stats"]["turns_before"]
    assert "sexta" in text
    assert result["cleaned_text"].strip()


def test_clean_file_keeps_decision_answers_from_meeting_fixture():
    # Fixture rica: "Sim"/"Não" respondem a perguntas de atribuição de ação e
    # não podem desaparecer; "dois milhões" não deveria existir aqui, mas o
    # combinado de prazo e responsável precisa sobreviver à limpeza.
    result = clean_file(str(FIXTURES / "meeting.json"))
    text = result["cleaned_text"]
    assert "você assume a integração" in text
    assert "Sim" in text  # resposta de Bruno, mesclada ao turno seguinte dele
    assert "Não" in text  # resposta de Carla ao "alguém mais tem bloqueio?"
    assert "sexta" in text
    assert "churn" in text
    # small talk de borda (saudações, "Uhum", "Beleza", "Entendi", "Certo",
    # "Tchau, falou") deve ter sido descartado
    assert result["stats"]["turns_after"] < result["stats"]["turns_before"]


def test_clean_turns_api():
    turns = normalize_file(str(FIXTURES / "sample.csv"))
    result = clean_turns(turns)
    assert "cleaned_text" in result
    assert "speaker_map" in result
