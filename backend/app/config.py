"""
Configuration management for the Email Module.
Uses Pydantic Settings for environment variable loading.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Outlook Email Module"
    debug: bool = False
    platform_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    secret_key: str = "change-this-in-production"
    
    # Azure AD Configuration
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/email_module_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Elasticsearch
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_url: Optional[str] = None
    
    # Encryption
    encryption_key: str = ""
    
    # Webhook
    webhook_secret: str = ""
    
    # Features
    enable_webhooks: bool = True
    background_sync_interval: int = 120  # seconds
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    # Token settings
    access_token_expire_minutes: int = 30
    
    @property
    def microsoft_auth_url(self) -> str:
        """Microsoft OAuth authorization URL."""
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/authorize"
    
    @property
    def microsoft_token_url(self) -> str:
        """Microsoft OAuth token URL."""
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}/oauth2/v2.0/token"
    
    @property
    def redirect_uri(self) -> str:
        """OAuth redirect URI."""
        return f"{self.platform_url}/auth/callback"
    
    @property
    def graph_scopes(self) -> str:
        """Microsoft Graph API scopes."""
        return "Mail.ReadWrite Mail.Send MailboxSettings.ReadWrite User.Read offline_access"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
