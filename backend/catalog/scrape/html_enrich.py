"""Enriquece descrições vazias a partir do HTML público da ficha/produto.

Seletores CSS (páginas WordPress SSR em produtos.totvs.com):

- Nome: ``h1`` (título do arquivo da taxonomia, ex. TOTVS Backoffice - Linha Protheus)
- Descrição curta: primeiro ``p`` substancial após o ``h1`` (lead do produto)
- Categoria: ``a[href*="/produto/"]`` no card/breadcrumb
- Ficha técnica: ``a[href*="/ficha-tecnica/"]`` na seção FICHA TÉCNICA

A listagem ``/ficha-tecnica/`` usa o botão "VEJA MAIS" (AJAX) e não é a fonte
primária: a API WP já devolve todos os termos.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from catalog.models import Product
from catalog.scrape.client import HttpError, get
from catalog.scrape.wp_taxonomy import is_generic_description, strip_html

_SKIP_PARAGRAPHS = frozenset(
    {
        "aceito",
        "ligamos para você",
        "saiba mais",
        "acesse",
        "veja mais",
        "cadastre seu e-mail para se atualizar",
        "contato via whatsapp",
        "fique por dentro das novidades",
    }
)
_MIN_DESCRIPTION_LEN = 40


def enrich_missing_descriptions(products: list[Product]) -> list[Product]:
    """Preenche `description` vazia com o lead HTML da página do produto."""
    pending = [item for item in products if not item.description and item.url]
    for index, product in enumerate(pending, start=1):
        try:
            lead = fetch_product_lead(product.url)
        except (HttpError, AttributeError):
            continue
        if lead:
            product.description = lead
        if index % 10 == 0 or index == len(pending):
            print(f"  HTML {index}/{len(pending)}")
    return products


def fetch_product_lead(url: str) -> str:
    """Extrai a descrição curta de uma página de produto.

    Raises:
        HttpError: conexão ou status HTTP diferente de 200.
        AttributeError: elemento esperado ausente no DOM.
    """
    response = get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    heading = soup.find("h1")
    if heading is None:
        raise AttributeError(f"h1 não encontrado em {url}")

    paragraph = _first_useful_paragraph(heading)
    if paragraph is None:
        raise AttributeError(f"parágrafo de lead não encontrado em {url}")

    text = strip_html(paragraph.get_text(" ", strip=True))
    if len(text) < _MIN_DESCRIPTION_LEN or is_generic_description(text):
        raise AttributeError(f"lead curto demais em {url}")
    return text


def _first_useful_paragraph(heading: Tag) -> Tag | None:
    for sibling in heading.next_elements:
        if not isinstance(sibling, Tag) or sibling.name != "p":
            continue
        text = strip_html(sibling.get_text(" ", strip=True))
        normalized = re.sub(r"\s+", " ", text).strip().casefold()
        if not normalized or normalized in _SKIP_PARAGRAPHS:
            continue
        if is_generic_description(normalized):
            continue
        if len(normalized) < _MIN_DESCRIPTION_LEN:
            continue
        return sibling
    return None
