"""
Attachment Analyzer Tool - FIXED
Wrapper around multimodal_document_analyzer to extract model numbers and entities.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain.tools import tool

from app.tools.multimodal_document_analyzer import multimodal_document_analyzer_tool

logger = logging.getLogger(__name__)


@tool
def attachment_analyzer_tool(
    attachments: Optional[List[Dict[str, Any]]] = None,
    focus: str = "general",
) -> Dict[str, Any]:
    """
    Analyze ticket attachments to extract model numbers, entities, and text.

    Args:
        attachments: List of attachment dicts with at least 'attachment_url' and 'name'.
        focus: Optional focus area for extraction (default: general)

    Returns:
        {
            "success": bool,
            "extracted_info": {
                "model_numbers": [...],
                "entities": [...],
            },
            "count": int,
            "message": str
        }
    """
    attachments = attachments or []
    if not attachments:
        return {
            "success": False,
            "extracted_info": {},
            "count": 0,
            "message": "No attachments provided"
        }

    try:
        # FIXED: Use .invoke() instead of .run()
        result = multimodal_document_analyzer_tool.invoke({
            "attachments": attachments,
            "focus": focus,
        })

        # Handle case where invoke returns None or error
        if not result or not isinstance(result, dict):
            logger.error(f"[ATTACHMENT_ANALYZER] Invalid result from multimodal analyzer: {result}")
            return {
                "success": False,
                "extracted_info": {},
                "count": 0,
                "message": "Failed to analyze attachments - invalid response"
            }

        documents = result.get("documents", [])
        entities_list: List[Dict[str, Any]] = []
        model_numbers: List[str] = []

        for doc in documents:
            extracted = doc.get("extracted_info", {}) if isinstance(doc, dict) else {}
            entities_list.append(extracted)
            
            # Extract model numbers from various possible fields
            mn = extracted.get("model_numbers") or extracted.get("models") or []
            if isinstance(mn, list):
                model_numbers.extend([str(m).strip() for m in mn if str(m).strip()])
            elif isinstance(mn, str) and mn.strip():
                model_numbers.append(mn.strip())

        # Deduplicate while preserving order
        model_numbers = list(dict.fromkeys(model_numbers))

        return {
            "success": True,
            "extracted_info": {
                "model_numbers": model_numbers,
                "entities": entities_list,
            },
            "count": len(documents),
            "message": f"Processed {len(documents)} attachment(s)"
        }
    except Exception as e:
        logger.error(f"[ATTACHMENT_ANALYZER] Failed: {e}", exc_info=True)
        return {
            "success": False,
            "extracted_info": {},
            "count": 0,
            "message": f"Attachment analysis failed: {str(e)}"
        }   