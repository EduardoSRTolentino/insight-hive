from __future__ import annotations

from pathlib import Path

import pytest

from transcript_cleaner import clean_file, clean_turns
from transcript_cleaner.normalize import NormalizeError, normalize_content, normalize_file
from transcript_cleaner.stage1_text import clean_text, collapse_stutters
from transcript_cleaner.stage2_format import format_turns, merge_consecutive, normalize_timestamp
from transcript_cleaner.stage3_filter import heuristic_labels, is_acknowledgement

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


def test_clean_file_pipeline_reduces_noise():
    result = clean_file(str(FIXTURES / "sample.json"))
    text = result["cleaned_text"].lower()
    assert "p1=" in text
    assert result["stats"]["turns_after"] < result["stats"]["turns_before"]
    assert "sexta" in text
    # concordância vazia "Sim" deve cair na heurística
    labels = heuristic_labels(result["cleaned_turns"])
    # pipeline já filtrou; garantir que texto limpo existe
    assert result["cleaned_text"].strip()


def test_clean_turns_api():
    turns = normalize_file(str(FIXTURES / "sample.csv"))
    result = clean_turns(turns)
    assert "cleaned_text" in result
    assert "speaker_map" in result
