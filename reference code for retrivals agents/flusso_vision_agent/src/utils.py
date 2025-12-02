"""
Utility functions for the Flusso Image RAG system.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import colorlog

from config.config import METADATA_FILE, FIELD_MAPPINGS, METADATA_FIELDS


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Create a configured logger with color support.
    
    Args:
        name: Logger name
        log_file: Optional file path for logging
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def load_metadata() -> List[Dict[str, Any]]:
    """
    Load and parse the metadata manifest file.
    
    Returns:
        List of product metadata dictionaries
    """
    logger = setup_logger(__name__)
    
    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"Metadata file not found: {METADATA_FILE}")
    
    logger.info(f"Loading metadata from: {METADATA_FILE}")
    
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} product records")
    return data


def extract_pinecone_metadata(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and transform metadata for Pinecone storage.
    
    Args:
        product: Full product metadata dictionary
    
    Returns:
        Filtered and transformed metadata for Pinecone
    """
    metadata = product.get("metadata", {})
    
    # Extract and rename fields
    pinecone_metadata = {}
    
    for source_field, target_field in FIELD_MAPPINGS.items():
        if source_field in metadata:
            value = metadata[source_field]
            # Convert to string and clean
            if value is not None and value != "":
                # Handle numeric fields
                if source_field in ["List_Price", "MAP_Price"]:
                    try:
                        pinecone_metadata[target_field] = float(value)
                    except (ValueError, TypeError):
                        pinecone_metadata[target_field] = 0.0
                else:
                    pinecone_metadata[target_field] = str(value)
    
    # Add the saved filename
    if "savedAs" in product:
        pinecone_metadata["saved_filename"] = product["savedAs"]
    
    return pinecone_metadata


def get_image_path(product: Dict[str, Any], images_dir: Path) -> Path:
    """
    Get the full path to a product image.
    
    Args:
        product: Product metadata dictionary
        images_dir: Base images directory
    
    Returns:
        Full path to the image file
    """
    saved_filename = product.get("savedAs", "")
    if not saved_filename:
        raise ValueError("Product missing 'savedAs' field")
    
    image_path = images_dir / saved_filename
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    return image_path


def create_vector_id(product: Dict[str, Any]) -> str:
    """
    Create a unique ID for the vector based on product metadata.
    
    Args:
        product: Product metadata dictionary
    
    Returns:
        Unique vector ID
    """
    metadata = product.get("metadata", {})
    model_no = metadata.get("Model_NO", "")
    
    if not model_no:
        # Fallback to filename without extension
        saved_as = product.get("savedAs", "")
        model_no = Path(saved_as).stem
    
    # Clean the model number for use as an ID
    vector_id = model_no.replace(".", "_").replace("/", "_").replace(" ", "_")
    return vector_id


def validate_image(image_path: Path) -> bool:
    """
    Validate that an image file exists and is readable.
    
    Args:
        image_path: Path to image file
    
    Returns:
        True if valid, False otherwise
    """
    if not image_path.exists():
        return False
    
    # Check file size (basic validation)
    if image_path.stat().st_size == 0:
        return False
    
    # Check extension
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    if image_path.suffix.lower() not in valid_extensions:
        return False
    
    return True


def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    Format search results for display.
    
    Args:
        results: List of search result dictionaries
    
    Returns:
        Formatted string representation
    """
    if not results:
        return "No results found."
    
    output = []
    output.append("\n" + "="*80)
    output.append(f"Found {len(results)} similar products:")
    output.append("="*80)
    
    for i, result in enumerate(results, 1):
        metadata = result.get('metadata', {})
        score = result.get('score', 0.0)
        
        output.append(f"\n{i}. {metadata.get('product_title', 'Unknown Product')}")
        output.append(f"   Model: {metadata.get('model_no', 'N/A')}")
        output.append(f"   Finish: {metadata.get('finish', 'N/A')}")
        output.append(f"   Category: {metadata.get('product_category', 'N/A')} > {metadata.get('sub_category', 'N/A')}")
        output.append(f"   Similarity Score: {score:.4f}")
        output.append(f"   Image: {metadata.get('saved_filename', 'N/A')}")
        output.append(f"   URL: {metadata.get('image_url', 'N/A')}")
    
    output.append("\n" + "="*80)
    return "\n".join(output)
