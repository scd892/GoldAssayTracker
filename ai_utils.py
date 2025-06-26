import os
import pandas as pd
from typing import Dict, List, Tuple

def check_ai_providers() -> Dict[str, bool]:
    """
    Check which AI providers are configured
    
    Returns:
        Dict[str, bool]: Dictionary with provider names as keys and boolean values indicating if they're configured
    """
    # Get API keys from environment
    deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    
    # Check if API keys are set
    providers = {
        "OpenAI": bool(openai_api_key),
        "Anthropic": bool(anthropic_api_key),
        "DeepSeek": bool(deepseek_api_key),
        "Statistical Fallback": True  # Always available
    }
    
    return providers

def get_ai_provider_details() -> List[Dict[str, str]]:
    """
    Get detailed information about each AI provider
    
    Returns:
        List[Dict[str, str]]: List of dictionaries with provider details
    """
    providers = check_ai_providers()
    
    details = [
        {
            "name": "OpenAI",
            "model": "GPT-4o",
            "configured": providers["OpenAI"],
            "description": "Latest large language model from OpenAI with strong analytical capabilities.",
            "order": 1
        },
        {
            "name": "Anthropic",
            "model": "Claude 3.5 Sonnet",
            "configured": providers["Anthropic"],
            "description": "State-of-the-art model from Anthropic focused on safe and helpful responses.",
            "order": 2
        },
        {
            "name": "DeepSeek",
            "model": "DeepSeek Chat",
            "configured": providers["DeepSeek"],
            "description": "Advanced language model from DeepSeek with comprehensive AI capabilities.",
            "order": 3
        },
        {
            "name": "Statistical Fallback",
            "model": "Built-in",
            "configured": True,
            "description": "Basic statistical analysis for common queries when AI providers are unavailable.",
            "order": 4
        }
    ]
    
    return details

def get_active_providers() -> List[str]:
    """
    Get a list of active (configured) AI providers
    
    Returns:
        List[str]: List of active provider names
    """
    providers = check_ai_providers()
    return [name for name, is_configured in providers.items() if is_configured]

def get_provider_usage_stats(sample_data: pd.DataFrame) -> Dict[str, int]:
    """
    Get stats about how many queries each provider has answered
    
    Args:
        sample_data: DataFrame with sample query data (not implemented yet)
        
    Returns:
        Dict[str, int]: Dictionary with provider names and query counts
    """
    # This is a placeholder function for future implementation
    # For now, just return some sample data
    return {
        "OpenAI": 0,
        "Anthropic": 0,
        "DeepSeek": 0,
        "Statistical Fallback": 0
    }