"""
Gemini API Utilities
====================
Shared utilities for interacting with Google's Gemini API, including:
- Client initialization with API key management
- Robust API calls with retry logic
- Scorecard extraction from LLM responses
"""

import os
import time
import re
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv
import google.generativeai as genai


def load_api_key() -> str:
    """
    Load Gemini API key from environment variables.
    
    Returns:
        API key string
        
    Raises:
        ValueError: If API key is not found or invalid
    """
    # Load from .env file
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key or api_key == 'your_gemini_api_key_here':
        raise ValueError(
            "GEMINI_API_KEY not found or invalid. "
            "Please set it in your .env file. "
            "Get your key from: https://makersuite.google.com/app/apikey"
        )
    
    return api_key


def create_gemini_client(model_name: str = "gemini-1.5-flash") -> genai.GenerativeModel:
    """
    Initialize a Gemini client with the specified model.
    
    Args:
        model_name: Name of the Gemini model to use
        
    Returns:
        Configured GenerativeModel instance
    """
    api_key = load_api_key()
    genai.configure(api_key=api_key)
    
    # Configure safety settings to allow research content
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ]
    
    model = genai.GenerativeModel(
        model_name=model_name,
        safety_settings=safety_settings
    )
    
    return model


def call_gemini_with_retry(
    model: genai.GenerativeModel,
    prompt: str,
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> str:
    """
    Call Gemini API with exponential backoff retry logic.
    
    Args:
        model: Configured GenerativeModel instance
        prompt: The prompt to send to the model
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        
    Returns:
        The model's response text
        
    Raises:
        Exception: If all retries are exhausted
    """
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            
            # Check if response was blocked
            if not response.text:
                if response.prompt_feedback:
                    raise ValueError(f"Response blocked: {response.prompt_feedback}")
                raise ValueError("Empty response received from Gemini API")
            
            return response.text
            
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                raise Exception(f"Gemini API call failed after {max_retries} attempts: {e}")
            
            print(f"⚠️  API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            print(f"   Retrying in {delay:.1f} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff


def extract_scorecard(full_response: str) -> Tuple[Dict[str, str], str]:
    """
    Extract the scorecard and audit report from a reviewer's response.
    
    This function reuses the validated robust parsing logic from
    router_agent_orchestrator.py with enhanced error handling.
    
    Args:
        full_response: The complete response from the Reviewer Agent
        
    Returns:
        Tuple of (scorecard_dict, audit_report_text)
    """
    try:
        # Use regex for robust marker detection (case-insensitive)
        start_pattern = r'\*\*REVIEWER_SCORECARD\*\*'
        end_pattern = r'\*\*END_SCORECARD\*\*'
        
        start_match = re.search(start_pattern, full_response, re.IGNORECASE)
        if not start_match:
            print("⚠️  WARNING: REVIEWER_SCORECARD marker not found")
            return {}, full_response
        
        start_idx = start_match.end()
        end_match = re.search(end_pattern, full_response[start_idx:], re.IGNORECASE)
        
        if not end_match:
            print("⚠️  WARNING: END_SCORECARD marker not found")
            scorecard_section = full_response[start_idx:].strip()
            audit_report = ""
        else:
            scorecard_section = full_response[start_idx:start_idx + end_match.start()].strip()
            audit_report = full_response[start_idx + end_match.end():].strip()
        
        # Parse scorecard section into dictionary
        scorecard = {}
        
        for line in scorecard_section.split('\n'):
            line = line.strip()
            if ':' in line:
                # Remove markdown formatting
                line = line.replace('*', '').replace('[', '').replace(']', '')
                match = re.match(r'([^:]+):(.*)', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    scorecard[key] = value
        
        if not scorecard:
            print("⚠️  WARNING: No valid scorecard entries found")
        else:
            print(f"✓ Scorecard parsed successfully ({len(scorecard)} fields)")
        
        return scorecard, audit_report
        
    except Exception as e:
        print(f"🛑 ERROR: Scorecard parsing failed: {e}")
        return {}, full_response


def format_context_for_prompt(context: Dict[str, any]) -> str:
    """
    Format context dictionary into a readable string for LLM prompts.
    
    Args:
        context: Dictionary of context variables
        
    Returns:
        Formatted context string
    """
    if not context:
        return ""
    
    lines = ["\n--- CONTEXT ---"]
    for key, value in context.items():
        lines.append(f"\n{key}:")
        lines.append(str(value))
    lines.append("\n--- END CONTEXT ---\n")
    
    return "\n".join(lines)
