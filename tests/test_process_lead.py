"""Unit tests for process_lead function."""

import pytest
from functions.process_lead import process_lead, validate_email, compute_lead_score


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("test@example.com") is True

    def test_valid_email_with_dots(self):
        assert validate_email("first.last@company.co.uk") is True

    def test_invalid_email_no_at(self):
        assert validate_email("testexample.com") is False

    def test_invalid_email_empty(self):
        assert validate_email("") is False


class TestComputeLeadScore:
    def test_high_revenue_referral(self):
        data = {
            'annual_revenue': 50_000_000,
            'phone': '+1-555-0100',
            'job_title': 'CEO',
            'source': 'referral',
            'employees': 600,
        }
        score = compute_lead_score(data)
        assert score >= 80

    def test_low_value_cold_lead(self):
        data = {
            'annual_revenue': 50_000,
            'source': 'cold',
            'employees': 5,
        }
        score = compute_lead_score(data)
        assert score <= 20

    def test_max_cap_100(self):
        data = {
            'annual_revenue': 999_000_000,
            'phone': '+1-555',
            'website': 'https://big.com',
            'job_title': 'CTO',
            'source': 'referral',
            'employees': 10000,
        }
        score = compute_lead_score(data)
        assert score <= 100


class TestProcessLead:
    def test_valid_lead(self):
        raw = {
            'first_name': 'Sarah',
            'last_name': 'Thompson',
            'email': 's.thompson@nexatech.io',
            'company_name': 'NexaTech Solutions',
            'industry': 'technology',
            'source': 'linkedin',
            'annual_revenue': 8500000,
            'employees': 120,
        }
        result = process_lead(raw)
        assert 'error' not in result
        assert result['full_name'] == 'Sarah Thompson'
        assert result['industry'] == 'Technology'
        assert result['source'] == 'LinkedIn'
        assert result['lead_score'] > 0
        assert result['status'] == 'New'

    def test_missing_required_fields(self):
        raw = {'first_name': 'Test'}
        result = process_lead(raw)
        assert 'error' in result

    def test_invalid_email(self):
        raw = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'not-an-email',
            'company_name': 'Test Corp',
        }
        result = process_lead(raw)
        assert 'error' in result
        assert 'Invalid email' in result['error']

    def test_industry_mapping(self):
        raw = {
            'first_name': 'A',
            'last_name': 'B',
            'email': 'a@b.com',
            'company_name': 'C',
            'industry': 'saas',
        }
        result = process_lead(raw)
        assert result['industry'] == 'Technology'

    def test_unknown_industry(self):
        raw = {
            'first_name': 'A',
            'last_name': 'B',
            'email': 'a@b.com',
            'company_name': 'C',
            'industry': 'aerospace',
        }
        result = process_lead(raw)
        assert result['industry'] == 'Aerospace'
