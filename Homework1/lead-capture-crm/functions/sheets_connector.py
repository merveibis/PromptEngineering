"""
sheets_connector.py — Google Sheets CRM Connector

Appends each validated lead to a Google Sheets spreadsheet.
Authentication: Service Account JSON key (OAuth2).
"""

import os, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES           = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID   = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON', 'service_account.json')
SHEET_NAME       = 'Leads'

COLUMN_ORDER = [
    'lead_id', 'created_at', 'full_name', 'email', 'phone',
    'company_name', 'job_title', 'industry', 'annual_revenue',
    'employees', 'country', 'source', 'website', 'lead_score',
    'status', 'notes',
]


def _get_service():
    """Build authenticated Google Sheets service client."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=creds).spreadsheets()


def ensure_header(service):
    """Write column headers on row 1 if the sheet is empty."""
    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A1:P1'
    ).execute()
    if not result.get('values'):
        service.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A1',
            valueInputOption='RAW',
            body={'values': [[c.replace('_', ' ').title() for c in COLUMN_ORDER]]}
        ).execute()


def append_lead_to_sheet(lead: dict) -> dict:
    """
    Append a processed lead dict as a new row in Google Sheets.
    Returns the API response metadata.
    """
    service = _get_service()
    ensure_header(service)

    row = [str(lead.get(col, '')) for col in COLUMN_ORDER]

    result = service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A1',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': [row]}
    ).execute()

    return result.get('updates', {})
