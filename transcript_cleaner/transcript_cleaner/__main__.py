"""CLI: python -m transcript_cleaner INPUT [-o OUT] [--stats] [--format json|csv]."""

from __future__ import annotations

import argparse
import json
import sys

from .normalize import NormalizeError
from .pipeline import clean_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transcript_cleaner",
        description="Limpa transcrições JSON/CSV para consumo eficiente por LLMs.",
    )
    parser.add_argument("input", help="Caminho do arquivo .json ou .csv")
    parser.add_argument("-o", "--output", help="Arquivo de saída (default: stdout)")
    parser.add_argument(
        "--format",
        choices=("json", "csv"),
        default=None,
        help="Força o formato de entrada",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Imprime estatísticas em stderr (JSON)",
    )
    parser.add_argument(
        "--keep-inaudible",
        action="store_true",
        help="Mantém marcadores [inaudível]",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = {"keep_inaudible": args.keep_inaudible}
    try:
        result = clean_file(args.input, format=args.format, config=config)
    except (NormalizeError, OSError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(result["cleaned_text"])
    else:
        sys.stdout.write(result["cleaned_text"])

    if args.stats:
        print(json.dumps(result["stats"], ensure_ascii=False, indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
