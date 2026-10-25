from fastapi.testclient import TestClient

from app import agent
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_endpoint(monkeypatch):
    # Agent ko mock karte hain — CI me LLM call nahi (fast, free, deterministic)
    monkeypatch.setattr(agent, "chat", lambda msg, tid: {"answer": f"echo: {msg}", "tool_calls": [],
                                                          "tools_executed": [], "thread_id": tid})
    r = client.post("/chat", json={"message": "hello", "thread_id": "t1"})
    assert r.status_code == 200
    assert r.json()["answer"] == "echo: hello"


def test_ui_served():
    assert client.get("/").status_code == 200
