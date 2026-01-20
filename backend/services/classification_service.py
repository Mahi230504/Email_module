"""
Email classification service.
"""

import re
from enum import Enum
from typing import Optional, Dict


class EmailType(str, Enum):
    """Email type classification."""
    NIL_FILING = "NIL_FILING"
    VAT_FILING = "VAT_FILING"
    GST_FILING = "GST_FILING"
    ITR_SUBMISSION = "ITR_SUBMISSION"
    DOC_REQUEST = "DOC_REQUEST"
    COMPLIANCE_NOTICE = "COMPLIANCE_NOTICE"
    RTI_SUBMISSION = "RTI_SUBMISSION"
    GENERAL = "GENERAL"


class EmailClassifier:
    """
    Rule-based email classifier.
    
    Classifies emails into predefined types based on subject and body patterns.
    """
    
    # Pattern definitions for each email type
    PATTERNS = {
        EmailType.NIL_FILING: [
            r"nil\s+filing",
            r"nil\s+return",
            r"no\s+income",
            r"nil\s+profit",
            r"zero\s+return",
        ],
        EmailType.VAT_FILING: [
            r"vat\s+filing",
            r"vat\s+return",
            r"vat\s+submission",
            r"value\s+added\s+tax",
            r"vat-\d+",
        ],
        EmailType.GST_FILING: [
            r"gst\s+filing",
            r"gst\s+return",
            r"gst\s+submission",
            r"goods\s+and\s+services\s+tax",
            r"gstr-\d+",
            r"gstin",
        ],
        EmailType.ITR_SUBMISSION: [
            r"itr\s+submission",
            r"income\s+tax\s+return",
            r"itr\s+filed",
            r"itr\s+status",
            r"itr-\d+",
            r"tax\s+return",
            r"assessment\s+year",
        ],
        EmailType.DOC_REQUEST: [
            r"please\s+provide",
            r"please\s+submit",
            r"document\s+required",
            r"documentation\s+needed",
            r"waiting\s+for",
            r"awaiting",
            r"kindly\s+send",
            r"request\s+for\s+documents?",
            r"pending\s+documents?",
        ],
        EmailType.COMPLIANCE_NOTICE: [
            r"compliance\s+notice",
            r"urgent\s+notice",
            r"important\s+notice",
            r"action\s+required",
            r"immediate\s+attention",
            r"penalty\s+notice",
            r"show\s+cause",
            r"scrutiny\s+notice",
        ],
        EmailType.RTI_SUBMISSION: [
            r"rti\s+file",
            r"rti\s+submission",
            r"return\s+of\s+tax\s+information",
            r"rti\s+generated",
            r"rti\s+attached",
        ],
    }
    
    # Priority order (earlier = higher priority)
    PRIORITY_ORDER = [
        EmailType.COMPLIANCE_NOTICE,  # High priority items first
        EmailType.RTI_SUBMISSION,
        EmailType.NIL_FILING,
        EmailType.VAT_FILING,
        EmailType.GST_FILING,
        EmailType.ITR_SUBMISSION,
        EmailType.DOC_REQUEST,
    ]
    
    @classmethod
    def classify(
        cls, 
        subject: str, 
        body: Optional[str] = None
    ) -> EmailType:
        """
        Classify email based on subject and body.
        
        Args:
            subject: Email subject
            body: Email body text (optional)
            
        Returns:
            EmailType classification
        """
        # Combine subject and body for matching
        text = f"{subject} {body or ''}".lower()
        
        # Check patterns in priority order
        for email_type in cls.PRIORITY_ORDER:
            patterns = cls.PATTERNS.get(email_type, [])
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return email_type
        
        # Default to GENERAL
        return EmailType.GENERAL
    
    @classmethod
    def get_classification_confidence(
        cls, 
        subject: str, 
        body: Optional[str] = None
    ) -> Dict:
        """
        Get classification with confidence score.
        
        Args:
            subject: Email subject
            body: Email body text
            
        Returns:
            Dict with type and confidence
        """
        text = f"{subject} {body or ''}".lower()
        
        matches = {}
        
        # Count pattern matches for each type
        for email_type, patterns in cls.PATTERNS.items():
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    match_count += 1
            
            if match_count > 0:
                matches[email_type] = match_count
        
        if not matches:
            return {
                "type": EmailType.GENERAL,
                "confidence": 0.5,
                "matches": 0
            }
        
        # Find type with most matches
        best_type = max(matches, key=matches.get)
        best_count = matches[best_type]
        
        # Calculate confidence based on match count
        confidence = min(0.95, 0.6 + (best_count * 0.1))
        
        return {
            "type": best_type,
            "confidence": confidence,
            "matches": best_count
        }
    
    @staticmethod
    def get_type_display_name(email_type: EmailType) -> str:
        """Get human-readable name for email type."""
        display_names = {
            EmailType.NIL_FILING: "NIL Filing Confirmation",
            EmailType.VAT_FILING: "VAT Filing Confirmation",
            EmailType.GST_FILING: "GST Filing Confirmation",
            EmailType.ITR_SUBMISSION: "ITR Submission Status",
            EmailType.DOC_REQUEST: "Document Request",
            EmailType.COMPLIANCE_NOTICE: "Compliance Notice",
            EmailType.RTI_SUBMISSION: "RTI File Submission",
            EmailType.GENERAL: "General",
        }
        return display_names.get(email_type, email_type.value)
