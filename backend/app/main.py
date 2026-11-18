"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # load .env before anything that reads settings

from app.database.connection import Base, engine  # noqa: E402  (must be after load_dotenv)
from app.core.config import settings as app_settings  # noqa: E402
# Import every model before create_all so SQLAlchemy registers all tables.
from app.models import alert, device, reading, settings as settings_model, user  # noqa: E402,F401
from app.api import auth, sensors, devices, alerts, settings as settings_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables that do not yet exist (non-destructive).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Smart Weather Monitoring API",
    description="REST backend for the IoT Weather Monitoring System",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS origins are configured for local development and can be narrowed in deployment.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in app_settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(sensors.router)
app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(settings_router.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Smart Weather Monitoring API"}
