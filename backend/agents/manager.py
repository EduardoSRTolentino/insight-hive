"""Funções do agente manager: triagem inicial e síntese final."""

import json
from typing import Any

from agents.base import invoke_agent
from config.agents_config import SPECIALIST_AGENTS
from graph.state import State

MANAGER_TRIAGE_SYSTEM_PROMPT = (
    "Você é o agente gestor (manager) de um sistema multiagente. Sua função é "
    "receber a entrada do usuário, fazer uma análise preliminar (base) do "
    "conteúdo, e decidir quais agentes especialistas devem analisá-la em "
    "profundidade.\n\n"
    "Agentes especialistas disponíveis:\n{agents_list}\n\n"
    "Responda APENAS com um JSON no formato:\n"
    '{{"triage": "<sua análise preliminar>", "selected_agents": ["<key1>", "<key2>"]}}\n'
    "Selecione somente as chaves ('key') dos agentes realmente relevantes "
    "para a entrada recebida."
)

MANAGER_SYNTHESIS_SYSTEM_PROMPT = (
    "Você é o agente gestor (manager) de um sistema multiagente. Você recebeu "
    "relatórios de análise profunda de diferentes agentes especialistas. Sua "
    "tarefa é consolidar essas informações em um único relatório final, claro "
    "e objetivo, destacando os principais pontos, riscos e recomendações de "
    "cada área analisada."
)


def _build_triage_prompt() -> str:
    agents_list = "\n".join(
        f"- {agent['key']}: {agent['name']}" for agent in SPECIALIST_AGENTS
    )
    return MANAGER_TRIAGE_SYSTEM_PROMPT.format(agents_list=agents_list)


def manager_triage(state: State) -> dict[str, Any]:
    """Analisa a entrada do usuário e decide quais especialistas acionar."""
    raw_response = invoke_agent(_build_triage_prompt(), state["input"])

    all_keys = [agent["key"] for agent in SPECIALIST_AGENTS]
    triage_text = raw_response
    selected_agents = all_keys

    try:
        parsed = json.loads(raw_response)
        triage_text = parsed.get("triage", raw_response)
        candidate_keys = parsed.get("selected_agents", all_keys)
        valid_keys = [key for key in candidate_keys if key in all_keys]
        selected_agents = valid_keys or all_keys
    except (json.JSONDecodeError, AttributeError, TypeError):
        # Se o modelo não retornar um JSON válido, mantém a resposta bruta
        # como triagem e aciona todos os especialistas configurados.
        pass

    return {"triage": triage_text, "selected_agents": selected_agents}


def manager_synthesis(state: State) -> dict[str, Any]:
    """Consolida os relatórios dos especialistas em um relatório final único."""
    reports_text = "\n\n".join(
        f"### Relatório: {report['agent_name']}\n{report['content']}"
        for report in state["reports"]
    )
    user_content = (
        f"Entrada original do usuário:\n{state['input']}\n\n"
        f"Análise preliminar do gestor:\n{state['triage']}\n\n"
        f"Relatórios dos especialistas:\n{reports_text}"
    )
    final_report = invoke_agent(MANAGER_SYNTHESIS_SYSTEM_PROMPT, user_content)
    return {"final_report": final_report}
