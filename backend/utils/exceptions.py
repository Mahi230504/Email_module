"""
Custom exceptions for the Email Module.
"""


class EmailModuleException(Exception):
    """Base exception for email module."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(EmailModuleException):
    """Authentication related errors."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class TokenExpiredError(AuthenticationError):
    """Token has expired."""
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class TokenRefreshError(AuthenticationError):
    """Failed to refresh token."""
    def __init__(self, message: str = "Failed to refresh token"):
        super().__init__(message)


class GraphAPIError(EmailModuleException):
    """Microsoft Graph API errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(f"Graph API Error: {message}", status_code)


class EmailNotFoundError(EmailModuleException):
    """Email not found."""
    def __init__(self, email_id: str):
        super().__init__(f"Email not found: {email_id}", status_code=404)


class ThreadNotFoundError(EmailModuleException):
    """Thread not found."""
    def __init__(self, thread_id: str):
        super().__init__(f"Thread not found: {thread_id}", status_code=404)


class UserNotFoundError(EmailModuleException):
    """User not found."""
    def __init__(self, user_id: str):
        super().__init__(f"User not found: {user_id}", status_code=404)


class ClientNotFoundError(EmailModuleException):
    """Client not found."""
    def __init__(self, client_id: str):
        super().__init__(f"Client not found: {client_id}", status_code=404)


class WebhookValidationError(EmailModuleException):
    """Webhook validation failed."""
    def __init__(self, message: str = "Webhook validation failed"):
        super().__init__(message, status_code=400)


class SubscriptionError(EmailModuleException):
    """Graph subscription errors."""
    def __init__(self, message: str):
        super().__init__(f"Subscription Error: {message}", status_code=500)
