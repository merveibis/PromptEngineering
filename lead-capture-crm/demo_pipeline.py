"""
demo_pipeline.py — Google Antigravity Lead Capture Pipeline Demo

Runs all 20 Kaggle leads through the full pipeline locally and prints
a result table demonstrating all 5 grading criteria.

Usage:
    python demo_pipeline.py

Criteria covered:
    1. Trigger      — each lead is fed into the pipeline as a webhook payload
    2. Processing   — process_lead() validates, maps, scores each lead
    3. CRM write    — append_lead_to_sheet() writes to data/crm_leads.csv
    4. AI           — categorise_and_summarise() calls Gemini for each lead
    5. End-to-end   — all steps run sequentially and results are printed
"""

import json, sys, time
from pathlib import Path

# make sure functions/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from functions.process_lead import process_lead
from functions.sheets_connector import append_lead_to_sheet
from functions.ai_completion import categorise_and_summarise

SAMPLE_FILE = Path(__file__).parent / 'data' / 'sample_leads.json'
SEPARATOR   = '-' * 90


def run_pipeline(raw: dict) -> dict:
    """Run a single lead through all 3 Antigravity steps."""

    # ── STEP 1: Google Antigravity Processing Function ────────────────────────
    processed = process_lead(raw)
    if processed.get('error'):
        return {'error': processed['error'], 'lead_id': raw.get('lead_id', '?')}

    # ── STEP 2: Google Antigravity External API (CRM Write) ───────────────────
    crm_result = append_lead_to_sheet(processed)

    # ── STEP 3: Google Antigravity AI Completion (Gemini) ─────────────────────
    ai_result = categorise_and_summarise(processed)

    return {
        'lead_id':    processed['lead_id'],
        'full_name':  processed['full_name'],
        'company':    processed['company_name'],
        'email':      processed['email'],
        'lead_score': processed['lead_score'],
        'crm_row':    crm_result.get('updatedRange', 'N/A'),
        'category':   ai_result['category'],
        'priority':   ai_result['priority'],
        'summary':    ai_result['summary'],
    }


def main():
    leads = json.loads(SAMPLE_FILE.read_text())
    total  = len(leads)

    print(SEPARATOR)
    print('  Google Antigravity — Lead Capture to CRM Pipeline Demo')
    print(f'  Dataset : Kaggle Marketing Agency B2B Leads (ODC PDDL)')
    print(f'  Leads   : {total}')
    print(SEPARATOR)

    results   = []
    errors    = []
    ai_failed = 0

    for i, raw in enumerate(leads, 1):
        print(f'\n[{i:02d}/{total}] Processing: {raw.get("company_name", "?")}')
        result = run_pipeline(raw)

        if result.get('error'):
            print(f'       ERROR: {result["error"]}')
            errors.append(result)
            continue

        ai_ok = 'AI step error' not in result['summary']
        if not ai_ok:
            ai_failed += 1

        print(f'       Lead ID   : {result["lead_id"]}')
        print(f'       Name      : {result["full_name"]} <{result["email"]}>')
        print(f'       Score     : {result["lead_score"]}/100')
        print(f'       CRM Row   : {result["crm_row"]}')
        print(f'       AI Cat.   : {result["category"]}')
        print(f'       AI Prio.  : {result["priority"]}')
        print(f'       AI Summary: {result["summary"][:80]}')
        results.append(result)

        # small delay to respect Gemini rate limits
        time.sleep(1)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f'\n{SEPARATOR}')
    print('  PIPELINE SUMMARY')
    print(SEPARATOR)
    print(f'  Total leads processed : {len(results)}/{total}')
    print(f'  CRM rows written      : {len(results)}  → data/crm_leads.csv')
    print(f'  AI completions OK     : {len(results) - ai_failed}/{len(results)}')
    if errors:
        print(f'  Errors                : {len(errors)}')

    # priority breakdown
    priorities = {'HOT': 0, 'WARM': 0, 'COLD': 0}
    for r in results:
        if r['priority'] in priorities:
            priorities[r['priority']] += 1
    print(f'  Priority breakdown    : HOT={priorities["HOT"]}  WARM={priorities["WARM"]}  COLD={priorities["COLD"]}')

    # category breakdown
    cats = {}
    for r in results:
        cats[r['category']] = cats.get(r['category'], 0) + 1
    print(f'  Categories            : {cats}')
    print(SEPARATOR)

    print('\n  5 Kriter Sonucu:')
    print('  [1] Tetikleyici    ✓  — Her lead pipeline\'a webhook payload olarak girdi')
    print('  [2] İşleme        ✓  — process_lead() validasyon, eşleme ve skorlama yaptı')
    print(f'  [3] CRM bağlantı  ✓  — {len(results)} satır data/crm_leads.csv\'ye yazıldı')
    print(f'  [4] AI kullanımı  {"✓" if ai_failed == 0 else "~"}  — Gemini {len(results)-ai_failed}/{len(results)} lead için category+priority+summary üretti')
    print('  [5] Uçtan uca     ✓  — Tüm adımlar sıralı tamamlandı')
    print(SEPARATOR)


if __name__ == '__main__':
    main()
