from app.models import TicketAnalysis
from app.mock_data import MOCK_CRITICAL, MOCK_LOW, MOCK_MEDIUM
import json
from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME, MAX_TOKENS

def detect_mock_type(ticket_text: str) -> str:
    """
    Check keywords in the ticket text to decide which mock response to use

    Args:
        ticket_text: raw ticket text from the user

    Return:
        "critical", "medium", "low"
    """
    text_lower = ticket_text.lower()

    if "gdpr" in text_lower or "consent" in text_lower or "45,000" in text_lower:
        return "critical"
    
    if "salary" in text_lower or "confidential" in text_lower or "manager" in text_lower:
        return "medium"
    
    return "low"


def triage_ticket_mock(ticket_text: str) -> TicketAnalysis:

    """"
    Returns a pre-written triage result without calling an AI API.
    Used when USE_MOCK=true so anyone can run the project without an API key.

    Args:
        ticket_text: raw ticket text from the user

    Returns:
        A validated TicketAnalysis object
    """
    mock_type = detect_mock_type(ticket_text)

    if mock_type == "critical":
        data = MOCK_CRITICAL
    elif mock_type == "medium":
        data = MOCK_MEDIUM
    else:
        data = MOCK_LOW

    return TicketAnalysis(**data)

def build_prompt(ticket_text: str) -> str:
    """
    Builds the instruction prompt sent to the AI.
    Tells the model exactly what JSON fields to return and what they mean.

    Args:
        ticket_text: raw ticket text from the user

    Returns:
        A formatted prompt string    
    """
    return f"""
You are a senior compliance and legal analyst.
Analyze the following compliance incident ticket and return a JSON object.

TICKET:
{ticket_text}

Return ONLY a valid JSON object with exactly these fields:

{{
  "ticket_summary": "Brief 2-3 sentence summary of the incident",
  "issue_category": "Category of the issue, e.g. GDPR Data Breach / Consent Violation",
  "priority": "One of: Critical, High, Medium, Low",
  "urgency_reason": "Why this priority level was assigned",
  "suggested_team": "Which team should handle this",
  "required_information": ["list", "of", "missing", "information"],
  "recommended_next_steps": ["list", "of", "action", "steps"],
  "escalation_required": true or false,
  "needs_more_info": true or false,
  "follow_up_question": "Question to ask if needs_more_info is true, otherwise null",
  "draft_customer_response": "Professional response to send to the ticket submitter",
  "internal_legal_note": "Internal note for the legal team"
}}

Rules:
- priority must be exactly one of: Critical, High, Medium, Low
- escalation_required and needs_more_info must be boolean (true/false)
- follow_up_question must be null if needs_more_info is false
- required_information and recommended_next_steps must be lists of strings
- Return ONLY the JSON object, no extra text
- Do not invent data
    """

def triage_ticket_real(ticket_text: str) -> TicketAnalysis:
    """
    Calls the OpenAI API to analyze the ticket and returns a validated TicketAnalysis.
    Used when USE_MOCK=false in .env.

    Args:
        ticket_text: raw ticket text from the user

    Returns:
        A validated TicketAnalysis object

    Raises:
        ValueError: if the AI response cannot be parsed or validated
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = build_prompt(ticket_text)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            max_completion_tokens=MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a compliance analyst. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
        return TicketAnalysis(**data)
    
    except Exception as e:
        raise ValueError(f"AI triage failed: {str(e)}")
