"""
test_process_contact.py — Unit tests for HW2 contact form processing.
Tests the {name, email, message} payload validation and processing.
"""
import pytest
from functions.process_contact import process_contact, validate_email


class TestValidateEmail:
    def test_valid_emails(self):
        assert validate_email("user@example.com")
        assert validate_email("user.name+tag@domain.co")

    def test_invalid_emails(self):
        assert not validate_email("not-an-email")
        assert not validate_email("@domain.com")
        assert not validate_email("")


class TestProcessContact:
    def test_valid_contact(self):
        raw = {"name": "Merve Ibis", "email": "merve@example.com", "message": "Hello, I need help."}
        result = process_contact(raw)
        assert 'error' not in result
        assert result['name'] == "Merve Ibis"
        assert result['email'] == "merve@example.com"
        assert result['message'] == "Hello, I need help."
        assert result['contact_id']
        assert result['status'] == 'New'
        assert result['source'] == 'Contact Form'
        assert result['created_at']

    def test_missing_name(self):
        raw = {"email": "test@example.com", "message": "Hello"}
        result = process_contact(raw)
        assert 'error' in result
        assert 'name' in result['error']

    def test_missing_email(self):
        raw = {"name": "Test User", "message": "Hello"}
        result = process_contact(raw)
        assert 'error' in result
        assert 'email' in result['error']

    def test_missing_message(self):
        raw = {"name": "Test User", "email": "test@example.com"}
        result = process_contact(raw)
        assert 'error' in result
        assert 'message' in result['error']

    def test_invalid_email(self):
        raw = {"name": "Test User", "email": "invalid-email", "message": "Hello"}
        result = process_contact(raw)
        assert 'error' in result
        assert 'Invalid email' in result['error']

    def test_empty_fields(self):
        raw = {"name": "", "email": "test@example.com", "message": "Hello"}
        result = process_contact(raw)
        assert 'error' in result

    def test_email_normalisation(self):
        raw = {"name": "Test", "email": "  USER@EXAMPLE.COM  ", "message": "Hi"}
        result = process_contact(raw)
        assert result['email'] == "user@example.com"

    def test_whitespace_trimming(self):
        raw = {"name": "  John Doe  ", "email": "john@example.com", "message": "  Hello World  "}
        result = process_contact(raw)
        assert result['name'] == "John Doe"
        assert result['message'] == "Hello World"

    def test_no_data_loss(self):
        """HW2 Success Criteria: No data loss during transfer."""
        raw = {"name": "Full Name Here", "email": "full@test.com", "message": "This is a complete message with special chars: @#$%"}
        result = process_contact(raw)
        assert result['name'] == raw['name']
        assert result['email'] == raw['email'].lower()
        assert result['message'] == raw['message']
