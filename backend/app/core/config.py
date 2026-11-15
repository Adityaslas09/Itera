import os
from typing import Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PackVote"
    PROJECT_DESCRIPTION: str = "End-to-End Group Travel Consensus Platform with Multi-Model AI Gateway & SMS Coordination"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # AI Provider Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "+15005550006")
    
    # Operational Flags
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "openai")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    
    # Model Pricing per 1M tokens (USD)
    MODEL_PRICING: Dict[str, Dict[str, float]] = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek-reasoner": {"input": 0.55, "output": 2.19},
        "mock-ai-engine": {"input": 0.05, "output": 0.10}
    }
    
    # Task-to-Model Routing Defaults
    TASK_ROUTING: Dict[str, Dict[str, str]] = {
        "survey_extraction": {"provider": "deepseek", "model": "deepseek-chat"},
        "recommendation_synthesis": {"provider": "openai", "model": "gpt-4o-mini"},
        "complex_itinerary": {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"},
        "pricing_agent": {"provider": "openai", "model": "gpt-4o-mini"}
    }
    
    # App Settings
    RATE_LIMIT_GLOBAL: str = "100/minute"
    RATE_LIMIT_AI: str = "20/minute"
    
    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings()
