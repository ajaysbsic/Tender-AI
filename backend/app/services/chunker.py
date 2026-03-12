"""
Chunking Module: Break tender text into semantic chunks while preserving section metadata.

Requirements:
- Chunk size: 800-1200 tokens
- Preserve section type metadata
- Smart boundaries (sentence/paragraph-aware)
- Maintain context and references
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from app.services.section_detector import SectionType

try:
    import tiktoken
except ImportError:
    tiktoken = None

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Try to download punkt tokenizer if not available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Different strategies for chunking documents"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


class TextChunker:
    """Break text into semantic chunks with metadata preservation."""
    
    # Default chunk size in tokens
    DEFAULT_CHUNK_SIZE_TOKENS = 1000
    DEFAULT_MIN_CHUNK_SIZE_TOKENS = 800
    DEFAULT_MAX_CHUNK_SIZE_TOKENS = 1200
    DEFAULT_OVERLAP_TOKENS = 100
    
    # Character-to-token ratio (approximate)
    CHAR_TO_TOKEN_RATIO = 4.0  # Rough average: 1 token ≈ 4 characters
    
    def __init__(
        self,
        chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
        min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE_TOKENS,
        max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE_TOKENS,
        overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
        use_tiktoken: bool = True
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size_tokens: Target chunk size in tokens (800-1200)
            min_chunk_size: Minimum chunk size in tokens
            max_chunk_size: Maximum chunk size in tokens
            overlap_tokens: Overlap between chunks (context preservation)
            use_tiktoken: Use OpenAI's tiktoken for accurate token counting
        """
        self.chunk_size_tokens = chunk_size_tokens
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_tokens = overlap_tokens
        self.use_tiktoken = use_tiktoken and tiktoken is not None
        
        if self.use_tiktoken:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-3.5/4 encoding
            except Exception as e:
                logger.warning(f"Failed to initialize tiktoken: {e}, using character-based counting")
                self.tokenizer = None
        else:
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or character estimation."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Tiktoken counting failed: {e}, using char-based")
        
        # Fallback to character-based estimation
        return int(len(text) / self.CHAR_TO_TOKEN_RATIO)
    
    def chunk_text(
        self,
        text: str,
        section_type: SectionType = SectionType.OTHER,
        page_number: int = 1,
        chunk_strategy: str = ChunkingStrategy.SENTENCE
    ) -> List[Dict]:
        """
        Break text into chunks with metadata.
        
        Args:
            text: Input text to chunk
            section_type: Type of section (for metadata)
            page_number: Original page number
            chunk_strategy: Strategy for chunking
            
        Returns:
            List of chunk dicts with: {
                chunk_id, text, tokens, section_type, page, position,
                total_chunks, overlap_with_next
            }
        """
        if not text or len(text.strip()) < 50:
            return []
        
        # Choose chunking strategy
        if chunk_strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentences(text)
        elif chunk_strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraphs(text)
        else:  # ChunkingStrategy.FIXED_SIZE or SEMANTIC
            chunks = self._chunk_by_fixed_size(text)
        
        # Merge small chunks and add overlap
        chunks = self._merge_small_chunks(chunks)
        chunks = self._add_overlap(chunks)
        
        # Add metadata to each chunk
        result = []
        for idx, chunk_text in enumerate(chunks):
            token_count = self.count_tokens(chunk_text)
            
            result.append({
                'chunk_id': f"page_{page_number}_chunk_{idx}",
                'text': chunk_text,
                'tokens': token_count,
                'section_type': section_type.value if isinstance(section_type, SectionType) else section_type,
                'page': page_number,
                'position': idx,
                'total_chunks': len(chunks),
                'char_count': len(chunk_text),
                'within_limits': self.min_chunk_size <= token_count <= self.max_chunk_size
            })
        
        return result
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk text by sentences, respecting size limits."""
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            logger.warning(f"Sentence tokenization failed: {e}, using simple splitting")
            sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            test_chunk = f"{current_chunk} {sentence}".strip()
            token_count = self.count_tokens(test_chunk)
            
            if token_count <= self.max_chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is full
                if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        # Add final chunk
        if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]
    
    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """Chunk text by paragraphs, merging small ones."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            test_chunk = f"{current_chunk}\n\n{para}".strip()
            token_count = self.count_tokens(test_chunk)
            
            if token_count <= self.max_chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                current_chunk = para
        
        if current_chunk and self.count_tokens(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]
    
    def _chunk_by_fixed_size(self, text: str) -> List[str]:
        """Chunk text by fixed token size."""
        target_char_size = int(self.chunk_size_tokens * self.CHAR_TO_TOKEN_RATIO)
        chunks = []
        
        start = 0
        while start < len(text):
            end = min(start + target_char_size, len(text))
            
            # Try to find a good break point (sentence end)
            if end < len(text):
                # Look backward for sentence end
                last_period = text.rfind('.', start, end)
                if last_period > start + target_char_size * 0.7:  # At least 70% through
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end
        
        return chunks if chunks else [text]
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """Merge chunks that are smaller than minimum size."""
        merged = []
        
        for chunk in chunks:
            if merged and self.count_tokens(merged[-1]) < self.min_chunk_size:
                # Previous chunk is small, merge with current
                merged[-1] = f"{merged[-1]}\n\n{chunk}"
            else:
                merged.append(chunk)
        
        # Handle last chunk
        if merged and self.count_tokens(merged[-1]) < self.min_chunk_size and len(merged) > 1:
            merged[-2] = f"{merged[-2]}\n\n{merged[-1]}"
            merged.pop()
        
        return merged
    
    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlap between chunks for context preservation."""
        if len(chunks) <= 1:
            return chunks
        
        overlapped = [chunks[0]]
        overlap_char_size = int(self.overlap_tokens * self.CHAR_TO_TOKEN_RATIO)
        
        for i in range(1, len(chunks)):
            prev_chunk = overlapped[-1]
            current_chunk = chunks[i]
            
            # Take last part of previous chunk as context
            if len(prev_chunk) > overlap_char_size:
                overlap_text = prev_chunk[-overlap_char_size:]
                overlapped.append(f"{overlap_text}\n\n{current_chunk}")
            else:
                overlapped.append(current_chunk)
        
        return overlapped
    
    def chunk_section(
        self,
        header: str,
        content: str,
        section_type: SectionType,
        page_number: int = 1
    ) -> List[Dict]:
        """
        Chunk a complete section (header + content).
        
        Args:
            header: Section header
            content: Section content
            section_type: Type of section
            page_number: Original page number
            
        Returns:
            List of chunks with metadata
        """
        # Combine header and content
        full_text = f"{header}\n\n{content}"
        
        # Chunk the text
        chunks = self.chunk_text(full_text, section_type, page_number)
        
        return chunks
    
    def chunk_document(
        self,
        sections: List[Dict],
        page_map: Optional[Dict[int, int]] = None
    ) -> List[Dict]:
        """
        Chunk a complete document (list of sections).
        
        Args:
            sections: List of section dicts from SectionDetector
            page_map: Optional mapping of text position to page number
            
        Returns:
            List of all chunks across all sections
        """
        all_chunks = []
        
        for section in sections:
            chunks = self.chunk_section(
                header=section.get('header', 'Section'),
                content=section.get('content', ''),
                section_type=SectionType(section.get('section_type', SectionType.OTHER)),
                page_number=section.get('page', 1)
            )
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def get_chunking_statistics(self, chunks: List[Dict]) -> Dict:
        """Get statistics about chunks."""
        if not chunks:
            return {}
        
        token_counts = [c['tokens'] for c in chunks]
        char_counts = [c['char_count'] for c in chunks]
        
        stats = {
            'total_chunks': len(chunks),
            'total_tokens': sum(token_counts),
            'total_characters': sum(char_counts),
            'avg_chunk_tokens': sum(token_counts) / len(chunks),
            'avg_chunk_chars': sum(char_counts) / len(chunks),
            'min_chunk_tokens': min(token_counts),
            'max_chunk_tokens': max(token_counts),
            'chunks_within_limits': sum(1 for c in chunks if c['within_limits']),
            'section_distribution': {},
        }
        
        # Count by section type
        for chunk in chunks:
            sec_type = chunk['section_type']
            if sec_type not in stats['section_distribution']:
                stats['section_distribution'][sec_type] = 0
            stats['section_distribution'][sec_type] += 1
        
        return stats


def estimate_tokens(text: str, use_tiktoken: bool = True) -> int:
    """Estimate token count for text."""
    if use_tiktoken and tiktoken:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except:
            pass
    
    # Fallback to character-based estimation
    return int(len(text) / 4.0)
