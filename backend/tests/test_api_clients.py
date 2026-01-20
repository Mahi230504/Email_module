"""
Tests for client management API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.client import Client
from models.user import User


class TestClientList:
    """Test client listing endpoint."""
    
    def test_list_clients_success(
        self, 
        client: TestClient, 
        auth_headers: dict,
        test_client_corporate: Client,
        test_client_non_corporate: Client
    ):
        """Test successful client listing."""
        response = client.get("/clients", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "clients" in data
        assert "total" in data
        assert data["total"] >= 2
        assert len(data["clients"]) >= 2
    
    def test_list_clients_with_type_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        test_client_corporate: Client
    ):
        """Test client listing with type filter."""
        response = client.get(
            "/clients",
            headers=auth_headers,
            params={"client_type": "corporate"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned clients should be corporate
        for c in data["clients"]:
            assert c["client_type"] == "corporate"
    
    def test_list_clients_with_search(
        self,
        client: TestClient,
        auth_headers: dict,
        test_client_corporate: Client
    ):
        """Test client search functionality."""
        response = client.get(
            "/clients",
            headers=auth_headers,
            params={"search": "ABC"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
    
    def test_list_clients_unauthorized(self, client: TestClient):
        """Test client listing without authentication."""
        response = client.get("/clients")
        assert response.status_code == 401


class TestClientCreate:
    """Test client creation endpoint."""
    
    def test_create_client_success(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test successful client creation."""
        payload = {
            "name": "New Test Client",
            "email": "newclient@example.com",
            "phone": "9999999999",
            "client_type": "corporate",
            "tax_year": "FY 2025-26",
            "pan": "NEWCL1234X",
            "gstin": "27NEWCL1234X1Z5"
        }
        
        response = client.post("/clients", headers=auth_headers, json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "client" in data
        assert data["client"]["name"] == "New Test Client"
        assert data["client"]["pan"] == "NEWCL1234X"
    
    def test_create_client_duplicate_pan(
        self,
        client: TestClient,
        auth_headers: dict,
        test_client_corporate: Client
    ):
        """Test client creation with duplicate PAN."""
        payload = {
            "name": "Duplicate Client",
            "pan": test_client_corporate.pan  # Use existing PAN
        }
        
        response = client.post("/clients", headers=auth_headers, json=payload)
        
        assert response.status_code == 400
        assert "PAN already exists" in response.json()["detail"]
    
    def test_create_client_invalid_pan(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test client creation with invalid PAN format."""
        payload = {
            "name": "Test Client",
            "pan": "INVALID"  # Invalid PAN format
        }
        
        response = client.post("/clients", headers=auth_headers, json=payload)
        
        # Should fail validation
        assert response.status_code == 422


class TestClientDetail:
    """Test client detail endpoint."""
    
    def test_get_client_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_client_corporate: Client
    ):
        """Test successful client retrieval."""
        response = client.get(
            f"/clients/{test_client_corporate.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_client_corporate.id
        assert data["name"] == test_client_corporate.name
    
    def test_get_client_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test client retrieval with invalid ID."""
        response = client.get(
            "/clients/invalid-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestClientUpdate:
    """Test client update endpoint."""
    
    def test_update_client_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_client_corporate: Client
    ):
        """Test successful client update."""
        payload = {
            "name": "Updated Client Name",
            "email": "updated@example.com"
        }
        
        response = client.patch(
            f"/clients/{test_client_corporate.id}",
            headers=auth_headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["client"]["name"] == "Updated Client Name"
        assert data["client"]["email"] == "updated@example.com"


class TestClientEmails:
    """Test client emails endpoint."""
    
    def test_get_client_emails(
        self,
        client: TestClient,
        auth_headers: dict,
        test_client_corporate: Client,
        test_email
    ):
        """Test retrieving client's emails."""
        response = client.get(
            f"/clients/{test_client_corporate.id}/emails",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert "total" in data
        assert data["total"] >= 1


class TestClientThreads:
    """Test client threads endpoint."""
    
    def test_get_client_threads(
        self,
        client: TestClient,
        auth_headers: dict,
        test_client_corporate: Client,
        test_thread
    ):
        """Test retrieving client's threads."""
        response = client.get(
            f"/clients/{test_client_corporate.id}/threads",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data
        assert "total" in data
        assert data["total"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
