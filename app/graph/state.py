"""
State Model for LangGraph Workflow
Defines the complete state structure for ticket processing
"""

from typing import TypedDict, List, Dict, Any, Optional


class RetrievalHit(TypedDict):
    """Single retrieval result from vector database or file search."""
    id: str
    score: float
    metadata: Dict[str, Any]
    content: str  # Text chunk, product info, or ticket summary


class TicketState(TypedDict, total=False):
    """
    Complete state object passed between all LangGraph nodes.
    Each node reads from and updates this state.
    """

    # ==========================================
    # RAW TICKET INFO
    # ==========================================
    ticket_id: str
    ticket_subject: str
    ticket_text: str  # Includes description + extracted attachment content
    ticket_images: List[str]
    requester_email: str
    requester_name: str
    ticket_type: Optional[str]
    priority: Optional[str]
    tags: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    ticket_conversation: List[Dict[str, Any]]  # OPTIONAL but recommended
    
    # ==========================================
    # ATTACHMENT INFO
    # ==========================================
    attachment_summary: List[Dict[str, Any]]  # List of processed attachments with metadata

    # ==========================================
    # RAG EXECUTION FLAGS (REQUIRED!)
    # ==========================================
    ran_vision: bool
    ran_text_rag: bool
    ran_past_tickets: bool

    # ==========================================
    # CLASSIFICATION / ROUTING
    # ==========================================
    ticket_category: Optional[str]
    has_text: bool
    has_image: bool

    # ==========================================
    # CUSTOMER PROFILE / RULES
    # ==========================================
    customer_type: Optional[str]
    customer_metadata: Dict[str, Any]
    vip_rules: Dict[str, Any]

    # ==========================================
    # RAG RESULTS
    # ==========================================
    text_retrieval_results: List[RetrievalHit]
    image_retrieval_results: List[RetrievalHit]
    past_ticket_results: List[RetrievalHit]
    multimodal_context: str

    # ==========================================
    # PRODUCT / DECISION METRICS
    # ==========================================
    detected_product_id: Optional[str]   # OPTIONAL but recommended
    product_match_confidence: float
    hallucination_risk: float
    enough_information: bool
    vip_compliant: bool
    overall_confidence: float  # Combined confidence score (0-100%)

    # ==========================================
    # LLM OUTPUTS
    # ==========================================
    clarification_message: Optional[str]
    draft_response: Optional[str]

    # ==========================================
    # FINAL OUTCOME
    # ==========================================
    final_response_public: Optional[str]
    final_private_note: Optional[str]
    resolution_status: Optional[str]
    extra_tags: List[str]

    # ==========================================
    # AUDIT TRAIL
    # ==========================================
    audit_events: List[Dict[str, Any]]
