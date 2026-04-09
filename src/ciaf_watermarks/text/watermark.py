"""
CIAF Watermarking - Text Watermark Functions

Watermark application, extraction, and manipulation.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.5.0
"""

import re
from typing import Optional


def apply_text_watermark(
    raw_text: str,
    watermark_id: str,
    verification_url: str,
    style: str = "footer",
) -> str:
    """
    Apply visible text watermark to AI-generated content.

    Args:
        raw_text: Original AI output (before watermark)
        watermark_id: Unique watermark identifier
        verification_url: URL for verification
        style: Watermark style ("footer", "header", "inline")

    Returns:
        Watermarked text
    """
    if style == "footer":
        return _apply_footer_watermark(raw_text, watermark_id, verification_url)
    elif style == "header":
        return _apply_header_watermark(raw_text, watermark_id, verification_url)
    elif style == "inline":
        return _apply_inline_watermark(raw_text, watermark_id, verification_url)
    else:
        raise ValueError(f"Unknown watermark style: {style}")


def _apply_footer_watermark(
    text: str,
    watermark_id: str,
    verification_url: str,
) -> str:
    """Apply footer-style watermark."""
    footer = (
        "\n\n"
        "---\n"
        f"AI Provenance Tag: {watermark_id}\n"
        f"Verify: {verification_url}\n"
        "Generated with CIAF (Cognitive Insight Audit Framework)\n"
    )
    return text + footer


def _apply_header_watermark(
    text: str,
    watermark_id: str,
    verification_url: str,
) -> str:
    """Apply header-style watermark."""
    header = f"AI Provenance Tag: {watermark_id}\n" f"Verify: {verification_url}\n" "---\n\n"
    return header + text


def _apply_inline_watermark(
    text: str,
    watermark_id: str,
    verification_url: str,
) -> str:
    """Apply inline watermark (end of first paragraph)."""
    # Find first paragraph break
    match = re.search(r"\n\n", text)

    if match:
        pos = match.end()
        # Store full watermark ID for exact verification
        tag = f" [AI Generated: {watermark_id}]"
        return text[:pos] + tag + text[pos:]
    else:
        # No paragraph break, use footer
        return _apply_footer_watermark(text, watermark_id, verification_url)


def extract_watermark_id(text: str) -> Optional[str]:
    """
    Extract watermark ID from text if present.

    Args:
        text: Text to check

    Returns:
        Watermark ID if found, None otherwise
    """
    # Try footer pattern
    match = re.search(r"AI Provenance Tag:\s*([a-zA-Z0-9_-]+)", text)
    if match:
        return match.group(1)

    # Try inline pattern
    match = re.search(r"\[AI Generated:\s*([a-zA-Z0-9_-]+)", text)
    if match:
        return match.group(1)

    return None


def extract_verification_url(text: str) -> Optional[str]:
    """
    Extract verification URL from text if present.

    Args:
        text: Text to check

    Returns:
        Verification URL if found, None otherwise
    """
    match = re.search(r"Verify:\s*(https?://[^\s\n]+)", text)
    if match:
        return match.group(1)
    return None


def has_watermark(text: str) -> bool:
    """
    Check if text contains a CIAF watermark.

    Args:
        text: Text to check

    Returns:
        True if watermark detected
    """
    return extract_watermark_id(text) is not None


def remove_watermark(text: str) -> str:
    """
    Remove CIAF watermark from text.

    Use case: Internal testing, or extracting clean content.

    Args:
        text: Watermarked text

    Returns:
        Text with watermark removed
    """
    # Remove footer watermarks
    text = re.sub(r"\n+---+\n+AI Provenance Tag:.*$", "", text, flags=re.DOTALL | re.MULTILINE)

    # Remove header watermarks
    text = re.sub(r"^AI Provenance Tag:.*?\n+---+\n+", "", text, flags=re.MULTILINE)

    # Remove inline watermarks
    text = re.sub(r"\s*\[AI Generated:.*?\]", "", text)

    return text.strip()


__all__ = [
    "apply_text_watermark",
    "extract_watermark_id",
    "extract_verification_url",
    "has_watermark",
    "remove_watermark",
]
