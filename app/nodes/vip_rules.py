"""
VIP Rules Node
Loads applicable VIP / Distributor / Internal rules based on customer type.
"""

import logging
import time
from typing import Dict, Any

from app.graph.state import TicketState
from app.utils.audit import add_audit_event
from app.config.constants import CustomerType

logger = logging.getLogger(__name__)
STEP_NAME = "7️⃣ VIP_RULES"


def load_vip_rules(state: TicketState) -> Dict[str, Any]:
    """
    Load special rule sets for customers depending on customer_type.

    Supported categories:
      - VIP
      - DISTRIBUTOR
      - INTERNAL
      - NORMAL
    """
    start_time = time.time()
    logger.info(f"{STEP_NAME} | ▶ Starting VIP rules lookup")

    customer_type = state.get("customer_type", CustomerType.NORMAL.value)
    customer_type = str(customer_type).upper().strip()

    logger.info(f"{STEP_NAME} | 📥 Input: customer_type='{customer_type}'")

    rules: Dict[str, Any] = {}

    # ----------------------- VIP CUSTOMERS -----------------------
    if customer_type == CustomerType.VIP.value:
        rules = {
            "warranty_extension_months": 6,
            "allow_free_replacement": True,
            "priority_shipping": True,
            "response_time_sla_hours": 4,
            "dedicated_support": True,
            "max_discount_percent": 20,
        }
        logger.info(f"{STEP_NAME} | 🌟 VIP rules applied: {list(rules.keys())}")

    # ----------------------- DISTRIBUTORS ------------------------
    elif customer_type == CustomerType.DISTRIBUTOR.value:
        rules = {
            "bulk_discount_eligible": True,
            "extended_return_window_days": 60,
            "priority_shipping": True,
            "response_time_sla_hours": 8,
            "max_discount_percent": 15,
        }
        logger.info(f"{STEP_NAME} | 🏭 Distributor rules applied: {list(rules.keys())}")

    # ----------------------- INTERNAL USERS -----------------------
    elif customer_type == CustomerType.INTERNAL.value:
        rules = {
            "bypass_warranty_validation": True,
            "allow_internal_replacement": True,
            "debug_mode_enabled": True,
        }
        logger.info(f"{STEP_NAME} | 🏢 Internal rules applied: {list(rules.keys())}")

    # ----------------------- NORMAL CUSTOMERS ----------------------
    else:
        logger.info(f"{STEP_NAME} | 👤 Standard customer → no special rules")

    duration = time.time() - start_time
    logger.info(f"{STEP_NAME} | ✅ Complete in {duration:.2f}s (rules_count={len(rules)})")

    # ----------------------- AUDIT LOG -----------------------------
    audit_events = add_audit_event(
        state,
        "load_vip_rules",
        "RULES",
        {"customer_type": customer_type, "rules_present": bool(rules), "rule_keys": list(rules.keys())},
    )["audit_events"]

    return {"vip_rules": rules, "audit_events": audit_events}
