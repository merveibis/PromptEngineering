# B2B Lead Capture & Contact Form — CRM Pipeline

**Platform:** Google Antigravity (Agents + Workflows)  
**Model:** Google Gemini 2.0 Flash Lite  
**CRM:** Google Sheets API v4 (OAuth2 service account)

---

## Architecture

### HW1 — B2B Lead Pipeline
```
POST /webhook/lead
HTTP Webhook  →  process_lead()  →  append_lead_to_sheet()  →  categorise_and_summarise()  →  HTTP 200
  main.py       process_lead.py    sheets_connector.py          ai_completion.py
```

### HW2 — Contact Form Pipeline
```
POST /webhook/contact
HTTP Webhook  →  process_contact()  →  append_contact_to_sheet()  →  categorise_and_summarise()  →  HTTP 200
  main.py        process_contact.py    sheets_connector.py              ai_completion.py
```

---

## Project Structure

```
lead-capture-crm/
├── main.py                        # Flask HTTP webhook — /webhook/lead + /webhook/contact
├── demo_pipeline.py               # End-to-end demo — 20 Kaggle leads (HW1)
├── demo_hw2.py                    # End-to-end demo — contact form pipeline (HW2)
├── functions/
│   ├── process_lead.py            # HW1 — B2B lead validation, scoring, normalisation
│   ├── process_contact.py         # HW2 — {name, email, message} validation
│   ├── sheets_connector.py        # Google Sheets API / CSV fallback (HW1 + HW2)
│   └── ai_completion.py           # Gemini 2.0 Flash Lite — category, priority, summary
├── schema/
│   ├── contact_pipeline_schema.json   # JSON Schema — all pipeline data models
│   └── contact_pipeline_schema.html   # Visual pipeline architecture diagram
├── data/
│   ├── sample_leads.json          # 20 Kaggle B2B leads (HW1 input)
│   ├── crm_leads.csv              # HW1 CRM output (CSV fallback)
│   └── contacts.csv               # HW2 contact form output (CSV fallback)
├── tests/
│   ├── test_process_lead.py       # 13 tests
│   ├── test_process_contact.py    # 11 tests
│   ├── test_sheets_connector.py   # 1 test
│   └── test_ai_completion.py      # 1 test
├── workflow/
│   ├── antigravity_workflow.json  # HW1 Antigravity export
│   └── hw2_contact_workflow.json  # HW2 Antigravity export
├── .env.example
└── requirements.txt
```

---

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GEMINI_API_KEY and GOOGLE_SHEETS_SPREADSHEET_ID
python main.py
```

---

## Endpoints

### POST /webhook/lead
```bash
curl -X POST http://localhost:5000/webhook/lead \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "James",
    "last_name": "Johnson",
    "email": "james@example.com",
    "company_name": "Acme Corp",
    "industry": "marketing",
    "source": "website"
  }'
```

### POST /webhook/contact
```bash
curl -X POST http://localhost:5000/webhook/contact \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Merve İbiş",
    "email": "merveeibis@gmail.com",
    "message": "Ürününüz hakkında bilgi almak istiyorum."
  }'
```

### GET /health
```bash
curl http://localhost:5000/health
# {"status": "ok"}
```

---

## Run Tests

```bash
pytest tests/ -v   # 26 tests
```

---

## External Links

- **Google Sheets CRM:** https://docs.google.com/spreadsheets/d/1jNu4pxL61yd4tIwq09fMwQC5OQhET7CFXeowwBqV9r0/edit?usp=sharing
