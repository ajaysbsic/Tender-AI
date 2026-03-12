"""
FAISS Index Manager: Vector similarity search and storage for tender chunks.

Features:
- Create and manage FAISS indices
- Store embeddings with metadata
- Query functions for specific section types (eligibility, penalties, deadlines)
- Persist indices locally
- Efficient similarity search
"""

import os
import pickle
import logging
from typing import List, Dict, Optional, Tuple, Set
import numpy as np
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class FAISSIndexManager:
    """Manage FAISS indices for tender embeddings."""
    
    def __init__(self, index_dir: str = "faiss_indices"):
        """
        Initialize FAISS index manager.
        
        Args:
            index_dir: Directory to store FAISS indices
        """
        try:
            import faiss
            self.faiss = faiss
        except ImportError:
            raise ImportError("faiss-cpu required. Install with: pip install faiss-cpu")
        
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.indices: Dict[str, Dict] = {}  # In-memory index cache
        self.metadata_store: Dict[str, List[Dict]] = {}  # Store chunk metadata
    
    def create_index(
        self,
        tender_id: str,
        dimension: int,
        index_type: str = "flat",
        **kwargs
    ) -> bool:
        """
        Create a FAISS index for a tender.
        
        Args:
            tender_id: Unique tender ID
            dimension: Embedding dimension
            index_type: Type of index ("flat", "ivf", "hnsw")
            **kwargs: Additional parameters for index
            
        Returns:
            True if successful
        """
        try:
            if index_type == "flat":
                index = self.faiss.IndexFlatL2(dimension)  # L2 distance (Euclidean)
            elif index_type == "ivf":
                quantizer = self.faiss.IndexFlatL2(dimension)
                nlist = kwargs.get('nlist', 100)
                index = self.faiss.IndexIVFFlat(quantizer, dimension, nlist)
            elif index_type == "hnsw":
                index = self.faiss.IndexHNSWFlat(dimension, kwargs.get('M', 32))
            else:
                raise ValueError(f"Unknown index type: {index_type}")
            
            self.indices[tender_id] = {
                'index': index,
                'dimension': dimension,
                'index_type': index_type,
                'size': 0,
            }
            
            self.metadata_store[tender_id] = []
            
            logger.info(f"Created {index_type} FAISS index for tender {tender_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            return False
    
    def add_embeddings(
        self,
        tender_id: str,
        embeddings: List[np.ndarray],
        metadata: List[Dict]
    ) -> int:
        """
        Add embeddings to an index.
        
        Args:
            tender_id: Tender ID
            embeddings: List of embedding vectors
            metadata: List of metadata dicts (must match embeddings)
            
        Returns:
            Number of embeddings added
        """
        if tender_id not in self.indices:
            raise ValueError(f"No index for tender {tender_id}. Create one first.")
        
        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata must have same length")
        
        try:
            # Convert list of embeddings to numpy array
            embeddings_array = np.array([np.array(e, dtype=np.float32) for e in embeddings])
            
            # Ensure correct shape (n_embeddings, dimension)
            if embeddings_array.ndim == 1:
                embeddings_array = embeddings_array.reshape(1, -1)
            
            # Add to FAISS index
            index = self.indices[tender_id]['index']
            index.add(embeddings_array)
            
            # Store metadata
            self.metadata_store[tender_id].extend(metadata)
            
            # Update size
            self.indices[tender_id]['size'] += len(embeddings)
            
            logger.info(f"Added {len(embeddings)} embeddings to tender {tender_id}")
            return len(embeddings)
        
        except Exception as e:
            logger.error(f"Failed to add embeddings: {e}")
            raise
    
    def search(
        self,
        tender_id: str,
        query_embedding: np.ndarray,
        k: int = 5,
        threshold: float = 0.0
    ) -> List[Dict]:
        """
        Search for similar chunks.
        
        Args:
            tender_id: Tender ID
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold (0-1, for L2 this is distance)
            
        Returns:
            List of similar chunks with metadata
        """
        if tender_id not in self.indices:
            raise ValueError(f"No index for tender {tender_id}")
        
        try:
            index = self.indices[tender_id]['index']
            metadata_list = self.metadata_store[tender_id]
            
            if index.ntotal == 0:
                return []
            
            # Ensure query embedding is correct shape
            query = np.array([query_embedding], dtype=np.float32)
            if query.ndim == 1:
                query = query.reshape(1, -1)
            
            # Search in FAISS index
            distances, indices = index.search(query, min(k, index.ntotal))
            
            # Build results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                # Convert L2 distance to similarity (1 / (1 + distance))
                similarity = 1.0 / (1.0 + float(distance))
                
                if similarity >= threshold:
                    result = metadata_list[int(idx)].copy()
                    result['similarity'] = similarity
                    result['distance'] = float(distance)
                    result['rank'] = i + 1
                    results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def search_by_section(
        self,
        tender_id: str,
        query_embedding: np.ndarray,
        section_type: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Search for chunks of a specific section type.
        
        Args:
            tender_id: Tender ID
            query_embedding: Query embedding
            section_type: Section type to filter (eligibility, penalties, deadlines, etc.)
            k: Number of results
            
        Returns:
            List of matching chunks
        """
        # Do general search first
        results = self.search(tender_id, query_embedding, k=k*2)  # Get more to filter
        
        # Filter by section type
        filtered = [r for r in results if r.get('section_type') == section_type]
        
        return filtered[:k]
    
    def search_eligibility(
        self,
        tender_id: str,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Dict]:
        """Search eligibility sections."""
        return self.search_by_section(tender_id, query_embedding, "eligibility", k)
    
    def search_penalties(
        self,
        tender_id: str,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Dict]:
        """Search penalty sections."""
        return self.search_by_section(tender_id, query_embedding, "penalties", k)
    
    def search_deadlines(
        self,
        tender_id: str,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Dict]:
        """Search deadline sections."""
        return self.search_by_section(tender_id, query_embedding, "deadlines", k)
    
    def search_technical(
        self,
        tender_id: str,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Dict]:
        """Search technical requirements sections."""
        return self.search_by_section(tender_id, query_embedding, "technical_requirements", k)
    
    def get_sections_by_type(
        self,
        tender_id: str,
        section_type: str
    ) -> List[Dict]:
        """Get all chunks of a specific section type (without search)."""
        if tender_id not in self.metadata_store:
            return []
        
        return [m for m in self.metadata_store[tender_id] if m.get('section_type') == section_type]
    
    def save_index(self, tender_id: str) -> bool:
        """
        Save FAISS index to disk.
        
        Args:
            tender_id: Tender ID
            
        Returns:
            True if successful
        """
        if tender_id not in self.indices:
            logger.warning(f"No index for tender {tender_id}")
            return False
        
        try:
            index_data = self.indices[tender_id]
            index_path = self.index_dir / f"{tender_id}.index"
            metadata_path = self.index_dir / f"{tender_id}.metadata"
            
            # Save FAISS index
            self.faiss.write_index(index_data['index'], str(index_path))
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump({
                    'metadata': self.metadata_store[tender_id],
                    'dimension': index_data['dimension'],
                    'index_type': index_data['index_type'],
                }, f, indent=2, default=str)
            
            logger.info(f"Saved FAISS index for tender {tender_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False
    
    def load_index(self, tender_id: str) -> bool:
        """
        Load FAISS index from disk.
        
        Args:
            tender_id: Tender ID
            
        Returns:
            True if successful
        """
        try:
            index_path = self.index_dir / f"{tender_id}.index"
            metadata_path = self.index_dir / f"{tender_id}.metadata"
            
            if not index_path.exists() or not metadata_path.exists():
                logger.warning(f"Index files not found for tender {tender_id}")
                return False
            
            # Load FAISS index
            index = self.faiss.read_index(str(index_path))
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                data = json.load(f)
            
            self.indices[tender_id] = {
                'index': index,
                'dimension': data['dimension'],
                'index_type': data['index_type'],
                'size': index.ntotal,
            }
            
            self.metadata_store[tender_id] = data['metadata']
            
            logger.info(f"Loaded FAISS index for tender {tender_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def delete_index(self, tender_id: str) -> bool:
        """Delete FAISS index from disk and memory."""
        try:
            # Remove from memory
            if tender_id in self.indices:
                del self.indices[tender_id]
            if tender_id in self.metadata_store:
                del self.metadata_store[tender_id]
            
            # Remove from disk
            index_path = self.index_dir / f"{tender_id}.index"
            metadata_path = self.index_dir / f"{tender_id}.metadata"
            
            if index_path.exists():
                index_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Deleted FAISS index for tender {tender_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            return False
    
    def get_index_info(self, tender_id: str) -> Dict:
        """Get information about an index."""
        if tender_id not in self.indices:
            return {}
        
        index_data = self.indices[tender_id]
        return {
            'tender_id': tender_id,
            'index_type': index_data['index_type'],
            'dimension': index_data['dimension'],
            'total_vectors': index_data['size'],
            'total_chunks': len(self.metadata_store.get(tender_id, [])),
        }
    
    def get_all_indices(self) -> Dict[str, Dict]:
        """Get info about all loaded indices."""
        return {tender_id: self.get_index_info(tender_id) for tender_id in self.indices}
    
    def list_saved_indices(self) -> List[str]:
        """List all saved indices on disk."""
        indices = []
        for path in self.index_dir.glob("*.index"):
            tender_id = path.stem
            indices.append(tender_id)
        return indices


class VectorStore:
    """High-level vector store interface for tender embeddings."""
    
    def __init__(self, faiss_manager: FAISSIndexManager):
        """Initialize vector store."""
        self.faiss_manager = faiss_manager
    
    def index_tender_chunks(
        self,
        tender_id: str,
        chunks: List[Dict],
        dimension: int
    ) -> bool:
        """
        Index all chunks for a tender.
        
        Args:
            tender_id: Tender ID
            chunks: List of chunk dicts with 'embedding' key
            dimension: Embedding dimension
            
        Returns:
            True if successful
        """
        try:
            # Create index
            self.faiss_manager.create_index(tender_id, dimension)
            
            # Prepare embeddings and metadata
            embeddings = []
            metadata = []
            
            for chunk in chunks:
                if 'embedding' not in chunk:
                    logger.warning(f"Chunk missing embedding: {chunk.get('chunk_id')}")
                    continue
                
                embeddings.append(chunk['embedding'])
                
                # Build metadata
                meta = {
                    'chunk_id': chunk.get('chunk_id'),
                    'text': chunk.get('text', '')[:500],  # Store first 500 chars
                    'section_type': chunk.get('section_type', 'other'),
                    'page': chunk.get('page', 1),
                    'tokens': chunk.get('tokens', 0),
                    'section_header': chunk.get('section_header', ''),
                }
                metadata.append(meta)
            
            # Add to index
            if embeddings:
                self.faiss_manager.add_embeddings(tender_id, embeddings, metadata)
                self.faiss_manager.save_index(tender_id)
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to index tender chunks: {e}")
            return False
    
    def search_similar(
        self,
        tender_id: str,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Dict]:
        """Search for similar chunks."""
        return self.faiss_manager.search(tender_id, query_embedding, k)
    
    def search_by_criteria(
        self,
        tender_id: str,
        query_embedding: np.ndarray,
        criteria: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Search by specific criteria.
        
        Args:
            tender_id: Tender ID
            query_embedding: Query embedding
            criteria: Criteria ("eligibility", "penalties", "deadlines", "technical")
            k: Number of results
            
        Returns:
            List of matching chunks
        """
        search_methods = {
            'eligibility': self.faiss_manager.search_eligibility,
            'penalties': self.faiss_manager.search_penalties,
            'deadlines': self.faiss_manager.search_deadlines,
            'technical': self.faiss_manager.search_technical,
        }
        
        if criteria not in search_methods:
            raise ValueError(f"Unknown criteria: {criteria}")
        
        return search_methods[criteria](tender_id, query_embedding, k)
