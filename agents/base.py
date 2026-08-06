"""Configuração compartilhada do LLM usado por todos os agentes."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

MODEL_NAME = "gpt-oss:20b"

llm = ChatOllama(model=MODEL_NAME, num_predict=1024)


def invoke_agent(system_prompt: str, user_content: str) -> str:
    """Invoca o LLM com um prompt de sistema e uma mensagem de usuário.

    Usado tanto pelo agente manager quanto pelos agentes especialistas,
    diferenciando o comportamento de cada um apenas pelo `system_prompt`.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages)
    return response.content
