"""
Routing Agent Node
Classifies ticket using LLM or fallback rules
CLEAN + PRODUCTION READY VERSION
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.utils.audit import add_audit_event
from app.clients.llm_client import call_llm
from app.config.constants import ROUTING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

STEP_NAME = "2️⃣ ROUTING_AGENT"


def classify_ticket_category(state: TicketState) -> Dict[str, Any]:
    """
    Classify the ticket category using LLM.
    Falls back to rule-based classification on errors.
    """
    start_time = time.time()
    
    logger.info(f"{'='*60}")
    logger.info(f"{STEP_NAME} | Starting ticket classification")
    logger.info(f"{'='*60}")

    subject = state.get("ticket_subject", "") or ""
    text = state.get("ticket_text", "") or ""
    tags = state.get("tags", [])
    ticket_type = state.get("ticket_type")
    
    logger.info(f"{STEP_NAME} | Input: subject={len(subject)} chars, text={len(text)} chars, tags={tags}")

    # -------------------------------------------
    # Handle empty tickets
    # -------------------------------------------
    if not subject.strip() and not text.strip():
        logger.warning(f"{STEP_NAME} | ⚠️ Empty ticket content → defaulting to 'general'")
        return {
            "ticket_category": "general",
            "audit_events": add_audit_event(
                state,
                event="classify_ticket_category",
                event_type="CLASSIFICATION",
                details={"category": "general", "reason": "empty_ticket"}
            )["audit_events"]
        }

    # -------------------------------------------
    # Build prompt content
    # -------------------------------------------
    content = f"Subject: {subject}\n\nDescription:\n{text}"

    if tags:
        content += f"\n\nTags: {', '.join(tags)}"
    if ticket_type:
        content += f"\n\nTicket Type: {ticket_type}"

    try:
        # -------------------------------------------
        # LLM classification
        # -------------------------------------------
        logger.info(f"{STEP_NAME} | Calling LLM for classification...")
        llm_start = time.time()
        
        response = call_llm(
            system_prompt=ROUTING_SYSTEM_PROMPT,
            user_prompt=content,
            response_format="json",
            temperature=0.1
        )
        
        llm_duration = time.time() - llm_start
        logger.info(f"{STEP_NAME} | LLM responded in {llm_duration:.2f}s")

        if not isinstance(response, dict):
            raise ValueError("Invalid LLM response format")

        category = response.get("category", "general")
        confidence = response.get("confidence", 0.0)
        reasoning = response.get("reasoning", "")

        # normalize category
        if not isinstance(category, str) or not category.strip():
            category = "general"

        category = category.lower().strip().replace(" ", "_")

        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | ✅ Classified as '{category}' (confidence={confidence:.2f})")
        logger.info(f"{STEP_NAME} | Reasoning: {reasoning[:150]}..." if reasoning else f"{STEP_NAME} | No reasoning provided")
        logger.info(f"{STEP_NAME} | Completed in {duration:.2f}s")

        return {
            "ticket_category": category,
            "audit_events": add_audit_event(
                state,
                event="classify_ticket_category",
                event_type="CLASSIFICATION",
                details={
                    "category": category,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "tags_used": len(tags) > 0,
                    "ticket_type_used": ticket_type is not None
                }
            )["audit_events"]
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{STEP_NAME} | ❌ LLM classification failed after {duration:.2f}s: {e}", exc_info=True)

        # Fallback
        category = fallback_classification(subject, text, tags)
        logger.warning(f"{STEP_NAME} | Using fallback classification → '{category}'")

        return {
            "ticket_category": category,
            "audit_events": add_audit_event(
                state,
                event="classify_ticket_category",
                event_type="ERROR",
                details={
                    "category": category,
                    "error": str(e),
                    "fallback_used": True
                }
            )["audit_events"]
        }


# -------------------------------------------------------------
# FALLBACK CLASSIFIER (rule-based)
# -------------------------------------------------------------
def fallback_classification(subject: str, text: str, tags: list) -> str:
    content = (subject + " " + text).lower()
    tags_lower = [t.lower() for t in tags]

    # Tag matches
    tag_map = {
        "warranty": "warranty",
        "install": "installation_help",
        "installation": "installation_help",
        "return": "return_request",
        "refund": "return_request",
        "defect": "product_issue",
        "broken": "product_issue",
        "damaged": "product_issue",
        "complaint": "complaint"
    }

    for t in tags_lower:
        for key, cat in tag_map.items():
            if key in t:
                return cat

    # Keyword matches
    keyword_map = {
        "warranty": ["warranty", "guarantee"],
        "product_issue": ["broken", "defective", "faulty", "damaged"],
        "installation_help": ["install", "installation", "setup", "mount"],
        "return_request": ["return", "refund", "exchange"],
        "complaint": ["unhappy", "angry", "bad service"],
        "general_inquiry": ["inquiry", "question", "information"]
    }

    for category, keywords in keyword_map.items():
        for word in keywords:
            if word in content:
                return category

    return "general"


# -------------------------------------------------------------
# Validator (Optional)
# -------------------------------------------------------------
def validate_routing_result(state: TicketState) -> bool:
    category = state.get("ticket_category")
    return isinstance(category, str) and len(category) > 0
