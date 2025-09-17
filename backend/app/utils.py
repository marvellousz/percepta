# backend/app/utils.py
import asyncio
import logging
import time
from typing import TypeVar, Callable, Any, Awaitable, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

async def retry_async(
    func: Callable[..., Awaitable[T]], 
    *args: Any, 
    retries: int = 2,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs: Any
) -> T:
    """
    Retry an async function with exponential backoff
    
    Args:
        func: The async function to retry
        *args: Arguments to pass to the function
        retries: Maximum number of retries
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function call
    """
    max_retries = retries
    current_delay = delay
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            if attempt == max_retries:
                logger.error(f"Max retries ({max_retries}) reached for {func.__name__}: {e}")
                raise
            
            logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__} failed: {e}. Retrying in {current_delay:.2f}s...")
            await asyncio.sleep(current_delay)
            current_delay *= backoff

def async_retry(retries: int = 2, delay: float = 0.5, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator to retry async functions with exponential backoff
    
    Args:
        retries: Maximum number of retries
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_async(
                func, *args, 
                retries=retries, 
                delay=delay, 
                backoff=backoff, 
                exceptions=exceptions, 
                **kwargs
            )
        return wrapper
    return decorator

class RateLimiter:
    """Rate limiter for API calls or other operations"""
    
    def __init__(self, rate_limit_seconds: float = 1.5):
        """
        Initialize the rate limiter
        
        Args:
            rate_limit_seconds: Minimum seconds between operations for the same key
        """
        self.last_operation_time: dict[str, float] = {}
        self.rate_limit_seconds = rate_limit_seconds
        
    def is_rate_limited(self, key: str) -> bool:
        """
        Check if an operation for the given key is rate limited
        
        Args:
            key: The key to check (e.g., username)
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        current_time = time.time()
        last_time = self.last_operation_time.get(key, 0)
        
        return (current_time - last_time) < self.rate_limit_seconds
        
    def update_last_operation_time(self, key: str) -> None:
        """
        Update the last operation time for the given key
        
        Args:
            key: The key to update (e.g., username)
        """
        self.last_operation_time[key] = time.time()
        
    async def wait_if_needed(self, key: str) -> None:
        """
        Wait if needed to respect rate limits
        
        Args:
            key: The key to check (e.g., username)
        """
        current_time = time.time()
        last_time = self.last_operation_time.get(key, 0)
        
        time_since_last = current_time - last_time
        if time_since_last < self.rate_limit_seconds:
            wait_time = self.rate_limit_seconds - time_since_last
            logger.debug(f"Rate limiting {key}, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            
        self.update_last_operation_time(key)

