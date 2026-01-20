"""
Audit log model for compliance and RTI tracking.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Index

from app.database import Base


class AuditLog(Base):
    """Audit log for tracking all email-related actions."""
    
    __tablename__ = "email_audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # References
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    email_id = Column(String(36), ForeignKey("emails.id", ondelete="SET NULL"), index=True)
    thread_id = Column(String(36), ForeignKey("email_threads.id", ondelete="SET NULL"), index=True)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)
    # Actions: viewed, sent, replied, forwarded, marked_read, marked_unread,
    #          flagged, unflagged, archived, deleted, attachment_downloaded,
    #          exported, thread_created, thread_resolved
    
    # Request context
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    
    # Additional metadata
    details = Column(JSON, default={})
    # Can include: old_status, new_status, attachment_name, export_format, etc.
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action', 'timestamp'),
        Index('idx_audit_client_action', 'client_id', 'action', 'timestamp'),
        Index('idx_audit_email_action', 'email_id', 'action'),
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_id": self.email_id,
            "thread_id": self.thread_id,
            "client_id": self.client_id,
            "action": self.action,
            "ip_address": self.ip_address,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id}>"


class AuditAction:
    """Constants for audit actions."""
    
    # Email actions
    VIEWED = "viewed"
    SENT = "sent"
    REPLIED = "replied"
    FORWARDED = "forwarded"
    MARKED_READ = "marked_read"
    MARKED_UNREAD = "marked_unread"
    FLAGGED = "flagged"
    UNFLAGGED = "unflagged"
    ARCHIVED = "archived"
    DELETED = "deleted"
    RESTORED = "restored"
    
    # Attachment actions
    ATTACHMENT_DOWNLOADED = "attachment_downloaded"
    ATTACHMENT_UPLOADED = "attachment_uploaded"
    
    # Thread actions
    THREAD_CREATED = "thread_created"
    THREAD_RESOLVED = "thread_resolved"
    THREAD_REOPENED = "thread_reopened"
    
    # Export actions
    EXPORTED = "exported"
    
    # Auth actions
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESHED = "token_refreshed"
