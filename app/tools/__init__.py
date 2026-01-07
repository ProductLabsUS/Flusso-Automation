"""
Tools Package for ReACT Agent
"""

# PRIMARY PRODUCT SEARCH - JSON-based comprehensive catalog
from app.tools.product_catalog_tool import product_catalog_tool

# Legacy product search (CSV-based) - kept for backwards compatibility
from app.tools.product_search_from_csv import product_search_tool as product_search_tool_legacy

# Import other tools
from app.tools.document_search import document_search_tool
from app.tools.vision_search import vision_search_tool
from app.tools.past_tickets import past_tickets_search_tool
from app.tools.attachment_analyzer import attachment_analyzer_tool
from app.tools.finish import finish_tool
from app.tools.multimodal_document_analyzer import multimodal_document_analyzer_tool
from app.tools.ocr_image_analyzer import ocr_image_analyzer_tool
from app.tools.attachment_classifier_tool import attachment_type_classifier_tool

__all__ = [
    "product_catalog_tool",
    "product_search_tool_legacy",
    "document_search_tool",
    "vision_search_tool",
    "past_tickets_search_tool",
    "attachment_analyzer_tool",
    "finish_tool",
    "multimodal_document_analyzer_tool",
    "ocr_image_analyzer_tool",
    "attachment_type_classifier_tool"
]

# AVAILABLE_TOOLS: Maps tool names to actual tool objects
# NOTE: Both "product_catalog_tool" and "product_search_tool" map to the same NEW tool
AVAILABLE_TOOLS = {
    "product_catalog_tool": product_catalog_tool,
    "product_search_tool": product_catalog_tool,  # Alias for backwards compatibility
    "document_search_tool": document_search_tool,
    "vision_search_tool": vision_search_tool,
    "past_tickets_search_tool": past_tickets_search_tool,
    "attachment_analyzer_tool": attachment_analyzer_tool,
    "finish_tool": finish_tool,
    "multimodal_document_analyzer_tool": multimodal_document_analyzer_tool,
    "ocr_image_analyzer_tool": ocr_image_analyzer_tool,
    "attachment_type_classifier_tool": attachment_type_classifier_tool
}