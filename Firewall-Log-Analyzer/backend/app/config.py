"""
Configuration and environment validation
"""
import os
from dotenv import load_dotenv

load_dotenv()


def validate_environment():
    """
    Validate required environment variables.
    Raises ValueError if required variables are missing.
    """
    required_vars = {
        "MONGO_URI": os.getenv("MONGO_URI"),
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set these in your .env file or environment."
        )
    
    # Optional but recommended
    optional_vars = {
        "INGESTION_API_KEY": os.getenv("INGESTION_API_KEY", "default-api-key-change-in-production"),
        "VIRUS_TOTAL_API_KEY": os.getenv("VIRUS_TOTAL_API_KEY"),
        "LOG_RETENTION_ENABLED": os.getenv("LOG_RETENTION_ENABLED", "true"),
        "LOG_RETENTION_MAX_MB": os.getenv("LOG_RETENTION_MAX_MB", "450"),
        "RATE_LIMIT_REQUESTS": os.getenv("RATE_LIMIT_REQUESTS", "100"),
        "RATE_LIMIT_WINDOW": os.getenv("RATE_LIMIT_WINDOW", "60"),
    }
    
    return {
        **required_vars,
        **optional_vars
    }


# Validate on import
try:
    ENV_CONFIG = validate_environment()
except ValueError as e:
    print(f"WARNING: {e}")
    ENV_CONFIG = {}

