def _generate_simple_html(self, paper_data: Dict) -> str:
        """Generate a simple HTML version if the template is missing"""
        # Updated to exclude code analysis sections
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