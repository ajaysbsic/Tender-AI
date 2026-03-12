"""
Step-5 & Step-6 Demo: Chunking, Section Detection, and FAISS Embedding Pipeline

Demonstrates:
1. Section detection from tender text
2. Intelligent chunking (800-1200 tokens)
3. Embedding generation (OpenAI or local)
4. FAISS vector indexing
5. Semantic search with metadata filtering
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.section_detector import SectionDetector, SectionType
from app.services.chunker import TextChunker, ChunkingStrategy
from app.services.embeddings_pipeline import (
    SentenceTransformerEmbeddingProvider,
    create_embedding_pipeline
)
from app.services.faiss_manager import FAISSIndexManager, VectorStore
from app.services.tender_processing_pipeline import TenderProcessingPipeline
import numpy as np


# ============================================================================
# DEMO 1: Section Detection
# ============================================================================

def demo_section_detection():
    """Demonstrate section detection with regex patterns."""
    print("\n" + "="*80)
    print("DEMO 1: Section Detection")
    print("="*80)
    
    sample_text = """
    1. ELIGIBILITY REQUIREMENTS
    
    Companies must meet the following eligibility criteria:
    - Minimum 5 years of experience in similar projects
    - ISO 9001 certification
    - Annual turnover of at least $5 million
    - No pending litigation
    
    2. TECHNICAL REQUIREMENTS
    
    The solution must support:
    - Cloud-based infrastructure
    - API-first architecture
    - 99.9% uptime SLA
    - Real-time data processing
    
    3. COMMERCIAL TERMS
    
    Payment terms: Net 30
    Warranty period: 12 months
    Price: Fixed price contract
    Insurance: Required coverage details
    
    4. DEADLINES AND SUBMISSION
    
    Proposal submission deadline: 2026-02-28
    Final bid close: March 31, 2026 by 5:00 PM EST
    Award date: May 15, 2026
    
    5. PENALTIES FOR NON-COMPLIANCE
    
    Liquidated damages: 0.5% per week of delay
    Performance penalty: 1% for each failed requirement
    Late submission penalty: Automatic rejection
    """
    
    detector = SectionDetector()
    sections = detector.detect_sections(sample_text)
    
    print(f"\nDetected {len(sections)} sections:\n")
    for section in sections:
        print(f"  Header: {section['header']}")
        print(f"  Type: {section['section_type'].value}")
        print(f"  Confidence: {section['confidence']:.2%}")
        print(f"  Content Preview: {section['content'][:100]}...")
        print()
    
    # Get statistics
    stats = detector.get_section_statistics(sections)
    print(f"\nStatistics:")
    print(f"  Total sections: {stats['total_sections']}")
    print(f"  Average confidence: {stats['avg_confidence']:.2%}")
    print(f"  Confidence by type: {stats['confidence_by_type']}")


# ============================================================================
# DEMO 2: Text Chunking with Token Counting
# ============================================================================

def demo_text_chunking():
    """Demonstrate intelligent text chunking."""
    print("\n" + "="*80)
    print("DEMO 2: Text Chunking (800-1200 tokens)")
    print("="*80)
    
    sample_text = """
    The scope of work includes the design, development, testing, and deployment of 
    a cloud-based analytics platform. The system must be capable of processing 
    large volumes of data in real-time, with support for multiple data sources and 
    output formats.
    
    Key deliverables include: comprehensive system architecture documentation, 
    fully functional software modules, automated test suites with 95%+ code coverage, 
    user training materials, and ongoing technical support for the first year.
    
    The project timeline spans 12 months, divided into four quarters with specific 
    milestones. Q1 focuses on architecture and design. Q2 covers core development. 
    Q3 includes testing and quality assurance. Q4 handles deployment and training.
    
    Technical requirements specify that all components must follow REST API standards, 
    use PostgreSQL for data storage, implement OAuth 2.0 for security, and support 
    horizontal scaling. Performance requirements mandate sub-100ms response times, 
    99.9% uptime SLA, and support for 10,000 concurrent users.
    """
    
    chunker = TextChunker()
    chunks = chunker.chunk_text(
        text=sample_text,
        section_type=SectionType.TECHNICAL_REQUIREMENTS,
        page_number=1
    )
    
    print(f"\nChunked {len(chunks)} chunks from sample text:\n")
    for chunk in chunks:
        print(f"  Chunk {chunk['position'] + 1}:")
        print(f"    Tokens: {chunk['tokens']} (within limits: {chunk['within_limits']})")
        print(f"    Characters: {chunk['char_count']}")
        print(f"    Section: {chunk['section_type']}")
        print(f"    Text: {chunk['text'][:80]}...")
        print()
    
    # Statistics
    stats = chunker.get_chunking_statistics(chunks)
    print(f"Statistics:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Average chunk size: {stats['avg_chunk_tokens']:.0f} tokens")
    print(f"  Chunks within limits: {stats['chunks_within_limits']}/{stats['total_chunks']}")


# ============================================================================
# DEMO 3: Embedding Generation (Local)
# ============================================================================

def demo_embeddings_local():
    """Demonstrate embedding generation using SentenceTransformers."""
    print("\n" + "="*80)
    print("DEMO 3: Embedding Generation (SentenceTransformers)")
    print("="*80)
    
    # Use local embeddings (no API key required)
    try:
        provider = SentenceTransformerEmbeddingProvider(model="all-MiniLM-L6-v2")
        pipeline = create_embedding_pipeline(
            provider_type="sentence-transformers",
            model_name="all-MiniLM-L6-v2"
        )
        
        # Sample texts
        texts = [
            "The company must have ISO 9001 certification",
            "Minimum 5 years of experience required",
            "Submit proposals by March 31, 2026",
            "Late submissions will be automatically rejected",
        ]
        
        print(f"\nEmbedding {len(texts)} sample texts...\n")
        embeddings = pipeline.embed_texts(texts)
        
        print(f"Embedding shape: {embeddings.shape}")
        print(f"Model: {pipeline.provider.get_model_name()}")
        print(f"Dimension: {pipeline.provider.get_dimension()}\n")
        
        # Compute similarity between texts
        print("Similarity matrix (first 3 sentences):")
        for i in range(min(3, len(embeddings))):
            similarities = pipeline.compute_similarity(embeddings[i], embeddings)
            print(f"  '{texts[i][:40]}...'")
            for j, sim in enumerate(similarities):
                print(f"    vs text {j+1}: {sim:.3f}")
        
        print("\n✓ Embedding pipeline ready for tender processing!")
    
    except ImportError as e:
        print(f"\n✗ SentenceTransformers not available: {e}")
        print("  Install with: pip install sentence-transformers")


# ============================================================================
# DEMO 4: FAISS Indexing and Search
# ============================================================================

def demo_faiss_indexing():
    """Demonstrate FAISS indexing and semantic search."""
    print("\n" + "="*80)
    print("DEMO 4: FAISS Indexing and Semantic Search")
    print("="*80)
    
    try:
        import faiss
    except ImportError:
        print("\n✗ FAISS not installed. Install with: pip install faiss-cpu")
        return
    
    # Initialize components
    provider = SentenceTransformerEmbeddingProvider(model="all-MiniLM-L6-v2")
    pipeline = create_embedding_pipeline(
        provider_type="sentence-transformers",
        model_name="all-MiniLM-L6-v2"
    )
    
    # Sample tender chunks
    chunks = [
        {
            'chunk_id': 'chunk_1',
            'text': 'Company must be ISO 9001 certified with 5+ years experience',
            'section_type': 'eligibility',
            'page': 1,
        },
        {
            'chunk_id': 'chunk_2',
            'text': 'Late submission penalty: automatic rejection of proposal',
            'section_type': 'penalties',
            'page': 5,
        },
        {
            'chunk_id': 'chunk_3',
            'text': 'Proposal submission deadline is March 31, 2026 at 5 PM EST',
            'section_type': 'deadlines',
            'page': 2,
        },
        {
            'chunk_id': 'chunk_4',
            'text': 'Must implement REST APIs with OAuth 2.0 security',
            'section_type': 'technical_requirements',
            'page': 8,
        },
    ]
    
    # Generate embeddings
    print("\nGenerating embeddings...\n")
    embedded_chunks = pipeline.embed_chunks(chunks)
    
    # Create and populate FAISS index
    print("Creating FAISS index...\n")
    faiss_mgr = FAISSIndexManager()
    vector_store = VectorStore(faiss_mgr)
    
    tender_id = "tender_demo_001"
    success = vector_store.index_tender_chunks(
        tender_id=tender_id,
        chunks=embedded_chunks,
        dimension=provider.get_dimension()
    )
    
    if success:
        print(f"✓ Indexed {len(embedded_chunks)} chunks")
        
        # Perform searches
        print("\n" + "-"*80)
        print("SEMANTIC SEARCH TESTS")
        print("-"*80)
        
        test_queries = [
            ("company certification", "eligibility"),
            ("when to submit", "deadlines"),
            ("technical stack", "technical_requirements"),
            ("what happens if late", "penalties"),
        ]
        
        for query, expected_type in test_queries:
            print(f"\nQuery: '{query}' (expecting {expected_type})")
            query_embedding = pipeline.embed_query(query)
            results = faiss_mgr.search(tender_id, query_embedding, k=2)
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result['section_type']}] Sim: {result['similarity']:.3f}")
                print(f"     {result['text'][:60]}...")


# ============================================================================
# DEMO 5: Complete Pipeline
# ============================================================================

def demo_complete_pipeline():
    """Demonstrate complete end-to-end pipeline."""
    print("\n" + "="*80)
    print("DEMO 5: Complete Processing Pipeline (Sections → Chunks → Embeddings → FAISS)")
    print("="*80)
    
    try:
        # Initialize pipeline
        print("\nInitializing pipeline...")
        pipeline = TenderProcessingPipeline(
            embedding_provider="sentence-transformers",
            embedding_model="all-MiniLM-L6-v2"
        )
        
        # Create sample tender document
        sample_tender = """
        REQUEST FOR PROPOSAL: Cloud Analytics Platform
        
        1. ELIGIBILITY CRITERIA
        
        Eligible vendors must demonstrate:
        - ISO 27001 Information Security certification
        - Minimum 7 years delivering enterprise analytics solutions
        - Annual revenue exceeding $10 million
        - Active support for at least 500 concurrent users
        - Zero critical security vulnerabilities in past 2 years
        
        2. TECHNICAL REQUIREMENTS
        
        System Architecture:
        - Cloud-native design on AWS/Azure
        - Kubernetes-based container orchestration
        - GraphQL and REST API endpoints
        - Real-time data streaming with Apache Kafka
        - Machine learning capabilities using TensorFlow
        - Support for custom Python/R model integration
        
        Performance Specifications:
        - Query response time < 200ms for 95th percentile
        - System availability: 99.99% uptime SLA
        - Concurrent user support: minimum 5000 users
        - Data storage: petabyte-scale PostgreSQL + S3
        
        3. COMMERCIAL TERMS AND CONDITIONS
        
        Payment Model:
        - Year 1: $500,000 fixed software license
        - Years 2-3: Annual maintenance at 20% of license cost
        - Additional: $50/month per additional concurrent user
        
        Warranty and Support:
        - 12-month software defect warranty
        - 24/7/365 priority support included
        - Quarterly software updates mandatory
        
        4. PROJECT SCHEDULE AND DEADLINES
        
        Key Milestones:
        - Proposal Submission: March 31, 2026, 5:00 PM EST
        - Technical Evaluation: April 15-30, 2026
        - Vendor Presentations: May 5-10, 2026
        - Final Selection: May 20, 2026
        - Contract Signature: May 25, 2026
        - Project Kickoff: June 1, 2026
        - Phase 1 Delivery: August 31, 2026
        
        5. PENALTIES FOR NON-PERFORMANCE
        
        Late Submission: Automatic disqualification
        Schedule Delays: 1% per week liquidated damages
        Performance Failures:
          - System downtime >0.01%: 0.5% monthly fee reduction
          - Query response >200ms: 0.25% monthly fee reduction
          - Security incidents: $50,000 per incident
        Warranty Violations: Full refund + $100,000 penalty
        """
        
        # Process the tender
        print("Processing tender document...")
        result = pipeline.process_file("sample_tender.txt", "tender_001")
        
        # Display results
        print(f"\n✓ Processing complete!\n")
        print(f"Sections detected: {len(result['sections'])}")
        print(f"Chunks created: {len(result['chunks'])}")
        print(f"Embeddings generated: {len(result['embeddings'])}")
        
        if result['statistics']:
            stats = result['statistics']
            print(f"\nStatistics:")
            print(f"  Total tokens: {stats['total_tokens']}")
            print(f"  Average chunk: {stats['avg_chunk_tokens']:.0f} tokens")
            print(f"  Embedding model: {stats['embedding_model']}")
            print(f"  Chunks by type: {stats['chunks_by_type']}")
        
        # Test queries
        print("\n" + "-"*80)
        print("SAMPLE QUERIES")
        print("-"*80)
        
        test_queries = [
            "What certifications are required?",
            "When is the proposal due?",
            "What happens if we miss deadlines?",
            "What are the technical requirements?",
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = pipeline.query_tender("tender_001", query, k=2)
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result['section_type']}] Relevance: {result['similarity']:.2%}")
                print(f"     {result['text'][:70]}...")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# DEMO 6: Comparison - Token Counting Methods
# ============================================================================

def demo_token_counting():
    """Demonstrate token counting accuracy."""
    print("\n" + "="*80)
    print("DEMO 6: Token Counting Methods")
    print("="*80)
    
    sample_text = """
    The Requested Proposal (RFP) process is designed to ensure transparency and 
    fair competition among qualified vendors. All submissions must adhere strictly 
    to the specified format and timeline requirements outlined in this document.
    """
    
    chunker = TextChunker()
    
    # Character-based estimation
    char_estimate = int(len(sample_text) / 4.0)
    
    print(f"\nText length: {len(sample_text)} characters")
    print(f"Character-based estimate: ~{char_estimate} tokens")
    
    # Try tiktoken if available
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        actual = len(enc.encode(sample_text))
        print(f"Tiktoken actual count: {actual} tokens")
        print(f"Estimation accuracy: {100 * char_estimate / actual:.1f}%")
    except ImportError:
        print("(tiktoken not available for exact counting)")


# ============================================================================
# MAIN: Run all demos
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("STEP-5 & STEP-6 DEMO: Advanced Chunking and Embedding")
    print("="*80)
    
    demos = [
        ("Section Detection", demo_section_detection),
        ("Text Chunking", demo_text_chunking),
        ("Embeddings (Local)", demo_embeddings_local),
        ("FAISS Indexing", demo_faiss_indexing),
        ("Complete Pipeline", demo_complete_pipeline),
        ("Token Counting", demo_token_counting),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  7. Run all demos")
    
    try:
        choice = input("\nSelect demo (1-7): ").strip()
        
        if choice == "7":
            for name, demo_func in demos:
                try:
                    demo_func()
                except Exception as e:
                    print(f"\n✗ {name} demo failed: {e}")
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(demos):
                demos[idx][1]()
            else:
                print("Invalid selection")
    
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("Demo complete!")
    print("="*80 + "\n")
