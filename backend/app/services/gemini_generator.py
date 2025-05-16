import google.generativeai as genai
from app.core.config import settings
import asyncio
from typing import Dict, List, Any, Optional
import random
import re
import time

class GeminiGenerator:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        
        # Configuration for humanization
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.9,  # Increased for more creative output
            top_p=0.9,
            top_k=40,
            candidate_count=1,
            max_output_tokens=2048,
        )
        
        # Enhanced system prompts for each section with anti-AI detection techniques
        self.prompts = {
            "abstract": """You are an experienced research scholar writing a scholarly abstract.
                        Write in your natural academic voice, using varied sentence structures.
                        Include occasional contractions and personal touches while maintaining formality.
                        Occasionally include a slightly unconventional phrasing or word choice that a human would make.
                        Focus on the purpose and significance of the code analysis.""",
            
            "introduction": """You are a seasoned academic researcher writing an introduction.
                           Write conversationally yet professionally, as if explaining to a colleague.
                           Use rhetorical questions occasionally. Vary your sentence lengths naturally.
                           Include some domain-specific metaphors or analogies that show personal understanding.
                           Explain the background and motivation naturally, not formulaically.""",
            
            "methodology": """You are a technical expert explaining your approach to a peer.
                          Use a mix of technical precision and casual explanations.
                          Include some personal observations about challenges faced.
                          Occasionally use phrases like "we found that..." or "our approach differs in that..."
                          Explain the technical implementation with subtle imperfections that humans would make.""",
            
            "literature_review": """You are a scholar surveying related work in your field.
                                 Write with the voice of someone who has deeply engaged with these sources.
                                 Occasionally include slight bias or preference for certain approaches.
                                 Use transitional phrases that show critical thinking: "while X argues..., we contend..."
                                 Include subtle critiques or praise that shows personal academic judgment.""",
            
            "results": """You are presenting findings with the enthusiasm of discovery.
                        Use varied data presentation methods. Include some interpretation alongside raw results.
                        Occasionally acknowledge limitations or surprises in the findings.
                        Use phrases that show personal involvement: "we were surprised to find..." or "notably, our results suggest..."
                        Present results with the natural flow of someone who lived through the research process.""",
            
            "discussion": """You are reflecting on your research findings like a thoughtful scholar.
                          Include nuanced arguments and acknowledge multiple perspectives.
                          Use conditional language: "might suggest", "could indicate", "appears to confirm"
                          Include some speculation about implications with appropriate caveats.
                          Show depth of thought with complex, interconnected ideas.""",
            
            "conclusion": """You are concluding your research narrative as a researcher would.
                         Include some personal reflection on the research journey.
                         Acknowledge both achievements and limitations honestly.
                         Use future tense variably: mix "will", "could", "might" for future work.
                         End with impact that goes beyond just summarizing.""",
            
            "references": """You are selecting references as a knowledgeable researcher would.
                         Include a mix of seminal works and recent developments.
                         Occasionally include slightly unexpected but relevant sources.
                         Show awareness of different schools of thought in your citations."""
        }
        
        # Humanization techniques
        self.human_patterns = {
            "sentence_starters": [
                "Interestingly,", "Notably,", "It's worth mentioning that", 
                "One might argue that", "In practice,", "From our experience,",
                "Surprisingly,", "As expected,", "Contrary to expectations,"
            ],
            "transition_phrases": [
                "more specifically", "in other words", "that is to say",
                "on the other hand", "nevertheless", "in contrast",
                "furthermore", "what's more", "in addition to this"
            ],
            "uncertainty_markers": [
                "perhaps", "likely", "possibly", "probably", "seemingly",
                "apparently", "presumably", "conceivably", "potentially"
            ],
            "hedging_phrases": [
                "to some extent", "in most cases", "generally speaking",
                "broadly speaking", "by and large", "for the most part"
            ]
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
    
    def _humanize_text(self, text: str) -> str:
        """
        Apply various humanization techniques to make text appear more natural
        """
        # Add slight inconsistencies in punctuation and spacing
        text = re.sub(r'\s+', ' ', text)  # Normalize spaces first
        
        # Randomly add extra space after commas occasionally
        if random.random() < 0.1:
            text = text.replace(', ', ',  ')
        
        # Occasionally replace some periods with semicolons in compound sentences
        sentences = text.split('. ')
        for i, sentence in enumerate(sentences):
            if random.random() < 0.15 and 'and' in sentence and len(sentence) > 50:
                sentences[i] = sentence.replace(' and ', '; and ')
        text = '. '.join(sentences)
        
        # Add natural language markers
        words = text.split()
        humanized_words = []
        
        for i, word in enumerate(words):
            # Randomly insert transition phrases
            if random.random() < 0.05 and i > 0:
                transition = random.choice(self.human_patterns["transition_phrases"])
                humanized_words.append(f"{transition},")
            
            # Add uncertainty markers occasionally
            if random.random() < 0.08 and word.endswith('.'):
                uncertainty = random.choice(self.human_patterns["uncertainty_markers"])
                word = f"{uncertainty} {word}"
            
            humanized_words.append(word)
        
        text = ' '.join(humanized_words)
        
        # Clean up double commas and spaces
        text = re.sub(r',\s*,', ',', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _add_natural_variations(self, text: str) -> str:
        """
        Add natural variations that humans would make
        """
        # Replace some formal phrases with more casual equivalents
        replacements = {
            r'\bIn conclusion\b': random.choice(['To conclude', 'In summary', 'To sum up', 'Finally']),
            r'\bFurthermore\b': random.choice(['What is more', 'Additionally', 'Also', 'Beyond this']),
            r'\bHowever\b': random.choice(['Nevertheless', 'On the other hand', 'Yet', 'Nonetheless']),
            r'\bTherefore\b': random.choice(['Thus', 'Hence', 'Consequently', 'As a result']),
            r'\bMoreover\b': random.choice(['In addition', 'What is more', 'Plus', 'Besides']),
        }
        
        for pattern, replacement in replacements.items():
            if random.random() < 0.3:  # Apply replacement 30% of the time
                text = re.sub(pattern, replacement, text)
        
        return text
    
    def _add_intentional_imperfections(self, text: str) -> str:
        """
        Add subtle imperfections that humans naturally make
        """
        # Occasionally use contractions in less formal sections
        if random.random() < 0.2:
            text = text.replace(' is not ', " isn't ")
            text = text.replace(' are not ', " aren't ")
            text = text.replace(' will not ', " won't ")
        
        # Add some British vs American spelling variations
        if random.random() < 0.3:
            text = text.replace('organize', 'organise')
            text = text.replace('optimize', 'optimise')
            text = text.replace('analyze', 'analyse')
        
        # Occasionally add redundant phrases that humans use
        redundant_phrases = [
            ('very', 'quite'),
            ('really', 'rather'),
            ('extremely', 'exceptionally'),
        ]
        
        for formal, casual in redundant_phrases:
            if random.random() < 0.1:
                text = text.replace(f' {formal} ', f' {casual} ')
        
        return text
    
    async def generate_paper_section(self, section: str, code_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a section of the research paper based on code chunks
        
        Args:
            section: Section name (abstract, introduction, etc.)
            code_chunks: List of code chunks to analyze
            
        Returns:
            Generated section content with humanization
        """
        system_prompt = self.prompts.get(section, "You are a research paper generator.")
        
        # Add randomness to code selection and presentation
        selected_chunks = random.sample(code_chunks, min(8, len(code_chunks)))
        
        # Prepare code content with varied formatting
        code_content = ""
        for i, chunk in enumerate(selected_chunks):
            if random.random() < 0.5:
                code_content += f"File {i+1}: {chunk['file_path']}\n"
            else:
                code_content += f"{chunk['file_path']} ({chunk['language']}):\n"
            
            # Include partial code rather than full files
            content_lines = chunk['content'].split('\n')
            if len(content_lines) > 30:
                selected_lines = content_lines[:15] + ['...', '// (snippet continues)'] + content_lines[-10:]
            else:
                selected_lines = content_lines
            
            code_content += f"```{chunk['language'].lower()}\n"
            code_content += '\n'.join(selected_lines)
            code_content += "\n```\n\n"
        
        # Create varied user prompts
        prompt_variations = [
            f"Based on the following code snippets, generate a {section} section for a research paper.",
            f"Using the code examples below, write a {section} section that sounds natural and human-written.",
            f"Analyze these code fragments and create a {section} section with academic tone.",
            f"From the provided code samples, develop a {section} section for a scholarly paper.",
        ]
        
        base_prompt = random.choice(prompt_variations)
        
        # Add specific instructions for humanization
        humanization_instructions = """
        IMPORTANT: Write as a human researcher would:
        - Use varied sentence structures and lengths
        - Include occasional subjective observations
        - Use transitional phrases naturally
        - Show uncertainty where appropriate with hedging language
        - Include minor grammatical imperfections that humans make
        - Vary your vocabulary choices
        - Write with subtle personal voice while maintaining academic tone
        """
        
        user_prompt = f"""{base_prompt}
        
        {humanization_instructions}
        
        Code to analyze:
        {code_content}
        """
        
        try:
            # Generate with higher temperature and multiple attempts
            attempts = 3
            best_response = None
            
            for attempt in range(attempts):
                # Slightly vary temperature for each attempt
                temp = 0.8 + (attempt * 0.1)
                self.generation_config.temperature = temp
                
                response = await self._generate_with_gemini(system_prompt, user_prompt)
                
                # Apply post-processing humanization
                response = self._humanize_text(response)
                response = self._add_natural_variations(response)
                response = self._add_intentional_imperfections(response)
                
                # Select best response (could add scoring logic here)
                if best_response is None or len(response) > len(best_response):
                    best_response = response
                
                # Add delay between attempts to avoid rate limiting
                await asyncio.sleep(0.5)
            
            return best_response
            
        except Exception as e:
            print(f"Error generating {section}: {str(e)}")
            return f"Error generating {section}. Please try again later."
    
    async def _generate_with_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call Gemini API with system and user prompts using enhanced configuration
        """
        try:
            # Add randomness to the combined prompt structure
            if random.random() < 0.5:
                combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            else:
                combined_prompt = f"{user_prompt}\n\nRemember to: {system_prompt}"
            
            # Add contextual noise to avoid pattern detection
            contextual_additions = [
                "\n\nWrite with natural academic flow.",
                "\n\nEnsure the content sounds human-written.",
                "\n\nUse varied language patterns.",
                "\n\nInclude subtle personal insights.",
            ]
            
            if random.random() < 0.4:
                combined_prompt += random.choice(contextual_additions)
            
            # Generate with enhanced configuration
            response = await asyncio.to_thread(
                self.model.generate_content,
                [combined_prompt],
                generation_config=self.generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            raise