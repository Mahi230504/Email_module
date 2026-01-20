"""
Authentication decorators and dependencies.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import get_settings
from models.user import User
from services.auth_service import AuthService
from utils.encryption import get_encryption

settings = get_settings()
encryption = get_encryption()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Validates the bearer token and returns the user.
    
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Find user by token
    # In production, you'd decode a JWT or session token
    # For this implementation, we use a simple user ID in the token
    user = db.query(User).filter(User.id == token).first()
    
    if not user:
        # Try finding by access token
        users = db.query(User).filter(User.access_token.isnot(None)).all()
        for u in users:
            try:
                decrypted = encryption.decrypt(u.access_token)
                if decrypted == token:
                    user = u
                    break
            except:
                continue
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )
    
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional user dependency - returns None if not authenticated.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(allowed_roles: list):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @app.get("/admin", dependencies=[Depends(require_role(["admin"]))])
    """
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    
    return role_checker


# Type aliases for cleaner route definitions
CurrentUser = Depends(get_current_user)
OptionalUser = Depends(get_current_user_optional)
AdminOnly = Depends(require_role(["admin"]))
