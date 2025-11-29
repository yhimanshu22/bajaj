import time
import hashlib
from typing import Dict, Any, Optional, Tuple

class CacheService:
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._ttl = ttl_seconds

    def _get_key(self, key_input: str) -> str:
        """Generate a consistent key."""
        return hashlib.md5(key_input.encode()).hexdigest()

    def get(self, key_input: str) -> Optional[Any]:
        """Retrieve item from cache if valid."""
        key = self._get_key(key_input)
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            else:
                del self._cache[key]  # Expired
        return None

    def set(self, key_input: str, data: Any):
        """Store item in cache."""
        key = self._get_key(key_input)
        self._cache[key] = (time.time(), data)

    def clear(self):
        self._cache.clear()

# Global instance
response_cache = CacheService(ttl_seconds=86400)  # 24 hour cache
