"""
validate_lead_hw3.py — HW3: Validation with Lead Flagging (No Discard Policy)

Platform:    Google Antigravity (Agents + Workflows)
Payload:     { name, email, message }
Architecture: Input → Validation (flag Valid/Invalid) → AI Analysis → CRM/Sheets

Key difference from HW2: invalid leads are NEVER discarded.
Every submission is saved with a validation_status of "Valid" or "Invalid"
and a list of validation_errors so the data team can investigate and recover.
"""

import uuid, re
from datetime import datetime, timezone

REQUIRED_FIELDS = ['name', 'email', 'message']


def validate_email(email: str) -> bool:
    """Validate email format using RFC-5321-compatible regex."""
    pattern = r'^[\w.+-]+@[\w-]+\.[\w.-]+$'
    return bool(re.match(pattern, email.strip().lower()))


def validate_and_flag(raw: dict) -> dict:
    """
    Validate a {name, email, message} payload and always return a CRM-ready record.

    Validation rules:
      1. All three required fields must be present and non-empty.
      2. Email field must match the expected format.

    Unlike HW2's process_contact(), this function NEVER returns an error key.
    Bad data is flagged with validation_status="Invalid" and saved alongside
    valid records so no lead is ever lost.

    Returns a dict ready for AI analysis and Sheets persistence containing:
      - contact_id, created_at, name, email, message   (original data)
      - validation_status : "Valid" | "Invalid"
      - validation_errors : list of human-readable error strings (empty if valid)
    """
    errors = []

    # --- Field presence checks ---
    for field in REQUIRED_FIELDS:
        value = raw.get(field, '')
        if not (value and str(value).strip()):
            errors.append(f"Missing required field: '{field}'")

    # --- Email format check (only if the field was present) ---
    email_raw = str(raw.get('email', '')).strip()
    if email_raw and not validate_email(email_raw):
        errors.append(f"Invalid email format: '{email_raw}'")

    is_valid = len(errors) == 0

    # Normalise values — use raw value or empty string if absent
    name    = str(raw.get('name',    '')).strip()
    email   = email_raw.lower() if email_raw else ''
    message = str(raw.get('message', '')).strip()

    record = {
        'contact_id':        str(uuid.uuid4())[:8].upper(),
        'created_at':        datetime.now(timezone.utc).isoformat(),
        'name':              name,
        'email':             email,
        'message':           message,
        'validation_status': 'Valid' if is_valid else 'Invalid',
        'validation_errors': '; '.join(errors) if errors else '',
        # Aliases kept for AI completion compatibility
        'full_name':         name or 'Unknown',
        'company_name':      'N/A',
        'source':            'HW3 Contact Form',
    }

    return record
