"""
Outlook Email Module - FastAPI Application Entry Point
"""

import os
import sys
from contextlib import asynccontextmanager

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import engine, Base
from routes import (
    auth_router,
    emails_router,
    threads_router,
    webhooks_router,
    signatures_router,
    templates_router,
    search_router,
    clients_router,
)
from utils.exceptions import EmailModuleException

settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Outlook Email Module...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Outlook Email Module",
    description="""
    Production-ready email module for tax automation platform.
    
    ## Features
    - Microsoft Graph API integration
    - Multi-layer email threading
    - Real-time webhook notifications
    - Full-text search with Elasticsearch
    - Email templates and signatures
    - Audit logging for compliance
    
    ## Authentication
    Use `/auth/login` to initiate OAuth flow with Microsoft.
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(EmailModuleException)
async def email_module_exception_handler(request: Request, exc: EmailModuleException):
    """Handle custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    # Log the error
    print(f"❌ Unhandled error: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )


# Include routers
app.include_router(auth_router)
app.include_router(emails_router)
app.include_router(threads_router)
app.include_router(webhooks_router)
app.include_router(signatures_router)
app.include_router(templates_router)
app.include_router(search_router)
app.include_router(clients_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "outlook-email-module",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Outlook Email Module",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# API info endpoint
@app.get("/api/info", tags=["Info"])
async def api_info():
    """Get API configuration info."""
    return {
        "platform_url": settings.platform_url,
        "oauth_configured": bool(settings.azure_client_id),
        "webhooks_enabled": settings.enable_webhooks,
        "features": [
            "email_sync",
            "email_threading",
            "webhooks",
            "templates",
            "signatures",
            "audit_logging"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
