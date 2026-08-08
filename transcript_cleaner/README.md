# transcript_cleaner

Módulo **independente** de limpeza e compressão de transcrições de reunião (JSON/CSV), pensado para reduzir tokens e ruído antes de qualquer LLM de análise.

Este README é o handoff para o próximo agente: contém contrato, isolamento, pipeline, API sugerida, integração futura e checklist de implementação.

---

## Contexto do repositório

O monorepo **insight-hive** hoje tem:

| Área | Papel |
|------|--------|
| `backend/` | FastAPI + LangGraph/Ollama: upload CSV/JSON → triagem → especialistas → relatório |
| `frontend/` | React: login + upload de arquivo |

**Não existe** domínio de reuniões, limpeza de transcrição nem schema de speakers/timestamps no código atual.

Pontos de referência do backend (somente leitura; **não importar daqui**):

- [`backend/file_input.py`](../backend/file_input.py) — parse genérico CSV/JSON para o grafo
- [`backend/routers/analysis.py`](../backend/routers/analysis.py) — `parse` → `compiled_graph.invoke`
- [`backend/agents/base.py`](../backend/agents/base.py) — `ChatOllama` / `invoke_agent`

Este pacote **não** reutiliza esses módulos.

---

## Requisitos de isolamento (obrigatório)

Isolamento **bidirecional**:

1. `transcript_cleaner` **não importa** nada de `backend/` (`agents`, `graph`, `routers`, `file_input`, `security`, `api`, `agents_config`).
2. `backend/` **não precisa** importar `transcript_cleaner` para continuar funcionando. Nenhuma mudança obrigatória no multiagente nesta fase.

```text
insight-hive/
├── backend/                 # multiagente (intocado por este pacote)
├── frontend/
└── transcript_cleaner/      # ESTE pacote (irmão da raiz)
    ├── README.md            # este arquivo
    ├── pyproject.toml       # ou requirements.txt próprio (opcional)
    ├── transcript_cleaner/  # código Python
    └── tests/
```

| Regra | Detalhe |
|-------|---------|
| Dependências | Preferir **stdlib**. Sem FastAPI, LangGraph, LangChain, PyJWT. |
| LLM (etapas 3–4) | Porta abstrata `LlmClient` **injetada pelo caller**. Sem cliente Ollama dentro do pacote. |
| Sem LLM | Se `llm_client=None`, rodar só etapas 1–2 + heurísticas determinísticas de DROP. |
| Config | Fillers, aliases, limiares **dentro deste pacote** (JSON/YAML próprios). |
| Testes | Suite própria; não sobe API nem grafo. |
| Uso | CLI `python -m transcript_cleaner ...` e/ou API Python pública. |

Composição futura com o insight-hive: **apenas** no ponto de entrada (ex.: uma linha no router ou um script wrapper). Nunca dentro de `agents/` ou `graph/`.

---

## Objetivo do pipeline

Entrada: arquivo **JSON** ou **CSV** com turnos de fala.  
Saída: texto (e/ou turns) otimizado para LLM — menos fillers, tags curtas, less small talk, opcionalmente resumido em blocos longos.

Preservar: decisões, ações, prazos, riscos, perguntas de negócio.  
Descartar com segurança: ruído mecânico de fala, saudações vazias, papo furado, concordâncias sem voto.

---

## Schema canônico

Normalizar qualquer entrada para:

```text
Turn {
  id: str | int         # estável na sessão de limpeza (para KEEP/DROP)
  speaker: str          # nome original; ausente → "UNKNOWN"
  text: str             # obrigatório
  start: str | null     # HH:MM:SS (opcional)
  end: str | null
}
```

### Aliases de campos (normalizador)

| Canônico | Aliases aceitos |
|----------|-----------------|
| `speaker` | `speaker`, `falante`, `nome`, `participant` |
| `text` | `text`, `texto`, `content`, `fala`, `transcript` |
| `start` | `start`, `inicio`, `timestamp`, `start_time` |
| `end` | `end`, `fim`, `end_time` |

### Formatos de arquivo

**CSV:** cabeçalho com aliases; uma linha = um turno.

**JSON:**

- array de objetos: `[{ "speaker", "text", "start?", "end?" }, ...]`, ou
- envelope: `{ "segments": [ ... ] }` (aceitar também `turns` / `utterances` se fizer sentido)

Validação:

- Sem coluna/campo `text` (após aliases) → erro claro.
- `speaker` ausente → `"UNKNOWN"`.
- UTF-8 (aceitar BOM).

---

## Fluxo das 4 etapas

```text
JSON/CSV bruto
    │
    ▼
[0. Normalizador]     → Turn[]
    │
    ▼
[1. Limpeza regex]    → fillers, gagueiras, whitespace, artefatos ASR
    │
    ▼
[2. Formatador]       → speaker map P1..Pn, timestamps, merge consecutivos
    │
    ▼
[3. Filtro conteúdo]  → heurísticas + LLM classificador KEEP/DROP (opcional)
    │
    ▼
[4. Sumarização]      → só se reunião longa / muitos tokens (opcional, precisa LLM)
    │
    ▼
CleanResult (texto + turns + stats)
```

Custo: etapas 1–2 baratas e determinísticas; 3–4 só com `LlmClient`.

---

### Etapa 1 — Limpeza textual (regex + dicionários)

Por cada `Turn.text`:

1. Remover fillers PT-BR **como tokens isolados** (não substrings): ex. `hum`, `hã`, `éé`, `tipo`, `né`, `tá ligado`, `ahh`, `uhm`; `então`/`assim` só quando claramente filler isolado. Lista em config versionável.
2. Colapsar gagueiras: `nós nós vamos` → `nós vamos`; bigramas repetidos (`a gente a gente`).
3. Colapsar whitespace; trim; remover linhas vazias.
4. Remover artefatos ASR por padrão: `[inaudível]`, `(risos)`, etc. (flag para manter `[inaudível]` se necessário).

**Não alterar:** números, URLs, códigos, nomes próprios embutidos.

---

### Etapa 2 — Metadados e formato

1. Mapa estável: `João Silva` → `P1`, … Cabeçalho único `P1=João Silva`.
2. Timestamps → `HH:MM:SS` (sem ms). Em turnos mesclados, manter só o `start` do primeiro.
3. Mesclar falas **consecutivas** do mesmo speaker (texto juntado por espaço).
4. Serialização preferida:

```text
# Speakers
P1=João Silva
P2=Maria Souza

[P1] 00:01:12 Conteúdo mesclado...
[P2] 00:01:40 Resposta...
```

Não gerar prosa do tipo “O participante João disse que…”.

---

### Etapa 3 — Filtro de conteúdo não essencial

Entrada: turns já formatados (não o arquivo bruto).

**Heurísticas pré-IA (sempre, mesmo sem LLM):**

- Turnos curtos (≤ ~3 tokens) em lista de concordância (`sim`, `entendi`, `uhum`, `com certeza`, …) → `DROP` (exceto se contexto indicar votação — na dúvida com LLM, ou `KEEP` se sem LLM e ambíguo).
- Primeiros/últimos K turnos matching saudação/despedida → candidatos a `DROP`.

**Com LLM:** classificar candidatos ambíguos (+ vizinhos) como `KEEP` | `DROP`.

- `KEEP`: decisão, ação, risco, pergunta de negócio, conteúdo substantivo.
- `DROP`: saudação, clima, fim de semana, “mic mudo”, “pode falar?”, concordância vazia — **exceto** voto/decisão formal.

Contrato de resposta do LLM: **somente** JSON de labels, ex.:

```json
[{"turn_id": "12", "label": "DROP"}, {"turn_id": "13", "label": "KEEP"}]
```

O LLM **não reescreve** o texto. Remoção é aplicada no código após o parse.

Política de erro: se o JSON do LLM falhar, tratar candidatos ambíguos como `KEEP` (preferir ruído a apagar decisão).

---

### Etapa 4 — Sumarização intermediária (opcional)

Disparar se **qualquer** limiar (configurável):

- duração estimada &gt; ~2h, **ou**
- tokens estimados do texto pós-etapa-3 &gt; ~8k–12k

Procedimento:

1. Particionar por tempo (~10 min) ou por N turns.
2. Com `LlmClient`, resumir cada bloco: tópicos densos + decisões + action items (`quem`, `o quê`, `prazo`).
3. Manter dissenso relevante em 1–2 frases; descartar debate longo sem mudança de conclusão.
4. Concatenar resumos + speaker map → `cleaned_text` final.

Sem LLM ou abaixo do limiar: pular.

---

## API pública sugerida

```python
from typing import Protocol, Any

class LlmClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Retorna texto bruto do modelo (esperado: JSON nas etapas 3–4)."""
        ...

class Turn(TypedDict):
    id: str
    speaker: str
    text: str
    start: str | None
    end: str | None

class CleanResult(TypedDict):
    cleaned_text: str
    cleaned_turns: list[Turn]
    speaker_map: dict[str, str]   # {"P1": "João Silva", ...}
    stats: dict[str, Any]         # ver abaixo

def clean_file(
    source: str | bytes,          # path ou conteúdo
    *,
    format: str | None = None,    # "json" | "csv" | inferir pela extensão/conteúdo
    llm_client: LlmClient | None = None,
    config: dict | None = None,
) -> CleanResult: ...

def clean_turns(
    turns: list[Turn],
    *,
    llm_client: LlmClient | None = None,
    config: dict | None = None,
) -> CleanResult: ...
```

### `stats` mínimo

```json
{
  "chars_before": 0,
  "chars_after": 0,
  "turns_before": 0,
  "turns_after": 0,
  "turns_dropped": 0,
  "stage4_used": false,
  "llm_used": false
}
```

Exportar no `__init__.py` só: `clean_file`, `clean_turns`, `CleanResult`, `Turn`, `LlmClient` (Protocol).

---

## CLI sugerido

```bash
# Só etapas 1–2 (+ heurísticas)
python -m transcript_cleaner input.json -o cleaned.txt

# Com LLM (adapter fornecido pelo caller / flag futura)
python -m transcript_cleaner input.csv -o cleaned.txt --with-llm
```

Imprimir stats no stderr ou com `--stats`.

---

## Integração futura com o backend (para o próximo agente)

Quando for plugar no insight-hive, **sem quebrar o isolamento do núcleo**:

### Opção recomendada (cola fina)

No ponto de entrada apenas — tipicamente [`backend/routers/analysis.py`](../backend/routers/analysis.py) e/ou [`backend/main.py`](../backend/main.py):

```text
arquivo upload
  → (opcional) transcript_cleaner.clean_file(...)
  → montar string de input do grafo
  → compiled_graph.invoke(...)
```

Regras:

- **Não** importar `transcript_cleaner` de dentro de `agents/` ou `graph/`.
- **Não** mover `ChatOllama` para dentro do cleaner; se etapas 3–4 forem usadas na API, implementar um adapter fino no **caller**:

```python
# Exemplo de adapter NO CALLER (backend ou script), não no pacote
class OllamaLlmClient:
    def complete(self, prompt: str) -> str:
        # usa langchain_ollama / httpx / o que o backend já tiver
        ...
```

- Detectar “é transcrição?” por schema (colunas speaker/text) ou flag/query param; se for CSV analítico genérico, **não** passar pelo cleaner.
- Manter `file_input.parse_file_content` para o fluxo atual de análise genérica; o cleaner tem parser **próprio**.

### O que NÃO fazer

- Adicionar dependência de LangGraph/LangChain em `transcript_cleaner`.
- Colocar fillers em `agents_config.py`.
- Fazer o grafo multiagente “conhecer” etapas de limpeza como nodes internos (a menos que se abandone o isolamento — fora do escopo acordado).
- Alterar contratos da API existentes sem necessidade (`/api/analysis/upload` pode ganhar flag depois).

---

## Layout de arquivos sugerido

```text
transcript_cleaner/
├── README.md                 # este handoff
├── pyproject.toml            # nome do pacote, python>=3.11
├── transcript_cleaner/
│   ├── __init__.py           # API pública
│   ├── __main__.py           # CLI
│   ├── models.py             # Turn, CleanResult
│   ├── normalize.py          # JSON/CSV → Turn[]
│   ├── stage1_text.py        # regex / fillers
│   ├── stage2_format.py      # speakers, merge, serialize
│   ├── stage3_filter.py      # heurísticas + classificação
│   ├── stage4_summarize.py   # compressão por blocos
│   ├── pipeline.py           # orquestra clean_file / clean_turns
│   ├── llm.py                # Protocol LlmClient apenas
│   └── data/
│       ├── fillers_pt.json
│       ├── greetings_pt.json
│       └── acknowledgements_pt.json
└── tests/
    ├── test_normalize.py
    ├── test_stage1.py
    ├── test_stage2.py
    ├── test_stage3_heuristics.py
    ├── test_pipeline.py
    └── fixtures/
        ├── sample.json
        └── sample.csv
```

---

## Ordem de implementação sugerida

1. Pacote + `models` + `normalize` (JSON/CSV) + fixtures.
2. Etapa 1 + etapa 2 + `pipeline` sem LLM + CLI + testes.
3. Heurísticas etapa 3; depois classificação via `LlmClient` opcional.
4. Etapa 4 com limiares em config.
5. (Separado) cola opcional no insight-hive no ponto de entrada — **outro PR**, se desejado.

---

## Validação / golden set

- 5–10 reuniões anotadas: labels `KEEP`/`DROP` + lista de action items que **não podem** sumir.
- Unit tests etapas 1–2 (determinísticas).
- Etapa 3: priorizar **baixo falso-DROP** (melhor deixar ruído).
- Medir `chars_before` → `chars_after` e amostrar before/after.

KPIs alvo: redução típica 30–60% de tokens; etapas 1–2 &lt; ~1s em arquivos médios.

---

## Fora de escopo

- Persistência / DB de reuniões
- ASR / diarização (entrada já é texto estruturado)
- UI de revisão humana de `DROP`
- Mudanças nos agentes especialistas ou no grafo LangGraph
- Imports cruzados com o backend multiagente

---

## Checklist rápido para o agente implementador

- [ ] Criar pacote em `transcript_cleaner/` (raiz), isolado
- [ ] Zero imports de `backend/`
- [ ] `clean_file` / `clean_turns` + `CleanResult` + stats
- [ ] Normalizador com aliases documentados
- [ ] Etapas 1–2 com listas PT-BR em `data/`
- [ ] `LlmClient` Protocol; etapas 3–4 no-op/heurística sem client
- [ ] CLI `python -m transcript_cleaner`
- [ ] Testes + fixtures JSON/CSV
- [ ] Não alterar `agents/`, `graph/`, `routers/`, `file_input.py` neste escopo
- [ ] Integração com insight-hive só depois, com cola fina no entrypoint + adapter LLM no caller
