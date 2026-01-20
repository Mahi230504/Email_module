"""
Email template routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from models.user import User
from models.signature import EmailTemplate
from utils.decorators import get_current_user

router = APIRouter(prefix="/templates", tags=["Templates"])


class TemplateRequest(BaseModel):
    """Request model for creating/updating templates."""
    name: str
    description: Optional[str] = None
    email_type: Optional[str] = None
    subject_template: str
    body_template: Optional[str] = None
    body_html_template: Optional[str] = None
    variables: Optional[List[str]] = None


class RenderTemplateRequest(BaseModel):
    """Request model for rendering a template."""
    context: dict


@router.get("")
async def list_templates(
    email_type: Optional[str] = Query(None, description="Filter by email type"),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all email templates with optional filtering.
    """
    query = db.query(EmailTemplate).filter(EmailTemplate.is_active == True)
    
    if email_type:
        query = query.filter(EmailTemplate.email_type == email_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(EmailTemplate.name.ilike(search_term))
    
    total = query.count()
    
    templates = query.order_by(
        EmailTemplate.usage_count.desc(),
        EmailTemplate.name
    ).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "templates": [t.to_dict() for t in templates]
    }


@router.get("/types")
async def get_template_types():
    """Get available email types for templates."""
    from models.email import EmailType
    
    return {
        "types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in EmailType
        ]
    }


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific template by ID."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template.to_dict()


@router.post("")
async def create_template(
    payload: TemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new email template."""
    # Check for duplicate name
    existing = db.query(EmailTemplate).filter(
        EmailTemplate.name == payload.name,
        EmailTemplate.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    template = EmailTemplate(
        name=payload.name,
        description=payload.description,
        email_type=payload.email_type,
        subject_template=payload.subject_template,
        body_template=payload.body_template,
        body_html_template=payload.body_html_template,
        variables=payload.variables or [],
        created_by=current_user.id,
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {
        "message": "Template created successfully",
        "template": template.to_dict()
    }


@router.patch("/{template_id}")
async def update_template(
    template_id: str,
    payload: TemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing template."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check for duplicate name
    if payload.name != template.name:
        existing = db.query(EmailTemplate).filter(
            EmailTemplate.name == payload.name,
            EmailTemplate.is_active == True,
            EmailTemplate.id != template_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    template.name = payload.name
    template.description = payload.description
    template.email_type = payload.email_type
    template.subject_template = payload.subject_template
    template.body_template = payload.body_template
    template.body_html_template = payload.body_html_template
    template.variables = payload.variables or []
    
    db.commit()
    
    return {
        "message": "Template updated successfully",
        "template": template.to_dict()
    }


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a template (soft delete)."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_active = False
    db.commit()
    
    return {"message": "Template deleted successfully"}


@router.post("/{template_id}/render")
async def render_template(
    template_id: str,
    payload: RenderTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Render a template with provided context variables.
    
    Example context:
    ```json
    {
        "context": {
            "client_name": "John Doe",
            "tax_year": "FY 2025-26",
            "due_date": "March 31, 2026"
        }
    }
    ```
    """
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Render template
    subject, body_text, body_html = template.render(payload.context)
    
    # Increment usage count
    template.usage_count = (template.usage_count or 0) + 1
    db.commit()
    
    return {
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "variables_used": list(payload.context.keys())
    }


@router.post("/{template_id}/duplicate")
async def duplicate_template(
    template_id: str,
    new_name: str = Query(..., description="Name for the duplicated template"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a copy of an existing template."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id,
        EmailTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check for duplicate name
    existing = db.query(EmailTemplate).filter(
        EmailTemplate.name == new_name,
        EmailTemplate.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    new_template = EmailTemplate(
        name=new_name,
        description=template.description,
        email_type=template.email_type,
        subject_template=template.subject_template,
        body_template=template.body_template,
        body_html_template=template.body_html_template,
        variables=template.variables,
        created_by=current_user.id,
    )
    
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    return {
        "message": "Template duplicated successfully",
        "template": new_template.to_dict()
    }
