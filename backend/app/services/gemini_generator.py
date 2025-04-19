import google.generativeai as genai
from app.core.config import settings
import asyncio
from typing import Dict, List, Any, Optional

class GeminiGenerator:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        
        # Hard-coded system prompts for each section
        self.prompts = {
            "abstract": """You are a research paper abstract generator. 
                        Generate a concise abstract that summarizes the given codebase.
                        Focus on the purpose, methodology, and significance of the code.""",
            
            "introduction": """You are a research paper introduction generator.
                           Generate an introduction that explains the background, 
                           motivation, and objectives of the provided codebase.""",
            
            "methodology": """You are a research paper methodology section generator.
                          Analyze the given codebase and explain the technical approach,
                          architecture, algorithms, and implementation details.""",
            
            "literature_review": """You are a research paper literature review generator.
                                 Based on the codebase, generate a literature review that
                                 discusses related work, techniques, and approaches.""",
            
            "results": """You are a research paper results section generator.
                        Analyze the codebase and generate a results section that 
                        describes the capabilities, performance, and outcomes.""",
            
            "discussion": """You are a research paper discussion section generator.
                          Based on the codebase, generate a discussion that analyzes
                          strengths, limitations, and implications of the work.""",
            
            "conclusion": """You are a research paper conclusion generator.
                         Generate a conclusion summarizing the key contributions,
                         limitations, and future work based on the codebase.""",
            
            "references": """You are a research paper references generator.
                         Generate a list of relevant references that would be cited 
                         in a paper about the given codebase."""
        }
    
    async def divide_code_into_chunks(self, code_content: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Divide a codebase into logical chunks for processing
        
        Args:
            code_content: Dictionary mapping file paths to content
            
        Returns:
            List of code chunks with metadata
        """
        chunks = []
        
        # Simple chunking by file
        for file_path, content in code_content.items():
            # Skip non-code files, binaries, etc.
            if self._is_processable_file(file_path):
                chunk = {
                    "file_path": file_path,
                    "content": content,
                    "language": self._detect_language(file_path),
                    "size": len(content)
                }
                chunks.append(chunk)
        
        return chunks
    
    def _is_processable_file(self, file_path: str) -> bool:
        """Check if a file should be processed based on extension"""
        excluded_extensions = ['.exe', '.bin', '.jpg', '.png', '.gif', '.pdf', '.zip']
        excluded_dirs = ['.git', 'node_modules', '__pycache__', 'venv', 'env']
        
        # Check for excluded directories
        for dir_name in excluded_dirs:
            if f"/{dir_name}/" in file_path or file_path.startswith(f"{dir_name}/"):
                return False
        
        # Check file extension
        for ext in excluded_extensions:
            if file_path.endswith(ext):
                return False
                
        return True
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'React/JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'React/TypeScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.md': 'Markdown',
            '.json': 'JSON',
            '.yml': 'YAML',
            '.xml': 'XML'
        }
        
        for ext, lang in extensions.items():
            if file_path.endswith(ext):
                return lang
        
        return 'Unknown'
    
    async def generate_paper_section(self, section: str, code_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a section of the research paper based on code chunks
        
        Args:
            section: Section name (abstract, introduction, etc.)
            code_chunks: List of code chunks to analyze
            
        Returns:
            Generated section content
        """
        system_prompt = self.prompts.get(section, "You are a research paper generator.")
        
        # Prepare code content for Gemini
        code_content = "\n\n".join([
            f"File: {chunk['file_path']}\nLanguage: {chunk['language']}\n\n```{chunk['language'].lower()}\n{chunk['content']}\n```"
            for chunk in code_chunks[:10]  # Limit to 10 chunks to avoid token limits
        ])
        
        # Add instruction for humanized output
        user_prompt = f"""Based on the following code chunks, generate a {section} section for a research paper.
        Make the content sound natural and human-written, avoiding robotic or formulaic language.
        
        {code_content}
        """
        
        # Call Gemini API
        try:
            response = await self._generate_with_gemini(system_prompt, user_prompt)
            return response
        except Exception as e:
            print(f"Error generating {section}: {str(e)}")
            return f"Error generating {section}. Please try again later."
    
    async def _generate_with_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call Gemini API with system and user prompts
        
        This is a placeholder for the actual implementation that would use the Gemini API
        """
        try:
            print(f"Gemini API call with system prompt: {system_prompt}")
            print(f"Gemini API call with user prompt: {user_prompt}")
            # In an async context, we need to run the Gemini call in a thread pool
            response = await asyncio.to_thread(
                self.model.generate_content,
                [
                    {"role": "system", "parts": [system_prompt]},
                    {"role": "user", "parts": [user_prompt]}
                ]
            )
            print(f"Gemini API response: {response}")
        
            return response.text
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            raise