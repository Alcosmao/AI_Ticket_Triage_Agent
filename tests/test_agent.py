import json
from types import SimpleNamespace
import pytest

import app.services as services
from app.services import triage_ticket_agent
from app.config import MAX_AGENT_STEPS


def fake_tool_call_response():
    """
    A fake OpenAI reply where the model CALLS the tool (ticket too vague).
    Mimics the shape: response.choices[0].message.tool_calls[0].id
    """
    tool_call = SimpleNamespace(id="call_1")
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def fake_final_response():
    """
    A fake OpenAI reply where the model returns the FINAL JSON answer.
    Mimics the shape: response.choices[0].message.content (a JSON string)
    """
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
    """
    Stands in for the real OpenAI client during tests.
    It returns prepared responses one by one and counts how many times
    .chat.completions.create() was called.
    """

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
    
def test_agent_vague_ticket_asks_follow_up(monkeypatch):
    """
    A vague ticket should make the model call the tool on turn 1,
    then return a final answer on turn 2 with needs_more_info=True.
    """
    responses = [fake_tool_call_response(), fake_final_response()]
    fake_client = FakeOpenAI(responses)

    # Replace the real OpenAI client with our fake one, only for this test.
    monkeypatch.setattr(services, "OpenAI", lambda api_key: fake_client)

    result = triage_ticket_agent("Manager shared salary data, no details given.")

    assert result.needs_more_info is True
    assert result.follow_up_question is not None
    assert fake_client.call_count == 2


def test_agent_never_exceeds_max_steps(monkeypatch):
    """
    If the model keeps calling the tool forever, the loop must stop
    after MAX_AGENT_STEPS calls and raise a clear error.
    """
    responses = [fake_tool_call_response() for _ in range(MAX_AGENT_STEPS)]
    fake_client = FakeOpenAI(responses)

    monkeypatch.setattr(services, "OpenAI", lambda api_key: fake_client)

    with pytest.raises(ValueError):
        triage_ticket_agent("Vague ticket that never gets resolved.")

    assert fake_client.call_count == MAX_AGENT_STEPS