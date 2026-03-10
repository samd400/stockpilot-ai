"""
E2E tests — Inventory Service (port 8002)
Covers: products CRUD, branch management, supplier, purchase orders, device/IMEI, internal stock deduction.
"""
import pytest
import httpx
from conftest import INVENTORY_URL

created_product_id = None


@pytest.fixture(scope="module")
def client(auth_headers):
    return httpx.Client(base_url=INVENTORY_URL, headers=auth_headers, timeout=30)


def test_health():
    r = httpx.get(f"{INVENTORY_URL}/health")
    assert r.status_code == 200
    assert r.json()["service"] == "inventory-service"


def test_create_product(client):
    global created_product_id
    r = client.post("/products/", json={
        "product_name": "E2E Test Product",
        "sku": f"E2E-SKU-{__import__('uuid').uuid4().hex[:6]}",
        "selling_price": 999.99,
        "purchase_price": 800.0,
        "stock_quantity": 50,
        "category": "Electronics",
        "brand": "TestBrand",
        "gst_percentage": 18.0,
        "hsn_code": "8471",
        "currency": "INR",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["product_name"] == "E2E Test Product"
    created_product_id = data["id"]


def test_list_products(client):
    r = client.get("/products/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_product(client):
    assert created_product_id is not None
    r = client.get(f"/products/{created_product_id}")
    assert r.status_code == 200
    assert r.json()["id"] == created_product_id


def test_update_product(client):
    r = client.patch(f"/products/{created_product_id}", json={"selling_price": 1099.99})
    assert r.status_code == 200
    assert r.json()["selling_price"] == 1099.99


def test_low_stock_filter(client):
    r = client.get("/products/?low_stock=true")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_branch(client):
    r = client.post("/branches/", json={
        "name": "E2E Test Branch",
        "code": "E2E01",
        "city": "Mumbai",
        "country": "IN",
        "is_main": True,
    })
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "E2E Test Branch"


def test_list_branches(client):
    r = client.get("/branches/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_supplier(client):
    r = client.post("/suppliers/", json={
        "name": "E2E Test Supplier",
        "email": "supplier@test.com",
        "country": "IN",
        "gst_number": "22AAAAA0000A1Z5",
    })
    assert r.status_code == 201, r.text


def test_internal_stock_deduct_invalid_token(service_headers):
    """Internal endpoint must reject requests without service token."""
    r = httpx.post(f"{INVENTORY_URL}/internal/stock/deduct", json={
        "tenant_id": "00000000-0000-0000-0000-000000000000",
        "items": [{"product_id": "00000000-0000-0000-0000-000000000000", "quantity": 1}]
    })
    assert r.status_code == 403


def test_register_device(client):
    assert created_product_id is not None
    r = client.post("/devices/", json={
        "product_id": created_product_id,
        "serial_number": f"SN-E2E-{__import__('uuid').uuid4().hex[:8]}",
        "imei": f"35{__import__('random').randint(100000000000, 999999999999)}",
        "warranty_months": "12",
    })
    assert r.status_code == 201, r.text


def test_create_rma(client):
    assert created_product_id is not None
    r = client.post("/rma/", json={
        "product_id": created_product_id,
        "customer_name": "E2E Customer",
        "customer_phone": "+919876543210",
        "reason": "Screen not working",
    })
    assert r.status_code == 201, r.text
    assert "rma_number" in r.json()
