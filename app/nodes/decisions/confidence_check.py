"""
Product Match Confidence Check Node
Evaluates confidence in product identification.
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.utils.audit import add_audit_event
from app.clients.llm_client import call_llm
from app.config.constants import PRODUCT_CONFIDENCE_PROMPT
from app.utils.detailed_logger import (
    log_node_start, log_node_complete, log_llm_interaction
)

logger = logging.getLogger(__name__)
STEP_NAME = "1️⃣2️⃣ CONFIDENCE_CHECK"


def evaluate_product_confidence(state: TicketState) -> Dict[str, Any]:
    """
    Evaluate product match confidence using LLM output.

    Writes:
      - product_match_confidence: float in [0, 1]
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Evaluating product match confidence...")
    
    # Start node log
    node_log = log_node_start("confidence_check", {})

    ticket_text = state.get("ticket_text", "") or ""
    context = state.get("multimodal_context", "") or ""
    
    node_log.input_summary = {
        "ticket_length": len(ticket_text),
        "context_length": len(context)
    }
    
    logger.info(f"{STEP_NAME} | 📥 Input: ticket_len={len(ticket_text)}, context_len={len(context)}")

    user_prompt = f"""Ticket:
{ticket_text}

Retrieved Product Information:
{context}
"""

    try:
        logger.info(f"{STEP_NAME} | 🔄 Calling LLM for confidence assessment...")
        llm_start = time.time()
        
        response = call_llm(
            system_prompt=PRODUCT_CONFIDENCE_PROMPT,
            user_prompt=user_prompt,
            response_format="json",
        )
        
        llm_duration = time.time() - llm_start
        logger.info(f"{STEP_NAME} | ✓ LLM response in {llm_duration:.2f}s")

        if not isinstance(response, dict):
            logger.warning(f"{STEP_NAME} | ⚠ Non-dict response from LLM, using default 0.5")
            confidence = 0.5
            reasoning = None
        else:
            confidence = float(response.get("confidence", 0.5))
            reasoning = response.get("reasoning")

        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | 🎯 Decision: product_match_confidence={confidence:.2f}")
        if reasoning:
            logger.info(f"{STEP_NAME} | 📝 Reasoning: {reasoning[:150]}..." if len(str(reasoning)) > 150 else f"{STEP_NAME} | 📝 Reasoning: {reasoning}")
        logger.info(f"{STEP_NAME} | ✅ Complete in {duration:.2f}s")
        
        # Log LLM interaction
        log_llm_interaction(
            node_log,
            system_prompt=PRODUCT_CONFIDENCE_PROMPT,
            user_prompt=user_prompt,
            response=str(response),
            parsed_response=response if isinstance(response, dict) else {"confidence": confidence}
        )
        log_node_complete(
            node_log,
            output_summary={"product_match_confidence": confidence},
            decision={"confidence": confidence},
            reasoning=str(reasoning) if reasoning else None
        )

        audit_events = add_audit_event(
            state,
            event="evaluate_product_confidence",
            event_type="DECISION",
            details={"confidence": confidence, "reasoning": reasoning, "llm_duration_seconds": llm_duration},
        )["audit_events"]

        return {
            "product_match_confidence": confidence,
            "audit_events": audit_events,
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{STEP_NAME} | ❌ Error after {duration:.2f}s: {e}", exc_info=True)

        fallback_conf = 0.3  # safe, low-confidence default
        logger.warning(f"{STEP_NAME} | Using fallback confidence={fallback_conf}")

        audit_events = add_audit_event(
            state,
            event="evaluate_product_confidence",
            event_type="ERROR",
            details={"error": str(e), "confidence": fallback_conf},
        )["audit_events"]

        return {
            "product_match_confidence": fallback_conf,
            "audit_events": audit_events,
        }
