"""Persistência do catálogo em CSV (auditoria) e JSON (runtime do agente)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from catalog.models import Product

CSV_COLUMNS = [
    "name",
    "slug",
    "category",
    "pillar",
    "description",
    "url",
    "aliases",
    "parent_slug",
]


def default_data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def write_csv(products: list[Product], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for product in products:
            writer.writerow(product.to_csv_row())
    return path


def write_json(products: list[Product], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [product.to_json() for product in products]
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def export_catalog(products: list[Product], data_dir: Path | str | None = None) -> tuple[Path, Path]:
    target = Path(data_dir) if data_dir is not None else default_data_dir()
    csv_path = write_csv(products, target / "produtos_totvs.csv")
    json_path = write_json(products, target / "produtos_totvs.json")
    return csv_path, json_path
