"""Nó genérico de agente especialista e roteamento paralelo via Send."""

from typing import Any, Callable, List

from langgraph.types import Send

from agents.base import MAX_SPECIALISTS, invoke_agent, truncate_text
from config.agents_config import SPECIALIST_AGENTS, SpecialistAgentConfig
from graph.state import State


def specialist_node_name(agent_key: str) -> str:
    return f"specialist_{agent_key}"


def make_specialist_node(agent_config: SpecialistAgentConfig) -> Callable[[State], dict]:
    """Cria a função de nó de um agente especialista a partir da sua configuração."""

    def specialist_node(state: State) -> dict[str, Any]:
        user_content = (
            f"Entrada original do usuário:\n{truncate_text(state['input'], 3500)}\n\n"
            f"Análise preliminar do gestor:\n{truncate_text(state['triage'], 600)}\n\n"
            "Faça uma análise profunda desta entrada sob a ótica da sua área "
            "de especialidade."
        )
        content = invoke_agent(
            agent_config["system_prompt"],
            user_content,
            json_mode=True,
        )
        report = {
            "agent_key": agent_config["key"],
            "agent_name": agent_config["name"],
            "content": content,
        }
        return {"reports": [report]}

    return specialist_node


def dispatch_to_specialists(state: State) -> List[Send]:
    """Despacha para até MAX_SPECIALISTS especialistas selecionados pelo manager."""
    valid_keys = {agent["key"] for agent in SPECIALIST_AGENTS}
    selected = [key for key in state.get("selected_agents", []) if key in valid_keys]
    selected = selected[:MAX_SPECIALISTS]
    if not selected:
        selected = [agent["key"] for agent in SPECIALIST_AGENTS][:MAX_SPECIALISTS]

    return [Send(specialist_node_name(key), state) for key in selected]
