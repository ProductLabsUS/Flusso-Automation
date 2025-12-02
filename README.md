# Flusso Workflow - Freshdesk Multimodal Support Automation

A production-ready LangGraph-based automated support system that processes Freshdesk tickets using multimodal RAG (Retrieval-Augmented Generation) capabilities.

## 🎯 Overview

This system automatically:
- Fetches ticket details from Freshdesk (including attachments)
- Processes images using CLIP embeddings for visual product matching
- Retrieves relevant documentation via Gemini File Search
- Finds similar past resolved tickets for context
- Makes intelligent decisions using confidence checks and guard rails
- Generates HTML-formatted AI-powered responses with confidence indicators
- Updates Freshdesk with formatted notes, tags, and resolution status

## 🏗️ Architecture

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Orchestration** | LangGraph (17-node workflow) |
| **API Framework** | FastAPI |
| **LLM** | Google Gemini 2.0 Flash |
| **Image Embeddings** | CLIP ViT-B-32 (512 dimensions) |
| **Text Embeddings** | Gemini text-embedding-004 (768 dimensions) |
| **Vector Database** | Pinecone (2 indexes) |
| **Document Search** | Gemini File Search |
| **Ticketing** | Freshdesk REST API |

### System Flow

```
Freshdesk Webhook → FastAPI → LangGraph Workflow → Decision Gates → Freshdesk Update
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              Vision Pipeline   Text RAG Pipeline   Past Tickets
              (CLIP + Pinecone) (Gemini File Search) (Gemini Embeddings)
```

## 📁 Project Structure

```
app/
├── main.py                      # FastAPI entry point & webhook
├── graph/
│   ├── state.py                 # TicketState TypedDict (30+ fields)
│   └── graph_builder.py         # LangGraph workflow construction
├── nodes/                       # 17 Workflow Nodes
│   ├── fetch_ticket.py          # Fetch ticket + attachments from Freshdesk
│   ├── routing_agent.py         # LLM-based ticket classification
│   ├── vision_pipeline.py       # CLIP embedding → Pinecone image search
│   ├── text_rag_pipeline.py     # Gemini File Search for documentation
│   ├── past_tickets.py          # Similar resolved tickets lookup
│   ├── customer_lookup.py       # Customer type detection
│   ├── vip_rules.py             # VIP/Distributor rule application
│   ├── context_builder.py       # Combine all retrieval results
│   ├── orchestration_agent.py   # Analyze resolution feasibility
│   ├── decisions/               # Decision & guard nodes
│   │   ├── enough_information.py
│   │   ├── hallucination_guard.py
│   │   ├── confidence_check.py
│   │   └── vip_compliance.py
│   ├── response/                # Response generation
│   │   ├── draft_response.py    # LLM response with HTML formatting
│   │   └── resolution_logic.py  # Status & tag determination
│   ├── freshdesk_update.py      # Update ticket in Freshdesk
│   └── audit_log.py             # Complete workflow audit trail
├── clients/                     # External API clients
│   ├── freshdesk_client.py      # Freshdesk API wrapper
│   ├── pinecone_client.py       # Pinecone vector search
│   ├── gemini_client.py         # Gemini File Search client
│   ├── embeddings.py            # CLIP & Gemini embedding functions
│   └── llm_client.py            # Gemini LLM wrapper
├── utils/
│   ├── attachment_processor.py  # PDF/image attachment handling
│   ├── audit.py                 # Audit event helpers
│   └── detailed_logger.py       # Structured logging
└── config/
    ├── settings.py              # Pydantic environment config
    └── constants.py             # Enums and thresholds
```

## 🚀 Setup

### 1. Create Virtual Environment

```bash
python -m venv .venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
.\.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required credentials:
- `FRESHDESK_DOMAIN` - Your Freshdesk subdomain
- `FRESHDESK_API_KEY` - Freshdesk API key
- `PINECONE_API_KEY` - Pinecone API key
- `PINECONE_IMAGE_INDEX` - Index name for product images (CLIP embeddings)
- `PINECONE_TICKETS_INDEX` - Index name for past tickets (Gemini embeddings)
- `GEMINI_API_KEY` - Google Gemini API key
- `GEMINI_FILE_SEARCH_STORE_ID` - Gemini File Search store ID

## 🎬 Usage

### Run the API Server

```bash
uvicorn app.main:app --reload --port 8000
```

### Configure Freshdesk Webhook

Point your Freshdesk automation webhook to:
```
POST https://your-domain/webhook
```

Payload format:
```json
{
  "ticket_id": 123
}
```

### Manual Testing

```python
import requests
response = requests.post(
    "http://localhost:8000/webhook",
    json={"ticket_id": 42}
)
print(response.json())
```

## 🔄 Workflow Pipeline

### Node Execution Order

1. **fetch_ticket** - Retrieve ticket details and attachments from Freshdesk
2. **routing_agent** - Classify ticket (install_help, product_inquiry, order_status, etc.)
3. **vision_pipeline** - If images present: CLIP embed → Pinecone product search
4. **text_rag_pipeline** - If text present: Gemini File Search for documentation
5. **past_tickets** - Find similar resolved tickets via Gemini embeddings
6. **customer_lookup** - Identify customer type (VIP, DISTRIBUTOR, INTERNAL, NORMAL)
7. **vip_rules** - Load applicable VIP rules
8. **context_builder** - Combine all retrieval results into unified context
9. **orchestration_agent** - Analyze if enough information to resolve
10. **enough_information** - Decision gate for information sufficiency
11. **hallucination_guard** - Assess risk of generating false information
12. **confidence_check** - Verify product match confidence
13. **vip_compliance** - Ensure VIP rules are satisfied
14. **draft_response** - Generate HTML-formatted response with confidence header
15. **resolution_logic** - Determine final status and tags
16. **freshdesk_update** - Update ticket with response and tags
17. **audit_log** - Write complete audit trail

### Conditional Routing

- After `routing_agent` → Branch based on `has_image` / `has_text`
- After `hallucination_guard` → Continue if safe, escalate if risky
- After `enough_information` → Generate response OR request clarification

## 📊 Response Format

Responses are posted to Freshdesk with HTML formatting:

```html
<!-- Confidence Header -->
<div style="background: linear-gradient(...)">
  <span>📊 AI CONFIDENCE: 🟢 HIGH (85%)</span>
  <span>Product Match: 80%</span>
  <span>Info Quality: 90%</span>
</div>

<!-- Formatted Response Body -->
<div style="font-family: Arial...">
  <p>Dear Customer,</p>
  <ol>
    <li><strong>Step 1:</strong> ...</li>
    <li><strong>Step 2:</strong> ...</li>
  </ol>
</div>
```

### Confidence Levels

| Level | Range | Color |
|-------|-------|-------|
| 🟢 HIGH | 80-100% | Green |
| 🟡 MEDIUM | 60-79% | Yellow |
| 🔴 LOW | 0-59% | Red |

## 📋 Resolution Statuses

| Status | Description |
|--------|-------------|
| `RESOLVED` | AI successfully resolved with high confidence |
| `AI_UNRESOLVED` | Needs human intervention |
| `LOW_CONFIDENCE_MATCH` | Product match below 40% threshold |
| `VIP_RULE_FAILURE` | VIP rules not satisfied |
| `HALLUCINATION_RISK` | High risk of generating false information |

## 🔐 Security

- ✅ All API keys loaded from environment variables
- ✅ `.env` file excluded from git
- ✅ No hardcoded credentials in codebase
- ✅ Freshdesk API uses HTTP Basic Auth
- ✅ Audit logs exclude sensitive data

## 📊 Monitoring & Logging

### Audit Log (`audit.log`)

Every workflow execution is logged with:
- Ticket ID and subject
- Resolution status
- Customer type
- Vision pipeline matches (top 5 products with scores)
- Text RAG matches (top 5 documents with scores)
- Confidence scores
- Timestamps
- Complete event trail

### Structured Logging

All nodes use structured logging with:
- Step name prefixes
- Duration tracking
- Success/failure indicators
- Emoji indicators for quick scanning

## 🛠️ Configuration

### Thresholds (`config/settings.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `hallucination_risk_threshold` | 0.7 | Max acceptable hallucination risk |
| `product_confidence_threshold` | 0.4 | Min product match confidence |
| `vision_top_k` | 5 | Number of image search results |
| `text_rag_top_k` | 10 | Number of document search results |

### Customer Types (`config/constants.py`)

- `VIP` - Premium customers with priority handling
- `DISTRIBUTOR` - Business partners with special rules
- `INTERNAL` - Company employees
- `NORMAL` - Standard customers

## 📝 Development

### Adding a New Node

1. Create file in `app/nodes/`
2. Import `add_audit_event` from `app.utils.audit`
3. Define function signature: `def node_name(state: TicketState) -> dict:`
4. Add audit event at the end
5. Register in `app/graph/graph_builder.py`

### Testing a Node

```python
from app.graph.graph_builder import build_graph

graph = build_graph()
result = graph.invoke({"ticket_id": 42})
print(result["resolution_status"])
```

## 📦 Dependencies

Key packages:
- `langgraph` - Workflow orchestration
- `fastapi` - API framework
- `google-genai` - Gemini LLM & File Search
- `pinecone` - Vector database
- `open-clip-torch` - CLIP image embeddings
- `pydantic-settings` - Configuration management
- `httpx` - HTTP client
- `PyMuPDF` - PDF processing

See `requirements.txt` for complete list.

## 📞 Support

For issues and questions, contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: December 2, 2025
