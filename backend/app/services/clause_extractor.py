"""
Clause Extractor - Step-7 Pipeline

Extracts clauses from tender documents with LLM-based analysis.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.services.ai_schemas import (
    ClauseExtractionOutput,
    ExtractedClause,
    ClauseRequirement,
    ExtractionMetadata,
)
from app.services.llm_client import LLMClient, LLMProvider, LLMModel, get_default_llm_client
from app.services.prompts import PromptManager, get_system_prompt_for_analyzer
from app.services.chunker import TextChunker
from app.services.section_detector import SectionDetector

logger = logging.getLogger(__name__)


class ClauseExtractor:
    """
    Extracts clauses from tender documents using LLM.
    
    Process:
    1. Detect sections in document
    2. Chunk text appropriately
    3. Use LLM to extract clauses and requirements
    4. Structure output as JSON
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize clause extractor"""
        self.llm = llm_client or get_default_llm_client()
        self.chunker = TextChunker()
        self.section_detector = SectionDetector()
        self.extraction_start_time = None
        
    def extract_clauses(
        self,
        tender_id: str,
        full_text: str,
        model: Optional[LLMModel] = None
    ) -> ClauseExtractionOutput:
        """
        Extract all clauses from tender document.
        
        Args:
            tender_id: Tender identifier
            full_text: Complete tender text
            model: Optional specific model to use
            
        Returns:
            ClauseExtractionOutput with extracted clauses
        """
        self.extraction_start_time = datetime.now()
        
        try:
            logger.info(f"Starting clause extraction for tender {tender_id}")
            
            # Detect sections to focus extraction
            sections = self._detect_key_sections(full_text)
            logger.info(f"Detected {len(sections)} key sections")
            
            # Extract clauses from each section
            all_clauses: List[ExtractedClause] = []
            total_confidence = 0.0
            
            for section_name, section_text in sections.items():
                logger.info(f"Extracting clauses from section: {section_name}")
                
                section_clauses = self._extract_clauses_from_section(
                    section_name=section_name,
                    section_text=section_text,
                    model=model
                )
                
                all_clauses.extend(section_clauses)
                total_confidence += sum(c.requirements[0].metric for c in section_clauses if c.requirements)
            
            # Calculate average confidence
            avg_confidence = (
                total_confidence / len(all_clauses)
                if all_clauses
                else 0.5
            )
            
            logger.info(
                f"Extracted {len(all_clauses)} clauses "
                f"with average confidence {avg_confidence:.2f}"
            )
            
            # Build output
            output = ClauseExtractionOutput(
                tender_id=tender_id,
                total_clauses_found=len(all_clauses),
                clauses=all_clauses,
                extraction_confidence=min(avg_confidence, 1.0),
                extraction_notes=[
                    f"Analyzed {len(sections)} major sections",
                    f"Extracted {len(all_clauses)} distinct clauses",
                    "Clause-level requirement analysis performed",
                    "Clause dependencies identified",
                ]
            )
            
            return output
        
        except Exception as e:
            logger.error(f"Error extracting clauses: {e}", exc_info=True)
            raise
    
    def _detect_key_sections(self, text: str) -> Dict[str, str]:
        """Detect and extract key sections from tender"""
        sections = {}
        
        # Use section detector to identify sections
        section_types = [
            "scope",
            "technical",
            "eligibility",
            "deliverables",
            "commercial",
            "evaluation_criteria",
            "deadlines",
            "penalties"
        ]
        
        for section_type in section_types:
            # Find sections of this type in the text
            # This is a simplified approach - in production, use section_detector
            if section_type in text.lower():
                sections[section_type] = self._extract_section_text(text, section_type)
        
        return sections if sections else {"full_document": text[:10000]}  # Fallback
    
    def _extract_section_text(self, text: str, section_name: str) -> str:
        """Extract section text from full document"""
        # Simplified extraction - in production, use more sophisticated approach
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
            elif in_section and line.strip() and line[0].isupper():
                break
            elif in_section:
                section_lines.append(line)
        
        return '\n'.join(section_lines[:200])  # Limit to first 200 lines
    
    def _extract_clauses_from_section(
        self,
        section_name: str,
        section_text: str,
        model: Optional[LLMModel] = None
    ) -> List[ExtractedClause]:
        """Extract clauses from a single section"""
        
        try:
            # Prepare prompt
            prompt = PromptManager.get_clause_extraction_prompt(section_text)
            
            # Get LLM response
            if model:
                # Use specific model
                original_model = self.llm.config.model
                self.llm.config.model = model
            
            logger.info(f"Sending clause extraction to LLM ({section_name})")
            response = self.llm.generate_json(prompt, ClauseExtractionOutput)
            
            if model:
                self.llm.config.model = original_model
            
            # Extract clauses from response
            clauses: List[ExtractedClause] = []
            
            if isinstance(response, dict) and 'clauses' in response:
                for clause_data in response['clauses']:
                    try:
                        clause = ExtractedClause(**clause_data)
                        clauses.append(clause)
                    except Exception as e:
                        logger.warning(f"Failed to parse clause: {e}")
            
            logger.info(f"Extracted {len(clauses)} clauses from {section_name}")
            return clauses
        
        except Exception as e:
            logger.error(f"Error extracting from section {section_name}: {e}")
            return []
    
    def extract_single_clause(
        self,
        clause_number: str,
        clause_text: str
    ) -> Optional[ExtractedClause]:
        """
        Extract information from a single clause.
        
        Args:
            clause_number: Clause identifier (e.g., "2.3.1")
            clause_text: Full clause text
            
        Returns:
            Extracted clause or None if extraction fails
        """
        try:
            logger.info(f"Extracting single clause {clause_number}")
            
            # Create focused prompt for single clause
            prompt = f"""Analyze this single clause and extract its requirements:

CLAUSE {clause_number}:
{clause_text}

Extract:
1. Clause title
2. All requirements (mandatory/recommended/optional)
3. Key terms and keywords
4. Whether penalties apply
5. Dependencies on other clauses

Return as JSON matching ClauseExtractionOutput schema."""
            
            response = self.llm.generate_json(prompt, ClauseExtractionOutput)
            
            if isinstance(response, dict) and 'clauses' in response and response['clauses']:
                return ExtractedClause(**response['clauses'][0])
            
            return None
        
        except Exception as e:
            logger.error(f"Error extracting clause {clause_number}: {e}")
            return None
    
    def batch_extract_clauses(
        self,
        tender_id: str,
        clause_list: List[tuple[str, str]]  # List of (clause_number, clause_text)
    ) -> List[ExtractedClause]:
        """
        Extract multiple clauses in batch.
        
        Args:
            tender_id: Tender identifier
            clause_list: List of (clause_number, clause_text) tuples
            
        Returns:
            List of extracted clauses
        """
        logger.info(f"Batch extracting {len(clause_list)} clauses")
        
        results = []
        for clause_num, clause_text in clause_list:
            try:
                clause = self.extract_single_clause(clause_num, clause_text)
                if clause:
                    results.append(clause)
            except Exception as e:
                logger.warning(f"Failed to extract clause {clause_num}: {e}")
        
        return results
    
    def extract_from_chunks(
        self,
        tender_id: str,
        chunks: List[str]
    ) -> ClauseExtractionOutput:
        """
        Extract clauses from pre-chunked text.
        
        Args:
            tender_id: Tender identifier
            chunks: List of text chunks (from Step-5 chunker)
            
        Returns:
            Clause extraction result
        """
        logger.info(f"Extracting clauses from {len(chunks)} chunks")
        
        # Combine chunks for analysis
        combined_text = "\n\n".join(chunks)
        
        # Extract clauses
        return self.extract_clauses(tender_id, combined_text)
    
    def get_extraction_metadata(self) -> ExtractionMetadata:
        """Get metadata about extraction process"""
        elapsed = (
            (datetime.now() - self.extraction_start_time).total_seconds()
            if self.extraction_start_time
            else 0.0
        )
        
        return ExtractionMetadata(
            extraction_timestamp=datetime.now().isoformat(),
            llm_model_used=self.llm.model_name,
            llm_tokens_used=0,  # Would need to track in LLMClient
            processing_time_seconds=elapsed,
            extraction_version="1.0"
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def extract_clauses_from_text(tender_id: str, text: str) -> ClauseExtractionOutput:
    """Convenience function to extract clauses from text"""
    extractor = ClauseExtractor()
    return extractor.extract_clauses(tender_id, text)


def extract_clauses_from_chunks(tender_id: str, chunks: List[str]) -> ClauseExtractionOutput:
    """Convenience function to extract clauses from chunks"""
    extractor = ClauseExtractor()
    return extractor.extract_from_chunks(tender_id, chunks)
