from fastapi import APIRouter, HTTPException
import asyncio
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..services.gemini_generator import GeminiGenerator
from ..services.github_processor import GitHubProcessor
from ..services.content_generator import ContentGenerator
from ..utils.paper_humanizer import PaperHumanizer

logger = logging.getLogger(__name__)

router = APIRouter()

class ResearchPaperGenerator:
    """
    Service to generate research papers from code repositories
    using the Gemini AI model with enhanced humanization.
    """
    def __init__(self):
        self.gemini_generator = GeminiGenerator()
        self.github_processor = GitHubProcessor()
        self.content_generator = ContentGenerator()
        self.humanizer = PaperHumanizer()
        
    async def generate_research_paper(
        self,
        topic: str,
        sections: Optional[List[str]] = None,
        word_count: int = 3000,
        repo_url: Optional[str] = None,
        include_function_details: bool = False
    ) -> Dict[str, str]:
        try:
            logger.info(f"Generating research paper on topic: {topic}")

            if not sections:
                sections = [
                    "abstract",
                    "introduction",
                    "literature_review",
                    "methodology",
                    "results",
                    "discussion",
                    "conclusion",
                    "references"
                ]
            sections = [section.lower() for section in sections]
            if "code_analysis" in sections:
                sections.remove("code_analysis")

            result = {}

            if repo_url:
                logger.info(f"Analyzing GitHub repository: {repo_url}")
                repo_path = await self.github_processor.clone_repository(repo_url)
                try:
                    code_files = await self.github_processor.read_repository_files(repo_path)
                    repo_metadata = await self.github_processor.get_repository_metadata(repo_url)
                    code_chunks = await self.gemini_generator.divide_code_into_chunks(code_files)

                    if include_function_details:
                        system_prompt = """
You are generating a technical research paper based on a software repository.

IMPORTANT INSTRUCTIONS:
1. You MAY include function names and provide concise descriptions of their purposes.
2. You MAY include high-level summaries of key files and their roles.
3. You MUST NOT include raw code snippets or full code blocks.
4. Focus on how the codebase is structured, including important modules, classes, and functions.
5. Structure your response like a formal software engineering report, with sections for architecture, key components, and (optionally) a function index.
6. Where relevant, include a table listing function names, parameters, and a one-line description.
7. Write in a natural, human-like manner that flows well and sounds professional.
8. Use varied sentence structures and avoid repetitive patterns.
"""
                    else:
                        system_prompt = """
You are generating a formal IEEE-style academic research paper based on a software repository.

EXTREMELY IMPORTANT INSTRUCTIONS - You MUST follow these exactly:
1. DO NOT include ANY code snippets whatsoever in your response
2. DO NOT include a "Code Analysis" section or any similar section
3. DO NOT analyze or describe individual files, functions, or code fragments
4. Focus ONLY on high-level architectural concepts, design patterns, and software engineering principles
5. Structure your response like a traditional academic paper with ONLY the standard sections
6. Your analysis should focus on architectural patterns, not implementation details
7. Write in a natural, human-like academic style that flows well
8. Use varied sentence structures and avoid repetitive or robotic patterns
9. Include thoughtful insights and analysis rather than just descriptions
"""

                    for section in sections:
                        if section in ["code_analysis", "code analysis", "implementation"]:
                            continue

                        # Generate base content
                        if include_function_details:
                            section_instruction = f"""
Generate the {section} section for a technical research paper about the repository.

- You MAY include function names and summaries.
- Provide tables or lists of important functions with their purposes and parameters.
- DO NOT include raw code snippets.
- Focus on code structure, architecture, and key components.
- Write naturally and professionally, as if a human academic wrote this.
- Use varied sentence structures and smooth transitions between ideas.
"""
                        else:
                            section_instruction = f"""
Generate the {section} section for an IEEE research paper about the repository.

EXTREMELY IMPORTANT:
- DO NOT include ANY code snippets
- DO NOT include file-by-file analysis
- DO NOT mention specific variable names, function names, or code details
- Focus ONLY on high-level architectural concepts and software engineering principles
- Write in a natural, human-like academic style
- Use thoughtful analysis and insights, not just descriptions
- Ensure smooth flow and proper transitions between ideas
"""

                        repo_info = f"""
Repository Name: {repo_metadata.get('name', 'Unknown')}
Repository Owner: {repo_metadata.get('owner', 'Unknown')}
Description: {repo_metadata.get('description', 'No description')}
Stars: {repo_metadata.get('stars', 0)}
Primary Language: {repo_metadata.get('language', 'Unknown')}
Created: {repo_metadata.get('created_at', 'Unknown')}
Last Updated: {repo_metadata.get('updated_at', 'Unknown')}
"""

                        if section == "references":
                            refs_instruction = """
Generate the references section for an IEEE research paper about software architecture and engineering.
Format the references in proper IEEE format.
Include the GitHub repository as the first reference. Then include relevant software engineering references.
DO NOT make up fake citations - use only legitimate, well-known software engineering books and papers.
Write the references in a natural, proper academic format.
"""
                            base_content = await self.gemini_generator._generate_with_gemini(
                                "You are a bibliography generator for IEEE papers. You create proper IEEE format references with natural academic formatting.",
                                f"{refs_instruction}\n\nRepository: {repo_url}\nNo code snippets allowed."
                            )
                        else:
                            base_content = await self.gemini_generator._generate_with_gemini(
                                system_prompt,
                                f"{section_instruction}\n\nRepository Metadata:\n{repo_info}"
                            )
                        
                        # Humanize the content
                        result[section] = await self.humanizer.humanize_content(base_content, section)
                        
                finally:
                    if os.path.exists(repo_path):
                        try:
                            self.github_processor.safe_rmtree(repo_path)
                        except Exception as cleanup_error:
                            logger.warning(f"Failed to clean up temporary directory: {str(cleanup_error)}")
            else:
                # Topic-only generation with humanization
                target_words_per_section = max(200, word_count // len(sections))
                
                for section in sections:
                    if section == "references":
                        combined_prompt = f"""
Generate the references section for a research paper on the topic: {topic}.
Include legitimate academic references in proper IEEE format.
Ensure the references are relevant to {topic} and properly formatted.
Write them naturally as they would appear in a professional academic paper.
"""
                    else:
                        combined_prompt = f"""
Generate the {section} section for a research paper on the topic: {topic}.
This section should be approximately {target_words_per_section} words.
Write in a natural, human-like academic style with:
- Varied sentence structures
- Smooth transitions between ideas
- Professional yet engaging tone
- Thoughtful insights and analysis
- Proper academic vocabulary without being overly complex
Focus on {topic} and ensure the content is relevant and well-structured.
"""

                    system_prompt = """
You are a research paper generator that creates comprehensive, well-structured academic papers.
Your writing should sound natural and human-like, with:
- Varied sentence structures and lengths
- Smooth transitions between paragraphs
- Thoughtful analysis and insights
- Professional yet accessible language
- Proper academic tone without being robotic
Write in IEEE format with proper structure and flow.
"""

                    try:
                        base_content = await self.gemini_generator._generate_with_gemini(system_prompt, combined_prompt)
                        result[section] = await self.humanizer.humanize_content(base_content, section)
                    except Exception as e:
                        logger.error(f"Error generating {section}: {str(e)}")
                        result[section] = f"Error generating {section}. Please try again."

            # Format and structure the final paper
            formatted_result = {}
            section_order = ["abstract", "introduction", "literature_review", "methodology",
                             "results", "discussion", "conclusion", "references"]

            for section in section_order:
                formatted_section = ' '.join(word.capitalize() for word in section.split('_'))
                formatted_result[formatted_section] = result.get(section, f"This {formatted_section} section was not generated.")

            # Create IEEE-style header with better formatting
            ieee_header = self._generate_ieee_header(topic, repo_url)
            
            # Construct full paper with proper structure
            full_paper = self._construct_full_paper(topic, ieee_header, result, section_order)
            formatted_result["Full Paper"] = full_paper

            return formatted_result

        except Exception as e:
            import traceback
            logger.error(f"Error generating research paper: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def _generate_ieee_header(self, topic: str, repo_url: Optional[str] = None) -> str:
        """Generate a properly formatted IEEE-style header"""
        header = "## IEEE Conference Paper\n\n"
        header += f"**Title**: {topic}\n"
        
        if repo_url:
            parts = repo_url.rstrip('/').split('/')
            owner = parts[-2] if len(parts) >= 2 else "Unknown"
            repo_name = parts[-1] if len(parts) >= 1 else "Unknown"
            header += f"**Repository**: {owner}/{repo_name}\n"
            header += f"**URL**: {repo_url}\n"
        
        header += f"**Date**: {datetime.now().strftime('%B %d, %Y')}\n"
        header += f"**Authors**: Research Paper Generator v2.0\n\n"
        
        return header
    
    def _construct_full_paper(self, topic: str, header: str, content: Dict[str, str], section_order: List[str]) -> str:
        """Construct the full paper with proper formatting and structure"""
        full_paper = f"# {topic}\n\n"
        full_paper += header
        
        # Add table of contents
        full_paper += "## Table of Contents\n\n"
        for i, section in enumerate(section_order, 1):
            formatted_section = ' '.join(word.capitalize() for word in section.split('_'))
            full_paper += f"{i}. {formatted_section}\n"
        full_paper += "\n---\n\n"
        
        # Add sections with proper numbering
        section_numbers = {
            "abstract": "0",
            "introduction": "I",
            "literature_review": "II",
            "methodology": "III",
            "results": "IV",
            "discussion": "V",
            "conclusion": "VI",
            "references": ""
        }
        
        for section in section_order:
            formatted_section = ' '.join(word.capitalize() for word in section.split('_'))
            
            if section == "abstract":
                full_paper += f"## Abstract\n\n"
            elif section == "references":
                full_paper += f"## References\n\n"
            else:
                full_paper += f"## {section_numbers[section]}. {formatted_section}\n\n"
            
            content_text = content.get(section, f"This {formatted_section} section was not generated.")
            
            # Add some formatting improvements
            if section == "references":
                # Format references with proper numbering
                refs = content_text.split('\n')
                formatted_refs = []
                for i, ref in enumerate(refs, 1):
                    if ref.strip() and not ref.startswith('['):
                        formatted_refs.append(f"[{i}] {ref.strip()}")
                    elif ref.strip():
                        formatted_refs.append(ref)
                full_paper += '\n'.join(formatted_refs)
            else:
                full_paper += content_text
            
            full_paper += "\n\n"
        
        # Add footer
        full_paper += "---\n\n"
        full_paper += "*This paper was generated using advanced AI technology for research and educational purposes.*\n"
        
        return full_paper

generator = ResearchPaperGenerator()

@router.post("/generate-paper")
async def generate_research_paper(request_data: dict):
    try:
        topic = request_data.get("topic")
        sections = request_data.get("sections", [])
        word_count = request_data.get("wordCount", 3000)
        repo_url = request_data.get("repoUrl")
        if not repo_url and request_data.get("sourceType") == "github":
            repo_url = request_data.get("sourceUrl")
        include_function_details = request_data.get("includeFunctionDetails", False)

        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")

        paper = await generator.generate_research_paper(
            topic=topic,
            sections=sections,
            word_count=word_count,
            repo_url=repo_url,
            include_function_details=include_function_details
        )
        return {"paper": paper}
    except Exception as e:
        logger.error(f"Error in generate_research_paper endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))