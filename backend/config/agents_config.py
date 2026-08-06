"""Registro configurável dos agentes especialistas do sistema multiagente.

Para adicionar uma nova área de análise, basta incluir um novo dict nesta
lista com "key", "name" e "system_prompt". Nenhuma alteração no grafo
(ver `graph/builder.py`) é necessária: os nós dos especialistas e as
conexões com o agente manager são criados dinamicamente a partir desta
configuração.
"""

from typing import Optional, TypedDict


class SpecialistAgentConfig(TypedDict):
    key: str
    name: str
    system_prompt: str


SPECIALIST_AGENTS: list[SpecialistAgentConfig] = [
    {
        "key": "geral",
        "name": "Agente Geral",
        "system_prompt": (
            "Você é um especialista em análise geral. Aprofunde a análise "
            "preliminar feita pelo agente gestor, destacando riscos, "
            "oportunidades e pontos que exigem atenção."
        ),
    },
    {
        "key": "tecnico",
        "name": "Agente Técnico",
        "system_prompt": (
            "Você é um especialista técnico. Analise a entrada sob a ótica "
            "de viabilidade técnica, riscos de implementação e requisitos "
            "necessários."
        ),
    },
]


def get_agent_by_key(key: str) -> Optional[SpecialistAgentConfig]:
    return next((agent for agent in SPECIALIST_AGENTS if agent["key"] == key), None)
