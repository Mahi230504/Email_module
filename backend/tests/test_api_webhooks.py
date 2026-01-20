"""
Tests for webhook API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from models.user import User


class TestWebhookNotification:
    """Test webhook notification endpoint."""
    
    def test_validation_token_response(self, client: TestClient):
        """Test validation token response for Microsoft Graph."""
        validation_token = "test-validation-token-123"
        
        response = client.post(
            "/webhooks/notify",
            params={"validationToken": validation_token},
            json={}
        )
        
        assert response.status_code == 200
        assert response.text == validation_token
    
    @patch('services.graph_service.GraphService.get_message')
    @patch('services.auth_service.AuthService.get_valid_access_token')
    def test_handle_new_email_notification(
        self,
        mock_get_token: MagicMock,
        mock_get_message: MagicMock,
        client: TestClient,
        test_user: User,
        db,
        mock_graph_api_response: dict
    ):
        """Test handling of new email notification."""
        # Set up subscription for user
        test_user.graph_subscription_id = "sub-123"
        db.commit()
        
        mock_get_token.return_value = "access-token"
        mock_get_message.return_value = mock_graph_api_response
        
        payload = {
            "value": [
                {
                    "subscriptionId": "sub-123",
                    "clientState": "test-webhook-secret",  # Match settings
                    "changeType": "created",
                    "resource": "messages/msg-456",
                    "resourceData": {
                        "id": "msg-456"
                    }
                }
            ]
        }
        
        # Patch settings for webhook secret
        with patch('routes.webhooks.settings.webhook_secret', "test-webhook-secret"):
            response = client.post("/webhooks/notify", json=payload)
        
        assert response.status_code == 200


class TestWebhookSubscription:
    """Test webhook subscription management."""
    
    @patch('services.graph_service.GraphService.create_subscription')
    @patch('services.auth_service.AuthService.get_valid_access_token')
    def test_create_subscription(
        self,
        mock_get_token: MagicMock,
        mock_create_sub: MagicMock,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test creating webhook subscription."""
        mock_get_token.return_value = "access-token"
        mock_create_sub.return_value = {
            "id": "subscription-123",
            "expirationDateTime": (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z"
        }
        
        response = client.post("/webhooks/subscribe", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "subscription_id" in data
        assert "expires_at" in data
    
    @patch('services.graph_service.GraphService.renew_subscription')
    @patch('services.auth_service.AuthService.get_valid_access_token')
    def test_renew_existing_subscription(
        self,
        mock_get_token: MagicMock,
        mock_renew: MagicMock,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db
    ):
        """Test renewing existing subscription."""
        # Set existing subscription
        test_user.graph_subscription_id = "existing-sub-123"
        db.commit()
        
        mock_get_token.return_value = "access-token"
        mock_renew.return_value = {
            "id": "existing-sub-123",
            "expirationDateTime": (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z"
        }
        
        response = client.post("/webhooks/subscribe", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "renewed" in data["message"].lower() or "created" in data["message"].lower()
    
    @patch('services.graph_service.GraphService.delete_subscription')
    @patch('services.auth_service.AuthService.get_valid_access_token')
    def test_delete_subscription(
        self,
        mock_get_token: MagicMock,
        mock_delete: MagicMock,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db
    ):
        """Test deleting webhook subscription."""
        # Set existing subscription
        test_user.graph_subscription_id = "sub-to-delete"
        db.commit()
        
        mock_get_token.return_value = "access-token"
        mock_delete.return_value = None
        
        response = client.delete("/webhooks/subscribe", headers=auth_headers)
        
        assert response.status_code == 200


class TestWebhookStatus:
    """Test webhook status endpoint."""
    
    def test_status_with_active_subscription(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db
    ):
        """Test status check with active subscription."""
        # Set active subscription
        test_user.graph_subscription_id = "active-sub-123"
        test_user.graph_subscription_expires_at = datetime.utcnow() + timedelta(days=2)
        db.commit()
        
        response = client.get("/webhooks/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["active"] == True
        assert data["subscription_id"] == "active-sub-123"
    
    def test_status_without_subscription(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test status check without subscription."""
        response = client.get("/webhooks/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["active"] == False
        assert data["subscription_id"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
