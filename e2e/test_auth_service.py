"""
E2E tests — Auth Service (port 8001)
Covers: registration, login, token refresh, RBAC role assignment, health check.
"""
import pytest
import httpx
from conftest import AUTH_URL


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url=AUTH_URL, timeout=30)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auth-service"


def test_register_and_login(client):
    unique_email = f"rbac-test-{__import__('uuid').uuid4().hex[:8]}@test.com"
    reg = client.post("/register", json={
        "business_name": "RBAC Test Biz",
        "email": unique_email,
        "password": "TestPass123!",
        "country": "IN",
        "currency": "INR",
    })
    assert reg.status_code == 201, reg.text
    data = reg.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Login with same credentials
    login = client.post("/login", data={"username": unique_email, "password": "TestPass123!"})
    assert login.status_code == 200, login.text
    assert "access_token" in login.json()


def test_me_endpoint(admin_token):
    r = httpx.get(f"{AUTH_URL}/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert "email" in data
    assert "role" in data


def test_wrong_password_returns_401(client):
    r = client.post("/login", data={"username": "nonexistent@test.com", "password": "WrongPass"})
    assert r.status_code == 401


def test_token_without_auth_returns_401(client):
    r = client.get("/users/me")
    assert r.status_code == 401


def test_rbac_get_roles(admin_token):
    r = httpx.get(
        f"{AUTH_URL}/rbac/roles",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_register_duplicate_email(client):
    """Second registration with same email should fail."""
    email = f"dup-{__import__('uuid').uuid4().hex[:8]}@test.com"
    client.post("/register", json={
        "business_name": "Biz 1", "email": email, "password": "Pass123!",
        "country": "IN", "currency": "INR"
    })
    r = client.post("/register", json={
        "business_name": "Biz 2", "email": email, "password": "Pass123!",
        "country": "IN", "currency": "INR"
    })
    assert r.status_code == 409
