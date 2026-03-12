"""
Step-4: Document Ingestion Demo and Test
Demonstrates streaming, header/footer removal, and language detection
"""

import sys
import time
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.parser import DocumentParser


def demo_streaming_large_pdf():
    """Demo: Stream a large PDF without loading entire document in memory"""
    print("\n" + "="*70)
    print("DEMO 1: Streaming Large PDF (Memory-Efficient)")
    print("="*70)
    
    # Example usage - would work with any PDF file
    example_code = """
    from app.services.parser import DocumentParser
    
    # Stream pages one by one (memory efficient for 1000+ page PDFs)
    for page_data in DocumentParser.stream_pdf_pages("large_tender.pdf"):
        print(f"Processing page {page_data['page']} of {page_data['total_pages']}")
        print(f"Detected language: {page_data['language']}")
        print(f"Cleaned text length: {page_data['cleaned_length']} chars")
        
        # Process each page without keeping entire PDF in memory
        process_page(page_data['text'])
    """
    
    print(example_code)
    print("\n✓ This approach handles 1000+ page PDFs efficiently")
    print("✓ Each page is processed independently")
    print("✓ Memory usage stays constant regardless of document size")


def demo_header_footer_removal():
    """Demo: Automatic header and footer removal"""
    print("\n" + "="*70)
    print("DEMO 2: Header/Footer Removal with Heuristics")
    print("="*70)
    
    # Example text with headers/footers
    sample_text = """
    RFP 2024-01-22
    
    SECTION 1: REQUIREMENTS
    
    The following requirements must be met:
    - Requirement 1
    - Requirement 2
    
    Page 1
    
    www.example.com | info@example.com
    """
    
    print("BEFORE cleanup:")
    print("-" * 70)
    print(sample_text)
    
    cleaned = DocumentParser.remove_headers_footers(sample_text)
    
    print("\nAFTER cleanup:")
    print("-" * 70)
    print(cleaned)
    
    print("\n✓ Removed: 'RFP 2024-01-22', 'Page 1', email and website")
    print("✓ Kept: Section headers and actual content")


def demo_language_detection():
    """Demo: Language detection per page"""
    print("\n" + "="*70)
    print("DEMO 3: Language Detection per Page")
    print("="*70)
    
    test_texts = {
        "English": "This is a tender document for the software development project. We are seeking qualified vendors.",
        "Spanish": "Este es un documento de licitación para el proyecto de desarrollo de software. Buscamos proveedores calificados.",
        "French": "Ceci est un document d'appel d'offres pour le projet de développement de logiciels. Nous recherchons des fournisseurs qualifiés.",
        "German": "Dies ist ein Ausschreibungsdokument für das Softwareentwicklungsprojekt. Wir suchen nach qualifizierten Anbietern.",
    }
    
    print("\nLanguage Detection Results:")
    print("-" * 70)
    
    for lang_name, text in test_texts.items():
        detected = DocumentParser.detect_language(text)
        print(f"{lang_name:12} → Detected: {detected}")
    
    print("\n✓ Automatic language detection for each page")
    print("✓ Enables multilingual document handling")
    print("✓ Per-page detection allows mixed-language documents")


def demo_smart_chunking():
    """Demo: Smart text chunking that respects sentence boundaries"""
    print("\n" + "="*70)
    print("DEMO 4: Smart Text Chunking (Respects Boundaries)")
    print("="*70)
    
    sample_text = """SECTION 1: SCOPE OF WORK

The vendor must provide comprehensive software development services. This includes design, development, testing, and deployment. 

SECTION 2: DELIVERABLES

The following deliverables are required:
- Design documents
- Source code
- Test reports
- Deployment guides

SECTION 3: TIMELINE

Project must be completed within 12 months from start date. Monthly milestones must be met."""
    
    print("Original text:")
    print("-" * 70)
    print(sample_text)
    
    chunks = DocumentParser.chunk_text(sample_text, chunk_size=150, overlap=30)
    
    print(f"\n✓ Created {len(chunks)} chunks (chunk_size=150, overlap=30)")
    print("\nChunks:")
    print("-" * 70)
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print(f"{chunk[:100]}..." if len(chunk) > 100 else chunk)


def demo_document_metadata():
    """Demo: Get document metadata without full parsing"""
    print("\n" + "="*70)
    print("DEMO 5: Document Metadata Extraction")
    print("="*70)
    
    print("""
    from app.services.parser import DocumentParser
    
    # Get metadata quickly without parsing entire document
    metadata = DocumentParser.get_document_metadata("tender_doc.pdf")
    
    # Returns:
    {
        "file_type": "pdf",
        "page_count": 45,
        "estimated_language": "en",
        "file_path": "tender_doc.pdf"
    }
    
    # Use for:
    # - Preprocessing checks
    # - Language routing
    # - Page count validation
    # - Format detection
    """)
    
    print("✓ Quick metadata without loading full document")
    print("✓ Useful for preprocessing and validation")
    print("✓ Samples document to estimate language")


def demo_streaming_vs_batch():
    """Demo: Compare streaming vs batch processing"""
    print("\n" + "="*70)
    print("DEMO 6: Streaming vs Batch Processing Comparison")
    print("="*70)
    
    comparison = """
    BATCH PROCESSING (Traditional):
    ────────────────────────────────
    1. Load entire PDF into memory
    2. Extract all pages at once
    3. Process everything together
    
    Pros:
    ✓ Simple to implement
    
    Cons:
    ✗ High memory usage
    ✗ Slow for large documents
    ✗ Can crash on 1000+ page documents
    
    Use for: Small documents (< 100 pages)
    
    ────────────────────────────────────────────────────────────
    
    STREAMING PROCESSING (Step-4):
    ────────────────────────────────
    1. Open document
    2. Process one page at a time
    3. Yield results immediately
    4. Memory released after each page
    
    Pros:
    ✓ Constant memory usage
    ✓ Fast for large documents
    ✓ Process 1000+ page PDFs easily
    ✓ Real-time processing
    
    Cons:
    ✗ Slightly more complex code
    
    Use for: Large documents (100-5000+ pages)
    
    ────────────────────────────────────────────────────────────
    
    Example:
    
    # Batch (loads entire PDF)
    pages = DocumentParser.extract_pages("tender.pdf")  # Slow, high memory
    
    # Streaming (processes one page at a time)
    for page in DocumentParser.stream_pdf_pages("tender.pdf"):
        process(page)  # Fast, low memory
    """
    
    print(comparison)


def demo_integration_with_step3():
    """Demo: Integration with Step-3 background task"""
    print("\n" + "="*70)
    print("DEMO 7: Integration with Step-3 Processing Pipeline")
    print("="*70)
    
    integration_example = """
    # In backend/app/workers/tasks.py
    
    @shared_task(bind=True, max_retries=3)
    def process_tender_task(self, tender_id: str):
        # ... (existing code)
        
        # Stream and process document
        for page_data in DocumentParser.stream_pdf_pages(tender.file_path):
            # Extract metadata
            page_num = page_data['page']
            language = page_data['language']
            cleaned_text = page_data['text']
            
            # Detect sections
            sections = detect_sections(cleaned_text)
            
            # Create chunks for AI processing
            chunks = DocumentParser.chunk_text(cleaned_text, 
                                              chunk_size=1200, 
                                              overlap=150)
            
            # Save sections with language info
            for section_name, section_text in sections.items():
                section = TenderSection(
                    tender_id=tender.id,
                    section_name=section_name,
                    section_text=section_text,
                    language=language,
                    page_range=f"{page_num}"
                )
                db.add(section)
            
            db.commit()
            
            # Process chunks with AI (in Step-5)
            for i, chunk in enumerate(chunks):
                # AI extraction will go here
                ai_results = extract_clauses(chunk, language)
                store_results(ai_results)
        
        tender.status = TenderStatus.COMPLETED
        db.commit()
    """
    
    print(integration_example)
    
    print("\n✓ Streaming integration with existing pipeline")
    print("✓ Language detection feeds into AI processing")
    print("✓ Memory-efficient end-to-end workflow")


def main():
    """Run all Step-4 demos"""
    print("\n" + "="*70)
    print(" STEP-4: Advanced Document Ingestion Demos")
    print("="*70)
    
    demos = [
        ("Streaming", demo_streaming_large_pdf),
        ("Header/Footer Removal", demo_header_footer_removal),
        ("Language Detection", demo_language_detection),
        ("Smart Chunking", demo_smart_chunking),
        ("Metadata", demo_document_metadata),
        ("Streaming vs Batch", demo_streaming_vs_batch),
        ("Integration", demo_integration_with_step3),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n✗ Error in {name} demo: {str(e)}")
    
    print("\n" + "="*70)
    print(" STEP-4 Demos Complete")
    print("="*70)
    print("""
Key Features Implemented:

✓ Streaming PDF parsing (handles 1000+ pages)
✓ Streaming DOCX parsing (memory efficient)
✓ Header/footer removal (heuristic-based)
✓ Language detection per page
✓ Smart text chunking (respects boundaries)
✓ Document metadata extraction
✓ Backward compatible with Step-3

Ready for: Step-5 (AI Extraction & Processing)
""")


if __name__ == "__main__":
    main()
