"""
Flusso Vision Agent - Main Interface
Simple API for querying the image RAG system
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.indexer import ImageIndexer
from src.utils import setup_logger
from config.config import validate_config


class VisionAgent:
    """
    Main interface for the Flusso Vision Agent.
    Provides simple methods for image-based product search.
    """
    
    def __init__(self):
        """Initialize the vision agent."""
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing Flusso Vision Agent...")
        
        # Validate configuration
        try:
            validate_config()
        except ValueError as e:
            self.logger.error(f"Configuration error: {e}")
            raise
        
        # Initialize indexer (loads CLIP model + connects to Pinecone)
        self.indexer = ImageIndexer()
        self.logger.info("Vision Agent ready!")
    
    def search(
        self,
        image_path: str,
        top_k: int = 5,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar products using an image.
        
        Args:
            image_path: Path to the query image
            top_k: Number of results to return (default: 5)
            min_score: Minimum similarity score threshold (0.0-1.0)
            filters: Optional metadata filters, e.g. {"finish": "Chrome"}
        
        Returns:
            List of matching products with metadata and scores
            
        Example:
            >>> agent = VisionAgent()
            >>> results = agent.search("unknown-faucet.jpg", top_k=3)
            >>> for result in results:
            ...     print(f"{result['metadata']['product_title']}: {result['score']:.2f}")
        """
        self.logger.info(f"Searching for: {image_path}")
        
        # Query Pinecone
        results = self.indexer.search_by_image(
            image_path=image_path,
            top_k=top_k,
            filter_dict=filters
        )
        
        # Filter by minimum score
        if min_score > 0.0:
            results = [r for r in results if r['score'] >= min_score]
        
        self.logger.info(f"Found {len(results)} results")
        return results
    
    def get_product_by_model(self, model_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific product by model number.
        
        Args:
            model_number: Product model number
        
        Returns:
            Product metadata if found, None otherwise
        """
        # Search with model number filter
        results = self.indexer.search_by_metadata(
            filter_dict={"model_no": model_number},
            top_k=1
        )
        
        return results[0] if results else None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary with index statistics
        """
        return self.indexer.get_index_stats()
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format a single result for display.
        
        Args:
            result: Search result dictionary
        
        Returns:
            Formatted string
        """
        metadata = result.get('metadata', {})
        score = result.get('score', 0.0)
        
        return f"""
Product: {metadata.get('product_title', 'Unknown')}
Model: {metadata.get('model_no', 'N/A')}
Finish: {metadata.get('finish', 'N/A')}
Category: {metadata.get('product_category', 'N/A')}
Price: ${metadata.get('list_price', 'N/A')}
Similarity: {score:.2%}
Image URL: {metadata.get('image_url', 'N/A')}
        """.strip()


if __name__ == "__main__":
    """
    Example usage of the Vision Agent
    """
    # Initialize agent
    agent = VisionAgent()
    
    # Get database stats
    stats = agent.get_stats()
    print(f"\nDatabase contains {stats.get('total_vectors', 0)} products")
    
    # Example search (replace with actual image path)
    import os
    if os.path.exists("test_image.jpg"):
        print("\nSearching for similar products...")
        results = agent.search("test_image.jpg", top_k=3, min_score=0.8)
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(agent.format_result(result))
    else:
        print("\nTo test, add a 'test_image.jpg' file and run this script again.")
