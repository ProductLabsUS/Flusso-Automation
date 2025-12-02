"""
VIP Compliance Check Node
Verifies that response complies with VIP rules.
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.utils.audit import add_audit_event
from app.clients.llm_client import call_llm
from app.config.constants import VIP_COMPLIANCE_PROMPT

logger = logging.getLogger(__name__)
STEP_NAME = "1️⃣3️⃣ VIP_COMPLIANCE"


def verify_vip_compliance(state: TicketState) -> Dict[str, Any]:
    """
    Check if the drafted response complies with VIP rules.

    Writes:
      - vip_compliant: bool
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Checking VIP compliance...")

    vip_rules = state.get("vip_rules", {}) or {}

    # If no VIP rules, automatically compliant.
    if not vip_rules:
        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | ⏭ No VIP rules → automatically compliant ({duration:.2f}s)")
        audit_events = add_audit_event(
            state,
            event="verify_vip_compliance",
            event_type="DECISION",
            details={
                "vip_compliant": True,
                "reason": "No VIP rules applicable",
            },
        )["audit_events"]

        return {
            "vip_compliant": True,
            "audit_events": audit_events,
        }

    logger.info(f"{STEP_NAME} | 📥 Input: {len(vip_rules)} VIP rules to check")

    ticket_text = state.get("ticket_text", "") or ""
    context = state.get("multimodal_context", "") or ""
    draft_response = state.get("draft_response", "") or ""

    user_prompt = f"""Ticket:
{ticket_text}

Knowledge:
{context}

Draft Response:
{draft_response}

VIP Rules:
{vip_rules}
"""

    try:
        logger.info(f"{STEP_NAME} | 🔄 Calling LLM for compliance check...")
        llm_start = time.time()
        
        response = call_llm(
            system_prompt=VIP_COMPLIANCE_PROMPT,
            user_prompt=user_prompt,
            response_format="json",
        )
        
        llm_duration = time.time() - llm_start
        logger.info(f"{STEP_NAME} | ✓ LLM response in {llm_duration:.2f}s")

        if not isinstance(response, dict):
            logger.warning(f"{STEP_NAME} | ⚠ Non-dict response, defaulting to compliant=True")
            compliant = True
            reason = None
        else:
            compliant = bool(response.get("vip_compliant", True))
            reason = response.get("reason", "")

        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | 🎯 Decision: vip_compliant={compliant}")
        if not compliant:
            logger.warning(f"{STEP_NAME} | ⚠ Non-compliance reason: {reason}")
        logger.info(f"{STEP_NAME} | ✅ Complete in {duration:.2f}s")

        audit_events = add_audit_event(
            state,
            event="verify_vip_compliance",
            event_type="DECISION",
            details={
                "vip_compliant": compliant,
                "reason": reason,
                "llm_duration_seconds": llm_duration,
            },
        )["audit_events"]

        return {
            "vip_compliant": compliant,
            "audit_events": audit_events,
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{STEP_NAME} | ❌ Error after {duration:.2f}s: {e}", exc_info=True)

        # Safe fallback: don't block resolution just due to check failure.
        audit_events = add_audit_event(
            state,
            event="verify_vip_compliance",
            event_type="ERROR",
            details={"error": str(e), "vip_compliant": True},
        )["audit_events"]

        return {
            "vip_compliant": True,
            "audit_events": audit_events,
        }
