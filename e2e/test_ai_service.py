"""
E2E tests — AI Service (port 8005)
Covers: agent registration, sync trigger, audit logs, assistant chat, health check.
Note: These tests verify the agentic loop infrastructure, not Gemini responses (which require live API key).
"""
import pytest
import httpx
from conftest import AI_URL


@pytest.fixture(scope="module")
def client(auth_headers):
    return httpx.Client(base_url=AI_URL, headers=auth_headers, timeout=120)


def test_health():
    r = httpx.get(f"{AI_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-service"
    # All 5 agents should be registered
    assert "registered_agents" in data
    assert "stock_agent" in data["registered_agents"]
    assert "profit_agent" in data["registered_agents"]
    assert "pricing_agent" in data["registered_agents"]
    assert "insight_agent" in data["registered_agents"]
    assert "compliance_agent" in data["registered_agents"]


def test_list_agents(client):
    r = client.get("/agents/")
    assert r.status_code == 200
    agents = r.json()
    assert isinstance(agents, list)
    agent_names = [a["name"] for a in agents]
    assert "stock_agent" in agent_names


def test_trigger_stock_agent_async(client):
    """Trigger stock agent as background task — should return task ID."""
    r = client.post("/agents/run/stock_agent")
    assert r.status_code in (200, 202), r.text
    data = r.json()
    assert "task_id" in data or "status" in data


def test_get_agent_status(client):
    r = client.get("/agents/status/stock_agent")
    assert r.status_code == 200


def test_get_audit_logs(client):
    r = client.get("/agents/audit-logs?limit=10")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_assistant_chat(client):
    """Test the business assistant chat endpoint."""
    r = client.post("/assistant/chat", json={
        "message": "What is my current stock situation?",
        "conversation_history": [],
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0


def test_assistant_multi_turn(client):
    """Test multi-turn conversation."""
    history = [{"role": "user", "content": "What are my top selling products?"}]
    r = client.post("/assistant/chat", json={
        "message": "And what about the revenue last month?",
        "conversation_history": history,
    })
    assert r.status_code == 200, r.text


def test_ai_requires_auth():
    r = httpx.get(f"{AI_URL}/agents/")
    assert r.status_code == 401
