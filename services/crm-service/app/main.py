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
    import app.models  # noqa — register all models for create_all
    logger.info("crm-service starting...")
    Base.metadata.create_all(bind=engine)
    logger.info("crm-service ready")
    yield


app = FastAPI(title="StockPilot CRM Service", version="2.0.0",
              description="Customers, loyalty, orders, storefront", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def add_service_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Service-Name"] = "crm-service"
    return response


@app.exception_handler(Exception)
async def global_exc(request: Request, exc: Exception):
    logger.error(f"Unhandled {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


from app.routers import customer as customer_router
from app.routers import internal as internal_router
from app.routers import order as order_router

app.include_router(customer_router.router)
app.include_router(internal_router.router)
app.include_router(order_router.router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "crm-service", "version": "2.0.0"}
