"""Configuração compartilhada do LLM usado por todos os agentes."""

import os
import time
from threading import Lock

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from ollama import ResponseError

load_dotenv()


def _env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


MODEL_NAME = os.getenv("OLLAMA_MODEL", "gpt-oss:20b").strip() or "gpt-oss:20b"
# Limite conservador: o modelo 20B não aguenta muitas gerações seguidas.
NUM_PREDICT = _env_int("NUM_PREDICT", 512, minimum=128, maximum=8192)
# Síntese: thinking low + JSON aninhado do card.
NUM_PREDICT_SYNTHESIS = _env_int(
    "NUM_PREDICT_SYNTHESIS", 2048, minimum=256, maximum=8192
)
MAX_ATTEMPTS = 3
RETRY_BASE_SECONDS = 2.0
# Cap de especialistas por análise (triagem + N + síntese).
MAX_SPECIALISTS = _env_int("MAX_SPECIALISTS", 2, minimum=1, maximum=12)
# gpt-oss: "low" pensa pouco e separa o JSON em content. False piora a
# síntese; o padrão (medium/high) esgota o num_predict e esvazia o card.
REASONING_LEVEL = os.getenv("OLLAMA_REASONING", "low").strip() or "low"

# Ollama local não aguenta bem várias gerações em paralelo no mesmo modelo.
_llm_lock = Lock()

llm = ChatOllama(
    model=MODEL_NAME,
    num_predict=NUM_PREDICT,
    reasoning=REASONING_LEVEL,
)

_THINKING_BLOCK_TYPES = {"thinking", "reasoning", "reason"}


def truncate_text(text: str, max_chars: int) -> str:
    text = text or ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20].rstrip() + "\n...[truncado]"


def _text_from_content_item(item: object) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return ""
    block_type = str(item.get("type", "")).lower()
    if block_type in _THINKING_BLOCK_TYPES:
        return ""
    if "text" in item:
        return str(item["text"])
    return ""


def _coerce_message_content(response: object) -> str:
    content = getattr(response, "content", "")
    if isinstance(content, list):
        text = "".join(_text_from_content_item(item) for item in content)
    elif content is None:
        text = ""
    else:
        text = str(content)

    if text.strip():
        return text

    extra = getattr(response, "additional_kwargs", None) or {}
    for key in ("reasoning_content", "reasoning", "thinking"):
        value = extra.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return text


def invoke_agent(
    system_prompt: str,
    user_content: str,
    *,
    num_predict: int | None = None,
    json_mode: bool = False,
) -> str:
    """Invoca o LLM com um prompt de sistema e uma mensagem de usuário.

    Usado tanto pelo agente manager quanto pelos agentes especialistas,
    diferenciando o comportamento de cada um apenas pelo `system_prompt`.
    Serializa as chamadas e retenta erros transitórios do Ollama.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]
    # `bind(num_predict=...)` cai em kwargs soltos do Ollama (`Client.chat`
    # não aceita num_predict no topo; só em options). Copia o modelo.
    updates: dict[str, object] = {"reasoning": REASONING_LEVEL}
    if num_predict is not None:
        updates["num_predict"] = num_predict
    if json_mode:
        updates["format"] = "json"
    model = llm.model_copy(update=updates)

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with _llm_lock:
                response = model.invoke(messages)
            return _coerce_message_content(response)
        except (ResponseError, ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt >= MAX_ATTEMPTS:
                break
            time.sleep(RETRY_BASE_SECONDS * attempt)

    assert last_error is not None
    raise last_error
