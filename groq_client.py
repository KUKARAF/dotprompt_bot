"""
Groq API integration module for DotPrompt Bot
Handles all AI-powered functionality using Groq API.
"""

import os
from typing import Optional
from dotenv import load_dotenv

from groq import Groq
from logger_config import get_logger

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger(__name__)


def get_groq_client() -> Optional[Groq]:
    """Initialize and return Groq client."""
    # Try both possible environment variable names
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_TOKEN")

    if not api_key:
        logger.error(
            "Neither GROQ_API_KEY nor GROQ_TOKEN found in environment variables"
        )
        return None

    return Groq(api_key=api_key)


def get_groq_response(prompt: str, model: str = "llama-3.1-70b", 
                     temperature: float = 0.7, max_tokens: int = 1000) -> Optional[str]:
    """Get response from Groq API for a given prompt."""
    client = get_groq_client()
    if not client:
        return "❌ AI service unavailable. Please check configuration."

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "❌ Failed to get AI response. Please try again later."


async def get_ai_help(question: str, source_code: str = "") -> Optional[str]:
    """Get AI-powered help using Groq API."""
    client = get_groq_client()
    if not client:
        return "❌ AI service unavailable. Please check configuration."

    try:
        prompt = f"""You are a helpful assistant for a Telegram bot called "DotPrompt Bot". 
Based on the bot's source code below, answer the user's question concisely and accurately.

Bot Source Code:
```python
{source_code}
```

User Question: {question}

Provide a helpful, concise answer about how to use the bot. Focus on the specific commands and their usage."""

        response = client.chat.completions.create(
            model="llama-3.1-70b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant for a Telegram bot.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "❌ Failed to get AI response. Please try again later."


def test_groq_connection() -> bool:
    """Test if Groq API connection is working."""
    client = get_groq_client()
    if not client:
        return False

    try:
        # Simple test request
        response = client.chat.completions.create(
            model="llama-3.1-70b",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10,
        )
        return True
    except Exception as e:
        logger.error(f"Groq connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the connection
    if test_groq_connection():
        print("✅ Groq API connection successful")
    else:
        print("❌ Groq API connection failed")