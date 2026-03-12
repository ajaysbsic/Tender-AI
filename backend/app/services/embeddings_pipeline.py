"""
Embedding Pipeline: Generate embeddings for tender chunks using configurable models.

Supports:
- OpenAI embeddings (text-embedding-3-small/large)
- Sentence-Transformers local embeddings (MiniLM, MPNET)
- Custom embedding functions
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Callable
from abc import ABC, abstractmethod
import os

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Array of shape (len(texts), embedding_dimension)
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider (text-embedding-3-small/large)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name ("text-embedding-3-small" or "text-embedding-3-large")
        """
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
        
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not provided and not found in environment")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Model dimensions
        self.dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            # Sort by index to ensure correct order
            embeddings = sorted(response.data, key=lambda x: x.index)
            embedding_list = [e.embedding for e in embeddings]
            
            return np.array(embedding_list, dtype=np.float32)
        
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    def get_dimension(self) -> int:
        return self.dimensions.get(self.model, 1536)
    
    def get_model_name(self) -> str:
        return self.model


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""
    
    # Recommended models with dimensions
    MODELS = {
        "all-MiniLM-L6-v2": 384,           # Fast, good quality
        "all-mpnet-base-v2": 768,          # Better quality, slower
        "paraphrase-MiniLM-L6-v2": 384,    # Good for paraphrasing
        "paraphrase-mpnet-base-v2": 768,   # Better paraphrase quality
    }
    
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """
        Initialize SentenceTransformer embedding provider.
        
        Args:
            model: Model name (see MODELS dict)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("sentence-transformers required. Install with: pip install sentence-transformers")
        
        if model not in self.MODELS:
            logger.warning(f"Model {model} not in recommended list. Will try to load anyway.")
        
        self.model = model
        self.encoder = SentenceTransformer(model)
        self.dimension = self.MODELS.get(model, self.encoder.get_sentence_embedding_dimension())
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using sentence-transformers."""
        try:
            embeddings = self.encoder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"SentenceTransformer embedding failed: {e}")
            raise
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_model_name(self) -> str:
        return self.model


class CustomEmbeddingProvider(EmbeddingProvider):
    """Wrapper for custom embedding functions."""
    
    def __init__(self, embed_func: Callable, model_name: str, dimension: int):
        """
        Initialize custom embedding provider.
        
        Args:
            embed_func: Function that takes List[str] and returns np.ndarray
            model_name: Name of the model
            dimension: Embedding dimension
        """
        self.embed_func = embed_func
        self.model_name = model_name
        self.dimension = dimension
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using custom function."""
        try:
            embeddings = self.embed_func(texts)
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Custom embedding failed: {e}")
            raise
    
    def get_dimension(self) -> int:
        return self.dimension
    
    def get_model_name(self) -> str:
        return self.model_name


class EmbeddingPipeline:
    """Main embedding pipeline for processing tender chunks."""
    
    def __init__(
        self,
        provider: Optional[EmbeddingProvider] = None,
        batch_size: int = 32,
        cache_embeddings: bool = True
    ):
        """
        Initialize embedding pipeline.
        
        Args:
            provider: Embedding provider (default: OpenAI text-embedding-3-small)
            batch_size: Batch size for processing
            cache_embeddings: Whether to cache embeddings in memory
        """
        if provider is None:
            # Default to OpenAI
            try:
                provider = OpenAIEmbeddingProvider()
            except ValueError:
                logger.warning("OpenAI API key not found. Using SentenceTransformer.")
                provider = SentenceTransformerEmbeddingProvider()
        
        self.provider = provider
        self.batch_size = batch_size
        self.cache_embeddings = cache_embeddings
        self.cache: Dict[str, np.ndarray] = {} if cache_embeddings else None
    
    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Embed a list of chunks.
        
        Args:
            chunks: List of chunk dicts with 'text' key
            
        Returns:
            List of chunk dicts with 'embedding' key added
        """
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embed_texts(texts)
        
        result = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_copy = chunk.copy()
            chunk_copy['embedding'] = embedding.tolist()  # Convert to list for JSON serialization
            chunk_copy['embedding_model'] = self.provider.get_model_name()
            chunk_copy['embedding_dimension'] = self.provider.get_dimension()
            result.append(chunk_copy)
        
        return result
    
    def embed_texts(self, texts: List[str], use_cache: bool = True) -> np.ndarray:
        """
        Embed a list of texts in batches.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache for previously seen texts
            
        Returns:
            Array of shape (len(texts), embedding_dimension)
        """
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self.provider.get_dimension())
        
        all_embeddings = []
        texts_to_embed = []
        original_indices = []
        
        # Check cache for known texts
        if use_cache and self.cache is not None:
            for i, text in enumerate(texts):
                text_hash = hash(text)
                if text_hash in self.cache:
                    all_embeddings.append((i, self.cache[text_hash]))
                else:
                    texts_to_embed.append(text)
                    original_indices.append(i)
        else:
            texts_to_embed = texts
            original_indices = list(range(len(texts)))
        
        # Embed in batches
        if texts_to_embed:
            for batch_start in range(0, len(texts_to_embed), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(texts_to_embed))
                batch_texts = texts_to_embed[batch_start:batch_end]
                
                batch_embeddings = self.provider.embed(batch_texts)
                
                # Cache and store
                for text, embedding in zip(batch_texts, batch_embeddings):
                    text_hash = hash(text)
                    if self.cache is not None:
                        self.cache[text_hash] = embedding
                    
                    original_idx = original_indices[batch_start + (len(all_embeddings) - len(all_embeddings))]
                    all_embeddings.append((original_idx, embedding))
        
        # Sort by original index to maintain order
        all_embeddings.sort(key=lambda x: x[0])
        embeddings_array = np.array([e[1] for e in all_embeddings], dtype=np.float32)
        
        return embeddings_array
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a search query.
        
        Args:
            query: Query text
            
        Returns:
            Embedding array of shape (1, embedding_dimension)
        """
        embedding = self.provider.embed([query])
        return embedding[0]
    
    def compute_similarity(self, query_embedding: np.ndarray, chunk_embeddings: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between query and chunks.
        
        Args:
            query_embedding: Query embedding (shape: embedding_dimension)
            chunk_embeddings: Chunk embeddings (shape: n_chunks, embedding_dimension)
            
        Returns:
            Similarity scores (shape: n_chunks)
        """
        # Normalize vectors for cosine similarity
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        chunk_norms = chunk_embeddings / (np.linalg.norm(chunk_embeddings, axis=1, keepdims=True) + 1e-8)
        
        # Compute cosine similarity
        similarities = np.dot(chunk_norms, query_norm)
        
        return similarities
    
    def get_model_info(self) -> Dict:
        """Get information about the embedding model."""
        return {
            'model_name': self.provider.get_model_name(),
            'dimension': self.provider.get_dimension(),
            'batch_size': self.batch_size,
            'cache_enabled': self.cache_embeddings,
            'cache_size': len(self.cache) if self.cache is not None else 0,
        }
    
    def clear_cache(self):
        """Clear embedding cache."""
        if self.cache is not None:
            self.cache.clear()
            logger.info("Embedding cache cleared")


def create_embedding_pipeline(
    provider_type: str = "openai",
    model_name: str = "text-embedding-3-small",
    **kwargs
) -> EmbeddingPipeline:
    """
    Factory function to create embedding pipeline.
    
    Args:
        provider_type: "openai" or "sentence-transformers" or "custom"
        model_name: Model name (depends on provider)
        **kwargs: Additional arguments for pipeline
        
    Returns:
        Configured EmbeddingPipeline
    """
    if provider_type == "openai":
        provider = OpenAIEmbeddingProvider(model=model_name)
    elif provider_type == "sentence-transformers":
        provider = SentenceTransformerEmbeddingProvider(model=model_name)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    return EmbeddingPipeline(provider=provider, **kwargs)
