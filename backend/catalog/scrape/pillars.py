"""Mapeia a taxonomia de produtos TOTVS para os 3 pilares do ecossistema."""

from __future__ import annotations

from typing import Iterable, Mapping, Optional

PILLAR_GESTAO = "Gestão"
PILLAR_TECHFIN = "Techfin"
PILLAR_BUSINESS_PERFORMANCE = "Business Performance"

# Slugs da taxonomia WP (próprios ou ancestrais) → pilar.
TECHFIN_SLUGS = frozenset(
    {
        "servicos-financeiros",
        "techfin",
    }
)
BUSINESS_PERFORMANCE_SLUGS = frozenset(
    {
        "digital-commerce",
        "automacao-de-marketing-e-vendas",
        "rd-station",
        "rdstation",
    }
)

KNOWN_LINE_ALIASES: dict[str, tuple[str, ...]] = {
    "protheus": ("Protheus", "Microsiga", "Linha Protheus"),
    "datasul": ("Datasul", "Linha Datasul"),
    "logix": ("Logix", "Linha Logix"),
    "fluig": ("Fluig",),
    "rm": ("RM", "Linha RM"),
}

# Aliases curtos só no ERP/plataforma canônico — não nas verticais "Linha X".
CANONICAL_LINE_SLUGS: dict[str, str] = {
    "protheus": "totvs-backoffice-linha-protheus",
    "datasul": "totvs-backoffice-linha-datasul",
    "logix": "totvs-backoffice-linha-logix",
    "rm": "totvs-backoffice-linha-rm",
    "fluig": "totvs-fluig",
}
EXTRA_ALIASES_BY_SLUG: dict[str, tuple[str, ...]] = {
    "servicos-financeiros": ("Techfin", "TOTVS Techfin"),
    "automacao-de-marketing-e-vendas": ("RD Station",),
    "totvs-cloud": ("TOTVS Cloud",),
    "totvs-rh": ("TOTVS RH",),
}


def pillar_for_slugs(slugs: Iterable[str]) -> str:
    """Classifica um produto a partir do slug próprio e da cadeia de pais."""
    normalized = {slug.strip().lower() for slug in slugs if slug}
    if normalized & TECHFIN_SLUGS:
        return PILLAR_TECHFIN
    if normalized & BUSINESS_PERFORMANCE_SLUGS:
        return PILLAR_BUSINESS_PERFORMANCE
    return PILLAR_GESTAO


def ancestor_chain(
    term_id: int,
    by_id: Mapping[int, Mapping[str, object]],
) -> list[Mapping[str, object]]:
    """Sobe a hierarquia `parent` até a raiz, sem loops."""
    chain: list[Mapping[str, object]] = []
    seen: set[int] = set()
    current_id: Optional[int] = term_id
    while current_id and current_id not in seen:
        seen.add(current_id)
        term = by_id.get(current_id)
        if term is None:
            break
        parent_id = int(term.get("parent") or 0)
        if not parent_id:
            break
        parent = by_id.get(parent_id)
        if parent is None:
            break
        chain.append(parent)
        current_id = parent_id
    return chain
