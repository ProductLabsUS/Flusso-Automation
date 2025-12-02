"""
CLIP Embedding Module with GPU Support.
Handles image encoding using OpenCLIP with GPU acceleration.
"""
import torch
import open_clip
from PIL import Image
from pathlib import Path
from typing import List, Union
import numpy as np

from config.config import CLIP_MODEL, CLIP_PRETRAINED, GPU_ENABLED
from src.utils import setup_logger


class CLIPEmbedder:
    """
    CLIP-based image embedder with GPU support.
    Optimized for batch processing and production use.
    """
    
    def __init__(self):
        """Initialize CLIP model and preprocessing."""
        self.logger = setup_logger(__name__)
        self.device = self._setup_device()
        self.model, self.preprocess = self._load_model()
        self.logger.info(f"CLIPEmbedder initialized on device: {self.device}")
    
    def _setup_device(self) -> torch.device:
        """
        Configure device (GPU/CPU) for inference.
        
        Returns:
            torch.device object
        """
        if GPU_ENABLED and torch.cuda.is_available():
            device = torch.device("cuda")
            self.logger.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
            self.logger.info(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            device = torch.device("cpu")
            if GPU_ENABLED:
                self.logger.warning("GPU requested but not available. Using CPU.")
            else:
                self.logger.info("Using CPU as configured.")
        
        return device
    
    def _load_model(self):
        """
        Load CLIP model and preprocessing function.
        
        Returns:
            Tuple of (model, preprocess_function)
        """
        self.logger.info(f"Loading CLIP model: {CLIP_MODEL} ({CLIP_PRETRAINED})")
        
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(
                CLIP_MODEL,
                pretrained=CLIP_PRETRAINED,
                device=self.device
            )
            
            # Set to evaluation mode
            model.eval()
            
            # Get embedding dimension
            with torch.no_grad():
                dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
                embedding_dim = model.encode_image(dummy_input).shape[-1]
            
            self.logger.info(f"Model loaded successfully. Embedding dimension: {embedding_dim}")
            
            return model, preprocess
            
        except Exception as e:
            self.logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def embed_image(self, image_path: Union[str, Path]) -> np.ndarray:
        """
        Generate embedding for a single image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Normalized embedding vector as numpy array
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")
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
            self.logger.error(f"Failed to embed image {image_path}: {e}")
            raise
    
    def embed_images_batch(self, image_paths: List[Union[str, Path]]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple images in batch mode.
        More efficient for GPU processing.
        
        Args:
            image_paths: List of paths to image files
        
        Returns:
            List of normalized embedding vectors
        """
        try:
            # Load and preprocess all images
            images = []
            valid_indices = []
            
            for idx, img_path in enumerate(image_paths):
                try:
                    image = Image.open(img_path).convert("RGB")
                    images.append(self.preprocess(image))
                    valid_indices.append(idx)
                except Exception as e:
                    self.logger.warning(f"Failed to load image {img_path}: {e}")
            
            if not images:
                return []
            
            # Stack into batch tensor
            image_batch = torch.stack(images).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                embeddings = self.model.encode_image(image_batch)
                # Normalize
                embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embeddings_np = embeddings.cpu().numpy()
            
            return [embeddings_np[i] for i in range(len(embeddings_np))]
            
        except Exception as e:
            self.logger.error(f"Failed to embed batch: {e}")
            raise
    
    def get_embedding_dim(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        with torch.no_grad():
            dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
            embedding = self.model.encode_image(dummy_input)
            return embedding.shape[-1]
    
    def preload_for_inference(self):
        """Warm up the model with a dummy forward pass."""
        self.logger.info("Warming up model...")
        try:
            dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
            with torch.no_grad():
                _ = self.model.encode_image(dummy_input)
            self.logger.info("Model warmed up successfully")
        except Exception as e:
            self.logger.warning(f"Model warmup failed: {e}")
    
    def get_device_info(self) -> dict:
        """
        Get information about the current device.
        
        Returns:
            Dictionary with device information
        """
        info = {
            "device_type": self.device.type,
            "device_name": None,
            "total_memory_gb": None,
            "allocated_memory_gb": None,
        }
        
        if self.device.type == "cuda":
            info["device_name"] = torch.cuda.get_device_name(0)
            info["total_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / 1e9
            info["allocated_memory_gb"] = torch.cuda.memory_allocated(0) / 1e9
        
        return info


# Singleton instance for reuse
_embedder_instance = None


def get_embedder() -> CLIPEmbedder:
    """
    Get or create the global embedder instance.
    
    Returns:
        CLIPEmbedder instance
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = CLIPEmbedder()
    return _embedder_instance
