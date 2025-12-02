"""
Freshdesk Update Node
Updates ticket with public/private reply + tags
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.utils.audit import add_audit_event
from app.clients.freshdesk_client import get_freshdesk_client
from app.config.constants import ResolutionStatus

logger = logging.getLogger(__name__)
STEP_NAME = "1️⃣6️⃣ FRESHDESK_UPDATE"


def update_freshdesk_ticket(state: TicketState) -> Dict[str, Any]:
    """Final step → push replies + tags to Freshdesk."""
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Starting Freshdesk update...")

    try:
        ticket_id = int(state.get("ticket_id"))
    except Exception:
        raise ValueError("Invalid ticket_id in state")

    status = state.get("resolution_status", ResolutionStatus.AI_UNRESOLVED.value)
    reply_text = state.get("final_response_public") or ""

    logger.info(f"{STEP_NAME} | 📥 Input: ticket_id={ticket_id}, status='{status}', reply_len={len(reply_text)}")

    client = get_freshdesk_client()

    try:
        # ---------------- DO WE REPLY PUBLIC OR PRIVATE? ----------------
        unresolved = status in [
            ResolutionStatus.AI_UNRESOLVED.value,
            ResolutionStatus.LOW_CONFIDENCE_MATCH.value,
            ResolutionStatus.VIP_RULE_FAILURE.value,
        ]

        if unresolved:
            # private note
            note_text = f"""
🤖 *AI Review Needed*

**Status:** {status}

**Suggested Reply:**  
{reply_text}

**Decision Metrics**
- Product Confidence: {state.get('product_match_confidence', 0):.2f}
- Hallucination Risk: {state.get('hallucination_risk', 0):.2f}
- Enough Info: {state.get('enough_information', False)}
- VIP Compliant: {state.get('vip_compliant', True)}
"""
            logger.info(f"{STEP_NAME} | 📝 Adding PRIVATE note (needs human review)")
            note_start = time.time()
            client.add_note(ticket_id, note_text, private=True)
            logger.info(f"{STEP_NAME} | ✓ Private note added in {time.time() - note_start:.2f}s")
            note_type = "private"
        else:
            # public reply
            logger.info(f"{STEP_NAME} | 📨 Adding PUBLIC reply")
            note_start = time.time()
            client.add_note(ticket_id, reply_text, private=False)
            logger.info(f"{STEP_NAME} | ✓ Public reply added in {time.time() - note_start:.2f}s")
            note_type = "public"

        # ---------------------- UPDATE TAGS ----------------------
        old_tags = state.get("tags") or []
        extra_tags = state.get("extra_tags") or []
        merged_tags = sorted(list(set(old_tags + extra_tags)))

        logger.info(f"{STEP_NAME} | 🏷 Updating tags: {old_tags} + {extra_tags} → {merged_tags}")
        tags_start = time.time()
        client.update_ticket(ticket_id, tags=merged_tags)
        logger.info(f"{STEP_NAME} | ✓ Tags updated in {time.time() - tags_start:.2f}s")

        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | ✅ Complete: ticket #{ticket_id} updated ({note_type} note) in {duration:.2f}s")

        return {
            "tags": merged_tags,
            "audit_events": add_audit_event(
                state,
                "update_freshdesk_ticket",
                "UPDATE",
                {
                    "ticket_id": ticket_id,
                    "resolution_status": status,
                    "note_type": note_type,
                    "tags": merged_tags,
                    "duration_seconds": duration,
                },
            )["audit_events"],
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{STEP_NAME} | ❌ Error updating ticket #{ticket_id} after {duration:.2f}s: {e}", exc_info=True)

        return {
            "audit_events": add_audit_event(
                state,
                "update_freshdesk_ticket",
                "ERROR",
                {"ticket_id": ticket_id, "error": str(e)},
            )["audit_events"]
        }
