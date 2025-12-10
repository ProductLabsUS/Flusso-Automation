"""
Attachment Analyzer Tool - FIXED
Properly extracts model numbers and entities from ticket attachments
"""

import logging
from typing import Dict, Any, List, Optional
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def attachment_analyzer_tool(
    attachments: Optional[List[Dict[str, Any]]] = None,
    focus: str = "model_numbers",
) -> Dict[str, Any]:
    """
    Analyze ticket attachments to extract model numbers, part numbers, and entities.
    
    CRITICAL: This tool should be called FIRST if attachments are present.
    
    Args:
        attachments: List of attachment dicts with 'name', 'attachment_url', 'content_type'
        focus: What to focus on - "model_numbers" (default), "order_info", or "general"
    
    Returns:
        {
            "success": bool,
            "extracted_info": {
                "model_numbers": [str],  # Product model numbers found
                "part_numbers": [str],   # Part numbers found
                "order_numbers": [str],  # PO/Order numbers
                "entities": [dict]       # Other structured data
            },
            "count": int,
            "message": str
        }
    """
    logger.info(f"[ATTACHMENT_ANALYZER] Called with {len(attachments or [])} attachment(s), focus: {focus}")
    
    # Critical fix: Handle None or empty attachments
    if not attachments:
        logger.warning("[ATTACHMENT_ANALYZER] No attachments provided")
        return {
            "success": False,
            "extracted_info": {
                "model_numbers": [],
                "part_numbers": [],
                "order_numbers": [],
                "entities": []
            },
            "count": 0,
            "message": "No attachments provided"
        }
    
    try:
        # Import here to avoid circular dependencies
        from app.tools.multimodal_document_analyzer import multimodal_document_analyzer_tool
        
        logger.info(f"[ATTACHMENT_ANALYZER] Processing {len(attachments)} attachment(s)")
        
        # Call the underlying document analyzer
        # CRITICAL FIX: Use .run() method with proper parameter wrapping
        try:
            result = multimodal_document_analyzer_tool.run(
                tool_input={
                    "attachments": attachments,
                    "focus": focus
                }
            )
        except AttributeError:
            # Fallback: Try direct invocation
            result = multimodal_document_analyzer_tool.invoke({
                "attachments": attachments,
                "focus": focus
            })
        
        # Validate result
        if not result or not isinstance(result, dict):
            logger.error(f"[ATTACHMENT_ANALYZER] Invalid result: {type(result)}")
            return {
                "success": False,
                "extracted_info": {
                    "model_numbers": [],
                    "part_numbers": [],
                    "order_numbers": [],
                    "entities": []
                },
                "count": 0,
                "message": "Document analyzer returned invalid response"
            }
        
        # Extract and aggregate data from all documents
        documents = result.get("documents", [])
        
        all_model_numbers = []
        all_part_numbers = []
        all_order_numbers = []
        all_entities = []
        
        for doc in documents:
            if not isinstance(doc, dict):
                continue
                
            extracted = doc.get("extracted_info", {})
            
            # Extract model numbers
            models = extracted.get("model_numbers", [])
            if isinstance(models, str):
                models = [models]
            if isinstance(models, list):
                all_model_numbers.extend([str(m).strip().upper() for m in models if m])
            
            # Extract part numbers
            parts = extracted.get("part_numbers", [])
            if isinstance(parts, str):
                parts = [parts]
            if isinstance(parts, list):
                all_part_numbers.extend([str(p).strip().upper() for p in parts if p])
            
            # Extract order numbers
            orders = extracted.get("order_numbers", [])
            if isinstance(orders, str):
                orders = [orders]
            if isinstance(orders, list):
                all_order_numbers.extend([str(o).strip() for o in orders if o])
            
            # Keep full extracted info for reference
            if extracted:
                all_entities.append({
                    "filename": doc.get("filename", "unknown"),
                    "data": extracted
                })
        
        # Deduplicate while preserving order
        all_model_numbers = list(dict.fromkeys(all_model_numbers))
        all_part_numbers = list(dict.fromkeys(all_part_numbers))
        all_order_numbers = list(dict.fromkeys(all_order_numbers))
        
        logger.info(f"[ATTACHMENT_ANALYZER] Extracted: {len(all_model_numbers)} model numbers, "
                   f"{len(all_part_numbers)} part numbers, {len(all_order_numbers)} order numbers")
        
        return {
            "success": True,
            "extracted_info": {
                "model_numbers": all_model_numbers,
                "part_numbers": all_part_numbers,
                "order_numbers": all_order_numbers,
                "entities": all_entities
            },
            "count": len(documents),
            "message": f"Successfully analyzed {len(documents)} attachment(s). "
                      f"Found {len(all_model_numbers)} model numbers."
        }
        
    except Exception as e:
        logger.error(f"[ATTACHMENT_ANALYZER] Failed: {e}", exc_info=True)
        return {
            "success": False,
            "extracted_info": {
                "model_numbers": [],
                "part_numbers": [],
                "order_numbers": [],
                "entities": []
            },
            "count": 0,
            "message": f"Attachment analysis failed: {str(e)}"
        }