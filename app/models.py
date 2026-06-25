from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class TicketInput(BaseModel):
    """The raw compliance ticket received from the user."""

    ticket_text: str = Field(
        ...,
        min_length=10,
        description="Raw text of the compliance incident report or legal email."
    )

class TicketAnalysis(BaseModel):
    """The structured triage result returned in the JSON response."""

    ticket_summary: str
    issue_category: str
    priority: Literal["Critical", "High", "Medium", "Low"]
    urgency_reason: str
    suggested_team: str
    required_information: List[str]
    recommended_next_steps: List[str]
    escalation_required: bool
    needs_more_info: bool
    follow_up_question: Optional[str] = None
    draft_customer_response: str
    internal_legal_note: str