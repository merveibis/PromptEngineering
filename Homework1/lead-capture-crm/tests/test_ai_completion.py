"""Unit tests for AI completion step (mocked)."""

import pytest
from unittest.mock import patch, MagicMock


@patch('functions.ai_completion.genai')
def test_categorise_and_summarise(mock_genai):
    """Test that AI categorisation returns expected structure."""
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = MagicMock(
        text='{"category": "Technology", "priority": "HOT", "summary": "High-value tech lead."}'
    )

    from functions.ai_completion import categorise_and_summarise

    test_lead = {
        'full_name': 'Sarah Thompson',
        'company_name': 'NexaTech Solutions',
        'job_title': 'VP of Operations',
        'industry': 'Technology',
        'annual_revenue': 8500000,
        'employees': 120,
        'lead_score': 85,
        'source': 'LinkedIn',
        'country': 'USA',
        'notes': 'Interested in automation.',
    }

    result = categorise_and_summarise(test_lead)
    assert result['category'] == 'Technology'
    assert result['priority'] in ['HOT', 'WARM', 'COLD']
    assert len(result['summary']) > 0


@patch('functions.ai_completion.genai')
def test_ai_error_handling(mock_genai):
    """Test graceful fallback when AI call fails."""
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.side_effect = Exception("API quota exceeded")

    from functions.ai_completion import categorise_and_summarise

    result = categorise_and_summarise({'full_name': 'Test'})
    assert result['category'] == 'Other'
    assert result['priority'] == 'WARM'
    assert 'error' in result['summary'].lower()
