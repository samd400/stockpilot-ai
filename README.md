# StockPilot - AI-Powered Retail Operating System SaaS

A production-grade, multi-tenant SaaS platform for retail inventory management with GST compliance, AI-powered demand forecasting, dynamic pricing, and comprehensive business intelligence.

## Features

### Core Features
- ✅ Multi-tenant authentication with JWT
- ✅ GST-compliant invoice generation with PDF export
- ✅ Auto invoice numbering
- ✅ SMS async notifications
- ✅ 30-day stock analytics
- ✅ Risk + movement classification
- ✅ Profit/loss estimation
- ✅ Capital blocked analysis
- ✅ Smart alerts

### Extended Features
- ✅ Payment tracking (Stripe & Razorpay integration)
- ✅ Purchase management
- ✅ Expense tracking
- ✅ Multi-branch inventory management
- ✅ POS billing UI
- ✅ Customer CRM + loyalty program
- ✅ Usage tracking + plan guard
- ✅ Subscription expiry auto-downgrade
- ✅ Admin revenue dashboard (MRR/ARR)
- ✅ ML demand forecasting
- ✅ Dynamic pricing engine
- ✅ Inventory health scoring
- ✅ Role-based access control (RBAC)
- ✅ Comprehensive audit logs
- ✅ Dashboard analytics with charts

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Task Queue**: Celery with Redis
- **Authentication**: JWT with bcrypt
- **Payment Gateways**: Stripe, Razorpay
- **PDF Generation**: ReportLab
- **SMS**: Twilio
- **Deployment**: Docker, Kubernetes-ready

## Project Structure

```
stockpilot-backend/
├── app/
│   ├── core/
│   │   ├── auth_dependency.py      # JWT authentication
│   │   ├── celery_config.py        # Celery configuration
│   │   ├── celery_worker.py        # Celery worker setup
│   │   ├── database.py             # Database connection
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   └── security.py             # Password hashing & JWT
│   ├── models/
│   │   ├── user.py                 # User model
│   │   ├── product.py              # Product model
│   │   ├── invoice.py              # Invoice model
│   │   ├── payment.py              # Payment model
│   │   ├── customer.py             # Customer model
│   │   ├── branch.py               # Branch model (multi-branch)
│   │   ├── user_role.py            # RBAC model
│   │   ├── audit_log.py            # Audit logging
│   │   ├── inventory_health.py     # Inventory health scoring
│   │   ├── dynamic_price.py        # Dynamic pricing
│   │   ├── demand_forecast.py      # ML forecasting
│   │   ├── customer_loyalty.py     # Loyalty program
│   │   ├── user_subscription.py    # Subscription management
│   │   ├── payment_transaction.py  # Payment gateway transactions
│   │   └── revenue_metrics.py      # Revenue analytics
│   ├── routers/
│   │   ├── auth.py                 # Authentication endpoints
│   │   ├── user.py                 # User management
│   │   ├── product.py              # Product management
│   │   ├── invoice.py              # Invoice management
│   │   ├── payment.py              # Payment tracking
│   │   ├── dashboard.py            # Dashboard analytics
│   │   ├── analytics.py            # Advanced analytics
│   │   ├── alerts.py               # Smart alerts
│   │   ├── admin.py                # Admin panel
│   │   ├── branch.py               # Multi-branch management
│   │   ├── subscription.py         # Subscription management
│   │   ├── revenue_dashboard.py    # Revenue metrics (MRR/ARR)
│   │   ├── crm.py                  # Customer CRM + loyalty
│   │   ├── ai_ml.py                # AI/ML features
│   │   ├── rbac.py                 # Role-based access control
│   │   ├── audit.py                # Audit logging
│   │   └── pos.py                  # POS billing
│   ├── schemas/
│   │   ├── auth.py                 # Auth schemas
│   │   ├── user.py                 # User schemas
│   │   ├── product.py              # Product schemas
│   │   ├── invoice.py              # Invoice schemas
│   │   ├── payment.py              # Payment schemas
│   │   ├── branch.py               # Branch schemas
│   │   ├── user_role.py            # RBAC schemas
│   │   ├── inventory_health.py     # Health schemas
│   │   ├── dynamic_price.py        # Pricing schemas
│   │   ├── demand_forecast.py      # Forecast schemas
│   │   ├── customer_loyalty.py     # Loyalty schemas
│   │   └── user_subscription.py    # Subscription schemas
│   ├── services/
│   │   ├── alert_service.py        # Smart alerts
│   │   ├── invoice_number_service.py
│   │   ├── notification_service.py
│   │   ├── payment_service.py
│   │   ├── payment_gateway_service.py  # Stripe/Razorpay
│   │   ├── pdf_service.py          # PDF generation
│   │   ├── plan_guard.py           # Subscription enforcement
│   │   ├── purchase_service.py
│   │   ├── sms_service.py
│   │   └── stock_prediction_service.py
│   ├── tasks/
│   │   ├── notification_tasks.py   # Async SMS/Email
│   │   └── subscription_tasks.py   # Subscription automation
│   └── main.py                     # FastAPI app entry point
├── alembic/
│   ├── versions/                   # Migration files
│   ├── env.py
│   └── script.py.mako
├── requirements.txt                # Python dependencies
├── alembic.ini                     # Alembic configuration
└── .env                            # Environment variables
```

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Docker (optional)

### Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd stockpilot-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Create database**
```bash
createdb stockpilot_db
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Seed initial data**
```bash
python -m app.scripts.seed_plans
```

8. **Start the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

9. **Start Celery worker** (in another terminal)
```bash
celery -A app.core.celery_config worker --loglevel=info
```

10. **Start Celery Beat** (in another terminal)
```bash
celery -A app.core.celery_config beat --loglevel=info
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/stockpilot_db

# JWT
SECRET_KEY=your-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_key

# Razorpay
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# Twilio (SMS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Email (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration

### User Management
- `GET /users/me` - Get current user
- `PUT /users/me` - Update profile
- `POST /users` - Create user (admin)
- `GET /users` - List users (admin)

### Products
- `POST /products` - Create product
- `GET /products` - List products
- `GET /products/{id}` - Get product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product

### Invoices
- `POST /invoices` - Create invoice
- `GET /invoices` - List invoices
- `GET /invoices/{id}` - Get invoice
- `GET /invoices/{id}/pdf` - Download PDF

### Payments
- `POST /payments` - Create payment
- `GET /payments/{invoice_id}` - Get payments
- `PUT /payments/{id}/status` - Update payment status

### Multi-Branch
- `POST /branches` - Create branch
- `GET /branches` - List branches
- `PUT /branches/{id}` - Update branch
- `DELETE /branches/{id}` - Delete branch

### Subscriptions
- `POST /subscriptions` - Create subscription
- `GET /subscriptions` - List subscriptions
- `GET /subscriptions/active` - Get active subscription
- `POST /subscriptions/{id}/upgrade` - Upgrade plan
- `POST /subscriptions/{id}/cancel` - Cancel subscription

### CRM & Loyalty
- `POST /crm/customers` - Create customer
- `GET /crm/customers` - List customers
- `GET /crm/loyalty/{customer_id}` - Get loyalty info
- `POST /crm/loyalty/{customer_id}/add-points` - Add points
- `POST /crm/loyalty/{customer_id}/redeem-points` - Redeem points

### AI/ML Features
- `POST /ai/forecast/{product_id}` - Generate demand forecast
- `POST /ai/dynamic-price/{product_id}` - Calculate dynamic price
- `POST /ai/inventory-health/{product_id}` - Calculate health score

### RBAC
- `POST /rbac/roles` - Assign role
- `GET /rbac/roles/{user_id}` - Get user role
- `GET /rbac/permissions` - Get user permissions

### Audit Logs
- `GET /audit/logs` - Get audit logs
- `GET /audit/logs/{entity_type}/{entity_id}` - Get entity history
- `GET /audit/summary` - Get audit summary

### POS Billing
- `POST /pos/bill` - Create POS bill
- `GET /pos/bills` - Get recent bills
- `POST /pos/bills/{id}/return` - Create return

### Admin Revenue Dashboard
- `GET /admin/revenue/metrics` - Get MRR/ARR metrics
- `GET /admin/revenue/monthly-breakdown` - Monthly revenue
- `GET /admin/revenue/subscription-breakdown` - Plan breakdown
- `GET /admin/revenue/customer-metrics` - Customer metrics

### Dashboard & Analytics
- `GET /dashboard/summary` - Dashboard summary
- `GET /dashboard/revenue` - Revenue analytics
- `GET /dashboard/insights` - Business insights
- `GET /analytics/sales-trend` - Sales trend
- `GET /analytics/top-products` - Top products
- `GET /analytics/profit-loss-trend` - P&L trend

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

## Docker Deployment

### Build Docker image
```bash
docker build -t stockpilot-backend .
```

### Run with Docker Compose
```bash
docker-compose up -d
```

## Production Deployment

### Using Gunicorn
```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Kubernetes
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Testing

```bash
pytest tests/ -v
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Submit a pull request

## License

MIT License

## Support

For support, email support@stockpilot.com or create an issue on GitHub.
