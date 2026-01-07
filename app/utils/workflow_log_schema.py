"""
Workflow Log Schema
Defines the structure for centralized logging.

This module defines EXACTLY what gets sent to the log collector API.
Following the principle: "One Ticket = One Log"
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import hashlib


@dataclass
class WorkflowLogSchema:
    """
    Complete log structure for one ticket execution.
    This is what gets sent to the centralized logging API.
    """

    # ==========================================
    # IDENTIFICATION (queryable)
    # ==========================================
    client_id: str
    environment: str
    workflow_version: str

    # ==========================================
    # TICKET INFO (queryable)
    # ==========================================
    ticket_id: str
    ticket_subject_hash: str
    executed_at: str
    execution_time_seconds: float

    # ==========================================
    # OUTCOME (queryable)
    # ==========================================
    status: str  # "SUCCESS" | "PARTIAL" | "FAILED" | "ERROR"
    requester_email_hash: str

    # ==========================================
    # OPTIONAL OUTCOME CONTEXT
    # ==========================================
    category: Optional[str] = None
    resolution_status: Optional[str] = None
    customer_type: Optional[str] = None

    # ==========================================
    # METRICS (queryable)
    # ==========================================
    metrics: Dict[str, Any] = field(default_factory=dict)

    # ==========================================
    # ERROR TRACKING
    # ==========================================
    workflow_error: Optional[str] = None
    workflow_error_type: Optional[str] = None
    workflow_error_node: Optional[str] = None
    is_system_error: bool = False

    # ==========================================
    # PAYLOAD (non-queryable, detailed data)
    # ==========================================
    payload: Dict[str, Any] = field(default_factory=dict)
    # Contains:
    # - trace
    # - final_response
    # - private_note (optional)

    # ==========================================
    # METADATA
    # ==========================================
    metadata: Dict[str, Any] = field(default_factory=dict)


def hash_pii(value: str) -> str:
    """Hash sensitive information for privacy."""
    if not value:
        return "unknown"
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def sanitize_trace(trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove or hash PII from trace data before shipping."""
    sanitized = trace_data.copy()

    sensitive_keys = [
        "password", "api_key", "freshdesk_api_key", "gemini_api_key",
        "pinecone_api_key", "openai_api_key", "credit_card", "ssn"
    ]
    for key in sensitive_keys:
        if key in sanitized:
            sanitized[key] = "[REDACTED]"

    pii_keys = ["requester_email", "requester_name", "customer_email"]
    for key in pii_keys:
        if key in sanitized and sanitized[key]:
            sanitized[key] = hash_pii(str(sanitized[key]))

    return sanitized


def to_json_safe(data: Any) -> Any:
    """Convert dataclass or complex objects to JSON-safe dicts."""
    if hasattr(data, "__dataclass_fields__"):
        return asdict(data)
    if isinstance(data, dict):
        return {k: to_json_safe(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [to_json_safe(v) for v in data]
    return data
