# Flusso Workflow

An intelligent AI-powered workflow automation system for Freshdesk customer support, featuring multi-agent orchestration, document analysis, and automated ticket resolution.

## 🌟 Overview

Flusso Workflow is an advanced customer support automation platform that leverages LangGraph and Google Gemini AI to intelligently process, analyze, and respond to Freshdesk tickets. The system uses a multi-agent architecture with specialized agents for routing, planning, orchestration, and response generation.

## ✨ Key Features

- **Multi-Agent Architecture**: Specialized agents for different aspects of ticket processing
  - Routing Agent: Intelligent ticket classification and prioritization
  - Planning Agent: Strategic workflow planning
  - Orchestration Agent: Coordinates multiple agents and tools
  - ReAct Agent: Reasoning and action-taking agent

- **Advanced Document Processing**
  - OCR image analysis for scanned documents
  - Multimodal document analyzer
  - Attachment classification and processing
  - Vision-based search capabilities

- **Smart Ticket Management**
  - Automated ticket fetching and updates
  - Customer lookup and history analysis
  - Past tickets analysis for context
  - VIP customer rules and compliance

- **Product Catalog Integration**
  - Pinecone vector database integration
  - CSV-based product search
  - Cached product catalog for performance

- **Security & Compliance**
  - PII masking for sensitive data
  - Audit logging for all operations
  - Evidence resolver for compliance tracking
  - VIP compliance decision engine

- **Robust Infrastructure**
  - Centralized logging system
  - Retry mechanisms with exponential backoff
  - Detailed workflow logging
  - Health monitoring and validation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Freshdesk API                      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│            Polling Service / Webhook                │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              Routing Agent                          │
│         (Classify & Prioritize)                     │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│            Planning Agent                           │
│         (Strategy & Workflow)                       │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│        Orchestration Agent                          │
│    (Coordinate Tools & Agents)                      │
└─────┬─────────┬─────────┬──────────┬────────────────┘
      │         │         │          │
      ▼         ▼         ▼          ▼
  ┌───────┐ ┌──────┐ ┌────────┐ ┌─────────┐
  │Product│ │Vision│ │Document│ │Customer │
  │Search │ │Search│ │Analysis│ │Lookup   │
  └───────┘ └──────┘ └────────┘ └─────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│          Response Generation                        │
│      (Draft & Finalize Response)                    │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│         Freshdesk Update                            │
└─────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
app/
├── clients/           # External service clients
│   ├── freshdesk_client.py
│   ├── gemini_client.py
│   ├── pinecone_client.py
│   └── llm_client.py
├── config/            # Configuration and settings
│   ├── constants.py
│   └── settings.py
├── graph/             # LangGraph workflow definitions
│   ├── graph_builder_react.py
│   └── state.py
├── nodes/             # Workflow nodes/agents
│   ├── routing_agent.py
│   ├── planner.py
│   ├── orchestration_agent.py
│   ├── react_agent.py
│   ├── customer_lookup.py
│   ├── past_tickets.py
│   ├── fetch_ticket.py
│   ├── freshdesk_update.py
│   ├── audit_log.py
│   ├── decisions/     # Decision-making nodes
│   └── response/      # Response generation
├── tools/             # Agent tools
│   ├── document_search.py
│   ├── product_search_pinecone.py
│   ├── attachment_analyzer.py
│   ├── ocr_image_analyzer.py
│   ├── multimodal_document_analyzer.py
│   └── vision_search.py
├── services/          # Business logic services
│   ├── policy_service.py
│   ├── product_catalog.py
│   └── product_catalog_cache.py
└── utils/             # Utility functions
    ├── audit.py
    ├── detailed_logger.py
    ├── pii_masker.py
    ├── retry.py
    ├── validation.py
    └── workflow_log_builder.py
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Freshdesk account with API access
- Google Gemini API key
- Pinecone account (optional, for vector search)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Flusso workflow"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1  # Windows
   # or
   source .venv/bin/activate    # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # Freshdesk Configuration
   FRESHDESK_DOMAIN=your-domain.freshdesk.com
   FRESHDESK_API_KEY=your_api_key
   
   # Gemini AI Configuration
   GEMINI_API_KEY=your_gemini_api_key
   
   # Pinecone Configuration (Optional)
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_INDEX_NAME=your_index_name
   
   # Application Settings
   LOG_LEVEL=INFO
   ENVIRONMENT=development
   ```

### Running Locally

**For Local Development with Webhooks:**
```bash
# Terminal 1: Start the webhook server
python run_local_server.py

# Terminal 2: Expose local server to internet (for Freshdesk webhooks)
ngrok http 8000

# Configure Freshdesk webhook with ngrok URL: https://xxx.ngrok.io/webhook
```

**For Testing Without Freshdesk:**
```bash
python test_workflow_manual.py
```

> **Note**: `poll_freshdesk.py` is for local testing only. Production uses webhook-based architecture.

The API will be available at `http://localhost:8000`

### API Endpoints

- `POST /webhook` - **Main Freshdesk webhook endpoint** (production)
- `GET /health` - Health check endpoint
- `GET /health/deep` - Detailed health check
- `POST /debug/process/{ticket_id}` - Manual ticket processing for debugging
- `GET /info` - Workflow configuration information

## ☁️ Production Deployment

### Google Cloud Run (Recommended) ⭐

Cloud Run is the recommended deployment platform for this webhook-based application:

- **Serverless**: Auto-scaling from 0 to hundreds of instances
- **Cost-effective**: Pay only for actual usage
- **Easy deployment**: Simple one-command deployment
- **Built-in HTTPS**: Secure webhook endpoint out of the box

**Quick Deploy:**
```bash
# See QUICKSTART_CLOUD_RUN.md for complete instructions
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/flusso-webhook -f Dockerfile.cloudrun
gcloud run deploy flusso-webhook --image gcr.io/YOUR_PROJECT_ID/flusso-webhook
```

📖 **[Complete Google Cloud Deployment Guide →](GOOGLE_CLOUD_DEPLOYMENT.md)**

### Other Deployment Options

### Local Testing
```bash
# Test workflow with a specific ticket ID
python test_workflow_manual.py
```

### Production Testing
```bash
# Health check
curl https://your-service-url/health

# Debug endpoint (test with specific ticket)
curl -X POST https://your-service-url/debug/process/123

# Test webhook with sample payload
curl -X POST https://your-service-url/webhook \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "123"}'ployment on any platform

See [GOOGLE_CLOUD_DEPLOYMENT.md](GOOGLE_CLOUD_DEPLOYMENT.md) for detailed instructions on all deployment options.

## 🧪 Testing

Run the test workflow manually:
```bash
python test_workflow_manual.py
```

## 📊 Logging & Monitoring

The system includes comprehensive logging:

- **Centralized Logging**: All components use standardized logging
- **Audit Trail**: Complete audit logs for compliance
- **Workflow Logs**: Detailed step-by-step execution tracking
- **PII Masking**: Automatic masking of sensitive information

Logs are structured in JSON format for easy parsing and analysis.

## 🔧 Configuration

Key configuration files:

- `app/config/settings.py` - Application settings
- `app/config/constants.py` - System constants
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `render.yaml` - Render deployment config

## 📖 Documentation

Additional documentation available in the `documentation/` folder:

- [Architecture Diagram](documentation/ARCHITECTURE_DIAGRAM.md)
- [Centralized Logging Implementation](documentation/CENTRALIZED_LOGGING_IMPLEMENTATION.md)
- [Cleanup Analysis](documentation/CLEANUP_ANALYSIS.md)
- [Implementation Summary](documentation/IMPLEMENTATION_SUMMARY.md)
- [Quick Start Logging](documentation/QUICK_START_LOGGING.md)
- [Testing Report](documentation/TESTING_REPORT.md)

## 🛠️ Development

### Code Structure

- **Nodes**: Individual workflow steps (agents, processors)
- **Tools**: Utilities that agents can use
- **Clients**: External service integrations
- **Services**: Business logic layer
- **Utils**: Helper functions and utilities

### Adding New Features

1. Create new nodes in `app/nodes/`
2. Define tools in `app/tools/`
3. Update graph in `app/graph/graph_builder_react.py`
4. Add tests in root directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

[Add your license information here]

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review logs for troubleshooting

## 🔐 Security

- All sensitive data is masked using PII masker
- API keys should be stored in environment variables
- Audit logs track all operations
- Regular security updates recommended

## 📈 Performance

- Product catalog caching for faster lookups
- Retry mechanisms for resilience
- Optimized vector search with Pinecone
- Async processing where applicable

## 🎯 Roadmap

- [ ] Additional AI model support
- [ ] Enhanced analytics dashboard
- [ ] Multi-language support
- [ ] Advanced reporting features
- [ ] Integration with more ticketing systems

---

**Built with ❤️ using LangGraph, Google Gemini, and FastAPI**
