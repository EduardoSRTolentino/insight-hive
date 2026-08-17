from __future__ import annotations

import pytest

from ratelimit import client_ip
from settings import get_settings


class _FakeClient:
    def __init__(self, host: str) -> None:
        self.host = host


class _FakeRequest:
    def __init__(self, headers: dict[str, str], host: str = "10.0.0.5") -> None:
        self.headers = headers
        self.client = _FakeClient(host)


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    yield
    get_settings.cache_clear()


def test_client_ip_ignores_forwarded_headers_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    get_settings.cache_clear()
    request = _FakeRequest({"x-forwarded-for": "1.2.3.4", "x-real-ip": "1.2.3.4"})
    assert client_ip(request) == "10.0.0.5"


def test_client_ip_trusts_x_real_ip_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    get_settings.cache_clear()
    request = _FakeRequest({"x-real-ip": "203.0.113.9"})
    assert client_ip(request) == "203.0.113.9"


def test_client_ip_uses_last_xff_hop_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    get_settings.cache_clear()
    # O nginx deste repo só acrescenta ao X-Forwarded-For — o último hop é o
    # que ele registrou, os anteriores podem ter sido forjados pelo cliente.
    request = _FakeRequest({"x-forwarded-for": "9.9.9.9, 203.0.113.9"})
    assert client_ip(request) == "203.0.113.9"


def test_client_ip_falls_back_to_socket_when_headers_missing_even_if_trusted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    get_settings.cache_clear()
    request = _FakeRequest({})
    assert client_ip(request) == "10.0.0.5"
