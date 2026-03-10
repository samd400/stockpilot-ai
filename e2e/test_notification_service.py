"""
E2E tests — Notification Service (port 8006)
Covers: webhook endpoints CRUD, notification logs, internal endpoints, health.
"""
import pytest
import httpx
from conftest import NOTIF_URL

created_endpoint_id = None


@pytest.fixture(scope="module")
def client(auth_headers):
    return httpx.Client(base_url=NOTIF_URL, headers=auth_headers, timeout=30)


def test_health():
    r = httpx.get(f"{NOTIF_URL}/health")
    assert r.status_code == 200
    assert r.json()["service"] == "notification-service"


def test_create_webhook_endpoint(client):
    global created_endpoint_id
    r = client.post("/webhooks/endpoints", json={
        "url": "https://webhook.site/e2e-test",
        "events": ["invoice.created", "stock.low"],
        "description": "E2E test webhook",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["url"] == "https://webhook.site/e2e-test"
    assert "invoice.created" in data["events"]
    created_endpoint_id = data["id"]


def test_list_webhook_endpoints(client):
    r = client.get("/webhooks/endpoints")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_update_webhook_endpoint(client):
    assert created_endpoint_id is not None
    r = client.patch(f"/webhooks/endpoints/{created_endpoint_id}", json={
        "description": "Updated E2E webhook",
        "is_active": True,
    })
    assert r.status_code == 200


def test_webhook_invalid_event(client):
    r = client.post("/webhooks/endpoints", json={
        "url": "https://example.com/hook",
        "events": ["invalid.event.name"],
    })
    assert r.status_code == 400


def test_notification_logs(client):
    r = client.get("/notifications/logs?limit=10")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_notification_stats(client):
    r = client.get("/notifications/stats")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_internal_sms_requires_service_token(service_headers):
    """Internal SMS endpoint must require service token."""
    r = httpx.post(f"{NOTIF_URL}/internal/notify/sms", json={
        "tenant_id": "00000000-0000-0000-0000-000000000000",
        "to_phone": "+919876543210",
        "message": "Test message",
    })
    assert r.status_code == 403  # No service token


def test_internal_sms_with_service_token(service_headers):
    r = httpx.post(
        f"{NOTIF_URL}/internal/notify/sms",
        json={
            "tenant_id": "00000000-0000-0000-0000-000000000001",
            "to_phone": "+919876543210",
            "message": "E2E test SMS",
        },
        headers=service_headers,
    )
    assert r.status_code == 200
    assert "queued" in r.json()["message"].lower()


def test_internal_webhook_broadcast(service_headers):
    r = httpx.post(
        f"{NOTIF_URL}/internal/notify/webhook",
        json={
            "tenant_id": "00000000-0000-0000-0000-000000000001",
            "event": "invoice.created",
            "data": {"invoice_id": "test-123", "amount": 1000},
        },
        headers=service_headers,
    )
    assert r.status_code == 200


def test_delete_webhook_endpoint(client):
    assert created_endpoint_id is not None
    r = client.delete(f"/webhooks/endpoints/{created_endpoint_id}")
    assert r.status_code == 200


def test_notification_requires_auth():
    r = httpx.get(f"{NOTIF_URL}/notifications/logs")
    assert r.status_code == 401
