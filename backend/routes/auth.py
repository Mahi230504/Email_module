"""
Authentication routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import secrets

from app.database import get_db
from app.config import get_settings
from models.user import User
from services.auth_service import AuthService
from utils.decorators import get_current_user

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login")
async def login(redirect_url: str = Query(None)):
    """
    Initiate OAuth login flow.
    
    Returns the Microsoft login URL to redirect user to.
    """
    # Create state string
    rand_token = secrets.token_urlsafe(32)
    state = rand_token
    
    # If redirect_url provided, append to state
    if redirect_url:
        import base64
        # Simple encoding to avoid separator issues
        encoded_url = base64.urlsafe_b64encode(redirect_url.encode()).decode()
        state = f"{rand_token}|{encoded_url}"
    
    # Store state for CSRF protection (in production, use Redis/session)
    auth_url = AuthService.get_auth_url(state=state)
    
    return {
        "auth_url": auth_url,
        "state": state,
        "message": "Redirect user to auth_url to initiate login"
    }


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Microsoft.
    
    Exchanges authorization code for tokens and creates/updates user.
    """
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth error: {error} - {error_description}"
        )
    
    try:
        # Exchange code for tokens
        tokens = AuthService.exchange_code_for_tokens(code)
        
        # Get user info from Graph
        user_info = AuthService.get_user_info(tokens["access_token"])
        
        # Save or update user
        user = AuthService.save_or_update_user(db, user_info, tokens)
        
        # Check for redirect URL in state
        if state and "|" in state:
            try:
                import base64
                _, encoded_url = state.split("|", 1)
                redirect_url = base64.urlsafe_b64decode(encoded_url.encode()).decode()
                
                # Redirect back to frontend
                return RedirectResponse(f"{redirect_url}?token={user.id}")
            except Exception:
                # Fallback to JSON if decoding fails
                pass
        
        return {
            "message": "Authentication successful",
            "user": user.to_dict(),
            "token": user.id,  # In production, generate a proper JWT
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh-token")
async def refresh_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Refresh the access token.
    """
    try:
        access_token = AuthService.get_valid_access_token(db, current_user)
        
        return {
            "message": "Token refreshed successfully",
            "expires_at": current_user.token_expires_at.isoformat() if current_user.token_expires_at else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user and clear tokens.
    """
    AuthService.logout(db, current_user)
    
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    """
    return current_user.to_dict()


@router.get("/status")
async def auth_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check authentication status and token validity.
    """
    return {
        "authenticated": True,
        "user": current_user.to_dict(),
        "token_expired": current_user.is_token_expired(),
        "token_expires_at": current_user.token_expires_at.isoformat() if current_user.token_expires_at else None,
        "has_subscription": bool(current_user.graph_subscription_id),
        "subscription_expires_at": current_user.graph_subscription_expires_at.isoformat() if current_user.graph_subscription_expires_at else None,
    }
