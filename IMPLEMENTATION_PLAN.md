# IMPLEMENTATION PLAN - Freshdesk Multimodal Support Automation

## 📋 COMPLETE TASK BREAKDOWN

### ✅ PHASE 1: PROJECT FOUNDATION (Tasks 1-4)

#### Task 1: Create Folder Structure
- [ ] Create `/app` directory structure
- [ ] Set up `/graph`, `/nodes`, `/clients`, `/services`, `/utils`, `/config`
- [ ] Create subdirectories: `/nodes/decisions`, `/nodes/response`
- [ ] Add `__init__.py` files to all packages

#### Task 2: Configuration & Environment
- [ ] Create `config/settings.py` with Pydantic BaseSettings
- [ ] Create `config/constants.py` for status enums and constants
- [ ] Create `.env.example` template
- [ ] Set up environment variable loading

#### Task 3: State Model Definition
- [ ] Create `graph/state.py` with complete TicketState TypedDict
- [ ] Define RetrievalHit TypedDict
- [ ] Add type imports and annotations
- [ ] Document all state fields

#### Task 4: Dependencies & Requirements
- [ ] Create `requirements.txt` with all dependencies
- [ ] Pin versions for production stability
- [ ] Add comments for dependency purposes

---

### ✅ PHASE 2: CLIENT LAYER (Tasks 5-9)

#### Task 5: Freshdesk Client
- [ ] Create `clients/freshdesk_client.py`
- [ ] Implement `get_ticket(ticket_id)` method
- [ ] Implement `add_note(ticket_id, body, private)` method
- [ ] Implement `update_ticket(ticket_id, **fields)` method
- [ ] Add error handling and retry logic

#### Task 6: Embeddings Module
- [ ] Create `clients/embeddings.py`
- [ ] Implement `embed_text(text)` using OpenAI/similar
- [ ] Implement `embed_image(image_url)` using CLIP/OpenAI
- [ ] Add caching for embeddings (optional)
- [ ] Handle errors gracefully

#### Task 7: Gemini File Search Client
- [ ] Create `clients/gemini_client.py`
- [ ] Implement `search_files(query, top_k)` method **RETRIEVAL ONLY**
- [ ] Format results into RetrievalHit structure
- [ ] Add error handling
- [ ] Test with existing Gemini File Search store

#### Task 8: Pinecone Client
- [ ] Create `clients/pinecone_client.py`
- [ ] Initialize connections to both indexes (image + tickets)
- [ ] Implement `query_images(vector, top_k)` **RETRIEVAL ONLY**
- [ ] Implement `query_past_tickets(vector, top_k)` **RETRIEVAL ONLY**
- [ ] Format results into RetrievalHit structure
- [ ] Add connection pooling and error handling

#### Task 9: LLM Client Wrapper
- [ ] Create `clients/llm_client.py`
- [ ] Implement `call_llm(system_prompt, user_prompt, response_format)` wrapper
- [ ] Support JSON response mode
- [ ] Add retry logic and error handling
- [ ] Support streaming (optional)

---

### ✅ PHASE 3: SERVICE LAYER (Tasks 10-12)

#### Task 10: RAG Service
- [ ] Create `services/rag_service.py`
- [ ] Implement unified interface for all retrieval sources
- [ ] Combine results from multiple sources
- [ ] Add relevance scoring and deduplication
- [ ] Format context for LLM consumption

#### Task 11: Customer Service
- [ ] Create `services/customer_service.py`
- [ ] Implement customer lookup by email
- [ ] Fetch customer metadata from Freshdesk/CRM
- [ ] Determine customer type (VIP, DISTRIBUTOR, NORMAL, etc.)

#### Task 12: VIP Rules Service
- [ ] Create `services/vip_rules_service.py`
- [ ] Load VIP rules from config/database
- [ ] Implement rule matching logic
- [ ] Return applicable rules for customer type

---

### ✅ PHASE 4: CORE NODES - DATA ACQUISITION (Tasks 13-18)

#### Task 13: Fetch Ticket Node
- [ ] Create `nodes/fetch_ticket.py`
- [ ] Implement `fetch_ticket_details(state)` function
- [ ] Fetch ticket from Freshdesk
- [ ] Extract text, images, metadata
- [ ] Update state with ticket info
- [ ] Add audit event

#### Task 14: Routing Agent Node
- [ ] Create `nodes/routing_agent.py`
- [ ] Implement `routing_agent(state)` function
- [ ] Use LLM to classify ticket category
- [ ] Set `ticket_category` in state
- [ ] Add audit event

#### Task 15: Vision Pipeline Node
- [ ] Create `nodes/vision_pipeline.py`
- [ ] Implement `vision_pipeline(state)` function
- [ ] Skip if no images
- [ ] Generate image embeddings
- [ ] Query Pinecone image index
- [ ] Store results in `image_retrieval_results`
- [ ] Add audit event

#### Task 16: Text RAG Pipeline Node
- [ ] Create `nodes/text_rag_pipeline.py`
- [ ] Implement `text_rag_pipeline(state)` function
- [ ] Skip if no text
- [ ] Generate text embedding
- [ ] Query Gemini File Search
- [ ] Store results in `text_retrieval_results`
- [ ] Add audit event

#### Task 17: Past Tickets Retrieval Node
- [ ] Create `nodes/past_tickets.py`
- [ ] Implement `retrieve_past_tickets(state)` function
- [ ] Generate embedding from ticket text
- [ ] Query Pinecone past tickets index
- [ ] Store results in `past_ticket_results`
- [ ] Add audit event

#### Task 18: Customer Lookup & VIP Rules Nodes
- [ ] Create `nodes/customer_lookup.py`
- [ ] Implement `get_customer_type(state)` function
- [ ] Create `nodes/vip_rules.py`
- [ ] Implement `load_vip_rules(state)` function
- [ ] Add audit events

---

### ✅ PHASE 5: CONTEXT & ORCHESTRATION (Tasks 19-20)

#### Task 19: Context Builder Node
- [ ] Create `nodes/context_builder.py`
- [ ] Implement `build_multimodal_context(state)` function
- [ ] Combine text, image, and past ticket results
- [ ] Format VIP rules if applicable
- [ ] Create unified context string for LLM
- [ ] Store in `multimodal_context`
- [ ] Add audit event

#### Task 20: Orchestration Agent Node
- [ ] Create `nodes/orchestration_agent.py`
- [ ] Implement `orchestration_agent(state)` function
- [ ] Analyze ticket + retrieved context
- [ ] Determine if enough information exists
- [ ] Set `enough_information` flag
- [ ] Extract product_id if identifiable
- [ ] Add audit event

---

### ✅ PHASE 6: DECISION NODES (Tasks 21-24)

#### Task 21: Enough Information Decider
- [ ] Create `nodes/decisions/enough_information.py`
- [ ] Implement `enough_information_decider(state)` function
- [ ] Apply heuristics on top of orchestration result
- [ ] Ensure state properly set
- [ ] Add audit event

#### Task 22: Hallucination Guard
- [ ] Create `nodes/decisions/hallucination_guard.py`
- [ ] Implement `hallucination_guard(state)` function
- [ ] Use LLM to rate hallucination risk (0-1)
- [ ] Set `hallucination_risk` in state
- [ ] Add audit event

#### Task 23: Product Match Confidence Check
- [ ] Create `nodes/decisions/confidence_check.py`
- [ ] Implement `product_match_confidence_check(state)` function
- [ ] Use LLM to rate product match confidence (0-1)
- [ ] Set `product_match_confidence` in state
- [ ] Add audit event

#### Task 24: VIP Compliance Check
- [ ] Create `nodes/decisions/vip_compliance.py`
- [ ] Implement `vip_compliance_check(state)` function
- [ ] Verify if response complies with VIP rules
- [ ] Set `vip_compliant` boolean in state
- [ ] Add audit event

---

### ✅ PHASE 7: RESPONSE GENERATION (Tasks 25-26)

#### Task 25: Draft Final Response Node
- [ ] Create `nodes/response/draft_response.py`
- [ ] Implement `draft_final_response(state)` function
- [ ] Use LLM with all context and decision flags
- [ ] Generate clarification OR resolution response
- [ ] Set `draft_response` in state
- [ ] Add audit event

#### Task 26: Resolution Logic Node
- [ ] Create `nodes/response/resolution_logic.py`
- [ ] Implement `decide_tags_and_resolution(state)` function
- [ ] Determine resolution status based on all checks
- [ ] Set appropriate tags (AI_UNRESOLVED, LOW_CONFIDENCE, etc.)
- [ ] Set `resolution_status` and `extra_tags`
- [ ] Set `final_response_public`
- [ ] Add audit event

---

### ✅ PHASE 8: OUTPUT & INTEGRATION (Tasks 27-28)

#### Task 27: Freshdesk Update Node
- [ ] Create `nodes/freshdesk_update.py`
- [ ] Implement `update_freshdesk_ticket(state)` function
- [ ] Add public reply OR private note based on resolution status
- [ ] Update ticket tags
- [ ] Handle errors gracefully
- [ ] Add audit event

#### Task 28: Audit Log Node
- [ ] Create `nodes/audit_log.py`
- [ ] Implement `write_audit_log(state)` function
- [ ] Collect all audit events from state
- [ ] Write to file/database
- [ ] Include timestamp, ticket_id, resolution status

---

### ✅ PHASE 9: GRAPH CONSTRUCTION (Tasks 29-30)

#### Task 29: Build LangGraph
- [ ] Create `graph/graph_builder.py`
- [ ] Import all node functions
- [ ] Create StateGraph with TicketState
- [ ] Add all nodes to graph
- [ ] Set entry point to `fetch_ticket_details`

#### Task 30: Define Conditional Edges
- [ ] Add conditional routing after `routing_agent` (vision/text)
- [ ] Add conditional routing after `vision_pipeline`
- [ ] Add conditional routing after `enough_information_decider`
- [ ] Add conditional routing after `hallucination_guard`
- [ ] Connect all other nodes with standard edges
- [ ] Compile graph

---

### ✅ PHASE 10: API & DEPLOYMENT (Tasks 31-34)

#### Task 31: FastAPI Application
- [ ] Create `app/main.py`
- [ ] Set up FastAPI app instance
- [ ] Build and store compiled graph
- [ ] Create health check endpoint

#### Task 32: Webhook Endpoint
- [ ] Create `/freshdesk/webhook` POST endpoint
- [ ] Parse Freshdesk webhook payload
- [ ] Initialize TicketState with minimal data
- [ ] Invoke LangGraph workflow
- [ ] Return response with resolution status
- [ ] Add error handling and logging

#### Task 33: Error Handling & Logging
- [ ] Add try/except blocks to all nodes
- [ ] Implement structured logging throughout
- [ ] Create error response templates
- [ ] Add timeout handling for LLM calls
- [ ] Implement graceful degradation

#### Task 34: Testing & Validation
- [ ] Create test ticket payloads
- [ ] Test each retrieval client independently
- [ ] Test graph execution end-to-end
- [ ] Validate Freshdesk updates
- [ ] Check audit logs
- [ ] Test error scenarios

---

## 🎯 EXECUTION STRATEGY

### Incremental Development
1. Build foundation first (Phases 1-2)
2. Test each client independently before moving on
3. Implement nodes in workflow order
4. Test graph construction incrementally
5. Wire up FastAPI last

### Testing Approach
- Test retrieval clients with real queries
- Mock Freshdesk for node testing
- Use sample state objects for node unit tests
- Integration test with test webhook payloads

### Code Cleanup Rules
- Delete any unused imports immediately
- Remove TODO comments once implemented
- No commented-out code blocks
- Keep files focused and single-purpose

---

## 📊 PROGRESS TRACKING

Total Tasks: 34
- Phase 1 (Foundation): 4 tasks
- Phase 2 (Clients): 5 tasks
- Phase 3 (Services): 3 tasks
- Phase 4 (Core Nodes): 6 tasks
- Phase 5 (Context): 2 tasks
- Phase 6 (Decisions): 4 tasks
- Phase 7 (Response): 2 tasks
- Phase 8 (Output): 2 tasks
- Phase 9 (Graph): 2 tasks
- Phase 10 (API): 4 tasks

---

## 🚀 READY TO START

All prerequisites are in place:
- ✅ Gemini File Search store configured
- ✅ Pinecone image index ready
- ✅ Pinecone tickets index ready
- ✅ Project understanding documented
- ✅ Implementation plan created

**Next Command**: Begin Phase 1, Task 1 - Create folder structure
