"""Limite de tamanho do upload sem bufferizar o arquivo inteiro antes da checagem."""

from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

# Envelope multipart (boundary + client_id) além do arquivo em si.
MULTIPART_OVERHEAD_BYTES = 16_384
_CHUNK_SIZE = 64 * 1024


def upload_too_large_detail(max_bytes: int) -> str:
    return f"Arquivo excede o limite de {max_bytes} bytes."


def content_length_exceeds(header_value: str | None, max_bytes: int) -> bool:
    if not header_value:
        return False
    try:
        length = int(header_value)
    except ValueError:
        return False
    return length > max_bytes + MULTIPART_OVERHEAD_BYTES


def raise_upload_too_large(max_bytes: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=upload_too_large_detail(max_bytes),
    )


def read_upload_capped(upload: UploadFile, max_bytes: int) -> bytes:
    """Lê o arquivo em chunks e aborta no primeiro byte além do teto."""
    declared = getattr(upload, "size", None)
    if isinstance(declared, int) and declared > max_bytes:
        raise_upload_too_large(max_bytes)

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = upload.file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise_upload_too_large(max_bytes)
        chunks.append(chunk)
    return b"".join(chunks)
