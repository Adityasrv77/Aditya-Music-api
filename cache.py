import time
from functools import wraps

# Simple in-memory cache
cache_store = {}

def cache_response(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            if key in cache_store:
                cached_data, timestamp = cache_store[key]
                if time.time() - timestamp < ttl:
                    return cached_data
            
            result = func(*args, **kwargs)
            cache_store[key] = (result, time.time())
            return result
        return wrapper
    return decorator

def clear_cache():
    """Clear all cached data"""
    cache_store.clear()
