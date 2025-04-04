import os
import tempfile
import subprocess
import shutil
from typing import Dict, List, Optional
import asyncio
import aiohttp

class GitHubProcessor:
    """Service for processing GitHub repositories"""
    
    async def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        """
        Clone a GitHub repository to a temporary directory
        
        Args:
            repo_url: GitHub repository URL
            branch: Branch to clone
            
        Returns:
            Path to the cloned repository
        """
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Use asyncio subprocess to avoid blocking
            process = await asyncio.create_subprocess_exec(
                "git", "clone", "--branch", branch, "--single-branch", repo_url, temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Failed to clone repository: {stderr.decode()}")
                
            return temp_dir
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
    
    async def read_repository_files(self, repo_path: str) -> Dict[str, str]:
        """
        Read all files from the repository
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary mapping file paths to file content
        """
        result = {}
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Skip hidden files and directories
                if any(part.startswith('.') for part in relative_path.split(os.sep)):
                    continue
                    
                try:
                    # Try to read as text
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    result[relative_path] = content
                except (UnicodeDecodeError, IOError):
                    # Skip binary files
                    pass
        
        return result
    
    async def get_repository_metadata(self, repo_url: str) -> Dict[str, any]:
        """
        Get metadata about a GitHub repository
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Dictionary with repository metadata
        """
        # Extract owner and repo name from URL
        # Example: https://github.com/owner/repo
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        # GitHub API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get repository metadata: {await response.text()}")
                
                data = await response.json()
                
                return {
                    "name": data.get("name"),
                    "owner": data.get("owner", {}).get("login"),
                    "description": data.get("description"),
                    "stars": data.get("stargazers_count"),
                    "forks": data.get("forks_count"),
                    "language": data.get("language"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at")
                }