"""CLI: python -m catalog.scrape

Fonte primária: taxonomia WordPress pública
``GET https://produtos.totvs.com/wp-json/wp/v2/produto``.

Descrições vazias são enriquecidas com o lead HTML da página do produto
(``h1`` + primeiro ``p``). Playwright não é necessário: o portal é SSR.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from catalog.models import Product
from catalog.scrape.client import HttpError
from catalog.scrape.export import default_data_dir, export_catalog
from catalog.scrape.html_enrich import enrich_missing_descriptions
from catalog.scrape.wp_taxonomy import (
    assemble_products,
    fetch_all_terms,
    is_generic_description,
)


def _merge_existing_descriptions(products: list[Product], json_path: Path) -> None:
    """Preserva leads HTML já extraídos quando a API volta sem descrição."""
    if not json_path.is_file():
        return
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if not isinstance(payload, list):
        return
    previous = {
        str(item.get("slug") or ""): str(item.get("description") or "")
        for item in payload
        if isinstance(item, dict)
    }
    for product in products:
        if product.description and not is_generic_description(product.description):
            continue
        prior = previous.get(product.slug, "")
        if prior and not is_generic_description(prior):
            product.description = prior
        else:
            product.description = ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extrai o catálogo de produtos TOTVS para CSV e JSON.",
    )
    parser.add_argument(
        "--skip-enrich",
        action="store_true",
        help="Não baixa páginas HTML para preencher descrições vazias.",
    )
    parser.add_argument(
        "--data-dir",
        default=str(default_data_dir()),
        help="Diretório de saída (default: backend/catalog/data).",
    )
    args = parser.parse_args(argv)

    try:
        terms = fetch_all_terms()
    except HttpError as exc:
        print(f"Falha ao ler a API WordPress: {exc}", file=sys.stderr)
        return 1

    products = assemble_products(terms)
    data_dir = Path(args.data_dir)
    _merge_existing_descriptions(products, data_dir / "produtos_totvs.json")
    if not args.skip_enrich:
        missing = sum(1 for item in products if not item.description)
        print(f"Enriquecendo {missing} produtos sem descrição via HTML...")
        products = enrich_missing_descriptions(products)

    csv_path, json_path = export_catalog(products, data_dir=data_dir)
    with_desc = sum(1 for item in products if item.description)
    print(
        f"Exportados {len(products)} produtos "
        f"({with_desc} com descrição) para:\n  {csv_path}\n  {json_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
