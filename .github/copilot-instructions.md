# Tender-AI Copilot Instructions

## Project Overview
Tender-AI is an AI-powered analyzer for tender and RFP documents that helps SMEs quickly evaluate bid opportunities. The system extracts **eligibility requirements, scope requirements, risks, critical deadlines, and effort scores** to enable rapid bid/no-bid decisions.

## Core Architecture Pattern
The system likely follows a **document-analysis pipeline**:
1. **Document Ingestion** - Parse PDF/Word/text tenders
2. **Content Extraction** - Identify key sections (scope, deliverables, requirements, deadlines)
3. **AI Analysis** - Use LLM to extract structured data with domain context
4. **Scoring & Evaluation** - Calculate effort scores and risk ratings
5. **Output** - Generate actionable bid recommendation summary

## Key Components to Establish
- **Document Parser** - Handle multiple formats (PDF, DOCX, TXT)
- **Extraction Engine** - LLM-based structured extraction (use prompt templates)
- **Data Models** - Define `Tender`, `Requirement`, `Risk`, `Deadline`, `Score` entities
- **API Service** - RESTful endpoints for document upload and analysis
- **Frontend** - Dashboard showing extraction results and bid recommendation

## AI Integration Guidelines
- Use **prompt templates** (store in dedicated directory, not hardcoded) for consistency
- Implement **retry logic** for LLM calls with exponential backoff
- Cache extraction results to avoid re-processing identical documents
- Structure outputs as **JSON schemas** for type safety and downstream processing
- Log all LLM calls with inputs/outputs for debugging and cost tracking

## Development Workflow
- **Testing**: Focus on extraction accuracy tests; use synthetic tender documents as fixtures
- **Debugging**: Compare raw LLM outputs vs. parsed results when accuracy issues occur
- **Dependencies**: Likely includes PDF parser (PyPDF2/pdfplumber), LLM client (OpenAI/Anthropic), FastAPI/Flask

## Code Organization (Recommended)
```
src/
  ├── parsers/          # Document format handlers
  ├── extractors/       # AI extraction logic
  ├── models/           # Data classes (Tender, Requirement, etc.)
  ├── prompts/          # LLM prompt templates
  ├── scoring/          # Effort/risk scoring logic
  └── api/              # REST endpoints
tests/
  ├── fixtures/         # Sample tender documents
  └── test_extractors.py
```

## Key Decision Points
- **LLM Choice**: Use Claude for complex reasoning; GPT for cost efficiency
- **Chunking Strategy**: For large documents, split by section to maintain context
- **Error Handling**: Gracefully degrade when sections missing; flag low-confidence extractions
- **Data Privacy**: Ensure tenders can be processed locally or with enterprise LLM endpoints

## When Implementing Features
1. Start with **data model** (what data do we extract?)
2. Then **prompts** (how do we extract it reliably?)
3. Finally **integration** (how does it fit the pipeline?)
