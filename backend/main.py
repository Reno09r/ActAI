from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
import uvicorn
import logging.config
import traceback
from auth import auth_router
from model_registry import get_whisper_model, get_tts_model, get_xtts_model
from database import saengine, Base, init_db
from routers import user_router, plan_router, task_router, milestone_router, daily_checkin_router, audio_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
import os
from logging.handlers import RotatingFileHandler

# Создаем директорию для логов
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            filename=log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Инициализация базы данных
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully!")
        get_whisper_model()
        get_tts_model()
        get_xtts_model()
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    yield

app = FastAPI(
    lifespan=lifespan,
    middleware=[
        Middleware(GZipMiddleware, minimum_size=1000),
    ],
    title="ActAI API",
    description="API для ActAI - системы планирования обучения и мотивации",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

app.include_router(auth_router.router)
app.include_router(user_router)
app.include_router(plan_router)
app.include_router(task_router)
app.include_router(milestone_router)
app.include_router(daily_checkin_router.router)
app.include_router(audio_router)