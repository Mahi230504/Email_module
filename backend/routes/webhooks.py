"""
Webhook routes for Microsoft Graph notifications.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from models.user import User
from services.auth_service import AuthService
from services.graph_service import GraphService
from services.email_service import EmailService
from utils.decorators import get_current_user
from utils.encryption import get_encryption

settings = get_settings()
encryption = get_encryption()
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/notify")
async def webhook_notification(request: Request, db: Session = Depends(get_db)):
    """
    Receive notifications from Microsoft Graph.
    
    Microsoft sends notifications when emails arrive, are read, deleted, etc.
    This endpoint is called in real-time (<5 seconds after event).
    """
    # Handle validation token (Microsoft validation request)
    # Check query params FIRST - do not await body yet as it might timeout for validation requests
    if "validationToken" in request.query_params:
        validation_token = request.query_params["validationToken"]
        return PlainTextResponse(validation_token)

    try:
        body = await request.json()
    except Exception:
        # If no body or invalid JSON, and no validation token, raise error
        raise HTTPException(status_code=400, detail="Invalid request body")

    # Handle validation tokens in body (alternative format)
    if "validationTokens" in body:
        return PlainTextResponse(body["validationTokens"][0])
    
    # Process notifications
    notifications = body.get("value", [])
    
    processed = 0
    errors = []
    
    for notification in notifications:
        try:
            # Verify client state (security)
            if notification.get("clientState") != settings.webhook_secret:
                errors.append("Invalid client state")
                continue
            
            subscription_id = notification.get("subscriptionId")
            change_type = notification.get("changeType")
            resource = notification.get("resource", "")
            resource_data = notification.get("resourceData", {})
            
            # Find user by subscription
            user = db.query(User).filter(
                User.graph_subscription_id == subscription_id
            ).first()
            
            if not user:
                errors.append(f"Unknown subscription: {subscription_id}")
                continue
            
            # Get valid access token
            try:
                access_token = AuthService.get_valid_access_token(db, user)
            except Exception:
                errors.append(f"Failed to get token for user {user.id}")
                continue
            
            # Process based on change type
            if change_type == "created":
                # New email arrived
                message_id = resource_data.get("id")
                if message_id:
                    graph = GraphService(access_token)
                    email_data = graph.get_message(message_id)
                    
                    service = EmailService(db, graph)
                    service.sync_email_from_graph(email_data, user)
                    processed += 1
            
            elif change_type == "updated":
                # Email was updated (read, flagged, etc.)
                # Could sync the updated status here
                processed += 1
            
            elif change_type == "deleted":
                # Email was deleted
                # Could mark as deleted in our DB
                processed += 1
                
        except Exception as e:
            errors.append(str(e))
    
    return {
        "status": "processed",
        "processed": processed,
        "errors": errors if errors else None
    }


@router.post("/subscribe")
def create_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create webhook subscription for the current user's inbox.
    
    Microsoft will send notifications to /webhooks/notify when emails arrive.
    """
    try:
        # Get valid access token
        access_token = AuthService.get_valid_access_token(db, current_user)
        
        # Create Graph service
        graph = GraphService(access_token)
        
        # Check if subscription already exists
        if current_user.graph_subscription_id:
            try:
                # Try to renew existing subscription
                subscription = graph.renew_subscription(
                    current_user.graph_subscription_id
                )
                
                current_user.graph_subscription_expires_at = datetime.fromisoformat(
                    subscription["expirationDateTime"].replace("Z", "+00:00")
                )
                db.commit()
                
                return {
                    "message": "Subscription renewed",
                    "subscription_id": subscription["id"],
                    "expires_at": subscription["expirationDateTime"]
                }
            except Exception:
                # Subscription may have expired, create new one
                pass
        
        # Create new subscription
        subscription = graph.create_subscription(
            change_types=["created", "updated", "deleted"],
            resource="/me/mailFolders('inbox')/messages",
            expiration_minutes=4320  # 3 days
        )
        
        # Save subscription details
        current_user.graph_subscription_id = subscription["id"]
        current_user.graph_subscription_expires_at = datetime.fromisoformat(
            subscription["expirationDateTime"].replace("Z", "+00:00")
        )
        db.commit()
        
        return {
            "message": "Subscription created",
            "subscription_id": subscription["id"],
            "expires_at": subscription["expirationDateTime"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/subscribe")
def delete_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete the webhook subscription for the current user.
    """
    if not current_user.graph_subscription_id:
        return {"message": "No active subscription"}
    
    try:
        access_token = AuthService.get_valid_access_token(db, current_user)
        graph = GraphService(access_token)
        
        graph.delete_subscription(current_user.graph_subscription_id)
        
        current_user.graph_subscription_id = None
        current_user.graph_subscription_expires_at = None
        db.commit()
        
        return {"message": "Subscription deleted"}
        
    except Exception as e:
        # Subscription might already be deleted
        current_user.graph_subscription_id = None
        current_user.graph_subscription_expires_at = None
        db.commit()
        
        return {"message": "Subscription cleared", "note": str(e)}


@router.get("/status")
def subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get webhook subscription status.
    """
    if not current_user.graph_subscription_id:
        return {
            "active": False,
            "subscription_id": None,
            "expires_at": None
        }
    
    expires_at = current_user.graph_subscription_expires_at
    is_expired = expires_at and datetime.utcnow() >= expires_at
    
    return {
        "active": not is_expired,
        "subscription_id": current_user.graph_subscription_id,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "is_expired": is_expired
    }
