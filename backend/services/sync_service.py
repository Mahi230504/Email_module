"""
Sync service for email synchronization.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.config import get_settings
from models.user import User
from models.email import Email
from services.auth_service import AuthService
from services.graph_service import GraphService
from services.email_service import EmailService

settings = get_settings()


class SyncService:
    """
    Email synchronization service.
    
    Handles both manual and background sync operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize sync service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def sync_user_inbox(
        self,
        user: User,
        folder: str = "inbox",
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Sync emails from user's inbox.
        
        Args:
            user: User to sync
            folder: Mail folder to sync
            limit: Maximum emails to fetch
            since: Only fetch emails after this date
            
        Returns:
            Sync result with counts
        """
        try:
            # Get valid access token
            access_token = AuthService.get_valid_access_token(self.db, user)
            
            # Create services
            graph = GraphService(access_token)
            email_service = EmailService(self.db, graph)
            
            # Build filter query if since is provided
            filter_query = None
            if since:
                filter_query = f"receivedDateTime ge {since.isoformat()}Z"
            
            # Fetch emails from Graph
            result = graph.list_messages(
                folder=folder,
                limit=limit,
                filter_query=filter_query
            )
            
            # Sync each email
            synced_count = 0
            new_count = 0
            updated_count = 0
            errors = []
            
            for email_data in result.get("value", []):
                try:
                    graph_message_id = email_data.get("id")
                    
                    # Check if email exists
                    existing = self.db.query(Email).filter(
                        Email.graph_message_id == graph_message_id
                    ).first()
                    
                    if existing:
                        # Update existing email
                        updated_count += 1
                    else:
                        # Sync new email
                        email_service.sync_email_from_graph(email_data, user)
                        new_count += 1
                    
                    synced_count += 1
                    
                except Exception as e:
                    errors.append({
                        "message_id": email_data.get("id"),
                        "error": str(e)
                    })
            
            # Update last sync time
            user.last_email_sync_time = datetime.utcnow()
            self.db.commit()
            
            return {
                "status": "success",
                "synced_count": synced_count,
                "new_count": new_count,
                "updated_count": updated_count,
                "errors": errors if errors else None,
                "last_sync": user.last_email_sync_time.isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def sync_all_folders(
        self,
        user: User,
        limit_per_folder: int = 50
    ) -> Dict[str, Any]:
        """
        Sync emails from all standard folders.
        
        Args:
            user: User to sync
            limit_per_folder: Max emails per folder
            
        Returns:
            Combined sync result
        """
        folders = ["inbox", "sentItems", "drafts"]
        results = {}
        
        for folder in folders:
            results[folder] = self.sync_user_inbox(
                user=user,
                folder=folder,
                limit=limit_per_folder
            )
        
        total_synced = sum(
            r.get("synced_count", 0) for r in results.values()
        )
        
        return {
            "status": "success",
            "total_synced": total_synced,
            "folders": results
        }
    
    def sync_incremental(
        self,
        user: User,
        folder: str = "inbox"
    ) -> Dict[str, Any]:
        """
        Incremental sync - only fetch emails since last sync.
        
        Args:
            user: User to sync
            folder: Folder to sync
            
        Returns:
            Sync result
        """
        since = user.last_email_sync_time or (datetime.utcnow() - timedelta(days=7))
        
        return self.sync_user_inbox(
            user=user,
            folder=folder,
            limit=100,
            since=since
        )
    
    def get_sync_status(self, user: User) -> Dict[str, Any]:
        """
        Get synchronization status for a user.
        
        Args:
            user: User to check
            
        Returns:
            Sync status with counts
        """
        # Count emails
        email_count = self.db.query(Email).filter(
            Email.user_id == user.id
        ).count()
        
        # Count unread
        unread_count = self.db.query(Email).filter(
            Email.user_id == user.id,
            Email.is_read == False
        ).count()
        
        # Get latest email date
        latest_email = self.db.query(Email).filter(
            Email.user_id == user.id
        ).order_by(Email.received_date_time.desc()).first()
        
        return {
            "last_sync": user.last_email_sync_time.isoformat() if user.last_email_sync_time else None,
            "email_count": email_count,
            "unread_count": unread_count,
            "latest_email_date": latest_email.received_date_time.isoformat() if latest_email and latest_email.received_date_time else None,
            "subscription_active": bool(user.graph_subscription_id),
            "subscription_expires": user.graph_subscription_expires_at.isoformat() if user.graph_subscription_expires_at else None
        }
    
    def create_or_renew_subscription(self, user: User) -> Dict[str, Any]:
        """
        Create or renew webhook subscription for real-time sync.
        
        Args:
            user: User to create subscription for
            
        Returns:
            Subscription details
        """
        try:
            access_token = AuthService.get_valid_access_token(self.db, user)
            graph = GraphService(access_token)
            
            if user.graph_subscription_id:
                # Try to renew existing
                try:
                    subscription = graph.renew_subscription(
                        user.graph_subscription_id
                    )
                    
                    user.graph_subscription_expires_at = datetime.fromisoformat(
                        subscription["expirationDateTime"].replace("Z", "+00:00")
                    )
                    self.db.commit()
                    
                    return {
                        "status": "renewed",
                        "subscription_id": subscription["id"],
                        "expires_at": subscription["expirationDateTime"]
                    }
                    
                except Exception:
                    # Subscription expired, create new one
                    pass
            
            # Create new subscription
            subscription = graph.create_subscription(
                change_types=["created", "updated", "deleted"],
                resource="/me/mailFolders('inbox')/messages",
                expiration_minutes=4320  # 3 days
            )
            
            user.graph_subscription_id = subscription["id"]
            user.graph_subscription_expires_at = datetime.fromisoformat(
                subscription["expirationDateTime"].replace("Z", "+00:00")
            )
            self.db.commit()
            
            return {
                "status": "created",
                "subscription_id": subscription["id"],
                "expires_at": subscription["expirationDateTime"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def delete_subscription(self, user: User) -> Dict[str, Any]:
        """
        Delete webhook subscription.
        
        Args:
            user: User to delete subscription for
            
        Returns:
            Result
        """
        if not user.graph_subscription_id:
            return {"status": "no_subscription"}
        
        try:
            access_token = AuthService.get_valid_access_token(self.db, user)
            graph = GraphService(access_token)
            
            graph.delete_subscription(user.graph_subscription_id)
            
            user.graph_subscription_id = None
            user.graph_subscription_expires_at = None
            self.db.commit()
            
            return {"status": "deleted"}
            
        except Exception as e:
            # Clear anyway
            user.graph_subscription_id = None
            user.graph_subscription_expires_at = None
            self.db.commit()
            
            return {"status": "cleared", "note": str(e)}
