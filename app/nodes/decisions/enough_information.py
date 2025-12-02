"""
Enough Information Decider Node
Final check if we have enough information to proceed.
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.utils.audit import add_audit_event

logger = logging.getLogger(__name__)
STEP_NAME = "🔟 ENOUGH_INFO_CHECK"


def check_enough_information(state: TicketState) -> Dict[str, Any]:
    """
    Verify / confirm the enough_information flag.
    Currently just logs + audits what orchestration decided,
    but can be extended with extra heuristics (min hits, etc.).
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Verifying information sufficiency...")

    enough_info = bool(state.get("enough_information", False))
    text_hits = len(state.get("text_retrieval_results", []) or [])
    image_hits = len(state.get("image_retrieval_results", []) or [])
    past_hits = len(state.get("past_ticket_results", []) or [])
    
    logger.info(f"{STEP_NAME} | 📥 Input: enough_info={enough_info}, text_hits={text_hits}, image_hits={image_hits}, past_hits={past_hits}")
    
    duration = time.time() - start_time
    logger.info(f"{STEP_NAME} | 🎯 Decision: enough_information={enough_info}")
    logger.info(f"{STEP_NAME} | ✅ Complete in {duration:.2f}s")

    audit_events = add_audit_event(
        state,
        event="check_enough_information",
        event_type="DECISION",
        details={
            "enough_information": enough_info,
            "text_hits": text_hits,
            "image_hits": image_hits,
            "past_hits": past_hits,
        },
    )["audit_events"]

    return {
        # We don't alter enough_information here (just confirm + audit)
        "audit_events": audit_events,
    }
