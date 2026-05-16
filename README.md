# LangGraph Multi-Agent RAG Chatbot

Production-ready Python 3.12 FastAPI project for a LangGraph-orchestrated multi-agent AI system using LangChain agents, OpenAI models, ChromaDB, structured Pydantic outputs, conversation memory, retries, tool calling, streaming responses, and optional LangSmith tracing.

## Architecture

Request flow:

```text
User Request -> Supervisor -> Specialized Agent -> Shared State/Memory -> Final Aggregation -> Response
```

Agents:

- `SupervisorAgent`: classifies intent, rewrites the query, and selects a route.
- `ResearchAgent`: uses document and URL tools to gather and summarize findings.
- `CodingAgent`: generates/reviews Python or React code and can inspect project files.
- `RAGAgent`: retrieves ChromaDB chunks and answers with citations.
- `PlanningAgent`: breaks complex work into subtasks and delegates by agent type.

The LangGraph routing is implemented in [app/graph/workflow.py](/Users/danish/Documents/Projects/rag-multi-agent-chatbot/app/graph/workflow.py). The important bit is the conditional edge after the supervisor node: the supervisor writes `state["route"]`, and LangGraph sends the same shared state to `research`, `coding`, `rag`, `planning`, or `direct`.

## macOS Setup With pyenv

Install Homebrew if needed, then:

```bash
brew update
brew install pyenv
```

Add pyenv to your shell:

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
exec zsh
```

Install Python 3.12 and create the virtual environment:

```bash
pyenv install 3.12.9
pyenv local 3.12.9
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Configure environment:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=agent_knowledge
DOCUMENTS_DIR=./data/documents
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=rag-multi-agent-chatbot
```

## Run Locally

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

## Example API Requests

Health check:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

General chat through the supervisor:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "Create a plan to build a React dashboard backed by FastAPI"
  }'
```

Test the Planning Agent:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-planning",
    "message": "Create a step-by-step execution plan for building a React dashboard with a FastAPI backend, authentication, tests, and deployment"
  }'
```

Test the Coding Agent:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-coding",
    "message": "Write a Python FastAPI endpoint that accepts a user message and returns a JSON response. Explain the implementation."
  }'
```

Test the Research Agent:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-research",
    "message": "Research FastAPI deployment options and summarize the tradeoffs"
  }'
```

Streaming:

```bash
curl -N -X POST http://127.0.0.1:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "Research FastAPI deployment options and summarize the tradeoffs"
  }'
```

Ingest text into ChromaDB:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "LangGraph orchestrates stateful multi-agent workflows using nodes, edges, and shared graph state."
    ],
    "metadatas": [
      {"source": "manual-note", "title": "LangGraph note"}
    ]
  }'
```

Test the RAG Agent:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "Using the indexed knowledge base, what is LangGraph used for?"
  }'
```

Ingest the included sample knowledge file:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"paths": ["data/documents/sample-knowledge.md"]}'
```

Then ask a sample knowledge-base question:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sample-rag",
    "message": "Using the knowledge base, what does LangGraph do in this project?"
  }'
```

Upload and ingest a file from the UI:

1. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).
2. Use `Knowledge base -> Ingest file` in the left sidebar.
3. Select a text-like file, then click `Ingest for RAG`.
4. Ask a knowledge-base question in chat.

Upload and ingest a file with curl:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/ingest/file \
  -F "file=@data/documents/sample-knowledge.md"
```

Supported upload types include `.txt`, `.md`, `.py`, `.js`, `.ts`, `.json`, `.csv`, `.yaml`, `.html`, and `.css`. The default upload limit is 2 MB.

The Supervisor Agent chooses the route automatically. In each `/chat` response, check the `route` field to confirm whether LangGraph sent the request to `planning`, `coding`, `research`, `rag`, or `direct`.

## VS Code Debugging

This repo includes shared VS Code debugger settings in `.vscode/`.

Recommended extensions:

- Python
- Pylance

Setup:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Make sure `.env` contains a real `OPENAI_API_KEY`.

In VS Code:

1. Open the project folder.
2. Select the Python interpreter at `.venv/bin/python`.
3. Open Run and Debug.
4. Choose `FastAPI: Debug app`.
5. Press Start Debugging.

Available debug configurations:

- `FastAPI: Debug app`: starts `uvicorn app.main:app --reload` on `127.0.0.1:8000`.
- `Pytest: Current file`: debugs the currently open test file.
- `Pytest: All tests`: debugs the full test suite.

Useful breakpoint locations:

- `app/graph/workflow.py`: `_supervisor`, `_route_from_state`, and `_aggregate`
- `app/agents/supervisor.py`: `decide`
- `app/agents/rag_agent.py`: `run`
- `app/api/routes.py`: `chat` and `chat_stream`

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at [http://localhost:8000](http://localhost:8000). Chroma data is persisted in `./chroma_db`.

## Tests

```bash
source .venv/bin/activate
pytest
```

The included unit tests avoid live OpenAI calls by overriding FastAPI dependencies where needed.

## Project Structure

```text
project-root/
├── app/
│   ├── agents/
│   ├── api/
│   ├── config/
│   ├── graph/
│   ├── memory/
│   ├── rag/
│   ├── static/
│   ├── tools/
│   └── main.py
├── data/documents/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Production Notes

- Set `APP_ENV=production` and `LOG_LEVEL=INFO` or `WARNING` in deployed environments.
- Enable LangSmith tracing with `LANGSMITH_TRACING=true` plus `LANGSMITH_API_KEY`.
- Use a persistent disk for `CHROMA_PERSIST_DIR`.
- Put external web access behind allowlists if your deployment handles sensitive data.
- Replace in-process conversation memory with Redis or Postgres if you run multiple API replicas.

## Author

Danish Ashraf · danish.ashraf@codehills.net · https://codehills.net
