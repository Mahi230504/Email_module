# Outlook Email Module - Quick Start Implementation Guide
## For Cursor IDE - Ready to Code

This file provides all the code skeletons and setup instructions you need to start building the Outlook email module immediately.

---

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Core Project Structure](#core-project-structure)
3. [Step 1: Azure AD Configuration](#step-1-azure-ad-configuration)
4. [Step 2: Database Models](#step-2-database-models)
5. [Step 3: Authentication Service](#step-3-authentication-service)
6. [Step 4: Microsoft Graph Integration](#step-4-microsoft-graph-integration)
7. [Step 5: Email Threading Engine](#step-5-email-threading-engine)
8. [Step 6: Webhook Handler](#step-6-webhook-handler)
9. [Step 7: Email CRUD Operations](#step-7-email-crud-operations)
10. [Step 8: Frontend Scaffold](#step-8-frontend-scaffold)
11. [Testing & Deployment](#testing--deployment)

---

## Environment Setup

### Prerequisites
```bash
# Install Python 3.10+
python3 --version

# Install PostgreSQL 14+
psql --version

# Install Elasticsearch 8.0+
# Install Redis 7.0+

# Install Docker (recommended)
docker --version
```

### Create Project Structure
```bash
mkdir outlook-email-module
cd outlook-email-module

# Backend structure
mkdir backend
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary
pip install msgraph-sdk azure-identity
pip install python-dotenv
pip install celery redis
pip install elasticsearch
pip install python-multipart aiohttp
pip install pydantic

# Create folders
mkdir app models routes services utils

# Frontend structure
cd ..
mkdir frontend
cd frontend
npm init -y
npm install react react-dom react-router-dom
npm install axios zustand react-query
npm install @mui/material @emotion/react @emotion/styled
npm install socket.io-client
```

### Create .env File
```bash
# Backend/.env

# Microsoft Azure Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
PLATFORM_URL=https://yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tax_platform_db
REDIS_URL=redis://localhost:6379

# Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Security
JWT_SECRET_KEY=your-super-secret-key-change-this
WEBHOOK_SECRET=your-webhook-secret

# Features
ENABLE_WEBHOOKS=true
BACKGROUND_SYNC_INTERVAL=120  # seconds
```

---

## Core Project Structure

```
outlook-email-module/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration management
│   │   └── database.py             # Database connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User model
│   │   ├── email.py                # Email model
│   │   ├── client.py               # Client model
│   │   ├── signature.py            # Signature model
│   │   └── audit_log.py            # Audit logging
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication endpoints
│   │   ├── emails.py               # Email CRUD endpoints
│   │   ├── webhooks.py             # Webhook handlers
│   │   ├── filters.py              # Filter endpoints
│   │   └── signatures.py           # Signature management
│   ├── services/
│   │   ├── __init__.py
│   │   ├── graph_service.py        # Microsoft Graph API calls
│   │   ├── threading_engine.py     # Email threading logic
│   │   ├── auth_service.py         # OAuth handling
│   │   ├── email_service.py        # Email operations
│   │   ├── search_service.py       # Elasticsearch queries
│   │   └── sync_service.py         # Background sync jobs
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py           # Auth decorators
│   │   ├── exceptions.py           # Custom exceptions
│   │   ├── validators.py           # Input validation
│   │   └── helpers.py              # Utility functions
│   ├── celery_app.py               # Celery configuration
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── EmailList.jsx
│   │   │   ├── EmailThread.jsx
│   │   │   ├── EmailComposer.jsx
│   │   │   ├── Filters.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── pages/
│   │   │   ├── InboxPage.jsx
│   │   │   ├── ThreadPage.jsx
│   │   │   └── SettingsPage.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── websocket.js
│   │   ├── store/
│   │   │   ├── emailStore.js
│   │   │   └── userStore.js
│   │   ├── App.jsx
│   │   └── index.jsx
│   └── package.json
└── docker-compose.yml              # PostgreSQL, Redis, Elasticsearch
```

---

## Step 1: Azure AD Configuration

### Manual Setup (One-time)

```
1. Go to: https://portal.azure.com
2. Navigate to: Azure Active Directory → App registrations
3. Click: "+ New registration"
4. Fill:
   - Name: "Tax Platform Email Module"
   - Supported account types: "Accounts in any organizational directory"
   - Redirect URI: "https://yourdomain.com/auth/callback"
5. Click: Register

6. In the app registration:
   - Copy Application (client) ID → Save to .env as AZURE_CLIENT_ID
   - Copy Directory (tenant) ID → Save to .env as AZURE_TENANT_ID

7. Go to: Certificates & secrets → New client secret
   - Value → Copy to .env as AZURE_CLIENT_SECRET

8. Go to: API permissions
   - Click: "+ Add a permission"
   - Select: Microsoft Graph
   - Select: Delegated permissions
   - Search and select:
     ✓ Mail.Read
     ✓ Mail.ReadWrite
     ✓ Mail.Send
     ✓ MailboxSettings.ReadWrite
     ✓ User.Read
   - Click: Grant admin consent
```

### Programmatic Setup (Optional - for multi-tenant)

```python
# backend/utils/azure_setup.py

from azure.identity import ClientSecretCredential
from azure.mgmt.authorization import AuthorizationManagementClient
import json
import os

def create_azure_app_registration():
    """
    Creates an app registration in Azure AD programmatically.
    Requires: Global Administrator role
    """
    
    # This requires Microsoft Graph API with Application.ReadWrite.All permission
    # Usually easier to do manually via portal.azure.com
    
    pass
```

---

## Step 2: Database Models

### models/user.py
```python
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String)
    last_name = Column(String)
    
    # OAuth tokens (encrypted)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    
    # Graph subscription
    graph_subscription_id = Column(String)
    graph_subscription_expires_at = Column(DateTime)
    
    # Role-based access
    role = Column(String, default="accountant")  # admin, accountant, client_manager
    
    # Settings
    default_signature_id = Column(String, ForeignKey("email_signatures.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_email_sync_time = Column(DateTime)
    
    # Relationships
    emails = relationship("Email", back_populates="user")
    signatures = relationship("EmailSignature", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"
```

### models/email.py
```python
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class EmailThread(Base):
    __tablename__ = "email_threads"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, ForeignKey("clients.id"))
    
    # Thread metadata
    subject = Column(String, nullable=False)
    email_type = Column(String, index=True)  # NIL_FILING, VAT_FILING, etc.
    
    first_message_id = Column(String)
    last_message_id = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    # Status
    status = Column(String, default="awaiting_reply")  # awaiting_reply, replied, resolved
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    emails = relationship("Email", back_populates="thread", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_client_type', 'client_id', 'email_type'),
        Index('idx_created_at', 'created_at'),
    )


class Email(Base):
    __tablename__ = "emails"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(36), ForeignKey("email_threads.id"), nullable=False, index=True)
    
    # Content
    subject = Column(String, nullable=False)
    body = Column(Text)
    body_html = Column(Text)
    
    # Participants
    from_address = Column(String, nullable=False)
    from_name = Column(String)
    to_recipients = Column(JSON, default=[])
    cc_recipients = Column(JSON, default=[])
    bcc_recipients = Column(JSON, default=[])
    
    # Threading headers
    internet_message_id = Column(String, unique=True, index=True)
    in_reply_to_id = Column(String)
    references = Column(Text)
    conversation_id = Column(String, index=True)
    conversation_index = Column(String)
    
    # Custom headers
    tax_email_id = Column(String, unique=True)
    
    # Classification
    email_type = Column(String, index=True)
    client_id = Column(String, ForeignKey("clients.id"), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    
    # Status
    direction = Column(String)  # incoming, outgoing
    is_read = Column(Boolean, default=False)
    status = Column(String, default="received")  # draft, sent, received
    
    # Timestamps
    received_date_time = Column(DateTime, index=True)
    sent_date_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Attachments
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)
    
    # Flags
    is_flagged = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    thread = relationship("EmailThread", back_populates="emails")
    user = relationship("User", back_populates="emails")
    attachments = relationship("EmailAttachment", back_populates="email", cascade="all, delete-orphan")


class EmailSignature(Base):
    __tablename__ = "email_signatures"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    name = Column(String, nullable=False)
    signature_html = Column(Text)
    signature_text = Column(Text)
    
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="signatures")
```

### models/client.py
```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Client information
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    
    # Classification
    client_type = Column(String)  # corporate, non_corporate
    tax_year = Column(String)  # FY 2024-25, FY 2025-26
    
    # Metadata
    pan = Column(String, unique=True)
    gstin = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## Step 3: Authentication Service

### services/auth_service.py
```python
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from urllib.parse import urlencode
from sqlalchemy.orm import Session
from models.user import User
from utils.exceptions import AuthenticationError
import jwt
import base64

class AuthService:
    """OAuth 2.0 authentication with Microsoft Azure"""
    
    TENANT_ID = os.getenv("AZURE_TENANT_ID")
    CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
    PLATFORM_URL = os.getenv("PLATFORM_URL")
    
    @classmethod
    def get_auth_url(cls) -> str:
        """Generate Microsoft login URL"""
        
        params = {
            "client_id": cls.CLIENT_ID,
            "redirect_uri": f"{cls.PLATFORM_URL}/auth/callback",
            "response_type": "code",
            "scope": "Mail.ReadWrite MailboxSettings.ReadWrite User.Read offline_access",
            "response_mode": "query"
        }
        
        auth_url = (
            f"https://login.microsoftonline.com/{cls.TENANT_ID}/oauth2/v2.0/authorize?"
            f"{urlencode(params)}"
        )
        
        return auth_url
    
    @classmethod
    def exchange_code_for_tokens(cls, code: str) -> Dict[str, str]:
        """Exchange authorization code for access token"""
        
        token_url = f"https://login.microsoftonline.com/{cls.TENANT_ID}/oauth2/v2.0/token"
        
        data = {
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "code": code,
            "redirect_uri": f"{cls.PLATFORM_URL}/auth/callback",
            "grant_type": "authorization_code",
            "scope": "Mail.ReadWrite MailboxSettings.ReadWrite User.Read offline_access"
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            raise AuthenticationError(f"Failed to exchange code: {response.text}")
        
        tokens = response.json()
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens["expires_in"]
        }
    
    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> Dict[str, str]:
        """Refresh expired access token"""
        
        token_url = f"https://login.microsoftonline.com/{cls.TENANT_ID}/oauth2/v2.0/token"
        
        data = {
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "Mail.ReadWrite MailboxSettings.ReadWrite User.Read offline_access"
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code != 200:
            raise AuthenticationError("Failed to refresh token")
        
        tokens = response.json()
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", refresh_token),
            "expires_in": tokens["expires_in"]
        }
    
    @classmethod
    def get_user_info(cls, access_token: str) -> Dict:
        """Get user information from Microsoft Graph"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )
        
        if response.status_code != 200:
            raise AuthenticationError("Failed to get user info")
        
        return response.json()
    
    @classmethod
    def save_or_update_user(cls, db: Session, user_data: Dict, tokens: Dict) -> User:
        """Save or update user with tokens"""
        
        email = user_data["userPrincipalName"]
        
        # Find existing user or create new
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(
                email=email,
                first_name=user_data.get("givenName", ""),
                last_name=user_data.get("surname", ""),
            )
            db.add(user)
        
        # Update tokens
        user.access_token = cls.encrypt_token(tokens["access_token"])
        user.refresh_token = cls.encrypt_token(tokens["refresh_token"])
        user.token_expires_at = (
            datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        )
        
        db.commit()
        
        return user
    
    @staticmethod
    def encrypt_token(token: str) -> str:
        """Encrypt token for storage (basic base64 - use proper encryption in production)"""
        return base64.b64encode(token.encode()).decode()
    
    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """Decrypt token from storage"""
        return base64.b64decode(encrypted_token.encode()).decode()
```

---

## Step 4: Microsoft Graph Integration

### services/graph_service.py
```python
import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models.email import Email
from services.auth_service import AuthService
from utils.exceptions import GraphAPIError

class GraphService:
    """Microsoft Graph API wrapper"""
    
    GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def list_messages(
        self,
        folder: str = "inbox",
        limit: int = 50,
        skip: int = 0,
        filter_query: Optional[str] = None
    ) -> Dict:
        """List emails from a folder"""
        
        url = f"{self.GRAPH_API_URL}/me/mailFolders('{folder}')/messages"
        
        params = {
            "$select": (
                "id,subject,from,toRecipients,ccRecipients,bccRecipients,"
                "receivedDateTime,sentDateTime,bodyPreview,body,isRead,"
                "hasAttachments,internetMessageId,inReplyTo,references,"
                "conversationId,conversationIndex,categories,isReminderOn,"
                "importance,parentReference"
            ),
            "$orderby": "receivedDateTime desc",
            "$top": limit,
            "$skip": skip
        }
        
        if filter_query:
            params["$filter"] = filter_query
        
        response = requests.get(
            url,
            headers=self.headers,
            params=params
        )
        
        if response.status_code != 200:
            raise GraphAPIError(f"Failed to list messages: {response.text}")
        
        return response.json()
    
    def get_message(self, message_id: str) -> Dict:
        """Get full message details"""
        
        url = f"{self.GRAPH_API_URL}/me/messages/{message_id}"
        
        response = requests.get(
            url,
            headers=self.headers,
            params={"$select": "*"}
        )
        
        if response.status_code != 200:
            raise GraphAPIError(f"Failed to get message: {response.text}")
        
        return response.json()
    
    def send_email(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        body_type: str = "HTML",
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Send an email"""
        
        url = f"{self.GRAPH_API_URL}/me/sendmail"
        
        message_body = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": body_type,
                    "content": body
                },
                "toRecipients": [
                    {"emailAddress": {"address": addr}} for addr in to_recipients
                ],
                "ccRecipients": [
                    {"emailAddress": {"address": addr}} for addr in (cc_recipients or [])
                ],
                "bccRecipients": [
                    {"emailAddress": {"address": addr}} for addr in (bcc_recipients or [])
                ],
            },
            "saveToSentItems": True
        }
        
        # Add custom headers
        if headers:
            message_body["message"]["internetMessageHeaders"] = [
                {"name": k, "value": v} for k, v in headers.items()
            ]
        
        response = requests.post(
            url,
            headers=self.headers,
            json=message_body
        )
        
        if response.status_code not in [200, 202]:
            raise GraphAPIError(f"Failed to send email: {response.text}")
        
        return {"status": "sent"}
    
    def create_draft(
        self,
        to_recipients: List[str],
        subject: str,
        body: str
    ) -> Dict:
        """Create draft email"""
        
        url = f"{self.GRAPH_API_URL}/me/mailFolders('drafts')/messages"
        
        message_body = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body
            },
            "toRecipients": [
                {"emailAddress": {"address": addr}} for addr in to_recipients
            ]
        }
        
        response = requests.post(
            url,
            headers=self.headers,
            json=message_body
        )
        
        if response.status_code != 201:
            raise GraphAPIError(f"Failed to create draft: {response.text}")
        
        return response.json()
    
    def mark_as_read(self, message_id: str) -> Dict:
        """Mark message as read"""
        
        url = f"{self.GRAPH_API_URL}/me/messages/{message_id}"
        
        response = requests.patch(
            url,
            headers=self.headers,
            json={"isRead": True}
        )
        
        if response.status_code != 200:
            raise GraphAPIError(f"Failed to mark as read: {response.text}")
        
        return response.json()
    
    def create_subscription(
        self,
        change_types: List[str],
        resource: str = "/me/mailFolders('inbox')/messages",
        expiration_minutes: int = 4320  # 3 days default
    ) -> Dict:
        """Create webhook subscription for real-time notifications"""
        
        url = f"{self.GRAPH_API_URL}/subscriptions"
        
        payload = {
            "changeType": ",".join(change_types),
            "notificationUrl": f"{os.getenv('PLATFORM_URL')}/webhooks/notify",
            "resource": resource,
            "expirationDateTime": (
                datetime.utcnow() + timedelta(minutes=expiration_minutes)
            ).isoformat() + "Z",
            "clientState": os.getenv("WEBHOOK_SECRET")
        }
        
        response = requests.post(
            url,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code != 201:
            raise GraphAPIError(f"Failed to create subscription: {response.text}")
        
        return response.json()
    
    def renew_subscription(self, subscription_id: str) -> Dict:
        """Renew webhook subscription"""
        
        url = f"{self.GRAPH_API_URL}/subscriptions/{subscription_id}"
        
        payload = {
            "expirationDateTime": (
                datetime.utcnow() + timedelta(days=3)
            ).isoformat() + "Z"
        }
        
        response = requests.patch(
            url,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise GraphAPIError(f"Failed to renew subscription: {response.text}")
        
        return response.json()
```

---

## Step 5: Email Threading Engine

### services/threading_engine.py
```python
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.email import Email, EmailThread
import difflib
import uuid

class EmailThreadingEngine:
    """Multi-layer email threading algorithm"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def thread_email(self, email_data: Dict) -> Dict:
        """
        Main orchestrator: tries all threading methods in priority order.
        
        Returns: {
            'thread_id': 'xxx',
            'confidence': 0.95,
            'method': 'rfc_in_reply_to',
            'parent_id': 'xxx'
        }
        """
        
        # Layer 1: Conversation ID
        result = self._check_conversation_id(email_data)
        if result:
            print(f"✓ Thread via conversation ID (confidence: {result['confidence']})")
            return result
        
        # Layer 2: Custom header
        result = self._check_custom_header(email_data)
        if result:
            print(f"✓ Thread via custom header (confidence: {result['confidence']})")
            return result
        
        # Layer 3: RFC headers
        result = self._check_rfc_headers(email_data)
        if result:
            print(f"✓ Thread via RFC headers (confidence: {result['confidence']})")
            return result
        
        # Layer 4: Subject matching
        result = self._check_subject_matching(email_data)
        if result:
            print(f"✓ Thread via subject match (confidence: {result['confidence']})")
            return result
        
        # Create new thread
        new_thread_id = f"thread_{str(uuid.uuid4())}"
        print(f"✓ New thread created: {new_thread_id}")
        
        return {
            'thread_id': new_thread_id,
            'confidence': 0.0,
            'method': 'new_thread',
            'is_new': True
        }
    
    def _check_conversation_id(self, email_data: Dict) -> Optional[Dict]:
        """Microsoft's native conversation ID"""
        
        if 'conversationId' in email_data and email_data['conversationId']:
            thread = self.db.query(EmailThread).filter(
                EmailThread.conversation_id == email_data['conversationId']
            ).first()
            
            if thread:
                return {
                    'thread_id': thread.id,
                    'confidence': 1.0,
                    'method': 'conversation_id'
                }
        
        return None
    
    def _check_custom_header(self, email_data: Dict) -> Optional[Dict]:
        """Look for our X-Tax-Email-ID header"""
        
        headers = email_data.get('internetMessageHeaders', [])
        
        for header in headers:
            if header.get('name') == 'X-Tax-Email-ID':
                thread = self.db.query(EmailThread).filter(
                    EmailThread.tax_email_id == header.get('value')
                ).first()
                
                if thread:
                    return {
                        'thread_id': thread.id,
                        'confidence': 0.95,
                        'method': 'custom_header'
                    }
        
        return None
    
    def _check_rfc_headers(self, email_data: Dict) -> Optional[Dict]:
        """RFC 5322 threading headers"""
        
        # Check In-Reply-To
        if 'inReplyToId' in email_data and email_data['inReplyToId']:
            parent = self.db.query(Email).filter(
                Email.internet_message_id == email_data['inReplyToId']
            ).first()
            
            if parent:
                return {
                    'thread_id': parent.thread_id,
                    'confidence': 0.99,
                    'method': 'rfc_in_reply_to',
                    'parent_id': parent.id
                }
        
        # Check References
        if 'references' in email_data and email_data['references']:
            refs = email_data['references'].split(' ')
            
            for ref in refs:
                parent = self.db.query(Email).filter(
                    Email.internet_message_id == ref
                ).first()
                
                if parent:
                    return {
                        'thread_id': parent.thread_id,
                        'confidence': 0.95,
                        'method': 'rfc_references'
                    }
        
        return None
    
    def _check_subject_matching(self, email_data: Dict) -> Optional[Dict]:
        """Subject line fuzzy matching"""
        
        normalized_subject = self._normalize_subject(email_data.get('subject', ''))
        
        if not normalized_subject:
            return None
        
        # Look for similar subject in recent emails (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        recent_emails = self.db.query(Email).filter(
            Email.received_date_time >= cutoff_date
        ).all()
        
        for existing_email in recent_emails:
            existing_normalized = self._normalize_subject(existing_email.subject)
            
            # Fuzzy match
            similarity = difflib.SequenceMatcher(
                None, normalized_subject, existing_normalized
            ).ratio()
            
            if similarity >= 0.90:
                return {
                    'thread_id': existing_email.thread_id,
                    'confidence': 0.70,
                    'method': 'subject_matching',
                    'similarity': similarity
                }
        
        return None
    
    @staticmethod
    def _normalize_subject(subject: str) -> str:
        """Remove Re:, Fwd: prefixes from subject"""
        
        import re
        
        # Remove common prefixes
        cleaned = re.sub(r'^(re|fwd?|aw|rv):\s*', '', subject, flags=re.IGNORECASE)
        # Remove [brackets]
        cleaned = re.sub(r'^\[.*?\]\s*', '', cleaned)
        # Trim
        return cleaned.strip().lower()
```

---

## Step 6: Webhook Handler

### routes/webhooks.py
```python
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from celery import Celery
from datetime import datetime, timedelta
import os
import json

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/notify")
async def webhook_notification(request: Request, db: Session):
    """
    Receive notifications from Microsoft Graph when emails arrive.
    This is called < 5 seconds after new email arrives in Outlook.
    """
    
    body = await request.json()
    
    # Handle validation token (first call from Microsoft)
    if 'validationTokens' in body:
        return PlainTextResponse(body['validationTokens'][0])
    
    # Process notifications
    notifications = body.get('value', [])
    
    print(f"🔔 Received {len(notifications)} notifications")
    
    for notification in notifications:
        # Queue for async processing
        from services.email_service import process_notification
        
        process_notification.delay(notification)
    
    return {"status": "processing"}


@router.post("/create-subscription/{user_id}")
async def create_subscription(user_id: str, db: Session):
    """Create webhook subscription for a user"""
    
    from models.user import User
    from services.graph_service import GraphService
    from services.auth_service import AuthService
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        access_token = AuthService.decrypt_token(user.access_token)
        graph = GraphService(access_token)
        
        subscription = graph.create_subscription(
            change_types=["created", "updated"],
            resource="/me/mailFolders('inbox')/messages"
        )
        
        # Save subscription details
        user.graph_subscription_id = subscription['id']
        user.graph_subscription_expires_at = datetime.fromisoformat(
            subscription['expirationDateTime'].replace('Z', '')
        )
        db.commit()
        
        return {
            "subscription_id": subscription['id'],
            "expires_at": subscription['expirationDateTime']
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Step 7: Email CRUD Operations

### routes/emails.py
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from models.email import Email, EmailThread
from services.graph_service import GraphService
from services.threading_engine import EmailThreadingEngine
from services.auth_service import AuthService
from database import get_db
from utils.decorators import require_auth

router = APIRouter(prefix="/emails", tags=["emails"])

class SendEmailRequest(BaseModel):
    to_recipients: List[str]
    subject: str
    body: str
    cc_recipients: Optional[List[str]] = None
    bcc_recipients: Optional[List[str]] = None
    signature_id: Optional[str] = None

@router.get("")
async def list_emails(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth),
    email_type: Optional[str] = None,
    client_id: Optional[str] = None,
    folder: str = "inbox",
    limit: int = Query(50, le=100),
    skip: int = 0
):
    """List emails with filtering"""
    
    query = db.query(Email).filter(Email.user_id == current_user.id)
    
    if email_type:
        query = query.filter(Email.email_type == email_type)
    
    if client_id:
        query = query.filter(Email.client_id == client_id)
    
    total = query.count()
    
    emails = query.order_by(Email.received_date_time.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "skip": skip,
        "emails": [
            {
                "id": e.id,
                "subject": e.subject,
                "from": e.from_address,
                "to": e.to_recipients,
                "received_at": e.received_date_time,
                "is_read": e.is_read,
                "email_type": e.email_type,
                "thread_id": e.thread_id,
                "has_attachments": e.has_attachments
            }
            for e in emails
        ]
    }

@router.get("/{email_id}")
async def get_email(
    email_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth)
):
    """Get full email with body and headers"""
    
    email = db.query(Email).filter(Email.id == email_id).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Mark as read
    if not email.is_read:
        email.is_read = True
        db.commit()
    
    return {
        "id": email.id,
        "subject": email.subject,
        "from": {"address": email.from_address, "name": email.from_name},
        "to": email.to_recipients,
        "cc": email.cc_recipients,
        "body": email.body_html or email.body,
        "received_at": email.received_date_time,
        "thread_id": email.thread_id,
        "attachments": [
            {"name": a.file_name, "size": a.file_size, "url": a.s3_url}
            for a in email.attachments
        ]
    }

@router.get("/thread/{thread_id}")
async def get_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth)
):
    """Get complete email thread"""
    
    thread = db.query(EmailThread).filter(EmailThread.id == thread_id).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    emails = db.query(Email).filter(Email.thread_id == thread_id).order_by(Email.received_date_time).all()
    
    return {
        "thread_id": thread.id,
        "subject": thread.subject,
        "email_type": thread.email_type,
        "status": thread.status,
        "created_at": thread.created_at,
        "emails": [
            {
                "id": e.id,
                "from": e.from_address,
                "to": e.to_recipients,
                "subject": e.subject,
                "body": e.body_html or e.body,
                "received_at": e.received_date_time,
                "direction": e.direction
            }
            for e in emails
        ]
    }

@router.post("")
async def send_email(
    payload: SendEmailRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth)
):
    """Send email"""
    
    try:
        # Get user's access token
        access_token = AuthService.decrypt_token(current_user.access_token)
        graph = GraphService(access_token)
        
        # Prepare custom headers
        headers = {
            "X-Tax-Email-ID": f"TAX_{int(datetime.now().timestamp())}_{current_user.id}",
            "X-Email-Type": "EMAIL"
        }
        
        # Send via Graph API
        result = graph.send_email(
            to_recipients=payload.to_recipients,
            subject=payload.subject,
            body=payload.body,
            cc_recipients=payload.cc_recipients,
            bcc_recipients=payload.bcc_recipients,
            headers=headers
        )
        
        return {"status": "sent", "message_id": result.get("id")}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{email_id}")
async def update_email(
    email_id: str,
    is_read: Optional[bool] = None,
    is_flagged: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth)
):
    """Update email status"""
    
    email = db.query(Email).filter(Email.id == email_id).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if is_read is not None:
        email.is_read = is_read
    
    if is_flagged is not None:
        email.is_flagged = is_flagged
    
    db.commit()
    
    return {"status": "updated"}
```

---

## Step 8: Frontend Scaffold

### frontend/src/components/EmailList.jsx
```jsx
import React, { useEffect, useState } from 'react';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Box,
  Chip,
  CircularProgress
} from '@mui/material';
import { useEmailStore } from '../store/emailStore';
import api from '../services/api';

export function EmailList() {
  const { emails, setEmails, loading, setLoading } = useEmailStore();
  const [filter, setFilter] = useState(null);

  useEffect(() => {
    fetchEmails();
  }, [filter]);

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filter?.type) params.email_type = filter.type;
      if (filter?.client) params.client_id = filter.client;

      const response = await api.get('/emails', { params });
      setEmails(response.data.emails);
    } catch (error) {
      console.error('Failed to fetch emails:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <List>
      {emails.map((email) => (
        <ListItem key={email.id} disablePadding>
          <ListItemButton
            onClick={() => window.location.href = `/email/${email.id}`}
          >
            <ListItemText
              primary={email.subject}
              secondary={`From: ${email.from} - ${new Date(email.received_at).toLocaleDateString()}`}
            />
            {email.email_type && (
              <Chip label={email.email_type} size="small" />
            )}
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );
}
```

---

## Testing & Deployment

### Run Backend Locally

```bash
cd backend
source venv/bin/activate

# Start PostgreSQL
docker run -e POSTGRES_PASSWORD=password postgres:14

# Start Elasticsearch
docker run -e discovery.type=single-node docker.elastic.co/elasticsearch/elasticsearch:8.0.0

# Start Redis
docker run redis:7

# Run FastAPI
uvicorn app.main:app --reload --port 8000
```

### Test API

```bash
# Get auth URL
curl http://localhost:8000/auth/login

# Send test email
curl -X POST http://localhost:8000/emails \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "to_recipients": ["test@example.com"],
    "subject": "Test Email",
    "body": "This is a test"
  }'
```

---

**You're now ready to start building! Start with Step 1 and work through sequentially. Good luck! 🚀**
