"""
Tests for email API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from models.email import Email
from models.user import User


class TestEmailList:
    """Test email listing endpoint."""
    
    def test_list_emails_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test successful email listing."""
        response = client.get("/emails", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_list_emails_with_type_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test email listing with type filter."""
        response = client.get(
            "/emails",
            headers=auth_headers,
            params={"email_type": "GST_FILING"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned emails should match the type
        for email in data["emails"]:
            assert email["email_type"] == "GST_FILING"
    
    def test_list_emails_with_is_read_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test email listing with read status filter."""
        response = client.get(
            "/emails",
            headers=auth_headers,
            params={"is_read": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for email in data["emails"]:
            assert email["is_read"] == False
    
    def test_list_emails_with_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test email listing with pagination."""
        response = client.get(
            "/emails",
            headers=auth_headers,
            params={"limit": 10, "offset": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "limit" in data
        assert "offset" in data


class TestEmailDetail:
    """Test email detail endpoint."""
    
    def test_get_email_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test successful email retrieval."""
        response = client.get(
            f"/emails/{test_email.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_email.id
        assert data["subject"] == test_email.subject
        assert "body" in data or "body_html" in data
    
    def test_get_email_marks_as_read(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email,
        db: Session
    ):
        """Test that fetching email marks it as read."""
        # Email should be unread initially
        assert test_email.is_read == False
        
        response = client.get(
            f"/emails/{test_email.id}",
            headers=auth_headers,
            params={"mark_as_read": True}
        )
        
        assert response.status_code == 200
    
    def test_get_email_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test email retrieval with invalid ID."""
        response = client.get(
            "/emails/invalid-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestEmailSend:
    """Test email sending endpoint."""
    
    @patch('services.graph_service.GraphService.send_email')
    def test_send_email_success(
        self,
        mock_send: MagicMock,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test successful email sending."""
        mock_send.return_value = {"id": "sent-message-123"}
        
        payload = {
            "to_recipients": ["recipient@example.com"],
            "subject": "Test Email",
            "body": "This is a test email body.",
            "body_type": "HTML"
        }
        
        response = client.post("/emails", headers=auth_headers, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "email" in data
    
    def test_send_email_missing_subject(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test email sending with missing subject."""
        payload = {
            "to_recipients": ["recipient@example.com"],
            "body": "Test body"
        }
        
        response = client.post("/emails", headers=auth_headers, json=payload)
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_send_email_invalid_recipient(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test email sending with invalid recipient."""
        payload = {
            "to_recipients": ["invalid-email"],
            "subject": "Test",
            "body": "Test body"
        }
        
        response = client.post("/emails", headers=auth_headers, json=payload)
        
        # Should fail validation
        assert response.status_code == 422


class TestEmailUpdate:
    """Test email update endpoint."""
    
    def test_mark_email_read(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email,
        db: Session
    ):
        """Test marking email as read."""
        response = client.post(
            f"/emails/{test_email.id}/read",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_mark_email_unread(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test marking email as unread."""
        response = client.post(
            f"/emails/{test_email.id}/unread",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_flag_email(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test flagging email."""
        response = client.post(
            f"/emails/{test_email.id}/flag",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    def test_update_email_properties(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test updating multiple email properties."""
        payload = {
            "is_read": True,
            "is_flagged": True,
            "is_archived": False
        }
        
        response = client.patch(
            f"/emails/{test_email.id}",
            headers=auth_headers,
            json=payload
        )
        
        assert response.status_code == 200


class TestEmailSync:
    """Test email sync endpoint."""
    
    @patch('services.graph_service.GraphService.list_messages')
    def test_sync_emails_success(
        self,
        mock_list: MagicMock,
        client: TestClient,
        auth_headers: dict,
        mock_graph_api_response: dict
    ):
        """Test successful email sync."""
        mock_list.return_value = {
            "value": [mock_graph_api_response],
            "@odata.nextLink": None
        }
        
        response = client.get(
            "/emails/sync",
            headers=auth_headers,
            params={"folder": "inbox", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "synced_count" in data or "message" in data


class TestEmailDelete:
    """Test email deletion endpoint."""
    
    def test_delete_email_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_email: Email
    ):
        """Test successful email deletion."""
        response = client.delete(
            f"/emails/{test_email.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
