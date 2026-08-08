"""Esquema de estado compartilhado pelo grafo multiagente."""

import operator
from typing import Annotated, List, TypedDict

from schemas.intelligence_card import IntelligenceCard


class AgentReport(TypedDict):
    agent_key: str
    agent_name: str
    content: str


class State(TypedDict):
    input: str
    triage: str
    selected_agents: List[str]
    # `operator.add` permite que múltiplos nós especialistas, executando em
    # paralelo, adicionem seus relatórios à mesma lista sem sobrescrever
    # os resultados uns dos outros.
    reports: Annotated[List[AgentReport], operator.add]
    final_report: IntelligenceCard
