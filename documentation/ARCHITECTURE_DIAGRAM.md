# Centralized Logging Architecture Diagram

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    CLIENT CLOUD ENVIRONMENT                       │
│                    (Render / Google Cloud)                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                 FLUSSO WORKFLOW (FastAPI)                   │  │
│  │                                                             │  │
│  │  🎫 Ticket Arrives                                          │  │
│  │  ↓                                                          │  │
│  │  📥 fetch_ticket_from_freshdesk()                          │  │
│  │     • Records start time                                   │  │
│  │  ↓                                                          │  │
│  │  🔄 Workflow Executes                                       │  │
│  │     • Planner                                              │  │
│  │     • ReACT Agent                                          │  │
│  │     • Vision Search                                        │  │
│  │     • Text RAG                                             │  │
│  │     • Evidence Resolution                                  │  │
│  │     • Draft Response                                       │  │
│  │  ↓                                                          │  │
│  │  📝 write_audit_log()                                       │  │
│  │     • Build centralized log (in-memory)                    │  │
│  │     • ship_log_async() ← FIRE-AND-FORGET                   │  │
│  │     • Return immediately                                   │  │
│  │  ↓                                                          │  │
│  │  ✅ Workflow Complete                                       │  │
│  │                                                             │  │
│  │  (Background: HTTP POST happens here)                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            │ HTTPS POST                           │
│                            │ (async, non-blocking)                │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                     YOUR INFRASTRUCTURE                           │
│                  (Phase 4 & 5 - To Be Built)                      │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │           LOG COLLECTOR API (FastAPI)                       │  │
│  │                                                             │  │
│  │  POST /api/v1/logs                                         │  │
│  │  • Verify API key                                          │  │
│  │  • Store log in database                                   │  │
│  │  • Return 200 OK                                           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │         PostgreSQL Database (JSONB)                         │  │
│  │                                                             │  │
│  │  logs_table                                                │  │
│  │  ├── id (serial)                                           │  │
│  │  ├── client_id (text)                                      │  │
│  │  ├── ticket_id (text)                                      │  │
│  │  ├── status (text)                                         │  │
│  │  ├── executed_at (timestamp)                               │  │
│  │  ├── log_data (jsonb) ← Full log here                     │  │
│  │  └── created_at (timestamp)                                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │         ANALYTICS DASHBOARD (React/Next.js)                 │  │
│  │                                                             │  │
│  │  📊 Overview                                               │  │
│  │  • Total tickets processed                                 │  │
│  │  • Success rate                                            │  │
│  │  • Average confidence                                      │  │
│  │                                                             │  │
│  │  🔍 Search & Filter                                        │  │
│  │  • By client                                               │  │
│  │  • By date range                                           │  │
│  │  • By status                                               │  │
│  │                                                             │  │
│  │  📄 Detailed Log Viewer                                    │  │
│  │  • Full execution trace                                    │  │
│  │  • ReACT iterations                                        │  │
│  │  • Retrieval results                                       │  │
│  │  • Decisions & reasoning                                   │  │
│  │                                                             │  │
│  │  👥 Multi-Tenant Access                                    │  │
│  │  • You (service provider)                                  │  │
│  │  • Client (their own data only)                            │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Log Building (Phase 2)

```
TicketState
    ↓
build_workflow_log(state, start_time, end_time)
    ↓
    ├─ Extract metrics
    ├─ Build trace
    ├─ Hash PII
    ├─ Sanitize sensitive data
    ↓
Structured JSON Log
```

### 2. Log Shipping (Phase 3)

```
Log JSON
    ↓
ship_log_async(log_payload)  ← Returns immediately
    ↓
asyncio.create_task(_send_log_background)
    ↓
(Background Task)
    ├─ Prepare headers
    ├─ Add API key
    ├─ HTTP POST to collector
    ├─ Timeout after 10s
    └─ Catch all errors
    ↓
Success or silent failure
```

### 3. Log Structure

```json
{
  "identification": {
    "client_id": "...",
    "environment": "...",
    "workflow_version": "..."
  },
  
  "ticket_info": {
    "ticket_id": "...",
    "executed_at": "...",
    "execution_time_seconds": 4.82
  },
  
  "outcome": {
    "status": "SUCCESS",
    "resolution_status": "..."
  },
  
  "metrics": {
    "react_iterations": 5,
    "overall_confidence": 0.82,
    "hallucination_risk": 0.12,
    // ... 15+ metrics
  },
  
  "trace": {
    "ticket": {...},
    "planning": {...},
    "react": {...},
    "retrieval": {...},
    "evidence": {...},
    "output": {...}
  }
}
```

## Key Design Features

### 🔒 Privacy Protection

```
Raw Data              →  Hashed Data
─────────────────────────────────────
user@example.com      →  a3f9d8e2b1c5
John Doe              →  d8f3e1a9c7b2
"Fix my sink"         →  f2e4a6b8c0d1
```

### ⚡ Fire-and-Forget Shipping

```
Main Thread              Background Task
─────────────────────────────────────
ship_log_async()    →   [Task Created]
Returns in <1ms     →   HTTP POST (async)
                    →   10s timeout
Workflow continues  →   Success/Failure
                        (logged, not raised)
```

### 🛡️ Error Resilience

```
Error Type              Behavior
────────────────────────────────────
No collector URL   →   Warning log, continue
Cannot connect     →   Warning log, continue
Timeout            →   Warning log, continue
API error          →   Warning log, continue
JSON error         →   Error log, continue

Result: WORKFLOW NEVER FAILS
```

## Workflow Timeline

```
Time    Node                    Action
─────────────────────────────────────────────────────────────
0.0s    fetch_ticket           📍 Record start time
0.5s    planner                Execute
1.2s    react_agent            Execute
2.8s    vision_search          Execute
3.1s    text_rag               Execute
3.9s    evidence_resolver      Execute
4.5s    draft_response         Execute
4.8s    audit_log              📝 Build log
4.81s   audit_log              🚀 ship_log_async()
4.82s   audit_log              ✅ RETURN (workflow complete)
        
        (Background, async)
5.2s    [background]           📤 HTTP POST starts
5.8s    [background]           ✅ Log delivered
```

**Key Point:** Workflow completes at 4.82s, doesn't wait for HTTP (5.8s)

## Configuration Flow

```
.env file
    ↓
Settings (Pydantic)
    ↓
    ├─ CLIENT_ID
    ├─ LOG_COLLECTOR_URL
    ├─ LOG_COLLECTOR_API_KEY
    └─ ENVIRONMENT
    ↓
Log Shipper
    ↓
HTTP Headers
    ├─ X-API-Key: <API_KEY>
    ├─ Content-Type: application/json
    └─ User-Agent: Flusso-Workflow/v1.0
```

## Implementation Phases

```
✅ Phase 1: Foundation
   └─ Log schema defined
   └─ Privacy functions
   └─ Sanitization

✅ Phase 2: Building
   └─ State → Log transformation
   └─ Metric extraction
   └─ Trace compilation

✅ Phase 3: Shipping
   └─ Fire-and-forget HTTP
   └─ Error handling
   └─ Configuration

⏳ Phase 4: Collector (YOUR SIDE)
   └─ FastAPI endpoint
   └─ Database storage
   └─ Authentication

⏳ Phase 5: Dashboard (YOUR SIDE)
   └─ Web UI
   └─ Analytics
   └─ Log viewer
```

---

**Architecture Status:** ✅ Client Side Complete (Phases 1-3)
