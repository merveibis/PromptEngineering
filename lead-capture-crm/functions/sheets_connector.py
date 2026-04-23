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


# ── HW2: Contact form (name, email, message) ─────────────────

CONTACT_COLUMNS = ['contact_id', 'created_at', 'name', 'email', 'message', 'status']
CONTACT_CSV_PATH = Path(__file__).parent.parent / 'data' / 'contacts.csv'
CONTACT_SHEET = 'Contacts'


def _ensure_contact_sheet(service) -> None:
    """Create the 'Contacts' sheet tab if it doesn't already exist."""
    meta = service.get(spreadsheetId=SPREADSHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    if CONTACT_SHEET not in existing:
        service.batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [{'addSheet': {'properties': {'title': CONTACT_SHEET}}}]}
        ).execute()


def _contact_sheets_append(contact: dict) -> dict:
    service = _get_service()
    _ensure_contact_sheet(service)
    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{CONTACT_SHEET}!A1:F1'
    ).execute()
    if not result.get('values'):
        service.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{CONTACT_SHEET}!A1',
            valueInputOption='RAW',
            body={'values': [[c.replace('_', ' ').title() for c in CONTACT_COLUMNS]]}
        ).execute()
    row = [str(contact.get(col, '')) for col in CONTACT_COLUMNS]
    result = service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{CONTACT_SHEET}!A1',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': [row]}
    ).execute()
    return result.get('updates', {})


def _contact_csv_append(contact: dict) -> dict:
    CONTACT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not CONTACT_CSV_PATH.exists()
    with open(CONTACT_CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CONTACT_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({col: contact.get(col, '') for col in CONTACT_COLUMNS})
    with open(CONTACT_CSV_PATH, 'r', encoding='utf-8') as f:
        row_count = sum(1 for _ in f) - 1
    return {'updatedRange': f'contacts.csv!row{row_count}', 'updatedRows': 1}


def append_contact_to_sheet(contact: dict) -> dict:
    """
    Append a contact form submission {name, email, message} to CRM.
    Uses Google Sheets 'Contacts' tab when configured, otherwise contacts.csv.
    Falls back to CSV on any Sheets API error (e.g. missing tab).
    """
    if SPREADSHEET_ID and os.path.exists(CREDENTIALS_FILE):
        try:
            return _contact_sheets_append(contact)
        except Exception:
            pass
    return _contact_csv_append(contact)


# ── HW3: Validated + AI-classified leads (name, email, message + metadata) ───

HW3_COLUMNS = [
    'contact_id', 'created_at', 'name', 'email', 'message',
    'validation_status', 'validation_errors', 'intent', 'urgency',
]
HW3_CSV_PATH = Path(__file__).parent.parent / 'data' / 'hw3_leads.csv'
HW3_SHEET    = 'HW3_Leads'


def _ensure_hw3_sheet(service) -> None:
    """Create the 'HW3_Leads' sheet tab if it doesn't already exist."""
    meta = service.get(spreadsheetId=SPREADSHEET_ID).execute()
    existing = {s['properties']['title'] for s in meta.get('sheets', [])}
    if HW3_SHEET not in existing:
        service.batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [{'addSheet': {'properties': {'title': HW3_SHEET}}}]}
        ).execute()


def _hw3_sheets_append(record: dict) -> dict:
    service = _get_service()
    _ensure_hw3_sheet(service)
    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{HW3_SHEET}!A1:I1'
    ).execute()
    if not result.get('values'):
        service.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{HW3_SHEET}!A1',
            valueInputOption='RAW',
            body={'values': [[c.replace('_', ' ').title() for c in HW3_COLUMNS]]}
        ).execute()
    row = [str(record.get(col, '')) for col in HW3_COLUMNS]
    result = service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{HW3_SHEET}!A1',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': [row]}
    ).execute()
    return result.get('updates', {})


def _hw3_csv_append(record: dict) -> dict:
    HW3_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not HW3_CSV_PATH.exists()
    with open(HW3_CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=HW3_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({col: record.get(col, '') for col in HW3_COLUMNS})
    with open(HW3_CSV_PATH, 'r', encoding='utf-8') as f:
        row_count = sum(1 for _ in f) - 1
    return {'updatedRange': f'hw3_leads.csv!row{row_count}', 'updatedRows': 1}


def append_hw3_to_sheet(record: dict) -> dict:
    """
    Append a HW3 validated + AI-classified record to CRM.
    Writes ALL records (Valid and Invalid) — no data is ever discarded.
    Uses Google Sheets 'HW3_Leads' tab when configured, otherwise hw3_leads.csv.
    """
    if SPREADSHEET_ID and os.path.exists(CREDENTIALS_FILE):
        try:
            return _hw3_sheets_append(record)
        except Exception:
            pass
    return _hw3_csv_append(record)
