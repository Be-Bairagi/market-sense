"""
API Key Authentication Module

Provides API key-based authentication for protected endpoints.
"""
from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from app.config import settings

# API key header name
API_KEY_HEADER = "X-API-Key"

# Create API key security scheme
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key provided in the request header.
    
    Args:
        api_key: The API key from the request header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Missing API key",
                "message": "API key is required. Pass it in the 'X-API-Key' header.",
            },
        )
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid API key",
                "message": "The provided API key is not valid.",
            },
        )
    
    return api_key


def require_auth():
    """Dependency to require API key authentication."""
    return Security(verify_api_key)
