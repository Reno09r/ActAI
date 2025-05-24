from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
import uvicorn
import logging.config
import traceback
from auth import auth_router
from database import saengine, Base, init_db
from routers import user_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

# Настройка логирования

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("Initializing database...")
        await init_db()
        print("Database initialized successfully!")
        print("Preloading models...")
        print("All models loaded!")
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        print(traceback.format_exc())
        raise
    yield

app = FastAPI(
    lifespan=lifespan,
    middleware=[
        Middleware(GZipMiddleware, minimum_size=1000),
    ]
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Global error handler caught: {str(exc)}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(user_router.router)

if __name__=='__main__':
    print("Starting application...")
    uvicorn.run("main:app", reload=True, workers=3, port=8003)
