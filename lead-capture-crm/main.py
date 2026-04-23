"""
main.py — Lead Capture HTTP Webhook (Google Antigravity Trigger)

Platform:  Google Antigravity (Agents + Workflows)
Endpoint:  POST /webhook/lead
Sequence:  Receive -> Validate -> Process -> CRM -> AI Completion -> Respond
"""

import os, json, hmac, hashlib
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from functions.process_lead import process_lead
from functions.process_contact import process_contact
from functions.sheets_connector import append_lead_to_sheet, append_contact_to_sheet, append_hw3_to_sheet
from functions.ai_completion import categorise_and_summarise
from functions.validate_lead_hw3 import validate_and_flag
from functions.ai_intent_urgency import classify_intent_urgency

load_dotenv()

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'dev_secret')


def verify_signature(payload: bytes, signature: str) -> bool:
    """HMAC-SHA256 signature verification for webhook security."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f'sha256={expected}', signature)


@app.route('/webhook/lead', methods=['POST'])
def receive_lead():
    """
    POST /webhook/lead
    Accepts JSON payload from form submission or external webhook.
    """
    # --- Signature check (skip in dev if header absent) ---
    sig_header = request.headers.get('X-Hub-Signature-256', '')
    if sig_header and not verify_signature(request.data, sig_header):
        return jsonify({'error': 'Invalid signature'}), 401

    raw = request.get_json(force=True, silent=True)
    if not raw:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    # STEP 1: Process & validate the incoming lead data
    processed = process_lead(raw)
    if processed.get('error'):
        return jsonify({'error': processed['error']}), 422

    # STEP 2: Push to Google Sheets (CRM)
    sheet_result = append_lead_to_sheet(processed)

    # STEP 3: AI categorisation + summary
    ai_result = categorise_and_summarise(processed)

    return jsonify({
        'status': 'success',
        'lead_id': processed['lead_id'],
        'crm_row': sheet_result.get('updatedRange'),
        'ai_summary': ai_result['summary'],
        'ai_category': ai_result['category'],
        'ai_priority': ai_result['priority'],
    }), 200


@app.route('/webhook/contact', methods=['POST'])
def receive_contact():
    """
    POST /webhook/contact  (HW2 — Data Input & Persistence)
    Accepts JSON payload: { name, email, message }
    Architecture: HTTP POST -> Antigravity Connector -> Google Sheets / CRM
    """
    sig_header = request.headers.get('X-Hub-Signature-256', '')
    if sig_header and not verify_signature(request.data, sig_header):
        return jsonify({'error': 'Invalid signature'}), 401

    raw = request.get_json(force=True, silent=True)
    if not raw:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    # STEP 1: Validate & process the simple contact payload
    processed = process_contact(raw)
    if processed.get('error'):
        return jsonify({'error': processed['error']}), 422

    # STEP 2: Persist to Google Sheets (CRM) — zero data loss
    sheet_result = append_contact_to_sheet(processed)

    # STEP 3: AI categorisation + summary (continuation of HW1 AI pipeline)
    ai_result = categorise_and_summarise(processed)

    return jsonify({
        'status':      'success',
        'contact_id':  processed['contact_id'],
        'name':        processed['name'],
        'email':       processed['email'],
        'message':     processed['message'],
        'crm_row':     sheet_result.get('updatedRange'),
        'ai_summary':  ai_result['summary'],
        'ai_category': ai_result['category'],
        'ai_priority': ai_result['priority'],
    }), 200


@app.route('/webhook/hw3', methods=['POST'])
def receive_hw3():
    """
    POST /webhook/hw3  (HW3 — Validation, Flagging & AI Intelligence)

    Architecture:
      Input ({name, email, message})
        → Validation (flag Valid/Invalid — never discard)
        → AI Analysis (Intent / Urgency via Gemini)
        → CRM/Sheets (full record + metadata)

    Invalid leads are saved with validation_status="Invalid"; they are NOT rejected.
    """
    sig_header = request.headers.get('X-Hub-Signature-256', '')
    if sig_header and not verify_signature(request.data, sig_header):
        return jsonify({'error': 'Invalid signature'}), 401

    raw = request.get_json(force=True, silent=True)
    if not raw:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    # STEP 1: Validate & flag — always returns a record (Valid or Invalid)
    flagged = validate_and_flag(raw)

    # STEP 2: AI classification — Intent + Urgency (skips AI if message is empty)
    ai_result = classify_intent_urgency(flagged)

    # STEP 3: Merge AI metadata into the record for persistence
    flagged['intent']  = ai_result['intent']
    flagged['urgency'] = ai_result['urgency']

    # STEP 4: Persist to Google Sheets / CSV (all records, valid and invalid)
    sheet_result = append_hw3_to_sheet(flagged)

    return jsonify({
        'status':             'success',
        'contact_id':         flagged['contact_id'],
        'name':               flagged['name'],
        'email':              flagged['email'],
        'message':            flagged['message'],
        'validation_status':  flagged['validation_status'],
        'validation_errors':  flagged['validation_errors'],
        'intent':             flagged['intent'],
        'urgency':            flagged['urgency'],
        'crm_row':            sheet_result.get('updatedRange'),
    }), 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
