# B2B Lead Capture to CRM — Automation Pipeline

**Platform:** Google Antigravity (Agents + Workflows)
**Dataset:** [Kaggle Marketing Agency B2B Leads](https://www.kaggle.com/datasets/getivan/marketing-agency-b2b-leads) — ODC PDDL (Public Domain)
**Model:** Google Gemini 2.0 Flash Lite

---

## Architecture

```
HTTP Webhook Trigger  →  process_lead()  →  CRM (Sheets / CSV)  →  Gemini AI Completion
     [Step 0]              [Step 1]              [Step 2]               [Step 3]
     main.py          process_lead.py      sheets_connector.py      ai_completion.py
```

---

## Project Structure

```
lead-capture-crm/
├── main.py                   # Flask HTTP webhook trigger
├── demo_pipeline.py          # End-to-end demo (20 Kaggle leads)
├── functions/
│   ├── process_lead.py       # Step 1 — Processing Function
│   ├── sheets_connector.py   # Step 2 — External API (CRM)
│   └── ai_completion.py      # Step 3 — AI Completion
├── data/
│   ├── sample_leads.json     # 20 real Kaggle leads
│   └── crm_leads.csv         # CSV CRM fallback
├── tests/
│   ├── test_process_lead.py
│   ├── test_sheets_connector.py
│   └── test_ai_completion.py
├── workflow/
│   └── antigravity_workflow.json
├── .env.example
├── service_account.json      # Google OAuth2 credentials (not committed)
└── requirements.txt
```

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # Add GEMINI_API_KEY and GOOGLE_SHEETS_SPREADSHEET_ID
python main.py
```

## Run Demo — 20 Kaggle Leads

```bash
python demo_pipeline.py
```

## Test Single Lead via Webhook

```bash
curl -X POST http://localhost:5000/webhook/lead \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "James",
    "last_name": "Johnson",
    "email": "info@1015multimedia.com",
    "company_name": "1015 Multimedia & Marketing",
    "industry": "marketing",
    "source": "website"
  }'
```

## Run Tests

```bash
pytest tests/ -v
```

---

## External Links

- **GitHub Repository:** https://github.com/merveibis/PromptEngineering
- **Google Sheets CRM:** https://docs.google.com/spreadsheets/d/1jNu4pxL61yd4tIwq09fMwQC5OQhET7CFXeowwBqV9r0/edit?usp=sharing

---

## Workflow

See `workflow/antigravity_workflow.json` for the Google Antigravity export.

See `workflow/hw2_contact_workflow.json` for the HW2 contact form pipeline export.
