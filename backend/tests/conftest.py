"""
Pytest configuration and fixtures for testing.
"""

import os
import sys
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from models.user import User
from models.client import Client
from models.email import Email, EmailThread
from utils.encryption import get_encryption

# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    encryption = get_encryption()
    
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        role="accountant",
        is_active=True,
        access_token=encryption.encrypt("test-access-token"),
        refresh_token=encryption.encrypt("test-refresh-token")
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Get authentication headers for test user."""
    return {
        "Authorization": f"Bearer {test_user.id}"
    }


@pytest.fixture
def test_client_corporate(db: Session) -> Client:
    """Create a test corporate client."""
    client = Client(
        name="ABC Corporation Ltd",
        email="contact@abccorp.com",
        phone="9876543210",
        client_type="corporate",
        tax_year="FY 2025-26",
        pan="ABCDE1234F",
        gstin="27ABCDE1234F1Z5",
        contact_person_name="John Doe",
        contact_person_email="john@abccorp.com",
        is_active=True
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return client


@pytest.fixture
def test_client_non_corporate(db: Session) -> Client:
    """Create a test non-corporate client."""
    client = Client(
        name="Jane Smith Individual",
        email="jane@example.com",
        phone="9123456789",
        client_type="non_corporate",
        tax_year="FY 2025-26",
        pan="XYZAB9876C",
        contact_person_name="Jane Smith",
        contact_person_email="jane@example.com",
        is_active=True
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return client


@pytest.fixture
def test_thread(db: Session, test_client_corporate: Client) -> EmailThread:
    """Create a test email thread."""
    from datetime import datetime
    
    thread = EmailThread(
        client_id=test_client_corporate.id,
        subject="Test GST Filing Query",
        email_type="GST_FILING",
        conversation_id="test-conv-123",
        tax_email_id="tax-email-456",
        message_count=1,
        status="awaiting_reply",
        created_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow()
    )
    
    db.add(thread)
    db.commit()
    db.refresh(thread)
    
    return thread


@pytest.fixture
def test_email(db: Session, test_user: User, test_thread: EmailThread, test_client_corporate: Client) -> Email:
    """Create a test email."""
    from datetime import datetime
    
    email = Email(
        thread_id=test_thread.id,
        graph_message_id="graph-msg-123",
        subject="GST Filing Query",
        body="Please provide GST filing status.",
        body_html="<p>Please provide GST filing status.</p>",
        body_preview="Please provide GST filing status.",
        from_address="client@example.com",
        from_name="Client User",
        to_recipients=["accountant@company.com"],
        cc_recipients=[],
        bcc_recipients=[],
        internet_message_id="<test@example.com>",
        email_type="GST_FILING",
        client_id=test_client_corporate.id,
        user_id=test_user.id,
        direction="incoming",
        is_read=False,
        status="received",
        received_date_time=datetime.utcnow(),
        has_attachments=False,
        attachment_count=0
    )
    
    db.add(email)
    db.commit()
    db.refresh(email)
    
    return email


@pytest.fixture
def mock_graph_api_response():
    """Mock Microsoft Graph API response."""
    from datetime import datetime
    
    return {
        "id": "graph-message-456",
        "subject": "Test Email Subject",
        "conversationId": "conv-789",
        "bodyPreview": "This is a test email body...",
        "body": {
            "contentType": "HTML",
            "content": "<p>This is a test email body.</p>"
        },
        "from": {
            "emailAddress": {
                "name": "Test Sender",
                "address": "sender@example.com"
            }
        },
        "toRecipients": [
            {
                "emailAddress": {
                    "name": "Test Recipient",
                    "address": "recipient@example.com"
                }
            }
        ],
        "ccRecipients": [],
        "bccRecipients": [],
        "receivedDateTime": datetime.utcnow().isoformat(),
        "sentDateTime": datetime.utcnow().isoformat(),
        "hasAttachments": False,
        "importance": "normal",
        "isRead": False,
        "internetMessageId": "<test-message@example.com>",
        "internetMessageHeaders": [
            {"name": "Message-ID", "value": "<test-message@example.com>"}
        ]
    }
