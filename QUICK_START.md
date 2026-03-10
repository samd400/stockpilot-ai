# StockPilot - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone and navigate
git clone <repository-url>
cd stockpilot-backend

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
createdb stockpilot_db
alembic upgrade head

# 4. Start services (in separate terminals)
# Terminal 1:
uvicorn app.main:app --reload

# Terminal 2:
celery -A app.core.celery_config worker --loglevel=info

# Terminal 3:
celery -A app.core.celery_config beat --loglevel=info
```

---

## 📋 First Steps

### 1. Create Admin User
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "My Store",
    "owner_name": "John Doe",
    "email": "admin@example.com",
    "password": "secure_password"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=secure_password"
```

### 3. Create Subscription Plan
```bash
curl -X POST http://localhost:8000/admin/plans \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pro",
    "price": 999,
    "max_products": 100,
    "max_invoices_per_month": 500
  }'
```

### 4. Create Product
```bash
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Laptop",
    "brand": "Dell",
    "category": "Electronics",
    "purchase_price": 50000,
    "selling_price": 65000,
    "stock_quantity": 10,
    "gst_percentage": 18
  }'
```

### 5. Create Customer
```bash
curl -X POST http://localhost:8000/crm/customers \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "phone_number": "+91-9876543210",
    "email": "contact@acme.com"
  }'
```

### 6. Create Invoice
```bash
curl -X POST http://localhost:8000/invoices \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "<customer_id>",
    "items": [
      {
        "product_id": "<product_id>",
        "quantity": 2,
        "unit_price": 65000
      }
    ]
  }'
```

---

## 🔑 Key Features to Try

### AI/ML Features
```bash
# Generate demand forecast
curl -X POST http://localhost:8000/ai/forecast/<product_id>?days_ahead=30 \
  -H "Authorization: Bearer <your_token>"

# Calculate dynamic price
curl -X POST http://localhost:8000/ai/dynamic-price/<product_id> \
  -H "Authorization: Bearer <your_token>"

# Calculate inventory health
curl -X POST http://localhost:8000/ai/inventory-health/<product_id> \
  -H "Authorization: Bearer <your_token>"
```

### Analytics
```bash
# Dashboard summary
curl http://localhost:8000/dashboard/summary \
  -H "Authorization: Bearer <your_token>"

# Sales trend
curl http://localhost:8000/analytics/sales-trend \
  -H "Authorization: Bearer <your_token>"

# Top products
curl http://localhost:8000/analytics/top-products \
  -H "Authorization: Bearer <your_token>"
```

### Multi-Branch
```bash
# Create branch
curl -X POST http://localhost:8000/branches \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Downtown Store",
    "location": "New York",
    "manager_name": "Jane Smith"
  }'
```

### CRM & Loyalty
```bash
# Add loyalty points
curl -X POST http://localhost:8000/crm/loyalty/<customer_id>/add-points \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"points": 100}'

# Get loyalty info
curl http://localhost:8000/crm/loyalty/<customer_id> \
  -H "Authorization: Bearer <your_token>"
```

### POS Billing
```bash
# Create POS bill
curl -X POST http://localhost:8000/pos/bill \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "<customer_id>",
    "items": [
      {
        "product_id": "<product_id>",
        "quantity": 1,
        "price": 65000
      }
    ],
    "payment_mode": "CASH"
  }'
```

---

## 📊 Admin Dashboard

Access the admin revenue dashboard:
```bash
# Get MRR/ARR metrics
curl http://localhost:8000/admin/revenue/metrics \
  -H "Authorization: Bearer <your_token>"

# Get monthly breakdown
curl http://localhost:8000/admin/revenue/monthly-breakdown \
  -H "Authorization: Bearer <your_token>"

# Get subscription breakdown
curl http://localhost:8000/admin/revenue/subscription-breakdown \
  -H "Authorization: Bearer <your_token>"
```

---

## 🔐 RBAC & Audit

### Assign Role
```bash
curl -X POST http://localhost:8000/rbac/roles \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user_id>",
    "role": "MANAGER",
    "branch_id": "<branch_id>"
  }'
```

### View Audit Logs
```bash
curl http://localhost:8000/audit/logs \
  -H "Authorization: Bearer <your_token>"
```

---

## 📚 Documentation

- **Full API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **README**: See README.md
- **API Documentation**: See API_DOCUMENTATION.md
- **Deployment Guide**: See DEPLOYMENT.md

---

## 🐛 Troubleshooting

### Services not starting?
```bash
# Check logs
docker-compose logs -f

# Restart services
docker-compose restart

# Rebuild images
docker-compose build --no-cache
```

### Database connection error?
```bash
# Check database is running
docker-compose ps postgres

# Check database exists
docker-compose exec postgres psql -U postgres -l
```

### Celery not working?
```bash
# Check Redis is running
docker-compose ps redis

# Check Celery worker
docker-compose logs celery_worker
```

---

## 🚀 Next Steps

1. **Explore API Documentation**: http://localhost:8000/docs
2. **Create test data**: Use the curl commands above
3. **Try AI features**: Generate forecasts and dynamic prices
4. **Set up payment gateway**: Configure Stripe/Razorpay
5. **Deploy to production**: Follow DEPLOYMENT.md

---

## 💡 Tips

- Use Postman or Insomnia for easier API testing
- Check logs with `docker-compose logs -f <service>`
- Database is at `localhost:5432`
- Redis is at `localhost:6379`
- API runs on `localhost:8000`

---

## 📞 Support

For issues or questions:
- Check API_DOCUMENTATION.md
- Review DEPLOYMENT.md
- Check logs: `docker-compose logs -f`
- Contact: support@stockpilot.com

---

## 🎉 You're Ready!

Your StockPilot instance is now running. Start building your retail operating system!
