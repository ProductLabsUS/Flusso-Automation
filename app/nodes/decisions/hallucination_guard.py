"""
Hallucination Guard Node
Assesses risk of AI hallucinating / inventing facts.
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.utils.audit import add_audit_event
from app.clients.llm_client import call_llm
from app.config.constants import HALLUCINATION_GUARD_PROMPT
from app.utils.detailed_logger import (
    log_node_start, log_node_complete, log_llm_interaction
)

logger = logging.getLogger(__name__)
STEP_NAME = "1️⃣1️⃣ HALLUCINATION_GUARD"


def assess_hallucination_risk(state: TicketState) -> Dict[str, Any]:
    """
    Evaluate hallucination risk.

    Writes:
      - hallucination_risk: float in [0, 1]
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Evaluating hallucination risk...")
    
    # Start node log
    node_log = log_node_start("hallucination_guard", {})

    ticket_text = state.get("ticket_text", "") or ""
    context = state.get("multimodal_context", "") or ""
    
    node_log.input_summary = {
        "ticket_length": len(ticket_text),
        "context_length": len(context)
    }
    
    logger.info(f"{STEP_NAME} | 📥 Input: ticket_len={len(ticket_text)}, context_len={len(context)}")

    user_prompt = f"""Ticket:
{ticket_text}

Knowledge:
{context}
"""

    try:
        logger.info(f"{STEP_NAME} | 🔄 Calling LLM for risk assessment...")
        llm_start = time.time()
        
        response = call_llm(
            system_prompt=HALLUCINATION_GUARD_PROMPT,
            user_prompt=user_prompt,
            response_format="json",
        )
        
        llm_duration = time.time() - llm_start
        logger.info(f"{STEP_NAME} | ✓ LLM response in {llm_duration:.2f}s")

        if not isinstance(response, dict):
            logger.warning(f"{STEP_NAME} | ⚠ Non-dict response from LLM, defaulting to 0.5")
            risk = 0.5
            reasoning = None
        else:
            risk = float(response.get("risk", 0.5))
            reasoning = response.get("reasoning")

        risk = max(0.0, min(1.0, risk))

        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | 🎯 Decision: hallucination_risk={risk:.2f}")
        if reasoning:
            logger.info(f"{STEP_NAME} | 📝 Reasoning: {reasoning[:150]}..." if len(str(reasoning)) > 150 else f"{STEP_NAME} | 📝 Reasoning: {reasoning}")
        logger.info(f"{STEP_NAME} | ✅ Complete in {duration:.2f}s")
        
        # Log LLM interaction
        log_llm_interaction(
            node_log,
            system_prompt=HALLUCINATION_GUARD_PROMPT,
            user_prompt=user_prompt,
            response=str(response),
            parsed_response=response if isinstance(response, dict) else {"risk": risk}
        )
        log_node_complete(
            node_log,
            output_summary={"hallucination_risk": risk},
            decision={"risk": risk},
            reasoning=str(reasoning) if reasoning else None
        )

        audit_events = add_audit_event(
            state,
            event="assess_hallucination_risk",
            event_type="DECISION",
            details={"risk": risk, "reasoning": reasoning, "llm_duration_seconds": llm_duration},
        )["audit_events"]

        return {
            "hallucination_risk": risk,
            "audit_events": audit_events,
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{STEP_NAME} | ❌ Error after {duration:.2f}s: {e}", exc_info=True)

        fallback_risk = 0.8  # safe: treat as high risk
        logger.warning(f"{STEP_NAME} | Using fallback risk={fallback_risk}")

        audit_events = add_audit_event(
            state,
            event="assess_hallucination_risk",
            event_type="ERROR",
            details={"error": str(e), "risk": fallback_risk},
        )["audit_events"]

        return {
            "hallucination_risk": fallback_risk,
            "audit_events": audit_events,
        }
