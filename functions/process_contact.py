"""
process_contact.py — HW2: Simple Contact Form Processing (Data Input & Persistence)

Platform:    Google Antigravity (Agents + Workflows)
Payload:     { name, email, message }
Architecture: HTTP POST Request -> Antigravity Connector -> Google Sheets / CRM

Processes the simple three-field contact form payload required by HW2.
Validates input, normalises data, and prepares for CRM storage.
"""

import uuid, re
from datetime import datetime, timezone


REQUIRED_FIELDS = ['name', 'email', 'message']


def validate_email(email: str) -> bool:
    """Validate email format using regex pattern."""
    pattern = r'^[\w.+-]+@[\w-]+\.[\w.-]+$'
    return bool(re.match(pattern, email.strip().lower()))


def process_contact(raw: dict) -> dict:
    """
    Process a simple contact form payload: { name, email, message }

    Input:  raw webhook JSON payload with exactly 3 keys
    Output: processed contact record ready for CRM storage

    Validates:
      - All three required fields are present and non-empty
      - Email format is valid
      - No data loss — raw values are preserved exactly as received
    """
    # --- Validate required fields ---
    errors = [f for f in REQUIRED_FIELDS if not raw.get(f, '').strip()]
    if errors:
        return {'error': f'Missing required fields: {errors}'}

    name = raw['name'].strip()
    email = raw['email'].strip().lower()
    message = raw['message'].strip()

    # --- Validate email format ---
    if not validate_email(email):
        return {'error': f'Invalid email address: {email}'}

    # --- Build processed contact record ---
    processed = {
        'contact_id':  str(uuid.uuid4())[:8].upper(),
        'name':        name,
        'email':       email,
        'message':     message,
        'full_name':   name,            # alias for AI completion compatibility
        'company_name': 'N/A',          # placeholder for AI completion compatibility
        'status':      'New',
        'source':      'Contact Form',
        'created_at':  datetime.now(timezone.utc).isoformat(),
    }

    return processed
