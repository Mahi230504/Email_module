"""
Input validators and sanitizers.
"""

import re
from typing import Optional, List
from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime


class EmailAddressValidator:
    """Email address validation utilities."""
    
    # RFC 5322 compliant email regex
    EMAIL_REGEX = re.compile(
        r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    )
    
    @classmethod
    def is_valid(cls, email: str) -> bool:
        """Check if email address is valid."""
        if not email:
            return False
        return bool(cls.EMAIL_REGEX.match(email))
    
    @classmethod
    def validate_list(cls, emails: List[str]) -> tuple:
        """
        Validate a list of email addresses.
        
        Returns:
            Tuple of (valid_emails, invalid_emails)
        """
        valid = []
        invalid = []
        
        for email in emails:
            if cls.is_valid(email):
                valid.append(email.lower().strip())
            else:
                invalid.append(email)
        
        return valid, invalid
    
    @classmethod
    def normalize(cls, email: str) -> str:
        """Normalize email address (lowercase, stripped)."""
        if not email:
            return ""
        return email.lower().strip()


class SubjectValidator:
    """Email subject validation and sanitization."""
    
    MAX_LENGTH = 500
    
    @classmethod
    def sanitize(cls, subject: str) -> str:
        """
        Sanitize email subject.
        
        - Removes control characters
        - Limits length
        - Strips whitespace
        """
        if not subject:
            return ""
        
        # Remove control characters
        sanitized = "".join(
            char for char in subject
            if ord(char) >= 32 or char in "\t\n"
        )
        
        # Normalize whitespace
        sanitized = " ".join(sanitized.split())
        
        # Limit length
        if len(sanitized) > cls.MAX_LENGTH:
            sanitized = sanitized[:cls.MAX_LENGTH - 3] + "..."
        
        return sanitized.strip()
    
    @classmethod
    def is_valid(cls, subject: str) -> bool:
        """Check if subject is valid (not empty after sanitization)."""
        return bool(cls.sanitize(subject))


class BodyValidator:
    """Email body validation and sanitization."""
    
    MAX_LENGTH = 1_000_000  # 1MB text limit
    
    # Dangerous HTML tags to remove
    DANGEROUS_TAGS = re.compile(
        r'<\s*(script|iframe|object|embed|form)[^>]*>.*?</\s*\1\s*>',
        re.IGNORECASE | re.DOTALL
    )
    
    # Event handlers to remove
    EVENT_HANDLERS = re.compile(
        r'\s+(on\w+)\s*=\s*["\'][^"\']*["\']',
        re.IGNORECASE
    )
    
    @classmethod
    def sanitize_html(cls, html: str) -> str:
        """
        Sanitize HTML content.
        
        Removes dangerous tags and event handlers.
        """
        if not html:
            return ""
        
        # Remove dangerous tags
        sanitized = cls.DANGEROUS_TAGS.sub("", html)
        
        # Remove event handlers
        sanitized = cls.EVENT_HANDLERS.sub("", sanitized)
        
        # Limit length
        if len(sanitized) > cls.MAX_LENGTH:
            sanitized = sanitized[:cls.MAX_LENGTH]
        
        return sanitized
    
    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Sanitize plain text content."""
        if not text:
            return ""
        
        # Remove control characters except newlines/tabs
        sanitized = "".join(
            char for char in text
            if ord(char) >= 32 or char in "\t\n\r"
        )
        
        # Limit length
        if len(sanitized) > cls.MAX_LENGTH:
            sanitized = sanitized[:cls.MAX_LENGTH]
        
        return sanitized


class PANValidator:
    """Indian PAN number validator."""
    
    # PAN format: 5 letters, 4 digits, 1 letter
    PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    
    @classmethod
    def is_valid(cls, pan: str) -> bool:
        """Validate PAN number."""
        if not pan:
            return False
        return bool(cls.PAN_REGEX.match(pan.upper()))
    
    @classmethod
    def normalize(cls, pan: str) -> str:
        """Normalize PAN number (uppercase, no spaces)."""
        if not pan:
            return ""
        return pan.upper().replace(" ", "").strip()


class GSTINValidator:
    """Indian GSTIN validator."""
    
    # GSTIN format: 2 digits state code, 10 char PAN, 1 entity, 1 Z, 1 checksum
    GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z][Z][0-9A-Z]$")
    
    @classmethod
    def is_valid(cls, gstin: str) -> bool:
        """Validate GSTIN."""
        if not gstin:
            return False
        return bool(cls.GSTIN_REGEX.match(gstin.upper()))
    
    @classmethod
    def normalize(cls, gstin: str) -> str:
        """Normalize GSTIN."""
        if not gstin:
            return ""
        return gstin.upper().replace(" ", "").strip()
    
    @classmethod
    def extract_pan(cls, gstin: str) -> Optional[str]:
        """Extract PAN from GSTIN."""
        normalized = cls.normalize(gstin)
        if cls.is_valid(normalized):
            return normalized[2:12]
        return None


class PhoneValidator:
    """Phone number validator."""
    
    # Indian phone number (10 digits, may have +91 prefix)
    PHONE_REGEX = re.compile(r"^(\+91[-\s]?)?\d{10}$")
    
    @classmethod
    def is_valid(cls, phone: str) -> bool:
        """Validate phone number."""
        if not phone:
            return False
        # Remove spaces and dashes for validation
        cleaned = re.sub(r"[\s\-]", "", phone)
        return bool(cls.PHONE_REGEX.match(cleaned))
    
    @classmethod
    def normalize(cls, phone: str) -> str:
        """Normalize phone number to 10 digits."""
        if not phone:
            return ""
        # Remove all non-digits
        digits = re.sub(r"\D", "", phone)
        # Remove country code if present
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        return digits[-10:] if len(digits) >= 10 else digits


# Pydantic validators for use in request models

class SendEmailSchema(BaseModel):
    """Schema for sending email with validation."""
    
    to_recipients: List[EmailStr]
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    body_type: str = Field(default="HTML", pattern="^(HTML|Text)$")
    cc_recipients: Optional[List[EmailStr]] = None
    bcc_recipients: Optional[List[EmailStr]] = None
    
    @validator("subject")
    def sanitize_subject(cls, v):
        return SubjectValidator.sanitize(v)
    
    @validator("body")
    def sanitize_body(cls, v, values):
        body_type = values.get("body_type", "HTML")
        if body_type == "HTML":
            return BodyValidator.sanitize_html(v)
        return BodyValidator.sanitize_text(v)


class ClientSchema(BaseModel):
    """Schema for client with validation."""
    
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    pan: Optional[str] = None
    gstin: Optional[str] = None
    
    @validator("pan")
    def validate_pan(cls, v):
        if v and not PANValidator.is_valid(v):
            raise ValueError("Invalid PAN format")
        return PANValidator.normalize(v) if v else None
    
    @validator("gstin")
    def validate_gstin(cls, v):
        if v and not GSTINValidator.is_valid(v):
            raise ValueError("Invalid GSTIN format")
        return GSTINValidator.normalize(v) if v else None
    
    @validator("phone")
    def validate_phone(cls, v):
        if v and not PhoneValidator.is_valid(v):
            raise ValueError("Invalid phone number format")
        return PhoneValidator.normalize(v) if v else None
