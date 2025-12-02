"""
FastAPI Main Application
Webhook endpoint for Freshdesk ticket automation
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.graph.graph_builder import build_graph
from app.graph.state import TicketState

# ---------------------------------------------------
# LOGGING CONFIG
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

graph = None  # Global graph instance


# ---------------------------------------------------
# LIFESPAN HOOKS
# ---------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    logger.info("🚀 Starting Flusso Workflow Automation...")

    graph = build_graph()
    logger.info("✅ LangGraph workflow initialized")

    yield

    logger.info("🛑 Shutting down Flusso Workflow Automation...")


# ---------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------
app = FastAPI(
    title="Flusso Workflow Automation",
    description="Multimodal RAG for Freshdesk ticket automation",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Freshdesk webhook calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Freshdesk uses public IPs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# HEALTH ENDPOINTS
# ---------------------------------------------------
@app.get("/")
async def root():
    return {
        "service": "Flusso Workflow Automation",
        "status": "running",
        "graph_initialized": graph is not None,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "graph_ready": graph is not None,
        "service": "Flusso Workflow Automation",
    }


# ---------------------------------------------------
# FRESHDESK WEBHOOK
# ---------------------------------------------------
@app.post("/freshdesk/webhook")
async def freshdesk_webhook(request: Request):
    """
    Freshdesk webhook endpoint
    Receives ticket creation/update events.

    Expected payload:
    {
        "ticket_id": 12345,
        "freshdesk_webhook": {...}
    }
    """

    global graph
    if graph is None:
        logger.warning("⚠ Graph was not initialized — rebuilding...")
        graph = build_graph()

    try:
        payload = await request.json()
        logger.info(f"📨 Received webhook: {payload}")

        ticket_id = payload.get("ticket_id")
        if not ticket_id:
            raise HTTPException(status_code=400, detail="Missing ticket_id in payload")

        # ---------------------------------------------------
        # Initialize minimal safe TicketState
        # ALL REQUIRED FIELDS MUST EXIST
        # ---------------------------------------------------

        initial_state: TicketState = {
            "ticket_id": str(ticket_id),

            # Raw incoming data (optional field)
            "freshdesk_webhook_payload": payload,

            # Required defaults for workflow stability
            "ticket_subject": "",
            "ticket_text": "",
            "ticket_images": [],
            "requester_email": "",
            "requester_name": "",
            "ticket_type": None,
            "priority": None,
            "tags": [],
            "created_at": None,
            "updated_at": None,

            # Routing flags
            "has_text": False,
            "has_image": False,

            # Customer info
            "customer_type": None,
            "customer_metadata": {},
            "vip_rules": {},

            # RAG results
            "text_retrieval_results": [],
            "image_retrieval_results": [],
            "past_ticket_results": [],
            "multimodal_context": "",

            # Decision values
            "product_match_confidence": 0.0,
            "hallucination_risk": 0.0,
            "enough_information": False,
            "vip_compliant": True,

            # Response
            "clarification_message": None,
            "draft_response": None,
            "final_response_public": None,
            "final_private_note": None,
            "resolution_status": None,
            "extra_tags": [],

            # Audit trail
            "audit_events": [
                {"event": "webhook_received", "ticket_id": ticket_id}
            ],
        }

        logger.info(f"🔄 Starting workflow for ticket #{ticket_id}")

        final_state = graph.invoke(initial_state)

        result = {
            "ticket_id": ticket_id,
            "resolution_status": final_state.get("resolution_status"),
            "category": final_state.get("ticket_category"),
            "customer_type": final_state.get("customer_type"),
            "tags": final_state.get("tags"),
            "workflow_completed": True,
        }

        logger.info(
            f"✅ Workflow completed for ticket #{ticket_id}: {result['resolution_status']}"
        )

        return JSONResponse(content=result, status_code=200)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Workflow error: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e), "workflow_completed": False},
            status_code=500,
        )


# ---------------------------------------------------
# LOCAL DEV ENTRY POINT
# ---------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
