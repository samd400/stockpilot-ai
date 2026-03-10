import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=["1000/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import engine, Base
    logger.info("auth-service starting — creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("auth-service ready")
    yield
    logger.info("auth-service shutting down")


app = FastAPI(title="StockPilot Auth Service", version="2.0.0",
              description="Authentication, authorization, RBAC for StockPilot", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


from app.routers import auth as auth_router
from app.routers import user as user_router
from app.routers import tenant as tenant_router
from app.routers import rbac as rbac_router

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(tenant_router.router)
app.include_router(rbac_router.router)


@app.get("/health", tags=["Health"])
@limiter.exempt
async def health():
    return {"status": "healthy", "service": "auth-service", "version": "2.0.0"}
