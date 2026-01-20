"""
Client model for tax clients.
"""

from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Client(Base):
    """Client model representing tax clients."""
    
    __tablename__ = "clients"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Client information
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    address = Column(Text)
    
    # Classification
    client_type = Column(String(50), index=True)  # corporate, non_corporate
    tax_year = Column(String(20))  # FY 2024-25, FY 2025-26
    
    # Tax identifiers
    pan = Column(String(20), unique=True, index=True)
    gstin = Column(String(20), index=True)
    tan = Column(String(20))
    
    # Contact person
    contact_person_name = Column(String(255))
    contact_person_email = Column(String(255))
    contact_person_phone = Column(String(50))
    
    # Status
    is_active = Column(String(50), default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email_threads = relationship("EmailThread", back_populates="client", lazy="dynamic")
    emails = relationship("Email", back_populates="client", lazy="dynamic")
    footers = relationship("EmailFooter", back_populates="client", lazy="dynamic")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "client_type": self.client_type,
            "tax_year": self.tax_year,
            "pan": self.pan,
            "gstin": self.gstin,
            "contact_person_name": self.contact_person_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self) -> str:
        return f"<Client {self.name}>"
