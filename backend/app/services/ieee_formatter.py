from typing import Dict, List, Optional
import jinja2
import tempfile
import os
import asyncio

class IEEEFormatter:
    """Service for formatting research papers in IEEE style"""
    
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), '../templates')
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    async def generate_html(self, paper_data: Dict) -> str:
        """
        Generate HTML version of the research paper
        
        Args:
            paper_data: Dictionary containing paper sections and metadata
            
        Returns:
            HTML string of the formatted paper
        """
        try:
            template = self.env.get_template("ieee_template.html")
            html = template.render(**paper_data)
            return html
        except jinja2.exceptions.TemplateNotFound:
            # Fallback to simple HTML if template is missing
            return self._generate_simple_html(paper_data)
    
    def _generate_simple_html(self, paper_data: Dict) -> str:
        """Generate a simple HTML version if the template is missing"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{paper_data.get('title', 'Research Paper')}</title>
            <style>
                body {{ font-family: 'Times New Roman', Times, serif; margin: 40px; line-height: 1.5; }}
                h1 {{ text-align: center; }}
                h2 {{ margin-top: 20px; }}
                .abstract {{ font-style: italic; margin: 20px 0; }}
                .section {{ margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>{paper_data.get('title', 'Research Paper')}</h1>
            
            <div class="abstract">
                <h2>Abstract</h2>
                <p>{paper_data.get('abstract', '')}</p>
            </div>
            
            <div class="section">
                <h2>I. Introduction</h2>
                <p>{paper_data.get('introduction', '')}</p>
            </div>
            
            <div class="section">
                <h2>II. Literature Review</h2>
                <p>{paper_data.get('literature_review', '')}</p>
            </div>
            
            <div class="section">
                <h2>III. Methodology</h2>
                <p>{paper_data.get('methodology', '')}</p>
            </div>
            
            <div class="section">
                <h2>IV. Results</h2>
                <p>{paper_data.get('results', '')}</p>
            </div>
            
            <div class="section">
                <h2>V. Discussion</h2>
                <p>{paper_data.get('discussion', '')}</p>
            </div>
            
            <div class="section">
                <h2>VI. Conclusion</h2>
                <p>{paper_data.get('conclusion', '')}</p>
            </div>
            
            <div class="section">
                <h2>References</h2>
                <ol>
                    {self._format_references(paper_data.get('references', []))}
                </ol>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_references(self, references: List[str]) -> str:
        """Format references as HTML list items"""
        return ''.join([f"<li>{ref}</li>" for ref in references])
    
    async def generate_pdf(self, html: str) -> str:
        """
        Generate PDF from HTML using a tool like WeasyPrint or wkhtmltopdf
        
        Args:
            html: HTML content to convert
            
        Returns:
            Path to the generated PDF file
        """
        # This is a placeholder. You would implement PDF generation using
        # a library like WeasyPrint, wkhtmltopdf, or a similar tool.
        
        # For example, using wkhtmltopdf via subprocess:
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as html_file:
            html_file.write(html)
            html_path = html_file.name
        
        pdf_path = html_path.replace('.html', '.pdf')
        
        try:
            # Use asyncio subprocess to avoid blocking
            process = await asyncio.create_subprocess_exec(
                "wkhtmltopdf", html_path, pdf_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Failed to generate PDF: {stderr.decode()}")
                
            # Clean up HTML file
            os.unlink(html_path)
                
            return pdf_path
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(html_path):
                os.unlink(html_path)
            raise e