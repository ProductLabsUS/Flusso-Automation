# 📍 Code Reference Map - Tool Integration Points

## File Locations & Line References

### Tools Module Structure
```
app/tools/
├── __init__.py (31 lines)
│   ├── Line 7-12: Tool imports
│   ├── Line 15-22: __all__ exports
│   ├── Line 25-31: AVAILABLE_TOOLS registry
│
├── schema.py (70 lines) - Pydantic models (not used by ReACT)
│
├── product_search.py (166 lines) ✅
│   ├── Line 16: @tool decorator
│   ├── Line 17-44: Function definition + docstring
│   ├── Line 46-52: Input validation
│   ├── Line 56-77: Pure metadata lookup strategy
│   └── Line 79-166: Semantic search fallback
│
├── document_search.py (226 lines) ✅
│   ├── Line 13: @tool decorator
│   ├── Line 14-45: Function definition + docstring
│   ├── Line 54-68: Query validation
│   ├── Line 70-85: Gemini search execution
│   └── Line 87-226: Document parsing + answer extraction
│
├── vision_search.py (223 lines) ✅
│   ├── Line 7: @tool decorator
│   ├── Line 8-54: Function definition + docstring
│   ├── Line 56-63: Input validation
│   ├── Line 65-220: Image processing + CLIP embedding
│   └── Line 75-85: Pinecone query for each image
│
├── past_tickets.py (187 lines) ✅
│   ├── Line 7: @tool decorator
│   ├── Line 8-54: Function definition + docstring
│   │  └── Line 19-20: ADDED alternative parameter names
│   ├── Line 56-64: Parameter validation + fallback handling
│   └── Line 66-187: Embedding + Pinecone search
│
├── attachment_analyzer.py (87 lines) ✅
│   ├── Line 8: @tool decorator
│   ├── Line 9-37: Function definition + docstring
│   ├── Line 39-44: Input validation
│   ├── Line 46-82: Wraps multimodal_document_analyzer_tool
│   └── Line 52-77: Extracts + deduplicates model numbers
│
└── finish.py (137 lines) ✅
    ├── Line 11: _safe_extract_list() helper function
    ├── Line 23: @tool decorator
    ├── Line 24-56: Function definition + docstring
    │  └── Line 31-32: Lenient type handling
    ├── Line 59-79: Safe list extraction
    └── Line 81-137: Quality assessment
```

---

## ReACT Agent Implementation

### File: `app/nodes/react_agent.py` (494 lines)

#### System Prompt Definition
```python
Lines 38-105: REACT_SYSTEM_PROMPT
├── Lines 42-47: AVAILABLE TOOLS section
│   └── Lists all 6 tools with descriptions
├── Lines 49-60: CRITICAL RULES section
│   └── Tool ordering, finish_tool requirement
├── Lines 62-68: STOPPING CONDITIONS
│   └── When to call finish_tool
├── Lines 70-74: URGENCY RULES
│   └── MAX_ITERATIONS - 2 enforcement
├── Lines 76-88: RESPONSE FORMAT
│   └── JSON format expected
├── Lines 90-103: DECISION TREE
│   └── Tool selection by scenario
└── Lines 105: Dynamic MAX_ITERATIONS insertion
```

#### Main ReACT Loop
```python
Line 107: def react_agent_loop(state: TicketState) -> Dict[str, Any]:
├── Lines 113-125: Extract state values
│   ├── ticket_id, ticket_subject, ticket_text
│   ├── ticket_images, attachments
│   └── Log current ticket info
│
├── Lines 127-138: Initialize tracking variables
│   ├── iterations: List[ReACTIteration]
│   ├── tool_results: Dict with 5 tools
│   ├── identified_product, gathered_documents, etc.
│   ├── product_confidence, gemini_answer
│   └── tools_used: set() for deduplication
│
├── Lines 140: llm = get_llm_client()
│
├── Lines 162-421: Main loop (1 to MAX_ITERATIONS)
│   ├── Lines 165-199: Forced finish if iteration >= MAX_ITERATIONS - 1
│   │   ├── Line 171: logger.warning(...) 
│   │   ├── Lines 174-181: Build finish_input
│   │   ├── Lines 183-189: Execute finish_tool directly
│   │   │   └── Tries all three methods: invoke/run/_run
│   │   └── Lines 191-201: Record iteration + break
│   │
│   ├── Lines 203-216: Build agent context
│   │   └── Calls _build_agent_context()
│   │
│   ├── Lines 219-225: Log iteration start
│   │   └── iteration_start = time.time()
│   │
│   ├── Lines 227-240: Call Gemini LLM
│   │   ├── system_prompt=REACT_SYSTEM_PROMPT
│   │   ├── user_prompt=agent_context
│   │   ├── response_format="json"
│   │   └── temperature=0.2 (consistent decisions)
│   │
│   ├── Lines 242-254: Parse Gemini response
│   │   ├── Check isinstance(response, dict)
│   │   ├── Extract thought, action, action_input
│   │   └── Log all three
│   │
│   ├── Lines 256-276: Check for duplicate tool attempts
│   │   ├── tool_key = f"{action}:{json.dumps(action_input)}"
│   │   ├── if tool_key in tools_used → skip
│   │   └── tools_used.add(tool_key)
│   │
│   ├── Lines 278-307: Special finish_tool handling
│   │   ├── Normalize relevant_documents
│   │   ├── Normalize relevant_images
│   │   ├── Normalize past_tickets
│   │   ├── Ensure action_input is dict
│   │   └── Inject gathered data if missing
│   │
│   ├── Lines 309-316: Execute tool
│   │   ├── tool_output, observation = _execute_tool(...)
│   │   └── Passing all context
│   │
│   ├── Lines 318-328: Record iteration
│   │   └── iterations.append({...})
│   │
│   ├── Lines 330-372: Extract and update state from tool results
│   │   ├── Lines 330-341: product_search_tool results
│   │   │   └── Updates identified_product + product_confidence
│   │   ├── Lines 343-354: document_search_tool results
│   │   │   ├── Deduplicates by title
│   │   │   └── Captures gemini_answer
│   │   ├── Lines 356-366: vision_search_tool results
│   │   │   └── Can identify product from image
│   │   ├── Lines 368-372: past_tickets_search_tool results
│   │   │   └── Appends to gathered_past_tickets
│   │   │
│   │   └── Lines 374-421: finish_tool handling
│   │       ├── Check if action=="finish_tool" and finished
│   │       ├── Normalize finish_tool outputs
│   │       ├── Merge with existing gathered data
│   │       ├── Break loop
│   │       └── Never duplicate resources
│   │
│   └── Lines 423-426: Exception handling
│       ├── logger.error(..., exc_info=True)
│       └── break
│
├── Lines 428-447: Post-loop processing
│   ├── Calculate total_duration
│   ├── Count final_iteration_count = len(iterations)
│   ├── Determine status ("finished" or "max_iterations")
│   └── Log comprehensive results
│
├── Lines 449-454: Call legacy field population
│   └── legacy_updates = _populate_legacy_fields(...)
│
├── Lines 456-472: Build audit events
│   └── add_audit_event(state, ...) with all stats
│
└── Lines 474-496: Return state updates
    ├── react_iterations, react_total_iterations, react_status
    ├── identified_product, product_confidence
    ├── gathered_documents, gathered_images, gathered_past_tickets
    ├── gemini_answer
    ├── **legacy_updates (spreads all legacy fields)
    └── audit_events
```

#### Helper Function
```python
Lines 486-494: def _run_tool(tool, kwargs: Dict[str, Any]):
├── Tries tool.run(**kwargs)
├── Falls back to tool.invoke(kwargs)
├── Falls back to tool._run(**kwargs)
└── Raises AttributeError if none exist
```

---

## ReACT Agent Helpers

### File: `app/nodes/react_agent_helpers.py` (470 lines)

#### Tool Imports (Lines 7-12)
```python
from app.tools.product_search import product_search_tool
from app.tools.document_search import document_search_tool
from app.tools.vision_search import vision_search_tool
from app.tools.past_tickets import past_tickets_search_tool
from app.tools.finish import finish_tool
from app.tools.attachment_analyzer import attachment_analyzer_tool
```
✅ All 6 tools imported

#### Context Building Function (Lines 24-110)
```python
Line 24: def _build_agent_context(...) -> str:
├── Lines 27-48: Build context_parts list
│   ├── Iteration header + max_iterations
│   ├── Ticket subject and description (first 2000 chars)
│   ├── Images count and URLs
│   ├── Attachments metadata (first 5)
│   └── Log section header
│
├── Lines 50-59: Previous actions section
│   ├── Last 5 iterations
│   ├── Thought (150 chars)
│   ├── Action name
│   └── Observation (200 chars)
│
├── Lines 61-102: Current state section
│   ├── Lines 63-65: Product search results
│   ├── Lines 67-69: Document search results
│   ├── Lines 71-73: Vision search results
│   ├── Lines 75-77: Past tickets results
│   ├── Lines 79-83: Attachment analysis results
│   │   └── Extracted model numbers highlighted
│   │
│   ├── Lines 85-102: Urgency alerts
│   │   ├── if iteration_num >= max_iterations - 2:
│   │   └── Prominent warnings with === separators
│   │
│   └── Lines 103-110: Return joined string
```

#### Tool Execution Function (Lines 113-249)
```python
Line 113: def _execute_tool(...) -> Tuple[Dict[str, Any], str]:

Line 115: def _run_tool(tool, kwargs: Dict[str, Any]):
├── Returns tool.run(**kwargs) (v1)
├── Or tool.invoke(kwargs) (v0.x)
├── Or tool._run(**kwargs) (fallback)
└── Raises AttributeError if none exist

Lines 126-142: product_search_tool handler
├── _run_tool(product_search_tool, action_input or {})
├── tool_results["product_search"] = output
├── Success: {count, top product with model_no, score}
└── Failure: Error message

Lines 144-163: document_search_tool handler
├── Make defensive copy of action_input
├── Auto-inject product_context if identified_product known
│   └── if identified_product and not action_input.get("product_context"):
│   └── action_input["product_context"] = model or name
├── _run_tool(document_search_tool, action_input)
├── tool_results["document_search"] = output
├── Success: {count, top 3 documents, gemini_answer}
└── Failure: Error message

Lines 165-177: vision_search_tool handler
├── Make copy of action_input
├── Auto-inject ticket_images
│   └── action_input["image_urls"] = ticket_images
├── _run_tool(vision_search_tool, action_input)
├── tool_results["vision_search"] = output
├── Success: {quality, count, matches}
└── Failure: Error message

Lines 179-191: past_tickets_search_tool handler
├── _run_tool(past_tickets_search_tool, action_input or {})
├── tool_results["past_tickets"] = output
├── Success: {count, patterns, tickets}
└── Failure: Error message

Lines 193-207: attachment_analyzer_tool handler
├── Make copy of action_input
├── Auto-inject attachments
│   └── action_input["attachments"] = attachments
├── _run_tool(attachment_analyzer_tool, action_input)
├── tool_results["attachment_analysis"] = output
├── Success: {count, model_numbers, entities}
└── Failure: Error message

Lines 209-212: finish_tool handler
├── _run_tool(finish_tool, action_input or {})
├── observation string built
└── Returns (output, obs)

Lines 214-216: Unknown tool handler
├── Returns {"error": "Unknown tool: {action}", "success": False}
└── Also returns obs string

Lines 218-226: Exception handling
├── logger.error(..., exc_info=True)
└── Returns error dict with message
```

#### Legacy Field Population Function (Lines 269-454)
```python
Line 269: def _populate_legacy_fields(...) -> Dict[str, Any]:

Lines 272-276: Normalize inputs
├── product_details = identified_product or {}
├── relevant_documents = _normalize_documents(gathered_documents)
├── relevant_images = _normalize_images(gathered_images)
└── past_tickets = _normalize_tickets(gathered_past_tickets)

Lines 278-288: Deduplicate documents
├── seen_titles = set()
├── Loop through relevant_documents
├── Add unique titles to seen_titles
├── Skip duplicates
└── Allow docs without titles

Lines 290-303: Convert to text_retrieval_results (RetrievalHit format)
├── For each document:
│   ├── id: doc_i
│   ├── score: relevance_score (default 0.8)
│   ├── metadata: {title, source: "gemini_file_search"}
│   └── content: content_preview or title

Lines 305-317: Convert to image_retrieval_results (RetrievalHit format)
├── For each image URL:
│   ├── id: img_i
│   ├── score: 0.9
│   ├── metadata: {image_url, source: "react_vision"}
│   └── content: "Product image {i+1}"

Lines 319-333: Convert to past_ticket_results (RetrievalHit format)
├── For each ticket:
│   ├── Normalize similarity (divide by 100 if > 1)
│   ├── id: ticket_{ticket_id}
│   ├── score: similarity_score
│   ├── metadata: {ticket_id, subject, resolution_type}
│   └── content: resolution_summary

Lines 335-376: Build multimodal_context string (CRITICAL)
├── Lines 335-342: Surface Gemini answer FIRST
│   └── "### 🎯 DIRECT ANSWER FROM DOCUMENTATION"
├── Lines 344-350: Add document context
│   ├── Top 10 documents (increased from 5)
│   ├── Format: "N. **Title** (score: X.XX)"
│   └── Include content preview (500 chars)
├── Lines 352-357: Add product/vision context
│   ├── "### PRODUCT MATCHES (VISUAL)"
│   ├── Model, Name, Category, Confidence
│   └── Only if identified_product exists
├── Lines 359-370: Add past tickets context
│   ├── "### SIMILAR PAST TICKETS"
│   ├── Top 3 tickets
│   ├── Format: "N. Ticket #X (resolution) - Similarity: Y"
│   └── Include resolution summary (300 chars)
└── Lines 372-376: Join and validate multimodal_context

Lines 378-390: Build source_documents (top 10)
├── For each document:
│   ├── rank: i+1
│   ├── title, content_preview (500 chars)
│   ├── relevance_score, source_type
│   └── uri (if available)

Lines 392-402: Build source_products
├── If identified_product exists:
│   ├── rank: 1
│   ├── model_no, product_title, category
│   ├── similarity_score (as percentage)
│   └── source_type: "react_agent"

Lines 404-416: Build source_tickets (top 5)
├── For each ticket:
│   ├── rank: i+1
│   ├── ticket_id, subject, resolution_type
│   ├── resolution_summary (200 chars)
│   ├── similarity_score
│   └── source_type: "past_tickets"

Lines 418-424: Determine if enough_information
├── has_docs = len(text_retrieval_results) > 0
├── has_images = len(image_retrieval_results) > 0
├── has_product = identified_product is not None
└── enough_info = has_docs or has_images or has_product

Lines 426-442: Return legacy fields dictionary
├── text_retrieval_results
├── image_retrieval_results
├── past_ticket_results
├── multimodal_context (STRING - CRITICAL!)
├── source_documents
├── source_products
├── source_tickets
├── gemini_answer
├── enough_information
├── product_match_confidence
├── overall_confidence
├── ran_vision: True (prevents re-running)
├── ran_text_rag: True
└── ran_past_tickets: True

Lines 445-470: Normalization helper functions
├── _normalize_documents(docs): Dict handling
├── _normalize_images(images): URL extraction
└── _normalize_tickets(tickets): Dict/str handling
```

---

## Graph Integration

### File: `app/graph/graph_builder_react.py` (204 lines)

#### Node Addition
```python
Line 102: graph.add_node("react_agent", react_agent_loop)
```

#### Edge Configuration
```python
Lines 144-165: Edge setup
├── Line 144: graph.add_edge("routing", "react_agent")
│   └── Conditional via route_after_routing()
├── Line 153: graph.add_edge("react_agent", "customer_lookup")
├── Line 154: graph.add_edge("customer_lookup", "vip_rules")
├── Line 156: graph.add_edge("vip_rules", "hallucination_guard")
├── Line 157: graph.add_edge("hallucination_guard", "confidence_check")
├── Line 158: graph.add_edge("confidence_check", "vip_compliance")
├── Line 160: graph.add_edge("vip_compliance", "draft_response")
├── Line 161: graph.add_edge("draft_response", "resolution_logic")
├── Line 163: graph.add_edge("resolution_logic", "freshdesk_update")
├── Line 164: graph.add_edge("freshdesk_update", "audit_log")
└── Line 165: graph.add_edge("audit_log", END)
```

---

## Summary of Integration Points

### Direct Tool Access Paths:
1. **Individual imports:** `from app.tools.X import X_tool`
2. **Registry access:** `from app.tools import AVAILABLE_TOOLS`
3. **Via helpers:** `from app.nodes.react_agent_helpers import _execute_tool`
4. **Via main loop:** `from app.nodes.react_agent import react_agent_loop`

### Key State Propagation Points:
1. **Tool results storage:** `tool_results["X"]` (5 tools)
2. **Gathered context:** `identified_product`, `gathered_documents`, `gathered_images`, `gathered_past_tickets`
3. **Final return:** Includes both ReACT-specific and legacy fields
4. **Graph output:** All fields propagated to next node

### Critical Code Sections:
1. **System Prompt:** Lines 38-105 in react_agent.py
2. **Main loop:** Lines 162-426 in react_agent.py
3. **Tool execution:** Lines 113-249 in react_agent_helpers.py
4. **Legacy population:** Lines 269-442 in react_agent_helpers.py
5. **Graph setup:** Lines 102-165 in graph_builder_react.py

### Testing Points:
1. Check imports at lines 7-12 of react_agent_helpers.py
2. Verify _execute_tool() routes all 6 actions (lines 126-216)
3. Confirm tool_results dict gets populated (lines 63-83)
4. Validate state updates (lines 330-372)
5. Check legacy field output (lines 474-496)

---

**All integration points verified and documented.**
