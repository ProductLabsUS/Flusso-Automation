"""
LangGraph Builder
Constructs complete workflow with corrected multimodal RAG loop
"""

import logging
from typing import Literal
from langgraph.graph import StateGraph, END

from app.graph.state import TicketState

# Import all nodes
from app.nodes.fetch_ticket import fetch_ticket_from_freshdesk
from app.nodes.routing_agent import classify_ticket_category
from app.nodes.vision_pipeline import process_vision_pipeline
from app.nodes.text_rag_pipeline import text_rag_pipeline
from app.nodes.past_tickets import retrieve_past_tickets
from app.nodes.customer_lookup import identify_customer_type
from app.nodes.vip_rules import load_vip_rules
from app.nodes.context_builder import assemble_multimodal_context
from app.nodes.orchestration_agent import orchestration_agent
from app.nodes.decisions.enough_information import check_enough_information
from app.nodes.decisions.hallucination_guard import assess_hallucination_risk
from app.nodes.decisions.confidence_check import evaluate_product_confidence
from app.nodes.decisions.vip_compliance import verify_vip_compliance
from app.nodes.response.draft_response import draft_final_response
from app.nodes.response.resolution_logic import decide_tags_and_resolution
from app.nodes.freshdesk_update import update_freshdesk_ticket
from app.nodes.audit_log import write_audit_log

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
#  CORRECT MULTIMODAL RAG ROUTER
# ---------------------------------------------------------------------
def route_after_routing(state: TicketState) -> Literal[
    "vision", "text_rag", "past_tickets", "customer_lookup"
]:
    """
    Multimodal RAG controller:
        - Run all relevant pipelines in sequence
        - Only move to customer lookup when ALL applicable RAGs done
    """

    has_image = state.get("has_image", False)
    has_text = state.get("has_text", False)

    ran_vision = state.get("ran_vision", False)
    ran_text = state.get("ran_text_rag", False)
    ran_past = state.get("ran_past_tickets", False)

    # 1. Run vision first if images exist
    if has_image and not ran_vision:
        logger.info("[ROUTER] Running vision pipeline")
        return "vision"

    # 2. Then run text RAG if text exists
    if has_text and not ran_text:
        logger.info("[ROUTER] Running text RAG pipeline")
        return "text_rag"

    # 3. Always check past tickets (once)
    if not ran_past:
        logger.info("[ROUTER] Searching past tickets")
        return "past_tickets"

    # 4. If all RAG done → proceed
    logger.info("[ROUTER] All RAG pipelines completed → customer lookup")
    return "customer_lookup"


# ---------------------------------------------------------------------
#  ORCHESTRATION ROUTING
# ---------------------------------------------------------------------
def route_after_orchestration(
    state: TicketState,
) -> Literal["check_enough_info", "vision", "text_rag", "past_tickets"]:
    """
    If not enough information after orchestration,
    re-run the missing RAG modes before continuing.
    """

    enough = state.get("enough_information", False)
    if enough:
        logger.info("[ROUTER] Orchestration: enough info → proceed to checks")
        return "check_enough_info"

    # If not enough info → run missing RAG
    has_image = state.get("has_image", False)
    has_text = state.get("has_text", False)
    ran_vision = state.get("ran_vision", False)
    ran_text = state.get("ran_text_rag", False)
    ran_past = state.get("ran_past_tickets", False)

    if has_image and not ran_vision:
        return "vision"
    if has_text and not ran_text:
        return "text_rag"
    if not ran_past:
        return "past_tickets"

    # If all RAG already done
    return "check_enough_info"


# ---------------------------------------------------------------------
#  ENOUGH INFORMATION ROUTING
# ---------------------------------------------------------------------
def route_after_enough_info_check(
    state: TicketState,
) -> Literal["hallucination_guard", "draft_response"]:
    """
    If still not enough info → go straight to draft (ask for more details)
    """
    if state.get("enough_information", False):
        logger.info("[ROUTER] Enough information → hallucination guard")
        return "hallucination_guard"

    logger.info("[ROUTER] Not enough information → draft clarification response")
    return "draft_response"


# ---------------------------------------------------------------------
#  HALLUCINATION GUARD ROUTING
# ---------------------------------------------------------------------
def route_after_hallucination_guard(
    state: TicketState,
) -> Literal["confidence_check", "draft_response"]:
    from app.config.settings import settings
    
    risk = state.get("hallucination_risk", 1.0)
    threshold = settings.hallucination_risk_threshold

    if risk <= threshold:
        logger.info(f"[ROUTER] Low hallucination risk ({risk:.2f} <= {threshold}) → confidence check")
        return "confidence_check"

    logger.info(f"[ROUTER] High hallucination risk ({risk:.2f} > {threshold}) → draft fallback")
    return "draft_response"


# ---------------------------------------------------------------------
#  BUILD THE FINAL GRAPH
# ---------------------------------------------------------------------
def build_graph() -> StateGraph:
    logger.info("[GRAPH_BUILDER] Building LangGraph workflow...")

    graph = StateGraph(TicketState)

    # ------------------- ADD NODES -------------------
    graph.add_node("fetch_ticket", fetch_ticket_from_freshdesk)
    graph.add_node("routing", classify_ticket_category)

    graph.add_node("vision", process_vision_pipeline)
    graph.add_node("text_rag", text_rag_pipeline)
    graph.add_node("past_tickets", retrieve_past_tickets)

    graph.add_node("customer_lookup", identify_customer_type)
    graph.add_node("vip_rules", load_vip_rules)
    graph.add_node("context_builder", assemble_multimodal_context)

    graph.add_node("orchestration", orchestration_agent)
    graph.add_node("check_enough_info", check_enough_information)

    graph.add_node("hallucination_guard", assess_hallucination_risk)
    graph.add_node("confidence_check", evaluate_product_confidence)
    graph.add_node("vip_compliance", verify_vip_compliance)

    graph.add_node("draft_response", draft_final_response)
    graph.add_node("resolution_logic", decide_tags_and_resolution)
    graph.add_node("freshdesk_update", update_freshdesk_ticket)
    graph.add_node("audit_log", write_audit_log)

    # ------------------- ENTRY POINT -------------------
    graph.set_entry_point("fetch_ticket")

    # ------------------- BASE FLOW -------------------
    graph.add_edge("fetch_ticket", "routing")

    # ------------------- MULTIMODAL RAG LOOP -------------------
    graph.add_conditional_edges(
        "routing",
        route_after_routing,
        {
            "vision": "vision",
            "text_rag": "text_rag",
            "past_tickets": "past_tickets",
            "customer_lookup": "customer_lookup",
        },
    )

    # After vision/text/past → go back to routing for next step
    graph.add_edge("vision", "routing")
    graph.add_edge("text_rag", "routing")
    graph.add_edge("past_tickets", "routing")

    # ------------------- AFTER ALL RAG -------------------
    graph.add_edge("customer_lookup", "vip_rules")
    graph.add_edge("vip_rules", "context_builder")
    graph.add_edge("context_builder", "orchestration")

    # ------------------- ORCHESTRATION ROUTING -------------------
    graph.add_conditional_edges(
        "orchestration",
        route_after_orchestration,
        {
            "check_enough_info": "check_enough_info",
            "vision": "vision",
            "text_rag": "text_rag",
            "past_tickets": "past_tickets",
        },
    )

    # ------------------- ENOUGH INFO ROUTING -------------------
    graph.add_conditional_edges(
        "check_enough_info",
        route_after_enough_info_check,
        {
            "hallucination_guard": "hallucination_guard",
            "draft_response": "draft_response",
        },
    )

    # ------------------- HALLUCINATION ROUTING -------------------
    graph.add_conditional_edges(
        "hallucination_guard",
        route_after_hallucination_guard,
        {
            "confidence_check": "confidence_check",
            "draft_response": "draft_response",
        },
    )

    # ------------------- CONFIDENCE → VIP → DRAFT -------------------
    graph.add_edge("confidence_check", "vip_compliance")
    graph.add_edge("vip_compliance", "draft_response")

    # ------------------- FINAL CHAIN -------------------
    graph.add_edge("draft_response", "resolution_logic")
    graph.add_edge("resolution_logic", "freshdesk_update")
    graph.add_edge("freshdesk_update", "audit_log")
    graph.add_edge("audit_log", END)

    # ------------------- COMPILE -------------------
    compiled_graph = graph.compile()
    logger.info("[GRAPH_BUILDER] Graph compiled successfully")

    return compiled_graph
