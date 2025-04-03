# backend/app/services/github_processor.py
import os
import git
from pathlib import Path
import shutil
from typing import List, Dict
import asyncio
import aiohttp
from github import Github
from github.Repository import Repository

class GitHubProcessor:
    def __init__(self, working_dir: str = "temp/repos"):
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)

    async def process_repository(self, repo_url: str, branch: str = "main") -> Dict:
        """Process a GitHub repository and extract relevant information."""
        repo_path = self.working_dir / self._get_repo_name(repo_url)
        
        try:
            # Clone repository
            repo = git.Repo.clone_from(repo_url, repo_path, branch=branch)
            
            # Extract repository information
            repo_info = {
                "files": self._get_repository_files(repo_path),
                "readme": self._get_readme_content(repo_path),
                "metadata": self._extract_repo_metadata(repo)
            }
            
            return repo_info
        
        finally:
            # Cleanup
            if repo_path.exists():
                shutil.rmtree(repo_path)

    def _get_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        return repo_url.rstrip("/").split("/")[-1]

    def _get_repository_files(self, repo_path: Path) -> List[Dict]:
        """Get list of files in repository with their content."""
        files = []
        for file_path in repo_path.rglob("*"):
            if file_path.is_file() and self._is_relevant_file(file_path):
                files.append({
                    "path": str(file_path.relative_to(repo_path)),
                    "content": self._read_file_content(file_path),
                    "extension": file_path.suffix
                })
        return files

    def _is_relevant_file(self, file_path: Path) -> bool:
        """Check if file is relevant for processing."""
        # Add more extensions as needed
        relevant_extensions = {
            ".py", ".java", ".cpp", ".h", ".js", ".ts",
            ".md", ".txt", ".rst", ".json", ".yaml", ".yml"
        }
        return file_path.suffix in relevant_extensions

    def _read_file_content(self, file_path: Path) -> str:
        """Read content of a file safely."""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""  # Return empty string if file can't be read

    def _get_readme_content(self, repo_path: Path) -> str:
        """Get content of README file if it exists."""
        readme_files = ["README.md", "README.rst", "README.txt"]
        for readme in readme_files:
            readme_path = repo_path / readme
            if readme_path.exists():
                return self._read_file_content(readme_path)
        return ""

    def _extract_repo_metadata(self, repo: git.Repo) -> Dict:
        """Extract metadata from repository."""
        return {
            "last_commit": str(repo.head.commit),
            "branch": repo.active_branch.name,
            "total_files": len(list(repo.tree().traverse())),
            "contributors": [{"name": c.name, "email": c.email} 
                           for c in repo.iter_commits()]
        }