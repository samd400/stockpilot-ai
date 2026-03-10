"""
E2E tests — CRM Service (port 8004)
Covers: customer CRUD, loyalty points, tiers, order management.
"""
import pytest
import httpx
from conftest import CRM_URL

created_customer_id = None


@pytest.fixture(scope="module")
def client(auth_headers):
    return httpx.Client(base_url=CRM_URL, headers=auth_headers, timeout=30)


def test_health():
    r = httpx.get(f"{CRM_URL}/health")
    assert r.status_code == 200
    assert r.json()["service"] == "crm-service"


def test_create_customer(client):
    global created_customer_id
    r = client.post("/customers/", json={
        "name": "E2E Customer",
        "email": "e2ecustomer@test.com",
        "phone": "+919876543210",
        "city": "Bangalore",
        "country": "IN",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["name"] == "E2E Customer"
    created_customer_id = data["id"]


def test_list_customers(client):
    r = client.get("/customers/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_customer(client):
    assert created_customer_id is not None
    r = client.get(f"/customers/{created_customer_id}")
    assert r.status_code == 200
    assert r.json()["id"] == created_customer_id


def test_add_loyalty_points(client):
    assert created_customer_id is not None
    r = client.post(f"/customers/{created_customer_id}/loyalty/add", json={
        "points": 500,
        "reason": "E2E purchase",
        "invoice_id": None,
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["points_added"] == 500
    assert data["total_points"] >= 500


def test_loyalty_tier_promotion(client):
    """Adding 1000+ points should push customer to Silver tier."""
    assert created_customer_id is not None
    client.post(f"/customers/{created_customer_id}/loyalty/add", json={
        "points": 600, "reason": "Tier test"
    })
    r = client.get(f"/customers/{created_customer_id}/loyalty")
    assert r.status_code == 200
    data = r.json()
    assert data["total_points"] >= 1000
    assert data["tier"] in ("silver", "gold", "platinum")


def test_redeem_loyalty_points(client):
    assert created_customer_id is not None
    r = client.post(f"/customers/{created_customer_id}/loyalty/redeem", json={
        "points": 100,
        "reason": "E2E redemption",
    })
    assert r.status_code == 200, r.text


def test_search_customers(client):
    r = client.get("/customers/?search=E2E")
    assert r.status_code == 200
    results = r.json()
    assert any("E2E" in c["name"] for c in results)


def test_customer_not_found(client):
    r = client.get("/customers/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_crm_requires_auth():
    r = httpx.get(f"{CRM_URL}/customers/")
    assert r.status_code == 401
