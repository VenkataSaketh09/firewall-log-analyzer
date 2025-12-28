"""
Rate limiting middleware
"""
import os
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Rate limit storage: {ip: (count, reset_time)}
rate_limit_store: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0))

# Configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # requests per window
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for API endpoints.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only apply rate limiting to ingestion endpoint
        if request.url.path.startswith("/api/logs/ingest"):
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()
            
            count, reset_time = rate_limit_store[client_ip]
            
            # Reset if window expired
            if current_time > reset_time:
                count = 0
                reset_time = current_time + RATE_LIMIT_WINDOW
            
            # Check limit
            if count >= RATE_LIMIT_REQUESTS:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
                )
            
            # Increment count
            rate_limit_store[client_ip] = (count + 1, reset_time)
        
        response = await call_next(request)
        return response

