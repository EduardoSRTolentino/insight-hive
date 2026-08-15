"""Leitura da taxonomia WordPress `produto` em produtos.totvs.com."""

from __future__ import annotations

import html
import re
from typing import Any, Optional

from catalog.models import Product
from catalog.scrape.client import HttpError, get
from catalog.scrape.pillars import (
    CANONICAL_LINE_SLUGS,
    EXTRA_ALIASES_BY_SLUG,
    KNOWN_LINE_ALIASES,
    ancestor_chain,
    pillar_for_slugs,
)

WP_PRODUTO_URL = "https://produtos.totvs.com/wp-json/wp/v2/produto"
PER_PAGE = 100
_FIELDS = "id,name,slug,parent,count,description,link"

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_TOTVS_PREFIX_RE = re.compile(r"^TOTVS\s+", re.IGNORECASE)

# Aliases curtos demais ou genéricos demais para matching automático.
_SKIP_ALIASES = frozenset(
    {
        "totvs",
        "produto",
        "produtos",
        "sistema",
        "solucao",
        "solução",
        "servicos",
        "serviços",
        "by",
        "de",
        "da",
        "do",
        "e",
    }
)
_LINE_SUFFIXES = frozenset(
    {
        "linha protheus",
        "linha datasul",
        "linha rm",
        "linha logix",
        "linha protheus latam",
    }
)
_GENERIC_NAME_PARTS = frozenset({"backoffice", "totvs backoffice"})
GENERIC_DESCRIPTION_MARKERS = (
    "atualizações e informações completas sobre o portfólio da totvs",
    "receba as novidades dos nossos produtos",
    "conheça as próximas entregas previstas",
)


def fetch_all_terms() -> list[dict[str, Any]]:
    """Pagina a API até esgotar `X-WP-TotalPages` ou uma página vazia."""
    terms: list[dict[str, Any]] = []
    page = 1
    while True:
        try:
            response = get(
                WP_PRODUTO_URL,
                params={
                    "per_page": PER_PAGE,
                    "page": page,
                    "_fields": _FIELDS,
                },
            )
        except HttpError as exc:
            # WordPress devolve 400 quando a página passa do total.
            if exc.status_code in {400, 404} and page > 1:
                break
            raise
        payload = response.json()
        if not isinstance(payload, list) or not payload:
            break
        terms.extend(payload)
        total_pages = _header_int(response.headers.get("X-WP-TotalPages"))
        if total_pages is not None and page >= total_pages:
            break
        if len(payload) < PER_PAGE:
            break
        page += 1
    return terms


def assemble_products(terms: list[dict[str, Any]]) -> list[Product]:
    """Converte termos WP em produtos, com pilar, categoria e aliases."""
    by_id: dict[int, dict[str, Any]] = {}
    for term in terms:
        try:
            term_id = int(term.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if term_id:
            by_id[term_id] = term

    products: list[Product] = []
    for term in terms:
        product = _term_to_product(term, by_id)
        if product is not None:
            products.append(product)
    products.sort(key=lambda item: (item.pillar, item.category, item.name.lower()))
    return products


def strip_html(value: str) -> str:
    text = _HTML_TAG_RE.sub(" ", value or "")
    text = html.unescape(text).replace("\xa0", " ")
    return _WHITESPACE_RE.sub(" ", text).strip()


def is_generic_description(value: str) -> bool:
    normalized = (value or "").casefold()
    if not normalized:
        return True
    return any(marker in normalized for marker in GENERIC_DESCRIPTION_MARKERS)


def derive_aliases(name: str, slug: str) -> list[str]:
    """Gera aliases de matching: nome sem TOTVS, linha canônica e slug."""
    aliases: list[str] = []
    seen: set[str] = set()

    def add(candidate: str) -> None:
        cleaned = _WHITESPACE_RE.sub(" ", candidate).strip(" -–|/")
        if not cleaned:
            return
        key = cleaned.casefold()
        if key in seen or key in _SKIP_ALIASES:
            return
        if len(cleaned) < 2:
            return
        seen.add(key)
        aliases.append(cleaned)

    add(name)
    without_prefix = _TOTVS_PREFIX_RE.sub("", name).strip()
    short_line_names = {
        extra.casefold()
        for extras in KNOWN_LINE_ALIASES.values()
        for extra in extras
    }
    if without_prefix.casefold() in short_line_names:
        if slug.casefold() in CANONICAL_LINE_SLUGS.values():
            add(without_prefix)
    else:
        add(without_prefix)
    if " - " in without_prefix:
        left, right = without_prefix.split(" - ", 1)
        if left.casefold() not in _GENERIC_NAME_PARTS:
            add(left)
        if right.casefold() not in _LINE_SUFFIXES:
            add(right)
    add(slug.replace("-", " "))
    _attach_line_aliases(slug, add)
    for extra in EXTRA_ALIASES_BY_SLUG.get(slug.casefold(), ()):
        add(extra)
    return aliases


def _attach_line_aliases(slug: str, add) -> None:
    """Aliases curtos (Protheus, Fluig, RM…) só no produto canônico da linha."""
    slug_cf = slug.casefold()
    for needle, extras in KNOWN_LINE_ALIASES.items():
        if CANONICAL_LINE_SLUGS.get(needle) == slug_cf:
            for extra in extras:
                add(extra)


def _term_to_product(
    term: dict[str, Any],
    by_id: dict[int, dict[str, Any]],
) -> Optional[Product]:
    try:
        term_id = int(term.get("id") or 0)
        parent_id = int(term.get("parent") or 0)
        name = strip_html(str(term.get("name") or ""))
        slug = str(term.get("slug") or "").strip()
        url = str(term.get("link") or "").strip()
        description = strip_html(str(term.get("description") or ""))
    except (TypeError, ValueError, AttributeError):
        return None
    if not name or not slug:
        return None

    ancestors = ancestor_chain(term_id, by_id)
    parent = by_id.get(parent_id)
    parent_name = strip_html(str(parent.get("name") or "")) if parent else ""
    parent_slug = str(parent.get("slug") or "") if parent else ""
    category = parent_name or name

    slugs = [slug, parent_slug]
    slugs.extend(str(item.get("slug") or "") for item in ancestors)
    pillar = pillar_for_slugs(slugs)
    if is_generic_description(description):
        description = ""

    return Product(
        id=term_id,
        name=name,
        slug=slug,
        category=category,
        pillar=pillar,
        description=description,
        url=url,
        aliases=derive_aliases(name, slug),
        parent_slug=parent_slug,
        parent_id=parent_id,
    )


def _header_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None
