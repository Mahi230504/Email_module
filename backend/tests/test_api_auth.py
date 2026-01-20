"""
Tests for authentication API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from models.user import User


class TestAuthLogin:
    """Test authentication login endpoint."""
    
    def test_get_login_url(self, client: TestClient):
        """Test getting OAuth login URL."""
        response = client.get("/auth/login")
        
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "microsoftonline.com" in data["auth_url"]
    
    def test_login_url_with_redirect(self, client: TestClient):
        """Test login URL with redirect parameter."""
        response = client.get(
            "/auth/login",
            params={"redirect_url": "http://localhost:3000/dashboard"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data


class TestAuthCallback:
    """Test OAuth callback endpoint."""
    
    @patch('services.auth_service.AuthService.exchange_code_for_tokens')
    @patch('services.auth_service.AuthService.get_user_info')
    def test_callback_success(
        self,
        mock_get_user: MagicMock,
        mock_exchange: MagicMock,
        client: TestClient
    ):
        """Test successful OAuth callback."""
        mock_exchange.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 3600
        }
        
        mock_get_user.return_value = {
            "userPrincipalName": "test@example.com",
            "givenName": "Test",
            "surname": "User"
        }
        
        response = client.get(
            "/auth/callback",
            params={
                "code": "test-auth-code",
                "state": "test-state"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "user" in data
        assert "token" in data
    
    def test_callback_with_error(self, client: TestClient):
        """Test callback with OAuth error."""
        response = client.get(
            "/auth/callback",
            params={
                "error": "access_denied",
                "error_description": "User cancelled login"
            }
        )
        
        assert response.status_code == 400
        assert "access_denied" in response.json()["detail"]


class TestAuthRefreshToken:
    """Test token refresh endpoint."""
    
    @patch('services.auth_service.AuthService.get_valid_access_token')
    def test_refresh_token_success(
        self,
        mock_get_token: MagicMock,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test successful token refresh."""
        mock_get_token.return_value = "new-access-token"
        
        response = client.post("/auth/refresh-token", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestAuthLogout:
    """Test logout endpoint."""
    
    def test_logout_success(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test successful logout."""
        response = client.post("/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Logged out" in data["message"]


class TestAuthMe:
    """Test current user endpoint."""
    
    def test_get_current_user(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test getting current user profile."""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without auth."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401


class TestAuthStatus:
    """Test authentication status endpoint."""
    
    def test_auth_status(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test authentication status check."""
        response = client.get("/auth/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == True
        assert "user" in data
        assert "token_expired" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
