"""
CLIP Image Embedder + Gemini Text Embedder
- CLIP: Generates embeddings for images (512 dimensions with ViT-B-32)
- Gemini: Generates embeddings for text (768 dimensions)
"""

import logging
import torch
import open_clip
from PIL import Image
from pathlib import Path
from typing import Dict, List, Union, Optional
import numpy as np
from io import BytesIO
import requests
from google import genai

from app.config.settings import settings

logger = logging.getLogger(__name__)


class CLIPEmbedder:
    """
    CLIP-based image embedder with optional GPU support.
    Generates normalized embeddings for product images.
    """
    
    def __init__(self):
        """Initialize CLIP model"""
        self.device = self._setup_device()
        self.model, self.preprocess = self._load_model()
        logger.info(f"CLIP Embedder initialized on device: {self.device}")
    
    def _setup_device(self) -> torch.device:
        """Configure device (GPU/CPU) for inference"""
        if settings.gpu_enabled and torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            if settings.gpu_enabled:
                logger.warning("GPU requested but not available. Using CPU.")
            else:
                logger.info("Using CPU for embeddings")
        
        return device
    
    def _load_model(self):
        """Load CLIP model and preprocessing"""
        logger.info(f"Loading CLIP model: {settings.clip_model}")
        
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(
                settings.clip_model,
                pretrained=settings.clip_pretrained,
                device=self.device
            )
            
            model.eval()
            
            # Test embedding dimension
            with torch.no_grad():
                dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
                embedding_dim = model.encode_image(dummy_input).shape[-1]
            
            logger.info(f"CLIP model loaded. Embedding dimension: {embedding_dim}")
            
            return model, preprocess
            
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def embed_image_from_path(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Generate embedding for image from local path
        
        Args:
            image_path: Path to image file
            
        Returns:
            Normalized embedding vector (numpy array)
        """
        try:
            image = Image.open(image_path).convert("RGB")
            return self._embed_pil_image(image)
            
        except Exception as e:
            logger.error(f"Failed to embed image from path {image_path}: {e}")
            raise
    
    def embed_image_from_url(self, image_url: str) -> np.ndarray:
        """
        Generate embedding for image from URL
        
        Args:
            image_url: HTTP(S) URL to image
            
        Returns:
            Normalized embedding vector (numpy array)
        """
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Load image from bytes
            image = Image.open(BytesIO(response.content)).convert("RGB")
            return self._embed_pil_image(image)
            
        except Exception as e:
            logger.error(f"Failed to embed image from URL {image_url}: {e}")
            raise
    
    def _embed_pil_image(self, image: Image.Image) -> np.ndarray:
        """
        Generate embedding for PIL Image
        
        Args:
            image: PIL Image object
            
        Returns:
            Normalized embedding vector
        """
        try:
            # Preprocess and convert to tensor
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Generate embedding
            with torch.no_grad():
                embedding = self.model.encode_image(image_tensor)
                # Normalize
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embedding_np = embedding.cpu().numpy().flatten()
            
            return embedding_np
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def get_embedding_dim(self) -> int:
        """Get the dimension of embedding vectors"""
        with torch.no_grad():
            dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
            embedding = self.model.encode_image(dummy_input)
            return embedding.shape[-1]


# Global embedder instance
_embedder: Dict[str, CLIPEmbedder] = {}


def get_clip_embedder() -> CLIPEmbedder:
    """Get or create global CLIP embedder instance"""
    if 'instance' not in _embedder:
        _embedder['instance'] = CLIPEmbedder()
    return _embedder['instance']


# =====================================================
# GEMINI TEXT EMBEDDINGS (768 dimensions)
# For text/tickets index
# =====================================================

_gemini_client: Dict[str, genai.Client] = {}


def get_gemini_embed_client() -> genai.Client:
    """Get or create Gemini client for embeddings"""
    if 'instance' not in _gemini_client:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured for embeddings")
        _gemini_client['instance'] = genai.Client(api_key=settings.gemini_api_key)
        logger.info("Gemini embedding client initialized")
    return _gemini_client['instance']


def embed_text_gemini(text: str) -> List[float]:
    """
    Generate text embeddings using Gemini's text-embedding model.
    Produces 768-dimensional vectors for the tickets index.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector as list (768 dimensions)
    """
    try:
        client = get_gemini_embed_client()
        
        # Use Gemini's embedding model
        # text-embedding-004 produces 768-dim vectors by default
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        
        # Extract embedding vector
        if hasattr(result, 'embeddings') and result.embeddings:
            embedding = result.embeddings[0].values
            logger.debug(f"Generated Gemini embedding with {len(embedding)} dimensions")
            return list(embedding)
        else:
            logger.error("No embeddings returned from Gemini")
            return [0.0] * 768
            
    except Exception as e:
        logger.error(f"Failed to generate Gemini embedding: {e}", exc_info=True)
        return [0.0] * 768


def embed_text(text: str) -> List[float]:
    """
    Generate text embeddings using Gemini (768 dimensions).
    This is the main function used for text/ticket queries.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector as list (768 dimensions)
    """
    return embed_text_gemini(text)


# =====================================================
# CLIP TEXT EMBEDDINGS (512 dimensions)
# For image similarity with text queries
# =====================================================

def embed_text_clip(text: str) -> List[float]:
    """
    Generate text embeddings using CLIP (512 dimensions).
    Use this for text-to-image similarity searches.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector as list (512 dimensions)
    """
    embedder = get_clip_embedder()
    
    tokenizer = open_clip.get_tokenizer(settings.clip_model)
    
    try:
        with torch.no_grad():
            text_tokens = tokenizer([text]).to(embedder.device)
            text_embedding = embedder.model.encode_text(text_tokens)
            text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
            return text_embedding.cpu().numpy().flatten().tolist()
    except Exception as e:
        logger.error(f"Failed to embed text with CLIP: {e}")
        return [0.0] * 512


def embed_image(image_source: Union[str, Path]) -> List[float]:
    """
    Embed an image from path or URL
    
    Args:
        image_source: File path or HTTP URL
        
    Returns:
        Embedding vector as list
    """
    embedder = get_clip_embedder()
    
    # Determine if URL or path
    image_str = str(image_source)
    
    if image_str.startswith('http://') or image_str.startswith('https://'):
        embedding = embedder.embed_image_from_url(image_str)
    else:
        embedding = embedder.embed_image_from_path(image_source)
    
    return embedding.tolist()
