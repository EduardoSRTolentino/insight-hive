"""Nó genérico de agente especialista e roteamento paralelo via Send."""

import logging
from typing import Any, Callable, List

from langgraph.types import Send

from agents.base import MAX_SPECIALISTS, invoke_agent, truncate_text
from config.agents_config import SPECIALIST_AGENTS, SpecialistAgentConfig
from graph.state import State

logger = logging.getLogger(__name__)

ECOSYSTEM_AGENT_KEY = "ecossistema_totvs"

SPECIALIST_FAILURE_CONTENT = (
    "[Este especialista falhou ao gerar o relatório (erro no modelo local). "
    "Ignore esta seção na síntese; não invente dados para preenchê-la.]"
)


def specialist_node_name(agent_key: str) -> str:
    return f"specialist_{agent_key}"


def _ecosystem_catalog_block(text: str) -> str:
    """Injeta só os produtos do catálogo citados na reunião."""
    try:
        from catalog.loader import format_hits_for_prompt, match

        return format_hits_for_prompt(match(text))
    except Exception:
        return (
            "Catálogo TOTVS indisponível. Não invente produtos fora do gazetteer "
            "do system prompt."
        )


def make_specialist_node(agent_config: SpecialistAgentConfig) -> Callable[[State], dict]:
    """Cria a função de nó de um agente especialista a partir da sua configuração."""

    def specialist_node(state: State) -> dict[str, Any]:
        user_content = (
            f"Entrada original do usuário:\n{truncate_text(state['input'], 3500)}\n\n"
            f"Análise preliminar do gestor:\n{truncate_text(state['triage'], 600)}\n\n"
            "Faça uma análise profunda desta entrada sob a ótica da sua área "
            "de especialidade."
        )
        if agent_config["key"] == ECOSYSTEM_AGENT_KEY:
            user_content += "\n\n" + _ecosystem_catalog_block(state.get("input") or "")
        try:
            content = invoke_agent(
                agent_config["system_prompt"],
                user_content,
                json_mode=True,
            )
        except Exception:
            # Um especialista falhando não pode derrubar a análise inteira —
            # `invoke_agent` já esgotou os retries dele; melhor a síntese
            # seguir sem esta seção do que perder o trabalho dos outros
            # especialistas que deram certo.
            logger.exception(
                "Especialista '%s' falhou; seguindo sem o relatório dele.",
                agent_config["key"],
            )
            content = SPECIALIST_FAILURE_CONTENT
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
