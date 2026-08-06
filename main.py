"""Ponto de entrada do sistema multiagente: loop de interação no terminal."""

from graph.builder import compiled_graph


def run() -> None:
    while True:
        entrada = input("Digite a entrada para análise: ").strip()
        if not entrada:
            print("A entrada não pode ser vazia.")
            continue

        resultado = compiled_graph.invoke({"input": entrada, "reports": []})

        print("\n===== RELATÓRIO FINAL =====\n")
        print(resultado["final_report"])
        print("\n============================\n")

        continuar = input("Deseja fazer outra análise? (sim/não): ").strip().lower()
        if continuar != "sim":
            break


if __name__ == "__main__":
    run()
