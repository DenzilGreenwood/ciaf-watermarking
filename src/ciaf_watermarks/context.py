"""
CIAF Watermarking - Context Management

Provides helper functions and context managers to simplify watermarking
by automatically gathering model and actor information.

Features:
- Thread-safe context management using contextvars
- Auto-detection from popular AI SDKs (OpenAI, Anthropic)
- Environment variable support
- Context manager for scoped settings
- Global configuration fallback

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.7.0
"""

from __future__ import annotations

import os
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Thread-safe context storage
_watermark_context: ContextVar[Optional["WatermarkContext"]] = ContextVar(
    "watermark_context", default=None
)


@dataclass
class WatermarkContext:
    """
    Watermarking context containing model and actor information.

    Instead of passing model_id, model_version, and actor_id to every
    watermarking function, set the context once and reuse it.

    Example:
        >>> context = WatermarkContext(
        ...     model_id="gpt-4",
        ...     model_version="2024-03",
        ...     actor_id="user:alice"
        ... )
        >>> with watermark_context(context):
        ...     evidence, watermarked = build_text_artifact_evidence(
        ...         raw_text=text,
        ...         prompt="Generate summary"
        ...     )
    """

    model_id: str
    model_version: str
    actor_id: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata dict if not provided."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for **kwargs expansion."""
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "actor_id": self.actor_id,
        }

    @classmethod
    def from_env(cls) -> "WatermarkContext":
        """
        Create context from environment variables.

        Reads:
        - CIAF_MODEL_ID or AI_MODEL_ID
        - CIAF_MODEL_VERSION or AI_MODEL_VERSION
        - CIAF_ACTOR_ID or USER_ID or USERNAME

        Raises:
            ValueError: If required environment variables are not set
        """
        model_id = os.getenv("CIAF_MODEL_ID") or os.getenv("AI_MODEL_ID")
        model_version = os.getenv("CIAF_MODEL_VERSION") or os.getenv("AI_MODEL_VERSION")
        actor_id = os.getenv("CIAF_ACTOR_ID") or os.getenv("USER_ID") or os.getenv("USERNAME")

        if not model_id:
            raise ValueError("CIAF_MODEL_ID or AI_MODEL_ID environment variable must be set")
        if not model_version:
            raise ValueError(
                "CIAF_MODEL_VERSION or AI_MODEL_VERSION environment variable must be set"
            )
        if not actor_id:
            raise ValueError("CIAF_ACTOR_ID, USER_ID, or USERNAME environment variable must be set")

        # Prefix actor_id with "user:" if not already prefixed
        if ":" not in actor_id:
            actor_id = f"user:{actor_id}"

        return cls(model_id=model_id, model_version=model_version, actor_id=actor_id)

    @classmethod
    def from_openai(cls, client: Any, user_id: str) -> "WatermarkContext":
        """
        Create context from OpenAI client.

        Args:
            client: OpenAI client instance
            user_id: User identifier (will be prefixed with "user:" if needed)

        Returns:
            WatermarkContext with detected model information

        Example:
            >>> from openai import OpenAI
            >>> client = OpenAI()
            >>> context = WatermarkContext.from_openai(client, "alice")
        """
        # Try to detect model from client default
        model_id = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        model_version = "latest"  # OpenAI doesn't expose version easily

        if ":" not in user_id:
            user_id = f"user:{user_id}"

        return cls(
            model_id=model_id,
            model_version=model_version,
            actor_id=user_id,
            metadata={"source": "openai"},
        )

    @classmethod
    def from_anthropic(cls, client: Any, user_id: str) -> "WatermarkContext":
        """
        Create context from Anthropic client.

        Args:
            client: Anthropic client instance
            user_id: User identifier

        Returns:
            WatermarkContext with detected model information

        Example:
            >>> from anthropic import Anthropic
            >>> client = Anthropic()
            >>> context = WatermarkContext.from_anthropic(client, "bob")
        """
        model_id = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

        # Extract version from model ID if possible
        if "-" in model_id and len(model_id.split("-")) >= 4:
            version_part = model_id.split("-")[-1]
            if version_part.isdigit() and len(version_part) == 8:
                # Format: YYYYMMDD -> YYYY-MM
                model_version = f"{version_part[:4]}-{version_part[4:6]}"
            else:
                model_version = version_part
        else:
            model_version = "latest"

        if ":" not in user_id:
            user_id = f"user:{user_id}"

        return cls(
            model_id=model_id,
            model_version=model_version,
            actor_id=user_id,
            metadata={"source": "anthropic"},
        )


@contextmanager
def watermark_context(
    model_id: Optional[str] = None,
    model_version: Optional[str] = None,
    actor_id: Optional[str] = None,
    context: Optional[WatermarkContext] = None,
):
    """
    Context manager for setting watermark context in current scope.

    Args:
        model_id: AI model identifier (e.g., "gpt-4", "claude-3-opus")
        model_version: Model version (e.g., "2024-03", "20240229")
        actor_id: User/actor identifier (e.g., "user:alice", "service:api")
        context: Pre-built WatermarkContext (overrides individual params)

    Yields:
        WatermarkContext: Active context

    Example:
        >>> with watermark_context(
        ...     model_id="gpt-4",
        ...     model_version="2024-03",
        ...     actor_id="user:alice"
        ... ):
        ...     # All watermarking calls in this scope use the context
        ...     evidence, watermarked = build_text_artifact_evidence(
        ...         raw_text=text,
        ...         prompt="Generate content"
        ...     )

    Example with pre-built context:
        >>> ctx = WatermarkContext.from_env()
        >>> with watermark_context(context=ctx):
        ...     evidence, watermarked = build_text_artifact_evidence(...)
    """
    if context is None:
        if not all([model_id, model_version, actor_id]):
            raise ValueError(
                "Either provide a WatermarkContext or all of " "(model_id, model_version, actor_id)"
            )
        context = WatermarkContext(
            model_id=model_id, model_version=model_version, actor_id=actor_id
        )

    # Save previous context
    token = _watermark_context.set(context)

    try:
        yield context
    finally:
        # Restore previous context
        _watermark_context.reset(token)


def get_current_context() -> Optional[WatermarkContext]:
    """
    Get the currently active watermark context.

    Returns:
        WatermarkContext if one is active, None otherwise

    Example:
        >>> context = get_current_context()
        >>> if context:
        ...     print(f"Using model: {context.model_id}")
    """
    return _watermark_context.get()


def require_context() -> WatermarkContext:
    """
    Get current context, raising an error if none is active.

    Returns:
        WatermarkContext: Active context

    Raises:
        RuntimeError: If no context is currently active

    Example:
        >>> try:
        ...     context = require_context()
        ... except RuntimeError:
        ...     print("No context set - use watermark_context()")
    """
    context = get_current_context()
    if context is None:
        raise RuntimeError(
            "No watermark context is active. Use watermark_context() or "
            "set_global_context(), or pass model_id/model_version/actor_id "
            "directly to the watermarking function."
        )
    return context


# Global fallback context (not thread-safe, use for simple cases only)
_global_context: Optional[WatermarkContext] = None


def set_global_context(model_id: str, model_version: str, actor_id: str) -> None:
    """
    Set global fallback context (not thread-safe).

    This is a simple alternative to context managers for single-threaded
    applications. For multi-threaded use, prefer watermark_context().

    Args:
        model_id: AI model identifier
        model_version: Model version
        actor_id: User/actor identifier

    Example:
        >>> set_global_context(
        ...     model_id="gpt-4",
        ...     model_version="2024-03",
        ...     actor_id="user:alice"
        ... )
        >>> # Now all watermarking calls use this context by default
        >>> evidence, watermarked = build_text_artifact_evidence(...)
    """
    global _global_context
    _global_context = WatermarkContext(
        model_id=model_id, model_version=model_version, actor_id=actor_id
    )


def get_global_context() -> Optional[WatermarkContext]:
    """
    Get the global fallback context.

    Returns:
        WatermarkContext if one has been set globally, None otherwise
    """
    return _global_context


def clear_global_context() -> None:
    """Clear the global fallback context."""
    global _global_context
    _global_context = None


def get_context_or_params(
    model_id: Optional[str] = None,
    model_version: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Helper to resolve context from parameters, active context, or global context.

    Priority:
    1. Explicit parameters (if all provided)
    2. Active watermark_context()
    3. Global context
    4. Raise error if nothing available

    Args:
        model_id: Optional explicit model ID
        model_version: Optional explicit model version
        actor_id: Optional explicit actor ID

    Returns:
        Dict with model_id, model_version, and actor_id

    Raises:
        ValueError: If context cannot be resolved
    """
    # If all parameters provided, use them
    if all([model_id, model_version, actor_id]):
        return {
            "model_id": model_id,
            "model_version": model_version,
            "actor_id": actor_id,
        }

    # Try active context (thread-safe)
    context = get_current_context()
    if context:
        return context.to_dict()

    # Try global context (fallback)
    context = get_global_context()
    if context:
        return context.to_dict()

    # No context available
    raise ValueError(
        "No watermark context available. Either:\n"
        "1. Pass model_id, model_version, and actor_id directly\n"
        "2. Use watermark_context() context manager\n"
        "3. Call set_global_context() first\n"
        "4. Set environment variables (CIAF_MODEL_ID, CIAF_MODEL_VERSION, CIAF_ACTOR_ID)"
    )


def auto_detect_context(user_id: Optional[str] = None) -> WatermarkContext:
    """
    Auto-detect watermark context from environment and installed AI SDKs.

    Detection order:
    1. Environment variables (CIAF_MODEL_ID, etc.)
    2. OpenAI environment (OPENAI_MODEL)
    3. Anthropic environment (ANTHROPIC_MODEL)

    Args:
        user_id: Optional user ID (falls back to environment variables)

    Returns:
        WatermarkContext with detected information

    Raises:
        ValueError: If context cannot be auto-detected

    Example:
        >>> # With environment variables set
        >>> context = auto_detect_context(user_id="alice")
        >>> with watermark_context(context=context):
        ...     evidence, watermarked = build_text_artifact_evidence(...)
    """
    # Try environment variables first
    try:
        return WatermarkContext.from_env()
    except ValueError:
        pass

    # Try to detect from AI SDK environments
    openai_model = os.getenv("OPENAI_MODEL")
    anthropic_model = os.getenv("ANTHROPIC_MODEL")

    if not user_id:
        user_id = os.getenv("CIAF_ACTOR_ID") or os.getenv("USER_ID") or os.getenv("USERNAME")

    if not user_id:
        raise ValueError(
            "Cannot auto-detect user_id. Please provide user_id parameter or "
            "set CIAF_ACTOR_ID environment variable."
        )

    if openai_model:
        return WatermarkContext(
            model_id=openai_model,
            model_version="latest",
            actor_id=f"user:{user_id}" if ":" not in user_id else user_id,
            metadata={"source": "openai_env"},
        )

    if anthropic_model:
        # Extract version from model ID
        version_part = anthropic_model.split("-")[-1] if "-" in anthropic_model else "latest"
        if version_part.isdigit() and len(version_part) == 8:
            model_version = f"{version_part[:4]}-{version_part[4:6]}"
        else:
            model_version = version_part

        return WatermarkContext(
            model_id=anthropic_model,
            model_version=model_version,
            actor_id=f"user:{user_id}" if ":" not in user_id else user_id,
            metadata={"source": "anthropic_env"},
        )

    raise ValueError(
        "Cannot auto-detect context. Please set one of:\n"
        "- Environment variables: CIAF_MODEL_ID, CIAF_MODEL_VERSION, CIAF_ACTOR_ID\n"
        "- OpenAI: OPENAI_MODEL + user_id parameter\n"
        "- Anthropic: ANTHROPIC_MODEL + user_id parameter"
    )


# Convenience aliases
set_context = set_global_context
get_context = get_current_context
