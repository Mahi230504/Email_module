"""
User model for authentication and settings.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import uuid

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

if TYPE_CHECKING:
    from models.email import Email
    from models.signature import EmailSignature


class User(Base):
    """User model storing OAuth tokens and settings."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # OAuth tokens (encrypted)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    
    # Microsoft Graph subscription
    graph_subscription_id = Column(String(255))
    graph_subscription_expires_at = Column(DateTime)
    
    # Role-based access
    role = Column(String(50), default="accountant")  # admin, accountant, client_manager
    is_active = Column(Boolean, default=True)
    
    # Email settings
    default_signature_id = Column(String(36), ForeignKey("email_signatures.id", use_alter=True))
    
    # Sync tracking
    last_email_sync_time = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    emails = relationship("Email", back_populates="user", lazy="dynamic")
    signatures = relationship(
        "EmailSignature", 
        back_populates="user", 
        foreign_keys="EmailSignature.user_id",
        lazy="dynamic"
    )
    
    @property
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email
    
    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.token_expires_at:
            return True
        return datetime.utcnow() >= self.token_expires_at
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
