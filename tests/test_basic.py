# tests/test_basic.py
#
# Basic tests for the triage agent.
# All tests use mock mode — no API key needed.

import pytest
from app.services import triage_ticket_mock
from app.models import TicketAnalysis


TICKET_CRITICAL = "Our marketing team sent emails to 45,000 EU customers without GDPR consent."
TICKET_MEDIUM = "An employee says their manager shared confidential salary data with unauthorized staff."


def test_critical_ticket_requires_escalation():
    """Critical ticket must always have escalation_required = True."""
    result = triage_ticket_mock(TICKET_CRITICAL)
    assert result.escalation_required is True


def test_medium_ticket_needs_more_info():
    """Vague ticket must return needs_more_info = True with a follow-up question."""
    result = triage_ticket_mock(TICKET_MEDIUM)
    assert result.needs_more_info is True
    assert result.follow_up_question is not None


def test_priority_is_valid_value():
    """Priority must always be one of the four allowed values."""
    result = triage_ticket_mock(TICKET_CRITICAL)
    assert result.priority in ["Critical", "High", "Medium", "Low"]


def test_output_has_all_required_fields():
    """All fields defined in TicketAnalysis must be present in the output."""
    result = triage_ticket_mock(TICKET_CRITICAL)
    assert isinstance(result, TicketAnalysis)
    assert result.ticket_summary
    assert result.issue_category
    assert result.suggested_team
    assert result.urgency_reason
    assert isinstance(result.required_information, list)
    assert isinstance(result.recommended_next_steps, list)
