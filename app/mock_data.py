MOCK_CRITICAL = {
    "ticket_summary": (
        "Marketing sent promotional emails to 45,000 EU customers without "
        "documented consent. Opt-in records cannot be located. DPO notified "
        "but unresponsive. Legal is asking about GDPR obligations within 72 hours."
    ),
    "issue_category": "GDPR Data Breach / Consent Violation",
    "priority": "Critical",
    "urgency_reason": (
        "GDPR Article 33 requires notification to the supervisory authority "
        "within 72 hours of becoming aware of a personal data breach. "
        "The clock may already be running."
    ),
    "suggested_team": "Data Protection Officer / External Legal Counsel",
    "required_information": [
        "Exact date the campaign was sent",
        "Confirmation of whether consent records exist anywhere in the CRM",
        "Date the DPO was notified",
        "Whether the supervisory authority has been contacted yet",
    ],
    "recommended_next_steps": [
        "Escalate immediately to DPO and external legal counsel",
        "Determine whether this qualifies as a notifiable breach under Article 33",
        "If notifiable, file report with supervisory authority within 72-hour window",
        "Preserve all CRM and campaign records — do not delete or modify",
        "Draft an internal breach report",
    ],
    "escalation_required": True,
    "needs_more_info": False,
    "follow_up_question": None,
    "draft_customer_response": (
        "Thank you for reporting this matter. We are treating this as a "
        "high-priority compliance incident. Our Data Protection Officer and "
        "Legal team have been notified and are reviewing the situation. "
        "We will provide an update within 24 hours."
    ),
    "internal_legal_note": (
        "Potential GDPR Article 6 (lawful basis) and Article 7 (consent) "
        "violation affecting 45,000 data subjects. Article 33 notification "
        "window may be active. Immediate DPO escalation required. "
        "Do not delete or modify any campaign or CRM records pending investigation."
    ),
}


MOCK_MEDIUM = {
    "ticket_summary": (
        "An employee alleges their manager shared confidential salary data "
        "with unauthorized staff. Incident date unknown, no witnesses named, "
        "no documentation provided."
    ),
    "issue_category": "Internal Confidentiality Breach / HR Policy Violation",
    "priority": "Medium",
    "urgency_reason": (
        "No immediate regulatory deadline, but the lack of details prevents "
        "proper assessment of scope. If salary data constitutes personal data "
        "under GDPR, further review will be required."
    ),
    "suggested_team": "HR Legal / Internal Investigations",
    "required_information": [
        "Approximate date of the incident",
        "Names of the manager and the staff members who received the data",
        "Which salary figures were shared and how many employees were affected",
        "Supporting evidence such as emails, screenshots, or witness statements",
    ],
    "recommended_next_steps": [
        "Collect missing information before escalating",
        "Interview the reporting employee",
        "Review HR policy on data confidentiality",
    ],
    "escalation_required": False,
    "needs_more_info": True,
    "follow_up_question": (
        "To properly assess this incident, could you please provide: "
        "(1) the approximate date the incident occurred, "
        "(2) the names of the manager and the staff members who received the information, "
        "and (3) any supporting evidence such as emails or screenshots?"
    ),
    "draft_customer_response": (
        "Thank you for bringing this to our attention. To begin a proper review, "
        "we need a few additional details. Please see the questions below."
    ),
    "internal_legal_note": (
        "Insufficient information to determine breach severity or regulatory exposure. "
        "Do not escalate until incident date, individuals involved, "
        "and scope of data shared are confirmed."
    ),
}


MOCK_LOW = {
    "ticket_summary": (
        "A new vendor has sent a standard services contract and NDA for signature "
        "before a project kickoff next month. No specific deadline given."
    ),
    "issue_category": "Routine Contract / NDA Review",
    "priority": "Low",
    "urgency_reason": (
        "No regulatory deadline. Project kickoff is next month, "
        "leaving sufficient time for a standard review."
    ),
    "suggested_team": "Contract Review Team / Junior Legal Associate",
    "required_information": [
        "Vendor name",
        "Exact project kickoff date",
        "Whether the NDA is mutual or one-sided",
    ],
    "recommended_next_steps": [
        "Assign to the contract review queue",
        "Check NDA against the standard template for non-standard clauses",
        "Confirm jurisdiction and governing law clause",
        "Return signed NDA at least 5 business days before kickoff",
    ],
    "escalation_required": False,
    "needs_more_info": False,
    "follow_up_question": None,
    "draft_customer_response": (
        "Thank you for sending the NDA and services contract. We have received "
        "the documents and will route them to our contract review team. "
        "You can expect a response within 5-7 business days."
    ),
    "internal_legal_note": (
        "Routine NDA. Assign to junior associate. "
        "Verify governing law and confidentiality term length against standard policy. "
        "No escalation required."
    ),
}