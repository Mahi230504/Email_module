"""
Client management routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from models.user import User
from models.client import Client
from utils.decorators import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])


class ClientRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    client_type: Optional[str] = None  # corporate, non_corporate
    tax_year: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    tan: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[str] = None
    contact_person_phone: Optional[str] = None


@router.get("")
async def list_clients(
    client_type: Optional[str] = Query(None, description="Filter by client type"),
    search: Optional[str] = Query(None, description="Search by name, email, or PAN"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List clients with filtering."""
    query = db.query(Client)
    
    if client_type:
        query = query.filter(Client.client_type == client_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Client.name.ilike(search_term)) |
            (Client.email.ilike(search_term)) |
            (Client.pan.ilike(search_term))
        )
    
    total = query.count()
    
    clients = query.order_by(Client.name).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "clients": [c.to_dict() for c in clients]
    }


@router.get("/types")
async def get_client_types():
    """Get available client types."""
    return {
        "types": [
            {"value": "corporate", "label": "Corporate"},
            {"value": "non_corporate", "label": "Non-Corporate"}
        ]
    }


@router.get("/{client_id}")
async def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return client.to_dict()


@router.post("")
async def create_client(
    payload: ClientRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new client."""
    # Check for duplicate PAN
    if payload.pan:
        existing = db.query(Client).filter(Client.pan == payload.pan).first()
        if existing:
            raise HTTPException(status_code=400, detail="Client with this PAN already exists")
    
    client = Client(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        client_type=payload.client_type,
        tax_year=payload.tax_year,
        pan=payload.pan,
        gstin=payload.gstin,
        tan=payload.tan,
        contact_person_name=payload.contact_person_name,
        contact_person_email=payload.contact_person_email,
        contact_person_phone=payload.contact_person_phone,
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return {
        "message": "Client created",
        "client": client.to_dict()
    }


@router.patch("/{client_id}")
async def update_client(
    client_id: str,
    payload: ClientRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check for duplicate PAN
    if payload.pan and payload.pan != client.pan:
        existing = db.query(Client).filter(
            Client.pan == payload.pan,
            Client.id != client_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Another client with this PAN exists")
    
    for field, value in payload.model_dump().items():
        if value is not None:
            setattr(client, field, value)
    
    db.commit()
    
    return {
        "message": "Client updated",
        "client": client.to_dict()
    }


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a client (soft delete)."""
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client.is_active = False
    db.commit()
    
    return {"message": "Client deleted"}


@router.get("/{client_id}/emails")
async def get_client_emails(
    client_id: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all emails for a client."""
    from models.email import Email
    
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    query = db.query(Email).filter(Email.client_id == client_id)
    
    total = query.count()
    
    emails = query.order_by(
        Email.received_date_time.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "client": client.to_dict(),
        "total": total,
        "emails": [e.to_dict(include_body=False) for e in emails]
    }


@router.get("/{client_id}/threads")
async def get_client_threads(
    client_id: str,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all email threads for a client."""
    from models.email import EmailThread
    
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    query = db.query(EmailThread).filter(EmailThread.client_id == client_id)
    
    total = query.count()
    
    threads = query.order_by(
        EmailThread.last_activity_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "client": client.to_dict(),
        "total": total,
        "threads": [t.to_dict() for t in threads]
    }
