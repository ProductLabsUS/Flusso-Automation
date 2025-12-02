"""
Pinecone Indexer Module.
Handles vector database operations for image embeddings.
"""
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from pinecone import Pinecone, ServerlessSpec

from config.config import (
    PINECONE_API_KEY,
    PINECONE_ENVIRONMENT,
    INDEX_NAME,
    VECTOR_DIMENSION,
    METRIC,
    BATCH_SIZE,
    IMAGES_DIR,
)
from src.embedder import get_embedder
from src.utils import (
    setup_logger,
    load_metadata,
    extract_pinecone_metadata,
    get_image_path,
    create_vector_id,
    validate_image,
)


class ImageIndexer:
    """
    Manages indexing of product images into Pinecone vector database.
    """
    
    def __init__(self):
        """Initialize Pinecone client and index."""
        self.logger = setup_logger(__name__)
        self.embedder = get_embedder()
        self.pc = self._init_pinecone()
        self.index = None
        self._connect_to_index()
    
    def _init_pinecone(self) -> Pinecone:
        """
        Initialize Pinecone client.
        
        Returns:
            Pinecone client instance
        """
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not set. Check your .env file.")
        
        self.logger.info("Initializing Pinecone client...")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        self.logger.info("Pinecone client initialized successfully")
        return pc
    
    def create_index(self, delete_if_exists: bool = False):
        """
        Create a new Pinecone index for image embeddings.
        
        Args:
            delete_if_exists: If True, delete existing index before creating
        """
        self.logger.info(f"Creating index: {INDEX_NAME}")
        
        # Check if index exists
        existing_indexes = self.pc.list_indexes().names()
        
        if INDEX_NAME in existing_indexes:
            if delete_if_exists:
                self.logger.warning(f"Deleting existing index: {INDEX_NAME}")
                self.pc.delete_index(INDEX_NAME)
                # Wait for deletion
                time.sleep(5)
            else:
                self.logger.info(f"Index {INDEX_NAME} already exists")
                return
        
        # Create new index
        self.logger.info(f"Creating new index with dimension={VECTOR_DIMENSION}, metric={METRIC}")
        
        self.pc.create_index(
            name=INDEX_NAME,
            dimension=VECTOR_DIMENSION,
            metric=METRIC,
            spec=ServerlessSpec(
                cloud="aws",
                region=PINECONE_ENVIRONMENT
            )
        )
        
        self.logger.info(f"Index {INDEX_NAME} created successfully")
        
        # Wait for index to be ready
        self.logger.info("Waiting for index to be ready...")
        time.sleep(10)
    
    def _connect_to_index(self):
        """Connect to existing Pinecone index."""
        try:
            self.index = self.pc.Index(INDEX_NAME)
            stats = self.index.describe_index_stats()
            self.logger.info(f"Connected to index: {INDEX_NAME}")
            self.logger.info(f"Index stats: {stats.total_vector_count} vectors")
        except Exception as e:
            self.logger.warning(f"Could not connect to index {INDEX_NAME}: {e}")
            self.logger.info("You may need to create the index first using scripts/create_index.py")
    
    def index_single_product(self, product: Dict[str, Any]) -> bool:
        """
        Index a single product image.
        
        Args:
            product: Product metadata dictionary
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get image path
            image_path = get_image_path(product, IMAGES_DIR)
            
            # Validate image
            if not validate_image(image_path):
                self.logger.warning(f"Invalid image: {image_path}")
                return False
            
            # Generate embedding
            embedding = self.embedder.embed_image(image_path)
            
            # Extract metadata
            metadata = extract_pinecone_metadata(product)
            
            # Create vector ID
            vector_id = create_vector_id(product)
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[(vector_id, embedding.tolist(), metadata)]
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to index product: {e}")
            return False
    
    def index_all_images(self, skip_existing: bool = True):
        """
        Index all product images from metadata.
        
        Args:
            skip_existing: If True, skip images already in the index
        """
        self.logger.info("Starting batch indexing of all images...")
        
        # Load metadata
        products = load_metadata()
        total_products = len(products)
        
        self.logger.info(f"Found {total_products} products to index")
        
        # Get existing IDs if skipping
        existing_ids = set()
        if skip_existing and self.index:
            try:
                stats = self.index.describe_index_stats()
                existing_count = stats.total_vector_count
                self.logger.info(f"Index contains {existing_count} existing vectors")
            except Exception as e:
                self.logger.warning(f"Could not get existing vectors: {e}")
        
        # Process in batches
        successful = 0
        failed = 0
        skipped = 0
        
        batch_vectors = []
        batch_size = BATCH_SIZE
        
        with tqdm(total=total_products, desc="Indexing images") as pbar:
            for product in products:
                try:
                    # Create vector ID
                    vector_id = create_vector_id(product)
                    
                    # Skip if exists
                    if skip_existing and vector_id in existing_ids:
                        skipped += 1
                        pbar.update(1)
                        continue
                    
                    # Get image path
                    image_path = get_image_path(product, IMAGES_DIR)
                    
                    # Validate image
                    if not validate_image(image_path):
                        self.logger.warning(f"Invalid image: {image_path}")
                        failed += 1
                        pbar.update(1)
                        continue
                    
                    # Generate embedding
                    embedding = self.embedder.embed_image(image_path)
                    
                    # Extract metadata
                    metadata = extract_pinecone_metadata(product)
                    
                    # Add to batch
                    batch_vectors.append((vector_id, embedding.tolist(), metadata))
                    
                    # Upsert batch when full
                    if len(batch_vectors) >= batch_size:
                        self.index.upsert(vectors=batch_vectors)
                        successful += len(batch_vectors)
                        batch_vectors = []
                    
                    pbar.update(1)
                    
                except Exception as e:
                    self.logger.error(f"Failed to process product: {e}")
                    failed += 1
                    pbar.update(1)
        
        # Upsert remaining vectors
        if batch_vectors:
            self.index.upsert(vectors=batch_vectors)
            successful += len(batch_vectors)
        
        # Summary
        self.logger.info("="*80)
        self.logger.info("Indexing complete!")
        self.logger.info(f"Total products: {total_products}")
        self.logger.info(f"Successfully indexed: {successful}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Skipped (existing): {skipped}")
        self.logger.info("="*80)
    
    def search_by_image(
        self,
        image_path: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar images using an image query.
        
        Args:
            image_path: Path to query image
            top_k: Number of results to return
            filter_dict: Optional metadata filters
        
        Returns:
            List of search results with metadata and scores
        """
        try:
            # Generate embedding for query image
            self.logger.info(f"Searching for similar images to: {image_path}")
            embedding = self.embedder.embed_image(image_path)
            
            # Query Pinecone
            results = self.index.query(
                vector=embedding.tolist(),
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata
                })
            
            self.logger.info(f"Found {len(formatted_results)} similar images")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def search_by_metadata(
        self,
        filter_dict: Dict[str, Any],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search using metadata filters only.
        
        Args:
            filter_dict: Metadata filters
            top_k: Number of results to return
        
        Returns:
            List of matching products
        """
        try:
            # Use a dummy vector for metadata-only search
            dummy_vector = [0.0] * VECTOR_DIMENSION
            
            results = self.index.query(
                vector=dummy_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    'id': match.id,
                    'metadata': match.metadata
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Metadata search failed: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'dimension': VECTOR_DIMENSION,
                'metric': METRIC,
                'index_name': INDEX_NAME,
            }
        except Exception as e:
            self.logger.error(f"Failed to get index stats: {e}")
            return {}
    
    def delete_vectors(self, vector_ids: List[str]):
        """
        Delete vectors from the index.
        
        Args:
            vector_ids: List of vector IDs to delete
        """
        try:
            self.index.delete(ids=vector_ids)
            self.logger.info(f"Deleted {len(vector_ids)} vectors")
        except Exception as e:
            self.logger.error(f"Failed to delete vectors: {e}")
    
    def clear_index(self):
        """Delete all vectors from the index."""
        try:
            self.index.delete(delete_all=True)
            self.logger.info("Index cleared successfully")
        except Exception as e:
            self.logger.error(f"Failed to clear index: {e}")
