from app.models import TicketAnalysis
from app.mock_data import MOCK_CRITICAL, MOCK_LOW, MOCK_MEDIUM
import json
from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL_NAME, MAX_TOKENS, MAX_AGENT_STEPS
from app.knowledge_base import REGULATIONS

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

LOOKUP_REGULATION_TOOL = {
    "type": "function",
    "function": {
        "name": "lookup_regulation",
        "description": (
            "Look up the exact reference, deadline, and responsible authority "
            "for a compliance regulation from the controlled knowledge base. "
            "Call this before citing any regulation, so the citation is accurate "
            "instead of guessed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": [
                        "gdpr_breach",
                        "gdpr_consent",
                        "hr_confidentiality",
                        "nda_review",
                    ],
                    "description": "The regulation topic to look up.",
                }
            },
            "required": ["topic"],
        },
    },
}

AGENT_SYSTEM_PROMPT = (
    "You are a senior compliance and legal analyst. "
    "First decide whether the ticket has enough detail to triage properly. "
    "If key details are missing (incident date, names involved, supporting "
    "evidence, or regulation reference), call the check_missing_information tool. "
    "After calling the tool, return your final JSON analysis with "
    "needs_more_info set to true and follow_up_question set to your question. "
    "Before citing any regulation, call the lookup_regulation tool to get the "
    "exact reference, deadline, and authority — never guess legal citations. "
    "If the ticket is complete, return the final JSON analysis directly with "
    "needs_more_info set to false and follow_up_question null. "
    "Always respond with valid JSON only for the final answer."
)


def detect_mock_type(ticket_text: str) -> str:
    """Pick which mock response fits the ticket text by keyword."""
    text_lower = ticket_text.lower()

    if "gdpr" in text_lower or "consent" in text_lower or "45,000" in text_lower:
        return "critical"

    if "salary" in text_lower or "confidential" in text_lower or "manager" in text_lower:
        return "medium"

    return "low"


def triage_ticket_mock(ticket_text: str) -> TicketAnalysis:
    """Return a pre-written triage result without calling an API (USE_MOCK=true)."""
    mock_type = detect_mock_type(ticket_text)

    if mock_type == "critical":
        data = MOCK_CRITICAL
    elif mock_type == "medium":
        data = MOCK_MEDIUM
    else:
        data = MOCK_LOW

    return TicketAnalysis(**data)


def build_prompt(ticket_text: str) -> str:
    """Build the instruction prompt listing the JSON fields the model must return."""
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
    """One-shot OpenAI call returning a validated TicketAnalysis (USE_MOCK=false)."""
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
    """Agent loop: give the model its tools, run them, return the final analysis."""
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
                tools=[CHECK_MISSING_INFO_TOOL, LOOKUP_REGULATION_TOOL],
                messages=messages,
            )
            message = response.choices[0].message

            if not message.tool_calls:
                data = json.loads(message.content)
                return TicketAnalysis(**data)

            messages.append(message)
            for tool_call in message.tool_calls:
                result = run_tool(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })

        raise ValueError(f"Agent did not finish within {MAX_AGENT_STEPS} steps")

    except Exception as e:
        raise ValueError(f"Agent triage failed: {str(e)}")


def lookup_regulation(topic: str) -> dict:
    """Return regulation facts for a topic from the knowledge base, or a safe 'not found'."""
    regulation = REGULATIONS.get(topic)

    if regulation is None:
        return {
            "reference": "Not found",
            "deadline_hours": None,
            "authority": "Unknown — manual legal review required",
            "note": f"No regulation found for topic '{topic}'. Escalate to legal team.",
        }

    return regulation


def run_tool(tool_call) -> dict:
    """Dispatch a tool call to the matching Python function and return its result."""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    if name == "lookup_regulation":
        return lookup_regulation(args["topic"])
    if name == "check_missing_information":
        return {"status": "acknowledged"}

    return {"error": f"Unknown tool: {name}"}
