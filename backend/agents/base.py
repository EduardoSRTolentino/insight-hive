"""Configuração compartilhada do LLM usado por todos os agentes."""

import time
from functools import lru_cache
from threading import Lock

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from ollama import ResponseError

from settings import get_settings

_settings = get_settings()

MODEL_NAME = _settings.ollama_model
OLLAMA_BASE_URL = _settings.ollama_base_url
# Limite conservador: o modelo 20B não aguenta muitas gerações seguidas.
NUM_PREDICT = _settings.num_predict
# Síntese: thinking low + JSON aninhado do card.
NUM_PREDICT_SYNTHESIS = _settings.num_predict_synthesis
MAX_ATTEMPTS = 3
RETRY_BASE_SECONDS = 2.0
# Cap de especialistas por análise (triagem + N + síntese).
MAX_SPECIALISTS = _settings.max_specialists
# gpt-oss: "low" pensa pouco e separa o JSON em content. False piora a
# síntese; o padrão (medium/high) esgota o num_predict e esvazia o card.
REASONING_LEVEL = _settings.ollama_reasoning
_REASONING_OFF = {"", "false", "off", "none", "no", "0"}

# Ollama local não aguenta bem várias gerações em paralelo no mesmo modelo.
_llm_lock = Lock()
_thinking_override: dict[tuple[str, str], bool] = {}


def effective_reasoning(level: str, *, supports_thinking: bool) -> str | None:
    stripped = (level or "").strip()
    if stripped.lower() in _REASONING_OFF or not supports_thinking:
        return None
    return stripped


@lru_cache(maxsize=8)
def model_supports_thinking(model: str, base_url: str) -> bool:
    override = _thinking_override.get((model, base_url))
    if override is not None:
        return override
    url = base_url.rstrip("/") + "/api/tags"
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError, OSError, TypeError):
        return False
    for item in payload.get("models") or []:
        if not isinstance(item, dict):
            continue
        if item.get("name") != model and item.get("model") != model:
            continue
        caps = {str(cap).lower() for cap in (item.get("capabilities") or [])}
        return "thinking" in caps
    return False


def mark_thinking_unsupported() -> None:
    settings = get_settings()
    _thinking_override[(settings.ollama_model, settings.ollama_base_url)] = False
    model_supports_thinking.cache_clear()
    get_llm.cache_clear()


def _thinking_rejected(exc: BaseException) -> bool:
    return "does not support thinking" in str(exc).lower()


def _chat_ollama_kwargs(
    *,
    num_predict: int | None = None,
    json_mode: bool = False,
) -> dict[str, object]:
    settings = get_settings()
    kwargs: dict[str, object] = {
        "model": settings.ollama_model,
        "base_url": settings.ollama_base_url,
        "num_predict": settings.num_predict if num_predict is None else num_predict,
    }
    reasoning = effective_reasoning(
        settings.ollama_reasoning,
        supports_thinking=model_supports_thinking(
            settings.ollama_model, settings.ollama_base_url
        ),
    )
    if reasoning is not None:
        kwargs["reasoning"] = reasoning
    if json_mode:
        kwargs["format"] = "json"
    return kwargs


@lru_cache(maxsize=1)
def get_llm() -> ChatOllama:
    return ChatOllama(**_chat_ollama_kwargs())

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
    updates = _chat_ollama_kwargs(num_predict=num_predict, json_mode=json_mode)
    model = get_llm().model_copy(update=updates)

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with _llm_lock:
                response = model.invoke(messages)
            return _coerce_message_content(response)
        except (ResponseError, ConnectionError, TimeoutError, OSError) as exc:
            last_error = exc
            if _thinking_rejected(exc) and "reasoning" in updates:
                mark_thinking_unsupported()
                updates = _chat_ollama_kwargs(
                    num_predict=num_predict, json_mode=json_mode
                )
                model = get_llm().model_copy(update=updates)
                continue
            if attempt >= MAX_ATTEMPTS:
                break
            time.sleep(RETRY_BASE_SECONDS * attempt)

    assert last_error is not None
    raise last_error
