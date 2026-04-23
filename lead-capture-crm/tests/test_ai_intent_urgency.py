"""
test_ai_intent_urgency.py — Unit tests for HW3 AI Intent/Urgency classification.

Tests the classify_intent_urgency function without making real Gemini API calls
by patching the generativeai module.
"""
import pytest
from unittest.mock import patch, MagicMock
from functions.ai_intent_urgency import classify_intent_urgency


VALID_RECORD = {
    "name":    "Test User",
    "email":   "test@example.com",
    "message": "We need pricing for 100 seats urgently.",
}

EMPTY_MESSAGE_RECORD = {
    "name":    "Bad Lead",
    "email":   "",
    "message": "",
}


class TestClassifyIntentUrgency:

    def test_empty_message_returns_defaults_without_api_call(self):
        """If message is empty, AI is skipped and safe defaults are returned."""
        with patch('functions.ai_intent_urgency.genai') as mock_genai:
            result = classify_intent_urgency(EMPTY_MESSAGE_RECORD)
        mock_genai.GenerativeModel.assert_not_called()
        assert result['intent']  == 'Other'
        assert result['urgency'] == 'Low'

    def test_valid_json_response_parsed(self):
        mock_response = MagicMock()
        mock_response.text = '{"intent": "Sales", "urgency": "High"}'
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch('functions.ai_intent_urgency.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            result = classify_intent_urgency(VALID_RECORD)

        assert result['intent']  == 'Sales'
        assert result['urgency'] == 'High'

    def test_json_with_markdown_fences_stripped(self):
        mock_response = MagicMock()
        mock_response.text = '```json\n{"intent": "Support", "urgency": "Medium"}\n```'
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch('functions.ai_intent_urgency.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            result = classify_intent_urgency(VALID_RECORD)

        assert result['intent']  == 'Support'
        assert result['urgency'] == 'Medium'

    def test_unknown_intent_falls_back_to_other(self):
        mock_response = MagicMock()
        mock_response.text = '{"intent": "Banana", "urgency": "High"}'
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch('functions.ai_intent_urgency.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            result = classify_intent_urgency(VALID_RECORD)

        assert result['intent'] == 'Other'

    def test_unknown_urgency_falls_back_to_medium(self):
        mock_response = MagicMock()
        mock_response.text = '{"intent": "Sales", "urgency": "Extreme"}'
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch('functions.ai_intent_urgency.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            result = classify_intent_urgency(VALID_RECORD)

        assert result['urgency'] == 'Medium'

    def test_api_error_returns_safe_defaults(self):
        with patch('functions.ai_intent_urgency.genai') as mock_genai:
            mock_genai.GenerativeModel.side_effect = Exception("API unavailable")
            result = classify_intent_urgency(VALID_RECORD)

        assert result['intent']  == 'Other'
        assert result['urgency'] == 'Medium'

    def test_malformed_json_returns_safe_defaults(self):
        mock_response = MagicMock()
        mock_response.text = 'not json at all'
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch('functions.ai_intent_urgency.genai') as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            result = classify_intent_urgency(VALID_RECORD)

        assert result['intent']  == 'Other'
        assert result['urgency'] == 'Medium'

    def test_all_valid_intent_values_accepted(self):
        for intent in ['Sales', 'Support', 'Partnership', 'Inquiry', 'Complaint', 'Other']:
            mock_response = MagicMock()
            mock_response.text = f'{{"intent": "{intent}", "urgency": "Low"}}'
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response

            with patch('functions.ai_intent_urgency.genai') as mock_genai:
                mock_genai.GenerativeModel.return_value = mock_model
                result = classify_intent_urgency(VALID_RECORD)

            assert result['intent'] == intent

    def test_all_valid_urgency_values_accepted(self):
        for urgency in ['High', 'Medium', 'Low']:
            mock_response = MagicMock()
            mock_response.text = f'{{"intent": "Sales", "urgency": "{urgency}"}}'
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response

            with patch('functions.ai_intent_urgency.genai') as mock_genai:
                mock_genai.GenerativeModel.return_value = mock_model
                result = classify_intent_urgency(VALID_RECORD)

            assert result['urgency'] == urgency
