import os
import tempfile
import subprocess
import shutil
from typing import Dict, List, Optional
import asyncio
import aiohttp

class GitHubProcessor:
    """Service for processing GitHub repositories"""
    
    def safe_rmtree(self, path):
        """Safely remove a directory tree, ignoring permission errors on Windows."""
        def onerror(func, error_path, exc_info):
            # Try to make the file writable and try again
            try:
                os.chmod(error_path, 0o777)
                func(error_path)
            except:
                # If still failing, just ignore
                pass
        
        try:
            shutil.rmtree(path, onerror=onerror)
        except Exception as e:
            print(f"Warning: Could not fully remove directory {path}: {str(e)}")
    
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
            # Use regular subprocess called from a thread pool
            def clone_repo():
                result = subprocess.run(
                    ["git", "clone", repo_url, temp_dir],
                    capture_output=True,
                    text=True
                )
                return result
                
            # Run in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, clone_repo)
            
            if result.returncode != 0:
                raise Exception(f"Failed to clone repository: {result.stderr}")
                
            return temp_dir
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_dir):
                self.safe_rmtree(temp_dir)
            raise Exception(f"Repository cloning error: {str(e)}")
    
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