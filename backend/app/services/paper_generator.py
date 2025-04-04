import aiohttp
import asyncio
import logging
from urllib.parse import urlparse
import re
import base64
import os
from datetime import datetime
from app.utils.url_validator import URLValidator
from app.utils.cache import github_repo_cache

# Setup logging
logger = logging.getLogger(__name__)

class GitHubPaperGenerator:
    """Service to analyze GitHub repositories and generate research papers."""
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")  # Set your GitHub token in env
        
    async def fetch_repo_data(self, repo_url):
        """Fetch repository data from GitHub API."""
        try:
            # Validate URL format
            if not URLValidator.is_valid_github_url(repo_url):
                raise ValueError("Invalid GitHub repository URL format")
                
            # Check cache first
            cache_key = f"github_repo:{repo_url}"
            cached_data = github_repo_cache.get(cache_key)
            if cached_data:
                logger.info(f"Using cached data for repository: {repo_url}")
                return cached_data
                
            # Extract owner and repo from URL
            owner, repo = URLValidator.extract_github_info(repo_url)
            if not owner or not repo:
                raise ValueError("Could not extract repository information from URL")
            
            # Prepare headers for GitHub API
            headers = {
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Add token if available for higher rate limits
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
                
            # Fetch repository info
            async with aiohttp.ClientSession() as session:
                # Get repository metadata
                repo_url = f"https://api.github.com/repos/{owner}/{repo}"
                logger.info(f"Fetching repo metadata from: {repo_url}")
                
                async with session.get(repo_url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"GitHub API error: {error_text}")
                        raise ValueError(f"Failed to fetch repository info: {response.status}")
                    
                    repo_data = await response.json()
                
                # First, determine the default branch
                default_branch = repo_data.get("default_branch", "main")
                logger.info(f"Repository default branch: {default_branch}")
                
                # Get repository content (file tree)
                contents_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
                logger.info(f"Fetching repo contents from: {contents_url}")
                
                try:
                    async with session.get(contents_url, headers=headers) as response:
                        if response.status != 200:
                            # Try common branch names if default branch fails
                            common_branches = ["main", "master", "develop", "dev"]
                            contents_data = None
                            
                            for branch in common_branches:
                                if branch == default_branch:
                                    continue  # Already tried this branch
                                    
                                branch_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
                                logger.info(f"Trying alternative branch: {branch_url}")
                                
                                async with session.get(branch_url, headers=headers) as branch_response:
                                    if branch_response.status == 200:
                                        contents_data = await branch_response.json()
                                        logger.info(f"Successfully found content in branch: {branch}")
                                        break
                                        
                            # If we still don't have content, try getting contents directly
                            if not contents_data:
                                direct_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
                                logger.info(f"Trying direct contents endpoint: {direct_url}")
                                
                                async with session.get(direct_url, headers=headers) as direct_response:
                                    if direct_response.status == 200:
                                        direct_content = await direct_response.json()
                                        # Format direct content to match tree structure
                                        contents_data = {
                                            "tree": [
                                                {
                                                    "path": item.get("path", ""),
                                                    "type": "blob" if item.get("type") == "file" else "tree",
                                                    "url": item.get("url", "")
                                                }
                                                for item in direct_content if isinstance(item, dict)
                                            ]
                                        }
                                    else:
                                        error_text = await direct_response.text()
                                        logger.warning(f"GitHub API error for direct contents: {error_text}")
                                        # Create a minimal structure for empty repositories
                                        contents_data = {"tree": []}
                        else:
                            contents_data = await response.json()
                except Exception as e:
                    logger.error(f"Error fetching repository contents: {str(e)}")
                    # Create a minimal structure for repositories we can't access fully
                    contents_data = {"tree": []}
                
                # Get repository languages
                langs_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
                logger.info(f"Fetching repo languages from: {langs_url}")
                
                async with session.get(langs_url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"GitHub API error for languages: {error_text}")
                        raise ValueError(f"Failed to fetch repository languages: {response.status}")
                    
                    languages_data = await response.json()
                
                # Fetch up to 5 recent commits
                commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=5"
                logger.info(f"Fetching repo commits from: {commits_url}")
                
                async with session.get(commits_url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"GitHub API error for commits: {error_text}")
                        raise ValueError(f"Failed to fetch repository commits: {response.status}")
                    
                    commits_data = await response.json()
                
                # Get README content if it exists
                readme_content = await self._fetch_readme(session, owner, repo, headers)
                
                # Sample a few important files based on extension
                sampled_files = await self._sample_important_files(session, owner, repo, contents_data, headers)
                
            # Combine all data
            result = {
                "metadata": repo_data,
                "languages": languages_data,
                "commits": commits_data,
                "readme": readme_content,
                "sampled_files": sampled_files
            }
            
            # Cache the result
            cache_key = f"github_repo:{repo_url}"
            github_repo_cache.set(cache_key, result)
            
            return result
                
        except Exception as e:
            logger.error(f"Error fetching repository data: {str(e)}")
            raise
            
    async def _fetch_readme(self, session, owner, repo, headers):
        """Fetch the README file if it exists."""
        try:
            readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            async with session.get(readme_url, headers=headers) as response:
                if response.status != 200:
                    logger.info(f"No README found for {owner}/{repo}")
                    return None
                
                readme_data = await response.json()
                content = readme_data.get("content", "")
                if content:
                    return base64.b64decode(content).decode('utf-8', errors='ignore')
                return None
        except Exception as e:
            logger.error(f"Error fetching README: {str(e)}")
            return None
            
    async def _sample_important_files(self, session, owner, repo, contents_data, headers):
        """Sample a few important files from the repository."""
        try:
            # Filter to only include actual files (not directories)
            files = [item for item in contents_data.get("tree", []) if item.get("type") == "blob"]
            
            # Prioritize important files based on patterns
            important_patterns = [
                r'\.py$',      # Python files
                r'\.js$',      # JavaScript files
                r'\.java$',    # Java files
                r'\.cpp$',     # C++ files
                r'\.go$',      # Go files
                r'\.rs$',      # Rust files
                r'\.rb$',      # Ruby files
                r'\.php$',     # PHP files
                r'\.html$',    # HTML files
                r'\.css$',     # CSS files
                r'\.json$',    # JSON files
                r'\.xml$',     # XML files
                r'\.md$',      # Markdown files
                r'\.yaml$|\.yml$', # YAML files
                r'Dockerfile$', # Docker files
                r'Makefile$',   # Makefiles
            ]
            
            important_files = []
            for pattern in important_patterns:
                matches = [f for f in files if re.search(pattern, f.get("path", ""))]
                important_files.extend(matches[:2])  # Take up to 2 files of each type
                
            # Take up to 5 files total
            sampled_files = important_files[:5]
            
            # Fetch content for each file
            result = []
            for file in sampled_files:
                file_path = file.get("path")
                if not file_path:
                    continue
                    
                content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
                async with session.get(content_url, headers=headers) as response:
                    if response.status != 200:
                        continue
                        
                    file_data = await response.json()
                    content = file_data.get("content", "")
                    if content:
                        decoded_content = base64.b64decode(content).decode('utf-8', errors='ignore')
                        result.append({
                            "path": file_path,
                            "content": decoded_content[:2000]  # Limit content size
                        })
            
            return result
            
        except Exception as e:
            logger.error(f"Error sampling important files: {str(e)}")
            return []
            
    def _analyze_repo_structure(self, repo_data):
        """Analyze repository structure and extract key information."""
        try:
            # Extract basic repository metadata
            metadata = repo_data["metadata"]
            languages = repo_data["languages"]
            commits = repo_data["commits"]
            readme = repo_data["readme"]
            sampled_files = repo_data["sampled_files"]
            
            # Basic repository info
            repo_info = {
                "name": metadata.get("name", "Unknown"),
                "full_name": metadata.get("full_name", "Unknown"),
                "description": metadata.get("description", "No description available"),
                "stars": metadata.get("stargazers_count", 0),
                "forks": metadata.get("forks_count", 0),
                "watchers": metadata.get("watchers_count", 0),
                "created_at": metadata.get("created_at", "Unknown"),
                "updated_at": metadata.get("updated_at", "Unknown"),
                "license": metadata.get("license", {}).get("name", "Unknown"),
                "language_stats": languages,
                "primary_language": next(iter(languages)) if languages else "Unknown"
            }
            
            # Analyze commit history
            commit_history = []
            for commit in commits:
                commit_data = {
                    "sha": commit.get("sha", ""),
                    "message": commit.get("commit", {}).get("message", "No message"),
                    "author": commit.get("commit", {}).get("author", {}).get("name", "Unknown"),
                    "date": commit.get("commit", {}).get("author", {}).get("date", "Unknown")
                }
                commit_history.append(commit_data)
                
            # Analyze directory structure
            directory_structure = self._extract_directory_structure(repo_data["contents_data"]["tree"] if "contents_data" in repo_data else [])
            
            # Extract key features from README
            readme_summary = self._summarize_readme(readme) if readme else "No README available"
            
            # Analyze code samples
            code_analysis = []
            for file in sampled_files:
                code_analysis.append({
                    "file": file["path"],
                    "summary": self._summarize_code_file(file["path"], file["content"])
                })
                
            return {
                "repo_info": repo_info,
                "commit_history": commit_history,
                "directory_structure": directory_structure,
                "readme_summary": readme_summary,
                "code_analysis": code_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing repository structure: {str(e)}")
            return {}
    
    def _extract_directory_structure(self, tree_items):
        """Extract and categorize directory structure from the repository."""
        directories = {}
        
        for item in tree_items:
            path = item.get("path", "")
            if not path:
                continue
                
            parts = path.split("/")
            current = directories
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1 and item.get("type") == "blob":
                    # It's a file
                    if "__files__" not in current:
                        current["__files__"] = []
                    current["__files__"].append(part)
                else:
                    # It's a directory
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                    
        return directories
        
    def _summarize_readme(self, readme_content):
        """Extract key points from README content."""
        if not readme_content:
            return "No README available"
            
        # Extract sections
        sections = re.split(r'#+\s+', readme_content)
        sections = [s.strip() for s in sections if s.strip()]
        
        # If README is too long, just take first part and sections
        if len(sections) > 3:
            summary = f"README contains {len(sections)} sections including: " + ", ".join(
                re.match(r'^(.*?)(\n|$)', s).group(1) for s in sections[:5] if re.match(r'^(.*?)(\n|$)', s)
            )
        else:
            # Take first 500 chars as summary
            summary = readme_content[:500] + ("..." if len(readme_content) > 500 else "")
            
        return summary
        
    def _summarize_code_file(self, file_path, content):
        """Generate a basic summary of a code file."""
        # Extract file extension
        ext = file_path.split(".")[-1] if "." in file_path else ""
        
        # Count lines
        lines = content.split("\n")
        line_count = len(lines)
        
        # Look for patterns based on file type
        if ext in ["py", "js", "java", "cpp", "go", "rs", "rb", "php"]:
            # Look for class/function definitions
            classes = re.findall(r'class\s+(\w+)', content)
            functions = re.findall(r'(?:function|def|func)\s+(\w+)', content)
            
            summary = f"{file_path}: {line_count} lines of code. "
            if classes:
                summary += f"Contains {len(classes)} classes: {', '.join(classes[:3])}{'...' if len(classes) > 3 else ''}. "
            if functions:
                summary += f"Contains {len(functions)} functions: {', '.join(functions[:5])}{'...' if len(functions) > 5 else ''}."
                
            return summary
        else:
            # Generic summary for other file types
            return f"{file_path}: {line_count} lines of code."
    
    async def generate_research_paper(self, topic, repo_url, sections=None):
        """Generate a research paper based on GitHub repository analysis."""
        try:
            logger.info(f"Generating research paper for: {repo_url}")
            
            # Fetch repository data
            try:
                repo_data = await self.fetch_repo_data(repo_url)
            except Exception as e:
                logger.error(f"Error fetching repository data: {str(e)}")
                # Return a paper with error information
                return self._generate_error_paper(topic, repo_url, str(e), sections)
            
            # Extract repository metadata (with fallbacks for missing data)
            metadata = repo_data.get("metadata", {})
            languages = repo_data.get("languages", {})
            readme = repo_data.get("readme")
            sampled_files = repo_data.get("sampled_files", [])
            
            # Default sections if none provided
            if not sections:
                sections = [
                    "Abstract",
                    "Introduction",
                    "Literature Review",
                    "Methodology",
                    "Results",
                    "Discussion",
                    "Conclusion",
                    "References"
                ]
                
            # Generate paper content
            paper_content = f"# {metadata.get('name', 'Repository Analysis')}: {topic}\n\n"
            
            # Add IEEE-style metadata
            paper_content += "## IEEE Conference Paper\n\n"
            paper_content += f"**Repository**: {metadata.get('full_name', 'Unknown')}\n"
            paper_content += f"**Date**: {datetime.now().strftime('%B %d, %Y')}\n"
            paper_content += f"**URL**: {repo_url}\n\n"
            
            # Add abstract
            paper_content += "## Abstract\n\n"
            paper_content += f"This paper analyzes the software architecture and implementation of {metadata.get('name', 'the repository')}, "
            paper_content += f"a {next(iter(languages)) if languages else 'software'} project "
            paper_content += f"with {metadata.get('stargazers_count', 0)} stars on GitHub. "
            paper_content += f"{metadata.get('description', '')} "
            paper_content += "The analysis explores the codebase structure, architectural patterns, "
            paper_content += "implementation details, and potential applications. "
            paper_content += "This research provides insights into software engineering practices "
            paper_content += f"employed in {metadata.get('name', 'this repository')}.\n\n"
            
            # Add introduction
            paper_content += "## Introduction\n\n"
            paper_content += f"{metadata.get('name', 'This repository')} is "
            if metadata.get('description'):
                paper_content += f"described as '{metadata.get('description')}'. "
            paper_content += f"Created on {metadata.get('created_at', 'unknown date')}, "
            paper_content += f"it has garnered attention with {metadata.get('stargazers_count', 0)} stars and "
            paper_content += f"{metadata.get('forks_count', 0)} forks. "
            
            # Add language information
            if languages:
                total_bytes = sum(languages.values())
                lang_percentages = {k: (v / total_bytes) * 100 for k, v in languages.items()}
                top_languages = sorted(lang_percentages.items(), key=lambda x: x[1], reverse=True)[:3]
                
                paper_content += "The codebase primarily utilizes "
                if len(top_languages) == 1:
                    paper_content += f"{top_languages[0][0]} (100%). "
                else:
                    lang_description = ", ".join([f"{lang} ({percentage:.1f}%)" for lang, percentage in top_languages])
                    paper_content += f"a combination of {lang_description}. "
                    
            # Add README summary if available
            if readme:
                paper_content += "\n\nFrom the project README:\n\n"
                paper_content += "> " + "\n> ".join(readme.split("\n")[:10])
                if len(readme.split("\n")) > 10:
                    paper_content += "\n> ..."
                paper_content += "\n\n"
                
            # Add methodology
            paper_content += "## Methodology\n\n"
            paper_content += "This research paper employs static code analysis techniques to examine "
            paper_content += f"the structure and patterns within {metadata.get('name', 'the repository')}. "
            paper_content += "The methodology includes:\n\n"
            paper_content += "1. Repository structure analysis\n"
            paper_content += "2. Programming language composition assessment\n"
            paper_content += "3. Code organization patterns identification\n"
            paper_content += "4. Examination of key components and their interactions\n"
            paper_content += "5. Analysis of API design and implementation\n\n"
            
            # Add file analysis
            if sampled_files:
                paper_content += "## Code Analysis\n\n"
                paper_content += "The following key files were analyzed to understand the system architecture:\n\n"
                
                for file in sampled_files:
                    paper_content += f"### {file['path']}\n\n"
                    
                    # Add file content snippet
                    paper_content += "```\n"
                    # Limit code snippet to a reasonable size
                    lines = file['content'].split('\n')[:50]
                    paper_content += "\n".join(lines)
                    if len(file['content'].split('\n')) > 50:
                        paper_content += "\n..."
                    paper_content += "\n```\n\n"
                    
                    # Add brief analysis
                    paper_content += "This file "
                    if file['path'].endswith('.py'):
                        paper_content += "contains Python code "
                        # Look for classes and functions
                        classes = re.findall(r'class\s+(\w+)', file['content'])
                        functions = re.findall(r'def\s+(\w+)', file['content'])
                        
                        if classes:
                            paper_content += f"with {len(classes)} classes"
                            if functions:
                                paper_content += f" and {len(functions)} functions. "
                            else:
                                paper_content += ". "
                        elif functions:
                            paper_content += f"with {len(functions)} functions. "
                            
                    elif file['path'].endswith('.js') or file['path'].endswith('.jsx'):
                        paper_content += "implements JavaScript functionality "
                        functions = re.findall(r'function\s+(\w+)', file['content'])
                        if functions:
                            paper_content += f"with {len(functions)} named functions. "
                        
                    paper_content += "The code demonstrates "
                    
                    # Add some generic analysis based on file type
                    if 'test' in file['path'].lower():
                        paper_content += "testing implementation for ensuring code quality. "
                    elif 'model' in file['path'].lower():
                        paper_content += "data modeling and structure definitions. "
                    elif 'view' in file['path'].lower() or 'component' in file['path'].lower():
                        paper_content += "UI rendering and user interface components. "
                    elif 'controller' in file['path'].lower() or 'service' in file['path'].lower():
                        paper_content += "business logic and service implementation. "
                    elif 'util' in file['path'].lower() or 'helper' in file['path'].lower():
                        paper_content += "utility functions and helper methods. "
                    else:
                        paper_content += "core functionality of the application. "
                        
                    paper_content += "\n\n"
            
            # Add results/discussion
            paper_content += "## Results and Discussion\n\n"
            paper_content += f"The analysis of {metadata.get('name', 'the repository')} reveals several key findings:\n\n"
            
            # Add architecture observations
            paper_content += "### Architecture\n\n"
            if any('component' in file['path'].lower() for file in sampled_files):
                paper_content += "The codebase employs a component-based architecture, "
                paper_content += "separating functionality into reusable components. "
            elif any('controller' in file['path'].lower() and 'model' in file['path'].lower() for file in sampled_files):
                paper_content += "The project follows an MVC (Model-View-Controller) pattern, "
                paper_content += "separating data, business logic, and presentation concerns. "
            elif any('service' in file['path'].lower() for file in sampled_files):
                paper_content += "The system utilizes a service-oriented architecture, "
                paper_content += "with clearly defined service boundaries. "
            else:
                paper_content += "The code demonstrates a modular structure with separation of concerns. "
                
            # Add language-specific observations
            dominant_language = next(iter(languages)) if languages else None
            if dominant_language:
                paper_content += f"\n\n### {dominant_language} Implementation\n\n"
                if dominant_language == "JavaScript":
                    paper_content += "The JavaScript implementation "
                    if any('react' in file['content'].lower() or 'component' in file['content'].lower() for file in sampled_files):
                        paper_content += "utilizes React for frontend development, with component-based UI architecture. "
                    elif any('node' in file['content'].lower() or 'express' in file['content'].lower() for file in sampled_files):
                        paper_content += "employs Node.js with Express for server-side functionality. "
                    else:
                        paper_content += "demonstrates modern JavaScript patterns and practices. "
                elif dominant_language == "Python":
                    paper_content += "The Python implementation "
                    if any('flask' in file['content'].lower() for file in sampled_files):
                        paper_content += "uses Flask for web service functionality. "
                    elif any('django' in file['content'].lower() for file in sampled_files):
                        paper_content += "is built on Django, providing a robust web framework foundation. "
                    else:
                        paper_content += "follows Pythonic principles and coding standards. "
                        
            # Add quality observations
            paper_content += "\n\n### Code Quality\n\n"
            has_tests = any('test' in file['path'].lower() for file in sampled_files)
            if has_tests:
                paper_content += "The presence of test files indicates a commitment to code quality and reliability. "
            else:
                paper_content += "The codebase could benefit from more comprehensive test coverage. "
                
            # Add documentation observations
            paper_content += "Documentation is "
            if readme and len(readme) > 500:
                paper_content += "fairly comprehensive, with detailed README information. "
            else:
                paper_content += "present but could be expanded with more detailed implementation information. "
                
            # Add conclusion
            paper_content += "\n\n## Conclusion\n\n"
            paper_content += f"This analysis of {metadata.get('name', 'the repository')} provides insights into "
            paper_content += "modern software development practices and architectural patterns. "
            paper_content += f"With {metadata.get('stargazers_count', 0)} stars and {metadata.get('forks_count', 0)} forks, "
            paper_content += "the project demonstrates significant community interest. "
            paper_content += "The codebase exhibits "
            
            if languages and len(languages) > 3:
                paper_content += "a diverse technology stack, "
            else:
                paper_content += f"focused use of {dominant_language if dominant_language else 'programming languages'}, "
                
            if has_tests:
                paper_content += "with attention to testing and quality control. "
            else:
                paper_content += "with opportunities for enhanced testing coverage. "
                
            paper_content += "\n\nFuture research could explore performance optimizations, security aspects, "
            paper_content += "or comparative analysis with similar projects in the domain."
            
            # Add references
            paper_content += "\n\n## References\n\n"
            paper_content += f"1. {metadata.get('full_name', 'Repository')}, GitHub, {repo_url}\n"
            paper_content += "2. IEEE Standard for Software Engineering, IEEE Std 1016-2009\n"
            paper_content += "3. C. Northrop, \"Software Architecture in Practice,\" Addison-Wesley, 2012\n"
            paper_content += "4. M. Fowler, \"Patterns of Enterprise Application Architecture,\" Addison-Wesley, 2002\n"
            paper_content += "5. R. Martin, \"Clean Code: A Handbook of Agile Software Craftsmanship,\" Prentice Hall, 2008\n"
            
            return paper_content
            
        except Exception as e:
            logger.error(f"Error generating research paper: {str(e)}")
            return self._generate_error_paper(topic, repo_url, str(e), sections)
            
    def _generate_error_paper(self, topic, repo_url, error_message, sections=None):
        """Generate a paper with error information that's still useful to the user."""
        
        # Default sections if none provided
        if not sections:
            sections = [
                "Abstract",
                "Introduction",
                "Methodology",
                "Limitations",
                "Conclusion"
            ]
        
        # Extract owner/repo from URL if possible
        repo_parts = repo_url.split('/')
        repo_name = repo_parts[-1] if len(repo_parts) >= 1 else "repository"
        owner_name = repo_parts[-2] if len(repo_parts) >= 2 else "owner"
        
        # Generate paper content with error information
        paper_content = f"# Limited Analysis of {owner_name}/{repo_name}\n\n"
        
        # Add IEEE-style metadata
        paper_content += "## IEEE Conference Paper\n\n"
        paper_content += f"**Repository**: {owner_name}/{repo_name}\n"
        paper_content += f"**Date**: {datetime.now().strftime('%B %d, %Y')}\n"
        paper_content += f"**URL**: {repo_url}\n\n"
        
        # Add notice about limited analysis
        paper_content += "## ⚠️ Limited Repository Analysis\n\n"
        paper_content += f"This paper provides a limited analysis of the repository due to data access constraints. "
        paper_content += f"The following error was encountered: **{error_message}**\n\n"
        paper_content += "The analysis below is based on available repository metadata and general "
        paper_content += "software engineering principles relevant to similar repositories.\n\n"
        
        # Add abstract
        paper_content += "## Abstract\n\n"
        paper_content += f"This paper attempts to analyze the software architecture and implementation of {repo_name}, "
        paper_content += f"a project hosted on GitHub. While complete repository data was not accessible due to "
        paper_content += f"technical limitations, this analysis provides valuable insights into software engineering "
        paper_content += f"considerations for similar projects. This research examines potential architectural patterns, "
        paper_content += f"implementation approaches, and development practices that would be relevant for {repo_name}.\n\n"
        
        # Add introduction
        paper_content += "## Introduction\n\n"
        paper_content += f"GitHub repositories like {owner_name}/{repo_name} represent the modern approach to "
        paper_content += "collaborative software development. While this specific repository's contents could not be "
        paper_content += "fully accessed, we can still explore the broader context of software engineering approaches "
        paper_content += "that would apply to similar projects.\n\n"
        paper_content += "GitHub repositories typically contain source code, documentation, configuration files, "
        paper_content += "and other assets necessary for software development. They facilitate version control, "
        paper_content += "collaboration, issue tracking, and continuous integration/deployment.\n\n"
        
        # Add methodology section with limitations
        paper_content += "## Methodology and Limitations\n\n"
        paper_content += "This research faced significant limitations in data collection. The standard methodology "
        paper_content += "would involve:\n\n"
        paper_content += "1. Repository structure analysis\n"
        paper_content += "2. Programming language composition assessment\n"
        paper_content += "3. Code organization patterns identification\n"
        paper_content += "4. Examination of key components and their interactions\n\n"
        
        paper_content += "However, due to access constraints, a modified approach was necessary. This paper "
        paper_content += "instead focuses on:\n\n"
        paper_content += "1. General software engineering principles applicable to GitHub projects\n"
        paper_content += "2. Common architectural patterns in modern software development\n"
        paper_content += "3. Best practices for repository organization and management\n"
        paper_content += "4. Theoretical analysis based on repository metadata\n\n"
        
        # Add general best practices
        paper_content += "## Software Engineering Best Practices\n\n"
        paper_content += "While specific details of the repository cannot be analyzed, we can discuss "
        paper_content += "software engineering best practices that should be applied to all repositories:\n\n"
        
        paper_content += "### Code Organization\n\n"
        paper_content += "Well-structured repositories typically organize code into logical modules or packages. "
        paper_content += "This separation of concerns improves maintainability and allows different team members "
        paper_content += "to work on separate components simultaneously.\n\n"
        
        paper_content += "### Documentation\n\n"
        paper_content += "Comprehensive documentation is essential for any software project. This includes:\n\n"
        paper_content += "- README files explaining project purpose and setup\n"
        paper_content += "- API documentation for developers\n"
        paper_content += "- Architecture diagrams showing component relationships\n"
        paper_content += "- Code comments explaining complex implementations\n\n"
        
        paper_content += "### Testing\n\n"
        paper_content += "Robust testing strategies are critical for maintaining software quality. These typically include:\n\n"
        paper_content += "- Unit tests for individual functions and methods\n"
        paper_content += "- Integration tests for component interactions\n"
        paper_content += "- End-to-end tests simulating user workflows\n"
        paper_content += "- Performance tests ensuring system efficiency\n\n"
        
        # Add conclusion
        paper_content += "## Conclusion\n\n"
        paper_content += f"While this analysis of {owner_name}/{repo_name} faced significant limitations in data access, "
        paper_content += "it highlights the importance of software engineering principles in GitHub-based development. "
        paper_content += "Future research could address these limitations by working directly with repository maintainers "
        paper_content += "to gain proper access for analysis.\n\n"
        paper_content += "The theoretical framework presented here provides valuable insights for developers "
        paper_content += "working on similar projects, emphasizing code organization, documentation, and testing "
        paper_content += "as pillars of successful software development.\n\n"
        
        # Add references
        paper_content += "## References\n\n"
        paper_content += f"1. {owner_name}/{repo_name}, GitHub, {repo_url}\n"
        paper_content += "2. IEEE Standard for Software Engineering, IEEE Std 1016-2009\n"
        paper_content += "3. C. Northrop, \"Software Architecture in Practice,\" Addison-Wesley, 2012\n"
        paper_content += "4. M. Fowler, \"Patterns of Enterprise Application Architecture,\" Addison-Wesley, 2002\n"
        paper_content += "5. R. Martin, \"Clean Code: A Handbook of Agile Software Craftsmanship,\" Prentice Hall, 2008\n"
        
        return paper_content