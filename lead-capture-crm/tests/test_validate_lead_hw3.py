"""
test_validate_lead_hw3.py — Unit tests for HW3 validation and lead flagging.

Tests the 'flag not discard' behaviour: invalid leads must always return a
processable record with validation_status='Invalid', never raise an error.
"""
import pytest
from functions.validate_lead_hw3 import validate_and_flag, validate_email


class TestValidateEmail:
    def test_valid_standard(self):
        assert validate_email("user@example.com")

    def test_valid_subdomain(self):
        assert validate_email("user@mail.example.co.uk")

    def test_valid_plus_tag(self):
        assert validate_email("user+tag@domain.org")

    def test_invalid_no_at(self):
        assert not validate_email("userexample.com")

    def test_invalid_no_domain(self):
        assert not validate_email("user@")

    def test_invalid_empty(self):
        assert not validate_email("")

    def test_invalid_spaces(self):
        assert not validate_email("user @example.com")


class TestValidateAndFlag:

    # ── Valid leads ────────────────────────────────────────────────────────

    def test_valid_lead_returns_valid_status(self):
        raw = {"name": "Alice", "email": "alice@example.com", "message": "Hello"}
        result = validate_and_flag(raw)
        assert result['validation_status'] == 'Valid'
        assert result['validation_errors'] == ''

    def test_valid_lead_preserves_all_fields(self):
        raw = {"name": "Bob Smith", "email": "bob@corp.io", "message": "Need a demo please"}
        result = validate_and_flag(raw)
        assert result['name']    == "Bob Smith"
        assert result['email']   == "bob@corp.io"
        assert result['message'] == "Need a demo please"

    def test_valid_lead_has_contact_id(self):
        raw = {"name": "X", "email": "x@y.com", "message": "Hi"}
        result = validate_and_flag(raw)
        assert result.get('contact_id')
        assert len(result['contact_id']) == 8

    def test_valid_lead_email_normalised(self):
        raw = {"name": "Test", "email": "  TEST@EXAMPLE.COM  ", "message": "Hi"}
        result = validate_and_flag(raw)
        assert result['email'] == "test@example.com"
        assert result['validation_status'] == 'Valid'

    # ── Invalid leads — must NEVER be discarded ────────────────────────────

    def test_missing_email_flagged_not_discarded(self):
        raw = {"name": "No Email", "message": "Hello"}
        result = validate_and_flag(raw)
        assert 'error' not in result
        assert result['validation_status'] == 'Invalid'
        assert "email" in result['validation_errors'].lower()

    def test_missing_name_flagged_not_discarded(self):
        raw = {"email": "test@example.com", "message": "Hello"}
        result = validate_and_flag(raw)
        assert result['validation_status'] == 'Invalid'
        assert "name" in result['validation_errors'].lower()

    def test_missing_message_flagged_not_discarded(self):
        raw = {"name": "Alice", "email": "alice@example.com"}
        result = validate_and_flag(raw)
        assert result['validation_status'] == 'Invalid'
        assert "message" in result['validation_errors'].lower()

    def test_bad_email_format_flagged(self):
        raw = {"name": "Carol", "email": "not-an-email", "message": "Hi"}
        result = validate_and_flag(raw)
        assert result['validation_status'] == 'Invalid'
        assert "email" in result['validation_errors'].lower()

    def test_empty_payload_flagged(self):
        result = validate_and_flag({})
        assert result['validation_status'] == 'Invalid'
        assert result['validation_errors'] != ''

    def test_all_empty_strings_flagged(self):
        raw = {"name": "", "email": "", "message": ""}
        result = validate_and_flag(raw)
        assert result['validation_status'] == 'Invalid'

    def test_multiple_errors_all_reported(self):
        raw = {"name": "", "email": "bad@", "message": ""}
        result = validate_and_flag(raw)
        assert result['validation_status'] == 'Invalid'
        errors = result['validation_errors']
        assert "name" in errors.lower()
        assert "message" in errors.lower()

    # ── Grading criteria: system marks bad data ────────────────────────────

    def test_invalid_lead_still_has_contact_id(self):
        """HW3 Success Criteria: invalid data is marked, not dropped."""
        raw = {"name": "Ghost"}
        result = validate_and_flag(raw)
        assert result['contact_id']
        assert result['validation_status'] == 'Invalid'

    def test_invalid_lead_still_has_created_at(self):
        raw = {"email": "bad-format"}
        result = validate_and_flag(raw)
        assert result['created_at']

    def test_original_data_preserved_in_invalid_lead(self):
        raw = {"name": "Keep Me", "email": "bad", "message": "Save this"}
        result = validate_and_flag(raw)
        assert result['name']    == "Keep Me"
        assert result['message'] == "Save this"
