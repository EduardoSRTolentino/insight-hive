"""Rate limit em memória (um worker). Usado em login e registro."""

from __future__ import annotations

import time
from threading import Lock

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()

    def allow(self, key: str, max_requests: int, window_seconds: float) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            # `.get(key, ())` em vez de indexar um defaultdict: só cria entrada
            # para chaves que de fato fizeram request, então uma chave forjada
            # (ex.: X-Forwarded-For variando a cada tentativa) não infla o dict.
            hits = [stamp for stamp in self._hits.get(key, ()) if stamp > cutoff]
            if len(hits) >= max_requests:
                if hits:
                    self._hits[key] = hits
                else:
                    self._hits.pop(key, None)
                return False
            hits.append(now)
            self._hits[key] = hits
            return True


auth_limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    """IP do cliente para rate limit.

    Só confia em X-Real-IP / X-Forwarded-For quando `TRUST_PROXY_HEADERS=1`
    (ligado no compose de produção, atrás do nginx, que sobrescreve X-Real-IP
    e só *acrescenta* ao X-Forwarded-For — o último hop nunca é o que o
    cliente enviou). Sem isso — dev sem Docker, backend exposto direto — um
    cliente que fala com a API diretamente poderia escolher esses headers
    livremente e contornar o limite por IP.
    """
    from settings import get_settings

    if get_settings().trust_proxy_headers_enabled:
        real_ip = (request.headers.get("x-real-ip") or "").strip()
        if real_ip:
            return real_ip
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            hops = [hop.strip() for hop in forwarded.split(",") if hop.strip()]
            if hops:
                return hops[-1]
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
