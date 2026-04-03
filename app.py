from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import LOG_LEVEL, STATIC_DIR
from routes.saved_builds import router as saved_builds_router
from routes.web import router as web_router
from services.ai_service import run_ai_startup_check

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
)
logger = logging.getLogger('pcbuilder.app')


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Запуск FastAPI-застосунку. Рівень логування: %s', LOG_LEVEL)
    run_ai_startup_check()
    try:
        yield
    finally:
        logger.info('Завершення роботи FastAPI-застосунку.')


app = FastAPI(lifespan=lifespan)
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')

logger.info('Підключення роутерів застосунку.')
app.include_router(web_router)
app.include_router(saved_builds_router)
