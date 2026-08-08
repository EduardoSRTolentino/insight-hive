"""Configuração compartilhada do LLM usado por todos os agentes."""

import time
from threading import Lock

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from ollama import ResponseError

MODEL_NAME = "gpt-oss:20b"
# Limite conservador: o modelo 20B + fan-out de especialistas estoura RAM/conexão.
NUM_PREDICT = 512
MAX_ATTEMPTS = 3
RETRY_BASE_SECONDS = 2.0

# Ollama local não aguenta bem várias gerações em paralelo no mesmo modelo.
_llm_lock = Lock()

llm = ChatOllama(model=MODEL_NAME, num_predict=NUM_PREDICT)


def invoke_agent(system_prompt: str, user_content: str) -> str:
    """Invoca o LLM com um prompt de sistema e uma mensagem de usuário.

    Usado tanto pelo agente manager quanto pelos agentes especialistas,
    diferenciando o comportamento de cada um apenas pelo `system_prompt`.
    Serializa as chamadas e retenta erros transitórios do Ollama.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with _llm_lock:
                response = llm.invoke(messages)
            return response.content
        except (ResponseError, ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt >= MAX_ATTEMPTS:
                break
            time.sleep(RETRY_BASE_SECONDS * attempt)

    assert last_error is not None
    raise last_error
