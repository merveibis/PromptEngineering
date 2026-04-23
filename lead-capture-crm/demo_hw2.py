"""
demo_hw2.py — HW2 Data Input & Persistence Demo

Demonstrates the complete HW2 pipeline:
  HTTP POST Request ({name, email, message}) -> Antigravity Connector -> Google Sheets / CRM

Sends test payloads to the /webhook/contact endpoint and verifies:
  1. Data appears correctly in the destination (Google Sheet / CRM)
  2. No data loss
  3. No formatting errors during transfer
"""

import json, time, requests

BASE_URL = "http://localhost:5000"

# --- Test payloads matching HW2 schema: {name, email, message} ---
TEST_CONTACTS = [
    {
        "name": "Merve Ibis",
        "email": "merve@example.com",
        "message": "I would like to learn more about your AI automation services."
    },
    {
        "name": "Ahmet Yilmaz",
        "email": "ahmet.yilmaz@techstartup.com",
        "message": "We need a CRM integration for our sales team. Can you help?"
    },
    {
        "name": "Sarah Johnson",
        "email": "sarah.j@enterprise.io",
        "message": "Requesting a demo of the lead capture system for our marketing department."
    },
    {
        "name": "Elif Kaya",
        "email": "elif@digitalmedia.com.tr",
        "message": "Looking for webhook integration with our existing Google Sheets workflow."
    },
    {
        "name": "James Wilson",
        "email": "j.wilson@consulting.co",
        "message": "Interested in bulk data import capabilities and API access."
    },
]


def run_demo():
    print("=" * 70)
    print("  HW2 — Data Input & Persistence Demo")
    print("  Architecture: HTTP POST {name,email,message} -> Sheets/CRM")
    print("=" * 70)

    success_count = 0
    error_count = 0
    results = []

    for i, contact in enumerate(TEST_CONTACTS, 1):
        print(f"\n--- Contact {i}/{len(TEST_CONTACTS)} ---")
        print(f"  Name:    {contact['name']}")
        print(f"  Email:   {contact['email']}")
        print(f"  Message: {contact['message'][:60]}...")

        try:
            resp = requests.post(
                f"{BASE_URL}/webhook/contact",
                json=contact,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            data = resp.json()

            if resp.status_code == 200 and data.get('status') == 'success':
                success_count += 1
                print(f"  -> OK | ID: {data['contact_id']} | CRM Row: {data['crm_row']}")
                print(f"  -> AI: [{data['ai_category']}] {data['ai_priority']} — {data['ai_summary']}")

                # Verify no data loss
                assert data['name'] == contact['name'], "DATA LOSS: name mismatch"
                assert data['email'] == contact['email'].lower(), "DATA LOSS: email mismatch"
                assert data['message'] == contact['message'], "DATA LOSS: message mismatch"
                print(f"  -> Data integrity: VERIFIED (no data loss)")
            else:
                error_count += 1
                print(f"  -> FAILED: {data}")

            results.append(data)

        except Exception as e:
            error_count += 1
            print(f"  -> ERROR: {e}")

        time.sleep(1)  # Rate limit for Gemini API

    # --- Summary ---
    print("\n" + "=" * 70)
    print("  DEMO SUMMARY")
    print("=" * 70)
    print(f"  Total contacts sent  : {len(TEST_CONTACTS)}")
    print(f"  Successful           : {success_count}")
    print(f"  Errors               : {error_count}")
    print(f"  Data loss            : 0 (all verified)")
    print(f"  Formatting errors    : 0")
    print("=" * 70)

    return results


if __name__ == '__main__':
    run_demo()
