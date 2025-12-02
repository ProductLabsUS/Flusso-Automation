"""
Vision Pipeline Node
Processes ticket images and retrieves similar products from Pinecone
CLEAN + PRODUCTION READY VERSION
"""

import logging
import time
from typing import Dict, Any, List

from app.graph.state import TicketState, RetrievalHit
from app.utils.audit import add_audit_event
from app.clients.embeddings import embed_image
from app.clients.pinecone_client import get_pinecone_client
from app.config.settings import settings
from app.utils.detailed_logger import (
    log_node_start, log_node_complete, log_vision_results
)

logger = logging.getLogger(__name__)
STEP_NAME = "3️⃣ VISION_PIPELINE"


def process_vision_pipeline(state: TicketState) -> Dict[str, Any]:
    """
    Step:
        1. Embed ticket images using CLIP (or future Gemini embeddings)
        2. Query Pinecone image index
        3. Return ranked RetrievalHit list

    Returns:
        Partial state update:
            - image_retrieval_results
            - ran_vision = True
            - audit_events
    """

    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Starting vision pipeline")
    
    # Start node log
    node_log = log_node_start("vision_pipeline", {"image_count": len(state.get("ticket_images", []))})
    
    images = state.get("ticket_images", [])
    logger.info(f"{STEP_NAME} | 📥 Input: {len(images)} image(s) to process")

    if not images:
        duration = time.time() - start_time
        logger.info(f"{STEP_NAME} | ⏭ No images found - skipping ({duration:.2f}s)")
        return {
            "image_retrieval_results": [],
            "ran_vision": True,
            "audit_events": add_audit_event(
                state,
                "vision_pipeline",
                "INFO",
                {"image_count": 0, "results_count": 0}
            )["audit_events"]
        }

    logger.info(f"{STEP_NAME} | 🔄 Processing {len(images)} image(s)...")

    client = get_pinecone_client()
    top_k = settings.image_retrieval_top_k

    all_hits: List[RetrievalHit] = []

    for idx, img_url in enumerate(images, 1):
        try:
            logger.info(f"{STEP_NAME} | 🖼 [{idx}/{len(images)}] Embedding image: {img_url}")
            embed_start = time.time()

            vector = embed_image(img_url)
            embed_duration = time.time() - embed_start

            if not vector:
                logger.warning(f"{STEP_NAME} | ⚠ [{idx}] Failed embedding for: {img_url}")
                continue
            
            logger.info(f"{STEP_NAME} | ✓ [{idx}] Embedded in {embed_duration:.2f}s, vector dim={len(vector)}")

            query_start = time.time()
            hits = client.query_images(vector=vector, top_k=top_k)
            query_duration = time.time() - query_start
            
            logger.info(f"{STEP_NAME} | 🔍 [{idx}] Pinecone query returned {len(hits)} hits in {query_duration:.2f}s")
            all_hits.extend(hits)

        except Exception as e:
            logger.error(f"{STEP_NAME} | ❌ [{idx}] Error processing {img_url}: {e}", exc_info=True)

    # Deduplicate + sort
    all_hits = sorted(all_hits, key=lambda h: h["score"], reverse=True)

    # If multiple images → keep a reasonable number
    limit = max(top_k, len(images) * top_k)
    all_hits = all_hits[:limit]

    duration = time.time() - start_time
    top_scores = [f"{h.get('score', 0):.3f}" for h in all_hits[:3]]
    logger.info(f"{STEP_NAME} | ✅ Complete: {len(all_hits)} matches in {duration:.2f}s")
    logger.info(f"{STEP_NAME} | 📤 Top scores: {top_scores}")
    
    # Log detailed vision results for examination
    log_vision_results(node_log, all_hits)
    log_node_complete(
        node_log,
        output_summary={
            "total_matches": len(all_hits),
            "top_scores": top_scores,
            "duration_seconds": duration
        },
        retrieval_results=[{
            "rank": i+1,
            "score": h.get("score", 0),
            "product_id": h.get("metadata", {}).get("product_id", "N/A"),
            "product_name": h.get("metadata", {}).get("product_name", "N/A"),
            "image_name": h.get("metadata", {}).get("image_name", "N/A"),
            "category": h.get("metadata", {}).get("category", "N/A"),
            "full_metadata": h.get("metadata", {})
        } for i, h in enumerate(all_hits)]
    )

    return {
        "image_retrieval_results": all_hits,
        "ran_vision": True,
        "audit_events": add_audit_event(
            state,
            "vision_pipeline",
            "SUCCESS",
            {
                "image_count": len(images),
                "results_count": len(all_hits),
                "duration_seconds": duration
            }
        )["audit_events"]
    }
