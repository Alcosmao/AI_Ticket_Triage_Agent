import json
from types import SimpleNamespace
import pytest

import app.services as services
from app.services import triage_ticket_agent, lookup_regulation, run_tool
from app.config import MAX_AGENT_STEPS


def fake_tool_call_response():
    """A fake OpenAI reply where the model calls check_missing_information."""
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="check_missing_information", arguments="{}"),
    )
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def fake_final_response():
    """A fake OpenAI reply that returns the final JSON answer."""
    final_json = json.dumps({
        "ticket_summary": "Employee alleges manager shared salary data.",
        "issue_category": "HR Confidentiality Breach",
        "priority": "Medium",
        "urgency_reason": "Not enough detail to assess scope yet.",
        "suggested_team": "HR Legal",
        "required_information": ["incident date", "names involved"],
        "recommended_next_steps": ["collect missing details"],
        "escalation_required": False,
        "needs_more_info": True,
        "follow_up_question": "When did this happen and who was involved?",
        "draft_customer_response": "We need a few more details to proceed.",
        "internal_legal_note": "Insufficient information to assess severity.",
    })
    message = SimpleNamespace(content=final_json, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeOpenAI:
    """Stand-in OpenAI client that returns prepared responses and counts calls."""

    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        response = self.responses[self.call_count]
        self.call_count += 1
        return response


def make_tool_call(name, args_dict):
    """Build a fake tool_call object shaped like the real OpenAI one."""
    return SimpleNamespace(
        id="call_x",
        function=SimpleNamespace(name=name, arguments=json.dumps(args_dict)),
    )


def fake_lookup_tool_call_response(topic="gdpr_breach"):
    """A fake reply where the model calls lookup_regulation."""
    tool_call = SimpleNamespace(
        id="call_lookup",
        function=SimpleNamespace(
            name="lookup_regulation",
            arguments=json.dumps({"topic": topic}),
        ),
    )
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_agent_vague_ticket_asks_follow_up(monkeypatch):
    """Vague ticket: tool call on turn 1, final answer on turn 2."""
    responses = [fake_tool_call_response(), fake_final_response()]
    fake_client = FakeOpenAI(responses)

    monkeypatch.setattr(services, "OpenAI", lambda api_key: fake_client)

    result = triage_ticket_agent("Manager shared salary data, no details given.")

    assert result.needs_more_info is True
    assert result.follow_up_question is not None
    assert fake_client.call_count == 2


def test_agent_never_exceeds_max_steps(monkeypatch):
    """Endless tool calls must stop and raise after MAX_AGENT_STEPS."""
    responses = [fake_tool_call_response() for _ in range(MAX_AGENT_STEPS)]
    fake_client = FakeOpenAI(responses)

    monkeypatch.setattr(services, "OpenAI", lambda api_key: fake_client)

    with pytest.raises(ValueError):
        triage_ticket_agent("Vague ticket that never gets resolved.")

    assert fake_client.call_count == MAX_AGENT_STEPS


def test_lookup_regulation_known_topic():
    """A known topic returns the exact facts from the knowledge base."""
    result = lookup_regulation("gdpr_breach")
    assert result["reference"] == "GDPR Article 33"
    assert result["deadline_hours"] == 72


def test_lookup_regulation_unknown_topic():
    """An unknown topic returns a safe 'Not found' result."""
    result = lookup_regulation("not_a_real_topic")
    assert result["reference"] == "Not found"


def test_run_tool_executes_lookup_regulation():
    """run_tool dispatches lookup_regulation and returns grounded facts."""
    tool_call = make_tool_call("lookup_regulation", {"topic": "gdpr_breach"})
    result = run_tool(tool_call)
    assert result["reference"] == "GDPR Article 33"


def test_run_tool_acknowledges_check_missing_information():
    """check_missing_information is acknowledged with no computation."""
    tool_call = make_tool_call("check_missing_information", {})
    result = run_tool(tool_call)
    assert result["status"] == "acknowledged"


def test_run_tool_handles_unknown_tool():
    """An unknown tool name returns an error dict instead of crashing."""
    tool_call = make_tool_call("does_not_exist", {})
    result = run_tool(tool_call)
    assert "error" in result


def test_agent_runs_lookup_then_returns_final(monkeypatch):
    """lookup_regulation call is executed, then the loop returns the final answer."""
    responses = [fake_lookup_tool_call_response("gdpr_breach"), fake_final_response()]
    fake_client = FakeOpenAI(responses)

    monkeypatch.setattr(services, "OpenAI", lambda api_key: fake_client)

    result = triage_ticket_agent("Marketing emailed 45,000 EU customers without consent.")

    assert result.issue_category == "HR Confidentiality Breach"
    assert fake_client.call_count == 2
