# PROJECT CONTEXT & TECHNICAL GUIDE

## 🎯 PROJECT OVERVIEW

**Flusso Workflow** is a production-ready LangGraph-based automated Freshdesk support system with multimodal RAG capabilities. The system automatically processes customer support tickets using text and image analysis, retrieves relevant knowledge from multiple sources, and generates intelligent responses.

---

## 🏗️ SYSTEM ARCHITECTURE

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRESHDESK WEBHOOK                                │
│                    POST /webhook {ticket_id: 42}                         │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         LANGGRAPH WORKFLOW                               │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐   │
│  │ fetch_ticket │───▶│routing_agent │───▶│ PARALLEL RETRIEVAL       │   │
│  └──────────────┘    └──────────────┘    │  ├─ vision_pipeline      │   │
│                                          │  ├─ text_rag_pipeline    │   │
│                                          │  └─ past_tickets         │   │
│                                          └────────────┬─────────────┘   │
│                                                       │                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    CUSTOMER & CONTEXT                             │   │
│  │  customer_lookup → vip_rules → context_builder → orchestration   │   │
│  └──────────────────────────────────────────────────┬───────────────┘   │
│                                                      │                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      DECISION GATES                               │   │
│  │  enough_info → hallucination_guard → confidence → vip_compliance │   │
│  └──────────────────────────────────────────────────┬───────────────┘   │
│                                                      │                   │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    RESPONSE & OUTPUT                              │   │
│  │  draft_response → resolution_logic → freshdesk_update → audit    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | LangGraph | 17-node workflow with conditional routing |
| **API** | FastAPI | Webhook endpoint & health check |
| **LLM** | Gemini 2.0 Flash | Classification, analysis, response generation |
| **Image Embeddings** | CLIP ViT-B-32 | 512-dimensional image vectors |
| **Text Embeddings** | Gemini text-embedding-004 | 768-dimensional text vectors |
| **Vector Search** | Pinecone | Product images + past tickets indexes |
| **Document Search** | Gemini File Search | Product manuals, FAQs, policies |
| **Ticketing** | Freshdesk REST API | Ticket fetch, update, notes |

---

## 📊 DATA SOURCES

### 1. Gemini File Search Store
- **Purpose**: Text-based document retrieval
- **Contents**: Product manuals, FAQs, warranty policies, installation guides
- **Store ID**: Configured via `GEMINI_FILE_SEARCH_STORE_ID`
- **Query Method**: Natural language queries via Gemini API

### 2. Pinecone Image Index
- **Purpose**: Visual product matching
- **Index Name**: Configured via `PINECONE_IMAGE_INDEX` (default: `flusso-vision-index`)
- **Embedding Model**: CLIP ViT-B-32 (512 dimensions)
- **Metadata Fields**:
  - `product_id` - SKU/product identifier
  - `product_name` - Human-readable name
  - `collection` - Product category
  - `common_groups` - Related product groups
  - `image_url` - Original image URL

### 3. Pinecone Tickets Index
- **Purpose**: Similar past ticket retrieval
- **Index Name**: Configured via `PINECONE_TICKETS_INDEX` (default: `freshdesk-support-tickets`)
- **Embedding Model**: Gemini text-embedding-004 (768 dimensions)
- **Metadata Fields**:
  - `ticket_id` - Original Freshdesk ticket ID
  - `subject` - Ticket subject line
  - `status` - Resolution status
  - `priority` - Ticket priority
  - `char_count` - Content length

---

## 🔧 NODE IMPLEMENTATIONS

### Data Acquisition Nodes

| Node | File | Function | Key Operations |
|------|------|----------|----------------|
| `fetch_ticket` | `nodes/fetch_ticket.py` | `fetch_ticket_details()` | Fetch ticket from Freshdesk, extract text/images/attachments |
| `routing_agent` | `nodes/routing_agent.py` | `routing_agent()` | LLM classifies ticket into categories |
| `vision_pipeline` | `nodes/vision_pipeline.py` | `vision_pipeline()` | CLIP embed images → Pinecone query |
| `text_rag_pipeline` | `nodes/text_rag_pipeline.py` | `text_rag_pipeline()` | Gemini File Search for documentation |
| `past_tickets` | `nodes/past_tickets.py` | `retrieve_past_tickets()` | Gemini embed text → Pinecone past tickets |

### Customer & Context Nodes

| Node | File | Function | Key Operations |
|------|------|----------|----------------|
| `customer_lookup` | `nodes/customer_lookup.py` | `get_customer_type()` | Detect VIP/DISTRIBUTOR/INTERNAL/NORMAL |
| `vip_rules` | `nodes/vip_rules.py` | `load_vip_rules()` | Load applicable rules for customer type |
| `context_builder` | `nodes/context_builder.py` | `build_multimodal_context()` | Combine all retrieval results |
| `orchestration_agent` | `nodes/orchestration_agent.py` | `orchestration_agent()` | Analyze resolution feasibility |

### Decision Nodes

| Node | File | Function | Key Operations |
|------|------|----------|----------------|
| `enough_information` | `decisions/enough_information.py` | `enough_information_decider()` | Check if enough context to respond |
| `hallucination_guard` | `decisions/hallucination_guard.py` | `hallucination_guard()` | Assess fabrication risk (0-1 score) |
| `confidence_check` | `decisions/confidence_check.py` | `product_match_confidence_check()` | Verify product identification |
| `vip_compliance` | `decisions/vip_compliance.py` | `vip_compliance_check()` | Ensure VIP rules satisfied |

### Response Nodes

| Node | File | Function | Key Operations |
|------|------|----------|----------------|
| `draft_response` | `response/draft_response.py` | `draft_final_response()` | Generate HTML response with confidence header |
| `resolution_logic` | `response/resolution_logic.py` | `decide_tags_and_resolution()` | Set status, tags, final response |
| `freshdesk_update` | `nodes/freshdesk_update.py` | `update_freshdesk_ticket()` | Post note & update ticket in Freshdesk |
| `audit_log` | `nodes/audit_log.py` | `write_audit_log()` | Write complete audit trail to file |

---

## 📋 STATE MODEL

The `TicketState` TypedDict contains 30+ fields organized by purpose:

```python
class TicketState(TypedDict, total=False):
    # === TICKET DATA ===
    ticket_id: int
    ticket_subject: str
    ticket_text: str
    ticket_images: List[str]        # Image URLs from attachments
    requester_email: str
    requester_name: str
    priority: int
    tags: List[str]
    created_at: str
    updated_at: str
    
    # === CLASSIFICATION ===
    ticket_category: str            # install_help, product_inquiry, etc.
    has_text: bool
    has_image: bool
    ran_vision: bool
    ran_text_rag: bool
    ran_past_tickets: bool
    
    # === CUSTOMER DATA ===
    customer_type: str              # VIP, DISTRIBUTOR, INTERNAL, NORMAL
    customer_metadata: Dict[str, Any]
    vip_rules: Dict[str, Any]
    
    # === RETRIEVAL RESULTS ===
    text_retrieval_results: List[Dict]
    image_retrieval_results: List[Dict]
    past_ticket_results: List[Dict]
    multimodal_context: str         # Combined context for LLM
    
    # === DECISION METRICS ===
    enough_information: bool
    hallucination_risk: float       # 0.0 - 1.0
    product_match_confidence: float # 0.0 - 1.0
    vip_compliant: bool
    overall_confidence: float       # Computed percentage
    
    # === OUTPUT ===
    draft_response: str             # HTML formatted response
    final_response_public: str
    resolution_status: str          # RESOLVED, AI_UNRESOLVED, etc.
    extra_tags: List[str]
    
    # === AUDIT ===
    audit_events: List[Dict]        # Event trail
```

---

## 🔐 CONFIGURATION

### Environment Variables

```env
# Freshdesk
FRESHDESK_DOMAIN=your-company.freshdesk.com
FRESHDESK_API_KEY=your_api_key

# Pinecone
PINECONE_API_KEY=your_api_key
PINECONE_ENV=us-east-1
PINECONE_IMAGE_INDEX=flusso-vision-index
PINECONE_TICKETS_INDEX=freshdesk-support-tickets

# Gemini
GEMINI_API_KEY=your_api_key
GEMINI_FILE_SEARCH_STORE_ID=your_store_id

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Thresholds

| Setting | Value | Purpose |
|---------|-------|---------|
| `hallucination_risk_threshold` | 0.7 | Max risk before escalation |
| `product_confidence_threshold` | 0.4 | Min confidence for product match |
| `vision_top_k` | 5 | Image search results count |
| `text_rag_top_k` | 10 | Document search results count |
| `past_tickets_top_k` | 5 | Similar tickets count |

---

## 📊 RESPONSE FORMATTING

### HTML Confidence Header

Responses include a styled confidence indicator:

```html
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); 
            border-radius: 8px; padding: 16px; margin-bottom: 20px;">
    <div style="display: flex; align-items: center;">
        <span>📊</span>
        <span style="color: white; font-weight: bold;">AI CONFIDENCE:</span>
        <span style="background: #22c55e; color: white; padding: 4px 12px; 
                     border-radius: 12px;">🟢 HIGH (85%)</span>
    </div>
    <div style="display: flex; gap: 20px;">
        <div>Product Match: 80%</div>
        <div>Info Quality: 90%</div>
        <div>Context: ✓ Available</div>
    </div>
</div>
```

### Confidence Color Coding

| Range | Color | Label |
|-------|-------|-------|
| 80-100% | 🟢 Green | HIGH |
| 60-79% | 🟡 Yellow | MEDIUM |
| 0-59% | 🔴 Red | LOW |

### Body Formatting

- Paragraphs wrapped in `<p>` tags with margins
- Numbered lists use `<ol>` with styled `<li>`
- Bullet lists use `<ul>` with styled `<li>`
- Bold text converted to `<strong>`
- `[VERIFY]` tags highlighted in red

---

## 🔄 CONDITIONAL ROUTING

### Graph Edges

```python
# After routing_agent
def route_after_routing(state):
    if state.get("has_image"):
        return "vision_pipeline"
    elif state.get("has_text"):
        return "text_rag_pipeline"
    else:
        return "past_tickets"

# After hallucination_guard
def route_after_hallucination_guard(state):
    risk = state.get("hallucination_risk", 0)
    if risk > settings.hallucination_risk_threshold:  # 0.7
        return "resolution_logic"  # Skip response, mark as risky
    return "product_match_confidence_check"
```

---

## 📝 AUDIT LOGGING

### Event Structure

```python
{
    "event": "vision_pipeline",
    "type": "SUCCESS",
    "timestamp": "2025-12-02T18:30:45.123456",
    "details": {
        "images_processed": 1,
        "matches_found": 5,
        "top_match_score": 0.987,
        "duration": 1.23
    }
}
```

### Final Audit Record

Written to `audit.log` as JSON:

```json
{
    "ticket_id": 42,
    "ticket_subject": "Installation help needed",
    "resolution_status": "RESOLVED",
    "customer_type": "NORMAL",
    "overall_confidence": 85.0,
    "vision_matches": [
        {"product_id": "HS6270MB", "score": 0.987, "name": "Shower Head"}
    ],
    "text_matches": [
        {"title": "Installation Manual", "score": 0.95}
    ],
    "timestamp": "2025-12-02T18:31:00.000000",
    "events": [...]
}
```

---

## 🛠️ DEVELOPMENT GUIDELINES

### Adding a New Node

1. Create file in `app/nodes/`
2. Follow this template:

```python
import time
import logging
from app.graph.state import TicketState
from app.utils.audit import add_audit_event

logger = logging.getLogger(__name__)
STEP_NAME = "[NEW_NODE]"

def new_node(state: TicketState) -> dict:
    start_time = time.time()
    logger.info(f"{STEP_NAME} | Starting...")
    
    # Your logic here
    result = {}
    
    duration = time.time() - start_time
    logger.info(f"{STEP_NAME} | Complete in {duration:.2f}s")
    
    audit_events = add_audit_event(
        state, "new_node", "SUCCESS",
        {"duration": duration}
    )
    
    return {**result, "audit_events": audit_events}
```

3. Register in `graph/graph_builder.py`:

```python
from app.nodes.new_node import new_node

graph.add_node("new_node", new_node)
graph.add_edge("previous_node", "new_node")
```

### Code Style

- Use type hints everywhere
- Prefix logs with `STEP_NAME`
- Track duration for performance
- Add audit events for every node
- Handle errors gracefully with try/except

---

## 📞 TROUBLESHOOTING

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| CLIP model slow on first run | Model downloading | Wait for download, subsequent runs fast |
| Pinecone query fails | Wrong dimensions | Image: 512d, Text: 768d |
| Gemini File Search empty | Wrong store ID | Verify `GEMINI_FILE_SEARCH_STORE_ID` |
| Freshdesk 401 error | Invalid API key | Check `FRESHDESK_API_KEY` |

### Debug Commands

```python
# Test vision pipeline
from app.clients.embeddings import CLIPEmbedder
from app.clients.pinecone_client import PineconeClient

embedder = CLIPEmbedder()
pc = PineconeClient()
vector = embedder.embed_image_from_url("https://...")
results = pc.query_images(vector.tolist(), top_k=5)

# Test text RAG
from app.clients.gemini_client import GeminiFileSearchClient

client = GeminiFileSearchClient()
results = client.search("installation instructions")
```

---

**Last Updated**: December 2, 2025
