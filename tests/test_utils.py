"""
Unit tests for Utility functions module.
"""

import pytest
from datetime import datetime
from utils import (
    format_timestamp, format_priority, format_status,
    validate_priority, validate_status, validate_date, parse_date,
    truncate_text, highlight_search_term, validate_email,
    sanitize_filename, format_file_size
)


class TestFormatting:
    """Test formatting functions."""

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        # Test valid timestamp
        timestamp = "2023-01-01T12:00:00+00:00"
        formatted = format_timestamp(timestamp)
        assert "2023-01-01 12:00:00" in formatted
        
        # Test invalid timestamp
        invalid_timestamp = "invalid-timestamp"
        formatted = format_timestamp(invalid_timestamp)
        assert formatted == invalid_timestamp

    def test_format_priority(self):
        """Test priority formatting."""
        assert "HIGH" in format_priority("high")
        assert "MEDIUM" in format_priority("medium")
        assert "LOW" in format_priority("low")
        assert "unknown" in format_priority("unknown")

    def test_format_status(self):
        """Test status formatting."""
        assert "PENDING" in format_status("pending")
        assert "IN PROGRESS" in format_status("in_progress")
        assert "COMPLETED" in format_status("completed")
        assert "CANCELLED" in format_status("cancelled")
        assert "unknown" in format_status("unknown")


class TestValidation:
    """Test validation functions."""

    def test_validate_priority(self):
        """Test priority validation."""
        assert validate_priority("low") is True
        assert validate_priority("medium") is True
        assert validate_priority("high") is True
        assert validate_priority("LOW") is True  # Case insensitive
        assert validate_priority("invalid") is False
        assert validate_priority("") is False

    def test_validate_status(self):
        """Test status validation."""
        assert validate_status("pending") is True
        assert validate_status("in_progress") is True
        assert validate_status("completed") is True
        assert validate_status("cancelled") is True
        assert validate_status("PENDING") is True  # Case insensitive
        assert validate_status("invalid") is False
        assert validate_status("") is False

    def test_validate_date(self):
        """Test date validation."""
        assert validate_date("2023-01-01") is True
        assert validate_date("2023-01-01T12:00:00") is True
        assert validate_date("2023-01-01T12:00:00+00:00") is True
        assert validate_date("invalid-date") is False
        assert validate_date("") is False

    def test_validate_email(self):
        """Test email validation."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True
        assert validate_email("test+tag@example.com") is True
        assert validate_email("invalid-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("test@") is False
        assert validate_email("") is False


class TestParsing:
    """Test parsing functions."""

    def test_parse_date(self):
        """Test date parsing."""
        # Test valid formats
        assert parse_date("2023-01-01") is not None
        assert parse_date("2023-01-01 12:00:00") is not None
        assert parse_date("01/01/2023") is not None
        assert parse_date("01/01/2023") is not None
        
        # Test invalid formats
        assert parse_date("invalid-date") is None
        assert parse_date("") is None
        assert parse_date(None) is None

    def test_parse_date_formats(self):
        """Test different date formats."""
        # YYYY-MM-DD
        result = parse_date("2023-01-01")
        assert result == "2023-01-01T00:00:00"
        
        # YYYY-MM-DD HH:MM:SS
        result = parse_date("2023-01-01 12:30:45")
        assert result == "2023-01-01T12:30:45"
        
        # DD/MM/YYYY
        result = parse_date("01/01/2023")
        assert result == "2023-01-01T00:00:00"
        
        # MM/DD/YYYY
        result = parse_date("01/01/2023")
        assert result == "2023-01-01T00:00:00"


class TestTextProcessing:
    """Test text processing functions."""

    def test_truncate_text(self):
        """Test text truncation."""
        # Test short text
        assert truncate_text("Short text") == "Short text"
        
        # Test long text
        long_text = "This is a very long text that should be truncated"
        truncated = truncate_text(long_text, max_length=20)
        assert len(truncated) <= 20
        assert truncated.endswith("...")
        
        # Test exact length
        text = "Exactly twenty chars"
        truncated = truncate_text(text, max_length=20)
        assert truncated == text

    def test_highlight_search_term(self):
        """Test search term highlighting."""
        text = "This is a test text"
        
        # Test highlighting
        highlighted = highlight_search_term(text, "test")
        assert "[yellow]test[/yellow]" in highlighted
        
        # Test case insensitive
        highlighted = highlight_search_term(text, "TEST")
        assert "[yellow]test[/yellow]" in highlighted
        
        # Test no search term
        highlighted = highlight_search_term(text, "")
        assert highlighted == text
        
        # Test no match
        highlighted = highlight_search_term(text, "nonexistent")
        assert highlighted == text


class TestFileOperations:
    """Test file operation functions."""

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test valid filename
        assert sanitize_filename("valid_filename.txt") == "valid_filename.txt"
        
        # Test invalid characters
        assert sanitize_filename("file<name>.txt") == "file_name_.txt"
        assert sanitize_filename("file:name.txt") == "file_name.txt"
        assert sanitize_filename("file/name.txt") == "file_name.txt"
        assert sanitize_filename("file\\name.txt") == "file_name.txt"
        assert sanitize_filename("file|name.txt") == "file_name.txt"
        assert sanitize_filename("file?name.txt") == "file_name.txt"
        assert sanitize_filename("file*name.txt") == "file_name.txt"
        
        # Test leading/trailing spaces and dots
        assert sanitize_filename("  filename.txt  ") == "filename.txt"
        assert sanitize_filename("...filename.txt...") == "filename.txt"
        
        # Test empty filename
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"

    def test_format_file_size(self):
        """Test file size formatting."""
        # Test bytes
        assert format_file_size(1023) == "1023.0 B"
        
        # Test kilobytes
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(2048) == "2.0 KB"
        
        # Test megabytes
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(2 * 1024 * 1024) == "2.0 MB"
        
        # Test gigabytes
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        
        # Test terabytes
        assert format_file_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_format_timestamp_edge_cases(self):
        """Test timestamp formatting edge cases."""
        # Test None
        assert format_timestamp(None) == "None"
        
        # Test empty string
        assert format_timestamp("") == ""
        
        # Test malformed timestamp
        assert format_timestamp("2023-13-45T25:70:99") == "2023-13-45T25:70:99"

    def test_parse_date_edge_cases(self):
        """Test date parsing edge cases."""
        # Test None
        assert parse_date(None) is None
        
        # Test empty string
        assert parse_date("") is None
        
        # Test invalid formats
        assert parse_date("not-a-date") is None
        assert parse_date("2023-13-45") is None  # Invalid month/day

    def test_truncate_text_edge_cases(self):
        """Test text truncation edge cases."""
        # Test None
        assert truncate_text(None) == "None"
        
        # Test empty string
        assert truncate_text("") == ""
        
        # Test very short max_length
        assert truncate_text("Long text", max_length=3) == "..."
        assert truncate_text("Long text", max_length=4) == "L..."

    def test_highlight_search_term_edge_cases(self):
        """Test search term highlighting edge cases."""
        # Test None values
        assert highlight_search_term(None, "test") == "None"
        assert highlight_search_term("text", None) == "text"
        
        # Test empty strings
        assert highlight_search_term("", "test") == ""
        assert highlight_search_term("text", "") == "text"
        
        # Test special characters in search term
        text = "Text with special chars: [test]"
        highlighted = highlight_search_term(text, "[test]")
        assert "[yellow]" in highlighted 