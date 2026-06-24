# AI Compliance Ticket Triage Agent

A FastAPI backend that turns a raw compliance incident report into a structured
triage analysis — priority, category, suggested team, escalation flag, draft
response and an internal legal note — using the OpenAI API.

The domain is **legal / compliance**: GDPR breaches, HR policy violations and
NDA reviews. The goal is to show how an LLM can be used for the *judgement* part
of a workflow while plain Python handles everything that should stay
deterministic.

---

## What it does

Send a free-text ticket to `POST /triage-ticket` and get back a validated JSON
object. If the ticket is too vague to triage, the agent does not guess — it
flags `needs_more_info` and returns a follow-up question for the submitter.

```text
"An employee says their manager shared confidential salary data."
        │
        ▼
{
  "priority": "Medium",
  "issue_category": "Internal Confidentiality Breach / HR Policy Violation",
  "suggested_team": "HR Legal / Internal Investigations",
  "escalation_required": false,
  "needs_more_info": true,
  "follow_up_question": "Could you provide the incident date, the names of the
                         people involved, and any supporting evidence?",
  ...
}
```

---

## Key features

- **Structured, validated output** — every response is a Pydantic model, so the
  shape is guaranteed (priority is always one of `Critical / High / Medium / Low`).
- **Function-calling agent loop** — `triage_ticket_agent()` gives the model a
  `check_missing_information` tool. When details are missing it asks a follow-up
  question instead of inventing data. A `MAX_AGENT_STEPS` limit makes the loop
  safe by design (no infinite loops).
- **Mock mode** — runs with no API key (`USE_MOCK=true`), so anyone can clone and
  try the project instantly. Live mode (`USE_MOCK=false`) calls the OpenAI API.
- **File outputs** — each result is saved as `.json` and a human-readable `.txt`
  report under `outputs/`.
- **Tested** — 6 pytest tests, including the agent loop tested against a fake
  OpenAI client (no real API calls).

---

## Tech stack

Python · FastAPI · Pydantic · OpenAI API · python-dotenv · pytest

---

## Architecture

```
app/
├── main.py        FastAPI app + endpoints (no business logic)
├── models.py      Pydantic schemas: TicketInput + TicketAnalysis
├── services.py    Triage logic: mock, live OpenAI, and the agent loop
├── mock_data.py   Three pre-written example responses
├── file_utils.py  Save results as .json and .txt
└── config.py      All constants and environment settings
tests/
├── test_basic.py  Mock-mode tests (4)
└── test_agent.py  Agent-loop tests with a fake OpenAI client (2)
```

Design principle: one job per file, one thing per function, no hardcoded values
inside functions, type hints and docstrings throughout.

---

## How the agent loop works

1. The ticket is sent to the model with the `check_missing_information` tool
   available.
2. **Enough detail** → the model returns the final JSON analysis directly.
3. **Missing detail** → the model calls the tool; the loop records this and asks
   the model to finalise with `needs_more_info = true` and a follow-up question.
4. The loop runs at most `MAX_AGENT_STEPS` (3) times, so it can never hang.

---

## Getting started

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env          # mock mode works with no API key

# 3. Run the API
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/triage-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_text": "Marketing emailed 45,000 EU customers without GDPR consent."}'
```

---

## Testing

```bash
python -m pytest -v
```

The agent loop is tested without touching the real API: a fake OpenAI client
returns canned responses, which lets both branches (final answer vs. follow-up
question) and the `MAX_AGENT_STEPS` safety limit be verified deterministically.

---

## Roadmap

- [x] **Phase 1** — Core API: schemas, mock + live triage, file outputs, tests
- [x] **Phase 2** — Mini-agent: function calling, multi-turn loop, agent tests
- [ ] **Phase 3** — Power Automate integration (Outlook email → HTTP → Excel/Teams)
