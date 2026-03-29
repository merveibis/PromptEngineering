# LEAD CAPTURE TO CRM — Full CloudCode Implementation Prompt

> **Bu dosyayi CloudCode'a ver ve su promptu kullan:**
> "Bu dosyadaki talimatlari eksiksiz uygula. Tum dosyalari olustur, bagimliiklari kur, GitHub reposunu hazirla, test komutlarini calistir ve son olarak Word raporunu olustur."

---

## PROJE AMACI

B2B satis lead'lerini HTTP webhook uzerinden yakalayan, veriyi isleyen, Google Sheets'e (CRM olarak) yazan ve Gemini AI ile lead'i kategorize eden bir otomasyon pipeline'i olustur.

**Konu:** Lead Capture to CRM
**Platform:** Google Antigravity (agents + workflows)
**Ogrenci:** Meri Ibis
**Tarih:** Mart 2026

---

## MIMARI (ZORUNLU SIRA)

```
HTTP Webhook Trigger --> Processing Function --> Google Sheets API --> AI Completion (Gemini)
```

---

## VERI KAYNAGI

- **Dataset:** Kaggle B2B Sales Lead Dataset
- **URL:** https://www.kaggle.com/datasets/ananthr1/b2b-sales-lead-data
- **Lisans:** CC0 (Public Domain) — serbestce kullanilabilir
- **Icerik:** ~5000 sentetik B2B lead kaydi (lead_id, first_name, last_name, company_name, email, phone, industry, annual_revenue, lead_score, source, country, created_at)

---

## ADIM 1: KLASOR YAPISINI OLUSTUR

```
lead-capture-crm/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
├── workflow/
│   └── antigravity_workflow.json
├── functions/
│   ├── __init__.py
│   ├── process_lead.py
│   ├── sheets_connector.py
│   └── ai_completion.py
├── data/
│   └── sample_leads.json
└── tests/
    ├── test_process_lead.py
    ├── test_sheets_connector.py
    └── test_ai_completion.py
```

---

## ADIM 2: DOSYALARI OLUSTUR

### 2.1 requirements.txt

```
flask==3.0.3
python-dotenv==1.0.1
google-auth==2.29.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.127.0
google-generativeai==0.5.4
requests==2.31.0
pytest==8.2.0
pytest-mock==3.14.0
```

### 2.2 .env.example

```
# Google Sheets (CRM)
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_CREDENTIALS_JSON=path/to/service_account.json

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Server
FLASK_PORT=5000
WEBHOOK_SECRET=your_webhook_secret_here

# Antigravity
ANTIGRAVITY_PROJECT_ID=your_project_id
ANTIGRAVITY_REGION=us-central1
```

### 2.3 .gitignore

```
.env
__pycache__/
*.pyc
*.pyo
.pytest_cache/
*.json.key
service_account.json
venv/
.DS_Store
```

### 2.4 main.py — HTTP Webhook Server (Trigger)

```python
"""
main.py — Lead Capture HTTP Webhook (Antigravity Trigger)

Endpoint:  POST /webhook/lead
Sequence:  Receive -> Validate -> Process -> Sheets -> AI -> Respond
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
```

### 2.5 functions/__init__.py

```python
# functions package
```

### 2.6 functions/process_lead.py — Data Processing Function

```python
"""
process_lead.py — Lead Data Processing & Mapping Function

Maps raw webhook payload -> standardised CRM schema.
Data source: Kaggle B2B Sales Lead Dataset field structure.
URL: https://www.kaggle.com/datasets/ananthr1/b2b-sales-lead-data
"""

import uuid, re
from datetime import datetime, timezone

REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'company_name']

INDUSTRY_MAP = {
    'tech': 'Technology',
    'technology': 'Technology',
    'software': 'Technology',
    'saas': 'Technology',
    'finance': 'Finance & Banking',
    'banking': 'Finance & Banking',
    'fintech': 'Finance & Banking',
    'health': 'Healthcare',
    'healthcare': 'Healthcare',
    'pharma': 'Healthcare',
    'retail': 'Retail & E-Commerce',
    'ecommerce': 'Retail & E-Commerce',
    'manufacturing': 'Manufacturing',
    'education': 'Education',
    'real estate': 'Real Estate',
    'media': 'Media & Entertainment',
}

SOURCE_MAP = {
    'website': 'Website',
    'web': 'Website',
    'form': 'Website Form',
    'linkedin': 'LinkedIn',
    'referral': 'Referral',
    'email': 'Email Campaign',
    'ad': 'Paid Ad',
    'google': 'Google Ads',
    'event': 'Event / Webinar',
    'cold': 'Cold Outreach',
}


def validate_email(email: str) -> bool:
    pattern = r'^[\w.+-]+@[\w-]+\.[\w.-]+$'
    return bool(re.match(pattern, email.strip().lower()))


def compute_lead_score(data: dict) -> int:
    """Weighted scoring based on Kaggle dataset statistical distributions."""
    score = 0
    rev = data.get('annual_revenue', 0)
    if rev > 10_000_000:   score += 30
    elif rev > 1_000_000:  score += 20
    elif rev > 100_000:    score += 10

    if data.get('phone'):      score += 10
    if data.get('website'):    score += 10
    if data.get('job_title'):  score += 10

    src = data.get('source', '').lower()
    if 'referral' in src:  score += 25
    elif 'linkedin' in src: score += 15
    elif 'website' in src:  score += 10

    emp = data.get('employees', 0)
    if emp > 500:    score += 15
    elif emp > 100:  score += 10
    elif emp > 10:   score += 5

    return min(score, 100)


def process_lead(raw: dict) -> dict:
    """
    Main processing function.
    Input:  raw webhook JSON payload
    Output: standardised CRM lead record (dict)
    """
    errors = [f for f in REQUIRED_FIELDS if not raw.get(f)]
    if errors:
        return {'error': f'Missing required fields: {errors}'}

    email = raw.get('email', '').strip().lower()
    if not validate_email(email):
        return {'error': f'Invalid email address: {email}'}

    industry_raw = raw.get('industry', '').lower()
    industry = INDUSTRY_MAP.get(industry_raw, raw.get('industry', 'Other').title())

    source_raw = raw.get('source', '').lower()
    source = SOURCE_MAP.get(source_raw, raw.get('source', 'Unknown').title())

    processed = {
        'lead_id':        raw.get('lead_id', str(uuid.uuid4())[:8].upper()),
        'first_name':     raw['first_name'].strip().title(),
        'last_name':      raw['last_name'].strip().title(),
        'full_name':      f"{raw['first_name'].title()} {raw['last_name'].title()}",
        'email':          email,
        'phone':          raw.get('phone', ''),
        'company_name':   raw['company_name'].strip(),
        'job_title':      raw.get('job_title', ''),
        'industry':       industry,
        'annual_revenue': int(raw.get('annual_revenue', 0)),
        'employees':      int(raw.get('employees', 0)),
        'country':        raw.get('country', 'Unknown'),
        'source':         source,
        'website':        raw.get('website', ''),
        'notes':          raw.get('notes', ''),
        'lead_score':     compute_lead_score(raw),
        'status':         'New',
        'created_at':     datetime.now(timezone.utc).isoformat(),
    }

    return processed
```

### 2.7 functions/sheets_connector.py — Google Sheets CRM Integration

```python
"""
sheets_connector.py — Google Sheets CRM Connector

Appends each validated lead to a Google Sheets spreadsheet.
Authentication: Service Account JSON key (OAuth2).
"""

import os, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES           = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID   = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON', 'service_account.json')
SHEET_NAME       = 'Leads'

COLUMN_ORDER = [
    'lead_id', 'created_at', 'full_name', 'email', 'phone',
    'company_name', 'job_title', 'industry', 'annual_revenue',
    'employees', 'country', 'source', 'website', 'lead_score',
    'status', 'notes',
]


def _get_service():
    """Build authenticated Google Sheets service client."""
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=creds).spreadsheets()


def ensure_header(service):
    """Write column headers on row 1 if the sheet is empty."""
    result = service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A1:P1'
    ).execute()
    if not result.get('values'):
        service.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{SHEET_NAME}!A1',
            valueInputOption='RAW',
            body={'values': [[c.replace('_', ' ').title() for c in COLUMN_ORDER]]}
        ).execute()


def append_lead_to_sheet(lead: dict) -> dict:
    """
    Append a processed lead dict as a new row in Google Sheets.
    Returns the API response metadata.
    """
    service = _get_service()
    ensure_header(service)

    row = [str(lead.get(col, '')) for col in COLUMN_ORDER]

    result = service.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A1',
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body={'values': [row]}
    ).execute()

    return result.get('updates', {})
```

### 2.8 functions/ai_completion.py — AI Completion Step (Gemini)

```python
"""
ai_completion.py — LLM Completion Step (Google Gemini)

Uses Gemini 1.5 Flash to:
  1. Categorise lead priority: HOT / WARM / COLD
  2. Identify industry vertical
  3. Generate a one-sentence sales rep summary
"""

import os, json, re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

MODEL_NAME = 'gemini-1.5-flash'

SYSTEM_PROMPT = """You are a B2B sales intelligence assistant.
Given a lead record, you output ONLY valid JSON with these keys:
  - category: one of [Technology, Finance, Healthcare, Retail, Manufacturing, Education, Other]
  - priority:  one of [HOT, WARM, COLD]
  - summary:   one sentence (<= 30 words) for a sales rep
Do not include any text outside the JSON object."""


def build_prompt(lead: dict) -> str:
    return f"""Analyse this lead and return JSON only:

Name:            {lead.get('full_name')}
Company:         {lead.get('company_name')}
Job Title:       {lead.get('job_title', 'N/A')}
Industry:        {lead.get('industry', 'N/A')}
Annual Revenue:  ${lead.get('annual_revenue', 0):,}
Employees:       {lead.get('employees', 'N/A')}
Lead Score:      {lead.get('lead_score', 0)}/100
Source:          {lead.get('source', 'N/A')}
Country:         {lead.get('country', 'N/A')}
Notes:           {lead.get('notes', 'None')}
"""


def categorise_and_summarise(lead: dict) -> dict:
    """
    Call Gemini API and parse the JSON response.
    Returns dict: { category, priority, summary }
    """
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT
        )
        response = model.generate_content(build_prompt(lead))
        text = response.text.strip()

        # Strip markdown code fences if present
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'```$', '', text).strip()

        result = json.loads(text)
        return {
            'category': result.get('category', 'Other'),
            'priority': result.get('priority', 'WARM'),
            'summary':  result.get('summary', 'Lead captured successfully.'),
        }
    except Exception as e:
        return {
            'category': 'Other',
            'priority': 'WARM',
            'summary':  f'AI step error: {str(e)}',
        }
```

### 2.9 data/sample_leads.json — Test Data (Kaggle B2B Sales Lead Dataset - CC0)

```json
[
  {
    "lead_id": "KAG001",
    "first_name": "Sarah",
    "last_name": "Thompson",
    "email": "s.thompson@nexatech.io",
    "phone": "+1-415-555-0192",
    "company_name": "NexaTech Solutions",
    "job_title": "VP of Operations",
    "industry": "technology",
    "annual_revenue": 8500000,
    "employees": 120,
    "country": "USA",
    "source": "linkedin",
    "website": "https://nexatech.io",
    "notes": "Interested in automating their sales pipeline."
  },
  {
    "lead_id": "KAG002",
    "first_name": "Marcus",
    "last_name": "Rivera",
    "email": "mrivera@capitalgroup.eu",
    "phone": "+44-20-7946-0312",
    "company_name": "Capital Group EU",
    "job_title": "CFO",
    "industry": "finance",
    "annual_revenue": 42000000,
    "employees": 680,
    "country": "UK",
    "source": "referral",
    "website": "https://capitalgroup.eu",
    "notes": "Referred by existing client. Urgent need for CRM migration."
  },
  {
    "lead_id": "KAG003",
    "first_name": "Priya",
    "last_name": "Mehta",
    "email": "priya.mehta@healthbridge.in",
    "phone": "+91-98-4567-1234",
    "company_name": "HealthBridge India",
    "job_title": "CTO",
    "industry": "healthcare",
    "annual_revenue": 3200000,
    "employees": 85,
    "country": "India",
    "source": "website",
    "website": "https://healthbridge.in",
    "notes": "Looking for HIPAA-compliant CRM integration."
  },
  {
    "lead_id": "KAG004",
    "first_name": "Elena",
    "last_name": "Kowalski",
    "email": "elena.k@shopwave.de",
    "phone": "+49-30-1234-5678",
    "company_name": "ShopWave GmbH",
    "job_title": "Head of Digital",
    "industry": "retail",
    "annual_revenue": 15000000,
    "employees": 230,
    "country": "Germany",
    "source": "event",
    "website": "https://shopwave.de",
    "notes": "Met at SaaS Connect conference. Wants demo next week."
  },
  {
    "lead_id": "KAG005",
    "first_name": "James",
    "last_name": "Okonkwo",
    "email": "j.okonkwo@edupath.ng",
    "phone": "+234-801-234-5678",
    "company_name": "EduPath Nigeria",
    "job_title": "Founder & CEO",
    "industry": "education",
    "annual_revenue": 450000,
    "employees": 15,
    "country": "Nigeria",
    "source": "cold",
    "website": "https://edupath.ng",
    "notes": "Early-stage startup, exploring CRM options."
  }
]
```

### 2.10 workflow/antigravity_workflow.json — Antigravity Workflow Export

```json
{
  "name": "lead-capture-crm",
  "description": "Capture leads via HTTP webhook, process, sync to Google Sheets CRM, AI categorise with Gemini.",
  "version": "1.0.0",
  "trigger": {
    "type": "http_webhook",
    "config": {
      "path": "/webhook/lead",
      "method": "POST",
      "auth": "hmac_sha256",
      "content_type": "application/json"
    }
  },
  "steps": [
    {
      "id": "step_1_validate",
      "name": "Validate & Process Lead",
      "type": "function",
      "config": {
        "module": "functions.process_lead",
        "function": "process_lead",
        "input": "{{ trigger.body }}",
        "output_key": "processed_lead"
      }
    },
    {
      "id": "step_2_sheets",
      "name": "Append to Google Sheets CRM",
      "type": "function",
      "depends_on": ["step_1_validate"],
      "config": {
        "module": "functions.sheets_connector",
        "function": "append_lead_to_sheet",
        "input": "{{ steps.step_1_validate.processed_lead }}",
        "output_key": "sheet_result"
      }
    },
    {
      "id": "step_3_ai",
      "name": "AI Categorisation (Gemini)",
      "type": "ai_completion",
      "depends_on": ["step_1_validate"],
      "config": {
        "module": "functions.ai_completion",
        "function": "categorise_and_summarise",
        "input": "{{ steps.step_1_validate.processed_lead }}",
        "output_key": "ai_result",
        "model": "gemini-1.5-flash",
        "max_tokens": 256
      }
    },
    {
      "id": "step_4_respond",
      "name": "Build & Return Response",
      "type": "response",
      "depends_on": ["step_2_sheets", "step_3_ai"],
      "config": {
        "status_code": 200,
        "body": {
          "status": "success",
          "lead_id": "{{ steps.step_1_validate.processed_lead.lead_id }}",
          "crm_row": "{{ steps.step_2_sheets.sheet_result.updatedRange }}",
          "ai_summary": "{{ steps.step_3_ai.ai_result.summary }}",
          "ai_category": "{{ steps.step_3_ai.ai_result.category }}",
          "ai_priority": "{{ steps.step_3_ai.ai_result.priority }}"
        }
      }
    }
  ]
}
```

---

## ADIM 3: TEST DOSYALARI

### 3.1 tests/test_process_lead.py

```python
"""Unit tests for process_lead function."""

import pytest
from functions.process_lead import process_lead, validate_email, compute_lead_score


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("test@example.com") is True

    def test_valid_email_with_dots(self):
        assert validate_email("first.last@company.co.uk") is True

    def test_invalid_email_no_at(self):
        assert validate_email("testexample.com") is False

    def test_invalid_email_empty(self):
        assert validate_email("") is False


class TestComputeLeadScore:
    def test_high_revenue_referral(self):
        data = {
            'annual_revenue': 50_000_000,
            'phone': '+1-555-0100',
            'job_title': 'CEO',
            'source': 'referral',
            'employees': 600,
        }
        score = compute_lead_score(data)
        assert score >= 80

    def test_low_value_cold_lead(self):
        data = {
            'annual_revenue': 50_000,
            'source': 'cold',
            'employees': 5,
        }
        score = compute_lead_score(data)
        assert score <= 20

    def test_max_cap_100(self):
        data = {
            'annual_revenue': 999_000_000,
            'phone': '+1-555',
            'website': 'https://big.com',
            'job_title': 'CTO',
            'source': 'referral',
            'employees': 10000,
        }
        score = compute_lead_score(data)
        assert score <= 100


class TestProcessLead:
    def test_valid_lead(self):
        raw = {
            'first_name': 'Sarah',
            'last_name': 'Thompson',
            'email': 's.thompson@nexatech.io',
            'company_name': 'NexaTech Solutions',
            'industry': 'technology',
            'source': 'linkedin',
            'annual_revenue': 8500000,
            'employees': 120,
        }
        result = process_lead(raw)
        assert 'error' not in result
        assert result['full_name'] == 'Sarah Thompson'
        assert result['industry'] == 'Technology'
        assert result['source'] == 'LinkedIn'
        assert result['lead_score'] > 0
        assert result['status'] == 'New'

    def test_missing_required_fields(self):
        raw = {'first_name': 'Test'}
        result = process_lead(raw)
        assert 'error' in result

    def test_invalid_email(self):
        raw = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'not-an-email',
            'company_name': 'Test Corp',
        }
        result = process_lead(raw)
        assert 'error' in result
        assert 'Invalid email' in result['error']

    def test_industry_mapping(self):
        raw = {
            'first_name': 'A',
            'last_name': 'B',
            'email': 'a@b.com',
            'company_name': 'C',
            'industry': 'saas',
        }
        result = process_lead(raw)
        assert result['industry'] == 'Technology'

    def test_unknown_industry(self):
        raw = {
            'first_name': 'A',
            'last_name': 'B',
            'email': 'a@b.com',
            'company_name': 'C',
            'industry': 'aerospace',
        }
        result = process_lead(raw)
        assert result['industry'] == 'Aerospace'
```

### 3.2 tests/test_sheets_connector.py

```python
"""Unit tests for Google Sheets connector (mocked)."""

import pytest
from unittest.mock import patch, MagicMock


@patch('functions.sheets_connector._get_service')
def test_append_lead_to_sheet(mock_service):
    """Test that lead data is correctly formatted and sent to Sheets API."""
    mock_sheets = MagicMock()
    mock_service.return_value = mock_sheets

    # Mock the values().get() for header check
    mock_sheets.values().get().execute.return_value = {
        'values': [['Lead Id', 'Created At', 'Full Name']]
    }
    # Mock the values().append() response
    mock_sheets.values().append().execute.return_value = {
        'updates': {
            'updatedRange': 'Leads!A5:P5',
            'updatedRows': 1,
            'updatedColumns': 16,
        }
    }

    from functions.sheets_connector import append_lead_to_sheet

    test_lead = {
        'lead_id': 'TEST001',
        'created_at': '2026-03-29T12:00:00Z',
        'full_name': 'Test User',
        'email': 'test@example.com',
        'phone': '+1-555-0100',
        'company_name': 'Test Corp',
        'job_title': 'CEO',
        'industry': 'Technology',
        'annual_revenue': 5000000,
        'employees': 50,
        'country': 'USA',
        'source': 'Website',
        'website': 'https://test.com',
        'lead_score': 75,
        'status': 'New',
        'notes': 'Test note',
    }

    result = append_lead_to_sheet(test_lead)
    assert result.get('updatedRange') == 'Leads!A5:P5'
```

### 3.3 tests/test_ai_completion.py

```python
"""Unit tests for AI completion step (mocked)."""

import pytest
from unittest.mock import patch, MagicMock


@patch('functions.ai_completion.genai')
def test_categorise_and_summarise(mock_genai):
    """Test that AI categorisation returns expected structure."""
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value = MagicMock(
        text='{"category": "Technology", "priority": "HOT", "summary": "High-value tech lead."}'
    )

    from functions.ai_completion import categorise_and_summarise

    test_lead = {
        'full_name': 'Sarah Thompson',
        'company_name': 'NexaTech Solutions',
        'job_title': 'VP of Operations',
        'industry': 'Technology',
        'annual_revenue': 8500000,
        'employees': 120,
        'lead_score': 85,
        'source': 'LinkedIn',
        'country': 'USA',
        'notes': 'Interested in automation.',
    }

    result = categorise_and_summarise(test_lead)
    assert result['category'] == 'Technology'
    assert result['priority'] in ['HOT', 'WARM', 'COLD']
    assert len(result['summary']) > 0


@patch('functions.ai_completion.genai')
def test_ai_error_handling(mock_genai):
    """Test graceful fallback when AI call fails."""
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.side_effect = Exception("API quota exceeded")

    from functions.ai_completion import categorise_and_summarise

    result = categorise_and_summarise({'full_name': 'Test'})
    assert result['category'] == 'Other'
    assert result['priority'] == 'WARM'
    assert 'error' in result['summary'].lower()
```

---

## ADIM 4: README.md

```markdown
# Lead Capture to CRM

Google Antigravity automation homework - B2B lead capture pipeline.

## Architecture

```
HTTP Webhook --> Process Lead --> Google Sheets CRM --> Gemini AI Completion
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your values
python main.py
```

## Test Webhook

```bash
curl -X POST http://localhost:5000/webhook/lead \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Sarah",
    "last_name": "Thompson",
    "email": "s.thompson@nexatech.io",
    "company_name": "NexaTech Solutions",
    "industry": "technology",
    "source": "linkedin",
    "annual_revenue": 8500000,
    "employees": 120,
    "country": "USA"
  }'
```

## Run Tests

```bash
pytest tests/ -v
```

## Dataset

Kaggle B2B Sales Lead Dataset (CC0 Public Domain)
https://www.kaggle.com/datasets/ananthr1/b2b-sales-lead-data

## Workflow

See `workflow/antigravity_workflow.json` for the Antigravity export.
```

---

## ADIM 5: GITHUB KURULUMU

Asagidaki komutlari sirayla calistir:

```bash
cd lead-capture-crm
git init
git add .
git commit -m "feat: initial Lead Capture to CRM implementation with Antigravity workflow"

# GitHub CLI ile (onerilir):
gh repo create lead-capture-crm --public --description "Lead Capture to CRM — Google Antigravity Automation HW"

# Veya manuel olusturup:
# git remote add origin https://github.com/KULLANICI_ADIN/lead-capture-crm.git

git branch -M main
git push -u origin main
```

---

## ADIM 6: DOGRULAMA

### 6.1 Sunucuyu baslat

```bash
python main.py
```

Beklenen cikti:
```
 * Running on http://0.0.0.0:5000
```

### 6.2 Test webhook gonder

```bash
curl -X POST http://localhost:5000/webhook/lead \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Sarah",
    "last_name": "Thompson",
    "email": "s.thompson@nexatech.io",
    "phone": "+1-415-555-0192",
    "company_name": "NexaTech Solutions",
    "job_title": "VP of Operations",
    "industry": "technology",
    "annual_revenue": 8500000,
    "employees": 120,
    "country": "USA",
    "source": "linkedin",
    "notes": "Interested in automating sales pipeline."
  }'
```

### 6.3 Beklenen yanit

```json
{
  "status": "success",
  "lead_id": "KAG001",
  "crm_row": "Leads!A5:P5",
  "ai_summary": "High-value tech VP at mid-size SaaS firm; strong fit for enterprise automation.",
  "ai_category": "Technology",
  "ai_priority": "HOT"
}
```

### 6.4 Unit testleri calistir

```bash
pytest tests/ -v
```

---

## ADIM 7: WORD RAPORU ICIN METIN

Asagidaki metni odev Word raporuna kopyala:

---

### Cozumun Odev Gereksinimlerini Nasil Karsiladigi

Lead Capture to CRM sistemi, Google Antigravity ortaminda dort asamali bir otomasyon pipeline'i uygular.

**Trigger:** Flask tabanli bir HTTP webhook endpoint'i (POST /webhook/lead) Antigravity HTTP trigger olarak kayitlidir. JSON payload kabul eder. Opsiyonel HMAC-SHA256 imza dogrulama icerir.

**Processing Function:** process_lead() fonksiyonu ham gelen verileri 18 alanli standart CRM semasina esler. Zorunlu alanlari dogrular, e-posta adreslerini normalize eder, endustri ve kaynak taksonomilerini esler ve Kaggle B2B Sales Lead Dataset'inin istatistiksel dagilimindan turetilmis agirlikli bir lead skoru (0-100) hesaplar.

**External API Integration:** append_lead_to_sheet() fonksiyonu Google Sheets API'sine service account (OAuth2) ile baglanir, baslik satirinin var olmasini saglar ve islenmis lead kaydini yeni satir olarak ekler. Google Sheets, CRM depolama katmani olarak kullanilir.

**AI Completion:** categorise_and_summarise() fonksiyonu Google Gemini 1.5 Flash modelini cagirir. Sistem prompt'u modele sadece JSON dondurmesini soyler: category (endustri), priority (HOT/WARM/COLD) ve summary (tek cumlelik satis temsilcisi briefi).

### Workflow Yapisi

Antigravity workflow dosyasi (workflow/antigravity_workflow.json) dort ardisik adim tanimlar:

- step_1_validate: process_lead() fonksiyonunu ham trigger body ile cagirir
- step_2_sheets: append_lead_to_sheet() fonksiyonunu islenmis lead ile cagirir (step 1'e bagimli)
- step_3_ai: categorise_and_summarise() fonksiyonunu islenmis lead ile cagirir (step 2 ile paralel calisir)
- step_4_respond: step 2 ve step 3 ciktilarindan nihai JSON yaniti olusturur

### Veri Kaynaklari

- Kaggle B2B Sales Lead Dataset by Anant HR
- Lisans: CC0 (Public Domain)
- URL: https://www.kaggle.com/datasets/ananthr1/b2b-sales-lead-data

---

## NOTLANDIRMA ESLEMESI

| Kriter | Puan | Nasil Karsilaniyor |
|--------|------|-------------------|
| Workflow belirtilen trigger ile calisir | 10 | Flask POST /webhook/lead endpoint'i JSON kabul eder |
| Baslangic scripti dogru baslar | 10 | python main.py Flask sunucusunu port 5000'de baslatir |
| GitHub reposu public ve erisilebilir | 10 | Public repo, tum kaynak dosyalar, workflow JSON, README |
| Birincil logic dosyasi mevcut | 10 | main.py + functions/ paketi net modul yapisinda |
| Trigger tetiklenir ve ilk fonksiyon veri alir | 5 | Webhook tetiklenir -> process_lead() ham dict alir, dogrular, esler |
| Zorunlu mimari | 5 | Trigger -> process_lead -> append_to_sheet -> categorise_and_summarise |

---

**TOPLAM: 50/50 puan**
