"""
Redis Cache Service for Live Logs
Provides caching for live logs per source for instant switching
"""
import os
import json
import redis
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DECODE_RESPONSES = True

# Cache configuration
MAX_CACHED_LOGS_PER_SOURCE = 5000  # Maximum logs to cache per source
LOG_CACHE_TTL = 3600  # Cache TTL in seconds (1 hour)
LOG_SOURCE_PREFIX = "logs:source:"  # Redis key prefix for log sources
LOG_ALL_KEY = "logs:source:all"  # Key for all logs


class RedisLogCache:
    """
    Redis-based cache for live logs.
    Stores logs per source for instant retrieval when switching sources.
    """
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=REDIS_DECODE_RESPONSES,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            print(f"✓ Redis connected: {REDIS_HOST}:{REDIS_PORT}")
            self.enabled = True
        except Exception as e:
            print(f"✗ Redis connection failed: {e}")
            print("! Falling back to in-memory cache")
            self.redis_client = None
            self.enabled = False
    
    def _get_key(self, log_source: str) -> str:
        """Get Redis key for a log source"""
        if log_source == "all":
            return LOG_ALL_KEY
        return f"{LOG_SOURCE_PREFIX}{log_source}"
    
    def add_log(self, log_source: str, log_data: Dict) -> bool:
        """
        Add a log to the cache for a specific source.
        
        Args:
            log_source: Source of the log (auth, ufw, kern, syslog, messages, all)
            log_data: Log data dictionary with type, log_source, raw_line, timestamp
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            key = self._get_key(log_source)
            
            # Serialize log data
            log_json = json.dumps(log_data)
            
            # Add to list (left push to maintain chronological order)
            # Use LPUSH to add to the beginning, then trim to keep only recent logs
            self.redis_client.lpush(key, log_json)
            
            # Trim list to keep only MAX_CACHED_LOGS_PER_SOURCE most recent logs
            self.redis_client.ltrim(key, 0, MAX_CACHED_LOGS_PER_SOURCE - 1)
            
            # Set TTL on the key
            self.redis_client.expire(key, LOG_CACHE_TTL)
            
            # Also add to "all" cache if not already "all"
            if log_source != "all":
                all_key = LOG_ALL_KEY
                self.redis_client.lpush(all_key, log_json)
                self.redis_client.ltrim(all_key, 0, MAX_CACHED_LOGS_PER_SOURCE - 1)
                self.redis_client.expire(all_key, LOG_CACHE_TTL)
            
            return True
        except Exception as e:
            print(f"✗ Error adding log to Redis cache: {e}")
            return False
    
    def get_logs(self, log_source: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get cached logs for a specific source.
        
        Args:
            log_source: Source of the logs to retrieve
            limit: Maximum number of logs to return (default: all cached)
        
        Returns:
            List of log dictionaries
        """
        if not self.enabled or not self.redis_client:
            return []
        
        try:
            key = self._get_key(log_source)
            
            # Get logs from Redis (LRANGE returns in reverse order of insertion)
            # We want chronological order, so we reverse
            if limit:
                logs_json = self.redis_client.lrange(key, 0, limit - 1)
            else:
                logs_json = self.redis_client.lrange(key, 0, -1)
            
            # Reverse to get chronological order (oldest first)
            logs_json.reverse()
            
            # Deserialize logs
            logs = []
            for log_json in logs_json:
                try:
                    log_data = json.loads(log_json)
                    logs.append(log_data)
                except json.JSONDecodeError:
                    continue
            
            return logs
        except Exception as e:
            print(f"✗ Error getting logs from Redis cache: {e}")
            return []
    
    def clear_cache(self, log_source: Optional[str] = None) -> bool:
        """
        Clear cache for a specific source or all sources.
        
        Args:
            log_source: Source to clear (None = clear all)
        
        Returns:
            bool: True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            if log_source:
                key = self._get_key(log_source)
                self.redis_client.delete(key)
            else:
                # Clear all log caches
                pattern = f"{LOG_SOURCE_PREFIX}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                # Also clear "all" key
                self.redis_client.delete(LOG_ALL_KEY)
            
            return True
        except Exception as e:
            print(f"✗ Error clearing Redis cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            stats = {
                "enabled": True,
                "sources": {}
            }
            
            # Get stats for each source
            sources = ["all", "auth", "ufw", "kern", "syslog", "messages"]
            for source in sources:
                key = self._get_key(source)
                count = self.redis_client.llen(key)
                ttl = self.redis_client.ttl(key)
                stats["sources"][source] = {
                    "count": count,
                    "ttl": ttl if ttl > 0 else None
                }
            
            return stats
        except Exception as e:
            print(f"✗ Error getting cache stats: {e}")
            return {"enabled": False, "error": str(e)}


# Global singleton instance
redis_log_cache = RedisLogCache()

