# Flusso Workflow - Unused Code Analysis
**Analysis Date:** December 16, 2025  
**Current Implementation:** ReACT Agent-based Workflow

---

## 📋 Executive Summary

The new **ReACT agent-based workflow** (`graph_builder_react.py`) has replaced the old sequential pipeline. The following analysis identifies **safe-to-delete** files that are no longer used.

---

## ✅ CURRENTLY ACTIVE WORKFLOW

### Active Graph Builder
- ✅ **`app/graph/graph_builder_react.py`** - Current ReACT workflow
- ✅ **`app/main_react.py`** - FastAPI app using ReACT workflow

### Active Nodes (Used in ReACT Flow)
1. ✅ `fetch_ticket.py` - Fetch ticket from Freshdesk
2. ✅ `routing_agent.py` - Classify ticket category
3. ✅ **`react_agent.py`** - Main ReACT agent loop (CORE)
4. ✅ **`react_agent_helpers.py`** - Tool execution & context building
5. ✅ **`planner.py`** - Execution planning for ReACT agent
6. ✅ **`evidence_resolver.py`** - Multi-source evidence analysis
7. ✅ `customer_lookup.py` - Identify customer type (VIP/Normal)
8. ✅ `vip_rules.py` - Load VIP-specific rules
9. ✅ `decisions/vip_compliance.py` - Verify VIP rule compliance
10. ✅ `response/draft_response.py` - Generate customer response
11. ✅ `response/resolution_logic.py` - Determine final status/tags
12. ✅ `freshdesk_update.py` - Update ticket in Freshdesk
13. ✅ `audit_log.py` - Write audit trail

### Active Tools (Used by ReACT Agent)
1. ✅ **`product_catalog_tool.py`** - Search 5,687 products (NEW)
2. ✅ `document_search.py` - Gemini File Search
3. ✅ `vision_search.py` - Pinecone vision search
4. ✅ `past_tickets.py` - Similar ticket search
5. ✅ `multimodal_document_analyzer.py` - Analyze PDFs with Gemini
6. ✅ `ocr_image_analyzer.py` - Analyze images with Gemini
7. ✅ `attachment_analyzer.py` - Generic attachment analyzer
8. ✅ `attachment_classifier_tool.py` - Classify attachment types
9. ✅ `finish.py` - Submit gathered context and stop loop

### Active Services
1. ✅ **`policy_service.py`** - Policy document management (NEW)
2. ✅ **`product_catalog.py`** - Product catalog with 5,687 entries (NEW)
3. ✅ **`product_catalog_cache.py`** - Cache initialization (NEW)

---

## 🗑️ SAFE TO DELETE - UNUSED FILES

### 1️⃣ OLD GRAPH BUILDER (Replaced by ReACT)
**Status:** ❌ Only used in `poll_freshdesk.py` and old `app/main.py`

```
❌ app/graph/graph_builder.py
```

**Why it's safe:**
- Replaced by `graph_builder_react.py`
- Sequential pipeline no longer used in production
- Only referenced in:
  - `poll_freshdesk.py` (can be updated to use ReACT)
  - `app/main.py` (old version, not used)
  - `test_workflow_manual.py` (optional --mode sequential, rarely used)

**Action:** Update references before deletion (see Migration Plan below)

---

### 2️⃣ OLD PIPELINE NODES (Replaced by ReACT Agent)
**Status:** ❌ No longer called in ReACT workflow

```
❌ app/nodes/context_builder.py
❌ app/nodes/orchestration_agent.py
❌ app/nodes/text_rag_pipeline.py
❌ app/nodes/vision_pipeline.py
```

**Why they're safe:**
- `context_builder.py` - ReACT agent builds context dynamically
- `orchestration_agent.py` - ReACT agent handles tool orchestration
- `text_rag_pipeline.py` - `document_search_tool` replaces this
- `vision_pipeline.py` - `vision_search_tool` + multimodal tools replace this

**References:** Only in `graph_builder.py` (old graph)

---

### 3️⃣ OLD DECISION NODES (Replaced by Evidence Resolver)
**Status:** ❌ Evidence resolver handles these checks now

```
❌ app/nodes/decisions/confidence_check.py
❌ app/nodes/decisions/enough_information.py
❌ app/nodes/decisions/hallucination_guard.py
```

**Why they're safe:**
- `evidence_resolver.py` now performs all confidence/conflict checks
- Comments in `graph_builder_react.py` confirm removal:
  ```python
  # REMOVED: hallucination_guard and confidence_check (redundant - evidence_resolver handles this)
  ```

**References:** Only in `graph_builder.py` (old graph)

---

### 4️⃣ OLD PRODUCT SEARCH TOOLS (Replaced by Product Catalog Tool)
**Status:** ❌ CSV wrapper is indirect, Pinecone is unused

```
❌ app/tools/product_search_from_csv.py
❌ app/tools/product_search_pinecone.py
```

**Why they're safe:**
- **NEW:** `product_catalog_tool.py` directly uses `product_catalog.py`
- `product_search_from_csv.py` is a wrapper that internally calls pinecone
- ReACT agent imports `product_catalog_tool` directly
- These old tools are only in `app/tools/__init__.py` exports

**Current Flow:**
```
ReACT Agent → product_catalog_tool → product_catalog.py (ProductCatalog class)
```

**Old Flow (unused):**
```
Old → product_search_from_csv → product_search_pinecone (never called)
```

---

### 5️⃣ OLD FASTAPI MAIN (Not Used in Production)
**Status:** ❌ Superseded by main_react.py

```
❌ app/main.py
```

**Why it's safe:**
- `main_react.py` is the active FastAPI app
- Uses `graph_builder_react.py` (current workflow)
- `main.py` uses old `graph_builder.py`
- No production references to `main.py`

**Evidence:**
- `run_local_server.py` imports `"app.main:app"` (could use either)
- Render/Procfile should use `app.main_react:app`

---

## 📊 SUMMARY TABLE

| File/Directory | Status | Reason | Dependencies |
|---------------|--------|--------|--------------|
| `graph_builder.py` | ❌ DELETE | Old sequential workflow | 3 scripts reference it |
| `context_builder.py` | ❌ DELETE | ReACT builds context | Only in old graph |
| `orchestration_agent.py` | ❌ DELETE | ReACT handles orchestration | Only in old graph |
| `text_rag_pipeline.py` | ❌ DELETE | Replaced by document_search_tool | Only in old graph |
| `vision_pipeline.py` | ❌ DELETE | Replaced by vision tools | Only in old graph |
| `decisions/confidence_check.py` | ❌ DELETE | Evidence resolver handles this | Only in old graph |
| `decisions/enough_information.py` | ❌ DELETE | Evidence resolver handles this | Only in old graph |
| `decisions/hallucination_guard.py` | ❌ DELETE | Evidence resolver handles this | Only in old graph |
| `product_search_from_csv.py` | ❌ DELETE | Wrapper, not used | Only __init__ export |
| `product_search_pinecone.py` | ❌ DELETE | Not used by new catalog | Only CSV wrapper |
| `main.py` | ❌ DELETE | Old FastAPI app | run_local_server |

**Total Files to Delete:** 11 files

---

## 🔧 MIGRATION PLAN (Before Deletion)

### Step 1: Update Scripts to Use ReACT Workflow

#### A. Update `poll_freshdesk.py` (Line 30)
**Current:**
```python
from app.graph.graph_builder import build_graph
```

**Change to:**
```python
from app.graph.graph_builder_react import build_react_graph as build_graph
```

#### B. Update `run_local_server.py` (Line 44)
**Current:**
```python
uvicorn.run(
    "app.main:app",  # ← Could be old or new
```

**Change to:**
```python
uvicorn.run(
    "app.main_react:app",  # ← Explicitly use ReACT
```

#### C. Update `test_workflow_manual.py` (Optional)
Keep the `--mode sequential` option for now (testing purposes), but change default to ReACT-only after validation.

### Step 2: Update `app/tools/__init__.py`
**Remove old product search exports:**

**Current (lines 6, 18):**
```python
from app.tools.product_search_from_csv import product_search_tool

__all__ = [
    "product_search_tool",  # ← Remove this
    ...
]

AVAILABLE_TOOLS = {
    "product_search_tool": product_search_tool,  # ← Remove this
    ...
}
```

**Change to:**
```python
# Remove product_search_from_csv import entirely
from app.tools.product_catalog_tool import product_catalog_tool

__all__ = [
    "product_catalog_tool",  # ← Add this
    ...
]

AVAILABLE_TOOLS = {
    "product_catalog_tool": product_catalog_tool,  # ← Add this
    ...
}
```

### Step 3: Test After Updates
```bash
# Test ReACT workflow still works
python test_workflow_manual.py 9

# Test poller
python poll_freshdesk.py

# Test local server
python run_local_server.py
```

### Step 4: Delete Unused Files
```bash
# Delete old graph
rm app/graph/graph_builder.py

# Delete old nodes
rm app/nodes/context_builder.py
rm app/nodes/orchestration_agent.py
rm app/nodes/text_rag_pipeline.py
rm app/nodes/vision_pipeline.py

# Delete old decisions
rm app/nodes/decisions/confidence_check.py
rm app/nodes/decisions/enough_information.py
rm app/nodes/decisions/hallucination_guard.py

# Delete old product search
rm app/tools/product_search_from_csv.py
rm app/tools/product_search_pinecone.py

# Delete old main
rm app/main.py
```

---

## ⚠️ KEEP THESE (Still Used)

### Tools - Used by ReACT Agent
- ✅ `attachment_analyzer.py` - Generic analyzer (imported in helpers)
- ✅ `attachment_classifier_tool.py` - Type classifier (imported in helpers)
- ✅ `vision_search.py` - Pinecone vision index (imported in helpers)
- ✅ `document_search.py` - Gemini file search (imported in helpers)
- ✅ `past_tickets.py` - Similar tickets (imported in helpers)
- ✅ `multimodal_document_analyzer.py` - PDF analysis (imported in helpers)
- ✅ `ocr_image_analyzer.py` - Image analysis (imported in helpers)
- ✅ `finish.py` - Submit context (imported in helpers)
- ✅ `schema.py` - Tool schemas (may have schema definitions)

### Nodes - Used in ReACT Workflow
- ✅ All nodes listed in "Active Nodes" section above

### Decision Nodes - Still Used
- ✅ `decisions/vip_compliance.py` - Still in graph

---

## 📝 NOTES

1. **Enhanced Attachment Analyzer Folder**
   - `app/tools/enhanced attachment analyzer (option 2)/` contains `attachment_analyzer.py`
   - This appears to be an alternative implementation
   - **Status:** Uncertain if used - needs investigation
   - **Recommendation:** Keep for now, investigate later

2. **Schema.py**
   - `app/tools/schema.py` may contain shared type definitions
   - **Recommendation:** Keep - likely has shared schemas

3. **Old Graph for Testing**
   - Consider keeping `graph_builder.py` temporarily if you want to compare old vs new
   - Can be deleted after confidence in ReACT workflow

---

## ✅ SAFE DELETION CHECKLIST

- [ ] Backed up repository (committed to Git)
- [ ] Updated `poll_freshdesk.py` to use ReACT graph
- [ ] Updated `run_local_server.py` to use `main_react`
- [ ] Updated `app/tools/__init__.py` exports
- [ ] Tested workflow with `test_workflow_manual.py`
- [ ] Tested poller with `poll_freshdesk.py`
- [ ] Ready to delete 11 unused files

---

## 🎯 FINAL RECOMMENDATION

**DELETE IMMEDIATELY (No Risk):**
1. `app/nodes/context_builder.py`
2. `app/nodes/orchestration_agent.py`
3. `app/nodes/text_rag_pipeline.py`
4. `app/nodes/vision_pipeline.py`
5. `app/nodes/decisions/confidence_check.py`
6. `app/nodes/decisions/enough_information.py`
7. `app/nodes/decisions/hallucination_guard.py`

**DELETE AFTER UPDATES (Low Risk):**
8. `app/graph/graph_builder.py` (after updating 3 scripts)
9. `app/tools/product_search_from_csv.py` (after updating __init__.py)
10. `app/tools/product_search_pinecone.py` (after updating __init__.py)
11. `app/main.py` (after updating run_local_server.py)

**Total Cleanup:** ~2,000+ lines of unused code removed 🎉
