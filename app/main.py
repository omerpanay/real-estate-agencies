"""
FastAPI Multi-Tenant Application Entry Point.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    
    Initializes database tables on startup.
    """
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Cleanup if needed


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Tenant API with FastAPI and PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Root endpoint for health check."""
    return {"status": "healthy", "app": settings.APP_NAME}


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
