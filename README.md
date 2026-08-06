# Sistema Multiagente

Sistema multiagente (manager + especialistas, via LangGraph/Ollama) que analisa
arquivos `.csv`/`.json`, disponível tanto via terminal (`main.py`) quanto via
uma aplicação web com login (FastAPI + React).

## Pré-requisitos

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com/) rodando localmente, com o modelo configurado em
  [`backend/config/agents_config.py`](backend/config/agents_config.py) já baixado (ex.: `ollama pull gpt-oss:20b`)

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
