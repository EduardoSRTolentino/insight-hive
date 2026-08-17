"""Rate limit em memória (um worker). Usado em login e registro."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()

    def allow(self, key: str, max_requests: int, window_seconds: float) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            hits = [stamp for stamp in self._hits[key] if stamp > cutoff]
            if len(hits) >= max_requests:
                self._hits[key] = hits
                return False
            hits.append(now)
            self._hits[key] = hits
            return True


auth_limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"


def enforce_auth_rate_limit(request: Request) -> None:
    from settings import get_settings

    settings = get_settings()
    if settings.auth_rate_limit <= 0:
        return
    if auth_limiter.allow(
        client_ip(request),
        settings.auth_rate_limit,
        settings.auth_rate_window_seconds,
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Muitas tentativas. Aguarde um minuto e tente de novo.",
        headers={"Retry-After": str(settings.auth_rate_window_seconds)},
    )
