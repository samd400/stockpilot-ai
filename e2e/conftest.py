"""
Shared fixtures for E2E tests across all microservices.
Tests run against the running Docker Compose stack.
"""
import os
import pytest
import httpx

# Service base URLs — match docker-compose ports
AUTH_URL      = os.getenv("AUTH_URL",         "http://localhost:8001")
INVENTORY_URL = os.getenv("INVENTORY_URL",    "http://localhost:8002")
BILLING_URL   = os.getenv("BILLING_URL",      "http://localhost:8003")
CRM_URL       = os.getenv("CRM_URL",          "http://localhost:8004")
AI_URL        = os.getenv("AI_URL",           "http://localhost:8005")
NOTIF_URL     = os.getenv("NOTIF_URL",        "http://localhost:8006")

# Test credentials (created before tests via /auth/register)
TEST_EMAIL    = "e2e-test@stockpilot.test"
TEST_PASSWORD = "E2ETestPass123!"
TEST_BIZ      = "E2E Test Business"


@pytest.fixture(scope="session")
def admin_token():
    """Register (or re-use) a test tenant and return admin JWT."""
    client = httpx.Client(base_url=AUTH_URL, timeout=30)

    # Try registration
    reg = client.post("/register", json={
        "business_name": TEST_BIZ,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "country": "IN",
        "currency": "INR",
    })

    # If already registered, just login
    login = client.post("/login", data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
    login.raise_for_status()
    return login.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def service_headers():
    service_token = os.getenv("SERVICE_TOKEN", "internal-service-secret-change-me")
    return {"X-Service-Token": service_token}
