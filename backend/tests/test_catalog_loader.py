from __future__ import annotations

from catalog.loader import CatalogIndex
from catalog.models import Product


def _product(name: str, slug: str, aliases: list[str] | None = None) -> Product:
    return Product(
        name=name,
        slug=slug,
        category="Gestão",
        pillar="Gestão",
        description="",
        url="https://example.com",
        aliases=aliases or [name],
    )


def test_match_finds_alias_and_dedupes() -> None:
    index = CatalogIndex(
        [
            _product("Protheus", "protheus", ["Protheus", "ERP Protheus"]),
            _product("Fluig", "fluig", ["Fluig"]),
        ]
    )
    hits = index.match("Vamos migrar o ERP Protheus e o Fluig da operação.")
    slugs = [item.slug for item in hits]
    assert slugs == ["protheus", "fluig"]


def test_match_empty_text() -> None:
    index = CatalogIndex([_product("Protheus", "protheus")])
    assert index.match("   ") == []
