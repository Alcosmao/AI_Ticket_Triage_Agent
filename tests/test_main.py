from fastapi.testclient import TestClient

import app.main as main
from app.main import app
from app.models import TicketAnalysis

client = TestClient(app)


def make_analysis(escalation_required: bool) -> TicketAnalysis:
    """Builds a minimal valid TicketAnalysis for tests."""
    return TicketAnalysis(
        ticket_summary="summary",
        issue_category="category",
        priority="High",
        urgency_reason="reason",
        suggested_team="team",
        required_information=["info"],
        recommended_next_steps=["step"],
        escalation_required=escalation_required,
        needs_more_info=False,
        follow_up_question=None,
        draft_customer_response="draft",
        internal_legal_note="note",
    )


def patch_real_mode(monkeypatch, escalation_required: bool) -> dict:
    """Force real mode with fake triage functions; return a counter of agent calls."""
    calls = {"agent": 0}

    monkeypatch.setattr(main, "USE_MOCK", False)
    monkeypatch.setattr(main, "save_json_output", lambda *a, **k: None)
    monkeypatch.setattr(main, "save_txt_report", lambda *a, **k: None)
    monkeypatch.setattr(
        main, "triage_ticket_real", lambda text: make_analysis(escalation_required)
    )

    def fake_agent(text):
        calls["agent"] += 1
        return make_analysis(escalation_required)

    monkeypatch.setattr(main, "triage_ticket_agent", fake_agent)
    return calls


def test_endpoint_escalates_to_agent_when_required(monkeypatch):
    """If _real flags escalation_required, the endpoint must call the agent."""
    calls = patch_real_mode(monkeypatch, escalation_required=True)

    response = client.post(
        "/triage-ticket", json={"ticket_text": "Serious GDPR breach incident."}
    )

    assert response.status_code == 200
    assert calls["agent"] == 1


def test_endpoint_skips_agent_when_not_required(monkeypatch):
    """If escalation is not required, the agent must NOT be called (cheap path)."""
    calls = patch_real_mode(monkeypatch, escalation_required=False)

    response = client.post(
        "/triage-ticket", json={"ticket_text": "Routine NDA review request."}
    )

    assert response.status_code == 200
    assert calls["agent"] == 0
