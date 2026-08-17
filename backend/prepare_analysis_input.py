"""Cola no entrypoint: limpa transcrições antes do grafo, sem o grafo conhecer o cleaner.

Único módulo do backend que importa `transcript_cleaner`. Em qualquer falha de
detecção (pacote ausente, flag desligada, CSV/JSON sem campo de fala) devolve o
texto bruto de `file_input`, que continua o parser genérico.
"""

from __future__ import annotations

import logging
import os

from file_input import SUPPORTED_EXTENSIONS, FileInputError, load_file_input, parse_file_content
from settings import get_settings

logger = logging.getLogger(__name__)


def _has_supported_extension(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in SUPPORTED_EXTENSIONS


def _transcript_clean_enabled() -> bool:
    return get_settings().transcript_clean_enabled


def _wrap_cleaned(filename: str, cleaned_text: str) -> str:
    basename = os.path.basename(filename)
    formato = os.path.splitext(filename)[1].lower().lstrip(".")
    return (
        f"Arquivo de entrada: {basename} (formato {formato}, transcrição limpa)\n\n"
        f"{cleaned_text}"
    )


def _clean_or_none(source: str | bytes, filename: str) -> str | None:
    try:
        from transcript_cleaner import NormalizeError, clean_file
    except ImportError:
        logger.info("transcript_cleaner não instalado; usando texto bruto.")
        return None

    ext = os.path.splitext(filename)[1].lower().lstrip(".") or None
    try:
        result = clean_file(source, filename=filename, format=ext, llm_client=None)
    except NormalizeError:
        return None
    except Exception as exc:
        raise FileInputError(f"Falha ao limpar a transcrição: {exc}") from exc

    stats = result.get("stats") or {}
    logger.info(
        "Transcrição limpa: %s (%s → %s turnos)",
        os.path.basename(filename),
        stats.get("turns_before"),
        stats.get("turns_after"),
    )
    return _wrap_cleaned(filename, result["cleaned_text"])


def prepare_graph_input(filename: str, content: bytes) -> str:
    """Monta o `input` do grafo a partir de um upload (bytes)."""
    if not filename or not _transcript_clean_enabled() or not _has_supported_extension(filename):
        # Extensão fora da allowlist (ou sem extensão): não deixa o cleaner
        # sniffar o conteúdo e aceitar algo que `parse_file_content` recusaria.
        return parse_file_content(filename, content)

    cleaned = _clean_or_none(source=content, filename=filename)
    if cleaned is None:
        return parse_file_content(filename, content)
    return cleaned


def prepare_graph_input_from_path(path: str) -> str:
    """Monta o `input` do grafo a partir de um arquivo em disco."""
    if not path or not _transcript_clean_enabled() or not _has_supported_extension(path):
        return load_file_input(path)

    cleaned = _clean_or_none(source=path, filename=path)
    if cleaned is None:
        return load_file_input(path)
    return cleaned
