"""Normalização e validação simples de e-mail."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    return value.strip().casefold()


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL_RE.fullmatch(normalize_email(value)))
