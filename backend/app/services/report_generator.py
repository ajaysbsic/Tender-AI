"""
Report Generator - Step-9

Generates professional PDF reports with business-friendly language.
Converts technical scores into actionable insights.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from app.services.scoring_models import (
    TenderScore,
    EligibilityCategory,
    RiskCategory,
    EffortCategory,
)

logger = logging.getLogger(__name__)


class BusinessLanguageTranslator:
    """Converts technical scores to business-friendly language"""
    
    @staticmethod
    def eligibility_verdict(score: float, category: str) -> Dict[str, str]:
        """Translate eligibility score to business language"""
        
        verdict_map = {
            EligibilityCategory.ELIGIBLE.value: {
                "title": "✓ ELIGIBLE",
                "headline": "Company Meets All Requirements",
                "summary": f"Excellent fit. The company meets {score:.0f}% of requirements, well above the 90% threshold needed for eligibility.",
                "action": "Proceed with confidence.",
            },
            EligibilityCategory.PARTIALLY_ELIGIBLE.value: {
                "title": "⚠ PARTIALLY ELIGIBLE",
                "headline": "Company Meets Most Requirements",
                "summary": f"Viable option with gaps. The company meets {score:.0f}% of requirements, which is above the 70% minimum for consideration but below the 90% ideal.",
                "action": "Proceed with caution. Address identified gaps during negotiation.",
            },
            EligibilityCategory.NOT_ELIGIBLE.value: {
                "title": "✗ NOT ELIGIBLE",
                "headline": "Company Does Not Meet Key Requirements",
                "summary": f"Not recommended at this time. The company meets only {score:.0f}% of requirements, falling short of the 70% minimum threshold.",
                "action": "Consider alternative vendors or request company to address critical gaps.",
            },
        }
        
        return verdict_map.get(category, verdict_map[EligibilityCategory.NOT_ELIGIBLE.value])
    
    @staticmethod
    def risk_verdict(score: float, category: str, deal_breakers: List[str]) -> Dict[str, str]:
        """Translate risk score to business language"""
        
        verdict_map = {
            RiskCategory.LOW.value: {
                "title": "✓ LOW RISK",
                "headline": "Project Risk is Manageable",
                "summary": f"Good risk profile (score: {score:.0f}/100). The identified risks are minor and typical for projects of this type.",
                "action": "No significant risk mitigation required.",
            },
            RiskCategory.MEDIUM.value: {
                "title": "⚠ MEDIUM RISK",
                "headline": "Project Has Notable Risks",
                "summary": f"Moderate risk profile (score: {score:.0f}/100). The project has several risks that require attention and mitigation strategies.",
                "action": "Develop risk mitigation plan before proceeding.",
            },
            RiskCategory.HIGH.value: {
                "title": "🚨 HIGH RISK",
                "headline": "Significant Project Risks Identified",
                "summary": f"Concerning risk profile (score: {score:.0f}/100). Multiple high-severity risks have been identified.",
                "action": "Strongly recommend comprehensive risk mitigation or reconsideration.",
            },
        }
        
        base = verdict_map.get(category, verdict_map[RiskCategory.MEDIUM.value])
        
        if deal_breakers:
            base["summary"] += f" {len(deal_breakers)} deal-breaker risk(s) identified: " + ", ".join(deal_breakers[:3])
            base["action"] = "Deal-breaker risks must be resolved before proceeding."
        
        return base
    
    @staticmethod
    def effort_verdict(score: float, category: str, hours: float, days: int) -> Dict[str, str]:
        """Translate effort score to business language"""
        
        verdict_map = {
            EffortCategory.LOW.value: {
                "title": "✓ LOW EFFORT",
                "headline": "Project Scope is Manageable",
                "summary": f"Manageable effort (score: {score:.0f}/100). Approximately {hours:.0f} hours over {days} days with reasonable resource requirements.",
                "action": "Standard project timeline and resource allocation recommended.",
            },
            EffortCategory.MEDIUM.value: {
                "title": "⚠ MEDIUM EFFORT",
                "headline": "Project Requires Significant Resources",
                "summary": f"Substantial effort (score: {score:.0f}/100). Approximately {hours:.0f} hours over {days} days will require dedicated team and planning.",
                "action": "Ensure resource availability and project scheduling capacity.",
            },
            EffortCategory.HIGH.value: {
                "title": "🚨 HIGH EFFORT",
                "headline": "Project is Major Undertaking",
                "summary": f"Major effort (score: {score:.0f}/100). Approximately {hours:.0f} hours over {days} days represents significant commitment.",
                "action": "Verify team capacity and timeline feasibility before committing.",
            },
        }
        
        return verdict_map.get(category, verdict_map[EffortCategory.MEDIUM.value])
    
    @staticmethod
    def recommendation_explanation(recommendation: str, score: float) -> Dict[str, str]:
        """Translate bid recommendation to business language"""
        
        explanation_map = {
            "BID": {
                "title": "✓ RECOMMEND: BID",
                "headline": "Strong Candidate - Proceed with Bid",
                "summary": f"This is a strong opportunity (score: {score:.0f}/100). The company is well-positioned to win and successfully deliver on this tender.",
                "details": "Proceed with bid preparation. Focus on highlighting your unique strengths.",
            },
            "CONDITIONAL": {
                "title": "⚠ CONDITIONAL: REVIEW",
                "headline": "Viable but Requires Mitigation",
                "summary": f"This opportunity has mixed signals (score: {score:.0f}/100). Success depends on addressing identified concerns.",
                "details": "Carefully review critical items. Consider whether you can credibly address all gaps and risks.",
            },
            "NO_BID": {
                "title": "✗ RECOMMEND: NO BID",
                "headline": "Not Recommended at This Time",
                "summary": f"This opportunity does not align with your profile (score: {score:.0f}/100). Proceeding would be high-risk with low probability of success.",
                "details": "Focus resources on better-aligned opportunities.",
            },
        }
        
        return explanation_map.get(recommendation, explanation_map["CONDITIONAL"])


class ReportGenerator:
    """Generates professional PDF reports from tender scores"""
    
    def __init__(self):
        """Initialize report generator"""
        self.translator = BusinessLanguageTranslator()
        self.styles = self._setup_styles()
    
    def _setup_styles(self):
        """Setup ReportLab paragraph styles"""
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='TitleMain',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=HexColor('#1a1a1a'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHead',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold',
        ))
        
        styles.add(ParagraphStyle(
            name='SubSectionHead',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold',
        ))
        
        styles.add(ParagraphStyle(
            name='BodyText',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14,
        ))
        
        styles.add(ParagraphStyle(
            name='VerdictText',
            parent=styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=13,
            textColor=HexColor('#2c3e50'),
        ))
        
        styles.add(ParagraphStyle(
            name='ActionText',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=HexColor('#d35400'),
            fontName='Helvetica-Bold',
            spaceAfter=10,
        ))
        
        return styles
    
    def generate_pdf(self, tender_score: TenderScore, company_name: str = "Your Company") -> BytesIO:
        """Generate PDF report from tender score"""
        
        logger.info(f"Generating PDF report for {tender_score.tender_id}")
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        # Build content
        story = []
        
        # Title page
        story.extend(self._build_title_section(tender_score, company_name))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive summary
        story.extend(self._build_executive_summary(tender_score))
        story.append(PageBreak())
        
        # Detailed analysis
        story.extend(self._build_detailed_analysis(tender_score))
        story.append(PageBreak())
        
        # Clause verdicts
        story.extend(self._build_clause_verdicts(tender_score))
        story.append(PageBreak())
        
        # Risk and effort details
        story.extend(self._build_risk_details(tender_score))
        story.append(Spacer(1, 0.2*inch))
        story.extend(self._build_effort_details(tender_score))
        story.append(PageBreak())
        
        # Recommendations
        story.extend(self._build_recommendations(tender_score))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        logger.info(f"PDF report generated successfully for {tender_score.tender_id}")
        return buffer
    
    def _build_title_section(self, tender_score: TenderScore, company_name: str) -> List:
        """Build title page section"""
        
        story = []
        
        # Main title
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("TENDER EVALUATION REPORT", self.styles['TitleMain']))
        story.append(Spacer(1, 0.1*inch))
        
        # Tender ID
        story.append(Paragraph(f"Tender ID: {tender_score.tender_id}", self.styles['SubSectionHead']))
        story.append(Spacer(1, 0.2*inch))
        
        # Company name and date
        company_text = f"<b>Evaluating Company:</b> {company_name}"
        story.append(Paragraph(company_text, self.styles['BodyText']))
        
        date_text = f"<b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(date_text, self.styles['BodyText']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Overall recommendation box
        rec_data = self.translator.recommendation_explanation(
            tender_score.bid_recommendation,
            tender_score.overall_score
        )
        
        story.append(self._build_recommendation_box(rec_data, tender_score.overall_score))
        
        return story
    
    def _build_recommendation_box(self, rec_data: Dict[str, str], score: float) -> Table:
        """Build recommendation box"""
        
        # Color based on recommendation
        if "BID" in rec_data["title"]:
            bg_color = HexColor('#d5f4e6')
            text_color = HexColor('#27ae60')
        elif "CONDITIONAL" in rec_data["title"]:
            bg_color = HexColor('#fdebd0')
            text_color = HexColor('#d68910')
        else:
            bg_color = HexColor('#fadbd8')
            text_color = HexColor('#c0392b')
        
        content = [
            Paragraph(f"<font color='{text_color.hexval()}'><b>{rec_data['title']}</b></font>", self.styles['SubSectionHead']),
            Spacer(1, 0.1*inch),
            Paragraph(f"<b>{rec_data['headline']}</b>", self.styles['BodyText']),
            Paragraph(rec_data['summary'], self.styles['VerdictText']),
            Paragraph(f"<b>Action:</b> {rec_data['details']}", self.styles['ActionText']),
        ]
        
        table = Table(
            [[content]],
            colWidths=[7*inch],
        )
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BORDER', (0, 0), (-1, -1), 2, text_color),
            ('PADDING', (0, 0), (-1, -1), 0.3*inch),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return table
    
    def _build_executive_summary(self, tender_score: TenderScore) -> List:
        """Build executive summary section"""
        
        story = []
        
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHead']))
        story.append(Spacer(1, 0.1*inch))
        
        # Overall score
        summary_text = f"""
        <b>Overall Evaluation Score: {tender_score.overall_score:.1f}/100</b><br/><br/>
        This tender has been evaluated based on three key dimensions:
        """
        story.append(Paragraph(summary_text, self.styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))
        
        # Score summary table
        score_data = [
            ['Dimension', 'Score', 'Assessment'],
            [
                'Eligibility',
                f"{tender_score.eligibility.eligibility_score:.0f}%",
                tender_score.eligibility.category.value.replace('_', ' ').title(),
            ],
            [
                'Risk',
                f"{tender_score.risk.risk_score:.0f}/100",
                tender_score.risk.risk_category.value.title(),
            ],
            [
                'Effort',
                f"{tender_score.effort.effort_score:.0f}/100",
                tender_score.effort.effort_category.value.title(),
            ],
        ]
        
        table = Table(score_data, colWidths=[1.8*inch, 1.2*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#ecf0f1')]),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
        
        # Key findings
        story.append(Paragraph("<b>Key Findings:</b>", self.styles['SubSectionHead']))
        
        for strength in tender_score.strengths[:3]:
            story.append(Paragraph(f"✓ {strength}", self.styles['BodyText']))
        
        story.append(Spacer(1, 0.1*inch))
        
        for weakness in tender_score.weaknesses[:3]:
            story.append(Paragraph(f"⚠ {weakness}", self.styles['BodyText']))
        
        return story
    
    def _build_detailed_analysis(self, tender_score: TenderScore) -> List:
        """Build detailed analysis section"""
        
        story = []
        
        story.append(Paragraph("DETAILED ANALYSIS", self.styles['SectionHead']))
        story.append(Spacer(1, 0.1*inch))
        
        # Eligibility analysis
        elig_verdict = self.translator.eligibility_verdict(
            tender_score.eligibility.eligibility_score,
            tender_score.eligibility.category.value
        )
        
        story.append(Paragraph(f"<b>{elig_verdict['title']}</b>", self.styles['SubSectionHead']))
        story.append(Paragraph(f"<b>{elig_verdict['headline']}</b>", self.styles['BodyText']))
        story.append(Paragraph(elig_verdict['summary'], self.styles['VerdictText']))
        story.append(Paragraph(f"<b>Recommendation:</b> {elig_verdict['action']}", self.styles['ActionText']))
        story.append(Spacer(1, 0.2*inch))
        
        # Risk analysis
        risk_verdict = self.translator.risk_verdict(
            tender_score.risk.risk_score,
            tender_score.risk.risk_category.value,
            tender_score.risk.deal_breakers,
        )
        
        story.append(Paragraph(f"<b>{risk_verdict['title']}</b>", self.styles['SubSectionHead']))
        story.append(Paragraph(f"<b>{risk_verdict['headline']}</b>", self.styles['BodyText']))
        story.append(Paragraph(risk_verdict['summary'], self.styles['VerdictText']))
        story.append(Paragraph(f"<b>Recommendation:</b> {risk_verdict['action']}", self.styles['ActionText']))
        story.append(Spacer(1, 0.2*inch))
        
        # Effort analysis
        effort_verdict = self.translator.effort_verdict(
            tender_score.effort.effort_score,
            tender_score.effort.effort_category.value,
            tender_score.effort.metrics.total_hours,
            tender_score.effort.metrics.total_days,
        )
        
        story.append(Paragraph(f"<b>{effort_verdict['title']}</b>", self.styles['SubSectionHead']))
        story.append(Paragraph(f"<b>{effort_verdict['headline']}</b>", self.styles['BodyText']))
        story.append(Paragraph(effort_verdict['summary'], self.styles['VerdictText']))
        story.append(Paragraph(f"<b>Recommendation:</b> {effort_verdict['action']}", self.styles['ActionText']))
        
        return story
    
    def _build_clause_verdicts(self, tender_score: TenderScore) -> List:
        """Build clause-level verdicts section"""
        
        story = []
        
        story.append(Paragraph("REQUIREMENT ANALYSIS", self.styles['SectionHead']))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("The following requirements were evaluated:", self.styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))
        
        # Build requirement table
        req_data = [['Requirement', 'Met?', 'Notes']]
        
        for assessment in tender_score.eligibility.requirements_assessments[:10]:
            met_status = "✓ Yes" if assessment.company_meets else "✗ No"
            req_data.append([
                assessment.requirement_text[:40] + ('...' if len(assessment.requirement_text) > 40 else ''),
                met_status,
                assessment.reasoning[:50] + ('...' if len(assessment.reasoning) > 50 else ''),
            ])
        
        table = Table(req_data, colWidths=[2.8*inch, 0.8*inch, 2.6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
        
        if len(tender_score.eligibility.requirements_assessments) > 10:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(
                f"... and {len(tender_score.eligibility.requirements_assessments) - 10} more requirements",
                self.styles['BodyText']
            ))
        
        return story
    
    def _build_risk_details(self, tender_score: TenderScore) -> List:
        """Build risk details section"""
        
        story = []
        
        story.append(Paragraph("RISK ASSESSMENT DETAILS", self.styles['SectionHead']))
        story.append(Spacer(1, 0.1*inch))
        
        # Risk summary
        risk_text = f"""
        <b>Total Risks Identified:</b> {tender_score.risk.total_risks}<br/>
        <b>Critical Risks:</b> {tender_score.risk.critical_count}<br/>
        <b>High-Severity Risks:</b> {tender_score.risk.high_count}<br/>
        <b>Medium-Severity Risks:</b> {tender_score.risk.medium_count}<br/>
        <b>Low-Severity Risks:</b> {tender_score.risk.low_count}<br/>
        """
        story.append(Paragraph(risk_text, self.styles['BodyText']))
        story.append(Spacer(1, 0.2*inch))
        
        # Top risks
        if tender_score.risk.top_risks:
            story.append(Paragraph("<b>Top Risks:</b>", self.styles['SubSectionHead']))
            for i, risk in enumerate(tender_score.risk.top_risks, 1):
                story.append(Paragraph(f"{i}. {risk}", self.styles['BodyText']))
        
        # Deal-breakers
        if tender_score.risk.deal_breakers:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<b>Critical Deal-Breaker Risks (Must be resolved):</b>", self.styles['SubSectionHead']))
            for db in tender_score.risk.deal_breakers:
                story.append(Paragraph(f"🚫 {db}", self.styles['ActionText']))
        
        return story
    
    def _build_effort_details(self, tender_score: TenderScore) -> List:
        """Build effort details section"""
        
        story = []
        
        story.append(Paragraph("EFFORT & RESOURCE REQUIREMENTS", self.styles['SectionHead']))
        story.append(Spacer(1, 0.1*inch))
        
        # Effort metrics
        metrics = tender_score.effort.metrics
        effort_text = f"""
        <b>Total Estimated Hours:</b> {metrics.total_hours:.0f}<br/>
        <b>Timeline:</b> {metrics.total_days} calendar days<br/>
        <b>Recommended Team Size:</b> {metrics.team_size} people<br/>
        <b>Estimated Cost:</b> ${metrics.estimated_cost:,.0f}<br/>
        <b>Cost per Hour:</b> ${metrics.cost_per_hour:.2f}<br/>
        """
        story.append(Paragraph(effort_text, self.styles['BodyText']))
        
        # Complexity factors
        if tender_score.effort.complexity_factors:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<b>Complexity Factors:</b>", self.styles['SubSectionHead']))
            for factor in tender_score.effort.complexity_factors:
                story.append(Paragraph(f"• {factor}", self.styles['BodyText']))
        
        return story
    
    def _build_recommendations(self, tender_score: TenderScore) -> List:
        """Build recommendations section"""
        
        story = []
        
        story.append(Paragraph("STRATEGIC RECOMMENDATIONS", self.styles['SectionHead']))
        story.append(Spacer(1, 0.1*inch))
        
        # Critical items
        if tender_score.critical_items:
            story.append(Paragraph("<b>Critical Action Items:</b>", self.styles['SubSectionHead']))
            for item in tender_score.critical_items[:5]:
                story.append(Paragraph(item, self.styles['ActionText']))
            story.append(Spacer(1, 0.2*inch))
        
        # Decision rationale
        rec_data = self.translator.recommendation_explanation(
            tender_score.bid_recommendation,
            tender_score.overall_score
        )
        
        story.append(Paragraph("<b>Final Recommendation:</b>", self.styles['SubSectionHead']))
        story.append(Paragraph(rec_data['headline'], self.styles['BodyText']))
        story.append(Paragraph(rec_data['summary'], self.styles['VerdictText']))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph("<b>Next Steps:</b>", self.styles['SubSectionHead']))
        story.append(Paragraph(rec_data['details'], self.styles['ActionText']))
        
        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            f"<font size=8>Report generated by Tender-AI on {datetime.now().strftime('%B %d, %Y')}</font>",
            self.styles['BodyText']
        ))
        
        return story


# Convenience function
def generate_tender_report(tender_score: TenderScore, company_name: str = "Your Company") -> BytesIO:
    """Convenience function to generate PDF report"""
    
    generator = ReportGenerator()
    return generator.generate_pdf(tender_score, company_name)
