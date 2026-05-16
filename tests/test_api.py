from app.api.dependencies import get_workflow
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
