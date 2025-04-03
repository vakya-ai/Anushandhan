# backend/app/services/ieee_formatter.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import List, Dict
import textwrap
from datetime import datetime

class IEEEFormatter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom styles for IEEE format"""
        self.styles.add(ParagraphStyle(
            name='IEEETitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=30,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='IEEEAuthor',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=24,
            alignment=1
        ))
        
        self.styles.add(ParagraphStyle(
            name='IEEEAbstract',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            leftIndent=36,
            rightIndent=36
        ))
        
        self.styles.add(ParagraphStyle(
            name='IEEESection',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='IEEEBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=6,
            spaceAfter=6
        ))

    def format_paper(self, content: Dict, output_path: str):
        """Format paper content according to IEEE guidelines"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title
        story.append(Paragraph(content['title'], self.styles['IEEETitle']))
        story.append(Spacer(1, 12))
        
        # Abstract
        story.append(Paragraph('Abstract', self.styles['IEEESection']))
        story.append(Paragraph(content['abstract'], self.styles['IEEEAbstract']))
        story.append(Spacer(1, 12))
        
        # Main sections
        sections = [
            ('Introduction', content['introduction']),
            ('Methodology', content['methodology']),
            ('Results', content['results']),
            ('Conclusion', content['conclusion'])
        ]
        
        for section_title, section_content in sections:
            story.append(Paragraph(section_title, self.styles['IEEESection']))
            
            # Split content into paragraphs and format each
            paragraphs = section_content.split('\n\n')
            for para in paragraphs:
                story.append(Paragraph(para.strip(), self.styles['IEEEBody']))
            
            story.append(Spacer(1, 12))
        
        # Build the PDF
        doc.build(story)

    def _format_references(self, references: List[Dict]) -> List[Paragraph]:
        """Format references according to IEEE style"""
        formatted_refs = []
        for i, ref in enumerate(references, 1):
            ref_text = f"[{i}] {ref['authors']}, \"{ref['title']}\", "
            if ref.get('journal'):
                ref_text += f"{ref['journal']}, "
            if ref.get('volume'):
                ref_text += f"vol. {ref['volume']}, "
            if ref.get('number'):
                ref_text += f"no. {ref['number']}, "
            if ref.get('pages'):
                ref_text += f"pp. {ref['pages']}, "
            if ref.get('year'):
                ref_text += f"{ref['year']}."
            
            formatted_refs.append(Paragraph(ref_text, self.styles['IEEEBody']))
        return formatted_refs

    def format_code_snippet(self, code: str, language: str) -> str:
        """Format code snippets for inclusion in the paper"""
        wrapped_code = textwrap.fill(code, width=80)
        return f"""\\begin{{lstlisting}}[language={language}]
{wrapped_code}
\\end{{lstlisting}}"""