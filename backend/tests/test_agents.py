from __future__ import annotations

from unittest.mock import MagicMock

from agents.specialist import SPECIALIST_FAILURE_CONTENT, make_specialist_node
from config.agents_config import SPECIALIST_AGENTS


def test_specialist_node_survives_invoke_agent_failure(monkeypatch) -> None:
    # Um especialista falhando (Ollama caiu no meio, timeout, etc.) não pode
    # derrubar a análise inteira — a síntese deve seguir sem esta seção em
    # vez de perder o trabalho dos especialistas que deram certo.
    monkeypatch.setattr(
        "agents.specialist.invoke_agent",
        MagicMock(side_effect=ConnectionError("ollama down")),
    )
    agent_config = SPECIALIST_AGENTS[0]
    node = make_specialist_node(agent_config)
    state = {"input": "reunião de teste", "triage": "triagem", "reports": []}

    result = node(state)

    assert len(result["reports"]) == 1
    report = result["reports"][0]
    assert report["agent_key"] == agent_config["key"]
    assert report["content"] == SPECIALIST_FAILURE_CONTENT
