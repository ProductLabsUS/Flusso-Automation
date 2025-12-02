"""
Audit Logging Utility
Adds structured audit events into TicketState.audit_events
"""

from typing import Dict, Any, List


def add_audit_event(
    state: Dict[str, Any],
    event: str,
    event_type: str = "INFO",
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Append a structured audit event to the state's audit_events list.

    Args:
        state: Current state object
        event: Name of the event (e.g., "fetch_ticket", "vision_rag")
        event_type: INFO | ERROR | SUCCESS | FETCH | DECISION
        details: Additional info dictionary

    Returns:
        Updated state partial: {"audit_events": [...]}
    """

    details = details or {}

    audit_events: List[Dict[str, Any]] = state.get("audit_events", [])

    audit_events.append({
        "event": event,
        "type": event_type,
        "details": details
    })

    return {"audit_events": audit_events}
