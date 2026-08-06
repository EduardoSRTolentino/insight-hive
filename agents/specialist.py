"""Nó genérico de agente especialista e roteamento paralelo via Send."""

from typing import Any, Callable, List

from langgraph.types import Send

from agents.base import invoke_agent
from config.agents_config import SPECIALIST_AGENTS, SpecialistAgentConfig
from graph.state import State


def specialist_node_name(agent_key: str) -> str:
    return f"specialist_{agent_key}"


def make_specialist_node(agent_config: SpecialistAgentConfig) -> Callable[[State], dict]:
    """Cria a função de nó de um agente especialista a partir da sua configuração."""

    def specialist_node(state: State) -> dict[str, Any]:
        user_content = (
            f"Entrada original do usuário:\n{state['input']}\n\n"
            f"Análise preliminar do gestor:\n{state['triage']}\n\n"
            "Faça uma análise profunda desta entrada sob a ótica da sua área "
            "de especialidade."
        )
        content = invoke_agent(agent_config["system_prompt"], user_content)
        report = {
            "agent_key": agent_config["key"],
            "agent_name": agent_config["name"],
            "content": content,
        }
        return {"reports": [report]}

    return specialist_node


def dispatch_to_specialists(state: State) -> List[Send]:
    """Aresta condicional que despacha, em paralelo, para cada especialista selecionado pelo manager."""
    valid_keys = {agent["key"] for agent in SPECIALIST_AGENTS}
    selected = [key for key in state.get("selected_agents", []) if key in valid_keys]
    if not selected:
        selected = list(valid_keys)

    return [Send(specialist_node_name(key), state) for key in selected]
