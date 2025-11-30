import time
import hashlib
from typing import Dict, Any, Optional, Tuple

class CacheService:
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size  # Limit number of items

    def _get_key(self, key_input: str) -> str:
        """Use SHA256 for better collision resistance."""
        return hashlib.sha256(key_input.encode()).hexdigest()

    def get(self, key_input: str) -> Optional[Any]:
        key = self._get_key(key_input)
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            else:
                del self._cache[key]  # Remove expired
        return None

    def set(self, key_input: str, data: Any):
        # PROTECT MEMORY: If cache is full, clear old items
        if len(self._cache) >= self._max_size:
            # Simple cleanup: Remove items older than TTL immediately
            self._cleanup_expired()
            
            # If still full, clear 20% of the cache to make room (FIFO)
            if len(self._cache) >= self._max_size:
                keys_to_remove = list(self._cache.keys())[:int(self._max_size * 0.2)]
                for k in keys_to_remove:
                    del self._cache[k]

        key = self._get_key(key_input)
        self._cache[key] = (time.time(), data)

    def _cleanup_expired(self):
        """Helper to remove expired items."""
        now = time.time()
        keys_to_delete = [k for k, v in self._cache.items() if now - v[0] >= self._ttl]
        for k in keys_to_delete:
            del self._cache[k]

    def clear(self):
        self._cache.clear()

# Global instance
# Stores max 500 items to keep RAM usage low on free tier servers
response_cache = CacheService(ttl_seconds=86400, max_size=500)