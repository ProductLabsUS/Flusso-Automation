"""
Resolution Logic Node
Determines final status and tags based on all checks.
"""

import logging
import time
from typing import Dict, Any, List

from app.graph.state import TicketState
from app.utils.audit import add_audit_event
from app.config.constants import ResolutionStatus
from app.config.settings import settings

logger = logging.getLogger(__name__)
STEP_NAME = "1️⃣5️⃣ RESOLUTION_LOGIC"


def decide_tags_and_resolution(state: TicketState) -> Dict[str, Any]:
    """
    Determine resolution status and tags.

    Returns:
        Partial update with:
            - resolution_status
            - extra_tags
            - final_response_public
            - audit_events
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Determining final resolution status...")

    enough_info = state.get("enough_information", False)
    risk = state.get("hallucination_risk", 1.0)
    confidence = state.get("product_match_confidence", 0.0)
    vip_ok = state.get("vip_compliant", True)
    
    logger.info(f"{STEP_NAME} | 📥 Input metrics:")
    logger.info(f"{STEP_NAME} |   - enough_information: {enough_info}")
    logger.info(f"{STEP_NAME} |   - hallucination_risk: {risk:.2f} (threshold: {settings.hallucination_risk_threshold})")
    logger.info(f"{STEP_NAME} |   - product_confidence: {confidence:.2f} (threshold: {settings.product_confidence_threshold})")
    logger.info(f"{STEP_NAME} |   - vip_compliant: {vip_ok}")

    tags: List[str] = list(state.get("extra_tags", []) or [])
    draft = state.get("draft_response", "") or ""

    status = ResolutionStatus.RESOLVED.value
    decision_reason = ""

    # Priority 1: Not enough information or high hallucination risk
    if not enough_info or risk > settings.hallucination_risk_threshold:
        status = ResolutionStatus.AI_UNRESOLVED.value
        tags.extend(["AI_UNRESOLVED", "NEEDS_HUMAN_REVIEW"])
        decision_reason = f"insufficient info ({enough_info}) OR high hallucination risk ({risk:.2f} > {settings.hallucination_risk_threshold})"
        logger.info(f"{STEP_NAME} | 🚨 Status: AI_UNRESOLVED - {decision_reason}")

    # Priority 2: Low product confidence
    elif confidence < settings.product_confidence_threshold:
        status = ResolutionStatus.LOW_CONFIDENCE_MATCH.value
        tags.extend(["LOW_CONFIDENCE_MATCH", "NEEDS_HUMAN_REVIEW"])
        decision_reason = f"low product confidence ({confidence:.2f} < {settings.product_confidence_threshold})"
        logger.info(f"{STEP_NAME} | ⚠ Status: LOW_CONFIDENCE_MATCH - {decision_reason}")

    # Priority 3: VIP rule failure
    elif not vip_ok:
        status = ResolutionStatus.VIP_RULE_FAILURE.value
        tags.extend(["VIP_RULE_FAILURE", "NEEDS_HUMAN_REVIEW"])
        decision_reason = "VIP compliance check failed"
        logger.info(f"{STEP_NAME} | ⚠ Status: VIP_RULE_FAILURE - {decision_reason}")

    # All checks passed
    else:
        status = ResolutionStatus.RESOLVED.value
        tags.append("AI_PROCESSED")
        decision_reason = "all checks passed"
        logger.info(f"{STEP_NAME} | ✅ Status: RESOLVED - {decision_reason}")

    # Remove duplicates
    tags = list(set(tags))

    duration = time.time() - start_time
    logger.info(f"{STEP_NAME} | 🎯 Final decision: status='{status}', tags={tags}")
    logger.info(f"{STEP_NAME} | ✅ Complete in {duration:.2f}s")

    audit_events = add_audit_event(
        state,
        event="decide_tags_and_resolution",
        event_type="DECISION",
        details={
            "resolution_status": status,
            "decision_reason": decision_reason,
            "tags": tags,
            "enough_info": enough_info,
            "hallucination_risk": risk,
            "product_confidence": confidence,
            "vip_compliant": vip_ok,
        },
    )["audit_events"]

    return {
        "resolution_status": status,
        "extra_tags": tags,
        "final_response_public": draft,
        "audit_events": audit_events,
    }
