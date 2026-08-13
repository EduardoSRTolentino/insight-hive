# Sistema Multiagente

Sistema multiagente (manager + especialistas, via LangGraph/Ollama) que analisa
arquivos `.csv`/`.json`, disponível tanto via terminal (`main.py`) quanto via
uma aplicação web com login (FastAPI + React).

## Pré-requisitos

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com/) rodando localmente, com o modelo em `OLLAMA_MODEL`
  (default `gpt-oss:20b`; ex.: `ollama pull gpt-oss:20b`)

## Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # ajuste as credenciais/segredo se quiser
uvicorn api:app --reload --port 8000
```

A API sobe em `http://localhost:8000`. Endpoints principais:

- `POST /api/auth/login` — recebe `username`/`password` (form) e retorna um token JWT.
- `POST /api/analysis/upload` — recebe um arquivo `.csv`/`.json` (multipart, campo `file`) autenticado via `Authorization: Bearer <token>`, roda o sistema multiagente e retorna o relatório final.
- Documentação interativa em `http://localhost:8000/docs`.

Usuário/senha padrão (definidos em `.env.example`): `admin` / `admin`.

## Limites do modelo local (`gpt-oss:20b`)

Cada análise faz **1 triagem + N especialistas + 1 síntese**, uma chamada atrás
da outra (o Ollama local não aguenta fan-out paralelo no mesmo modelo). O card
tem 6 eixos comerciais, mas o default **N = 2** para o 20B não estourar RAM.

| Variável | Default | Efeito |
|----------|---------|--------|
| `MAX_SPECIALISTS` | `2` | Quantos especialistas rodam. `2` = estável no 20B; `6` = cobertura total do card, só com hardware/modelo que aguente. |
| `NUM_PREDICT` | `512` | Teto de tokens da triagem e dos especialistas. |
| `NUM_PREDICT_SYNTHESIS` | `2048` | Teto da síntese do card (JSON aninhado). Precisa ser maior que `NUM_PREDICT` ou o card volta vazio. |
| `OLLAMA_MODEL` | `gpt-oss:20b` | Trocar por um modelo menor permite subir `MAX_SPECIALISTS`. |
| `OLLAMA_REASONING` | `low` | No gpt-oss, `medium`/`high` gasta o orçamento de tokens pensando e esvazia o card. |

Trade-off: **cobertura vs. estabilidade**. Com N=2 o card só preenche de fato os
agentes escolhidos na triagem (os outros campos caem em “Não identificado”).
Subir N sem mudar de modelo costuma gerar 503 ou JSON truncado. Depois de
alterar o `.env`, reinicie o uvicorn.

## Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

A aplicação sobe em `http://localhost:5173`. Faça login e envie um arquivo
`.csv` ou `.json` para acionar a análise multiagente e ver o relatório final.

## Uso via terminal (sem web)

```bash
cd backend
pip install -r requirements.txt
python main.py
```
