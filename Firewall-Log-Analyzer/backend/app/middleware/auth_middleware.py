"""
API Key authentication middleware
"""
import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Load API key from environment
API_KEY = os.getenv("INGESTION_API_KEY", "default-api-key-change-in-production")


def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> bool:
    """
    Verify API key for ingestion endpoints.
    
    Args:
        api_key: API key from request header
    
    Returns:
        True if valid, raises HTTPException if invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header."
        )
    
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return True

