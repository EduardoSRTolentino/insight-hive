from __future__ import annotations

import pytest

from file_input import FileInputError, parse_file_content


def test_rejects_missing_filename() -> None:
    with pytest.raises(FileInputError, match="nome"):
        parse_file_content("", b"a,b")


def test_rejects_unsupported_extension() -> None:
    with pytest.raises(FileInputError, match="não suportado"):
        parse_file_content("notes.txt", b"hello")


def test_rejects_empty_file() -> None:
    with pytest.raises(FileInputError, match="vazio"):
        parse_file_content("data.csv", b"   \n")


def test_rejects_invalid_json() -> None:
    with pytest.raises(FileInputError, match="JSON inválido"):
        parse_file_content("data.json", b"{not json")


def test_parses_csv() -> None:
    text = parse_file_content("reuniao.csv", b"speaker,text\nA,ola")
    assert "reuniao.csv" in text
    assert "formato csv" in text
    assert "speaker,text" in text


def test_parses_json() -> None:
    text = parse_file_content("meeting.json", b'[{"speaker":"A","text":"oi"}]')
    assert "meeting.json" in text
    assert "formato json" in text


def test_utf8_sig() -> None:
    content = "\ufeff".encode("utf-8") + b'{"ok": true}'
    text = parse_file_content("bom.json", content)
    assert '{"ok": true}' in text
