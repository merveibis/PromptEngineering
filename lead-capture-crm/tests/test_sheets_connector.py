"""Unit tests for Google Sheets connector (mocked)."""

import pytest
from unittest.mock import patch, MagicMock


@patch('functions.sheets_connector.CREDENTIALS_FILE', 'service_account.json')
@patch('functions.sheets_connector.SPREADSHEET_ID', 'fake-spreadsheet-id')
@patch('os.path.exists', return_value=True)
@patch('functions.sheets_connector._get_service')
def test_append_lead_to_sheet(mock_service, mock_exists):
    """Test that lead data is correctly formatted and sent to Sheets API."""
    mock_sheets = MagicMock()
    mock_service.return_value = mock_sheets

    # Mock the values().get() for header check
    mock_sheets.values().get().execute.return_value = {
        'values': [['Lead Id', 'Created At', 'Full Name']]
    }
    # Mock the values().append() response
    mock_sheets.values().append().execute.return_value = {
        'updates': {
            'updatedRange': 'Leads!A5:P5',
            'updatedRows': 1,
            'updatedColumns': 16,
        }
    }

    from functions.sheets_connector import append_lead_to_sheet

    test_lead = {
        'lead_id': 'TEST001',
        'created_at': '2026-03-29T12:00:00Z',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone': '+1-555-0100',
        'company_name': 'Test Corp',
        'job_title': 'CEO',
        'industry': 'Technology',
        'annual_revenue': 5000000,
        'employees': 50,
        'country': 'USA',
        'source': 'Website',
        'website': 'https://test.com',
        'lead_score': 75,
        'status': 'New',
        'notes': 'Test note',
    }

    result = append_lead_to_sheet(test_lead)
    assert result.get('updatedRange') == 'Leads!A5:P5'
