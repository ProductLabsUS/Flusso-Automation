"""
Orchestration Agent
LLM evaluates whether enough info exists to proceed
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.utils.audit import add_audit_event
from app.clients.llm_client import call_llm
from app.config.constants import ORCHESTRATION_SYSTEM_PROMPT
from app.utils.detailed_logger import (
    log_node_start, log_node_complete, log_llm_interaction
)

logger = logging.getLogger(__name__)
STEP_NAME = "9️⃣ ORCHESTRATION"


def orchestration_agent(state: TicketState) -> Dict[str, Any]:
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Starting orchestration analysis...")
    
    # Start node log
    node_log = log_node_start("orchestration_agent", {})

    subject = state.get("ticket_subject", "")
    text = state.get("ticket_text", "")
    ctx = state.get("multimodal_context", "")
    
    node_log.input_summary = {
        "subject": subject[:100],
        "text_length": len(text),
        "context_length": len(ctx)
    }
    
    logger.info(f"{STEP_NAME} | 📥 Input: subject='{subject[:50]}...', text_len={len(text)}, context_len={len(ctx)}")

    prompt = f"""
Customer Ticket
---------------
Subject: {subject}

Description:
{text}

Retrieved Context:
------------------
{ctx}
"""

    try:
        logger.info(f"{STEP_NAME} | 🔄 Calling LLM for information assessment...")
        llm_start = time.time()
        
        response = call_llm(
            system_prompt=ORCHESTRATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_format="json",
        )
        
        llm_duration = time.time() - llm_start
        logger.info(f"{STEP_NAME} | ✓ LLM response in {llm_duration:.2f}s")

        # Safe extraction
        enough = bool(response.get("enough_information", False))
        product_id = response.get("product_id")
        summary = response.get("summary", "")
        reasoning = response.get("reasoning", "")

        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | 🎯 Decision: enough_information={enough}")
        logger.info(f"{STEP_NAME} | 📝 Reasoning: {reasoning[:200]}..." if len(reasoning) > 200 else f"{STEP_NAME} | 📝 Reasoning: {reasoning}")
        logger.info(f"{STEP_NAME} | ✅ Complete in {duration:.2f}s")
        
        # Log LLM interaction for detailed examination
        log_llm_interaction(
            node_log,
            system_prompt=ORCHESTRATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            response=str(response),
            parsed_response=response
        )
        log_node_complete(
            node_log,
            output_summary={
                "enough_information": enough,
                "product_id": product_id,
                "duration_seconds": duration
            },
            decision={
                "enough_information": enough,
                "product_id": product_id,
                "summary": summary
            },
            reasoning=reasoning
        )

        return {
            "enough_information": enough,
            "audit_events": add_audit_event(
                state,
                "orchestration_agent",
                "DECISION",
                {
                    "enough_information": enough,
                    "product_id": product_id,
                    "summary": summary,
                    "reasoning": reasoning,
                    "llm_duration_seconds": llm_duration,
                },
            )["audit_events"],
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{STEP_NAME} | ❌ Error after {duration:.2f}s: {e}", exc_info=True)

        return {
            "enough_information": False,
            "audit_events": add_audit_event(
                state,
                "orchestration_agent",
                "ERROR",
                {"error": str(e)},
            )["audit_events"]
        }
