"""
demo_hw3.py — HW3: Validation, Flagging & AI Intelligence Pipeline Demo

Demonstrates the full HW3 pipeline end-to-end:
  Input ({name, email, message})
    → Validation (flag Valid/Invalid — never discard)
    → AI Analysis (Intent / Urgency via Gemini 2.0 Flash Lite)
    → CRM/Sheets (full record + metadata)

Run:  python demo_hw3.py
"""

import sys, json
from pathlib import Path

# Add project root to path when running from repo root
sys.path.insert(0, str(Path(__file__).parent))

from functions.validate_lead_hw3 import validate_and_flag
from functions.ai_intent_urgency  import classify_intent_urgency
from functions.sheets_connector   import append_hw3_to_sheet

# ---------------------------------------------------------------------------
# Test cases — mix of valid and deliberately invalid payloads
# ---------------------------------------------------------------------------

TEST_CASES = [
    # Valid leads
    {
        "label": "Valid — Sales, High Urgency",
        "payload": {
            "name":    "Elif Yılmaz",
            "email":   "elif.yilmaz@techcorp.io",
            "message": "We need to purchase 50 licenses ASAP before end of quarter. Please send pricing immediately.",
        },
    },
    {
        "label": "Valid — Support, Medium Urgency",
        "payload": {
            "name":    "James Chen",
            "email":   "j.chen@startup.com",
            "message": "I'm having trouble setting up the API integration. Can you help me this week?",
        },
    },
    {
        "label": "Valid — Partnership, Low Urgency",
        "payload": {
            "name":    "Maria Santos",
            "email":   "maria@agencypartners.eu",
            "message": "We are interested in exploring a white-label reseller partnership for the European market.",
        },
    },
    {
        "label": "Valid — Inquiry, Low Urgency",
        "payload": {
            "name":    "Kemal Aydın",
            "email":   "kemal@university.edu.tr",
            "message": "Merhaba, ürününüz hakkında genel bilgi almak istiyorum.",
        },
    },
    {
        "label": "Valid — Complaint, High Urgency",
        "payload": {
            "name":    "Anna Kovacs",
            "email":   "anna.kovacs@enterprise.hu",
            "message": "Your service has been down for 3 hours and our production is blocked. This is unacceptable!",
        },
    },
    # Invalid leads — must be flagged and saved, NOT discarded
    {
        "label": "INVALID — Missing email field",
        "payload": {
            "name":    "Bob Missing",
            "message": "I want to learn more about your product.",
        },
    },
    {
        "label": "INVALID — Bad email format",
        "payload": {
            "name":    "Carol Badmail",
            "email":   "not-an-email-address",
            "message": "Please contact me regarding your enterprise plan.",
        },
    },
    {
        "label": "INVALID — Missing name and email",
        "payload": {
            "message": "Just a message with no contact info at all.",
        },
    },
    {
        "label": "INVALID — All fields missing",
        "payload": {},
    },
]


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline(label: str, payload: dict) -> dict:
    print(f"\n{'─' * 64}")
    print(f"  {label}")
    print(f"{'─' * 64}")
    print(f"  INPUT: {json.dumps(payload, ensure_ascii=False)}")

    # STEP 1: Validate & flag (never discards)
    flagged = validate_and_flag(payload)
    status  = flagged['validation_status']
    errors  = flagged['validation_errors']
    print(f"  STEP 1 → Validation  : {status}" + (f"  [{errors}]" if errors else ""))

    # STEP 2: AI — Intent + Urgency
    ai = classify_intent_urgency(flagged)
    flagged['intent']  = ai['intent']
    flagged['urgency'] = ai['urgency']
    print(f"  STEP 2 → AI Analysis : Intent={ai['intent']}  Urgency={ai['urgency']}")

    # STEP 3: Persist to Sheets / CSV
    sheet = append_hw3_to_sheet(flagged)
    print(f"  STEP 3 → CRM Write   : {sheet.get('updatedRange', 'written')}")

    return flagged


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("\n" + "=" * 64)
    print("  HW3 — Validation, Flagging & AI Intelligence Pipeline")
    print("  Google Antigravity · Gemini 2.0 Flash Lite")
    print("=" * 64)

    results = []
    for tc in TEST_CASES:
        rec = run_pipeline(tc['label'], tc['payload'])
        results.append({
            'label':              tc['label'],
            'validation_status':  rec['validation_status'],
            'intent':             rec.get('intent',  '—'),
            'urgency':            rec.get('urgency', '—'),
        })

    print("\n\n" + "=" * 64)
    print("  SUMMARY")
    print("=" * 64)
    print(f"  {'Label':<42} {'Status':<10} {'Intent':<14} {'Urgency'}")
    print(f"  {'─' * 42} {'─' * 9} {'─' * 13} {'─' * 8}")
    for r in results:
        print(f"  {r['label']:<42} {r['validation_status']:<10} {r['intent']:<14} {r['urgency']}")

    valid_count   = sum(1 for r in results if r['validation_status'] == 'Valid')
    invalid_count = sum(1 for r in results if r['validation_status'] == 'Invalid')
    print(f"\n  Total: {len(results)} records — {valid_count} Valid, {invalid_count} Invalid")
    print("  All records written to HW3_Leads (Google Sheets or hw3_leads.csv)\n")
