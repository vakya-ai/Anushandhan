# backend/app/services/content_generator.py
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqGeneration
from typing import Dict, List
import torch
from sentence_transformers import SentenceTransformer
import numpy as np

class ContentGenerator:
    def __init__(self):
        # Initialize models
        self.tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large")
        self.model = AutoModelForSeq2SeqGeneration.from_pretrained("facebook/bart-large")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize summarization pipeline
        self.summarizer = pipeline("summarization", 
                                 model="facebook/bart-large-cnn",
                                 device=0 if torch.cuda.is_available() else -1)

    def generate_paper_content(self, repository_data: Dict) -> Dict:
        """Generate research paper content from repository data."""
        # Extract and process repository information
        readme_content = repository_data.get("readme", "")
        code_files = repository_data.get("files", [])
        
        # Generate paper sections
        abstract = self._generate_abstract(readme_content, code_files)
        introduction = self._generate_introduction(readme_content)
        methodology = self._generate_methodology(code_files)
        results = self._generate_results(repository_data)
        conclusion = self._generate_conclusion(abstract, methodology)
        
        return {
            "title": self._generate_title(abstract),
            "abstract": abstract,
            "introduction": introduction,
            "methodology": methodology,
            "results": results,
            "conclusion": conclusion
        }

    def _generate_abstract(self, readme: str, code_files: List[Dict]) -> str:
        """Generate paper abstract."""
        # Combine relevant information
        content = readme + "\n" + "\n".join(f["content"] for f in code_files[:3])
        
        # Generate summary
        summary = self.summarizer(content, 
                                max_length=150, 
                                min_length=50, 
                                do_sample=False)[0]['summary_text']
        
        return self._enhance_text(summary)

    def _generate_methodology(self, code_files: List[Dict]) -> str:
        """Generate methodology section from code files."""
        # Extract main implementation details
        main_files = [f for f in code_files 
                     if self._is_main_implementation_file(f["path"])]
        
        methodology_text = ""
        for file in main_files:
            # Analyze code structure
            file_analysis = self._analyze_code_structure(file["content"])
            methodology_text += self._generate_section_content(
                file_analysis,
                "Methodology section for " + file["path"],
                max_length=300
            )
        
        return self._enhance_text(methodology_text)

    def _enhance_text(self, text: str) -> str:
        """Enhance text to make it more academic and formal."""
        # TODO: Implement text enhancement using transformers
        return text

    def _analyze_code_structure(self, code_content: str) -> Dict:
        """Analyze code structure and extract key components."""
        # TODO: Implement code analysis
        return {"content": code_content}

    def _is_main_implementation_file(self, file_path: str) -> bool:
        """Check if file is a main implementation file."""
        main_patterns = ["main", "core", "model", "implementation"]
        return any(pattern in file_path.lower() for pattern in main_patterns)

    def _generate_section_content(self, 
                                analysis: Dict, 
                                prompt: str, 
                                max_length: int = 200) -> str:
        """Generate content for a paper section."""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
        
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=max_length,
            num_beams=4,
            length_penalty=2.0,
            early_stopping=True
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def _generate_title(self, abstract: str) -> str:
        """Generate paper title from abstract."""
        return self._generate_section_content(
            {"content": abstract},
            "Generate academic paper title:",
            max_length=50
        )