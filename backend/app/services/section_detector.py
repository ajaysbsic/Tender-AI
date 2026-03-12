"""
Section Detector: Identify and classify tender document sections.

Detects key sections like Eligibility, Technical Requirements, Commercial Requirements,
Deadlines, and Penalties using regex patterns and lightweight LLM classification.
"""

import re
from typing import List, Dict, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SectionType(str, Enum):
    """Classification of tender document sections"""
    ELIGIBILITY = "eligibility"
    TECHNICAL_REQUIREMENTS = "technical_requirements"
    COMMERCIAL_REQUIREMENTS = "commercial_requirements"
    DEADLINES = "deadlines"
    PENALTIES = "penalties"
    EVALUATION_CRITERIA = "evaluation_criteria"
    SCOPE = "scope"
    DELIVERABLES = "deliverables"
    OTHER = "other"


class SectionDetector:
    """Detect and classify tender document sections using regex patterns and heuristics."""
    
    # Regex patterns for different section types
    SECTION_PATTERNS = {
        SectionType.ELIGIBILITY: [
            r"(?i)eligibility\s+(criteria|requirements|standards|conditions)",
            r"(?i)(company|bidder|vendor)\s+eligibility",
            r"(?i)to\s+be\s+eligible",
            r"(?i)qualification\s+requirements",
            r"(?i)bidder\s+qualification",
            r"(?i)required\s+capabilities?",
            r"(?i)(minimum|mandatory)\s+(experience|credentials|certifications)",
        ],
        SectionType.TECHNICAL_REQUIREMENTS: [
            r"(?i)technical\s+(requirements|specifications|standards)",
            r"(?i)specification\s+requirements",
            r"(?i)system\s+requirements",
            r"(?i)technical\s+compliance",
            r"(?i)infrastructure\s+requirements",
            r"(?i)technology\s+stack",
            r"(?i)software\s+(requirements|specifications)",
            r"(?i)performance\s+(requirements|criteria)",
        ],
        SectionType.COMMERCIAL_REQUIREMENTS: [
            r"(?i)commercial\s+(requirements|terms|conditions)",
            r"(?i)commercial\s+proposal",
            r"(?i)payment\s+(terms|schedule|method)",
            r"(?i)pricing\s+(requirements|structure)",
            r"(?i)financial\s+(terms|requirements|conditions)",
            r"(?i)contract\s+(terms|conditions)",
            r"(?i)warranty\s+(requirements|terms)",
            r"(?i)insurance\s+(requirements|coverage)",
        ],
        SectionType.DEADLINES: [
            r"(?i)deadline|due\s+date|submission\s+date",
            r"(?i)date\s+and\s+time",
            r"(?i)proposal\s+due",
            r"(?i)final\s+submission",
            r"(?i)\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # Date pattern
            r"(?i)by\s+\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)",
        ],
        SectionType.PENALTIES: [
            r"(?i)penalty|penalties|penalti",
            r"(?i)late\s+(fees|charges|penalties)",
            r"(?i)non-compliance\s+penalties",
            r"(?i)liquidated\s+damages",
            r"(?i)performance\s+penalty",
            r"(?i)delay\s+(charges|penalties)",
            r"(?i)breach\s+(penalties|consequences)",
        ],
        SectionType.EVALUATION_CRITERIA: [
            r"(?i)evaluation\s+(criteria|process)",
            r"(?i)scoring\s+(methodology|criteria)",
            r"(?i)proposal\s+evaluation",
            r"(?i)bid\s+evaluation",
            r"(?i)weightage\s+distribution",
            r"(?i)evaluation\s+points",
        ],
        SectionType.SCOPE: [
            r"(?i)scope\s+of\s+work",
            r"(?i)scope\s+(description|overview)",
            r"(?i)work\s+description",
            r"(?i)project\s+scope",
            r"(?i)services\s+to\s+be\s+(provided|delivered)",
        ],
        SectionType.DELIVERABLES: [
            r"(?i)deliverables?|deliverable\s+items",
            r"(?i)outputs?|output\s+deliverables",
            r"(?i)milestones?\s+(and\s+deliverables)?",
            r"(?i)timeline\s+and\s+deliverables",
            r"(?i)what\s+(must\s+be\s+)?delivered",
        ],
    }
    
    # Keywords that help identify section types
    SECTION_KEYWORDS = {
        SectionType.ELIGIBILITY: {
            "require", "qualify", "certified", "experience", "credentials",
            "minimum", "mandatory", "must", "necessary", "eligible", "eligibility"
        },
        SectionType.TECHNICAL_REQUIREMENTS: {
            "technical", "system", "infrastructure", "software", "hardware",
            "performance", "specification", "compatibility", "integration"
        },
        SectionType.COMMERCIAL_REQUIREMENTS: {
            "payment", "pricing", "cost", "financial", "commercial", "warranty",
            "insurance", "contract", "terms", "conditions", "rates", "fees"
        },
        SectionType.DEADLINES: {
            "deadline", "due", "date", "time", "submission", "close", "open",
            "schedule", "timeline", "by", "until", "before"
        },
        SectionType.PENALTIES: {
            "penalty", "penalties", "liquidated", "damages", "breach", "delay",
            "late", "charges", "non-compliance", "default", "failure"
        },
    }
    
    # Section header patterns (generic)
    HEADER_PATTERN = re.compile(
        r"^(\d{1,2}\.?\d*\.?\d*\s+|Section\s+\d+[A-Z]?:|[A-Z\d]{2,}\s*:\s*)"
        r"([A-Z][A-Za-z0-9\s\-&().,/]*?)(?:\s*$|\s*-\s*)",
        re.MULTILINE | re.IGNORECASE
    )
    
    @staticmethod
    def detect_sections(text: str) -> List[Dict]:
        """
        Detect sections in text and classify them.
        
        Returns:
            List of dicts with: {start_pos, end_pos, header, content, section_type, confidence}
        """
        sections = []
        
        # Find all potential section headers
        headers = list(SectionDetector.HEADER_PATTERN.finditer(text))
        
        if not headers:
            # No structured headers found, treat entire text as one section
            section_type, confidence = SectionDetector._classify_section(text[:500], text)
            return [{
                'start_pos': 0,
                'end_pos': len(text),
                'header': 'Document Content',
                'content': text,
                'section_type': section_type,
                'confidence': confidence,
                'page': 1
            }]
        
        # Extract sections between headers
        for i, header_match in enumerate(headers):
            start_pos = header_match.start()
            header_text = header_match.group(2).strip()
            
            # Find end position (start of next header or end of document)
            end_pos = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            
            # Extract section content
            content = text[header_match.end():end_pos].strip()
            
            if len(content) > 50:  # Only include sections with meaningful content
                # Classify the section
                section_type, confidence = SectionDetector._classify_section(header_text, content)
                
                sections.append({
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'header': header_text,
                    'content': content,
                    'section_type': section_type,
                    'confidence': confidence,
                    'page': 1  # Will be updated by caller
                })
        
        return sections
    
    @staticmethod
    def _classify_section(header: str, content: str) -> Tuple[SectionType, float]:
        """
        Classify a section based on header and content using regex patterns.
        
        Returns:
            Tuple of (section_type, confidence_score)
        """
        combined_text = f"{header} {content[:1000]}".lower()
        scores = {section_type: 0.0 for section_type in SectionType}
        
        # Score based on regex patterns
        for section_type, patterns in SectionDetector.SECTION_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    matches += 1
            
            if matches > 0:
                scores[section_type] = min(1.0, matches * 0.3)  # Each match adds 0.3
        
        # Score based on keywords
        header_lower = header.lower()
        content_lower = content.lower()[:500]
        
        for section_type, keywords in SectionDetector.SECTION_KEYWORDS.items():
            keyword_count = sum(
                1 for keyword in keywords
                if keyword in header_lower or keyword in content_lower
            )
            keyword_score = min(1.0, keyword_count * 0.15)
            scores[section_type] = min(1.0, scores[section_type] + keyword_score)
        
        # Determine best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        if best_score == 0:
            return SectionType.OTHER, 0.0
        
        return best_type, min(0.99, best_score)
    
    @staticmethod
    def classify_with_llm(
        header: str,
        content: str,
        llm_classifier: Optional[callable] = None
    ) -> Tuple[SectionType, float]:
        """
        Classify a section using regex first, then optionally with LLM for refinement.
        
        Args:
            header: Section header text
            content: Section content (first 1000 chars)
            llm_classifier: Optional LLM classification function that returns (type, confidence)
            
        Returns:
            Tuple of (section_type, confidence_score)
        """
        # First pass: regex-based classification
        regex_type, regex_confidence = SectionDetector._classify_section(header, content)
        
        # If confidence is high enough, return early
        if regex_confidence > 0.7:
            return regex_type, regex_confidence
        
        # Second pass: LLM-based classification if provided and regex confidence is low
        if llm_classifier and regex_confidence < 0.5:
            try:
                llm_type, llm_confidence = llm_classifier(header, content)
                return llm_type, llm_confidence
            except Exception as e:
                logger.warning(f"LLM classification failed, using regex result: {e}")
                return regex_type, regex_confidence
        
        return regex_type, regex_confidence
    
    @staticmethod
    def extract_key_sections(
        text: str,
        section_types: Optional[List[SectionType]] = None
    ) -> Dict[SectionType, str]:
        """
        Extract specific section types from text.
        
        Args:
            text: Document text
            section_types: List of section types to extract (default: all key types)
            
        Returns:
            Dictionary mapping section_type to extracted text
        """
        if section_types is None:
            section_types = [
                SectionType.ELIGIBILITY,
                SectionType.TECHNICAL_REQUIREMENTS,
                SectionType.COMMERCIAL_REQUIREMENTS,
                SectionType.DEADLINES,
                SectionType.PENALTIES
            ]
        
        sections = SectionDetector.detect_sections(text)
        extracted = {st: "" for st in section_types}
        
        for section in sections:
            if section['section_type'] in section_types:
                extracted[section['section_type']] += f"\n\n{section['header']}\n{section['content']}"
        
        return {k: v.strip() for k, v in extracted.items() if v.strip()}
    
    @staticmethod
    def get_section_statistics(sections: List[Dict]) -> Dict:
        """
        Get statistics about detected sections.
        
        Returns:
            Dictionary with section type counts and confidence stats
        """
        stats = {
            'total_sections': len(sections),
            'section_types': {},
            'avg_confidence': 0.0,
            'confidence_by_type': {},
        }
        
        confidences = []
        type_counts = {}
        type_confidences = {}
        
        for section in sections:
            sec_type = section['section_type']
            confidence = section['confidence']
            
            type_counts[sec_type] = type_counts.get(sec_type, 0) + 1
            
            if sec_type not in type_confidences:
                type_confidences[sec_type] = []
            type_confidences[sec_type].append(confidence)
            
            confidences.append(confidence)
        
        stats['section_types'] = type_counts
        stats['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0
        stats['confidence_by_type'] = {
            st: sum(confs) / len(confs) for st, confs in type_confidences.items()
        }
        
        return stats
