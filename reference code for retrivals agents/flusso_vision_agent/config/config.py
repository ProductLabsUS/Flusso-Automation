"""
Configuration management for Flusso Vision Agent.
Handles environment variables and system settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "your_pinecone_api_key_here")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
INDEX_NAME = os.getenv("INDEX_NAME", "flusso-vision-index")
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "512"))
METRIC = os.getenv("METRIC", "cosine")

# CLIP Model Configuration
CLIP_MODEL = os.getenv("CLIP_MODEL", "ViT-B-32")
CLIP_PRETRAINED = os.getenv("CLIP_PRETRAINED", "openai")

# Processing Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))
GPU_ENABLED = os.getenv("GPU_ENABLED", "true").lower() == "true"
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "4"))

# Metadata field mappings (JSON -> Pinecone)
FIELD_MAPPINGS = {
    "Model_NO": "model_no",
    "Product_Title": "product_title",
    "Finish": "finish",
    "Common_Group_Number": "common_group_number",
    "Product_Category": "product_category",
    "Sub_Product_Category": "sub_category",
    "Sub_Sub_Product_Category": "sub_sub_category",
    "Collection": "collection",
    "Keywords": "keywords",
    "Image_URL": "image_url",
    "List_Price": "list_price",
    "MAP_Price": "map_price",
}

def validate_config():
    """Validate that all required configuration is present."""
    errors = []
    
    if not PINECONE_API_KEY or PINECONE_API_KEY == "your_pinecone_api_key_here":
        errors.append("PINECONE_API_KEY not set in .env file")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True
