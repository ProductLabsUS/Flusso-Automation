"""
Customer Lookup Node
Identifies customer type and basic metadata from email and tags.
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.config.constants import CustomerType

logger = logging.getLogger(__name__)
STEP_NAME = "6️⃣ CUSTOMER_LOOKUP"


def identify_customer_type(state: TicketState) -> Dict[str, Any]:
    """
    Determine customer type (VIP / NORMAL / etc.) based on:
      - email domain
      - ticket tags

    Returns:
        Partial state update with:
            - customer_type
            - customer_metadata
            - audit_events
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Starting customer type identification")
    
    email = state.get("requester_email", "") or ""
    tags = state.get("tags", []) or []

    logger.info(f"{STEP_NAME} | 📥 Input: email='{email}', tags={tags}")

    customer_metadata: Dict[str, Any] = {"email": email}
    customer_type = CustomerType.NORMAL.value
    detection_reason = "default"

    # Simple VIP detection by domain (customize for your tenant)
    vip_domains = ["@company.com", "@distributor.com"]
    if any(d.lower() in email.lower() for d in vip_domains):
        customer_type = CustomerType.VIP.value
        customer_metadata["account_tier"] = "VIP"
        detection_reason = f"VIP domain match: {email}"

    # VIP tag-based detection
    tags_lower = [t.lower() for t in tags]
    if "vip" in tags_lower:
        customer_type = CustomerType.VIP.value
        customer_metadata["account_tier"] = "VIP"
        detection_reason = "VIP tag present"

    duration = time.time() - start_time
    logger.info(f"{STEP_NAME} | 🎯 Decision: customer_type='{customer_type}' (reason: {detection_reason})")
    logger.info(f"{STEP_NAME} | ✅ Complete in {duration:.2f}s")

    audit_events = state.get("audit_events", []) or []
    audit_events.append(
        {
            "event": "identify_customer_type",
            "customer_type": customer_type,
            "email": email,
            "tags_used": tags,
            "detection_reason": detection_reason,
        }
    )

    return {
        "customer_type": customer_type,
        "customer_metadata": customer_metadata,
        "audit_events": audit_events,
    }
