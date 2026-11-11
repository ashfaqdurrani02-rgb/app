"""llm_client.py - Anthropic Claude API provider client.

This module is the single isolated interface that communicates with the
Anthropic Claude API. It resolves credentials, configures the model,
and handles network, authentication, and rate limit errors cleanly.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_TEMPERATURE = 0.8
DEFAULT_MAX_TOKENS = 1500


class LLMError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMAPIKeyError(LLMError):
    """Raised when the Anthropic API key is missing or not configured."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when the API key is rejected by the provider."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limits are exceeded."""
    pass


class LLMConnectionError(LLMError):
    """Raised when network connectivity fails."""
    pass


def get_api_key() -> str:
    """Retrieve the Anthropic API key from environment variables or st.secrets.

    Returns:
        str: Valid non-empty API key.

    Raises:
        LLMAPIKeyError: If no key is found in environment or secrets.
    """
    # 1. Check OS environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key.strip():
        return api_key.strip()

    # 2. Check Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
            secret_key = st.secrets["ANTHROPIC_API_KEY"]
            if secret_key and str(secret_key).strip():
                return str(secret_key).strip()
    except Exception:
        pass

    raise LLMAPIKeyError(
        "Anthropic API Key not found. Please set ANTHROPIC_API_KEY in your .env file "
        "or in .streamlit/secrets.toml."
    )


def get_model_name() -> str:
    """Retrieve the configured model name from environment or secrets with a default fallback.

    Returns:
        str: Model identifier string.
    """
    # 1. Environment variable
    model = os.getenv("MODEL_NAME")
    if model and model.strip():
        return model.strip()

    # 2. Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "MODEL_NAME" in st.secrets:
            secret_model = st.secrets["MODEL_NAME"]
            if secret_model and str(secret_model).strip():
                return str(secret_model).strip()
    except Exception:
        pass

    return DEFAULT_MODEL


def call_llm(
    system_prompt: str,
    messages: List[Dict[str, str]],
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    override_api_key: Optional[str] = None,
) -> str:
    """Send a request to the Anthropic Messages API.

    Args:
        system_prompt: The game engine system instructions.
        messages: Conversation history list of {'role': 'user'|'assistant', 'content': '...'}.
        temperature: Sampling temperature (default 0.8).
        max_tokens: Maximum tokens to generate (default 1500).
        override_api_key: Optional API key override from user input.

    Returns:
        str: Raw text output from Claude.

    Raises:
        LLMAPIKeyError: If API key is missing.
        LLMAuthenticationError: If API key is invalid.
        LLMRateLimitError: If rate limit is hit.
        LLMConnectionError: If connection fails.
        LLMError: For any other API error.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise LLMError(
            "The 'anthropic' package is not installed. Please run: pip install anthropic"
        ) from exc

    # Determine API key
    api_key = override_api_key.strip() if (override_api_key and override_api_key.strip()) else get_api_key()
    model = get_model_name()

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            system=system_prompt,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not response.content:
            raise LLMError("Anthropic API returned an empty response.")

        # Extract text content from the first content block
        first_block = response.content[0]
        if hasattr(first_block, "text"):
            return first_block.text
        return str(first_block)

    except anthropic.AuthenticationError as exc:
        raise LLMAuthenticationError(
            f"Authentication failed: Invalid Anthropic API key. Details: {exc}"
        ) from exc
    except anthropic.RateLimitError as exc:
        raise LLMRateLimitError(
            f"Rate limit exceeded on Anthropic API. Please wait a moment and try again. Details: {exc}"
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise LLMConnectionError(
            f"Failed to connect to Anthropic API. Check your internet connection. Details: {exc}"
        ) from exc
    except anthropic.APIStatusError as exc:
        raise LLMError(
            f"Anthropic API status error ({exc.status_code}): {exc.message}"
        ) from exc
    except LLMError:
        raise
    except Exception as exc:
        raise LLMError(
            f"Unexpected error communicating with Anthropic API: {exc}"
        ) from exc
