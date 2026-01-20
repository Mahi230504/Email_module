"""
Tests for the email threading engine.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from services.threading_engine import EmailThreadingEngine, ThreadingResult


class TestSubjectNormalization:
    """Test subject line normalization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock()
        self.engine = EmailThreadingEngine(self.db)
    
    def test_removes_re_prefix(self):
        """Test removal of Re: prefix."""
        assert self.engine._normalize_subject("Re: GST Filing") == "gst filing"
    
    def test_removes_multiple_re_prefixes(self):
        """Test removal of multiple Re: prefixes."""
        assert self.engine._normalize_subject("Re: Re: Re: GST Filing") == "gst filing"
    
    def test_removes_fwd_prefix(self):
        """Test removal of Fwd: prefix."""
        assert self.engine._normalize_subject("Fwd: Tax Return") == "tax return"
    
    def test_removes_fw_prefix(self):
        """Test removal of Fw: prefix."""
        assert self.engine._normalize_subject("Fw: Tax Return") == "tax return"
    
    def test_removes_mixed_prefixes(self):
        """Test removal of mixed prefixes."""
        result = self.engine._normalize_subject("Re: Fwd: Re: Tax Filing")
        assert result == "tax filing"
    
    def test_removes_brackets(self):
        """Test removal of bracketed prefixes."""
        result = self.engine._normalize_subject("[URGENT] Tax Filing")
        assert result == "tax filing"
    
    def test_lowercases_subject(self):
        """Test lowercasing."""
        result = self.engine._normalize_subject("GST FILING CONFIRMATION")
        assert result == "gst filing confirmation"
    
    def test_normalizes_whitespace(self):
        """Test whitespace normalization."""
        result = self.engine._normalize_subject("GST   Filing    Confirmation")
        assert result == "gst filing confirmation"
    
    def test_handles_empty_subject(self):
        """Test handling of empty subject."""
        assert self.engine._normalize_subject("") == ""
        assert self.engine._normalize_subject(None) == ""


class TestMessageIdCleaning:
    """Test message ID cleaning."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock()
        self.engine = EmailThreadingEngine(self.db)
    
    def test_removes_angle_brackets(self):
        """Test removal of angle brackets."""
        result = self.engine._clean_message_id("<abc123@example.com>")
        assert result == "abc123@example.com"
    
    def test_handles_no_brackets(self):
        """Test handling of message ID without brackets."""
        result = self.engine._clean_message_id("abc123@example.com")
        assert result == "abc123@example.com"
    
    def test_handles_empty_id(self):
        """Test handling of empty message ID."""
        assert self.engine._clean_message_id("") == ""
        assert self.engine._clean_message_id(None) == ""


class TestConversationIdMatching:
    """Test conversation ID matching (Layer 1)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock()
        self.engine = EmailThreadingEngine(self.db)
    
    def test_matches_existing_conversation(self):
        """Test matching by conversation ID."""
        mock_thread = MagicMock()
        mock_thread.id = "thread-123"
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_thread
        
        email_data = {
            "conversationId": "conv-abc123"
        }
        
        result = self.engine._check_conversation_id(email_data)
        
        assert result is not None
        assert result.thread_id == "thread-123"
        assert result.confidence == 1.0
        assert result.method == "conversation_id"
    
    def test_no_match_when_conversation_not_found(self):
        """Test no match when conversation ID doesn't exist."""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        email_data = {
            "conversationId": "unknown-conv"
        }
        
        result = self.engine._check_conversation_id(email_data)
        
        assert result is None
    
    def test_no_match_when_no_conversation_id(self):
        """Test no match when email has no conversation ID."""
        email_data = {}
        
        result = self.engine._check_conversation_id(email_data)
        
        assert result is None


class TestInReplyToMatching:
    """Test In-Reply-To header matching (Layer 3)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock()
        self.engine = EmailThreadingEngine(self.db)
    
    def test_matches_in_reply_to_header(self):
        """Test matching by In-Reply-To header."""
        mock_email = MagicMock()
        mock_email.thread_id = "thread-456"
        mock_email.id = "email-789"
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_email
        
        email_data = {
            "internetMessageHeaders": [
                {"name": "In-Reply-To", "value": "<parent@example.com>"}
            ]
        }
        
        result = self.engine._check_in_reply_to(email_data)
        
        assert result is not None
        assert result.thread_id == "thread-456"
        assert result.parent_id == "email-789"
        assert result.confidence == 0.99
        assert result.method == "rfc_in_reply_to"


class TestThreadingOrchestrator:
    """Test the main threading orchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock()
        self.engine = EmailThreadingEngine(self.db)
    
    def test_creates_new_thread_when_no_match(self):
        """Test new thread creation when no match found."""
        # Mock all layers to return None
        self.db.query.return_value.filter.return_value.first.return_value = None
        self.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        email_data = {
            "subject": "Brand new conversation",
            "from": {"emailAddress": {"address": "sender@example.com"}},
            "toRecipients": [{"emailAddress": {"address": "recipient@example.com"}}]
        }
        
        result = self.engine.thread_email(email_data)
        
        assert result is not None
        assert result.is_new == True
        assert result.method == "new_thread"
        assert result.confidence == 0.0
        assert result.thread_id.startswith("thread_")


class TestRecipientExtraction:
    """Test recipient extraction helpers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = MagicMock()
        self.engine = EmailThreadingEngine(self.db)
    
    def test_extracts_from_address(self):
        """Test from address extraction."""
        email_data = {
            "from": {"emailAddress": {"address": "Sender@Example.COM"}}
        }
        
        result = self.engine._extract_from_address(email_data)
        
        assert result == "sender@example.com"
    
    def test_extracts_recipients(self):
        """Test recipient extraction."""
        email_data = {
            "toRecipients": [
                {"emailAddress": {"address": "user1@example.com"}},
                {"emailAddress": {"address": "User2@Example.COM"}},
            ]
        }
        
        result = self.engine._extract_recipients(email_data, "toRecipients")
        
        assert len(result) == 2
        assert "user1@example.com" in result
        assert "user2@example.com" in result
    
    def test_handles_missing_from(self):
        """Test handling of missing from field."""
        email_data = {}
        
        result = self.engine._extract_from_address(email_data)
        
        assert result == ""
    
    def test_handles_missing_recipients(self):
        """Test handling of missing recipients."""
        email_data = {}
        
        result = self.engine._extract_recipients(email_data, "toRecipients")
        
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
