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
from functions.sheets_connector import append_lead_to_sheet
from functions.ai_completion import categorise_and_summarise

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


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
