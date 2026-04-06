"""
CIAF Watermarking - Text Module

Text watermarking implementation with forensic verification.

Exports:
- Core functions: build_text_artifact_evidence
- Watermark functions: apply_text_watermark, extract_watermark_id, etc.
- Verification functions: verify_text_artifact, quick_verify, etc.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from .watermark import (
    apply_text_watermark,
    extract_watermark_id,
    extract_verification_url,
    has_watermark,
    remove_watermark,
)

from .core import (
    build_text_artifact_evidence,
    quick_watermark_text,
)

from .verification import (
    verify_text_artifact,
    verify_against_multiple_evidence,
    quick_verify,
    analyze_suspect_text,
    format_verification_report,
)

__all__ = [
    # Watermark functions
    "apply_text_watermark",
    "extract_watermark_id",
    "extract_verification_url",
    "has_watermark",
    "remove_watermark",
    # Core functions
    "build_text_artifact_evidence",
    "quick_watermark_text",
    # Verification functions
    "verify_text_artifact",
    "verify_against_multiple_evidence",
    "quick_verify",
    "analyze_suspect_text",
    "format_verification_report",
]
