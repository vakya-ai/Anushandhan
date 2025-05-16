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

logger = logging.getLogger(__name__)

router = APIRouter()

class ResearchPaperGenerator:
    """
    Service to generate research papers from code repositories
    using the Gemini AI model.
    """
    def __init__(self):
        self.gemini_generator = GeminiGenerator()
        self.github_processor = GitHubProcessor()
        self.content_generator = ContentGenerator()
        
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
"""

                    for section in sections:
                        if section in ["code_analysis", "code analysis", "implementation"]:
                            continue

                        if include_function_details:
                            section_instruction = f"""
Generate the {section} section for a technical research paper about the repository.

- You MAY include function names and summaries.
- Provide tables or lists of important functions with their purposes and parameters.
- DO NOT include raw code snippets.
- Focus on code structure, architecture, and key components.
"""
                        else:
                            section_instruction = f"""
Generate the {section} section for an IEEE research paper about the repository.

EXTREMELY IMPORTANT:
- DO NOT include ANY code snippets
- DO NOT include file-by-file analysis
- DO NOT mention specific variable names, function names, or code details
- Focus ONLY on high-level architectural concepts and software engineering principles
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
"""
                            result[section] = await self.gemini_generator._generate_with_gemini(
                                "You are a bibliography generator for IEEE papers. You create proper IEEE format references.",
                                f"{refs_instruction}\n\nRepository: {repo_url}\nNo code snippets allowed."
                            )
                        else:
                            result[section] = await self.gemini_generator._generate_with_gemini(
                                system_prompt,
                                f"{section_instruction}\n\nRepository Metadata:\n{repo_info}"
                            )
                finally:
                    if os.path.exists(repo_path):
                        try:
                            self.github_processor.safe_rmtree(repo_path)
                        except Exception as cleanup_error:
                            logger.warning(f"Failed to clean up temporary directory: {str(cleanup_error)}")
            else:
                # Topic-only generation
                combined_prompt = f"Generate a research paper on the topic: {topic}. "
                combined_prompt += f"Include the following sections: {', '.join(sections)}. "
                combined_prompt += f"The paper should be approximately {word_count} words. "
                combined_prompt += f"DO NOT include code snippets or a 'Code Analysis' section. "
                combined_prompt += f"This should be a formal academic paper in IEEE format."

                system_prompt = "You are a research paper generator that creates comprehensive, "
                system_prompt += "well-structured academic papers on a given topic in IEEE format. "
                system_prompt += "Focus on traditional academic writing, following a formal structure with "
                system_prompt += "Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, and References. "
                system_prompt += "DO NOT include code snippets or implementation details."

                try:
                    response = await self.gemini_generator._generate_with_gemini(system_prompt, combined_prompt)

                    current_section = None
                    for line in response.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        lower_line = line.lower()
                        found_section = None
                        for section in sections:
                            if section in lower_line or section.replace('_', ' ') in lower_line:
                                found_section = section
                                break
                        if found_section:
                            current_section = found_section
                            result[current_section] = ""
                        elif current_section:
                            result[current_section] += line + "\n"

                    for section in sections:
                        if section not in result:
                            result[section] = f"Content for {section} section."
                except Exception as e:
                    logger.error(f"Error generating paper with Gemini: {str(e)}")
                    raise

            formatted_result = {}
            section_order = ["abstract", "introduction", "literature_review", "methodology",
                             "results", "discussion", "conclusion", "references"]

            for section in section_order:
                formatted_section = ' '.join(word.capitalize() for word in section.split('_'))
                formatted_result[formatted_section] = result.get(section, f"This {formatted_section} section was not generated.")

            ieee_header = "## IEEE Conference Paper\n\n"
            if repo_url:
                parts = repo_url.rstrip('/').split('/')
                owner = parts[-2] if len(parts) >= 2 else "Unknown"
                repo_name = parts[-1] if len(parts) >= 1 else "Unknown"
                ieee_header += f"**Repository**: {owner}/{repo_name}\n"
            else:
                ieee_header += f"**Topic**: {topic}\n"

            ieee_header += f"**Date**: {datetime.now().strftime('%B %d, %Y')}\n"
            if repo_url:
                ieee_header += f"**URL**: {repo_url}\n\n"

            full_paper = f"# Research Paper: {topic}\n\n{ieee_header}"
            for section in section_order:
                formatted_section = ' '.join(word.capitalize() for word in section.split('_'))
                full_paper += f"## {formatted_section}\n\n{result.get(section, '')}\n\n"

            formatted_result["Full Paper"] = full_paper

            return formatted_result

        except Exception as e:
            import traceback
            logger.error(f"Error generating research paper: {str(e)}\n{traceback.format_exc()}")
            raise

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
