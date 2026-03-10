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
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import engine, Base
    import app.models  # noqa — register Alert, AgentAuditLog, DynamicPrice for create_all
    logger.info("ai-service starting — creating tables...")
    Base.metadata.create_all(bind=engine)

    # Register all agents on startup
    try:
        import app.agents.stock_agent   # noqa — registers StockAgent, InsightAgent, ComplianceAgent
        import app.agents.profit_agent  # noqa — registers ProfitAgent, PricingAgent
        logger.info("All AI agents registered successfully")
    except Exception as e:
        logger.error(f"Agent registration failed: {e}")

    logger.info("ai-service ready")
    yield
    logger.info("ai-service shutting down")


app = FastAPI(
    title="StockPilot AI Service",
    version="2.0.0",
    description="Multi-step agentic AI: stock monitoring, profit analysis, pricing, business assistant",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def add_service_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Service-Name"] = "ai-service"
    return response


@app.exception_handler(Exception)
async def global_exc(request: Request, exc: Exception):
    logger.error(f"Unhandled {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


from app.routers import assistant as assistant_router
from app.routers import agents as agents_router
from app.routers import dashboard as dashboard_router
from app.routers import alerts as alerts_router

app.include_router(assistant_router.router)
app.include_router(agents_router.router)
app.include_router(dashboard_router.router)
app.include_router(alerts_router.router)


@app.get("/health")
async def health():
    from app.agents.base import list_agents
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "2.0.0",
        "registered_agents": list(list_agents().keys()),
    }
