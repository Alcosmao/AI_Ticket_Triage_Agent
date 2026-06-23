from app.models import TicketAnalysis
from app.mock_data import MOCK_CRITICAL, MOCK_LOW, MOCK_MEDIUM

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
