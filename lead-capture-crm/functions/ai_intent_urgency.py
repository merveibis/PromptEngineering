"""
ai_intent_urgency.py — HW3: AI Classification for Intent and Urgency

Platform: Google Antigravity (Agents + Workflows)
Model:    Google Gemini 2.0 Flash Lite

Analyses the free-text 'message' field and classifies:
  - Intent:  Sales | Support | Partnership | Inquiry | Complaint | Other
  - Urgency: High | Medium | Low
"""

import os, json, re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

MODEL_NAME = 'gemini-2.0-flash-lite'

SYSTEM_PROMPT = """You are a lead intelligence classifier for a CRM system.
Given a contact form submission, classify the message into exactly two dimensions.
Return ONLY a valid JSON object with these keys:
  - intent:  one of [Sales, Support, Partnership, Inquiry, Complaint, Other]
  - urgency: one of [High, Medium, Low]

Classification guidelines:
  Sales      → buying interest, pricing questions, purchase intent, demo requests
  Support    → help requests, technical issues, bug reports, onboarding problems
  Partnership → collaboration, integration, reseller, white-label, joint venture
  Inquiry    → general information request, no clear commercial intent
  Complaint  → negative feedback, service failure, dissatisfaction
  Other      → does not fit any category above

  High   → explicit time pressure, "urgent", "ASAP", "immediately", blocked workflow
  Medium → near-term interest, "soon", "this week/month", active evaluation
  Low    → browsing, long-term plans, no deadline mentioned

Do not include any text outside the JSON object."""


def _build_prompt(record: dict) -> str:
    name    = record.get('name', 'Unknown')
    message = record.get('message', '')
    return f"""Classify this contact form submission:

Name:    {name}
Message: {message}

Return JSON only."""


def classify_intent_urgency(record: dict) -> dict:
    """
    Call Gemini and return intent + urgency classification.

    Args:
        record: processed/flagged contact record (must contain 'message' key)

    Returns:
        dict with keys: intent, urgency
        Falls back to safe defaults on any API or parse error.
    """
    message = record.get('message', '').strip()

    # If there is no message (e.g., invalid lead with missing field), skip AI call
    if not message:
        return {
            'intent':  'Other',
            'urgency': 'Low',
        }

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(_build_prompt(record))
        text = response.text.strip()

        # Strip markdown fences if present
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'```$', '', text).strip()

        result = json.loads(text)

        intent  = result.get('intent', 'Other')
        urgency = result.get('urgency', 'Medium')

        # Validate enum values
        valid_intents  = {'Sales', 'Support', 'Partnership', 'Inquiry', 'Complaint', 'Other'}
        valid_urgencies = {'High', 'Medium', 'Low'}

        return {
            'intent':  intent  if intent  in valid_intents   else 'Other',
            'urgency': urgency if urgency in valid_urgencies  else 'Medium',
        }

    except Exception as e:
        return {
            'intent':  'Other',
            'urgency': 'Medium',
        }
