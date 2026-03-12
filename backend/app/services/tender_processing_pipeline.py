"""
Integration Module: Orchestrate Step-5 and Step-6 workflows.

Coordinates:
- Section detection (Step-5)
- Text chunking (Step-5)
- Embedding generation (Step-6)
- FAISS indexing (Step-6)
"""

import logging
from typing import List, Dict, Optional, Tuple
from app.services.parser import DocumentParser
from app.services.section_detector import SectionDetector, SectionType
from app.services.chunker import TextChunker, ChunkingStrategy
from app.services.embeddings_pipeline import EmbeddingPipeline, create_embedding_pipeline
from app.services.faiss_manager import FAISSIndexManager, VectorStore
import numpy as np

logger = logging.getLogger(__name__)


class TenderProcessingPipeline:
    """
    Complete pipeline for processing tender documents:
    Document → Sections → Chunks → Embeddings → FAISS Index
    """
    
    def __init__(
        self,
        embedding_provider: str = "openai",
        embedding_model: str = "text-embedding-3-small",
        chunk_size_tokens: int = 1000,
        faiss_index_dir: str = "faiss_indices"
    ):
        """
        Initialize the processing pipeline.
        
        Args:
            embedding_provider: "openai" or "sentence-transformers"
            embedding_model: Model name
            chunk_size_tokens: Target chunk size (800-1200)
            faiss_index_dir: Directory for FAISS indices
        """
        self.section_detector = SectionDetector()
        self.text_chunker = TextChunker(
            chunk_size_tokens=chunk_size_tokens,
            min_chunk_size=800,
            max_chunk_size=1200
        )
        self.embedding_pipeline = create_embedding_pipeline(
            provider_type=embedding_provider,
            model_name=embedding_model
        )
        self.faiss_manager = FAISSIndexManager(faiss_index_dir)
        self.vector_store = VectorStore(self.faiss_manager)
    
    def process_file(
        self,
        file_path: str,
        tender_id: str,
        save_index: bool = True
    ) -> Dict:
        """
        Process a complete tender file.
        
        Args:
            file_path: Path to PDF/DOCX file
            tender_id: Unique tender ID
            save_index: Whether to save FAISS index to disk
            
        Returns:
            Processing result with statistics
        """
        result = {
            'tender_id': tender_id,
            'file_path': file_path,
            'sections': [],
            'chunks': [],
            'embeddings': [],
            'statistics': {},
            'errors': []
        }
        
        try:
            # Step 1: Parse document with streaming
            logger.info(f"Parsing document: {file_path}")
            all_chunks_from_file = []
            
            # Detect file type
            if file_path.lower().endswith('.pdf'):
                for page_data in DocumentParser.stream_pdf_pages(file_path):
                    all_chunks_from_file.append({
                        'text': page_data['text'],
                        'page': page_data['page'],
                        'language': page_data['language']
                    })
            elif file_path.lower().endswith('.docx'):
                for section_data in DocumentParser.stream_docx_paragraphs(file_path):
                    all_chunks_from_file.append({
                        'text': section_data['text'],
                        'page': 1,
                        'language': section_data.get('language', 'en')
                    })
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
            
            # Step 2: Detect sections
            logger.info("Detecting sections...")
            combined_text = "\n\n".join([c['text'] for c in all_chunks_from_file[:50]])  # First 50 pages
            sections = self.section_detector.detect_sections(combined_text)
            result['sections'] = sections
            
            # Step 3: Chunk the document
            logger.info("Chunking document...")
            all_chunks = []
            
            for page_data in all_chunks_from_file:
                # Detect section type for this content
                section_type = self._determine_section_type(page_data['text'], sections)
                
                # Chunk the page
                chunks = self.text_chunker.chunk_text(
                    text=page_data['text'],
                    section_type=section_type,
                    page_number=page_data['page'],
                    chunk_strategy=ChunkingStrategy.SENTENCE
                )
                
                all_chunks.extend(chunks)
            
            result['chunks'] = all_chunks
            
            # Step 4: Generate embeddings
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            embedded_chunks = self.embedding_pipeline.embed_chunks(all_chunks)
            result['embeddings'] = embedded_chunks
            
            # Step 5: Create and populate FAISS index
            logger.info("Creating FAISS index...")
            embedding_dim = self.embedding_pipeline.provider.get_dimension()
            success = self.vector_store.index_tender_chunks(
                tender_id=tender_id,
                chunks=embedded_chunks,
                dimension=embedding_dim
            )
            
            if not success:
                result['errors'].append("Failed to create FAISS index")
            
            # Step 6: Compile statistics
            result['statistics'] = self._compile_statistics(
                all_chunks,
                sections,
                embedded_chunks
            )
            
            logger.info(f"Processing complete for {tender_id}")
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            result['errors'].append(str(e))
        
        return result
    
    def _determine_section_type(self, text: str, sections: List[Dict]) -> SectionType:
        """Determine section type for text chunk."""
        # Use section detector to classify
        section_type, confidence = self.section_detector._classify_section("", text[:500])
        return section_type if confidence > 0.3 else SectionType.OTHER
    
    def _compile_statistics(
        self,
        chunks: List[Dict],
        sections: List[Dict],
        embedded_chunks: List[Dict]
    ) -> Dict:
        """Compile processing statistics."""
        if not chunks:
            return {}
        
        token_counts = [c['tokens'] for c in chunks]
        
        stats = {
            'total_chunks': len(chunks),
            'total_sections': len(sections),
            'total_tokens': sum(token_counts),
            'total_characters': sum(c['char_count'] for c in chunks),
            'avg_chunk_tokens': sum(token_counts) / len(chunks),
            'sections_by_type': {},
            'embedding_model': self.embedding_pipeline.provider.get_model_name(),
            'embedding_dimension': self.embedding_pipeline.provider.get_dimension(),
        }
        
        # Count sections by type
        for section in sections:
            sec_type = section['section_type'].value if isinstance(section['section_type'], SectionType) else section['section_type']
            stats['sections_by_type'][sec_type] = stats['sections_by_type'].get(sec_type, 0) + 1
        
        # Count chunks by type
        chunks_by_type = {}
        for chunk in chunks:
            sec_type = chunk['section_type']
            chunks_by_type[sec_type] = chunks_by_type.get(sec_type, 0) + 1
        
        stats['chunks_by_type'] = chunks_by_type
        
        return stats
    
    def query_tender(
        self,
        tender_id: str,
        query: str,
        k: int = 5,
        section_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Query a processed tender.
        
        Args:
            tender_id: Tender ID
            query: Search query
            k: Number of results
            section_type: Optional section filter
            
        Returns:
            List of relevant chunks
        """
        try:
            # Load index if needed
            if tender_id not in self.faiss_manager.indices:
                self.faiss_manager.load_index(tender_id)
            
            # Embed query
            query_embedding = self.embedding_pipeline.embed_query(query)
            
            # Search
            if section_type:
                results = self.faiss_manager.search_by_section(
                    tender_id,
                    query_embedding,
                    section_type,
                    k
                )
            else:
                results = self.faiss_manager.search(tender_id, query_embedding, k)
            
            return results
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def get_section_content(
        self,
        tender_id: str,
        section_type: str
    ) -> List[Dict]:
        """Get all chunks of a specific section type."""
        try:
            if tender_id not in self.faiss_manager.metadata_store:
                self.faiss_manager.load_index(tender_id)
            
            return self.faiss_manager.get_sections_by_type(tender_id, section_type)
        
        except Exception as e:
            logger.error(f"Failed to get section content: {e}")
            return []
    
    def get_tenderness_summary(self, tender_id: str) -> Dict:
        """Get summary of processed tender."""
        try:
            index_info = self.faiss_manager.get_index_info(tender_id)
            return {
                'tender_id': tender_id,
                'total_chunks': index_info.get('total_chunks', 0),
                'total_vectors': index_info.get('total_vectors', 0),
                'embedding_model': self.embedding_pipeline.provider.get_model_name(),
                'index_type': index_info.get('index_type', 'unknown'),
            }
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            return {}


# Convenience functions

def process_tender_file(
    file_path: str,
    tender_id: str,
    embedding_provider: str = "openai",
    embedding_model: str = "text-embedding-3-small"
) -> Dict:
    """
    Process a tender file end-to-end.
    
    Args:
        file_path: Path to tender document
        tender_id: Unique tender ID
        embedding_provider: Embedding provider
        embedding_model: Embedding model
        
    Returns:
        Processing result
    """
    pipeline = TenderProcessingPipeline(
        embedding_provider=embedding_provider,
        embedding_model=embedding_model
    )
    return pipeline.process_file(file_path, tender_id)


def search_tender(
    tender_id: str,
    query: str,
    section_type: Optional[str] = None,
    k: int = 5
) -> List[Dict]:
    """
    Search a processed tender.
    
    Args:
        tender_id: Tender ID
        query: Search query
        section_type: Optional section filter
        k: Number of results
        
    Returns:
        List of relevant chunks
    """
    pipeline = TenderProcessingPipeline()
    return pipeline.query_tender(tender_id, query, k, section_type)
