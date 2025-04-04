import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Simple in-memory cache manager with TTL (time-to-live)"""
    
    def __init__(self, default_ttl=3600):  # Default TTL: 1 hour
        """
        Initialize the cache manager.
        
        Args:
            default_ttl (int): Default time-to-live in seconds
        """
        self._cache = {}
        self._default_ttl = default_ttl
        
    def get(self, key):
        """
        Get a value from cache if it exists and hasn't expired.
        
        Args:
            key (str): Cache key
            
        Returns:
            any: Cached value or None if not found or expired
        """
        if key not in self._cache:
            return None
            
        cache_entry = self._cache[key]
        current_time = time.time()
        
        # Check if entry has expired
        if current_time > cache_entry['expires_at']:
            logger.debug(f"Cache entry expired for key: {key}")
            self._cache.pop(key, None)
            return None
            
        logger.debug(f"Cache hit for key: {key}")
        return cache_entry['value']
        
    def set(self, key, value, ttl=None):
        """
        Set a value in the cache with TTL.
        
        Args:
            key (str): Cache key
            value (any): Value to cache
            ttl (int, optional): Custom TTL in seconds
        """
        if ttl is None:
            ttl = self._default_ttl
            
        expires_at = time.time() + ttl
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        
        logger.debug(f"Cache set for key: {key}, expires in {ttl} seconds")
        
    def invalidate(self, key):
        """
        Remove a key from the cache.
        
        Args:
            key (str): Cache key to remove
        """
        if key in self._cache:
            self._cache.pop(key)
            logger.debug(f"Cache invalidated for key: {key}")
            
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.debug("Cache cleared")
        
    def cleanup(self):
        """Remove all expired entries from the cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() 
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            self._cache.pop(key)
            
        logger.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries")

# Create a global cache instance for GitHub repositories
# TTL: 1 hour (3600 seconds)
github_repo_cache = CacheManager(default_ttl=3600)