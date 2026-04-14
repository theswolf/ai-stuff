# AI Engineer Starter Kit

Production‑oriented starter kit to experiment with Large Language Models (LLMs) end‑to‑end: API, RAG, agents, evaluation, and deployment.

This project turns the typical “LLM notebook” into a small, deployable **AI service** you can run locally, containerize, and extend.

---

## Features

- **LLM Chat API**
  - FastAPI service exposing `/chat` and `/chat/simple`
  - Provider‑agnostic client (OpenAI / Anthropic)
  - Optional streaming responses

- **Minimal RAG Service**
  - `RAGService` built with LangChain + Chroma
  - PDF / text ingest, persistent vector store
  - `POST /rag/query` and `GET /rag/stats` endpoints

- **Agent with Tool Calling**
  - OpenAI function calling–style agent loop
  - Tools: `calculator`, `get_weather`, `search_wikipedia`
  - Controlled iterations, tool call logging

- **MLOps Light & Evaluation**
  - `eval/evaluate_rag.py` for RAG quality + latency
  - `eval/evaluate_agent.py` for tool‑sequence correctness
  - JSON reports + optional Markdown reports

- **Production & Monitoring**
  - Dockerfile + `docker-compose.yml`
  - Prometheus metrics via `/metrics`
  - JSON structured logging + request middleware

- **Job Search Templates**
  - Outreach / cold email templates
  - Follow‑up templates
  - CSV tracker for applications

---

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **LLM Providers:** OpenAI, Anthropic
- **RAG:** LangChain, Chroma, FAISS, OpenAI embeddings
- **Infra & Observability:** Docker, docker‑compose, Prometheus
- **Evaluation & Tests:** requests, dataclasses, pytest (placeholder)

---

## Repository Structure

```bash
ai-engineer-starter-kit/
├── src/
│   ├── main.py              # FastAPI app (chat + RAG + agent + metrics)
│   ├── llm_client.py        # Provider‑agnostic LLM client
│   ├── tools.py             # calculator, get_weather, search_wikipedia
│   ├── agent_service.py     # agent loop using tool calling
│   ├── agent_router.py      # /agent/run endpoint
│   ├── rag_service.py       # RAGService with ingest + query
│   ├── rag_router.py        # /rag/ingest, /rag/query, /rag/stats
│   └── logging_config.py    # JSON logging + request middleware
├── eval/
│   ├── rag_eval_dataset.json
│   ├── agent_eval_dataset.json
│   ├── evaluate_rag.py
│   ├── evaluate_agent.py
│   ├── generate_rag_report_md.py
│   └── reports/             # generated JSON / Markdown reports
├── monitoring/
│   └── prometheus.yml       # Prometheus scrape config
├── templates/
│   ├── linkedin_message_role_open.txt
│   ├── cold_email.txt
│   ├── follow_up.txt
│   └── application_tracker.csv
├── tests/
│   └── test_basic.py
├── notebooks/
│   └── README.md            # placeholder for ML notebook from Chapter 1
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── .github/
    └── workflows/
        └── eval.yml         # CI evaluation workflow
```

---

## Getting Started

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

`.env`:

```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
LLM_PROVIDER=openai         # or "anthropic"
LLM_MODEL=gpt-4o-mini       # or e.g. "claude-3-5-haiku-20241022"
LOG_LEVEL=INFO
PORT=8000
WORKERS=2
```

### 3. Run locally

```bash
uvicorn src.main:app --reload --port 8000
```

API docs (Swagger UI):  
`http://localhost:8000/docs`

---

## API Overview

### Health

- `GET /health`  
  Simple health check for readiness/liveness probes.

### Chat

- `POST /chat`  
  Body:

  ```json
  {
    "messages": [
      { "role": "user", "content": "Count from 1 to 3." }
    ],
    "system_prompt": "You are a helpful assistant.",
    "stream": false
  }
  ```

- `POST /chat/simple`  
  Quick test endpoint:

  ```bash
  curl -X POST "http://localhost:8000/chat/simple?message=Hello"
  ```

### RAG

- `POST /rag/ingest`  
  Ingest a PDF or text file into the vector store:

  ```bash
  curl -X POST http://localhost:8000/rag/ingest \
    -F "file=@/path/to/document.pdf"
  ```

- `POST /rag/query`  

  ```json
  {
    "question": "What is FastAPI?",
    "k": 4,
    "return_sources": true
  }
  ```

- `GET /rag/stats`  
  Returns basic vector store stats (status, document count, collection name).

### Agent

- `POST /agent/run`  

  ```json
  {
    "message": "What's the weather like in Turin right now?"
  }
  ```

The agent may call:

- `calculator` – safe math evaluation
- `get_weather` – current weather via Open‑Meteo
- `search_wikipedia` – brief summary from Wikipedia

The response includes the final answer and the tool call log.

### Metrics

- `GET /metrics`  
  Prometheus‑compatible metrics for requests, latency, etc.

---

## Evaluation

### RAG Evaluation

Dataset: `eval/rag_eval_dataset.json`  
Script: `eval/evaluate_rag.py`

Run:

```bash
python eval/evaluate_rag.py
```

This will:

- send queries to `POST /rag/query`
- compute:
  - keyword hit rate
  - “contains expected phrase”
  - latency (ms, avg, p95)
- write a JSON report into `eval/reports/`

You can generate a Markdown report from a JSON file with:

```bash
python eval/generate_rag_report_md.py
```

(adjust paths as needed).

### Agent Evaluation

Dataset: `eval/agent_eval_dataset.json`  
Script: `eval/evaluate_agent.py`

Run:

```bash
python eval/evaluate_agent.py
```

This checks:

- whether the tool sequence matches the expected one
- whether the agent uses no more than `max_iterations`

Reports are saved under `eval/reports/`.

---

## Docker & docker‑compose

Build and run with Docker:

```bash
docker build -t ai-engineer-starter-kit .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-openai-key \
  ai-engineer-starter-kit
```

Using `docker-compose`:

```bash
docker-compose up --build
```

This spins up:

- `ai-service` on `localhost:8000`
- `prometheus` on `localhost:9090` (scraping `/metrics`)

---

## CI: GitHub Actions

The workflow in `.github/workflows/eval.yml`:

- installs dependencies
- starts the FastAPI service on CI
- runs:
  - `eval/evaluate_rag.py`
  - `eval/evaluate_agent.py`
- uploads the evaluation reports as artifacts

To enable it, set the following repository secrets:

- `OPENAI_API_KEY`
- (optional) `ANTHROPIC_API_KEY`

---

## Job Search Templates

The `templates/` folder contains:

- `linkedin_message_role_open.txt` – message template for open roles
- `cold_email.txt` – cold outreach email template
- `follow_up.txt` – follow‑up template
- `application_tracker.csv` – simple CSV to track applications

These are designed to complement this repository when you present it as part of your AI engineer profile.

---

## Possible Extensions

Some ideas to extend the kit:

- Add an internal `rag_query` tool so the agent can use the RAG service as a tool
- Add LLM‑as‑a‑judge evaluation for more nuanced quality scoring
- Plug in a real document set (e.g. API docs, internal knowledge base)
- Add a small frontend dashboard to interact with `/chat`, `/rag`, `/agent`

---

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.