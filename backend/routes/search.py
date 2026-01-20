"""
Search routes for full-text email search.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from models.user import User
from services.search_service import SearchService
from utils.decorators import get_current_user

router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    """Full-text search request."""
    query: str
    email_type: Optional[str] = None
    client_id: Optional[str] = None
    from_address: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_read: Optional[bool] = None
    has_attachments: Optional[bool] = None
    direction: Optional[str] = None
    limit: int = 50
    offset: int = 0


@router.get("")
async def search_emails(
    q: str = Query(..., min_length=1, description="Search query"),
    email_type: Optional[str] = Query(None, description="Filter by email type"),
    client_id: Optional[str] = Query(None, description="Filter by client"),
    from_address: Optional[str] = Query(None, description="Filter by sender"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    has_attachments: Optional[bool] = Query(None, description="Filter by attachments"),
    direction: Optional[str] = Query(None, description="Filter by direction"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Full-text search across emails.
    
    Searches subject, body, and sender fields.
    """
    search_service = SearchService(db)
    
    # Parse dates if provided
    parsed_date_from = None
    parsed_date_to = None
    
    if date_from:
        try:
            parsed_date_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    
    if date_to:
        try:
            parsed_date_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")
    
    results = search_service.search_emails(
        user_id=current_user.id,
        query=q,
        email_type=email_type,
        client_id=client_id,
        from_address=from_address,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        is_read=is_read,
        has_attachments=has_attachments,
        direction=direction,
        limit=limit,
        offset=offset
    )
    
    return results


@router.post("")
async def search_emails_post(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Full-text search (POST version for complex queries).
    """
    search_service = SearchService(db)
    
    results = search_service.search_emails(
        user_id=current_user.id,
        query=payload.query,
        email_type=payload.email_type,
        client_id=payload.client_id,
        from_address=payload.from_address,
        date_from=payload.date_from,
        date_to=payload.date_to,
        is_read=payload.is_read,
        has_attachments=payload.has_attachments,
        direction=payload.direction,
        limit=payload.limit,
        offset=payload.offset
    )
    
    return results


@router.get("/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=2, description="Partial query for suggestions"),
    limit: int = Query(10, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get search suggestions based on partial query.
    
    Returns subject suggestions and sender suggestions.
    """
    search_service = SearchService(db)
    
    suggestions = search_service.get_suggestions(
        user_id=current_user.id,
        query=q,
        limit=limit
    )
    
    return suggestions


@router.get("/filters")
async def get_available_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available filter options for search.
    
    Returns unique values for email types, senders, clients, etc.
    """
    search_service = SearchService(db)
    
    filters = search_service.get_filter_options(user_id=current_user.id)
    
    return filters


@router.post("/reindex")
async def reindex_emails(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reindex all emails for the current user.
    
    Use this if search results are inconsistent.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can trigger reindexing"
        )
    
    search_service = SearchService(db)
    
    result = search_service.reindex_user_emails(user_id=current_user.id)
    
    return result
