"""
Email Signature, Footer, and Template models.
"""

from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class EmailSignature(Base):
    """User email signature."""
    
    __tablename__ = "email_signatures"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Signature content
    name = Column(String(100), nullable=False)  # "Default", "Formal", etc.
    signature_html = Column(Text)
    signature_text = Column(Text)
    
    # Settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="signatures", foreign_keys=[user_id])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "signature_html": self.signature_html,
            "signature_text": self.signature_text,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self) -> str:
        return f"<EmailSignature {self.name}>"


class EmailFooter(Base):
    """Client-specific email footer."""
    
    __tablename__ = "email_footers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Association
    client_id = Column(String(36), ForeignKey("clients.id"), index=True)
    
    # Footer content
    name = Column(String(100), nullable=False)
    footer_html = Column(Text)
    footer_text = Column(Text)
    
    # Applies to
    applies_to_type = Column(String(50))  # corporate, non_corporate, or None for all
    
    # Settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="footers")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "name": self.name,
            "footer_html": self.footer_html,
            "footer_text": self.footer_text,
            "applies_to_type": self.applies_to_type,
            "is_default": self.is_default,
            "is_active": self.is_active,
        }
    
    def __repr__(self) -> str:
        return f"<EmailFooter {self.name}>"


class EmailTemplate(Base):
    """Reusable email template."""
    
    __tablename__ = "email_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Template info
    name = Column(String(200), nullable=False)
    description = Column(Text)
    email_type = Column(String(50), index=True)  # NIL_FILING, VAT_FILING, etc.
    
    # Template content
    subject_template = Column(String(500), nullable=False)
    body_template = Column(Text)  # Plain text
    body_html_template = Column(Text)  # HTML
    
    # Variables (for mail merge)
    variables = Column(JSON, default=[])  # ["client_name", "tax_year", "due_date"]
    
    # Metadata
    created_by = Column(String(36), ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def render(self, context: dict) -> tuple:
        """
        Render template with context variables.
        
        Args:
            context: Dictionary of variable values
            
        Returns:
            Tuple of (subject, body_text, body_html)
        """
        subject = self.subject_template
        body_text = self.body_template or ""
        body_html = self.body_html_template or ""
        
        for var, value in context.items():
            placeholder = f"{{{{{var}}}}}"  # {{variable_name}}
            subject = subject.replace(placeholder, str(value))
            body_text = body_text.replace(placeholder, str(value))
            body_html = body_html.replace(placeholder, str(value))
        
        return subject, body_text, body_html
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "email_type": self.email_type,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "body_html_template": self.body_html_template,
            "variables": self.variables,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self) -> str:
        return f"<EmailTemplate {self.name}>"
