# Email Module - Advanced Topics & Best Practices
## For Production-Grade Tax Platform

---

## Advanced Topics

### 1. Handling Delegated Access & Shared Mailboxes

In a tax firm, multiple accountants might need access to client mailboxes. Here's how to handle this:

```python
# services/mailbox_service.py

class MailboxService:
    """Manage access to multiple mailboxes"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def get_delegated_mailboxes(self) -> List[str]:
        """Get list of mailboxes user has access to"""
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Get all mailfolders (own + delegated)
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me/mailFolders",
            headers=headers
        )
        
        mailboxes = []
        
        for folder in response.json()['value']:
            if 'inbox' in folder['displayName'].lower():
                mailboxes.append(folder['parentFolderId'])
        
        return mailboxes
    
    def get_emails_from_delegated_mailbox(
        self,
        mailbox_email: str,
        folder: str = "inbox"
    ) -> Dict:
        """Fetch emails from a delegated mailbox"""
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Access delegated mailbox
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{mailbox_email}/mailFolders('{folder}')/messages",
            headers=headers
        )
        
        return response.json()
    
    def send_email_on_behalf(
        self,
        from_email: str,
        to_recipients: List[str],
        subject: str,
        body: str
    ):
        """Send email on behalf of delegated user"""
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        message = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body},
                "toRecipients": [
                    {"emailAddress": {"address": addr}} for addr in to_recipients
                ],
                "from": {"emailAddress": {"address": from_email}}
            },
            "saveToSentItems": True
        }
        
        response = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{from_email}/sendmail",
            headers=headers,
            json=message
        )
        
        return response.json()
```

---

### 2. Email Type Classification (ML/Rule-Based)

```python
# services/classification_service.py

from enum import Enum
import re
from datetime import datetime

class EmailType(Enum):
    NIL_FILING = "NIL_FILING"
    VAT_FILING = "VAT_FILING"
    GST_FILING = "GST_FILING"
    ITR_SUBMISSION = "ITR_SUBMISSION"
    DOC_REQUEST = "DOC_REQUEST"
    COMPLIANCE_NOTICE = "COMPLIANCE_NOTICE"


class EmailClassifier:
    """Classify emails by type"""
    
    # Rule-based patterns
    PATTERNS = {
        EmailType.NIL_FILING: [
            r"nil filing",
            r"nil return",
            r"no income",
            r"nil profit"
        ],
        EmailType.VAT_FILING: [
            r"vat filing",
            r"vat return",
            r"vat submission",
            r"value added tax"
        ],
        EmailType.GST_FILING: [
            r"gst filing",
            r"gst return",
            r"gst submission",
            r"goods and services tax"
        ],
        EmailType.ITR_SUBMISSION: [
            r"itr submission",
            r"income tax return",
            r"itr filed",
            r"itr status"
        ],
        EmailType.DOC_REQUEST: [
            r"please provide",
            r"please submit",
            r"document required",
            r"documentation needed",
            r"waiting for",
            r"awaiting",
            r"kindly send"
        ],
        EmailType.COMPLIANCE_NOTICE: [
            r"notice",
            r"compliance",
            r"urgent",
            r"important",
            r"action required",
            r"immediate"
        ]
    }
    
    @classmethod
    def classify(cls, subject: str, body: str = "") -> EmailType:
        """Classify email based on subject and body"""
        
        text = f"{subject} {body}".lower()
        
        # Rule-based matching
        for email_type, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return email_type
        
        # Default
        return EmailType.DOC_REQUEST
    
    @classmethod
    def classify_with_ml(cls, email_data: Dict, model) -> EmailType:
        """
        Classify using trained ML model (optional).
        You can train a simple classifier on historical emails.
        
        Example: Use spaCy or sklearn for text classification
        """
        
        text = f"{email_data['subject']} {email_data.get('body', '')}"
        
        # Predict using model
        prediction = model.predict([text])[0]
        
        return EmailType(prediction)
```

---

### 3. RTI File Integration

When a client's RTI (Return of Tax Information) file is generated, automatically notify them via email:

```python
# services/rti_service.py

class RTIService:
    """Integrate with RTI file generation"""
    
    def __init__(self, db: Session, graph_service: GraphService):
        self.db = db
        self.graph = graph_service
    
    def send_rti_file(
        self,
        client_id: str,
        tax_year: str,
        rti_file_path: str,
        recipient_emails: List[str]
    ):
        """
        Send RTI file to client with email notification
        
        Creates:
        1. Email thread for audit trail
        2. Sends email with RTI file attached
        3. Tracks delivery status
        4. Logs for compliance
        """
        
        try:
            # Get RTI file
            with open(rti_file_path, 'rb') as f:
                file_content = f.read()
            
            # Prepare email
            subject = f"RTI File - {tax_year} - Action Required"
            body = f"""
            <html>
            <body>
            <p>Dear Client,</p>
            <p>Your RTI (Return of Tax Information) file for {tax_year} is attached.</p>
            <p><strong>Action Required:</strong> Please review and confirm receipt.</p>
            <p>If you have any questions, please reply to this email.</p>
            <p>Best regards,</p>
            <p>Tax Compliance Team</p>
            </body>
            </html>
            """
            
            # Create thread
            thread = EmailThread(
                client_id=client_id,
                email_type="RTI_SUBMISSION",
                subject=subject,
                status="awaiting_reply"
            )
            self.db.add(thread)
            self.db.commit()
            
            # Send email with Graph API
            # (Include attachment logic here)
            
            # Log in audit trail
            from models.audit_log import AuditLog
            
            for recipient in recipient_emails:
                audit = AuditLog(
                    client_id=client_id,
                    action="rti_file_sent",
                    metadata={
                        "rti_file": rti_file_path,
                        "recipient": recipient,
                        "tax_year": tax_year,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                self.db.add(audit)
            
            self.db.commit()
            
            return {
                "status": "sent",
                "thread_id": thread.id,
                "recipients": recipient_emails
            }
        
        except Exception as e:
            print(f"❌ Failed to send RTI file: {e}")
            raise
    
    def track_rti_acknowledgment(self, thread_id: str):
        """
        Track when client confirms receipt of RTI file.
        
        The system monitors the email thread for:
        - Client's reply (confirmation)
        - Time to confirmation (SLA tracking)
        - Any questions or clarifications
        """
        
        thread = self.db.query(EmailThread).filter(
            EmailThread.id == thread_id
        ).first()
        
        if not thread:
            return None
        
        # Get all replies
        replies = self.db.query(Email).filter(
            Email.thread_id == thread_id,
            Email.direction == "incoming"
        ).all()
        
        if replies:
            latest_reply = max(replies, key=lambda e: e.received_date_time)
            
            # Update thread status
            thread.status = "replied"
            
            # Calculate time to confirm
            time_to_confirm = (
                latest_reply.received_date_time - thread.created_at
            ).total_seconds() / 3600  # in hours
            
            self.db.commit()
            
            return {
                "status": "confirmed",
                "confirmation_time_hours": time_to_confirm,
                "confirmed_by": latest_reply.from_address,
                "confirmed_at": latest_reply.received_date_time
            }
        
        return None
```

---

### 4. Email Reminder System

```python
# services/reminder_service.py

class ReminderService:
    """Send reminders for awaiting-reply emails"""
    
    def __init__(self, db: Session, graph_service: GraphService):
        self.db = db
        self.graph = graph_service
    
    def find_overdue_threads(self, days_overdue: int = 7) -> List[EmailThread]:
        """Find email threads awaiting reply for N days"""
        
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_overdue)
        
        overdue_threads = self.db.query(EmailThread).filter(
            EmailThread.status == "awaiting_reply",
            EmailThread.last_activity_at <= cutoff_date
        ).all()
        
        return overdue_threads
    
    def send_reminders(self, days_overdue: int = 7):
        """Send reminder notifications to users"""
        
        threads = self.find_overdue_threads(days_overdue)
        
        for thread in threads:
            # Find responsible user (who sent the last email)
            last_email = self.db.query(Email).filter(
                Email.thread_id == thread.id,
                Email.direction == "outgoing"
            ).order_by(Email.sent_date_time.desc()).first()
            
            if last_email and last_email.user_id:
                # Send reminder
                user = self.db.query(User).filter(
                    User.id == last_email.user_id
                ).first()
                
                reminder_subject = f"Reminder: Awaiting reply - {thread.subject}"
                reminder_body = f"""
                <html>
                <body>
                <p>Hi {user.first_name},</p>
                <p>This is a reminder that you're still awaiting a reply on:</p>
                <p><strong>{thread.subject}</strong></p>
                <p>Client: {thread.client_id}</p>
                <p>Last activity: {thread.last_activity_at}</p>
                <p><a href="https://yourdomain.com/email/thread/{thread.id}">
                    Click here to view the thread
                </a></p>
                </body>
                </html>
                """
                
                # Send via internal notification system
                from services.notification_service import send_internal_notification
                
                send_internal_notification(
                    user_id=user.id,
                    subject=reminder_subject,
                    body=reminder_body,
                    link=f"/email/thread/{thread.id}"
                )
```

---

### 5. Performance Optimization Strategies

```python
# Best Practices for Large-Scale Deployment

# 1. Database Indexing
# Create indexes on frequently queried columns:
"""
CREATE INDEX idx_email_thread_client_type 
  ON emails(thread_id, client_id, email_type);

CREATE INDEX idx_email_user_received 
  ON emails(user_id, received_date_time DESC);

CREATE INDEX idx_thread_status_activity 
  ON email_threads(status, last_activity_at DESC);
"""

# 2. Caching Strategy
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_user_emails_cached(user_id: str, limit: int = 50):
    """Get user emails with caching"""
    
    cache_key = f"user_emails:{user_id}:{limit}"
    
    # Check cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # If not in cache, fetch from DB
    emails = db.query(Email).filter(
        Email.user_id == user_id
    ).order_by(
        Email.received_date_time.desc()
    ).limit(limit).all()
    
    # Store in cache for 5 minutes
    redis_client.setex(
        cache_key,
        300,  # seconds
        json.dumps([e.to_dict() for e in emails])
    )
    
    return emails

# 3. Batch Operations
def sync_multiple_users_batch(user_ids: List[str]):
    """Sync emails for multiple users in parallel"""
    
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(sync_user_emails, user_id)
            for user_id in user_ids
        ]
        
        results = [f.result() for f in futures]
    
    return results

# 4. Pagination for Large Result Sets
def get_emails_paginated(
    user_id: str,
    page: int = 1,
    per_page: int = 50
) -> Dict:
    """Get paginated emails"""
    
    query = db.query(Email).filter(Email.user_id == user_id)
    
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    
    emails = query.order_by(
        Email.received_date_time.desc()
    ).offset(
        (page - 1) * per_page
    ).limit(
        per_page
    ).all()
    
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "emails": [e.to_dict() for e in emails]
    }
```

---

### 6. Security Best Practices

```python
# 1. Token Encryption
from cryptography.fernet import Fernet
import os

class TokenEncryption:
    def __init__(self):
        self.cipher = Fernet(os.getenv("ENCRYPTION_KEY"))
    
    def encrypt(self, token: str) -> str:
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt(self, encrypted_token: str) -> str:
        return self.cipher.decrypt(encrypted_token.encode()).decode()

# 2. Rate Limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/emails")
@limiter.limit("100/minute")
async def list_emails(request: Request):
    """Limit to 100 requests per minute per IP"""
    return {}

# 3. CORS Configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Whitelist only trusted domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

# 4. Input Validation
from pydantic import BaseModel, validator, EmailStr

class SendEmailRequest(BaseModel):
    to_recipients: List[EmailStr]  # Validates email format
    subject: str
    body: str
    
    @validator('subject')
    def subject_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Subject cannot be empty')
        return v
    
    @validator('body')
    def body_not_too_long(cls, v):
        if len(v) > 10000:
            raise ValueError('Body too long (max 10000 chars)')
        return v

# 5. SQL Injection Prevention (use ORM)
# ❌ DON'T DO THIS:
# query = f"SELECT * FROM emails WHERE user_id = '{user_id}'"

# ✅ DO THIS (ORM handles escaping):
emails = db.query(Email).filter(Email.user_id == user_id).all()

# 6. Audit Logging
from models.audit_log import AuditLog

def log_action(
    user_id: str,
    action: str,
    resource_id: str,
    metadata: Dict = None
):
    """Log all user actions for compliance"""
    
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_id=resource_id,
        ip_address=request.client.host,
        user_agent=request.headers.get('User-Agent'),
        metadata=metadata,
        timestamp=datetime.utcnow()
    )
    
    db.add(audit)
    db.commit()
```

---

### 7. Testing Strategy

```python
# tests/test_email_service.py

import pytest
from unittest.mock import Mock, patch
from services.email_service import EmailService

@pytest.fixture
def email_service():
    """Create email service with mocked dependencies"""
    
    mock_db = Mock()
    mock_graph = Mock()
    
    return EmailService(mock_db, mock_graph)

def test_send_email_success(email_service):
    """Test successful email sending"""
    
    email_service.graph.send_email = Mock(
        return_value={"id": "msg_123"}
    )
    
    result = email_service.send_email(
        to_recipients=["test@example.com"],
        subject="Test",
        body="Test body"
    )
    
    assert result["status"] == "sent"
    email_service.graph.send_email.assert_called_once()

def test_thread_email_rfc_headers(email_service):
    """Test RFC header-based threading"""
    
    existing_email = Mock(id="msg_1", thread_id="thread_1")
    email_service.db.query().filter().first.return_value = existing_email
    
    email_data = {
        "id": "msg_2",
        "inReplyToId": "msg_1",
        "subject": "Re: Test"
    }
    
    result = email_service.threading_engine.thread_email(email_data)
    
    assert result["thread_id"] == "thread_1"
    assert result["confidence"] >= 0.95

@pytest.mark.asyncio
async def test_webhook_notification(client):
    """Test webhook notification handling"""
    
    payload = {
        "value": [
            {
                "subscriptionId": "sub_123",
                "changeType": "created",
                "resource": "messages/msg_123",
                "resourceData": {"id": "msg_123"}
            }
        ]
    }
    
    response = await client.post("/webhooks/notify", json=payload)
    
    assert response.status_code == 200

# Integration test
@pytest.mark.integration
def test_end_to_end_email_flow():
    """
    Test complete flow:
    1. User sends email
    2. Email saved to DB
    3. Added to search index
    4. Webhook processes reply
    5. Reply matched to thread
    """
    
    # This would test the entire system end-to-end
    pass
```

---

### 8. Monitoring & Logging

```python
# services/monitoring_service.py

import logging
from datetime import datetime
import json

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class MonitoringService:
    """Monitor system health and performance"""
    
    @staticmethod
    def log_webhook_received(notification_count: int):
        logger.info(f"Webhook: Received {notification_count} notifications")
    
    @staticmethod
    def log_email_synced(user_id: str, email_count: int, duration_ms: int):
        logger.info(
            f"Sync: User {user_id} synced {email_count} emails in {duration_ms}ms"
        )
    
    @staticmethod
    def log_error(error_type: str, message: str, context: Dict = None):
        logger.error(
            f"Error: {error_type} - {message}",
            extra={"context": context or {}}
        )
    
    @staticmethod
    def track_performance(operation: str, duration_ms: float):
        """Track operation performance for optimization"""
        
        logger.info(
            f"Performance: {operation} took {duration_ms:.2f}ms"
        )
        
        # Alert if slow
        if duration_ms > 5000:
            logger.warning(
                f"⚠️  Slow operation: {operation} took {duration_ms:.2f}ms"
            )

# Metrics to monitor
"""
1. Email sync latency
   - Time from email arriving in Outlook to appearing in our system
   - Target: < 5 seconds

2. API response time
   - GET /emails: < 1 second
   - GET /emails/{id}: < 500ms
   - POST /emails: < 2 seconds

3. Webhook reliability
   - Notification delivery rate
   - Notification processing success rate
   - Subscription renewal success rate

4. Database performance
   - Query execution time
   - Connection pool utilization
   - Slow query identification

5. Background job health
   - Job execution success rate
   - Average job duration
   - Queue size

6. Errors & Exceptions
   - API errors (4xx, 5xx)
   - Database errors
   - Microsoft Graph API errors
   - Token refresh failures
"""
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Code review completed
- [ ] Security audit completed (OWASP Top 10)
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] SSL certificate configured
- [ ] CORS whitelist configured
- [ ] Rate limiting configured
- [ ] Backup strategy defined

### Deployment Steps

1. **Database**
   ```bash
   # Backup existing database
   pg_dump production_db > backup_$(date +%Y%m%d).sql
   
   # Run migrations
   alembic upgrade head
   ```

2. **Backend**
   ```bash
   # Stop current service
   systemctl stop tax-platform-email
   
   # Deploy new code
   git pull origin main
   pip install -r requirements.txt
   
   # Start service
   systemctl start tax-platform-email
   ```

3. **Frontend**
   ```bash
   # Build
   npm run build
   
   # Deploy to CDN/static server
   aws s3 sync dist/ s3://yourdomain-frontend/
   
   # Invalidate CloudFront cache
   aws cloudfront create-invalidation --distribution-id ID --paths "/*"
   ```

4. **Verification**
   ```bash
   # Check API health
   curl https://yourdomain.com/health
   
   # Monitor logs
   tail -f /var/log/tax-platform-email.log
   
   # Check webhook subscriptions
   curl https://api.microsoft.com/v1.0/subscriptions \
     -H "Authorization: Bearer $TOKEN"
   ```

### Post-Deployment

- [ ] Monitor error rates (should be < 0.5%)
- [ ] Check performance metrics
- [ ] Verify webhook subscriptions active
- [ ] Test email sending & receiving
- [ ] Test thread matching
- [ ] Verify audit logs being recorded
- [ ] Check backup completion

---

## Scaling Strategies

As your platform grows, implement these in order:

**Phase 1: Single Server (0-1000 emails/day)**
- All services on one box
- PostgreSQL on same server
- Redis for sessions

**Phase 2: Separated Services (1000-10000 emails/day)**
- Separate DB server (managed RDS)
- Separate cache server (ElastiCache)
- Background jobs on separate workers
- CDN for static assets

**Phase 3: Distributed System (10000+ emails/day)**
- Load balancer (ALB)
- Multi-instance backend (auto-scaling)
- Read replicas for database
- Elasticsearch cluster
- Message queue (RabbitMQ/SQS)
- Separate webhook processor
- File storage (S3/Azure Blob)

---

**This guide covers production-ready implementation. Start with fundamentals and scale as needed. Good luck! 🚀**
