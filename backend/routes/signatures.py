"""
Signature and template routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from models.user import User
from models.signature import EmailSignature, EmailTemplate
from utils.decorators import get_current_user

router = APIRouter(tags=["Signatures & Templates"])


# Request Models
class SignatureRequest(BaseModel):
    name: str
    signature_html: Optional[str] = None
    signature_text: Optional[str] = None
    is_default: bool = False


class TemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    email_type: Optional[str] = None
    subject_template: str
    body_template: Optional[str] = None
    body_html_template: Optional[str] = None
    variables: Optional[List[str]] = None


# Signature Routes
signatures_router = APIRouter(prefix="/signatures")


@signatures_router.get("")
async def list_signatures(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's email signatures."""
    signatures = db.query(EmailSignature).filter(
        EmailSignature.user_id == current_user.id,
        EmailSignature.is_active == True
    ).all()
    
    return {
        "signatures": [s.to_dict() for s in signatures]
    }


@signatures_router.get("/{signature_id}")
async def get_signature(
    signature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific signature."""
    signature = db.query(EmailSignature).filter(
        EmailSignature.id == signature_id,
        EmailSignature.user_id == current_user.id
    ).first()
    
    if not signature:
        raise HTTPException(status_code=404, detail="Signature not found")
    
    return signature.to_dict()


@signatures_router.post("")
async def create_signature(
    payload: SignatureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new signature."""
    # If setting as default, unset other defaults
    if payload.is_default:
        db.query(EmailSignature).filter(
            EmailSignature.user_id == current_user.id,
            EmailSignature.is_default == True
        ).update({"is_default": False})
    
    signature = EmailSignature(
        user_id=current_user.id,
        name=payload.name,
        signature_html=payload.signature_html,
        signature_text=payload.signature_text,
        is_default=payload.is_default,
    )
    
    db.add(signature)
    db.commit()
    db.refresh(signature)
    
    return {
        "message": "Signature created",
        "signature": signature.to_dict()
    }


@signatures_router.patch("/{signature_id}")
async def update_signature(
    signature_id: str,
    payload: SignatureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a signature."""
    signature = db.query(EmailSignature).filter(
        EmailSignature.id == signature_id,
        EmailSignature.user_id == current_user.id
    ).first()
    
    if not signature:
        raise HTTPException(status_code=404, detail="Signature not found")
    
    # If setting as default, unset other defaults
    if payload.is_default and not signature.is_default:
        db.query(EmailSignature).filter(
            EmailSignature.user_id == current_user.id,
            EmailSignature.is_default == True
        ).update({"is_default": False})
    
    signature.name = payload.name
    signature.signature_html = payload.signature_html
    signature.signature_text = payload.signature_text
    signature.is_default = payload.is_default
    
    db.commit()
    
    return {
        "message": "Signature updated",
        "signature": signature.to_dict()
    }


@signatures_router.delete("/{signature_id}")
async def delete_signature(
    signature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a signature."""
    signature = db.query(EmailSignature).filter(
        EmailSignature.id == signature_id,
        EmailSignature.user_id == current_user.id
    ).first()
    
    if not signature:
        raise HTTPException(status_code=404, detail="Signature not found")
    
    signature.is_active = False
    db.commit()
    
    return {"message": "Signature deleted"}


# Template Routes
templates_router = APIRouter(prefix="/templates")


@templates_router.get("")
async def list_templates(
    email_type: Optional[str] = Query(None, description="Filter by email type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List email templates."""
    query = db.query(EmailTemplate).filter(EmailTemplate.is_active == True)
    
    if email_type:
        query = query.filter(EmailTemplate.email_type == email_type)
    
    templates = query.all()
    
    return {
        "templates": [t.to_dict() for t in templates]
    }


@templates_router.get("/{template_id}")
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific template."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template.to_dict()


@templates_router.post("")
async def create_template(
    payload: TemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new template."""
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
        "message": "Template created",
        "template": template.to_dict()
    }


@templates_router.patch("/{template_id}")
async def update_template(
    template_id: str,
    payload: TemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a template."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.name = payload.name
    template.description = payload.description
    template.email_type = payload.email_type
    template.subject_template = payload.subject_template
    template.body_template = payload.body_template
    template.body_html_template = payload.body_html_template
    template.variables = payload.variables or []
    
    db.commit()
    
    return {
        "message": "Template updated",
        "template": template.to_dict()
    }


@templates_router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a template."""
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template.is_active = False
    db.commit()
    
    return {"message": "Template deleted"}


@templates_router.post("/{template_id}/render")
async def render_template(
    template_id: str,
    context: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Render a template with context variables.
    
    Example context:
    {
        "client_name": "John Doe",
        "tax_year": "FY 2025-26",
        "due_date": "March 31, 2026"
    }
    """
    template = db.query(EmailTemplate).filter(
        EmailTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    subject, body_text, body_html = template.render(context)
    
    # Increment usage count
    template.usage_count = (template.usage_count or 0) + 1
    db.commit()
    
    return {
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html
    }


# Combine routers
router.include_router(signatures_router)
router.include_router(templates_router)
