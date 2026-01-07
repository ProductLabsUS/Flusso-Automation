"""
Workflow Log Shipper
Sends logs to centralized collector via HTTPS.

FINAL DESIGN PRINCIPLES:
1. Send logs immediately (reliable in cloud)
2. Short timeout (never hang request)
3. Fail silently (logging must not break workflow)
4. Simple & predictable behavior
"""

import logging
import os
from typing import Dict, Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

LOG_COLLECTOR_URL = os.getenv("LOG_COLLECTOR_URL", "")
LOG_COLLECTOR_API_KEY = os.getenv("LOG_COLLECTOR_API_KEY", "")
CLIENT_ID = os.getenv("CLIENT_ID", "unknown_client")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Timeouts (keep short)
REQUEST_TIMEOUT = 3.0   # total timeout
CONNECT_TIMEOUT = 2.0   # connection timeout


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

def ship_log(log_payload: Dict[str, Any]) -> None:
    """
    Send workflow log to centralized collector.

    - Executes synchronously
    - Uses short timeout
    - Never raises exceptions
    """

    if not LOG_COLLECTOR_URL:
        logger.debug("LOG_COLLECTOR_URL not set - skipping log shipping")
        return

    if not log_payload:
        logger.warning("Empty log payload - skipping log shipping")
        return

    ticket_id = log_payload.get("ticket_id", "unknown")

    try:
        _enrich_payload(log_payload)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"Flusso-Workflow/{log_payload.get('workflow_version', 'v1.0')}",
        }

        if LOG_COLLECTOR_API_KEY:
            headers["X-API-Key"] = LOG_COLLECTOR_API_KEY

        timeout = httpx.Timeout(
            timeout=REQUEST_TIMEOUT,
            connect=CONNECT_TIMEOUT
        )

        with httpx.Client(timeout=timeout) as client:
            logger.info(f"📤 Shipping log for ticket {ticket_id}")

            response = client.post(
                LOG_COLLECTOR_URL,
                json=log_payload,
                headers=headers
            )

            if response.status_code in (200, 201, 204):
                logger.info(f"✅ Log shipped successfully for ticket {ticket_id}")
            else:
                logger.warning(
                    f"⚠️ Log collector returned {response.status_code} "
                    f"for ticket {ticket_id}: {response.text[:200]}"
                )

    except httpx.TimeoutException:
        logger.warning(f"⏱️ Log shipping timed out for ticket {ticket_id}")

    except httpx.ConnectError as e:
        logger.warning(f"🔌 Cannot connect to log collector for ticket {ticket_id}: {e}")

    except httpx.HTTPError as e:
        logger.warning(f"📡 HTTP error shipping log for ticket {ticket_id}: {e}")

    except Exception as e:
        logger.error(
            f"❌ Unexpected error shipping log for ticket {ticket_id}: {e}",
            exc_info=True
        )


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _enrich_payload(log_payload: Dict[str, Any]) -> None:
    """
    Add standard metadata if missing.
    """
    log_payload.setdefault("client_id", CLIENT_ID)
    log_payload.setdefault("environment", ENVIRONMENT)


# -------------------------------------------------------------------
# Optional: connection test
# -------------------------------------------------------------------

def test_connection() -> bool:
    """
    Test if the log collector is reachable.
    """

    if not LOG_COLLECTOR_URL:
        logger.error("LOG_COLLECTOR_URL not configured")
        return False

    try:
        payload = {
            "client_id": CLIENT_ID,
            "environment": ENVIRONMENT,
            "test": True,
        }

        headers = {"Content-Type": "application/json"}
        if LOG_COLLECTOR_API_KEY:
            headers["X-API-Key"] = LOG_COLLECTOR_API_KEY

        timeout = httpx.Timeout(timeout=3.0, connect=2.0)

        with httpx.Client(timeout=timeout) as client:
            response = client.post(LOG_COLLECTOR_URL, json=payload, headers=headers)

        return response.status_code in (200, 201, 204)

    except Exception as e:
        logger.error(f"❌ Cannot reach log collector: {e}")
        return False


# -------------------------------------------------------------------
# Startup message
# -------------------------------------------------------------------

if __name__ != "__main__":
    if LOG_COLLECTOR_URL:
        logger.info(f"📝 Centralized logging configured: {LOG_COLLECTOR_URL}")
    else:
        logger.info("📝 Centralized logging disabled (LOG_COLLECTOR_URL not set)")






















# """
# Workflow Log Shipper
# Sends logs to centralized collector via HTTPS.

# KEY PRINCIPLES:
# 1. Never block the workflow
# 2. Fail silently
# 3. Fire-and-forget
# 4. Timeout quickly

# Usage:
#     ship_log_async(log_payload)  # Returns immediately
# """

# import logging
# import asyncio
# import os
# import json
# from typing import Dict, Any, Optional
# import httpx
# from dotenv import load_dotenv

# load_dotenv()

# logger = logging.getLogger(__name__)


# # Configuration from environment
# LOG_COLLECTOR_URL = os.getenv("LOG_COLLECTOR_URL", "")
# LOG_COLLECTOR_API_KEY = os.getenv("LOG_COLLECTOR_API_KEY", "")
# CLIENT_ID = os.getenv("CLIENT_ID", "unknown_client")
# ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# # Timeouts
# REQUEST_TIMEOUT = 10.0  # seconds - fail fast if collector is slow
# CONNECT_TIMEOUT = 5.0   # seconds - fail fast if can't connect


# def ship_log_async(log_payload: Dict[str, Any]) -> None:
#     """
#     Ship log to centralized collector (fire-and-forget).
    
#     This function returns IMMEDIATELY and does not block.
#     The actual HTTP request happens in the background.
    
#     Args:
#         log_payload: Complete log dictionary from build_workflow_log()
#     """
    
#     # Quick validation
#     if not LOG_COLLECTOR_URL:
#         logger.debug("LOG_COLLECTOR_URL not set - skipping log shipping")
#         return
    
#     if not log_payload:
#         logger.warning("Empty log payload - skipping log shipping")
#         return
    
#     # Create background task - this returns immediately
#     try:
#         # Get or create event loop
#         try:
#             loop = asyncio.get_running_loop()
#         except RuntimeError:
#             # No event loop running, create a new one
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
        
#         # Schedule the task to run in background
#         asyncio.create_task(_send_log_background(log_payload))
#         logger.debug(f"Scheduled log shipping for ticket {log_payload.get('ticket_id')}")
        
#     except Exception as e:
#         # If we can't even schedule the task, log and continue
#         logger.error(f"Failed to schedule log shipping: {e}")
#         # But DON'T raise - we never want logging to break the workflow


# async def _send_log_background(log_payload: Dict[str, Any]) -> None:
#     """
#     Background task that actually sends the log.
#     This runs asynchronously and won't block the main workflow.
    
#     ALL EXCEPTIONS are caught here - logging must never crash the workflow.
#     """
#     ticket_id = log_payload.get("ticket_id", "unknown")
    
#     try:
#         # Prepare the request
#         headers = {
#             "Content-Type": "application/json",
#             "User-Agent": f"Flusso-Workflow/{log_payload.get('workflow_version', 'v1.0')}",
#         }
        
#         # Add API key if configured
#         if LOG_COLLECTOR_API_KEY:
#             headers["X-API-Key"] = LOG_COLLECTOR_API_KEY
        
#         # Add client ID to payload if not already there
#         if "client_id" not in log_payload:
#             log_payload["client_id"] = CLIENT_ID
#         if "environment" not in log_payload:
#             log_payload["environment"] = ENVIRONMENT
        
#         # Create async HTTP client with timeouts
#         timeout_config = httpx.Timeout(
#             timeout=REQUEST_TIMEOUT,
#             connect=CONNECT_TIMEOUT
#         )
        
#         async with httpx.AsyncClient(timeout=timeout_config) as client:
#             logger.info(f"📤 Shipping log for ticket {ticket_id} to {LOG_COLLECTOR_URL}")
            
#             response = await client.post(
#                 LOG_COLLECTOR_URL,
#                 json=log_payload,
#                 headers=headers
#             )
            
#             # Check response
#             if response.status_code == 200 or response.status_code == 201:
#                 logger.info(f"✅ Log shipped successfully for ticket {ticket_id}")
#             else:
#                 logger.warning(
#                     f"⚠️ Log collector returned status {response.status_code} for ticket {ticket_id}: {response.text[:200]}"
#                 )
                
#     except asyncio.TimeoutError:
#         logger.warning(f"⏱️ Timeout shipping log for ticket {ticket_id} (collector not responding)")
        
#     except httpx.ConnectError as e:
#         logger.warning(f"🔌 Cannot connect to log collector for ticket {ticket_id}: {e}")
        
#     except httpx.HTTPError as e:
#         logger.warning(f"📡 HTTP error shipping log for ticket {ticket_id}: {e}")
        
#     except json.JSONEncodeError as e:
#         logger.error(f"📋 Invalid JSON in log payload for ticket {ticket_id}: {e}")
        
#     except Exception as e:
#         # Catch-all: log the error but never raise
#         logger.error(f"❌ Unexpected error shipping log for ticket {ticket_id}: {e}", exc_info=True)
    
#     # No return value - fire-and-forget


# def ship_log_sync(log_payload: Dict[str, Any]) -> bool:
#     """
#     Synchronous version of log shipping (for testing or special cases).
    
#     This WILL BLOCK until the request completes or times out.
#     Only use this if you specifically need synchronous behavior.
    
#     Returns:
#         True if log was sent successfully, False otherwise
#     """
    
#     if not LOG_COLLECTOR_URL:
#         logger.debug("LOG_COLLECTOR_URL not set - skipping log shipping")
#         return False
    
#     if not log_payload:
#         logger.warning("Empty log payload - skipping log shipping")
#         return False
    
#     ticket_id = log_payload.get("ticket_id", "unknown")
    
#     try:
#         # Prepare the request
#         headers = {
#             "Content-Type": "application/json",
#             "User-Agent": f"Flusso-Workflow/{log_payload.get('workflow_version', 'v1.0')}",
#         }
        
#         if LOG_COLLECTOR_API_KEY:
#             headers["X-API-Key"] = LOG_COLLECTOR_API_KEY
        
#         # Add client ID to payload if not already there
#         if "client_id" not in log_payload:
#             log_payload["client_id"] = CLIENT_ID
#         if "environment" not in log_payload:
#             log_payload["environment"] = ENVIRONMENT
        
#         # Create sync HTTP client with timeouts
#         timeout_config = httpx.Timeout(
#             timeout=REQUEST_TIMEOUT,
#             connect=CONNECT_TIMEOUT
#         )
        
#         with httpx.Client(timeout=timeout_config) as client:
#             logger.info(f"📤 Shipping log for ticket {ticket_id} to {LOG_COLLECTOR_URL} (sync)")
            
#             response = client.post(
#                 LOG_COLLECTOR_URL,
#                 json=log_payload,
#                 headers=headers
#             )
            
#             if response.status_code == 200 or response.status_code == 201:
#                 logger.info(f"✅ Log shipped successfully for ticket {ticket_id}")
#                 return True
#             else:
#                 logger.warning(
#                     f"⚠️ Log collector returned status {response.status_code} for ticket {ticket_id}: {response.text[:200]}"
#                 )
#                 return False
                
#     except Exception as e:
#         logger.error(f"❌ Error shipping log for ticket {ticket_id}: {e}", exc_info=True)
#         return False


# def test_connection() -> bool:
#     """
#     Test if the log collector is reachable.
    
#     Returns:
#         True if collector responds, False otherwise
#     """
    
#     if not LOG_COLLECTOR_URL:
#         logger.error("LOG_COLLECTOR_URL not configured")
#         return False
    
#     try:
#         # Send a minimal test payload
#         test_payload = {
#             "client_id": CLIENT_ID,
#             "environment": ENVIRONMENT,
#             "test": True,
#             "ticket_id": "test_connection"
#         }
        
#         headers = {
#             "Content-Type": "application/json",
#         }
        
#         if LOG_COLLECTOR_API_KEY:
#             headers["X-API-Key"] = LOG_COLLECTOR_API_KEY
        
#         timeout_config = httpx.Timeout(timeout=5.0, connect=3.0)
        
#         with httpx.Client(timeout=timeout_config) as client:
#             response = client.post(
#                 LOG_COLLECTOR_URL,
#                 json=test_payload,
#                 headers=headers
#             )
            
#             if response.status_code in [200, 201, 204]:
#                 logger.info(f"✅ Log collector is reachable at {LOG_COLLECTOR_URL}")
#                 return True
#             else:
#                 logger.warning(f"⚠️ Log collector returned status {response.status_code}")
#                 return False
                
#     except Exception as e:
#         logger.error(f"❌ Cannot reach log collector: {e}")
#         return False


# # Configuration check on module import
# if __name__ != "__main__":
#     if not LOG_COLLECTOR_URL:
#         logger.info("📝 Centralized logging not configured (LOG_COLLECTOR_URL not set)")
#     else:
#         logger.info(f"📝 Centralized logging configured: {LOG_COLLECTOR_URL}")
