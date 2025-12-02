"""
Context Builder Node
Combines all retrieval results into unified context for LLM.
"""

import logging
import time
from typing import Dict, Any, List

from app.graph.state import TicketState, RetrievalHit

logger = logging.getLogger(__name__)
STEP_NAME = "8️⃣ CONTEXT_BUILDER"


def assemble_multimodal_context(state: TicketState) -> Dict[str, Any]:
    """
    Combine all retrieval results (text, image, past tickets, VIP rules)
    into a single formatted context string for the orchestration agent.
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Building unified context...")

    sections: List[str] = []

    # ---------------- TEXT RAG ----------------
    text_hits: List[RetrievalHit] = state.get("text_retrieval_results", []) or []
    if text_hits:
        sections.append("### PRODUCT DOCUMENTATION\n")
        for i, hit in enumerate(text_hits[:5], 1):
            title = hit.get("metadata", {}).get("title", f"Document {i}")
            content = (hit.get("content") or "")[:500]
            score = hit.get("score", 0.0)
            sections.append(
                f"{i}. **{title}** (score: {score:.2f})\n{content}\n"
            )

    # ---------------- IMAGE RAG ----------------
    image_hits: List[RetrievalHit] = state.get("image_retrieval_results", []) or []
    if image_hits:
        sections.append("\n### PRODUCT MATCHES (VISUAL)\n")
        for i, hit in enumerate(image_hits[:5], 1):
            meta = hit.get("metadata", {}) or {}
            product_title = meta.get("product_title", "Unknown Product")
            model_no = meta.get("model_no", "N/A")
            finish = meta.get("finish", "N/A")
            score = hit.get("score", 0.0)
            sections.append(
                f"{i}. **{product_title}** (Model: {model_no}, Finish: {finish}) "
                f"- Similarity: {score:.2f}\n"
            )

    # ---------------- PAST TICKETS ----------------
    past_hits: List[RetrievalHit] = state.get("past_ticket_results", []) or []
    if past_hits:
        sections.append("\n### SIMILAR PAST TICKETS\n")
        for i, hit in enumerate(past_hits[:3], 1):
            meta = hit.get("metadata", {}) or {}
            ticket_id = meta.get("ticket_id", "Unknown")
            resolution_type = meta.get("resolution_type", "N/A")
            content = (hit.get("content") or "")[:300]
            score = hit.get("score", 0.0)

            sections.append(
                f"{i}. Ticket #{ticket_id} ({resolution_type}) "
                f"- Similarity: {score:.2f}\n{content}\n"
            )

    # ---------------- VIP RULES ----------------
    vip_rules = state.get("vip_rules", {}) or {}
    if vip_rules:
        sections.append("\n### VIP CUSTOMER RULES\n")
        for key, value in vip_rules.items():
            label = key.replace("_", " ").title()
            sections.append(f"- {label}: {value}\n")

    multimodal_context = (
        "\n".join(sections) if sections else "No relevant context found."
    )

    duration = time.time() - start_time
    logger.info(f"{STEP_NAME} | 📊 Sources: text={len(text_hits)}, image={len(image_hits)}, past={len(past_hits)}, vip_rules={bool(vip_rules)}")
    logger.info(f"{STEP_NAME} | ✅ Complete: {len(multimodal_context)} chars context in {duration:.2f}s")

    # Append audit info (manual, consistent with your pattern)
    audit_events = state.get("audit_events", []) or []
    audit_events.append(
        {
            "event": "assemble_multimodal_context",
            "text_hits": len(text_hits),
            "image_hits": len(image_hits),
            "past_hits": len(past_hits),
            "has_vip_rules": bool(vip_rules),
            "context_length": len(multimodal_context),
            "duration_seconds": duration,
        }
    )

    return {
        "multimodal_context": multimodal_context,
        "audit_events": audit_events,
    }
