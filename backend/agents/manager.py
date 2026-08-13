"""Funções do agente manager: triagem inicial e síntese final."""

import logging
from typing import Any

from agents.base import (
    MAX_SPECIALISTS,
    NUM_PREDICT_SYNTHESIS,
    invoke_agent,
    truncate_text,
)
from config.agents_config import SPECIALIST_AGENTS
from graph.state import State
from schemas.intelligence_card import (
    DEFAULT_VALUE,
    POINT_FIELDS,
    loads_json_object,
    parse_intelligence_card,
)

logger = logging.getLogger(__name__)

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
    "tarefa é consolidar essas informações em um Card de Inteligência "
    "comercial.\n\n"
    "Responda APENAS com um JSON válido (sem markdown, sem texto fora do JSON) "
    "no formato:\n"
    "{\n"
    '  "conta": "nome ou descrição da conta/cliente",\n'
    '  "ecossistema_mapeado": {\n'
    '    "valor": "resumo curto em uma linha",\n'
    '    "analise": "1 a 2 frases aprofundando o ponto",\n'
    '    "evidencias": ["trecho ou paráfrase de suporte"]\n'
    "  },\n"
    '  "concorrente_citado": {\n'
    '    "valor": "resumo curto",\n'
    '    "analise": "1 a 2 frases",\n'
    '    "evidencias": ["..."]\n'
    "  },\n"
    '  "oportunidade": {\n'
    '    "valor": "oportunidade principal (ex.: Cross-sell: ...)",\n'
    '    "analise": "1 a 2 frases",\n'
    '    "evidencias": ["..."]\n'
    "  },\n"
    '  "persona_detectada": {\n'
    '    "valor": "papel/persona principal",\n'
    '    "analise": "1 a 2 frases",\n'
    '    "evidencias": ["..."]\n'
    "  },\n"
    '  "sentimento": {\n'
    '    "valor": "tom geral (ex.: Receptivo / exploratório)",\n'
    '    "analise": "1 a 2 frases",\n'
    '    "evidencias": ["..."]\n'
    "  },\n"
    '  "status": "Pendente revisão humana"\n'
    "}\n"
    "Regras:\n"
    "- Preencha valor com o que os especialistas e a entrada original "
    "mostrarem (label, summary, produtos, riscos). Só use 'Não identificado' "
    "quando realmente não houver evidência.\n"
    "- analise e evidencias devem consolidar a entrada original e os "
    "relatórios dos especialistas; não invente fatos.\n"
    "- evidencias: no máximo 2 itens; pode ser [] se não houver suporte.\n"
    "- status deve ser 'Pendente revisão humana' salvo indicação explícita "
    "em contrário.\n"
    "- valor deve ser uma string curta (idealmente uma linha)."
)


def _build_triage_prompt() -> str:
    agents_list = "\n".join(
        f"- {agent['key']}: {agent['name']}" for agent in SPECIALIST_AGENTS
    )
    return MANAGER_TRIAGE_SYSTEM_PROMPT.format(agents_list=agents_list)


def manager_triage(state: State) -> dict[str, Any]:
    """Analisa a entrada do usuário e decide quais especialistas acionar."""
    raw_response = invoke_agent(
        _build_triage_prompt(),
        truncate_text(state["input"], 4000),
        json_mode=True,
    )

    all_keys = [agent["key"] for agent in SPECIALIST_AGENTS]
    fallback_keys = all_keys[:MAX_SPECIALISTS]
    triage_text = raw_response
    selected_agents = fallback_keys

    parsed = loads_json_object(raw_response)
    if parsed is not None:
        triage_text = parsed.get("triage", raw_response)
        candidate_keys = parsed.get("selected_agents", fallback_keys)
        if not isinstance(candidate_keys, list):
            candidate_keys = fallback_keys
        valid_keys = [key for key in candidate_keys if key in all_keys]
        selected_agents = (valid_keys or fallback_keys)[:MAX_SPECIALISTS]

    return {"triage": triage_text, "selected_agents": selected_agents}


def manager_synthesis(state: State) -> dict[str, Any]:
    """Consolida os relatórios dos especialistas em um Card de Inteligência."""
    reports_text = "\n\n".join(
        f"### Relatório: {report['agent_name']}\n{truncate_text(report['content'], 1200)}"
        for report in state["reports"]
    )
    user_content = (
        f"Entrada original do usuário:\n{truncate_text(state['input'], 4000)}\n\n"
        f"Análise preliminar do gestor:\n{truncate_text(state['triage'], 800)}\n\n"
        f"Relatórios dos especialistas:\n{truncate_text(reports_text, 6000)}"
    )
    raw_response = invoke_agent(
        MANAGER_SYNTHESIS_SYSTEM_PROMPT,
        user_content,
        num_predict=NUM_PREDICT_SYNTHESIS,
        json_mode=True,
    )
    card = parse_intelligence_card(raw_response)
    if card["conta"] == DEFAULT_VALUE and all(
        card[field]["valor"] == DEFAULT_VALUE for field in POINT_FIELDS
    ):
        logger.warning(
            "Síntese do card vazia (JSON inválido ou truncado). raw=%s",
            truncate_text(raw_response, 800),
        )
    return {"final_report": card}
