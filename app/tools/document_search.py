"""
Document Search Tool - Gemini File Search (PRIMARY KNOWLEDGE BASE)
The most important tool for product information - contains ALL parts specifications,
product manuals, installation guides, troubleshooting docs, and technical diagrams.
"""

import logging
from typing import Dict, Any, Optional, List
from langchain.tools import tool

from app.clients.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)


@tool
def document_search_tool(
    query: str,
    product_context: Optional[str] = None,
    top_k: int = 8
) -> Dict[str, Any]:
    """
    🌟 PRIMARY KNOWLEDGE BASE - Gemini File Search
    
    This is the MOST IMPORTANT tool for product information. It contains
    comprehensive documentation for ALL Flusso products.
    
    ═══════════════════════════════════════════════════════════════════════
    📚 WHAT THIS TOOL CONTAINS (COMPREHENSIVE LIBRARY):
    ═══════════════════════════════════════════════════════════════════════
    
    ✅ PRODUCT MANUALS & SPECIFICATIONS:
       - Complete product specification sheets (dimensions, materials, finishes)
       - Technical diagrams with measurements
       - Flow rates, pressure ratings, certifications
       - Compatibility information
    
    ✅ PARTS LISTS & DIAGRAMS:
       - Exploded parts diagrams showing ALL components
       - Part numbers for every component (cartridges, handles, valves, etc.)
       - MSRP/pricing for replacement parts
       - Which parts fit which products
    
    ✅ INSTALLATION GUIDES:
       - Step-by-step installation instructions
       - Required tools and materials
       - Rough-in dimensions and requirements
       - Mounting templates and clearances
    
    ✅ TROUBLESHOOTING & REPAIR:
       - Common problems and solutions
       - Diagnostic steps for issues (leaks, low pressure, etc.)
       - Repair procedures with diagrams
       - When to replace vs repair
    
    ✅ POLICY DOCUMENTS:
       - Warranty terms and coverage
       - Return/refund policies
       - MAP pricing agreements
       - Dealer program information
    
    ═══════════════════════════════════════════════════════════════════════
    ❌ WHAT THIS TOOL DOES NOT CONTAIN:
    ═══════════════════════════════════════════════════════════════════════
    ❌ Customer order information or purchase history
    ❌ Purchase orders or invoices
    ❌ Shipping/tracking information
    ❌ Customer account details
    
    ⚠️ CRITICAL: Do NOT search with order numbers - they are NOT product identifiers!
    
    ═══════════════════════════════════════════════════════════════════════
    🎯 WHEN TO USE THIS TOOL:
    ═══════════════════════════════════════════════════════════════════════
    
    USE FOR:
    • "What's the part number for the cartridge in model X?" → Parts list
    • "How do I install the 100.2420?" → Installation guide
    • "My faucet is leaking from the handle" → Troubleshooting guide
    • "What are the dimensions of model Y?" → Spec sheet
    • "Is this product compatible with..." → Technical specs
    • "What's covered under warranty?" → Policy documents
    • "How do I become a dealer?" → Dealer program info
    • ANY question about product specifications, parts, or installation
    
    Args:
        query: The specific information you need. Be detailed!
               Examples:
               - "replacement cartridge part number for diverter valve"
               - "installation rough-in dimensions and mounting requirements"
               - "troubleshooting steps for handle that won't turn off"
               - "warranty coverage for chrome finish discoloration"
        product_context: The product model number or name (IMPORTANT for accuracy)
                        Examples: "100.2420MB", "Serie 100 tub faucet", "PBV1005"
        top_k: Number of documents to retrieve (default: 8)
    
    Returns:
        {
            "success": bool,
            "documents": [...],      # Relevant documents with previews
            "gemini_answer": str,    # AI-synthesized answer from documents
            "count": int,
            "message": str
        }
    """
    logger.info(f"[DOCUMENT_SEARCH] Query: '{query}', Product Context: {product_context}")
    
    try:
        if not query or not str(query).strip():
            return {
                "success": False,
                "documents": [],
                "gemini_answer": "",
                "count": 0,
                "message": "Query text is required for document search"
            }

        # Keep top_k within sane bounds to avoid overwhelming the API/LLM
        top_k = max(1, min(int(top_k), 15))
        clean_query = str(query).strip()

        client = get_gemini_client()
        
        # Determine the search strategy based on context
        search_type = _determine_search_type(clean_query)
        
        # Build context-aware query with improved formatting for better Gemini results
        if product_context:
            # Extract model number from product context if available
            model_number = _extract_model_number(product_context)
            
            # Build product-specific search query (enhanced synthesis prompt)
            search_query = f"""
═══════════════════════════════════════════════════════════════════════
PRODUCT-SPECIFIC DOCUMENTATION SEARCH
═══════════════════════════════════════════════════════════════════════

**Target Product:** {product_context}
**Model Number:** {model_number if model_number else "Not specified"}
**Customer Query:** {clean_query}

═══════════════════════════════════════════════════════════════════════
SEARCH INSTRUCTIONS (CRITICAL):
═══════════════════════════════════════════════════════════════════════

1. **PRIORITIZE** documents that specifically mention model "{model_number or product_context}"
2. Search across ALL document types:
   - Product specification sheets and datasheets
   - Parts diagrams and exploded views
   - Parts lists with part numbers and pricing
   - Installation manuals and guides
   - Troubleshooting guides and FAQs
   
3. **EXTRACT** specific information:
   - Part numbers (format: XXX.XXXX or similar)
   - Dimensions and measurements
   - Step-by-step instructions
   - Compatibility information
   - Pricing/MSRP when available

4. **DOCUMENT PRIORITY ORDER:**
   1. Product manual/datasheet for {model_number or product_context}
   2. Parts diagram showing all components and part numbers
   3. Installation guide with step-by-step instructions
   4. Troubleshooting guide for specific issues
   5. Warranty/policy documents (only if query relates to warranty/returns)

═══════════════════════════════════════════════════════════════════════
RESPONSE FORMAT:
═══════════════════════════════════════════════════════════════════════

Provide a comprehensive answer that includes:
- Direct answer to the customer's question
- Specific part numbers when relevant
- Step-by-step instructions if applicable
- Dimensions/specifications if relevant
- Cite the exact document source for each piece of information

Be thorough and technical - this information will help support agents assist customers.
"""
        else:
            search_query = f"""
═══════════════════════════════════════════════════════════════════════
CUSTOMER SUPPORT DOCUMENTATION SEARCH
═══════════════════════════════════════════════════════════════════════

**Customer Query:** {clean_query}

═══════════════════════════════════════════════════════════════════════
SEARCH INSTRUCTIONS:
═══════════════════════════════════════════════════════════════════════

Find the most relevant documentation to answer this customer's question.

**DOCUMENT PRIORITY ORDER:**
1. Installation guides - if asking about setup/mounting/assembly
2. Troubleshooting guides - if reporting problems/defects/leaks
3. Parts diagrams and lists - if asking about missing/replacement parts
4. Product specifications - if asking about dimensions/compatibility/features
5. Warranty/policy documents - if asking about coverage/claims/returns
6. Dealer program info - if asking about partnerships/accounts

**EXTRACT AND INCLUDE:**
- Specific part numbers when relevant
- Step-by-step instructions
- Dimensions and specifications
- Policy terms and conditions
- Contact information if applicable

Provide actionable information that support agents can use immediately.
Cite the exact document source for each piece of information.
"""
        
        # Build context-aware system instruction (enhanced synthesis approach)
        if product_context:
            model_number = _extract_model_number(product_context)
            system_instruction = f"""You are a Product Support Expert Assistant for Flusso Faucets.

**Your Role:**
Help support agents research product information quickly and accurately. Provide comprehensive answers about products, installation, specifications, and troubleshooting.

**CRITICAL: Focus on product model "{model_number or product_context}"**

**Guidelines:**

1. **Prioritize Data Sources:**
   - For PRODUCT-SPECIFIC QUERIES: Start with specifications, parts lists, and technical documentation
   - Search product manuals, datasheets, and parts diagrams for the specific model
   - Include part numbers, dimensions, and step-by-step instructions

2. **Response Structure:**
   - Begin with a direct answer to the question
   - Include relevant specifications (dimensions, part numbers, materials)
   - Provide step-by-step instructions for installation/troubleshooting
   - Reference video/image resources when available
   - End with source citations

3. **Accuracy:**
   - Only provide information from the given documents
   - If information is missing, explicitly state it
   - Never make up specifications or part numbers
   - Distinguish between different product variants (finishes, sizes)

4. **Be Thorough:**
   - Include ALL relevant part numbers found
   - List ALL steps in procedures
   - Mention ALL compatibility requirements
   - Note ANY warnings or precautions

**Document Types to Search:**
- Product specification sheets
- Parts diagrams with part numbers
- Installation manuals
- Troubleshooting guides
- Warranty documentation (only if relevant)

Cite the exact document source for each piece of information."""
        else:
            system_instruction = """You are a Product Support Expert Assistant for Flusso Faucets.

**Your Role:**
Help support agents research product information quickly and accurately. Provide comprehensive answers about products, installation, specifications, policies, and troubleshooting.

**Guidelines:**

1. **Prioritize Data Sources:**
   - For GENERAL QUERIES (policies, warranties, programs): Use policy documents
   - For PRODUCT QUERIES: Use specification sheets, manuals, parts lists
   - For TROUBLESHOOTING: Use troubleshooting guides and FAQs

2. **Response Structure:**
   - Begin with a direct answer to the question
   - Include relevant details (specifications, steps, requirements)
   - Reference document sources
   - End with source citations

3. **Accuracy:**
   - Only provide information from the given documents
   - If information is missing or unclear, explicitly state it
   - Never make up specifications or instructions

4. **Be Thorough:**
   - Include ALL relevant information found
   - List ALL steps in procedures
   - Note ANY important conditions or requirements

Cite the exact document source for each piece of information."""
        
        # Execute Gemini File Search with sources
        result = client.search_files_with_sources(
            query=search_query,
            top_k=top_k,
            system_instruction=system_instruction
        )
        
        hits = result.get('hits', [])
        gemini_answer = result.get('gemini_answer', '')
        source_documents = result.get('source_documents', [])
        
        if not source_documents:
            if gemini_answer:
                logger.warning("[DOCUMENT_SEARCH] No grounded sources, returning Gemini answer as fallback")
                return {
                    "success": True,
                    "documents": [{
                        "id": "gemini_answer",
                        "title": "Gemini Generated Answer",
                        "content_preview": gemini_answer[:500],
                        "relevance_score": 0.8,
                        "source_type": "gemini_generated",
                        "uri": ""
                    }],
                    "gemini_answer": gemini_answer,
                    "count": 1,
                    "message": "Returned generated answer (no grounded documents)",
                    "source_documents": [],
                    "hits": hits
                }

            return {
                "success": False,
                "documents": [],
                "gemini_answer": gemini_answer,
                "count": 0,
                "message": "No relevant documentation found"
            }
        
        # Format documents for ReACT agent
        documents = []
        # Try to map hits to titles for richer previews
        hit_lookup = {}
        for hit in hits:
            title = hit.get("metadata", {}).get("title", "")
            if title:
                hit_lookup[title.lower()] = hit

        for idx, doc in enumerate(source_documents[:top_k]):
            title = doc.get("title", "Unknown Document")
            lower_title = title.lower()
            mapped_hit = hit_lookup.get(lower_title)
            # Prefer preview text from hit.content when available
            content_preview = doc.get("content_preview", "")
            if mapped_hit and mapped_hit.get("content"):
                preview_from_hit = str(mapped_hit.get("content", ""))[:500]
                if preview_from_hit:
                    content_preview = preview_from_hit

            uri = doc.get("uri") or (mapped_hit.get("metadata", {}).get("uri") if mapped_hit else "")
            doc_id = doc.get("id") or (mapped_hit.get("id") if mapped_hit else f"doc_{idx}")

            documents.append({
                "id": doc_id,
                "title": title,
                "content_preview": content_preview,
                "relevance_score": doc.get("relevance_score", 0),
                "source_type": _infer_document_type(title),
                "rank": doc.get("rank", 0),
                "uri": uri
            })
        
        logger.info(f"[DOCUMENT_SEARCH] Found {len(documents)} relevant document(s)")
        
        return {
            "success": True,
            "documents": documents,
            "gemini_answer": gemini_answer,
            "count": len(documents),
            "message": f"Found {len(documents)} relevant document(s)",
            # Return raw sources/hits for deeper debugging or downstream enrichment
            "source_documents": source_documents,
            "hits": hits
        }
        
    except Exception as e:
        logger.error(f"[DOCUMENT_SEARCH] Error: {e}", exc_info=True)
        return {
            "success": False,
            "documents": [],
            "gemini_answer": "",
            "count": 0,
            "message": f"Document search failed: {str(e)}"
        }


def _infer_document_type(title: str) -> str:
    """Infer document type from title"""
    title_lower = title.lower()
    
    if any(kw in title_lower for kw in ["install", "assembly", "setup"]):
        return "installation_guide"
    elif any(kw in title_lower for kw in ["manual", "user guide", "instructions"]):
        return "user_manual"
    elif any(kw in title_lower for kw in ["warranty", "guarantee"]):
        return "warranty"
    elif any(kw in title_lower for kw in ["faq", "troubleshoot", "problem"]):
        return "troubleshooting"
    elif any(kw in title_lower for kw in ["parts", "components", "diagram"]):
        return "parts_list"
    elif any(kw in title_lower for kw in ["spec", "technical", "dimension"]):
        return "specifications"
    else:
        return "general_documentation"


def _extract_model_number(product_context: str) -> Optional[str]:
    """
    Extract model number from product context.
    Model numbers typically follow patterns like: 100.1050SB, ABC-123, PROD-456-XL
    """
    import re
    
    if not product_context:
        return None
    
    # Common model number patterns:
    # 1. Alphanumeric with dots: 100.1050SB
    # 2. Letters-numbers: ABC123, PROD456
    # 3. Hyphenated: ABC-123-XL
    patterns = [
        r'\b(\d{3}\.\d{4}[A-Z]{1,3})\b',  # Pattern: 100.1050SB
        r'\b([A-Z]{2,5}-\d{3,5}(?:-[A-Z]{1,3})?)\b',  # Pattern: PROD-123-XL
        r'\b([A-Z]{2,4}\d{3,6}[A-Z]{0,3})\b',  # Pattern: ABC123, PROD456XL
        r'\b(\d{2,3}-\d{3,4}[A-Z]{0,3})\b',  # Pattern: 10-1234AB
    ]
    
    for pattern in patterns:
        match = re.search(pattern, product_context, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    # Fallback: look for any word that looks like a model number (mix of letters and numbers)
    words = product_context.split()
    for word in words:
        # Has both letters and numbers, reasonable length
        if (any(c.isdigit() for c in word) and 
            any(c.isalpha() for c in word) and 
            4 <= len(word) <= 15):
            return word.upper()
    
    return None


def _determine_search_type(query: str) -> str:
    """
    Determine the type of search based on query content.
    This helps in prioritizing different document types.
    """
    query_lower = query.lower()
    
    # Issue type detection
    if any(kw in query_lower for kw in ["replace", "replacement", "new one", "send another"]):
        return "replacement_request"
    elif any(kw in query_lower for kw in ["install", "setup", "assemble", "mount"]):
        return "installation"
    elif any(kw in query_lower for kw in ["broken", "damage", "defect", "leak", "not working"]):
        return "troubleshooting"
    elif any(kw in query_lower for kw in ["warranty", "guarantee", "coverage"]):
        return "warranty"
    elif any(kw in query_lower for kw in ["missing", "parts", "component"]):
        return "parts_inquiry"
    elif any(kw in query_lower for kw in ["dimension", "size", "compatible", "fit"]):
        return "specifications"
    else:
        return "general"
