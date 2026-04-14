# AI Engineer Starter Kit

Stack end-to-end per sperimentare con LLM in produzione.

## Include

- Endpoint `/chat` con LLM astratto (OpenAI/Anthropic)
- RAG minimo con ingest PDF/txt e vector store persistente
- Agent con tool calling (`calculator`, `get_weather`, `search_wikipedia`)
- Script di evaluation per RAG e agent
- Docker, docker-compose e metriche Prometheus
- Template operativi per outreach e tracking candidature

## Tech stack

- Python, FastAPI, Uvicorn
- OpenAI / Anthropic
- LangChain, Chroma, FAISS
- Docker, Prometheus
- Requests, pytest

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn src.main:app --reload --port 8000
```

## Endpoint

- `GET /health`
- `POST /chat`
- `POST /chat/simple`
- `POST /rag/ingest`
- `POST /rag/query`
- `GET /rag/stats`
- `POST /agent/run`
- `GET /metrics`

## Perché questo repo

Questo starter kit riflette i deliverable descritti nel documento di riferimento: servizio `/chat`, `rag_service`, `agent_service`, script di valutazione, containerizzazione e materiale operativo per branding e job search.
