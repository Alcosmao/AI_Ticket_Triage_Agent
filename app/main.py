from fastapi import FastAPI, HTTPException
from datetime import datetime

from app.models import TicketInput, TicketAnalysis
from app.services import triage_ticket_mock
from app.config import USE_MOCK
from app.file_utils import save_json_output, save_txt_report

app = FastAPI(
    title="AI Compliance Ticket Triage Agent",
    description="Classifies compliance incidents and returns structured triage analysis.",
    version="1.0.0",
)

@app.get("/")
def heath_check():
    """Quck check that the server is ok"""
    return {"status": "ok", "mode": "mock" if USE_MOCK else "real"}

@app.post("/triage-ticket", response_model=TicketAnalysis)
def triage_ticket(ticket: TicketInput) -> TicketAnalysis:
    """
    Receives a raw compliance ticket and returns a structured triage analysis.

    Args:
        ticket: TicketInput object containing the raw ticket

    Returns:
        TicketAnalysis object with fields    
    """
    if not ticket.ticket_text.strip():
        raise HTTPException(status_code=400, detail="Ticket text cannot be empty.")

    try:
        if USE_MOCK:
            analysis = triage_ticket_mock(ticket.ticket_text)
        else:
            raise HTTPException(status_code=501, detail="Real mode not implemented yet.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"ticket_{timestamp}"

        save_json_output(analysis, f"{filename_base}.json")
        save_txt_report(analysis, f"{filename_base}.txt")

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}")          