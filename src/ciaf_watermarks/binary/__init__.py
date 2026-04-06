"""
CIAF Watermarking - Binary Module

Binary file watermarking implementation with metadata injection.

Exports:
- Core functions: build_binary_artifact_evidence
- Watermark functions: apply_binary_metadata_watermark
- Verification functions: verify_binary_artifact
- Utilities: extract_binary_metadata_watermark, has_binary_watermark

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from .metadata import (
    apply_binary_metadata_watermark,
    extract_binary_metadata_watermark,
    has_binary_watermark,
    get_binary_info,
)

from .core import (
    build_binary_artifact_evidence,
)

from .verification import (
    verify_binary_artifact,
)

__all__ = [
    # Metadata functions
    "apply_binary_metadata_watermark",
    "extract_binary_metadata_watermark",
    "has_binary_watermark",
    "get_binary_info",
    # Core functions
    "build_binary_artifact_evidence",
    # Verification functions
    "verify_binary_artifact",
]
