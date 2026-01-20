"""
Token encryption utilities using Fernet symmetric encryption.
"""

from cryptography.fernet import Fernet, InvalidToken
from app.config import get_settings

settings = get_settings()


class TokenEncryption:
    """Handles encryption and decryption of OAuth tokens."""
    
    def __init__(self):
        key = settings.encryption_key
        if not key:
            # Generate a key if not provided (for development only)
            key = Fernet.generate_key().decode()
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
    
    def encrypt(self, token: str) -> str:
        """
        Encrypt a token for secure storage.
        
        Args:
            token: Plain text token
            
        Returns:
            Encrypted token as string
        """
        if not token:
            return ""
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt(self, encrypted_token: str) -> str:
        """
        Decrypt a stored token.
        
        Args:
            encrypted_token: Encrypted token string
            
        Returns:
            Decrypted plain text token
            
        Raises:
            InvalidToken: If decryption fails
        """
        if not encrypted_token:
            return ""
        try:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except InvalidToken:
            raise ValueError("Failed to decrypt token - invalid or corrupted")


# Singleton instance
_encryption = None


def get_encryption() -> TokenEncryption:
    """Get singleton encryption instance."""
    global _encryption
    if _encryption is None:
        _encryption = TokenEncryption()
    return _encryption
