import json
import os
from app.models import TicketAnalysis

OUTPUTS_DIR = "outputs"


def save_json_output(analysis: TicketAnalysis, filename: str) -> None:
    """Save the triage result as a .json file under outputs/."""
    try:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis.model_dump(), f, indent=2, ensure_ascii=False)

        print(f"JSON saved: {filepath}")

    except Exception as e:
        print(f"Couldn't save JSON file: {e}")


def save_txt_report(analysis: TicketAnalysis, filename: str) -> None:
    """Save a readable text report under outputs/."""
    try:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUTS_DIR, filename)

        report = build_txt_report(analysis)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"TXT saved: {filepath}")

    except Exception as e:
        print(f"Couldn't save txt file: {e}")


def build_txt_report(analysis: TicketAnalysis) -> str:
    """Build the formatted report string (split out so it can be tested without writing a file)."""
    lines = [
        "=" * 60,
        "COMPLIANCE TICKET TRIAGE REPORT",
        "=" * 60,
        "",
        f"PRIORITY: {analysis.priority}",
        f"CATEGORY: {analysis.issue_category}",
        f"SUGGESTED TEAM: {analysis.suggested_team}",
        f"ESCALATION: {'YES' if analysis.escalation_required else 'NO'}",
        f"NEEDS MORE INFO: {'YES' if analysis.needs_more_info else 'NO'}",
        "",
        "SUMMARY:",
        analysis.ticket_summary,
        "",
        "URGENCY REASON:",
        analysis.urgency_reason,
        "",
        "REQUIRED INFORMATION:",
    ]    

    for item in analysis.required_information:
        lines.append(f"  - {item}")

    lines += [
        "",
        "RECOMMENDED NEXT STEPS:",
    ]

    for step in analysis.recommended_next_steps:
        lines.append(f"  - {step}")

    lines += [
        "",
        "DRAFT CUSTOMER RESPONSE:",
        analysis.draft_customer_response,
        "",
        "INTERNAL LEGAL NOTE:",
        analysis.internal_legal_note,
    ]

    if analysis.follow_up_question:
        lines += [
            "",
            "FOLLOW-UP QUESTION FOR SUBMITTER:",
            analysis.follow_up_question,
        ]

    lines += ["", "=" * 60]

    return "\n".join(lines)


