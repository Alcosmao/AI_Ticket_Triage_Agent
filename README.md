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
- **Grounded legal citations (RAG-lite)** — a `lookup_regulation` tool lets the
  agent fetch the exact regulation reference, deadline and authority from a
  controlled knowledge base instead of guessing them. The model decides *what*
  to look up; the citation comes from a trusted source, not its memory.
- **Two-tier escalation** — a cheap single-shot pass triages every ticket; only
  tickets flagged `escalation_required` are escalated to the grounding agent, so
  routine cases stay fast and inexpensive.
- **Mock mode** — runs with no API key (`USE_MOCK=true`), so anyone can clone and
  try the project instantly. Live mode (`USE_MOCK=false`) calls the OpenAI API.
- **File outputs** — each result is saved as `.json` and a human-readable `.txt`
  report under `outputs/`.
- **Tested** — 14 pytest tests covering mock triage, the agent loop, tool
  dispatch, the knowledge-base lookup and the escalation endpoint — all run
  against a fake OpenAI client, with no real API calls.

---

## Tech stack

Python · FastAPI · Pydantic · OpenAI API · python-dotenv · pytest

---

## Architecture

```
app/
├── main.py            FastAPI app + endpoints, with two-tier escalation (no business logic)
├── models.py          Pydantic schemas: TicketInput + TicketAnalysis
├── services.py        Triage logic: mock, live OpenAI, the agent loop and tool dispatch
├── knowledge_base.py  Controlled regulation facts (the RAG-lite retrieval source)
├── mock_data.py       Three pre-written example responses
├── file_utils.py      Save results as .json and .txt
└── config.py          All constants and environment settings
tests/
├── test_basic.py      Mock-mode tests (4)
├── test_agent.py      Agent loop, tool dispatch and knowledge-base tests (8)
└── test_main.py       Endpoint escalation tests (2)
```

Design principle: one job per file, one thing per function, no hardcoded values
inside functions, type hints and docstrings throughout.

---

## How the agent loop works

1. A cheap single-shot triage runs first. If it does **not** flag
   `escalation_required`, that result is returned — routine tickets never pay for
   the agent.
2. Otherwise the ticket escalates to the agent loop, which has two tools:
   `check_missing_information` and `lookup_regulation`.
3. Each turn the model either returns the final JSON analysis, or calls a tool.
   When it calls `lookup_regulation`, the loop **executes** the lookup against the
   knowledge base and feeds the real facts back, so the citation is grounded.
4. The loop runs at most `MAX_AGENT_STEPS` (3) times, so it can never hang.

Verified live: on a GDPR ticket the agent selected the `gdpr_consent` topic,
called `lookup_regulation`, and cited the reference returned by the knowledge
base rather than guessing it.

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

All 14 tests run without touching the real API: a fake OpenAI client returns
canned responses, so the agent's branches, the `MAX_AGENT_STEPS` limit, the tool
dispatcher, the knowledge-base lookup and the escalation endpoint are all
verified deterministically.

---

## Roadmap

- [x] **Phase 1** — Core API: schemas, mock + live triage, file outputs, tests
- [x] **Phase 2** — Mini-agent: function calling, multi-turn loop, agent tests
- [x] **Phase 2.5** — Grounding (RAG-lite): `lookup_regulation` tool, controlled
  knowledge base, two-tier escalation
- [ ] **Phase 3** — Power Automate integration (Outlook email → HTTP → Excel/Teams)
