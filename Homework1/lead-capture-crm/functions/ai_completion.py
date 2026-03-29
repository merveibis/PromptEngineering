"""
ai_completion.py — Google Antigravity AI Completion Step (Step 3)

Platform: Google Antigravity (Agents + Workflows)
Model:    Google Gemini 2.0 Flash Lite

Uses Gemini 2.0 Flash Lite to:
  1. Categorise lead priority: HOT / WARM / COLD
  2. Identify industry vertical
  3. Generate a one-sentence sales rep summary
"""

import os, json, re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

MODEL_NAME = 'gemini-2.0-flash-lite'

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
