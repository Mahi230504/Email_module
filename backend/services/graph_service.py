"""
Microsoft Graph API service for email operations.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from app.config import get_settings
from utils.exceptions import GraphAPIError

settings = get_settings()


class GraphService:
    """Microsoft Graph API wrapper for email operations."""
    
    GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, access_token: str):
        """
        Initialize Graph service with access token.
        
        Args:
            access_token: Valid Microsoft access token
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        expected_codes: List[int] = [200]
    ) -> Dict:
        """
        Make HTTP request to Graph API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON body
            expected_codes: Expected success status codes
            
        Returns:
            Response JSON
            
        Raises:
            GraphAPIError: If request fails
        """
        url = f"{self.GRAPH_API_URL}{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            params=params,
            json=json_data,
        )
        
        if response.status_code not in expected_codes:
            print(f"\n[GRAPH API ERROR] {method} {endpoint} -> {response.status_code}")
            print(f"[GRAPH API RESPONSE] {response.text}\n")
            raise GraphAPIError(
                f"{method} {endpoint} failed: {response.text}",
                status_code=response.status_code
            )
        
        if response.status_code in [202, 204]:  # No content or Accepted (async)
            return {}
        
        return response.json()
    
    # =========================================================================
    # Message Operations
    # =========================================================================
    
    def list_messages(
        self,
        folder: str = "inbox",
        limit: int = 50,
        skip: int = 0,
        filter_query: Optional[str] = None,
        select_fields: Optional[List[str]] = None,
        order_by: str = "receivedDateTime desc"
    ) -> Dict:
        """
        List emails from a folder.
        
        Args:
            folder: Folder name (inbox, sentItems, drafts)
            limit: Number of messages to return
            skip: Number to skip (pagination)
            filter_query: OData filter expression
            select_fields: Fields to select
            order_by: Sort order
            
        Returns:
            Dict with 'value' list of messages and '@odata.nextLink' if more
        """
        default_fields = [
            "id", "subject", "from", "toRecipients", "ccRecipients",
            "receivedDateTime", "sentDateTime", "bodyPreview", "body",
            "isRead", "hasAttachments", "internetMessageId", "conversationId",
            "conversationIndex", "parentFolderId", "importance", "flag",
            "internetMessageHeaders"
        ]
        
        params = {
            "$select": ",".join(select_fields or default_fields),
            "$orderby": order_by,
            "$top": limit,
            "$skip": skip,
        }
        
        if filter_query:
            params["$filter"] = filter_query
        
        return self._make_request(
            "GET",
            f"/me/mailFolders('{folder}')/messages",
            params=params
        )
    
    def get_message(self, message_id: str, include_headers: bool = True) -> Dict:
        """
        Get full message details.
        
        Args:
            message_id: Graph message ID
            include_headers: Include internet message headers
            
        Returns:
            Full message data
        """
        select = (
            "id,subject,from,toRecipients,ccRecipients,bccRecipients,"
            "body,bodyPreview,receivedDateTime,sentDateTime,isRead,"
            "hasAttachments,internetMessageId,conversationId,conversationIndex,"
            "parentFolderId,importance,flag,replyTo"
        )
        
        if include_headers:
            select += ",internetMessageHeaders"
        
        params = {"$select": select}
        
        return self._make_request("GET", f"/me/messages/{message_id}", params=params)
    
    def send_email(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        body_type: str = "HTML",
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        reply_to: Optional[List[str]] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        attachments: Optional[List[Dict]] = None,
        save_to_sent: bool = True
    ) -> Dict:
        """
        Send an email.
        
        Args:
            to_recipients: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: 'HTML' or 'Text'
            cc_recipients: CC recipients
            bcc_recipients: BCC recipients
            reply_to: Reply-to addresses
            custom_headers: Custom headers like X-Tax-Email-ID
            attachments: List of attachment dicts
            save_to_sent: Save copy to sent items
            
        Returns:
            Empty dict on success (202 Accepted)
        """
        message = {
            "subject": subject,
            "body": {
                "contentType": body_type,
                "content": body,
            },
            "toRecipients": [
                {"emailAddress": {"address": addr}} for addr in to_recipients
            ],
        }
        
        if cc_recipients:
            message["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc_recipients
            ]
        
        if bcc_recipients:
            message["bccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in bcc_recipients
            ]
        
        if reply_to:
            message["replyTo"] = [
                {"emailAddress": {"address": addr}} for addr in reply_to
            ]
        
        if custom_headers:
            message["internetMessageHeaders"] = [
                {"name": k, "value": v} for k, v in custom_headers.items()
            ]
        
        if attachments:
            message["attachments"] = attachments
        
        payload = {
            "message": message,
            "saveToSentItems": save_to_sent,
        }
        
        return self._make_request(
            "POST",
            "/me/sendMail",
            json_data=payload,
            expected_codes=[200, 202]
        )
    
    def reply_to_email(
        self,
        message_id: str,
        body: str,
        body_type: str = "HTML",
        reply_all: bool = False
    ) -> Dict:
        """
        Reply to an email.
        
        Args:
            message_id: Original message ID
            body: Reply body
            body_type: 'HTML' or 'Text'
            reply_all: Reply to all recipients
            
        Returns:
            Empty dict on success
        """
        endpoint = "replyAll" if reply_all else "reply"
        
        payload = {
            "comment": body,
        }
        
        return self._make_request(
            "POST",
            f"/me/messages/{message_id}/{endpoint}",
            json_data=payload,
            expected_codes=[200, 202]
        )
    
    def forward_email(
        self,
        message_id: str,
        to_recipients: List[str],
        comment: Optional[str] = None
    ) -> Dict:
        """
        Forward an email.
        
        Args:
            message_id: Message to forward
            to_recipients: Recipients
            comment: Optional comment to add
            
        Returns:
            Empty dict on success
        """
        payload = {
            "toRecipients": [
                {"emailAddress": {"address": addr}} for addr in to_recipients
            ],
        }
        
        if comment:
            payload["comment"] = comment
        
        return self._make_request(
            "POST",
            f"/me/messages/{message_id}/forward",
            json_data=payload,
            expected_codes=[200, 202]
        )
    
    def create_draft(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        body_type: str = "HTML",
        cc_recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a draft email.
        
        Args:
            to_recipients: Recipients
            subject: Subject
            body: Body content
            body_type: 'HTML' or 'Text'
            cc_recipients: CC recipients
            
        Returns:
            Created draft message
        """
        message = {
            "subject": subject,
            "body": {
                "contentType": body_type,
                "content": body,
            },
            "toRecipients": [
                {"emailAddress": {"address": addr}} for addr in to_recipients
            ],
        }
        
        if cc_recipients:
            message["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc_recipients
            ]
        
        return self._make_request(
            "POST",
            "/me/mailFolders('drafts')/messages",
            json_data=message,
            expected_codes=[201]
        )
    
    def update_message(self, message_id: str, updates: Dict) -> Dict:
        """
        Update message properties.
        
        Args:
            message_id: Message ID
            updates: Properties to update (isRead, flag, etc.)
            
        Returns:
            Updated message
        """
        return self._make_request(
            "PATCH",
            f"/me/messages/{message_id}",
            json_data=updates
        )
    
    def mark_as_read(self, message_id: str, is_read: bool = True) -> Dict:
        """Mark message as read/unread."""
        return self.update_message(message_id, {"isRead": is_read})
    
    def delete_message(self, message_id: str) -> Dict:
        """Delete a message."""
        return self._make_request(
            "DELETE",
            f"/me/messages/{message_id}",
            expected_codes=[204]
        )
    
    def move_message(self, message_id: str, destination_folder: str) -> Dict:
        """
        Move message to another folder.
        
        Args:
            message_id: Message ID
            destination_folder: Folder ID or well-known name
            
        Returns:
            Moved message
        """
        return self._make_request(
            "POST",
            f"/me/messages/{message_id}/move",
            json_data={"destinationId": destination_folder},
            expected_codes=[201]
        )
    
    # =========================================================================
    # Attachment Operations
    # =========================================================================
    
    def list_attachments(self, message_id: str) -> Dict:
        """List attachments for a message."""
        return self._make_request("GET", f"/me/messages/{message_id}/attachments")
    
    def get_attachment(self, message_id: str, attachment_id: str) -> Dict:
        """Get attachment content."""
        return self._make_request(
            "GET",
            f"/me/messages/{message_id}/attachments/{attachment_id}"
        )
    
    # =========================================================================
    # Folder Operations
    # =========================================================================
    
    def list_folders(self) -> Dict:
        """List mail folders."""
        return self._make_request("GET", "/me/mailFolders")
    
    def get_folder(self, folder_id: str) -> Dict:
        """Get folder details."""
        return self._make_request("GET", f"/me/mailFolders/{folder_id}")
    
    # =========================================================================
    # Subscription Operations (Webhooks)
    # =========================================================================
    
    def create_subscription(
        self,
        change_types: List[str],
        resource: str = "/me/mailFolders('inbox')/messages",
        expiration_minutes: int = 4320  # 3 days
    ) -> Dict:
        """
        Create webhook subscription for change notifications.
        
        Args:
            change_types: List of change types (created, updated, deleted)
            resource: Resource to watch
            expiration_minutes: Subscription expiration
            
        Returns:
            Created subscription
        """
        expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        
        payload = {
            "changeType": ",".join(change_types),
            "notificationUrl": f"{settings.platform_url}/webhooks/notify",
            "resource": resource,
            "expirationDateTime": expiration.isoformat() + "Z",
            "clientState": settings.webhook_secret,
        }
        
        return self._make_request(
            "POST",
            "/subscriptions",
            json_data=payload,
            expected_codes=[201]
        )
    
    def renew_subscription(self, subscription_id: str, expiration_minutes: int = 4320) -> Dict:
        """
        Renew webhook subscription.
        
        Args:
            subscription_id: Subscription to renew
            expiration_minutes: New expiration time
            
        Returns:
            Updated subscription
        """
        expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        
        return self._make_request(
            "PATCH",
            f"/subscriptions/{subscription_id}",
            json_data={"expirationDateTime": expiration.isoformat() + "Z"}
        )
    
    def delete_subscription(self, subscription_id: str) -> Dict:
        """Delete a subscription."""
        return self._make_request(
            "DELETE",
            f"/subscriptions/{subscription_id}",
            expected_codes=[204]
        )
    
    def list_subscriptions(self) -> Dict:
        """List all active subscriptions."""
        return self._make_request("GET", "/subscriptions")
    
    # =========================================================================
    # User Operations
    # =========================================================================
    
    def get_me(self) -> Dict:
        """Get current user profile."""
        return self._make_request("GET", "/me")
    
    def get_mailbox_settings(self) -> Dict:
        """Get user's mailbox settings."""
        return self._make_request("GET", "/me/mailboxSettings")
