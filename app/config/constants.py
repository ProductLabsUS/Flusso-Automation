"""
Constants and Enums for the Application
Centralized definitions for status codes, categories, thresholds
"""

from enum import Enum


class ResolutionStatus(str, Enum):
    """Possible resolution statuses for tickets"""
    RESOLVED = "RESOLVED"
    AI_UNRESOLVED = "AI_UNRESOLVED"
    LOW_CONFIDENCE_MATCH = "LOW_CONFIDENCE_MATCH"
    VIP_RULE_FAILURE = "VIP_RULE_FAILURE"


class CustomerType(str, Enum):
    """Customer classification types"""
    VIP = "VIP"
    DISTRIBUTOR = "DISTRIBUTOR"
    NORMAL = "NORMAL"
    INTERNAL = "INTERNAL"


class TicketCategory(str, Enum):
    """Ticket classification categories"""
    WARRANTY = "warranty"
    PRODUCT_ISSUE = "product_issue"
    INSTALLATION_HELP = "install_help"
    BILLING = "billing"
    GENERAL = "general"
    SPAM = "spam"


class TicketPriority(int, Enum):
    """Freshdesk ticket priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TicketStatus(int, Enum):
    """Freshdesk ticket status codes"""
    OPEN = 2
    PENDING = 3
    RESOLVED = 4
    CLOSED = 5


# ==========================================
# DEFAULT THRESHOLDS
# ==========================================

# These can be overridden by environment variables
DEFAULT_HALLUCINATION_THRESHOLD = 0.4
DEFAULT_CONFIDENCE_THRESHOLD = 0.6
DEFAULT_TEXT_RETRIEVAL_TOP_K = 10
DEFAULT_IMAGE_RETRIEVAL_TOP_K = 5
DEFAULT_PAST_TICKET_TOP_K = 5


# ==========================================
# LLM CONFIGURATION
# ==========================================

DEFAULT_LLM_MODEL = "gemini-2.0-flash-exp"
DEFAULT_LLM_TEMPERATURE = 0.2
DEFAULT_LLM_MAX_TOKENS = 2048


# ==========================================
# CLIP MODEL CONFIGURATION
# ==========================================

CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "openai"
CLIP_EMBEDDING_DIM = 512


# ==========================================
# SYSTEM PROMPTS
# ==========================================

ROUTING_SYSTEM_PROMPT = """You are a routing agent for customer support tickets.

Classify the ticket into one of these categories:
- warranty: Warranty claims, warranty extensions, coverage questions
- product_issue: Product defects, malfunctions, quality issues
- install_help: Installation questions, setup guidance, technical support
- billing: Pricing questions, payment issues, invoices
- general: General inquiries, product information
- spam: Spam, irrelevant messages

Respond ONLY with valid JSON in this exact format:
{"category": "<category_name>"}

Do not include any explanation or additional text."""

ORCHESTRATION_SYSTEM_PROMPT = """You are a support orchestration agent that helps human agents by analyzing customer tickets with retrieved knowledge.

Your role is to be a HELPFUL COMPANION for support agents - provide useful information even if not 100% certain.

Your task:
1. Understand the customer's issue based on the ticket and retrieved context
2. Identify the product(s) involved if possible
3. Summarize relevant information that could help the human agent

Retrieved context includes:
- Product documentation and manuals
- Similar past tickets and resolutions
- Product images and specifications
- VIP customer rules (if applicable)

Respond ONLY with valid JSON in this exact format:
{
  "summary": "<brief summary of the issue>",
  "product_id": "<product model number or null if unclear>",
  "reasoning": "<your analysis of the available information>",
  "enough_information": true/false
}

Set enough_information to TRUE if you found ANY relevant context that could help the agent.
Only set FALSE if the retrieved context has absolutely nothing related to the query."""

HALLUCINATION_GUARD_PROMPT = """You are a hallucination risk assessor for an AI agent assistant system.

IMPORTANT: This AI assists human support agents (not customers directly), so we can be somewhat lenient.
The goal is to surface useful information, not to be overly cautious.

Analyze whether answering this ticket requires inventing unsupported facts.

Consider:
- Is there ANY relevant information in the retrieved knowledge?
- Can partial information still be useful to the human agent?
- Is there a reasonable connection between the query and retrieved content?

Respond ONLY with valid JSON in this exact format:
{"risk": <number between 0.0 and 1.0>}

Where:
- 0.0-0.3 = Low risk, good supporting knowledge found
- 0.4-0.6 = Moderate risk, partial info available (still useful for agent)
- 0.7-1.0 = High risk, almost no relevant knowledge found"""

PRODUCT_CONFIDENCE_PROMPT = """You are a product identification confidence evaluator for an AI agent assistant.

IMPORTANT: This assists human agents, so partial matches are still valuable.
Even a likely product match helps the agent investigate faster.

Assess product match confidence based on the ticket and retrieved information.

Consider:
- Is there ANY product that seems related to the query?
- Could the retrieved products help narrow down the search?
- Even if not exact, is the product category correct?

Respond ONLY with valid JSON in this exact format:
{"confidence": <number between 0.0 and 1.0>}

Where:
- 0.0-0.2 = No relevant products found at all
- 0.3-0.5 = Related product category but uncertain exact model
- 0.6-0.8 = Likely correct product, minor uncertainty
- 0.9-1.0 = Clear, confident product identification"""

VIP_COMPLIANCE_PROMPT = """You are a VIP rule compliance checker.

Given the customer request, VIP rules, and available product/warranty information, determine if the requested action complies with VIP rules.

VIP rules may include:
- Extended warranty periods
- Free replacement allowances
- Priority shipping
- Price matching guarantees

Respond ONLY with valid JSON in this exact format:
{
  "vip_compliant": true/false,
  "reason": "<brief explanation>"
}"""

DRAFT_RESPONSE_PROMPT = """You are an AI assistant helping human support agents respond to customer tickets for a plumbing fixtures company.

Your role: Generate a DRAFT response that the human agent can review, edit, and send.

Context provided:
- Customer ticket
- Retrieved product documentation
- Past similar tickets and their resolutions
- VIP customer rules (if applicable)
- Decision metrics (for your awareness)

Your task:
Generate a helpful draft response that the agent can use as a starting point.

1. Always provide a substantive response based on retrieved context
2. Include relevant product information, warranty terms, or solutions found
3. If you're uncertain about something, phrase it as a suggestion:
   - "Based on the product documentation, it appears that..."
   - "A similar ticket was resolved by..."
4. If truly no relevant info exists, suggest what the agent should look up

Response guidelines:
- Use friendly, professional tone
- Cite specific product models when identified  
- Reference similar past ticket resolutions when helpful
- Be concise and actionable
- DO NOT mention internal scores or system metrics to the customer
- Mark uncertain parts with [VERIFY] so agent knows to double-check

Write your response naturally without JSON formatting."""


# ==========================================
# TAG DEFINITIONS
# ==========================================

SYSTEM_TAGS = [
    "AI_UNRESOLVED",
    "LOW_CONFIDENCE_MATCH",
    "VIP_RULE_FAILURE",
    "AI_PROCESSED",
    "NEEDS_HUMAN_REVIEW",
]
