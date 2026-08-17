"""Etapa 2 — compactação de metadados, merge e serialização."""

from __future__ import annotations

import re
from typing import Iterable

from .models import Turn

_TS_RE = re.compile(
    r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:[.,](\d{1,3}))?$"
)


def normalize_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    match = _TS_RE.match(raw)
    if not match:
        # tenta ISO-like ...T12:34:56
        tail = raw[-12:]
        parts = tail.replace("T", " ").split()
        match = _TS_RE.search(parts[-1]) if parts else None
        if not match:
            return raw
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def build_speaker_map(speakers: Iterable[str]) -> dict[str, str]:
    """Retorna mapa short_id -> nome original, estável por ordem de aparição."""
    mapping: dict[str, str] = {}
    seen: dict[str, str] = {}
    counter = 1
    for speaker in speakers:
        key = speaker.strip() or "UNKNOWN"
        if key not in seen:
            short = f"P{counter}"
            seen[key] = short
            mapping[short] = key
            counter += 1
    return mapping


def invert_speaker_map(speaker_map: dict[str, str]) -> dict[str, str]:
    return {name: short for short, name in speaker_map.items()}


def merge_consecutive(turns: list[Turn]) -> list[Turn]:
    if not turns:
        return []
    merged: list[Turn] = []
    current = dict(turns[0])
    for turn in turns[1:]:
        if turn["speaker"] == current["speaker"]:
            current["text"] = f'{current["text"]} {turn["text"]}'.strip()
            if turn["end"]:
                current["end"] = turn["end"]
        else:
            merged.append(current)  # type: ignore[arg-type]
            current = dict(turn)
    merged.append(current)  # type: ignore[arg-type]
    # reindex ids após merge
    for index, turn in enumerate(merged):
        turn["id"] = str(index)
        turn["start"] = normalize_timestamp(turn.get("start"))
        turn["end"] = normalize_timestamp(turn.get("end"))
    return merged  # type: ignore[return-value]


def apply_short_speakers(turns: list[Turn], speaker_map: dict[str, str]) -> list[Turn]:
    inverse = invert_speaker_map(speaker_map)
    result: list[Turn] = []
    for turn in turns:
        short = inverse.get(turn["speaker"], turn["speaker"])
        result.append({**turn, "speaker": short})
    return result


def serialize_turns(turns: list[Turn], speaker_map: dict[str, str]) -> str:
    lines: list[str] = ["# Speakers"]
    for short, name in speaker_map.items():
        lines.append(f"{short}={name}")
    lines.append("")
    for turn in turns:
        stamp = f" {turn['start']}" if turn.get("start") else ""
        lines.append(f"[{turn['speaker']}]{stamp} {turn['text']}".rstrip())
    return "\n".join(lines).strip() + "\n"


def format_turns(turns: list[Turn]) -> tuple[list[Turn], dict[str, str], str]:
    speaker_map = build_speaker_map(t["speaker"] for t in turns)
    merged = merge_consecutive(turns)
    short = apply_short_speakers(merged, speaker_map)
    text = serialize_turns(short, speaker_map)
    return short, speaker_map, text
