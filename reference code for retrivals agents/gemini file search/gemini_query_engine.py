"""
Flusso RAG - Query Engine
Processes queries using Google Gemini File Search API
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from diskcache import Cache

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class QueryEngine:
    """RAG query engine using Gemini File Search"""
    
    def __init__(self):
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        # Create Gemini client
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'
        
        # Load store configuration
        data_dir = Path(__file__).parent.parent / 'data'
        stores_file = data_dir / 'vector_stores.json'
        
        with open(stores_file, 'r') as f:
            self.stores_config = json.load(f)
        
        # Get active store IDs (only stores with files)
        self.active_stores = []
        for store_name, store_info in self.stores_config.get('stores', {}).items():
            if store_info.get('imported_count', 0) > 0:
                store_id = store_info.get('store_id')
                if store_id:
                    self.active_stores.append(store_id)
                    print(f"✓ Loaded store: {store_name} ({store_info['imported_count']} files)")
        
        if not self.active_stores:
            raise ValueError("No active file search stores found")
        
        print(f"✓ Query engine ready with {len(self.active_stores)} store(s)")
        
        # Initialize cache
        cache_dir = data_dir / 'cache'
        cache_dir.mkdir(exist_ok=True)
        self.cache = Cache(str(cache_dir))
    
    def query(self, user_query: str, use_cache: bool = True) -> dict:
        """
        Process a user query and return results
        
        Args:
            user_query: The user's question
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with answer and sources
        """
        # Check cache
        cache_key = f"query:{user_query}"
        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            # Ensure backward compatibility
            if 'sources' not in cached:
                cached['sources'] = []
            return cached
        
        try:
            # Generate response using File Search
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_query,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=self.active_stores
                        )
                    )],
                    temperature=0.2,
                    top_p=0.8,
                )
            )
            
            # Extract answer
            answer = response.text
            
            # Extract sources from grounding metadata
            sources = []
            if response.candidates:
                grounding = response.candidates[0].grounding_metadata
                if grounding and grounding.grounding_chunks:
                    sources = [
                        c.retrieved_context.title 
                        for c in grounding.grounding_chunks 
                        if hasattr(c, 'retrieved_context')
                    ]
            
            # Prepare result
            result = {
                'query': user_query,
                'answer': answer,
                'sources': sources
            }
            
            # Cache result (1 hour)
            if use_cache:
                self.cache.set(cache_key, result, expire=3600)
            
            return result
            
        except Exception as e:
            return {
                'query': user_query,
                'answer': f"Error: {str(e)}",
                'sources': []
            }


def main():
    """Test the query engine"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python query_engine.py <query>")
        return
    
    query = " ".join(sys.argv[1:])
    engine = QueryEngine()
    result = engine.query(query)
    
    print(f"\nQuery: {result['query']}")
    print(f"\nAnswer:\n{result['answer']}")
    if result['sources']:
        print(f"\nSources: {', '.join(result['sources'])}")


if __name__ == "__main__":
    main()
