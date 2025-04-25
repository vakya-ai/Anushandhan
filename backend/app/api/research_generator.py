# In backend/app/api/research_generator.py or similar
from fastapi import APIRouter, HTTPException
import asyncio
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import services directly without using app
from ..services.gemini_generator import GeminiGenerator
from ..services.github_processor import GitHubProcessor
from ..services.content_generator import ContentGenerator

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

class ResearchPaperGenerator:
    """
    Service to generate research papers from code repositories
    using the Gemini AI model.
    """
    
    def __init__(self):
        # Initialize the required services directly
        self.gemini_generator = GeminiGenerator()
        self.github_processor = GitHubProcessor()
        self.content_generator = ContentGenerator()
        
    async def generate_research_paper(self, topic: str, sections: Optional[List[str]] = None, 
                                     word_count: int = 3000, repo_url: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a research paper based on a topic and optionally a GitHub repository.
        
        Args:
            topic: The topic of the research paper
            sections: List of sections to include in the paper
            word_count: Target word count for the paper
            repo_url: Optional GitHub repository URL
            
        Returns:
            Dictionary with paper sections
        """
        try:
            logger.info(f"Generating research paper on topic: {topic}")
            
            # Use default sections if none provided
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
            
            # Convert sections to lowercase for consistent handling
            sections = [section.lower() for section in sections]
            
            # Explicitly remove any "code_analysis" section
            if "code_analysis" in sections:
                sections.remove("code_analysis")
            
            result = {}
            
            # If repo_url is provided, analyze code repository
            if repo_url:
                logger.info(f"Analyzing GitHub repository: {repo_url}")
                
                # Clone the repository
                repo_path = await self.github_processor.clone_repository(repo_url)
                
                try:
                    # Read repository files
                    code_files = await self.github_processor.read_repository_files(repo_path)
                    
                    # Get repository metadata
                    repo_metadata = await self.github_processor.get_repository_metadata(repo_url)
                    
                    # Divide code into chunks for processing
                    code_chunks = await self.gemini_generator.divide_code_into_chunks(code_files)
                    
                    # Create a strong prompt that absolutely prohibits code snippets and analysis
                    system_prompt = """You are generating a formal IEEE-style academic research paper based on a software repository.
                    
                    EXTREMELY IMPORTANT INSTRUCTIONS - You MUST follow these exactly:
                    1. DO NOT include ANY code snippets whatsoever in your response
                    2. DO NOT include a "Code Analysis" section or any similar section
                    3. DO NOT analyze or describe individual files, functions, or code fragments
                    4. Focus ONLY on high-level architectural concepts, design patterns, and software engineering principles
                    5. Structure your response like a traditional academic paper with ONLY the standard sections
                    6. Your analysis should focus on architectural patterns, not implementation details
                    
                    Your paper should exclusively discuss software engineering concepts, principles, and architectural patterns."""
                    
                    # Generate each section with strict no-code instructions
                    for section in sections:
                        # Skip if trying to generate a code analysis section
                        if section in ["code_analysis", "code analysis", "implementation"]:
                            continue
                            
                        # Create section-specific instruction
                        section_instruction = f"""Generate the {section} section for an IEEE research paper about the repository.
                        
                        EXTREMELY IMPORTANT: 
                        - DO NOT include ANY code snippets
                        - DO NOT include file-by-file analysis
                        - DO NOT mention specific variable names, function names, or code details
                        - Focus ONLY on high-level architectural concepts and software engineering principles
                        
                        Write this section like a traditional academic paper focusing on concepts, not code."""
                        
                        # Prepare repository metadata for Gemini
                        repo_info = f"""
                        Repository Name: {repo_metadata.get('name', 'Unknown')}
                        Repository Owner: {repo_metadata.get('owner', 'Unknown')}
                        Description: {repo_metadata.get('description', 'No description')}
                        Stars: {repo_metadata.get('stars', 0)}
                        Primary Language: {repo_metadata.get('language', 'Unknown')}
                        Created: {repo_metadata.get('created_at', 'Unknown')}
                        Last Updated: {repo_metadata.get('updated_at', 'Unknown')}
                        """
                        
                        # Special handling for references section to ensure IEEE format
                        if section == "references":
                            refs_instruction = f"""Generate the references section for an IEEE research paper about software architecture and engineering.
                            Format the references in proper IEEE format. For example:
                            [1] Author(s), "Title of paper," in Title of Published Proceedings, Year, pp. pages.
                            [2] Author(s), Title of Book. City, State: Publisher, Year.
                            
                            Include the GitHub repository as the first reference. Then include relevant software engineering references.
                            DO NOT make up fake citations - use only legitimate, well-known software engineering books and papers.
                            """
                            
                            result[section] = await self.gemini_generator._generate_with_gemini(
                                "You are a bibliography generator for IEEE papers. You create proper IEEE format references.",
                                f"{refs_instruction}\n\nRepository: {repo_url}\nNo code snippets allowed."
                            )
                        else:
                            # Call Gemini with the strong no-code prompt
                            result[section] = await self.gemini_generator._generate_with_gemini(
                                system_prompt, 
                                f"{section_instruction}\n\nRepository Metadata:\n{repo_info}\n\nRemember: NO code snippets or analysis."
                            )
                            
                finally:
    # Clean up temporary directory
                        if os.path.exists(repo_path):
                                try:
            # Use the github_processor's safe_rmtree method
                                    self.github_processor.safe_rmtree(repo_path)
                                except Exception as cleanup_error:
                                 logger.warning(f"Failed to clean up temporary directory: {str(cleanup_error)}")
            else:
                # Generate a research paper based only on the topic
                logger.info(f"Generating research paper based only on topic (no repository): {topic}")
                
                # For topic-only generation with no code
                combined_prompt = f"Generate a research paper on the topic: {topic}. "
                combined_prompt += f"Include the following sections: {', '.join(sections)}. "
                combined_prompt += f"The paper should be approximately {word_count} words. "
                combined_prompt += f"DO NOT include code snippets or a 'Code Analysis' section. "
                combined_prompt += f"This should be a formal academic paper in IEEE format."
                
                # Use content generator to generate the paper
                system_prompt = "You are a research paper generator that creates comprehensive, "
                system_prompt += "well-structured academic papers on a given topic in IEEE format. "
                system_prompt += "Focus on traditional academic writing, following a formal structure with "
                system_prompt += "Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, and References. "
                system_prompt += "DO NOT include code snippets or implementation details."
                
                try:
                    # Use the Gemini generator through the ContentGenerator wrapper
                    response = await self.gemini_generator._generate_with_gemini(system_prompt, combined_prompt)
                    
                    # Parse the response into sections
                    # This is a simple implementation; in production, you might want more robust parsing
                    current_section = None
                    for line in response.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Check if this line is a section header
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
                    
                    # Ensure all sections are present
                    for section in sections:
                        if section not in result:
                            result[section] = f"Content for {section} section."
                except Exception as e:
                    logger.error(f"Error generating paper with Gemini: {str(e)}")
                    raise
            
            # Format the result to have standardized section names (with first letter capitalized)
            formatted_result = {}
            
            # Define the exact order of sections for the paper
            section_order = ["abstract", "introduction", "literature_review", "methodology", 
                            "results", "discussion", "conclusion", "references"]
            
            for section in section_order:
                if section in result:
                    # Convert section_name to Section Name format
                    formatted_section = ' '.join(word.capitalize() for word in section.split('_'))
                    formatted_result[formatted_section] = result[section]
                else:
                    # Provide placeholder for missing sections
                    formatted_section = ' '.join(word.capitalize() for word in section.split('_'))
                    formatted_result[formatted_section] = f"This {formatted_section} section was not generated."
            
            # Add IEEE header with repository information
            ieee_header = "## IEEE Conference Paper\n\n"
            
            if repo_url:
                # Extract repo owner and name from URL
                parts = repo_url.rstrip('/').split('/')
                owner = parts[-2] if len(parts) >= 2 else "Unknown"
                repo_name = parts[-1] if len(parts) >= 1 else "Unknown"
                
                ieee_header += f"**Repository**: {owner}/{repo_name}\n"
            else:
                ieee_header += f"**Topic**: {topic}\n"
                
            ieee_header += f"**Date**: {datetime.now().strftime('%B %d, %Y')}\n"
            
            if repo_url:
                ieee_header += f"**URL**: {repo_url}\n\n"
                
            # Add a full paper representation that combines all sections
            full_paper = f"# Research Paper: {topic}\n\n{ieee_header}"
            
            for section in section_order:
                if section in result:
                    formatted_section = ' '.join(word.capitalize() for word in section.split('_'))
                    full_paper += f"## {formatted_section}\n\n{result[section]}\n\n"
            
            formatted_result["Full Paper"] = full_paper
            
            return formatted_result
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error generating research paper: {str(e)}\n{error_traceback}")
            raise

# Initialize the generator
generator = ResearchPaperGenerator()

@router.post("/generate-paper")
async def generate_research_paper(request_data: dict):
    """
    API endpoint to generate a research paper based on a topic and optional repository.
    
    Request body:
    - topic: The topic of the research paper
    - sections: List of sections to include
    - wordCount: Target word count for the paper
    - repoUrl: Optional GitHub repository URL (primary)
    - sourceUrl: Optional GitHub repository URL (fallback)
    
    Returns:
    - Dictionary with paper sections
    """
    try:
        # Extract request parameters
        topic = request_data.get("topic")
        sections = request_data.get("sections", [])
        word_count = request_data.get("wordCount", 3000)
        
        # Check both repoUrl and sourceUrl for GitHub repository
        repo_url = request_data.get("repoUrl") 
        if not repo_url and request_data.get("sourceType") == "github":
            repo_url = request_data.get("sourceUrl")
        
        # Validate required parameters
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")
            
        # Generate the research paper
        paper = await generator.generate_research_paper(
            topic=topic,
            sections=sections,
            word_count=word_count,
            repo_url=repo_url
        )
        
        return {"paper": paper}
    except Exception as e:
        logger.error(f"Error in generate_research_paper endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))