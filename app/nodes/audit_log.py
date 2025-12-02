"""
Audit Log Node
Writes complete workflow audit trail as JSON lines.
Also completes the detailed workflow log for examination.
"""

import logging
import json
import time
from typing import Dict, Any
from pathlib import Path

from app.graph.state import TicketState
from app.utils.detailed_logger import complete_workflow_log, get_current_log

logger = logging.getLogger(__name__)
STEP_NAME = "1️⃣7️⃣ AUDIT_LOG"


def write_audit_log(state: TicketState) -> Dict[str, Any]:
    """
    Final node in the graph.
    Writes the full audit trail + key metrics to a log file.

    Returns:
        {} (no further state updates)
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Writing audit trail...")
    
    ticket_id = state.get("ticket_id", "unknown")
    events = state.get("audit_events", []) or []

    logger.info(f"{STEP_NAME} | 📥 Input: ticket_id={ticket_id}, events_count={len(events)}")

    # Extract vision results for logging
    image_results = state.get("image_retrieval_results", []) or []
    vision_matches = []
    for i, hit in enumerate(image_results[:5]):  # Top 5 matches
        metadata = hit.get("metadata", {})
        vision_matches.append({
            "rank": i + 1,
            "score": round(hit.get("score", 0), 4),
            "product_id": metadata.get("product_id", "N/A"),
            "product_name": metadata.get("product_name", "N/A"),
            "image_name": metadata.get("image_name", "N/A"),
            "category": metadata.get("category", metadata.get("product_category", "N/A"))
        })
    
    # Extract text RAG results
    text_results = state.get("text_retrieval_results", []) or []
    text_matches = []
    for i, hit in enumerate(text_results[:5]):
        text_matches.append({
            "rank": i + 1,
            "score": round(hit.get("score", 0), 4),
            "title": hit.get("metadata", {}).get("title", hit.get("title", "N/A")),
            "content_preview": (hit.get("content", "") or "")[:200]
        })
    
    record = {
        "ticket_id": ticket_id,
        "timestamp": time.time(),
        "resolution_status": state.get("resolution_status"),
        "customer_type": state.get("customer_type"),
        "category": state.get("ticket_category"),
        "overall_confidence": state.get("overall_confidence", 0),
        "metrics": {
            "enough_information": state.get("enough_information"),
            "hallucination_risk": state.get("hallucination_risk"),
            "product_confidence": state.get("product_match_confidence"),
            "vip_compliant": state.get("vip_compliant"),
        },
        "retrieval_counts": {
            "text_hits": len(text_results),
            "image_hits": len(image_results),
            "past_ticket_hits": len(state.get("past_ticket_results", []) or []),
        },
        "vision_matches": vision_matches,
        "text_matches": text_matches,
        "events": events,
    }

    try:
        log_file = Path("audit.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        
        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | ✅ Audit trail written to {log_file} ({len(events)} events) in {duration:.2f}s")
        logger.info(f"{STEP_NAME} | 📊 Final summary: status='{record['resolution_status']}', metrics={record['metrics']}")
        
        # Complete and save detailed workflow log
        detailed_log_path = complete_workflow_log(
            resolution_status=record["resolution_status"],
            final_response=state.get("final_response_public") or state.get("draft_response"),
            overall_confidence=state.get("overall_confidence", 0.0),
            metrics=record["metrics"]
        )
        if detailed_log_path:
            logger.info(f"{STEP_NAME} | 📁 Detailed log saved: {detailed_log_path}")
            
    except Exception as e:
        logger.error(f"{STEP_NAME} | ❌ Error writing audit log: {e}", exc_info=True)

    # Final node → no further updates
    return {}
