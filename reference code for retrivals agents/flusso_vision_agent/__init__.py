"""
Flusso Vision Agent - AI-Powered Product Image Search

A production-ready vision-based RAG (Retrieval-Augmented Generation) agent
for searching and matching product images using CLIP embeddings and Pinecone vector database.
"""

from src.indexer import ImageIndexer
from src.embedder import get_embedder
from src.utils import setup_logger
from config.config import validate_config

__version__ = "1.0.0"
__all__ = ["ImageIndexer", "get_embedder", "setup_logger", "validate_config"]
