"""
Services Package
"""

from services.auth_service import AuthService
from services.graph_service import GraphService
from services.threading_engine import EmailThreadingEngine, ThreadingResult, create_or_get_thread
from services.classification_service import EmailClassifier, EmailType
from services.email_service import EmailService
from services.search_service import SearchService
from services.sync_service import SyncService

__all__ = [
    "AuthService",
    "GraphService",
    "EmailThreadingEngine",
    "ThreadingResult",
    "create_or_get_thread",
    "EmailClassifier",
    "EmailType",
    "EmailService",
    "SearchService",
    "SyncService",
]
