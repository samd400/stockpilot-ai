from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app import models
from app.routers import user as user_router
from app.routers import auth as auth_router
from app.routers import product as product_router
from app.routers import invoice as invoice_router
from app.routers import dashboard as dashboard_router
from app.routers import analytics
from app.routers import alerts
from app.routers import admin
from app.routers import payment as payment_router
from app.routers import purchase as purchase_router
from app.routers import expense as expense_router
from app.routers import branch
from app.routers import subscription
from app.routers import revenue_dashboard
from app.routers import crm
from app.routers import ai_ml
from app.routers import rbac
from app.routers import audit
from app.routers import pos
from app.routers import tenant as tenant_router
from app.routers import order as order_router
from app.routers import inventory as inventory_router
from app.routers import storefront as storefront_router
from app.routers import webhooks as webhooks_router
from app.routers import procurement as procurement_router
from app.routers import assistant as assistant_router
from app.routers import pricing as pricing_router
from app.routers import rma as rma_router
from app.routers import reports as reports_router
from app.routers import connectors as connectors_router
from app.routers import devices as devices_router
from app.routers import sync as sync_router


# Create FastAPI app FIRST
app = FastAPI(
    title="StockPilot API",
    description="AI-powered multi-tenant retail operating system SaaS with multi-region support",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Register routers AFTER app is defined
app.include_router(tenant_router.router)
app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(product_router.router)
app.include_router(invoice_router.router)
app.include_router(order_router.router)
app.include_router(inventory_router.router)
app.include_router(dashboard_router.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(admin.router)
app.include_router(payment_router.router)
app.include_router(purchase_router.router)
app.include_router(expense_router.router)
app.include_router(branch.router)
app.include_router(subscription.router)
app.include_router(revenue_dashboard.router)
app.include_router(crm.router)
app.include_router(ai_ml.router)
app.include_router(rbac.router)
app.include_router(audit.router)
app.include_router(pos.router)
app.include_router(storefront_router.router)
app.include_router(webhooks_router.router)
app.include_router(procurement_router.router)
app.include_router(assistant_router.router)
app.include_router(pricing_router.router)
app.include_router(rma_router.router)
app.include_router(reports_router.router)
app.include_router(connectors_router.router)
app.include_router(devices_router.router)
app.include_router(sync_router.router)




@app.get("/health")
def health_check():
    return {"status": "StockPilot backend running"}
