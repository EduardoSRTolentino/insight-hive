# Sistema Multiagente

Sistema multiagente (manager + especialistas, via LangGraph/Ollama) que analisa
arquivos `.csv`/`.json`, disponível tanto via terminal (`main.py`) quanto via
uma aplicação web com login (FastAPI + React/Vite).

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recomendado), **ou** Python 3.11+ e Node.js 18+
- [Ollama](https://ollama.com/) com o modelo em `OLLAMA_MODEL` (default `gpt-oss:20b`;
  ex.: `ollama pull gpt-oss:20b`). No **dev** o Ollama roda na máquina; no **prod**
  ele sobe como container (veja Docker abaixo).

## Docker

Copie o env do backend se ainda não existir:

```bash
cp backend/.env.example backend/.env
```

**Desenvolvimento** (hot-reload; frontend e backend em containers; Ollama na máquina):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

A UI fica em `http://localhost:5173`. A API/Swagger em `http://localhost:8000/docs`.
O Ollama precisa estar rodando no host (`http://127.0.0.1:11434`). O SQLite continua
em `backend/data/` no seu disco.

**Produção** (imagens fechadas; Ollama também em container; SQLite num volume Docker):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec ollama ollama pull gpt-oss:20b
```

A UI fica em `http://localhost:5173`. O backend não é publicado na máquina — o nginx
faz proxy de `/api` para o container `backend`. Na primeira vez o `ollama pull` baixa
o modelo (pode ser grande). No servidor com GPU NVIDIA, descomente `gpus: all` em
`docker-compose.prod.yml`.

Para parar: `docker compose -f docker-compose.yml -f docker-compose.dev.yml down`
(ou o par `prod`). O volume `backend_data` da produção persiste clientes e reuniões.

## Backend (FastAPI) — sem Docker

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # ajuste as credenciais/segredo se quiser
uvicorn api:app --reload --port 8000
```

A API sobe em `http://localhost:8000`. Endpoints principais:

- `POST /api/auth/login` — recebe `username`/`password` (form) e retorna um token JWT.
- `GET/POST /api/clients` — lista e cria clientes. `GET /api/clients/{id}` devolve o histórico de reuniões.
- `GET/DELETE /api/meetings/{id}` — consulta ou remove uma análise salva.
- `POST /api/analysis/upload` — recebe `client_id` (form) e um arquivo `.csv`/`.json` (multipart, campo `file`) autenticado via `Authorization: Bearer <token>`, roda o sistema multiagente, **salva a análise no cliente** e retorna o relatório final. Transcrições são limpas no upload, sem passar pelo grafo.
- Documentação interativa em `http://localhost:8000/docs`.

Análises ficam em SQLite (`backend/data/insight_hive.db`, gitignored; `DATABASE_URL` no `.env`).
O schema é versionado com Alembic: o lifespan da API aplica `alembic upgrade head`
(ou `stamp head` se o banco local já existia sem tabela de versão). Sem o servidor:

```bash
cd backend
alembic upgrade head
```

Usuário/senha padrão (definidos em `.env.example`): `admin` / `admin`.

## Catálogo TOTVS (agente Ecossistema)

O especialista `ecossistema_totvs` consulta um catálogo estruturado gerado a
partir da taxonomia pública de [produtos.totvs.com](https://produtos.totvs.com)
(API WordPress). A homepage totvs.com não lista o portfólio.

Para atualizar o CSV/JSON versionados em `backend/catalog/data/`:

```bash
cd backend
pip install -r requirements.txt -r requirements-scrape.txt
python -m catalog.scrape
```

O scraper usa `requests` + `beautifulsoup4` (sem Playwright); esses pacotes **não**
entram na imagem da API. Fonte primária:
`GET /wp-json/wp/v2/produto`. Páginas HTML só entram quando a API não traz
descrição (`h1` + primeiro `p`). Reinicie o backend depois de re-scrapar para
o gazetteer e o matcher lerem o JSON novo.

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
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | URL do Ollama. No Docker o Compose define o valor certo. |
| `OLLAMA_REASONING` | `low` | No gpt-oss, `medium`/`high` gasta o orçamento de tokens pensando e esvazia o card. |
| `TRANSCRIPT_CLEAN` | `1` | Limpa transcrições no entrypoint (sem LLM extra). `0` envia o texto bruto, como antes. |
| `MAX_UPLOAD_BYTES` | `5242880` | Teto do arquivo em `POST /api/analysis/upload` (5 MiB). Acima disso a API responde 413. |

Trade-off: **cobertura vs. estabilidade**. Com N=2 o card só preenche de fato os
agentes escolhidos na triagem (os outros campos caem em “Não identificado”).
Subir N sem mudar de modelo costuma gerar 503 ou JSON truncado. Depois de
alterar o `.env`, reinicie o uvicorn.

## Frontend (Vite) — sem Docker

```bash
cd frontend
npm install
npm run dev
```

A aplicação sobe em `http://localhost:5173`. Faça login, escolha (ou crie) um
cliente, envie um arquivo `.csv` ou `.json` e acompanhe o histórico em
**Clientes**.

## Testes

Backend (pytest, sem Ollama). A partir de `backend/`:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

O `transcript_cleaner` tem suíte própria:

```bash
cd transcript_cleaner
pip install -e ".[dev]"
pytest
```

Frontend:

```bash
cd frontend
npm install
npm test
npm run lint
npm run typecheck
```

## Uso via terminal (sem web)

```bash
cd backend
pip install -r requirements.txt
python main.py
```
