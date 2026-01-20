"""
Celery background tasks for email synchronization.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from celery import shared_task

from tasks.celery_app import celery_app
from app.database import SessionLocal
from app.config import get_settings
from utils.encryption import get_encryption

settings = get_settings()
encryption = get_encryption()


@celery_app.task(bind=True, max_retries=3)
def process_webhook_notification(self, notification: Dict[str, Any]):
    """
    Process incoming email notification from Microsoft Graph webhook.
    
    Called when a new email arrives in user's inbox.
    """
    from models.user import User
    from services.auth_service import AuthService
    from services.graph_service import GraphService
    from services.email_service import EmailService
    
    db = SessionLocal()
    
    try:
        subscription_id = notification.get("subscriptionId")
        change_type = notification.get("changeType")
        resource_data = notification.get("resourceData", {})
        
        # Find user by subscription
        user = db.query(User).filter(
            User.graph_subscription_id == subscription_id
        ).first()
        
        if not user:
            print(f"⚠️  Unknown subscription: {subscription_id}")
            return {"status": "error", "reason": "unknown_subscription"}
        
        # Get valid access token
        access_token = AuthService.get_valid_access_token(db, user)
        
        if change_type == "created":
            # New email arrived
            message_id = resource_data.get("id")
            
            if message_id:
                graph = GraphService(access_token)
                email_data = graph.get_message(message_id)
                
                service = EmailService(db, graph)
                email = service.sync_email_from_graph(email_data, user)
                
                print(f"✅ Synced email: {email.subject}")
                
                return {
                    "status": "success",
                    "email_id": email.id,
                    "thread_id": email.thread_id
                }
        
        elif change_type == "updated":
            # Email was updated (read, flagged, etc.)
            print(f"📧 Email updated notification received")
            return {"status": "acknowledged", "change_type": "updated"}
        
        elif change_type == "deleted":
            # Email was deleted
            print(f"🗑️  Email deleted notification received")
            return {"status": "acknowledged", "change_type": "deleted"}
        
        return {"status": "processed"}
        
    except Exception as exc:
        print(f"❌ Error processing notification: {exc}")
        
        # Retry with exponential backoff
        retry_delays = [30, 300, 1800]  # 30s, 5m, 30m
        countdown = retry_delays[min(self.request.retries, len(retry_delays) - 1)]
        
        raise self.retry(exc=exc, countdown=countdown)
        
    finally:
        db.close()


@celery_app.task
def sync_user_emails(user_id: str, folder: str = "inbox", limit: int = 50):
    """
    Sync emails for a specific user.
    
    Can be triggered manually or as part of background sync.
    """
    from models.user import User
    from services.auth_service import AuthService
    from services.graph_service import GraphService
    from services.email_service import EmailService
    
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"status": "error", "reason": "user_not_found"}
        
        # Get valid access token
        access_token = AuthService.get_valid_access_token(db, user)
        
        # Fetch emails from Graph
        graph = GraphService(access_token)
        result = graph.list_messages(folder=folder, limit=limit)
        
        # Sync each email
        service = EmailService(db, graph)
        synced_count = 0
        
        for email_data in result.get("value", []):
            try:
                service.sync_email_from_graph(email_data, user)
                synced_count += 1
            except Exception as e:
                print(f"Error syncing email: {e}")
        
        # Update last sync time
        user.last_email_sync_time = datetime.utcnow()
        db.commit()
        
        print(f"✅ Synced {synced_count} emails for user {user.email}")
        
        return {
            "status": "success",
            "synced_count": synced_count,
            "user_id": user_id
        }
        
    except Exception as e:
        print(f"❌ Error syncing emails for user {user_id}: {e}")
        return {"status": "error", "reason": str(e)}
        
    finally:
        db.close()


@celery_app.task
def background_email_sync():
    """
    Background sync job that runs periodically.
    
    Fetches emails for all active users as a fallback
    in case webhooks miss any notifications.
    """
    from models.user import User
    
    db = SessionLocal()
    
    try:
        # Get all active users with tokens
        users = db.query(User).filter(
            User.is_active == True,
            User.access_token.isnot(None)
        ).all()
        
        print(f"🔄 Background sync starting for {len(users)} users...")
        
        synced_users = 0
        
        for user in users:
            try:
                # Schedule sync task for each user
                sync_user_emails.delay(user.id, "inbox", 20)
                synced_users += 1
            except Exception as e:
                print(f"Error scheduling sync for user {user.id}: {e}")
        
        print(f"✅ Scheduled sync for {synced_users} users")
        
        return {
            "status": "success",
            "scheduled_users": synced_users
        }
        
    finally:
        db.close()


@celery_app.task
def renew_expiring_subscriptions():
    """
    Renew webhook subscriptions that are about to expire.
    
    Runs periodically to ensure continuous webhook delivery.
    """
    from models.user import User
    from services.auth_service import AuthService
    from services.graph_service import GraphService
    
    db = SessionLocal()
    
    try:
        # Find subscriptions expiring in next 24 hours
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        expiring_users = db.query(User).filter(
            User.graph_subscription_id.isnot(None),
            User.graph_subscription_expires_at <= tomorrow
        ).all()
        
        print(f"🔄 Renewing {len(expiring_users)} expiring subscriptions...")
        
        renewed_count = 0
        
        for user in expiring_users:
            try:
                access_token = AuthService.get_valid_access_token(db, user)
                graph = GraphService(access_token)
                
                subscription = graph.renew_subscription(
                    user.graph_subscription_id
                )
                
                user.graph_subscription_expires_at = datetime.fromisoformat(
                    subscription["expirationDateTime"].replace("Z", "+00:00")
                )
                
                renewed_count += 1
                print(f"✅ Renewed subscription for {user.email}")
                
            except Exception as e:
                print(f"❌ Failed to renew subscription for {user.email}: {e}")
                
                # Clear invalid subscription
                user.graph_subscription_id = None
                user.graph_subscription_expires_at = None
        
        db.commit()
        
        print(f"✅ Renewed {renewed_count} subscriptions")
        
        return {
            "status": "success",
            "renewed_count": renewed_count
        }
        
    finally:
        db.close()


@celery_app.task
def index_email_to_elasticsearch(email_id: str):
    """
    Index an email to Elasticsearch for full-text search.
    """
    from models.email import Email
    from app.database import es_client
    
    db = SessionLocal()
    
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        
        if not email:
            return {"status": "error", "reason": "email_not_found"}
        
        # Index to Elasticsearch
        doc = {
            "email_id": email.id,
            "thread_id": email.thread_id,
            "subject": email.subject,
            "body": email.body or email.body_preview,
            "from_address": email.from_address,
            "from_name": email.from_name,
            "to_recipients": email.to_recipients,
            "cc_recipients": email.cc_recipients,
            "email_type": email.email_type,
            "client_id": email.client_id,
            "user_id": email.user_id,
            "direction": email.direction,
            "received_date_time": email.received_date_time.isoformat() if email.received_date_time else None,
            "has_attachments": email.has_attachments,
            "is_read": email.is_read,
            "is_flagged": email.is_flagged,
        }
        
        es_client.index(
            index="emails",
            id=email.id,
            document=doc
        )
        
        print(f"✅ Indexed email {email.id} to Elasticsearch")
        
        return {"status": "success", "email_id": email.id}
        
    except Exception as e:
        print(f"❌ Error indexing email: {e}")
        return {"status": "error", "reason": str(e)}
        
    finally:
        db.close()
