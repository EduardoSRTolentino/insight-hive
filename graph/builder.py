"""Montagem do grafo multiagente: manager -> especialistas (paralelo) -> manager."""

from langgraph.graph import END, START, StateGraph

from agents.manager import manager_synthesis, manager_triage
from agents.specialist import dispatch_to_specialists, make_specialist_node, specialist_node_name
from config.agents_config import SPECIALIST_AGENTS
from graph.state import State


def build_graph():
    graph = StateGraph(State)

    graph.add_node("manager_triage", manager_triage)
    graph.add_node("manager_synthesis", manager_synthesis)

    for agent_config in SPECIALIST_AGENTS:
        node_name = specialist_node_name(agent_config["key"])
        graph.add_node(node_name, make_specialist_node(agent_config))
        graph.add_edge(node_name, "manager_synthesis")

    graph.add_edge(START, "manager_triage")
    # `dispatch_to_specialists` retorna objetos `Send`, permitindo fan-out
    # paralelo dinâmico para os especialistas escolhidos pelo manager.
    graph.add_conditional_edges("manager_triage", dispatch_to_specialists)
    graph.add_edge("manager_synthesis", END)

    return graph.compile()


compiled_graph = build_graph()
