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
