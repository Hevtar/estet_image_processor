"""
Parser Service — FastAPI Application.
API для управления парсингом и мониторинга.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes import router as api_router
from .config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager для приложения"""
    logger.info("🚀 Parser Service запускается...")
    yield
    logger.info("🛑 Parser Service останавливается...")


app = FastAPI(
    title="ESTET Parser Service",
    description="Сервис парсинга каталога ESTET",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "parser"}
