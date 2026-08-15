"""Ponto de entrada do sistema multiagente: loop de interação no terminal."""

import json

from file_input import FileInputError
from graph.builder import compiled_graph
from prepare_analysis_input import prepare_graph_input_from_path


def run() -> None:
    while True:
        caminho = input("Digite o caminho do arquivo (.csv ou .json) para análise: ").strip()
        try:
            entrada = prepare_graph_input_from_path(caminho)
        except FileInputError as exc:
            print(f"Erro: {exc}\n")
            continue

        resultado = compiled_graph.invoke({"input": entrada, "reports": []})

        print("\n===== CARD DE INTELIGÊNCIA =====\n")
        print(json.dumps(resultado["final_report"], ensure_ascii=False, indent=2))
        print("\n================================\n")

        continuar = input("Deseja fazer outra análise? (sim/não): ").strip().lower()
        if continuar != "sim":
            break


if __name__ == "__main__":
    run()
