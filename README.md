# Flusso Workflow - Freshdesk Multimodal Support Automation

A production-ready LangGraph-based automated support system that processes Freshdesk tickets using multimodal RAG (Retrieval-Augmented Generation) capabilities.

## 🎯 Overview

This system automatically:
- Fetches ticket details from Freshdesk
- Retrieves relevant information from multiple sources (Gemini File Search, Pinecone)
- Processes both text and image data
- Makes intelligent decisions using confidence checks and guard rails
- Generates AI-powered responses
- Updates Freshdesk with results and audit trails

## 🏗️ Architecture

**Technology Stack:**
- **Orchestration**: LangGraph
- **API Framework**: FastAPI
- **LLM**: Google Gemini
- **Vector DBs**: 
  - Gemini File Search (text documents)
  - Pinecone (image index + past tickets index)
- **Ticketing**: Freshdesk REST API

## 📁 Project Structure

```
app/
├── main.py                      # FastAPI entry point
├── graph/
│   ├── state.py                 # TicketState definition
│   └── graph_builder.py         # LangGraph construction
├── nodes/                       # Workflow nodes
│   ├── fetch_ticket.py
│   ├── routing_agent.py
│   ├── vision_pipeline.py
│   ├── text_rag_pipeline.py
│   ├── past_tickets.py
│   ├── customer_lookup.py
│   ├── vip_rules.py
│   ├── context_builder.py
│   ├── orchestration_agent.py
│   ├── decisions/               # Decision & guard nodes
│   ├── response/                # Response generation
│   ├── freshdesk_update.py
│   └── audit_log.py
├── clients/                     # External API clients
│   ├── freshdesk_client.py
│   ├── pinecone_client.py
│   ├── gemini_client.py
│   ├── embeddings.py
│   └── llm_client.py
├── services/                    # Business logic
│   ├── rag_service.py
│   ├── customer_service.py
│   └── vip_rules_service.py
├── utils/                       # Helper functions
└── config/                      # Configuration
    ├── settings.py
    └── constants.py
```

## 🚀 Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
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
- Freshdesk domain and API key
- Pinecone API key and index names
- Gemini API key and File Search store ID
- OpenAI API key (for embeddings)

## 🎬 Usage

### Run the API Server

```bash
uvicorn app.main:app --reload --port 8000
```

### Configure Freshdesk Webhook

Point your Freshdesk webhook to:
```
POST https://your-domain/freshdesk/webhook
```

## 🔄 Workflow

1. **Fetch Ticket** - Retrieve ticket details from Freshdesk
2. **Routing** - Classify ticket type
3. **Retrieval** - Query relevant sources:
   - Gemini File Search (text docs)
   - Pinecone Image Index (if images present)
   - Pinecone Past Tickets (similar resolved tickets)
4. **Customer Analysis** - Identify customer type and VIP rules
5. **Context Building** - Combine all retrieved information
6. **Decision Making** - Apply guard rails:
   - Enough information check
   - Hallucination guard
   - Product match confidence
   - VIP compliance
7. **Response Generation** - Create intelligent response
8. **Freshdesk Update** - Update ticket with response and tags
9. **Audit** - Log complete workflow

## 📋 Resolution Statuses

- `RESOLVED` - AI successfully resolved with high confidence
- `AI_UNRESOLVED` - Needs human intervention
- `LOW_CONFIDENCE_MATCH` - Product match below threshold
- `VIP_RULE_FAILURE` - VIP rules not satisfied

## 🔐 Security

- Never commit `.env` file
- Rotate API keys regularly
- Use environment-specific configurations
- Monitor audit logs for anomalies

## 📊 Monitoring

All workflow executions are logged with:
- Ticket ID
- Resolution status
- Customer type
- Detailed audit events
- Timestamps

## 🛠️ Development

See `PROJECT_CONTEXT.md` for detailed implementation guidelines.

See `IMPLEMENTATION_PLAN.md` for development roadmap.

## 📝 License

Proprietary - All rights reserved

## 📞 Support

For issues and questions, contact the development team.

---

**Last Updated**: November 29, 2025
