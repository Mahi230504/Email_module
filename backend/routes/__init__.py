"""
Routes Package
"""

from routes.auth import router as auth_router
from routes.emails import router as emails_router
from routes.threads import router as threads_router
from routes.webhooks import router as webhooks_router
from routes.signatures import router as signatures_router
from routes.templates import router as templates_router
from routes.search import router as search_router
from routes.clients import router as clients_router

__all__ = [
    "auth_router",
    "emails_router",
    "threads_router",
    "webhooks_router",
    "signatures_router",
    "templates_router",
    "search_router",
    "clients_router",
]
