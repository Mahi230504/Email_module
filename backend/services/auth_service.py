"""
Authentication service for Microsoft OAuth 2.0.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.config import get_settings
from models.user import User
from utils.encryption import get_encryption
from utils.exceptions import AuthenticationError, TokenRefreshError

settings = get_settings()
encryption = get_encryption()


class AuthService:
    """Handles Microsoft OAuth 2.0 authentication."""
    
    GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
    
    @staticmethod
    def get_auth_url(state: Optional[str] = None) -> str:
        """
        Generate Microsoft login URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": settings.azure_client_id,
            "redirect_uri": settings.redirect_uri,
            "response_type": "code",
            "scope": settings.graph_scopes,
            "response_mode": "query",
        }
        
        if state:
            params["state"] = state
        
        return f"{settings.microsoft_auth_url}?{urlencode(params)}"
    
    @staticmethod
    def exchange_code_for_tokens(code: str) -> Dict[str, any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Dict with access_token, refresh_token, expires_in
            
        Raises:
            AuthenticationError: If token exchange fails
        """
        data = {
            "client_id": settings.azure_client_id,
            "client_secret": settings.azure_client_secret,
            "code": code,
            "redirect_uri": settings.redirect_uri,
            "grant_type": "authorization_code",
            "scope": settings.graph_scopes,
        }
        
        response = requests.post(settings.microsoft_token_url, data=data)
        
        if response.status_code != 200:
            raise AuthenticationError(f"Token exchange failed: {response.text}")
        
        tokens = response.json()
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens["expires_in"],
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, any]:
        """
        Refresh expired access token.
        
        Args:
            refresh_token: Stored refresh token
            
        Returns:
            Dict with new access_token, refresh_token, expires_in
            
        Raises:
            TokenRefreshError: If refresh fails
        """
        data = {
            "client_id": settings.azure_client_id,
            "client_secret": settings.azure_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": settings.graph_scopes,
        }
        
        response = requests.post(settings.microsoft_token_url, data=data)
        
        if response.status_code != 200:
            raise TokenRefreshError(f"Token refresh failed: {response.text}")
        
        tokens = response.json()
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", refresh_token),
            "expires_in": tokens["expires_in"],
        }
    
    @staticmethod
    def get_user_info(access_token: str) -> Dict[str, any]:
        """
        Get user profile from Microsoft Graph.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User profile data
            
        Raises:
            AuthenticationError: If request fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(
            f"{AuthService.GRAPH_API_URL}/me",
            headers=headers
        )
        
        if response.status_code != 200:
            raise AuthenticationError(f"Failed to get user info: {response.text}")
        
        return response.json()
    
    @staticmethod
    def save_or_update_user(
        db: Session, 
        user_data: Dict, 
        tokens: Dict
    ) -> User:
        """
        Create or update user with OAuth tokens.
        
        Args:
            db: Database session
            user_data: Microsoft Graph user profile
            tokens: OAuth tokens dict
            
        Returns:
            User model instance
        """
        email = user_data.get("userPrincipalName") or user_data.get("mail")
        
        # Find existing user or create new
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(
                email=email,
                first_name=user_data.get("givenName", ""),
                last_name=user_data.get("surname", ""),
            )
            db.add(user)
        
        # Update tokens (encrypted)
        user.access_token = encryption.encrypt(tokens["access_token"])
        if tokens.get("refresh_token"):
            user.refresh_token = encryption.encrypt(tokens["refresh_token"])
        
        user.token_expires_at = datetime.utcnow() + timedelta(
            seconds=tokens["expires_in"]
        )
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_valid_access_token(db: Session, user: User) -> str:
        """
        Get valid access token, refreshing if needed.
        
        Args:
            db: Database session
            user: User model instance
            
        Returns:
            Valid access token
            
        Raises:
            AuthenticationError: If unable to get valid token
        """
        if not user.access_token:
            raise AuthenticationError("No access token stored for user")
        
        # Check if token is expired
        if user.is_token_expired():
            if not user.refresh_token:
                raise AuthenticationError("Token expired and no refresh token available")
            
            # Refresh the token
            try:
                refresh_token = encryption.decrypt(user.refresh_token)
                tokens = AuthService.refresh_access_token(refresh_token)
                
                # Update stored tokens
                user.access_token = encryption.encrypt(tokens["access_token"])
                if tokens.get("refresh_token"):
                    user.refresh_token = encryption.encrypt(tokens["refresh_token"])
                user.token_expires_at = datetime.utcnow() + timedelta(
                    seconds=tokens["expires_in"]
                )
                
                db.commit()
                
                return tokens["access_token"]
                
            except TokenRefreshError:
                raise AuthenticationError("Token refresh failed, user must re-authenticate")
        
        # Token is still valid
        return encryption.decrypt(user.access_token)
    
    @staticmethod
    def logout(db: Session, user: User) -> None:
        """
        Logout user by clearing tokens.
        
        Args:
            db: Database session
            user: User model instance
        """
        user.access_token = None
        user.refresh_token = None
        user.token_expires_at = None
        user.graph_subscription_id = None
        user.graph_subscription_expires_at = None
        
        db.commit()
