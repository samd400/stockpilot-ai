"""
E2E tests — Billing Service (port 8003)
Covers: invoice creation with tax, PDF, payments, expenses, GDPR export, GST report.
"""
import pytest
import httpx
from conftest import BILLING_URL

created_invoice_id = None


@pytest.fixture(scope="module")
def client(auth_headers):
    return httpx.Client(base_url=BILLING_URL, headers=auth_headers, timeout=60)


def test_health():
    r = httpx.get(f"{BILLING_URL}/health")
    assert r.status_code == 200
    assert r.json()["service"] == "billing-service"


def test_create_invoice_india_gst(client):
    """Create a B2B GST invoice for India."""
    global created_invoice_id
    r = client.post("/invoices/", json={
        "customer_name": "E2E Customer Pvt Ltd",
        "customer_email": "e2e@customer.com",
        "customer_gstin": "22AAAAA0000A1Z5",
        "customer_state": "Maharashtra",
        "region": "india",
        "items": [
            {
                "product_name": "Laptop",
                "sku": "LAP-001",
                "quantity": 2,
                "unit_price": 50000.0,
                "gst_percentage": 18.0,
                "hsn_code": "8471",
            }
        ],
        "currency": "INR",
        "notes": "E2E test invoice",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert "id" in data
    assert data["currency"] == "INR"
    assert data["tax_amount"] > 0  # GST must be calculated
    created_invoice_id = data["id"]


def test_create_invoice_gcc_vat(client):
    """Create a VAT invoice for UAE."""
    r = client.post("/invoices/", json={
        "customer_name": "Dubai Corp LLC",
        "customer_email": "billing@dubai.ae",
        "region": "gcc",
        "country_code": "AE",
        "items": [
            {
                "product_name": "iPhone 15",
                "sku": "IPH-15-128",
                "quantity": 1,
                "unit_price": 3500.0,
            }
        ],
        "currency": "AED",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["currency"] == "AED"
    # UAE VAT = 5%
    assert data["tax_amount"] == pytest.approx(175.0, abs=1.0)


def test_list_invoices(client):
    r = client.get("/invoices/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_invoice(client):
    assert created_invoice_id is not None
    r = client.get(f"/invoices/{created_invoice_id}")
    assert r.status_code == 200
    assert r.json()["id"] == created_invoice_id


def test_invoice_pdf(client):
    assert created_invoice_id is not None
    r = client.get(f"/invoices/{created_invoice_id}/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 1000  # PDF must have actual content


def test_create_expense(client):
    r = client.post("/expenses/", json={
        "title": "E2E Office Supplies",
        "amount": 1500.0,
        "currency": "INR",
        "category": "office",
        "date": "2024-01-15",
    })
    assert r.status_code == 201, r.text
    assert r.json()["title"] == "E2E Office Supplies"


def test_gdpr_data_export(client):
    r = client.get("/compliance/gdpr/export")
    assert r.status_code == 200
    data = r.json()
    assert "invoices" in data
    assert "payments" in data
    assert "export_date" in data


def test_india_gst_report(client):
    r = client.get("/compliance/india/gst-report?year=2024&month=1")
    assert r.status_code == 200
    data = r.json()
    assert data["report_type"] == "GSTR-1_SUMMARY"
    assert "b2b_supplies" in data
    assert "b2c_supplies" in data


def test_eu_vat_report(client):
    r = client.get("/compliance/eu/vat-report?year=2024&quarter=1")
    assert r.status_code == 200
    data = r.json()
    assert data["report_type"] == "EU_VAT_OSS"
    assert "breakdown_by_country" in data


def test_billing_requires_auth():
    """Unauthenticated request must be rejected."""
    r = httpx.get(f"{BILLING_URL}/invoices/")
    assert r.status_code == 401
