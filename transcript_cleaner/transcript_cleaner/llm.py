"""Porta abstrata de LLM — implementada pelo caller, nunca acoplada a Ollama/LangChain."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LlmClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Retorna texto bruto do modelo (JSON nas etapas 3–4)."""
        ...
