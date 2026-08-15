"""Registro canônico de um produto/solução do catálogo TOTVS."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Product:
    name: str
    slug: str
    category: str
    pillar: str
    description: str
    url: str
    aliases: list[str] = field(default_factory=list)
    parent_slug: str = ""
    id: int = 0
    parent_id: int = 0

    def to_csv_row(self) -> dict[str, str]:
        return {
            "name": self.name,
            "slug": self.slug,
            "category": self.category,
            "pillar": self.pillar,
            "description": self.description,
            "url": self.url,
            "aliases": "|".join(self.aliases),
            "parent_slug": self.parent_slug,
        }

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> Product:
        aliases = payload.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [part for part in aliases.split("|") if part]
        return cls(
            name=str(payload.get("name") or ""),
            slug=str(payload.get("slug") or ""),
            category=str(payload.get("category") or ""),
            pillar=str(payload.get("pillar") or ""),
            description=str(payload.get("description") or ""),
            url=str(payload.get("url") or ""),
            aliases=[str(alias) for alias in aliases],
            parent_slug=str(payload.get("parent_slug") or ""),
            id=int(payload.get("id") or 0),
            parent_id=int(payload.get("parent_id") or 0),
        )
