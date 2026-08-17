"""Carregamento da entrada inicial do sistema a partir de arquivos .csv ou .json."""

import json
import os

SUPPORTED_EXTENSIONS = {".csv", ".json"}


class FileInputError(Exception):
    """Erro ao validar ou ler o arquivo de entrada."""


def parse_file_content(filename: str, content: bytes) -> str:
    """Valida e formata o conteúdo de um arquivo .csv ou .json.

    Recebe o nome do arquivo e seu conteúdo em bytes (por exemplo, vindo de
    um upload HTTP), e retorna o texto usado diretamente como `input` do
    estado do grafo, servindo de contexto para o agente manager e os
    especialistas.
    """
    if not filename:
        raise FileInputError("Informe o nome de um arquivo.")

    extension = os.path.splitext(filename)[1].lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise FileInputError(
            f"Formato não suportado ({extension or 'sem extensão'}). "
            "Use um arquivo .csv ou .json."
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Exportações do Excel/Windows em pt-BR costumam sair em cp1252, não UTF-8.
        try:
            text = content.decode("cp1252")
        except UnicodeDecodeError as exc:
            raise FileInputError(
                f"Não foi possível ler o arquivo como texto UTF-8 ou cp1252: {exc}"
            ) from exc

    if not text.strip():
        raise FileInputError("O arquivo está vazio.")

    if extension == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            raise FileInputError(f"JSON inválido: {exc}") from exc

    basename = os.path.basename(filename)
    formato = extension.lstrip(".")
    return f"Arquivo de entrada: {basename} (formato {formato})\n\n{text}"


def load_file_input(path: str) -> str:
    """Valida e lê um arquivo .csv ou .json em disco, retornando seu conteúdo como texto."""
    if not path:
        raise FileInputError("Informe o caminho de um arquivo.")

    if not os.path.isfile(path):
        raise FileInputError(f"Arquivo não encontrado: {path}")

    try:
        with open(path, "rb") as file:
            content = file.read()
    except OSError as exc:
        raise FileInputError(f"Erro ao ler o arquivo: {exc}") from exc

    return parse_file_content(path, content)
