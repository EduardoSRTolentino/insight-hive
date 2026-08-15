"""Carrega o catálogo JSON e localiza produtos citados num texto de reunião."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from catalog.models import Product

DATA_DIR = Path(__file__).resolve().parent / "data"
JSON_PATH = DATA_DIR / "produtos_totvs.json"

MAX_HITS = 8
MAX_HIT_DESCRIPTION = 160
MAX_HITS_CHARS = 1200
MAX_GAZETTEER_CHARS = 3500

_FALLBACK_GAZETTEER = (
    "Gestão: ERP, Fluig, RM, Protheus, Datasul, Logix, iPaaS, Cloud, RH, Fiscal\n"
    "Techfin: crédito B2B, antecipação de recebíveis, pagamentos\n"
    "Business Performance: RD Station, CRM, Digital Commerce"
)


class CatalogIndex:
    """Índice de aliases → produto, aliases longos primeiro."""

    def __init__(self, products: list[Product]) -> None:
        self.products = products
        self._patterns: list[tuple[re.Pattern[str], Product]] = []
        ranked: list[tuple[str, Product]] = []
        for product in products:
            aliases = product.aliases or [product.name]
            for alias in aliases:
                cleaned = alias.strip()
                if len(cleaned) < 2:
                    continue
                ranked.append((cleaned, product))
        ranked.sort(key=lambda item: len(item[0]), reverse=True)
        seen_alias: set[str] = set()
        for alias, product in ranked:
            key = alias.casefold()
            if key in seen_alias:
                continue
            seen_alias.add(key)
            pattern = re.compile(
                rf"(?<!\w){re.escape(alias)}(?!\w)",
                re.IGNORECASE,
            )
            self._patterns.append((pattern, product))

    def match(self, text: str, limit: int = MAX_HITS) -> list[Product]:
        if not text or not text.strip():
            return []
        hits: list[tuple[int, Product]] = []
        seen_slugs: set[str] = set()
        for pattern, product in self._patterns:
            slug = product.slug or product.name
            if slug in seen_slugs:
                continue
            found = pattern.search(text)
            if found is None:
                continue
            seen_slugs.add(slug)
            hits.append((found.start(), product))
        hits.sort(key=lambda item: item[0])
        return [product for _, product in hits[:limit]]


@lru_cache(maxsize=1)
def load_products() -> tuple[Product, ...]:
    if not JSON_PATH.is_file():
        return tuple()
    try:
        payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return tuple()
    if not isinstance(payload, list):
        return tuple()
    products = []
    for item in payload:
        if isinstance(item, dict):
            products.append(Product.from_json(item))
    return tuple(products)


@lru_cache(maxsize=1)
def _index() -> CatalogIndex:
    return CatalogIndex(list(load_products()))


def match(text: str, limit: int = MAX_HITS) -> list[Product]:
    return _index().match(text, limit=limit)


def format_hits_for_prompt(hits: list[Product]) -> str:
    """Bloco injetado no user_content do especialista Ecossistema TOTVS."""
    if not hits:
        return (
            "Catálogo TOTVS: nenhum produto identificado automaticamente no "
            "texto. Não invente produtos fora do gazetteer do system prompt. "
            "Se nada se aplicar, use products_mentioned []."
        )

    lines = ["Catálogo TOTVS relevante à reunião:"]
    used = len(lines[0])
    for product in hits:
        description = (product.description or "").strip()
        if len(description) > MAX_HIT_DESCRIPTION:
            description = description[: MAX_HIT_DESCRIPTION - 1].rstrip() + "…"
        category = product.category or product.parent_slug or "—"
        line = f"- {product.name} ({product.pillar} / {category})"
        if description:
            line += f": {description}"
        if used + len(line) + 1 > MAX_HITS_CHARS:
            break
        lines.append(line)
        used += len(line) + 1
    lines.append(
        "Use estes nomes canônicos em products_mentioned. Não invente "
        "produtos fora desta lista e do gazetteer."
    )
    return "\n".join(lines)


def build_gazetteer(max_chars: int = MAX_GAZETTEER_CHARS) -> str:
    """Lista compacta de nomes canônicos agrupados por pilar.

    Famílias (nós que têm filhos) e linhas ERP entram primeiro, para o
    recorte de 2–4 KB não ficar só em produtos parceiros órfãos.
    """
    products = list(load_products())
    if not products:
        return _FALLBACK_GAZETTEER

    family_slugs = {item.parent_slug for item in products if item.parent_slug}

    def priority(item: Product) -> tuple[int, str]:
        if item.slug in family_slugs:
            return (0, item.name.lower())
        if not item.parent_slug:
            return (1, item.name.lower())
        return (2, item.name.lower())

    grouped: dict[str, list[str]] = {}
    seen: set[str] = set()
    for product in sorted(products, key=priority):
        name = product.name.strip()
        key = name.casefold()
        if not name or key in seen:
            continue
        seen.add(key)
        grouped.setdefault(product.pillar or "Gestão", []).append(name)

    pillar_order = ("Gestão", "Techfin", "Business Performance")
    chunks: list[str] = []
    used = 0
    for pillar in pillar_order:
        names = grouped.get(pillar) or []
        if not names:
            continue
        header = f"{pillar}: "
        body = ", ".join(names)
        chunk = header + body
        if used + len(chunk) + 1 > max_chars:
            remaining = max_chars - used - len(header) - 1
            if remaining > 20:
                chunks.append(header + body[:remaining].rstrip(", ") + "…")
            break
        chunks.append(chunk)
        used += len(chunk) + 1
    return "\n".join(chunks) if chunks else _FALLBACK_GAZETTEER
