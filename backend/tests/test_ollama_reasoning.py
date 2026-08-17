from __future__ import annotations

from unittest.mock import MagicMock

from agents.base import (
    _chat_ollama_kwargs,
    _thinking_override,
    effective_reasoning,
    get_llm,
    mark_thinking_unsupported,
    model_supports_thinking,
)


def _reset_llm_caches() -> None:
    _thinking_override.clear()
    model_supports_thinking.cache_clear()
    get_llm.cache_clear()


def test_effective_reasoning_skips_when_model_cannot_think() -> None:
    assert effective_reasoning("low", supports_thinking=False) is None
    assert effective_reasoning("low", supports_thinking=True) == "low"
    assert effective_reasoning("off", supports_thinking=True) is None
    assert effective_reasoning("", supports_thinking=True) is None


def test_model_supports_thinking_reads_capabilities(monkeypatch) -> None:
    _reset_llm_caches()
    payload = {
        "models": [
            {"name": "qwen2.5:3b", "capabilities": ["completion", "tools"]},
            {"name": "gpt-oss:20b", "capabilities": ["completion", "thinking"]},
        ]
    }
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    monkeypatch.setattr("agents.base.httpx.Client", lambda **_kwargs: client)

    assert model_supports_thinking("qwen2.5:3b", "http://ollama") is False
    _reset_llm_caches()
    assert model_supports_thinking("gpt-oss:20b", "http://ollama") is True
    _reset_llm_caches()


def test_chat_kwargs_omit_reasoning_for_qwen(monkeypatch) -> None:
    _reset_llm_caches()
    monkeypatch.setattr("agents.base.model_supports_thinking", lambda *_args: False)
    kwargs = _chat_ollama_kwargs()
    assert "reasoning" not in kwargs
    _reset_llm_caches()


def test_chat_kwargs_include_client_timeout(monkeypatch) -> None:
    # Sem isso o httpx do client Ollama fica sem teto (timeout=None) e uma
    # geração travada prende a thread do worker para sempre.
    _reset_llm_caches()
    monkeypatch.setattr("agents.base.model_supports_thinking", lambda *_args: False)
    kwargs = _chat_ollama_kwargs()
    assert kwargs["client_kwargs"] == {"timeout": 180}
    _reset_llm_caches()


def test_mark_thinking_unsupported_disables_reasoning(monkeypatch) -> None:
    _reset_llm_caches()
    monkeypatch.setattr(
        "agents.base.get_settings",
        lambda: MagicMock(ollama_model="qwen2.5:3b", ollama_base_url="http://ollama"),
    )
    mark_thinking_unsupported()
    assert model_supports_thinking("qwen2.5:3b", "http://ollama") is False
    _reset_llm_caches()
