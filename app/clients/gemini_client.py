"""
Google Gemini File Search Client
Queries Gemini File Search API for document retrieval
CORRECTED VERSION - Fixed API usage and grounding metadata extraction
"""

import logging
from typing import List, Dict, Any
from google import genai
from google.genai import types

from app.config.settings import settings
from app.graph.state import RetrievalHit

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for Google Gemini File Search API.
    Queries pre-configured file search store for document retrieval.
    NO INGESTION - only querying existing store.
    """
    
    def __init__(self):
        """Initialize Gemini client"""
        api_key = settings.gemini_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = settings.llm_model
        self.store_id = settings.gemini_file_search_store_id
        
        if not self.store_id:
            raise ValueError("GEMINI_FILE_SEARCH_STORE_ID not configured")
        
        logger.info(f"Gemini client initialized with model: {self.model_name}")
        logger.info(f"File search store: {self.store_id}")
    
    def search_files(self, query: str, top_k: int = 10) -> List[RetrievalHit]:
        """
        Search the file store for relevant documents
        
        Args:
            query: Search query (user question or ticket text)
            top_k: Number of results to return
            
        Returns:
            List of RetrievalHit objects with content and metadata
        """
        logger.info(f"Searching file store for: {query[:100]}...")
        
        try:
            # CORRECTED: Use proper File Search tool configuration
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[self.store_id]
                            )
                        )
                    ],
                    temperature=0.1,  # Low temperature for factual retrieval
                )
            )
            
            # Extract answer text
            answer_text = response.text if hasattr(response, 'text') else ""
            logger.info(f"Generated answer: {answer_text[:100]}...")
            
            # CORRECTED: Extract grounding chunks properly
            hits: List[RetrievalHit] = []
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Access grounding_metadata correctly
                if hasattr(candidate, 'grounding_metadata'):
                    grounding = candidate.grounding_metadata
                    
                    # CORRECTED: Check for grounding_chunks attribute
                    if hasattr(grounding, 'grounding_chunks') and grounding.grounding_chunks:
                        for i, chunk in enumerate(grounding.grounding_chunks[:top_k]):
                            # CORRECTED: Access retrieved_context properly
                            if hasattr(chunk, 'retrieved_context'):
                                context = chunk.retrieved_context
                                
                                # Extract metadata
                                title = getattr(context, 'title', f'Document {i+1}')
                                uri = getattr(context, 'uri', '')
                                
                                # CORRECTED: Get text content from retrieved_context
                                content_text = ""
                                if hasattr(context, 'text'):
                                    content_text = context.text
                                elif hasattr(context, 'content'):
                                    content_text = context.content
                                
                                # Create retrieval hit
                                hit: RetrievalHit = {
                                    'id': f"gemini_{i}",
                                    'score': 0.95 - (i * 0.05),  # Approximate relevance scores
                                    'metadata': {
                                        'title': title,
                                        'uri': uri,
                                        'source': 'gemini_file_search',
                                        'chunk_index': i
                                    },
                                    'content': content_text or title
                                }
                                
                                hits.append(hit)
                                logger.debug(f"Retrieved chunk {i}: {title[:50]}...")
                    
                    # CORRECTED: Also check for grounding_supports (alternative structure)
                    elif hasattr(grounding, 'grounding_supports') and grounding.grounding_supports:
                        for i, support in enumerate(grounding.grounding_supports[:top_k]):
                            if hasattr(support, 'segment'):
                                segment = support.segment
                                content_text = getattr(segment, 'text', '')
                                
                                # Extract source info
                                source_info = {}
                                if hasattr(support, 'source'):
                                    source = support.source
                                    source_info['title'] = getattr(source, 'title', f'Document {i+1}')
                                    source_info['uri'] = getattr(source, 'uri', '')
                                
                                hit: RetrievalHit = {
                                    'id': f"gemini_{i}",
                                    'score': 0.95 - (i * 0.05),
                                    'metadata': {
                                        'title': source_info.get('title', f'Document {i+1}'),
                                        'uri': source_info.get('uri', ''),
                                        'source': 'gemini_file_search',
                                        'support_index': i
                                    },
                                    'content': content_text
                                }
                                
                                hits.append(hit)
            
            logger.info(f"Retrieved {len(hits)} result(s) from Gemini File Search")
            
            # If no grounding chunks but we have an answer, create a single hit with the answer
            if not hits and answer_text:
                logger.warning("No grounding chunks found, using generated answer as single hit")
                hits.append({
                    'id': 'gemini_0',
                    'score': 0.8,  # Lower score since not directly grounded
                    'metadata': {
                        'title': 'Generated Answer',
                        'source': 'gemini_file_search',
                        'grounding_status': 'no_chunks_found'
                    },
                    'content': answer_text
                })
            
            # CORRECTED: If no results at all, return empty list instead of error
            if not hits:
                logger.warning(f"No results found for query: {query[:100]}")
            
            return hits
            
        except Exception as e:
            logger.error(f"Error searching Gemini File Search: {e}", exc_info=True)
            return []


# Global client instance
_client: Dict[str, GeminiClient] = {}


def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client instance"""
    if 'instance' not in _client:
        _client['instance'] = GeminiClient()
    return _client['instance']