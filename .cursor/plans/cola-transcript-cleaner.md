---
name: Cola fina transcript_cleaner
overview: Ligar o pacote isolado transcript_cleaner ao upload/CLI só nos entrypoints, sem LLM extra, sem mudar o grafo e sem o cleaner importar o backend.
todos:
  - id: glue-module
    content: Criar backend/prepare_analysis_input.py (único lugar que importa transcript_cleaner)
    status: pending
  - id: wire-entrypoints
    content: Usar a cola em routers/analysis.py e main.py; file_input.py permanece o fallback genérico
    status: pending
  - id: install-one-way
    content: Dependência unidirecional (pip -e ../transcript_cleaner) + ImportError fallback se o pacote não estiver instalado
    status: pending
  - id: env-escape
    content: TRANSCRIPT_CLEAN=1/0 no .env para desligar a limpeza sem código
    status: pending
  - id: smoke-transcript
    content: Smoke com fixture de reunião vs CSV genérico; grafo recebe texto limpo só no primeiro caso
    status: pending
isProject: true
---

# Cola fina do transcript_cleaner no insight-hive

> **Handoff.** Este plano é só a **composição no entrypoint**. O pipeline já existe em [`transcript_cleaner/`](../../transcript_cleaner/).  
> **Pacote / isolamento original:** [`.cursor/plans/transcript-cleaner.md`](transcript-cleaner.md) e [`transcript_cleaner/README.md`](../../transcript_cleaner/README.md).  
> **Não reimplementar** o cleaner. **Não** colocar limpeza dentro de `agents/` ou `graph/`.

## Estado atual (não alterar o desenho)

```text
upload CSV/JSON
  → file_input.parse_file_content   (texto bruto)
  → compiled_graph.invoke({input})  (triagem → até N especialistas → síntese)
  → IntelligenceCard
```

O cleaner já faz: normalize → regex → heurística KEEP/DROP → speakers/merge → (LLM opcional nas etapas 3–4).  
`llm_client=None` (default) **não chama modelo**: etapas 1–2 + DROP heurístico. É isso que a cola deve usar.

O backend hoje **não importa** o cleaner. O cleaner **não importa** o backend. Manter os dois sentidos.

## Objetivo

Se o arquivo for transcrição (`speaker`/`text` ou aliases), o `input` do grafo passa a ser `cleaned_text`.  
Se não for, o fluxo atual (`parse_file_content`) permanece idêntico.

## Princípio: o mínimo de dependência

| Direção | Permitido? |
|---------|------------|
| `transcript_cleaner` → `backend/*` | **Nunca** |
| `backend/agents`, `graph`, `schemas`, `security`, `config` → cleaner | **Nunca** |
| `backend/file_input.py` → cleaner | **Não** — continua parser genérico |
| Só `prepare_analysis_input.py` (e, via ele, `analysis.py` / `main.py`) → cleaner | **Sim**, API pública apenas |
| LangChain / LangGraph / FastAPI / PyJWT dentro do cleaner | **Nunca** |
| Novo nó LangGraph de limpeza | **Nunca** |
| Adapter `LlmClient` com Ollama nesta entrega | **Não** — zero chamadas LLM a mais (o 20B já faz triagem + N + síntese) |

Dependência nova, **unidirecional**: o backend *pode* usar o pacote como biblioteca. O pacote continua com `dependencies = []`.

Se `import transcript_cleaner` falhar, a análise **segue com texto bruto** (comportamento de hoje). O multiagente não fica refém do cleaner.

## Arquitetura alvo (única mudança de fluxo)

```text
bytes/path
    │
    ├─ TRANSCRIPT_CLEAN=0 ──────────────────────► parse_file_content ──► grafo
    │
    └─ TRANSCRIPT_CLEAN=1 (default)
           │
           ├─ parece transcrição ──► clean_file(..., llm_client=None)
           │                         wrap cleaned_text ──► grafo
           │
           └─ NormalizeError / não-transcrição ──► parse_file_content ──► grafo
```

O grafo, os especialistas, o card e o frontend **não mudam de contrato**. `State.input` continua `str`.

```mermaid
flowchart LR
  upload[upload_ou_CLI]
  glue[prepare_analysis_input]
  generic[file_input.parse_file_content]
  cleaner[transcript_cleaner.clean_file]
  graph[compiled_graph]

  upload --> glue
  glue -->|nao transcricao ou cleaner off| generic --> graph
  glue -->|transcricao| cleaner --> graph
```

## O que criar

### 1. Um módulo de cola — `backend/prepare_analysis_input.py`

Único arquivo novo no backend. Único que importa `transcript_cleaner`.

Responsabilidades:

1. Ler `TRANSCRIPT_CLEAN` do env (default ligado). `0` / `false` / `off` desliga.
2. `try: from transcript_cleaner import clean_file, NormalizeError` — se `ImportError`, devolver `parse_file_content(...)`.
3. Chamar `clean_file(content_or_path, filename=..., format=ext, llm_client=None)`.
4. Em `NormalizeError` (CSV/JSON sem campo de fala): **fallback** para `parse_file_content` / `load_file_input`. Não 400.
5. Montar a string do grafo no mesmo espírito do `file_input` atual:

```text
Arquivo de entrada: {basename} (formato {ext}, transcrição limpa)

{cleaned_text}
```

Não logar o transcript. Stats podem ir num `logger.info` (`turns_before` → `turns_after`); **não** mudar o JSON da API nesta entrega.

API sugerida do módulo (ajustar nomes, não espalhar):

```python
def prepare_graph_input(filename: str, content: bytes) -> str: ...
def prepare_graph_input_from_path(path: str) -> str: ...
```

### 2. Entrypoints — só duas chamadas

- [`backend/routers/analysis.py`](../../backend/routers/analysis.py): depois do `file.read()`, `entrada = prepare_graph_input(file.filename, content)` no lugar de `parse_file_content` direto. Manter o `except FileInputError` → 400.
- [`backend/main.py`](../../backend/main.py): `entrada = prepare_graph_input_from_path(caminho)` no lugar de `load_file_input`.

Não duplicar a lógica de detecção nos dois arquivos.

### 3. Instalação unidirecional

De `backend/`:

```bash
pip install -e ../transcript_cleaner
```

Opcional: uma linha em [`backend/requirements.txt`](../../backend/requirements.txt):

```text
-e ../transcript_cleaner
```

Isso **não** instala LangChain no cleaner. Não adicionar o backend ao `pyproject.toml` do cleaner.

### 4. Env

Em [`.env.example`](../../backend/.env.example):

```text
# 1 = limpa transcrições no entrypoint (sem LLM extra). 0 = texto bruto, como antes.
TRANSCRIPT_CLEAN=1
```

Não criar config no `agents_config.py`.

## Detecção de transcrição

Não inventar um segundo parser. Confiar no normalizador **já existente** do pacote (`speaker`/`text`/`falante`/`texto`/… e envelopes `segments`/`turns`/`utterances`). `NormalizeError` = não é transcrição = fallback.

Não usar o parser de `file_input.py` para “adivinhar” speakers.

## O que NÃO fazer (bloqueante)

- Importar `transcript_cleaner` em `agents/`, `graph/`, `schemas/`, `security.py`, `api.py`, `config/`, `file_input.py`.
- Adicionar node/edge de limpeza no LangGraph.
- Implementar `OllamaLlmClient` / etapas 3–4 com modelo nesta entrega (custo + acoplamento). Fica para um plano futuro, **no caller**, usando o `Protocol LlmClient` e o mesmo lock do Ollama — nunca dentro do pacote.
- Mudar prompts, `MAX_SPECIALISTS`, schema do card, frontend ou contrato de `POST /api/analysis/upload`.
- Golden set, `--with-llm` no CLI do pacote, UI de DROP, persistência.
- `sys.path` hack; copiar código do cleaner para `backend/`; fillers em `agents_config.py`.
- Exceção: se `clean_file` quebrar no meio **depois** de aceitar a transcrição, aí sim 400/500 — não engolir erro de pipeline como se fosse CSV genérico.

## Ordem de implementação

1. `prepare_analysis_input.py` + fallback `ImportError` / `NormalizeError` / `TRANSCRIPT_CLEAN=0`.
2. Trocar as duas linhas nos entrypoints.
3. `pip install -e ../transcript_cleaner` e linha no `.env.example` (+ README: uma frase “transcrições são limpas no upload, sem passar pelo grafo”).
4. Verificar à mão:
   - [`transcript_cleaner/tests/fixtures/meeting.json`](../../transcript_cleaner/tests/fixtures/meeting.json) → `input` do grafo tem `# Speakers` / `[P1]`, fillers reduzidos, **sem** `Hum, tipo`.
   - JSON/CSV **sem** coluna de fala → mesmo texto de hoje (`Arquivo de entrada: …` + bruto).
   - `TRANSCRIPT_CLEAN=0` → sempre bruto.
   - Pacote desinstalado → sempre bruto, análise sobe.

## Critério de pronto

- Grafo, agentes e card **bit-a-bit iguais** em código (exceto os dois entrypoints + módulo novo).
- `grep -r transcript_cleaner backend/agents backend/graph` → zero hits.
- `grep -r backend transcript_cleaner/transcript_cleaner` → zero hits.
- Análise de reunião usa texto limpo; arquivo genérico não quebra.

## Fora desta entrega (não começar)

- Adapter LLM no caller para KEEP/DROP via Ollama.
- Devolver `clean_stats` na API / UI.
- Flag query `?clean=` (o env basta).
- Testes de golden set do pacote (item ainda pending no plano do cleaner).
