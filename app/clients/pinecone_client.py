"""
Pinecone Client - Clean Production Version
Compatible with CLIP (now) and Gemini Multimodal (future)
"""

import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone

from app.config.settings import settings
from app.graph.state import RetrievalHit

logger = logging.getLogger(__name__)


class PineconeClient:

    def __init__(self):
        api_key = settings.pinecone_api_key
        if not api_key:
            raise ValueError("PINECONE_API_KEY missing")

        self.pc = Pinecone(api_key=api_key)

        # Index names
        self.image_index_name = settings.pinecone_image_index
        self.tickets_index_name = settings.pinecone_tickets_index

        # Connect + handle errors gracefully
        try:
            self.image_index = self.pc.Index(self.image_index_name)
            logger.info(f"[Pinecone] Connected image index: {self.image_index_name}")
        except Exception as e:
            logger.error(f"[Pinecone] Image index unavailable: {e}")
            self.image_index = None

        try:
            self.tickets_index = self.pc.Index(self.tickets_index_name)
            logger.info(f"[Pinecone] Connected tickets index: {self.tickets_index_name}")
        except Exception as e:
            logger.error(f"[Pinecone] Tickets index unavailable: {e}")
            self.tickets_index = None

    # ---------------------------------------------------------
    # Image Search
    # ---------------------------------------------------------
    def query_images(
        self,
        vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalHit]:

        if not self.image_index:
            logger.warning("[Pinecone] Image index not available")
            return []

        try:
            # Ensure vector is a list (not numpy array) for Pinecone serialization
            if hasattr(vector, 'tolist'):
                vector = vector.tolist()
            elif not isinstance(vector, list):
                vector = list(vector)
            
            results = self.image_index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )

            hits: List[RetrievalHit] = []

            for match in results.matches:
                metadata = match.metadata or {}

                # readable content summary
                parts = []
                for key in ["product_title", "model_no", "finish", "product_category"]:
                    if key in metadata:
                        parts.append(f"{key.capitalize()}: {metadata[key]}")

                content = " | ".join(parts) if parts else "Product Match"

                hits.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": metadata,
                    "content": content,
                })

            return hits

        except Exception as e:
            logger.error(f"[Pinecone] Error querying images: {e}", exc_info=True)
            return []

    # ---------------------------------------------------------
    # Past Tickets Search
    # ---------------------------------------------------------
    def query_past_tickets(
        self,
        vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalHit]:

        if not self.tickets_index:
            logger.warning("[Pinecone] Tickets index not available")
            return []

        try:
            # Ensure vector is a list (not numpy array) for Pinecone serialization
            if hasattr(vector, 'tolist'):
                vector = vector.tolist()
            elif not isinstance(vector, list):
                vector = list(vector)
            
            results = self.tickets_index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )

            hits: List[RetrievalHit] = []

            for match in results.matches:
                metadata = match.metadata or {}

                content = metadata.get("text") or metadata.get("summary") or "Past Ticket"

                hits.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": metadata,
                    "content": content,
                })

            return hits

        except Exception as e:
            logger.error(f"[Pinecone] Error querying tickets: {e}", exc_info=True)
            return []


# Singleton
_client = None

def get_pinecone_client() -> PineconeClient:
    global _client
    if _client is None:
        _client = PineconeClient()
    return _client
