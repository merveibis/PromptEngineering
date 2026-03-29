"""
process_lead.py — Lead Data Processing & Mapping Function

Maps raw webhook payload -> standardised CRM schema.
Data source: Kaggle Marketing Agency B2B Leads Dataset field structure.
URL: https://www.kaggle.com/datasets/getivan/marketing-agency-b2b-leads
License: ODC Public Domain Dedication and Licence (PDDL)
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
