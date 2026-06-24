from app.models import TicketAnalysis
from app.mock_data import MOCK_CRITICAL, MOCK_LOW, MOCK_MEDIUM
import json
from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME, MAX_TOKENS, MAX_AGENT_STEPS

CHECK_MISSING_INFO_TOOL = {
    "type": "function",
    "function": {
        "name": "check_missing_information",
        "description": (
            "Call this tool when the compliance ticket lacks the details needed "
            "to perform a proper triage. Use it to identify what is missing and "
            "to produce a follow-up question for the submitter. "
            "Check specifically for: incident date, names of people involved, "
            "supporting evidence (emails, screenshots), and any regulation reference."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "missing_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of missing pieces of information, "
                        "e.g. ['incident date', 'names of people involved']"
                    )
                },
                "follow_up_question": {
                    "type": "string",
                    "description": (
                        "A clear, professional question to send back to the ticket "
                        "submitter asking for the missing information."
                    )
                }
            },
            "required": ["missing_fields", "follow_up_question"]
        }
    }
}
AGENT_SYSTEM_PROMPT = (
    "You are a senior compliance and legal analyst. "
    "First decide whether the ticket has enough detail to triage properly. "
    "If key details are missing (incident date, names involved, supporting "
    "evidence, or regulation reference), call the check_missing_information tool. "
    "After calling the tool, return your final JSON analysis with "
    "needs_more_info set to true and follow_up_question set to your question. "
    "If the ticket is complete, return the final JSON analysis directly with "
    "needs_more_info set to false and follow_up_question null. "
    "Always respond with valid JSON only for the final answer."
)

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

def triage_ticket_agent(ticket_text: str) -> TicketAnalysis:
    """
    Runs the compliance ticket through an OpenAI agent loop.

    The model is given the check_missing_information tool. On each turn it
    either calls the tool (ticket is too vague) or returns the final JSON
    analysis. The loop runs at most MAX_AGENT_STEPS times so it can never
    loop forever.

    Args:
        ticket_text: raw ticket text from the user

    Returns:
        A validated TicketAnalysis object

    Raises:
        ValueError: if the model never returns a final answer, or the answer
                    cannot be parsed or validated.
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(ticket_text)},
        ]

        for step in range(MAX_AGENT_STEPS):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                max_completion_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
                tools=[CHECK_MISSING_INFO_TOOL],
                messages=messages,
            )
            message = response.choices[0].message

            if not message.tool_calls:
                data = json.loads(message.content)
                return TicketAnalysis(**data)

            tool_call = message.tool_calls[0]
            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": "Noted. Now return the final JSON analysis with needs_more_info=true.",
            })

        raise ValueError(f"Agent did not finish within {MAX_AGENT_STEPS} steps")
    
    except Exception as e:
        raise ValueError(f"Agent triage failed: {str(e)}")
    