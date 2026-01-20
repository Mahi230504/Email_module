"""
Tests for thread API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.email import EmailThread, ThreadStatus


class TestThreadList:
    """Test thread listing endpoint."""
    
    def test_list_threads_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread
    ):
        """Test successful thread listing."""
        response = client.get("/threads", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_list_threads_with_email_type_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread
    ):
        """Test thread listing with email type filter."""
        response = client.get(
            "/threads",
            headers=auth_headers,
            params={"email_type": "GST_FILING"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for thread in data["threads"]:
            assert thread["email_type"] == "GST_FILING"
    
    def test_list_threads_with_status_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread
    ):
        """Test thread listing with status filter."""
        response = client.get(
            "/threads",
            headers=auth_headers,
            params={"status": "awaiting_reply"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for thread in data["threads"]:
            assert thread["status"] == "awaiting_reply"
    
    def test_list_threads_exclude_archived(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread
    ):
        """Test that archived threads are excluded by default."""
        response = client.get(
            "/threads",
            headers=auth_headers,
            params={"is_archived": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for thread in data["threads"]:
            assert thread["is_archived"] == False


class TestThreadDetail:
    """Test thread detail endpoint."""
    
    def test_get_thread_with_emails(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread,
        test_email
    ):
        """Test getting thread with all emails."""
        response = client.get(
            f"/threads/{test_thread.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_thread.id
        assert "emails" in data
        assert isinstance(data["emails"], list)
    
    def test_get_thread_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test thread retrieval with invalid ID."""
        response = client.get(
            "/threads/invalid-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestThreadUpdate:
    """Test thread update endpoint."""
    
    def test_update_thread_status(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread
    ):
        """Test updating thread status."""
        payload = {
            "status": "replied"
        }
        
        response = client.patch(
            f"/threads/{test_thread.id}",
            headers=auth_headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread"]["status"] == "replied"
    
    def test_update_thread_flag(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread
    ):
        """Test updating thread flag status."""
        payload = {
            "is_flagged": True
        }
        
        response = client.patch(
            f"/threads/{test_thread.id}",
            headers=auth_headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["thread"]["is_flagged"] == True
    
    def test_update_thread_invalid_status(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread
    ):
        """Test updating with invalid status."""
        payload = {
            "status": "invalid_status"
        }
        
        response = client.patch(
            f"/threads/{test_thread.id}",
            headers=auth_headers,
            json=payload
        )
        
        assert response.status_code == 400


class TestThreadResolve:
    """Test thread resolve endpoint."""
    
    def test_resolve_thread(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread,
        db: Session
    ):
        """Test resolving a thread."""
        response = client.post(
            f"/threads/{test_thread.id}/resolve",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify thread is resolved
        db.refresh(test_thread)
        assert test_thread.status == ThreadStatus.RESOLVED.value
    
    def test_reopen_thread(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread,
        db: Session
    ):
        """Test reopening a resolved thread."""
        # First resolve it
        test_thread.status = ThreadStatus.RESOLVED.value
        db.commit()
        
        # Then reopen
        response = client.post(
            f"/threads/{test_thread.id}/reopen",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify thread is reopened
        db.refresh(test_thread)
        assert test_thread.status == ThreadStatus.AWAITING_REPLY.value


class TestThreadArchive:
    """Test thread archive endpoints."""
    
    def test_archive_thread(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread,
        db: Session
    ):
        """Test archiving a thread."""
        response = client.post(
            f"/threads/{test_thread.id}/archive",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify thread is archived
        db.refresh(test_thread)
        assert test_thread.is_archived == True
        assert test_thread.status == ThreadStatus.ARCHIVED.value
    
    def test_unarchive_thread(
        self,
        client: TestClient,
        auth_headers: dict,
        test_thread: EmailThread,
        db: Session
    ):
        """Test unarchiving a thread."""
        # First archive it
        test_thread.is_archived = True
        test_thread.status = ThreadStatus.ARCHIVED.value
        db.commit()
        
        # Then unarchive
        response = client.post(
            f"/threads/{test_thread.id}/unarchive",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Verify thread is unarchived
        db.refresh(test_thread)
        assert test_thread.is_archived == False


class TestThreadStatuses:
    """Test thread statuses endpoint."""
    
    def test_get_thread_statuses(
        self,
        client: TestClient
    ):
        """Test getting available thread statuses."""
        response = client.get("/threads/statuses")
        
        assert response.status_code == 200
        data = response.json()
        assert "statuses" in data
        assert len(data["statuses"]) > 0
        
        # Verify status structure
        for status in data["statuses"]:
            assert "value" in status
            assert "label" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
