from __future__ import annotations

import pytest

from settings import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    yield
    get_settings.cache_clear()


def test_ollama_timeout_seconds_is_clamped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "1")
    get_settings.cache_clear()
    assert get_settings().ollama_timeout_seconds == 30

    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "999999")
    get_settings.cache_clear()
    assert get_settings().ollama_timeout_seconds == 900


def test_trust_proxy_headers_enabled_parses_truthy_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for value in ("1", "true", "True", "on", "yes"):
        monkeypatch.setenv("TRUST_PROXY_HEADERS", value)
        get_settings.cache_clear()
        assert get_settings().trust_proxy_headers_enabled is True

    for value in ("", "0", "false", "off"):
        monkeypatch.setenv("TRUST_PROXY_HEADERS", value)
        get_settings.cache_clear()
        assert get_settings().trust_proxy_headers_enabled is False
