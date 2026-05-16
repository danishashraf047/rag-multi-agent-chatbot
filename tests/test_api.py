from app.api.dependencies import get_vector_store, get_workflow
from app.main import create_app
from app.models import AgentRoute, ChatResponse
from fastapi.testclient import TestClient


class FakeWorkflow:
    async def ainvoke(self, message: str, session_id: str) -> ChatResponse:
        return ChatResponse(
            session_id=session_id,
            route=AgentRoute.CODING,
            response=f"handled: {message}",
            agent_outputs=[],
        )


class FakeVectorStore:
    async def ingest_file_content(self, filename: str, content: bytes, content_type: str | None):
        assert filename == "notes.md"
        assert b"LangGraph" in content
        assert content_type in {"text/markdown", "text/plain"}
        return 2


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ui_index_is_served():
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "Agent Console" in response.text


def test_chat_endpoint_with_dependency_override():
    app = create_app()
    app.dependency_overrides[get_workflow] = lambda: FakeWorkflow()
    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={"message": "Write a FastAPI route", "session_id": "test-session"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "coding"
    assert body["response"] == "handled: Write a FastAPI route"


def test_rag_file_upload_endpoint_with_dependency_override():
    app = create_app()
    app.dependency_overrides[get_vector_store] = lambda: FakeVectorStore()
    client = TestClient(app)

    response = client.post(
        "/api/v1/rag/ingest/file",
        files={"file": ("notes.md", b"LangGraph routes agents.", "text/markdown")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["indexed_documents"] == 2
