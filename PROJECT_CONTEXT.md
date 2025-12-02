# PROJECT CONTEXT & IMPLEMENTATION GUIDE

## 🎯 PROJECT OVERVIEW

This is a **production-ready LangGraph-based automated Freshdesk support system** with multimodal RAG capabilities. The system automatically processes customer support tickets using text and image analysis, retrieves relevant knowledge, and generates intelligent responses.

---

## 🗄️ EXISTING INFRASTRUCTURE (ALREADY SET UP)

### 1. **Gemini File Search Store**
- Used for text-based document retrieval
- Contains product manuals, FAQs, warranty policies, installation guides

### 2. **Pinecone - Image Index**
- Stores CLIP/multimodal embeddings of product images
- Metadata includes: product_id, sku, image_url, ocr_text, doc_type

### 3. **Pinecone - Tickets Index** (separate index, same account)
- Stores embeddings of past resolved tickets
- Metadata includes: ticket_id, resolution_type, product_id, customer_type, agent_id, summary text

---

## 🚫 WHAT WE ARE NOT DOING

- **NO ingestion scripts** (already done)
- **NO database setup code** (already configured)
- **NO unnecessary complexity**
- **NO code for uploading/indexing data**

---

## ✅ WHAT WE ARE BUILDING

### Core Focus: **RETRIEVAL-ONLY SYSTEM**

A clean, focused LangGraph workflow that:

1. **Fetches** ticket details from Freshdesk
2. **Retrieves** relevant information from existing indexes
3. **Processes** multimodal data (text + images)
4. **Makes decisions** using guards and confidence checks
5. **Generates** intelligent responses
6. **Updates** Freshdesk with results

---

## 🏗️ SYSTEM ARCHITECTURE

### Technology Stack

- **Orchestration**: LangGraph
- **API Framework**: FastAPI
- **LLM**: Google Gemini
- **Text Embeddings**: OpenAI or similar
- **Image Embeddings**: CLIP/OpenAI multimodal
- **Vector DBs**: 
  - Gemini File Search (text docs)
  - Pinecone (images + past tickets)
- **Ticketing**: Freshdesk REST API

### Key Components

```
Freshdesk Webhook → FastAPI → LangGraph Workflow → Decision Nodes → Freshdesk Update
                                      ↓
                        Retrieval from 3 sources:
                        1. Gemini File Search
                        2. Pinecone Image Index
                        3. Pinecone Past Tickets
```

---

## 🔄 LANGGRAPH WORKFLOW

### State Model (`TicketState`)

```python
TypedDict containing:
- Raw ticket info (id, subject, text, images, email)
- Classification (category, has_text, has_image)
- Customer data (type, metadata, VIP rules)
- RAG results (text_retrieval, image_retrieval, past_tickets)
- Decision metrics (confidence, hallucination_risk, enough_info, vip_compliant)
- LLM outputs (draft_response, clarification_message)
- Final outcome (response, status, tags)
- Audit trail
```

### Node Flow

1. **fetch_ticket_details** - Get ticket from Freshdesk
2. **routing_agent** - Classify ticket type
3. **vision_pipeline** - If has_image → query Pinecone image index
4. **text_rag_pipeline** - If has_text → query Gemini File Search
5. **retrieve_past_tickets** - Query Pinecone past tickets
6. **get_customer_type** - Lookup customer profile
7. **load_vip_rules** - Load VIP rules if applicable
8. **build_multimodal_context** - Combine all retrieval results
9. **orchestration_agent** - Analyze if we can resolve
10. **enough_information_decider** - Check if we have enough info
11. **hallucination_guard** - Check risk of making up facts
12. **product_match_confidence_check** - Verify product identification
13. **vip_compliance_check** - Ensure VIP rules followed
14. **draft_final_response** - Generate response
15. **decide_tags_and_resolution** - Set status and tags
16. **update_freshdesk_ticket** - Update ticket in Freshdesk
17. **write_audit_log** - Log complete workflow

### Decision Points (Conditional Edges)

- After routing → branch on has_image/has_text
- After enough_info → continue OR ask for clarification
- After hallucination_guard → safe OR unsafe
- All leading to appropriate response generation

---

## 📁 PROJECT STRUCTURE

```
app/
├── main.py                          # FastAPI entry point
├── graph/
│   ├── state.py                     # TicketState definition
│   └── graph_builder.py             # LangGraph construction
├── nodes/
│   ├── fetch_ticket.py
│   ├── routing_agent.py
│   ├── vision_pipeline.py           # Query Pinecone image index
│   ├── text_rag_pipeline.py         # Query Gemini File Search
│   ├── past_tickets.py              # Query Pinecone tickets index
│   ├── customer_lookup.py
│   ├── vip_rules.py
│   ├── context_builder.py
│   ├── orchestration_agent.py
│   ├── decisions/
│   │   ├── hallucination_guard.py
│   │   ├── confidence_check.py
│   │   ├── enough_information.py
│   │   └── vip_compliance.py
│   ├── response/
│   │   ├── draft_response.py
│   │   └── resolution_logic.py
│   ├── freshdesk_update.py
│   └── audit_log.py
├── clients/
│   ├── freshdesk_client.py          # Freshdesk API wrapper
│   ├── pinecone_client.py           # Pinecone retrieval ONLY
│   ├── gemini_client.py             # Gemini File Search retrieval ONLY
│   ├── embeddings.py                # Text & image embedding functions
│   └── llm_client.py                # LLM calls wrapper
├── services/
│   ├── rag_service.py               # Unified RAG interface
│   ├── customer_service.py
│   ├── vip_rules_service.py
│   └── logging_service.py
├── utils/
│   ├── image_utils.py
│   ├── text_utils.py
│   └── formatters.py
└── config/
    ├── settings.py                  # Environment config
    └── constants.py
```

---

## 🎯 IMPLEMENTATION PRINCIPLES

### 1. **Retrieval-Only Focus**
- All clients only implement `query()` or `search()` methods
- NO ingestion, NO upsert, NO data upload code
- Clean separation: retrieval logic only

### 2. **Simplicity & Precision**
- Each node does ONE thing well
- No unnecessary abstractions
- Clear, readable code

### 3. **Delete Unused Code**
- If we refactor, we DELETE old implementations
- No commented-out code blocks
- Keep codebase clean

### 4. **Type Safety**
- Use TypedDict for state
- Type hints everywhere
- Pydantic for configs

### 5. **Error Handling**
- Graceful degradation
- If one retrieval fails, continue with others
- Always update ticket with status

---

## 🔧 CLIENT IMPLEMENTATIONS

### Gemini Client (`gemini_client.py`)
```python
class GeminiClient:
    def search_files(self, query: str, top_k: int = 10) -> List[RetrievalHit]:
        """Query Gemini File Search store - RETRIEVAL ONLY"""
        # Use Gemini File Search API
        # Return formatted hits with content and metadata
```

### Pinecone Client (`pinecone_client.py`)
```python
class PineconeClient:
    def __init__(self):
        self.image_index = pinecone.Index("image-index")
        self.tickets_index = pinecone.Index("tickets-index")
    
    def query_images(self, vector: List[float], top_k: int = 5) -> List[RetrievalHit]:
        """Query image index - RETRIEVAL ONLY"""
    
    def query_past_tickets(self, vector: List[float], top_k: int = 5) -> List[RetrievalHit]:
        """Query past tickets - RETRIEVAL ONLY"""
```

### Freshdesk Client (`freshdesk_client.py`)
```python
class FreshdeskClient:
    def get_ticket(self, ticket_id: int) -> Dict:
        """Fetch ticket details"""
    
    def add_note(self, ticket_id: int, body: str, private: bool = True):
        """Add note to ticket"""
    
    def update_ticket(self, ticket_id: int, **fields):
        """Update ticket fields (tags, status, etc.)"""
```

---

## 📋 RESOLUTION STATUSES

- `RESOLVED` - AI successfully resolved with high confidence
- `AI_UNRESOLVED` - Not enough information or needs human
- `LOW_CONFIDENCE_MATCH` - Product match below threshold
- `VIP_RULE_FAILURE` - VIP rules not satisfied

---

## 🔐 ENVIRONMENT VARIABLES

```env
# Freshdesk
FRESHDESK_DOMAIN=your-domain
FRESHDESK_API_KEY=your-key

# Pinecone
PINECONE_API_KEY=your-key
PINECONE_ENV=your-env
PINECONE_IMAGE_INDEX=image-index
PINECONE_TICKETS_INDEX=tickets-index

# Gemini
GEMINI_API_KEY=your-key
GEMINI_FILE_SEARCH_STORE_ID=your-store-id

# OpenAI (for embeddings)
OPENAI_API_KEY=your-key
```

---

## 🎬 WORKFLOW ENTRY POINT

```python
# main.py
@app.post("/freshdesk/webhook")
async def freshdesk_webhook(req: Request):
    payload = await req.json()
    ticket_id = str(payload["ticket_id"])
    
    initial_state = TicketState(
        ticket_id=ticket_id,
        # ... minimal initialization
    )
    
    final_state = graph.invoke(initial_state)
    return {"status": "ok", "resolution": final_state["resolution_status"]}
```

---

## 📊 AUDIT TRAIL

Every node appends to `state["audit_events"]`:

```python
{
    "event": "node_name",
    "timestamp": "...",
    "details": {...}
}
```

Final audit log written to file/DB at end of workflow.

---

## 🚀 NEXT STEPS (Implementation Plan)

### Phase 1: Foundation
1. Create folder structure
2. Set up config/settings
3. Implement state model
4. Create base clients (Freshdesk, Pinecone, Gemini)

### Phase 2: Retrieval Layer
5. Implement embeddings module
6. Build Gemini File Search client (retrieval only)
7. Build Pinecone clients (image + tickets, retrieval only)
8. Create RAG service (unified interface)

### Phase 3: Core Nodes
9. Implement fetch_ticket node
10. Implement routing_agent
11. Implement vision_pipeline (uses Pinecone image)
12. Implement text_rag_pipeline (uses Gemini)
13. Implement past_tickets retrieval (uses Pinecone tickets)

### Phase 4: Decision Logic
14. Customer lookup & VIP rules
15. Context builder (combine all retrievals)
16. Orchestration agent
17. All decision nodes (hallucination, confidence, etc.)

### Phase 5: Response & Integration
18. Response generation nodes
19. Freshdesk update node
20. Audit logging
21. Graph builder (connect all nodes)

### Phase 6: API & Testing
22. FastAPI webhook endpoint
23. Error handling
24. Basic testing
25. Deployment preparation

---

## 💡 DEVELOPMENT GUIDELINES

### When Adding Any Code:

1. **Ask**: Does this retrieve data or ingest data?
   - If ingest → DON'T ADD IT
   - If retrieve → Proceed

2. **Ask**: Is this necessary for the workflow?
   - If optional → Skip it
   - If core → Add it

3. **Ask**: Can I simplify this?
   - Always prefer simpler solution
   - Avoid over-engineering

4. **Before committing**: Delete any unused code

### Code Style:

- Clear function names
- Type hints required
- Docstrings for complex logic
- Error handling with try/except
- Logging at key points

---

## 🎓 KEY CONCEPTS TO REMEMBER

1. **State-driven**: Everything flows through TicketState
2. **Retrieval-only**: No data upload in production code
3. **Conditional routing**: LangGraph handles decision trees
4. **Multi-source RAG**: Gemini + Pinecone (2 indexes)
5. **Guard rails**: Multiple confidence/safety checks
6. **Audit everything**: Complete paper trail
7. **Fail gracefully**: Always update Freshdesk with status

---

## 📝 SUMMARY

**What we have**:
- 3 configured vector stores (Gemini File Search + 2 Pinecone indexes)

**What we're building**:
- Clean retrieval scripts
- LangGraph workflow
- FastAPI webhook
- Intelligent decision system
- Freshdesk integration

**What we're NOT building**:
- Data ingestion pipelines
- Vector DB setup scripts
- Unnecessary complexity

---

This document serves as the **single source of truth** for this project. Reference it in every implementation decision.

Last Updated: November 29, 2025
