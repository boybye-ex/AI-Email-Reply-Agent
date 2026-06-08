from typing import Any, List, Optional, TypedDict

class GraphState(TypedDict):
    """State management for the email processing workflow."""
    initial_email: str
    email_category: str
    urgency_level: str
    needs_human_escalation: bool
    escalation_reasoning: str
    draft_email: str
    final_email: str
    research_info: Optional[List[Any]]
    info_needed: bool
    num_steps: int
    draft_email_feedback: dict
