"""
Configuration Helper for OpenAI + CIAF Watermarking

This module provides a centralized configuration for all examples.
It loads settings from environment variables and provides sensible defaults.

Usage:
    from config import get_openai_client, get_watermark_config

    client = get_openai_client()
    config = get_watermark_config()

    evidence, watermarked = watermark_ai_output(
        artifact=text,
        **config,
        watermark_config={"text": {"style": "footer"}}
    )
"""

import os
from typing import Dict, Optional
from openai import OpenAI

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================


def load_env_file(filepath: str = ".env") -> None:
    """
    Load environment variables from .env file if it exists.

    Note: This is a simple implementation. For production, use python-dotenv:
        from dotenv import load_dotenv
        load_dotenv()
    """
    if not os.path.exists(filepath):
        return

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


# Try to load .env file
load_env_file()


# ============================================================================
# OPENAI CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_TOKENS = int(os.environ.get("OPENAI_MAX_TOKENS", "1000"))


def get_openai_client() -> OpenAI:
    """
    Get configured OpenAI client.

    Returns:
        OpenAI: Configured OpenAI client

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not set. Please set it in .env or environment:\n"
            "  export OPENAI_API_KEY='sk-your-key-here'"
        )

    return OpenAI(api_key=OPENAI_API_KEY)


# ============================================================================
# WATERMARKING CONFIGURATION
# ============================================================================

WATERMARK_STYLE = os.environ.get("WATERMARK_STYLE", "footer")
WATERMARK_ENABLE_FRAGMENTS = os.environ.get("WATERMARK_ENABLE_FRAGMENTS", "true").lower() == "true"
WATERMARK_NUM_FRAGMENTS = int(os.environ.get("WATERMARK_NUM_FRAGMENTS", "5"))
WATERMARK_FRAGMENT_LENGTH = int(os.environ.get("WATERMARK_FRAGMENT_LENGTH", "32"))


def get_watermark_config(
    style: Optional[str] = None, enable_fragments: Optional[bool] = None
) -> Dict:
    """
    Get watermark configuration with optional overrides.

    Args:
        style: Watermark style (footer, header, inline). If None, uses env var.
        enable_fragments: Enable forensic fragments. If None, uses env var.

    Returns:
        Dict: Configuration dictionary for watermark_ai_output()
    """
    style = style or WATERMARK_STYLE
    enable_fragments = (
        enable_fragments if enable_fragments is not None else WATERMARK_ENABLE_FRAGMENTS
    )

    return {
        "watermark_config": {
            "text": {"style": style, "include_timestamp": True, "include_model_info": True},
            "forensic_fragments": {
                "enabled": enable_fragments,
                "num_fragments": WATERMARK_NUM_FRAGMENTS,
                "fragment_length": WATERMARK_FRAGMENT_LENGTH,
            },
        }
    }


# ============================================================================
# EVIDENCE STORAGE
# ============================================================================

EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", "evidence")


def get_evidence_path(subdirectory: str = "", artifact_id: str = "") -> str:
    """
    Get path for evidence file.

    Args:
        subdirectory: Optional subdirectory (e.g., "basic", "conversation")
        artifact_id: Artifact ID for filename

    Returns:
        str: Full path for evidence file
    """
    path = os.path.join(EVIDENCE_DIR, subdirectory) if subdirectory else EVIDENCE_DIR
    os.makedirs(path, exist_ok=True)

    if artifact_id:
        return os.path.join(path, f"{artifact_id}.json")
    return path


# ============================================================================
# ACTOR CONFIGURATION
# ============================================================================

ORGANIZATION_ID = os.environ.get("ORGANIZATION_ID", "default-org")
ACTOR_ID_PREFIX = os.environ.get("ACTOR_ID_PREFIX", "user:")


def get_actor_id(user_identifier: str) -> str:
    """
    Construct actor ID from user identifier.

    Args:
        user_identifier: User identifier (email, username, etc.)

    Returns:
        str: Formatted actor ID
    """
    return f"{ACTOR_ID_PREFIX}{user_identifier}"


# ============================================================================
# COMPLETE CONFIGURATION
# ============================================================================


def get_full_config(
    user_id: str, prompt: str, model: Optional[str] = None, style: Optional[str] = None
) -> Dict:
    """
    Get complete configuration for watermark_ai_output().

    Args:
        user_id: User identifier
        prompt: User's prompt
        model: OpenAI model (defaults to OPENAI_MODEL)
        style: Watermark style (defaults to WATERMARK_STYLE)

    Returns:
        Dict: Complete configuration dictionary
    """
    model = model or OPENAI_MODEL

    config = {
        "model_id": model,
        "model_version": "2024-04",
        "actor_id": get_actor_id(user_id),
        "prompt": prompt,
        "enable_forensic_fragments": WATERMARK_ENABLE_FRAGMENTS,
    }

    # Add watermark config
    watermark_config = get_watermark_config(style)
    config.update(watermark_config)

    return config


# ============================================================================
# CONFIGURATION SUMMARY
# ============================================================================


def print_config_summary() -> None:
    """Print current configuration summary."""
    print("=" * 70)
    print("OpenAI + CIAF Watermarking Configuration")
    print("=" * 70)

    print("\n🔑 OpenAI Configuration:")
    print(f"   API Key: {'✅ Set' if OPENAI_API_KEY else '❌ Not set'}")
    print(f"   Model: {OPENAI_MODEL}")
    print(f"   Temperature: {OPENAI_TEMPERATURE}")
    print(f"   Max Tokens: {OPENAI_MAX_TOKENS}")

    print("\n🛡️ Watermarking Configuration:")
    print(f"   Style: {WATERMARK_STYLE}")
    print(f"   Forensic Fragments: {'Enabled' if WATERMARK_ENABLE_FRAGMENTS else 'Disabled'}")
    if WATERMARK_ENABLE_FRAGMENTS:
        print(f"   - Number of Fragments: {WATERMARK_NUM_FRAGMENTS}")
        print(f"   - Fragment Length: {WATERMARK_FRAGMENT_LENGTH} bytes")

    print("\n📁 Storage Configuration:")
    print(f"   Evidence Directory: {EVIDENCE_DIR}")

    print("\n👤 Actor Configuration:")
    print(f"   Organization ID: {ORGANIZATION_ID}")
    print(f"   Actor ID Prefix: {ACTOR_ID_PREFIX}")

    print("\n" + "=" * 70 + "\n")


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    print_config_summary()

    # Test configurations
    try:
        client = get_openai_client()
        print("✅ OpenAI client created successfully\n")
    except ValueError as e:
        print(f"❌ {e}\n")

    config = get_watermark_config()
    print("Watermark config:", config)

    full_config = get_full_config(user_id="alice@example.com", prompt="Test prompt")
    print("\nFull config:", full_config)
