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

### HW3 — Validation, Flagging & AI Intelligence Pipeline
```
POST /webhook/hw3
Input ({name, email, message})
  → Validation (Email/Format Check) — flag Valid/Invalid, never discard
  → AI Analysis (Intent / Urgency via Gemini 2.0 Flash Lite)
  → CRM/Sheets (Full Record + Metadata: validation_status, intent, urgency)
```

---

## Project Structure

```
lead-capture-crm/
├── main.py                            # Flask HTTP webhook — /webhook/lead + /webhook/contact + /webhook/hw3
├── demo_pipeline.py                   # End-to-end demo — 20 Kaggle leads (HW1)
├── demo_hw2.py                        # End-to-end demo — contact form pipeline (HW2)
├── demo_hw3.py                        # End-to-end demo — validation + AI intelligence (HW3)
├── functions/
│   ├── process_lead.py                # HW1 — B2B lead validation, scoring, normalisation
│   ├── process_contact.py             # HW2 — {name, email, message} validation
│   ├── validate_lead_hw3.py           # HW3 — flag-not-discard validation (Valid/Invalid status)
│   ├── ai_completion.py               # HW1/HW2 — Gemini: category, priority, summary
│   ├── ai_intent_urgency.py           # HW3 — Gemini: Intent (6 classes) + Urgency (High/Medium/Low)
│   └── sheets_connector.py            # Google Sheets API / CSV fallback (HW1 + HW2 + HW3)
├── schema/
│   ├── contact_pipeline_schema.json   # JSON Schema — all pipeline data models
│   └── contact_pipeline_schema.html   # Visual pipeline architecture diagram
├── data/
│   ├── sample_leads.json              # 20 Kaggle B2B leads (HW1 input)
│   ├── crm_leads.csv                  # HW1 CRM output (CSV fallback)
│   ├── contacts.csv                   # HW2 contact form output (CSV fallback)
│   └── hw3_leads.csv                  # HW3 validated+AI-classified output (CSV fallback)
├── tests/
│   ├── test_process_lead.py           # 13 tests (HW1)
│   ├── test_process_contact.py        # 11 tests (HW2)
│   ├── test_sheets_connector.py       # 1 test
│   ├── test_ai_completion.py          # 1 test (HW1/HW2)
│   ├── test_validate_lead_hw3.py      # 21 tests (HW3 validation)
│   └── test_ai_intent_urgency.py      # 9 tests (HW3 AI)
├── workflow/
│   ├── antigravity_workflow.json      # HW1 Antigravity export
│   ├── hw2_contact_workflow.json      # HW2 Antigravity export
│   └── hw3_intelligence_workflow.json # HW3 Antigravity export
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

### POST /webhook/lead  (HW1)
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

### POST /webhook/contact  (HW2)
```bash
curl -X POST http://localhost:5000/webhook/contact \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Merve İbiş",
    "email": "merveeibis@gmail.com",
    "message": "Ürününüz hakkında bilgi almak istiyorum."
  }'
```

### POST /webhook/hw3  (HW3 — Validation + AI Intelligence)
```bash
# Valid lead
curl -X POST http://localhost:5000/webhook/hw3 \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Elif Yılmaz",
    "email": "elif@techcorp.io",
    "message": "We need 50 licenses ASAP. Please send pricing immediately."
  }'

# Invalid lead (missing email) — flagged and saved, NOT rejected
curl -X POST http://localhost:5000/webhook/hw3 \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Bob Missing",
    "message": "I want to learn more."
  }'
```

**HW3 Response:**
```json
{
  "status":            "success",
  "contact_id":        "A1B2C3D4",
  "name":              "Elif Yılmaz",
  "email":             "elif@techcorp.io",
  "message":           "We need 50 licenses ASAP...",
  "validation_status": "Valid",
  "validation_errors": "",
  "intent":            "Sales",
  "urgency":           "High",
  "crm_row":           "HW3_Leads!A6"
}
```

### GET /health
```bash
curl http://localhost:5000/health
# {"status": "ok"}
```

---

## HW3 Google Sheets Schema (HW3_Leads tab)

| Column             | Description                                  |
|--------------------|----------------------------------------------|
| Contact Id         | Auto-generated 8-char UUID fragment          |
| Created At         | ISO 8601 UTC timestamp                       |
| Name               | Raw name (preserved as submitted)            |
| Email              | Normalised to lowercase                      |
| Message            | Raw message text                             |
| Validation Status  | `Valid` or `Invalid`                         |
| Validation Errors  | Semicolon-separated list of errors (or empty)|
| Intent             | Sales / Support / Partnership / Inquiry / Complaint / Other |
| Urgency            | High / Medium / Low                          |

---

## Run Tests

```bash
pytest tests/ -v   # 56 tests total
```

---

## External Links

- **Google Sheets CRM:** https://docs.google.com/spreadsheets/d/1jNu4pxL61yd4tIwq09fMwQC5OQhET7CFXeowwBqV9r0/edit?usp=sharing
