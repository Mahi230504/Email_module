"""
Tests for the email classification service.
"""

import pytest

from services.classification_service import EmailClassifier, EmailType


class TestEmailClassification:
    """Test email type classification."""
    
    def test_classifies_nil_filing(self):
        """Test NIL filing classification."""
        subject = "NIL Filing Confirmation for March 2026"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.NIL_FILING
    
    def test_classifies_nil_return(self):
        """Test NIL return classification."""
        subject = "Nil Return Submitted"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.NIL_FILING
    
    def test_classifies_vat_filing(self):
        """Test VAT filing classification."""
        subject = "VAT Filing Status Update"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.VAT_FILING
    
    def test_classifies_gst_filing(self):
        """Test GST filing classification."""
        subject = "GST Return for Q4"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.GST_FILING
    
    def test_classifies_gstr_form(self):
        """Test GSTR form classification."""
        subject = "GSTR-1 for January 2026"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.GST_FILING
    
    def test_classifies_itr_submission(self):
        """Test ITR submission classification."""
        subject = "ITR Submission Confirmation AY 2025-26"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.ITR_SUBMISSION
    
    def test_classifies_income_tax_return(self):
        """Test income tax return classification."""
        subject = "Income Tax Return Filed Successfully"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.ITR_SUBMISSION
    
    def test_classifies_doc_request(self):
        """Test document request classification."""
        subject = "Please provide bank statements"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.DOC_REQUEST
    
    def test_classifies_awaiting_documents(self):
        """Test awaiting documents classification."""
        subject = "Awaiting PAN card copy"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.DOC_REQUEST
    
    def test_classifies_compliance_notice(self):
        """Test compliance notice classification."""
        subject = "URGENT NOTICE: Action Required"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.COMPLIANCE_NOTICE
    
    def test_classifies_penalty_notice(self):
        """Test penalty notice classification."""
        subject = "Penalty Notice for Late Filing"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.COMPLIANCE_NOTICE
    
    def test_classifies_rti_submission(self):
        """Test RTI submission classification."""
        subject = "RTI File Generated and Attached"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.RTI_SUBMISSION
    
    def test_classifies_general(self):
        """Test general classification."""
        subject = "Hello, how are you?"
        result = EmailClassifier.classify(subject)
        assert result == EmailType.GENERAL
    
    def test_uses_body_for_classification(self):
        """Test classification uses body content."""
        subject = "Update"
        body = "Please provide the bank statements for the assessment"
        result = EmailClassifier.classify(subject, body)
        assert result == EmailType.DOC_REQUEST
    
    def test_compliance_notice_priority(self):
        """Test compliance notice has priority."""
        subject = "URGENT NOTICE: GST Filing Required"
        result = EmailClassifier.classify(subject)
        # Compliance notice should take priority
        assert result == EmailType.COMPLIANCE_NOTICE


class TestClassificationConfidence:
    """Test classification confidence scores."""
    
    def test_high_confidence_with_multiple_matches(self):
        """Test high confidence when multiple patterns match."""
        subject = "GST Return for GSTR-1"
        result = EmailClassifier.get_classification_confidence(subject)
        
        assert result["type"] == EmailType.GST_FILING
        assert result["confidence"] >= 0.7
        assert result["matches"] >= 2
    
    def test_low_confidence_for_general(self):
        """Test low confidence for general emails."""
        subject = "Meeting tomorrow"
        result = EmailClassifier.get_classification_confidence(subject)
        
        assert result["type"] == EmailType.GENERAL
        assert result["confidence"] == 0.5


class TestDisplayNames:
    """Test display name generation."""
    
    def test_nil_filing_display_name(self):
        """Test NIL filing display name."""
        name = EmailClassifier.get_type_display_name(EmailType.NIL_FILING)
        assert name == "NIL Filing Confirmation"
    
    def test_gst_filing_display_name(self):
        """Test GST filing display name."""
        name = EmailClassifier.get_type_display_name(EmailType.GST_FILING)
        assert name == "GST Filing Confirmation"
    
    def test_general_display_name(self):
        """Test general display name."""
        name = EmailClassifier.get_type_display_name(EmailType.GENERAL)
        assert name == "General"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
