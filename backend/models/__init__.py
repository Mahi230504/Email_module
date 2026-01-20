"""
Models Package - Database models for the Email Module.
"""

from models.user import User
from models.client import Client
from models.email import (
    Email,
    EmailThread,
    EmailAttachment,
    EmailType,
    ThreadStatus,
    EmailDirection,
    EmailStatus,
)
from models.signature import (
    EmailSignature,
    EmailFooter,
    EmailTemplate,
)
from models.audit_log import AuditLog, AuditAction

__all__ = [
    # User & Client
    "User",
    "Client",
    
    # Email
    "Email",
    "EmailThread",
    "EmailAttachment",
    "EmailType",
    "ThreadStatus",
    "EmailDirection",
    "EmailStatus",
    
    # Signatures & Templates
    "EmailSignature",
    "EmailFooter",
    "EmailTemplate",
    
    # Audit
    "AuditLog",
    "AuditAction",
]
