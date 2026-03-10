import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=["500/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import engine, Base
    logger.info("billing-service starting...")
    Base.metadata.create_all(bind=engine)
    logger.info("billing-service ready")
    yield
    logger.info("billing-service shutting down")


app = FastAPI(title="StockPilot Billing Service", version="2.0.0",
              description="Invoice, payment, POS, subscription, expense management",
              lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def add_service_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Service-Name"] = "billing-service"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


from app.routers import invoice as invoice_router
from app.routers import payment as payment_router
from app.routers import pos as pos_router
from app.routers import expense as expense_router
from app.routers import compliance as compliance_router

app.include_router(invoice_router.router)
app.include_router(payment_router.router)
app.include_router(pos_router.router)
app.include_router(expense_router.router)
app.include_router(compliance_router.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "service": "billing-service", "version": "2.0.0"}
