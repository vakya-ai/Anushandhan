import re
import logging
from urllib.parse import urlparse

# Setup logging
logger = logging.getLogger(__name__)

class URLValidator:
    """URL validation utilities"""
    
    @staticmethod
    def is_valid_github_url(url):
        """
        Validates if a URL is a valid GitHub repository URL.
        
        Args:
            url (str): The URL to validate
            
        Returns:
            bool: True if valid GitHub repo URL, False otherwise
        """
        if not url:
            return False
            
        try:
            # Check if the URL is generally valid
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
                
            # Check if it's a GitHub URL
            if not ('github.com' in parsed.netloc.lower()):
                return False
                
            # Basic check for repo path format (username/repo)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                return False
                
            # Check that username and repo name follow GitHub's rules
            username, repo = path_parts[0], path_parts[1]
            
            # GitHub username validation
            if not re.match(r'^[a-zA-Z0-9][-a-zA-Z0-9]*$', username):
                return False
                
            # GitHub repo name validation
            if not re.match(r'^[a-zA-Z0-9_.-]+$', repo):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating GitHub URL: {str(e)}")
            return False
    
    @staticmethod
    def extract_github_info(url):
        """
        Extracts owner and repo name from a GitHub URL.
        
        Args:
            url (str): GitHub repository URL
            
        Returns:
            tuple: (owner, repo) or (None, None) if invalid
        """
        if not URLValidator.is_valid_github_url(url):
            return (None, None)
            
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip('/').split('/')
            return (path_parts[0], path_parts[1])
        except:
            return (None, None)