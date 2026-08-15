"""Cliente HTTP com User-Agent moderno, retries e checagem de status."""

from __future__ import annotations

import time
from typing import Any, Optional

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.5
REQUEST_DELAY_SECONDS = 0.4

_SESSION: Optional[requests.Session] = None


class HttpError(Exception):
    """Falha de conexão ou resposta HTTP diferente de 200."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        _SESSION = session
    return _SESSION


def get(url: str, params: Optional[dict[str, Any]] = None) -> requests.Response:
    """GET com retry. Levanta HttpError se o status final não for 200."""
    last_error: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _session().get(url, params=params, timeout=DEFAULT_TIMEOUT)
            if response.status_code == 200:
                if REQUEST_DELAY_SECONDS:
                    time.sleep(REQUEST_DELAY_SECONDS)
                return response
            last_error = HttpError(
                f"GET {url} retornou HTTP {response.status_code}",
                status_code=response.status_code,
            )
            if response.status_code in {429, 500, 502, 503, 504} and attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            raise last_error
        except requests.RequestException as exc:
            last_error = HttpError(f"Falha de conexão em {url}: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            raise last_error from exc
    raise last_error or HttpError(f"GET {url} falhou")
