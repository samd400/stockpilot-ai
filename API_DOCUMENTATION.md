# StockPilot API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints (except `/auth/login`) require JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Authentication Endpoints

### Login
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## User Management

### Get Current User
```
GET /users/me
```

**Response:**
```json
{
  "id": "uuid",
  "business_name": "My Store",
  "owner_name": "John Doe",
  "email": "john@example.com",
  "phone": "+91-9876543210",
  "gst_number": "18AABCT1234H1Z0",
  "subscription_plan_id": "uuid",
  "created_at": "2024-01-01T00:00:00"
}
```

### Update Profile
```
PUT /users/me
Content-Type: application/json

{
  "business_name": "Updated Store Name",
  "phone": "+91-9876543210",
  "gst_number": "18AABCT1234H1Z0"
}
```

---

## Product Management

### Create Product
```
POST /products
Content-Type: application/json

{
  "product_name": "Laptop",
  "brand": "Dell",
  "category": "Electronics",
  "purchase_price": 50000,
  "selling_price": 65000,
  "stock_quantity": 10,
  "gst_percentage": 18,
  "hsn_code": "8471.30"
}
```

### List Products
```
GET /products?skip=0&limit=50
```

### Get Product
```
GET /products/{product_id}
```

### Update Product
```
PUT /products/{product_id}
Content-Type: application/json

{
  "stock_quantity": 15,
  "selling_price": 68000
}
```

### Delete Product
```
DELETE /products/{product_id}
```

---

## Invoice Management

### Create Invoice
```
POST /invoices
Content-Type: application/json

{
  "customer_id": "customer_uuid",
  "items": [
    {
      "product_id": "product_uuid",
      "quantity": 2,
      "unit_price": 65000
    }
  ],
  "notes": "Thank you for your purchase"
}
```

### List Invoices
```
GET /invoices?skip=0&limit=50
```

### Get Invoice
```
GET /invoices/{invoice_id}
```

### Download Invoice PDF
```
GET /invoices/{invoice_id}/pdf
```

---

## Payment Management

### Create Payment
```
POST /payments
Content-Type: application/json

{
  "invoice_id": "invoice_uuid",
  "amount": 130000,
  "mode": "CREDIT_CARD",
  "transaction_id": "TXN123456"
}
```

### Get Payments for Invoice
```
GET /payments/{invoice_id}
```

### Update Payment Status
```
PUT /payments/{payment_id}/status
Content-Type: application/json

{
  "status": "PAID"
}
```

---

## Multi-Branch Management

### Create Branch
```
POST /branches
Content-Type: application/json

{
  "name": "Downtown Store",
  "location": "New York",
  "address": "123 Main St, NY 10001",
  "phone": "+1-212-555-0123",
  "manager_name": "Jane Smith"
}
```

### List Branches
```
GET /branches
```

### Get Branch
```
GET /branches/{branch_id}
```

### Update Branch
```
PUT /branches/{branch_id}
Content-Type: application/json

{
  "manager_name": "John Smith"
}
```

### Delete Branch
```
DELETE /branches/{branch_id}
```

---

## Subscription Management

### Create Subscription
```
POST /subscriptions
Content-Type: application/json

{
  "subscription_plan_id": "plan_uuid",
  "payment_method": "stripe"
}
```

### List Subscriptions
```
GET /subscriptions
```

### Get Active Subscription
```
GET /subscriptions/active
```

### Upgrade Subscription
```
POST /subscriptions/{subscription_id}/upgrade
Content-Type: application/json

{
  "new_plan_id": "new_plan_uuid"
}
```

### Cancel Subscription
```
POST /subscriptions/{subscription_id}/cancel
```

---

## CRM & Customer Loyalty

### Create Customer
```
POST /crm/customers
Content-Type: application/json

{
  "name": "Acme Corp",
  "phone_number": "+91-9876543210",
  "email": "contact@acme.com",
  "address": "123 Business St"
}
```

### List Customers
```
GET /crm/customers
```

### Get Customer
```
GET /crm/customers/{customer_id}
```

### Get Customer Loyalty
```
GET /crm/loyalty/{customer_id}
```

### Add Loyalty Points
```
POST /crm/loyalty/{customer_id}/add-points
Content-Type: application/json

{
  "points": 100
}
```

### Redeem Loyalty Points
```
POST /crm/loyalty/{customer_id}/redeem-points
Content-Type: application/json

{
  "points": 50
}
```

---

## AI/ML Features

### Generate Demand Forecast
```
POST /ai/forecast/{product_id}?days_ahead=30
```

**Response:**
```json
{
  "id": "uuid",
  "product_id": "uuid",
  "forecast_date": "2024-02-01T00:00:00",
  "predicted_quantity": 150,
  "confidence_level": 85.5,
  "recommended_stock": 180,
  "reorder_urgency": "NORMAL"
}
```

### Calculate Dynamic Price
```
POST /ai/dynamic-price/{product_id}
```

**Response:**
```json
{
  "product_id": "uuid",
  "base_price": 65000,
  "current_price": 71500,
  "price_change_percentage": 10.0,
  "demand_multiplier": 1.15,
  "stock_multiplier": 0.95,
  "recommendation": "INCREASE"
}
```

### Calculate Inventory Health
```
POST /ai/inventory-health/{product_id}
```

**Response:**
```json
{
  "id": "uuid",
  "product_id": "uuid",
  "health_score": 75.5,
  "status": "GOOD",
  "turnover_ratio": 2.5,
  "dead_stock_percentage": 5.0,
  "recommendations": "Maintain current stock levels"
}
```

---

## Role-Based Access Control

### Assign Role
```
POST /rbac/roles
Content-Type: application/json

{
  "user_id": "user_uuid",
  "role": "MANAGER",
  "branch_id": "branch_uuid"
}
```

### Get User Role
```
GET /rbac/roles/{user_id}
```

### Get User Permissions
```
GET /rbac/permissions
```

**Response:**
```json
{
  "user_id": "uuid",
  "role": "MANAGER",
  "permissions": [
    "create_product",
    "read_product",
    "update_product",
    "create_invoice",
    "read_invoice",
    "view_analytics"
  ]
}
```

---

## Audit Logs

### Get Audit Logs
```
GET /audit/logs?entity_type=Invoice&action=CREATE&days=30
```

### Get Entity History
```
GET /audit/logs/{entity_type}/{entity_id}
```

### Get Audit Summary
```
GET /audit/summary?days=30
```

### Export Audit Logs
```
GET /audit/export?days=30
```

---

## POS Billing

### Create POS Bill
```
POST /pos/bill
Content-Type: application/json

{
  "customer_id": "customer_uuid",
  "items": [
    {
      "product_id": "product_uuid",
      "quantity": 2,
      "price": 65000
    }
  ],
  "payment_mode": "CASH"
}
```

### Get Recent Bills
```
GET /pos/bills?limit=50
```

### Get Bill Details
```
GET /pos/bills/{invoice_id}
```

### Create Return
```
POST /pos/bills/{invoice_id}/return
Content-Type: application/json

{
  "items": [
    {
      "product_id": "product_uuid",
      "quantity": 1
    }
  ]
}
```

---

## Admin Revenue Dashboard

### Get Revenue Metrics
```
GET /admin/revenue/metrics
```

**Response:**
```json
{
  "mrr": 50000,
  "arr": 600000,
  "churn_rate": 5.2,
  "total_revenue": 1500000,
  "active_subscriptions": 25,
  "calculated_at": "2024-01-15T10:30:00"
}
```

### Get Monthly Revenue Breakdown
```
GET /admin/revenue/monthly-breakdown
```

### Get Subscription Breakdown
```
GET /admin/revenue/subscription-breakdown
```

### Get Customer Metrics
```
GET /admin/revenue/customer-metrics
```

---

## Dashboard & Analytics

### Get Dashboard Summary
```
GET /dashboard/summary
```

**Response:**
```json
{
  "total_products": 50,
  "total_stock_value": 2500000,
  "total_invoices": 150,
  "revenue_today": 45000,
  "low_stock_products": 5
}
```

### Get Revenue Analytics
```
GET /dashboard/revenue
```

### Get Dashboard Insights
```
GET /dashboard/insights
```

### Get Sales Trend
```
GET /analytics/sales-trend
```

### Get Top Products
```
GET /analytics/top-products
```

### Get Profit/Loss Trend
```
GET /analytics/profit-loss-trend
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- Free Plan: 100 requests/hour
- Pro Plan: 1000 requests/hour
- Enterprise Plan: Unlimited

---

## Webhooks

### Payment Webhook
```
POST /webhooks/payment
Content-Type: application/json

{
  "event": "payment.success",
  "payment_id": "uuid",
  "amount": 130000,
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## Support

For API support, contact: api-support@stockpilot.com
