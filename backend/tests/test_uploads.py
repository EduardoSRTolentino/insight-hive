from __future__ import annotations

import io

import pytest
from fastapi import HTTPException, UploadFile

from uploads import content_length_exceeds, read_upload_capped, upload_too_large_detail


def test_content_length_exceeds_accounts_for_multipart_overhead() -> None:
    assert content_length_exceeds(None, 2048) is False
    assert content_length_exceeds("3000", 2048) is False
    assert content_length_exceeds("25000", 2048) is True
    assert content_length_exceeds("nope", 2048) is False


def test_read_upload_capped_rejects_declared_size() -> None:
    upload = UploadFile(file=io.BytesIO(b"abc"), size=3000, filename="huge.json")
    with pytest.raises(HTTPException) as exc:
        read_upload_capped(upload, 2048)
    assert exc.value.status_code == 413
    assert exc.value.detail == upload_too_large_detail(2048)


def test_read_upload_capped_rejects_stream_over_limit() -> None:
    payload = b"x" * 3000
    upload = UploadFile(file=io.BytesIO(payload), size=None, filename="huge.json")
    with pytest.raises(HTTPException) as exc:
        read_upload_capped(upload, 2048)
    assert exc.value.status_code == 413


def test_read_upload_capped_returns_bytes_under_limit() -> None:
    upload = UploadFile(file=io.BytesIO(b'{"ok":true}'), filename="ok.json")
    assert read_upload_capped(upload, 2048) == b'{"ok":true}'
