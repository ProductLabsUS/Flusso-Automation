"""
Product Search Tool - FIXED VERSION
Metadata-first strategy for exact model number lookups
"""

import logging
from typing import Dict, Any, Optional, List
from langchain.tools import tool

from app.clients.pinecone_client import get_pinecone_client
from app.clients.embeddings import embed_text_clip

logger = logging.getLogger(__name__)


@tool
def product_search_tool(
    query: Optional[str] = None,
    model_number: Optional[str] = None,
    category: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Search product catalog by model number or description using Pinecone.
    
    Use this tool when:
    - Customer mentions a specific model number (e.g., "HS6270MB", "F2580CP")
    - You need to verify a product exists in the catalog
    - You need product details (category, name, images)
    
    Args:
        query: Natural language description of the product (optional if model_number provided)
        model_number: Exact model number if mentioned in ticket (e.g., "HS6270MB")
        category: Product category filter if known (e.g., "Shower Heads", "Kitchen Faucets")
        top_k: Number of results to return (default: 5)
    
    Returns:
        {
            "success": bool,
            "products": [...],
            "count": int,
            "search_method": "model_number" | "semantic" | "metadata",
            "message": str
        }
    """
    if not query and not model_number:
        return {
            "success": False,
            "products": [],
            "count": 0,
            "search_method": "none",
            "message": "Either query or model_number must be provided"
        }
    
    if not query and model_number:
        query = model_number
    
    logger.info(f"[PRODUCT_SEARCH] Query: '{query}', Model: {model_number}, Category: {category}")
    
    try:
        client = get_pinecone_client()
        normalized_model = model_number.strip().upper() if model_number else None

        # ============================================================
        # STRATEGY 1: PURE METADATA LOOKUP (for exact model numbers)
        # Use dummy vector to avoid semantic interference
        # ============================================================
        if normalized_model:
            logger.info(f"[PRODUCT_SEARCH] Strategy: Pure metadata lookup for model '{normalized_model}'")
            
            # Create dummy/zero vector (512 dimensions for CLIP)
            # This prevents semantic similarity from interfering with metadata filter
            dummy_vector = [0.0] * 512
            
            filter_dict = {"model_no": {"$eq": normalized_model}}
            if category:
                filter_dict["product_category"] = {"$eq": category}
            
            results = client.query_images(vector=dummy_vector, top_k=top_k, filter_dict=filter_dict)
            
            if results:
                products = _format_product_results(results)
                logger.info(f"[PRODUCT_SEARCH] ✅ Found {len(products)} exact match(es) for model {normalized_model}")
                return {
                    "success": True,
                    "products": products,
                    "count": len(products),
                    "search_method": "metadata_exact",
                    "message": f"Found {len(products)} exact match(es) for model {normalized_model}"
                }
            else:
                logger.warning(f"[PRODUCT_SEARCH] No exact match for model '{normalized_model}', falling back to semantic search")
        
        # ============================================================
        # STRATEGY 2: SEMANTIC SEARCH (fallback or when no model number)
        # ============================================================
        logger.info(f"[PRODUCT_SEARCH] Strategy: Semantic search")
        vector = embed_text_clip(query)
        
        filter_dict = {}
        if category:
            filter_dict["product_category"] = {"$eq": category}
        
        results = client.query_images(vector=vector, top_k=top_k, filter_dict=filter_dict)
        
        if results:
            products = _format_product_results(results)
            logger.info(f"[PRODUCT_SEARCH] ✅ Found {len(products)} semantic match(es)")
            return {
                "success": True,
                "products": products,
                "count": len(products),
                "search_method": "semantic",
                "message": f"Found {len(products)} semantically similar product(s)"
            }
        
        # No results
        logger.warning(f"[PRODUCT_SEARCH] ❌ No products found for query: '{query}'")
        return {
            "success": False,
            "products": [],
            "count": 0,
            "search_method": "none",
            "message": "No products found matching the criteria"
        }
        
    except Exception as e:
        logger.error(f"[PRODUCT_SEARCH] Error: {e}", exc_info=True)
        return {
            "success": False,
            "products": [],
            "count": 0,
            "search_method": "error",
            "message": f"Search failed: {str(e)}"
        }


def _format_product_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format Pinecone results into clean product records"""
    products = []
    
    for hit in results:
        metadata = hit.get("metadata", {})
        
        # Extract image URLs
        image_urls = []
        if "image_url" in metadata:
            image_urls.append(metadata["image_url"])
        if "additional_images" in metadata and isinstance(metadata["additional_images"], list):
            image_urls.extend(metadata["additional_images"])
        
        product = {
            "model_no": metadata.get("model_no", metadata.get("product_id", "N/A")),
            "product_title": metadata.get("product_title", metadata.get("product_name", "Unknown")),
            "category": metadata.get("product_category", metadata.get("category", "Unknown")),
            "sub_category": metadata.get("sub_category", ""),
            "finish": metadata.get("finish", "N/A"),
            "collection": metadata.get("collection", ""),
            "image_urls": image_urls,
            "similarity_score": round(hit.get("score", 0) * 100),
            "raw_score": hit.get("score", 0)
        }
        
        products.append(product)
    
    return products