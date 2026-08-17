"""Normalização JSON/CSV → Turn[]."""

from __future__ import annotations

import csv
import io
import json
import os
from typing import Any

from .models import Turn

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "speaker": ("speaker", "falante", "nome", "participant"),
    "text": ("text", "texto", "content", "fala", "transcript"),
    "start": ("start", "inicio", "timestamp", "start_time"),
    "end": ("end", "fim", "end_time"),
}

SEGMENT_KEYS = ("segments", "turns", "utterances")


class NormalizeError(ValueError):
    """Entrada inválida ou incompleta para normalização."""


def _decode(content: bytes | str) -> str:
    if isinstance(content, str):
        return content
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    # Exportações do Excel/Windows em pt-BR costumam sair em cp1252, não UTF-8.
    try:
        return content.decode("cp1252")
    except UnicodeDecodeError as exc:
        raise NormalizeError(f"Não foi possível ler como UTF-8 ou cp1252: {exc}") from exc


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _build_header_map(headers: list[str]) -> dict[str, str]:
    normalized = {_normalize_key(h): h for h in headers}
    mapping: dict[str, str] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[canonical] = normalized[alias]
                break
    if "text" not in mapping:
        raise NormalizeError(
            "Campo de texto obrigatório não encontrado. "
            f"Aliases aceitos: {', '.join(FIELD_ALIASES['text'])}."
        )
    return mapping


def _cell(row: dict[str, Any], header_map: dict[str, str], field: str) -> str | None:
    source_key = header_map.get(field)
    if not source_key:
        return None
    value = row.get(source_key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _rows_to_turns(rows: list[dict[str, Any]], header_map: dict[str, str]) -> list[Turn]:
    turns: list[Turn] = []
    for index, row in enumerate(rows):
        text = _cell(row, header_map, "text")
        if not text:
            continue
        speaker = _cell(row, header_map, "speaker") or "UNKNOWN"
        turns.append(
            {
                "id": str(index),
                "speaker": speaker,
                "text": text,
                "start": _cell(row, header_map, "start"),
                "end": _cell(row, header_map, "end"),
            }
        )
    if not turns:
        raise NormalizeError("Nenhum turno com texto válido encontrado.")
    return turns


def _extract_json_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        if not payload:
            raise NormalizeError("JSON array vazio.")
        if not all(isinstance(item, dict) for item in payload):
            raise NormalizeError("JSON array deve conter objetos.")
        return payload  # type: ignore[return-value]

    if isinstance(payload, dict):
        for key in SEGMENT_KEYS:
            value = payload.get(key)
            if isinstance(value, list):
                return _extract_json_rows(value)
        # objeto único com campos de turno
        if any(_normalize_key(k) in FIELD_ALIASES["text"] for k in payload):
            return [payload]
        raise NormalizeError(
            "JSON objeto deve ter 'segments'/'turns'/'utterances' ou campos de turno."
        )

    raise NormalizeError("JSON deve ser um array ou objeto.")


def parse_json_text(text: str) -> list[Turn]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise NormalizeError(f"JSON inválido: {exc}") from exc

    rows = _extract_json_rows(payload)
    # unificar chaves do primeiro objeto como "headers"
    keys = list(rows[0].keys())
    header_map = _build_header_map(keys)
    # remapear aliases de cada row para as chaves originais do header_map
    return _rows_to_turns(rows, header_map)


def parse_csv_text(text: str) -> list[Turn]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise NormalizeError("CSV sem cabeçalho.")
    header_map = _build_header_map(list(reader.fieldnames))
    rows = [dict(row) for row in reader]
    return _rows_to_turns(rows, header_map)


def infer_format(filename: str | None, text: str, explicit: str | None) -> str:
    if explicit:
        fmt = explicit.lower().lstrip(".")
        if fmt not in {"json", "csv"}:
            raise NormalizeError(f"Formato não suportado: {explicit}")
        return fmt

    if filename:
        ext = os.path.splitext(filename)[1].lower().lstrip(".")
        if ext in {"json", "csv"}:
            return ext

    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    return "csv"


def normalize_content(
    content: bytes | str,
    *,
    filename: str | None = None,
    format: str | None = None,
) -> list[Turn]:
    text = _decode(content)
    if not text.strip():
        raise NormalizeError("Conteúdo vazio.")
    fmt = infer_format(filename, text, format)
    if fmt == "json":
        return parse_json_text(text)
    return parse_csv_text(text)


def normalize_file(path: str, *, format: str | None = None) -> list[Turn]:
    if not path:
        raise NormalizeError("Informe o caminho de um arquivo.")
    if not os.path.isfile(path):
        raise NormalizeError(f"Arquivo não encontrado: {path}")
    with open(path, "rb") as handle:
        content = handle.read()
    return normalize_content(content, filename=path, format=format)
