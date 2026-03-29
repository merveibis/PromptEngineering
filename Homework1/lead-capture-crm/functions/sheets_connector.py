"""
sheets_connector.py — Google Antigravity External API Step (Step 2)

Platform: Google Antigravity (Agents + Workflows)
Primary:  Google Sheets API (service account, when GOOGLE_SHEETS_SPREADSHEET_ID is set)
Fallback: Local CSV file (crm_leads.csv) when Sheets credentials are not configured.

Authentication: Service Account JSON key (OAuth2).
"""

import os, csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SPREADSHEET_ID   = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON', 'service_account.json')
SHEET_NAME       = 'Sayfa1'
CSV_PATH         = Path(__file__).parent.parent / 'data' / 'crm_leads.csv'

COLUMN_ORDER = [
    'lead_id', 'created_at', 'full_name', 'email', 'phone',
    'company_name', 'job_title', 'industry', 'annual_revenue',
    'employees', 'country', 'source', 'website', 'lead_score',
    'status', 'notes',
]


# ── Google Sheets path ────────────────────────────────────────

def _get_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=creds).spreadsheets()


def _sheets_append(lead: dict) -> dict:
    service = _get_service()
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

    row = [str(lead.get(col, '')) for col in COLUMN_ORDER]
    result = service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A1',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': [row]}
    ).execute()
    return result.get('updates', {})


# ── CSV fallback path ─────────────────────────────────────────

def _csv_append(lead: dict) -> dict:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not CSV_PATH.exists()
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMN_ORDER)
        if write_header:
            writer.writeheader()
        writer.writerow({col: lead.get(col, '') for col in COLUMN_ORDER})
    # count rows for the response
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        row_count = sum(1 for _ in f) - 1  # exclude header
    return {'updatedRange': f'crm_leads.csv!row{row_count}', 'updatedRows': 1}


# ── Public interface ──────────────────────────────────────────

def append_lead_to_sheet(lead: dict) -> dict:
    """
    Append a processed lead to CRM.
    Uses Google Sheets when configured, otherwise writes to local crm_leads.csv.
    """
    if SPREADSHEET_ID and os.path.exists(CREDENTIALS_FILE):
        return _sheets_append(lead)
    return _csv_append(lead)
