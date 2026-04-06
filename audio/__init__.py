"""
CIAF Watermarking - Audio Module

Audio watermarking implementation with spectral and metadata modes.

Exports:
- Core functions: build_audio_artifact_evidence
- Watermark functions: apply_audio_metadata_watermark, apply_audio_spectral_watermark
- Verification functions: verify_audio_artifact
- Utilities: extract_audio_metadata_watermark, has_audio_watermark

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from .metadata import (
    apply_audio_metadata_watermark,
    extract_audio_metadata_watermark,
    has_audio_watermark,
    get_audio_info,
    FFMPEG_AVAILABLE,
)

from .spectral import (
    apply_audio_spectral_watermark,
    extract_audio_spectral_watermark,
    AudioWatermarkSpec,
    LIBROSA_AVAILABLE,
)

from .core import (
    build_audio_artifact_evidence,
)

from .verification import (
    verify_audio_artifact,
)

__all__ = [
    # Metadata functions
    "apply_audio_metadata_watermark",
    "extract_audio_metadata_watermark",
    "has_audio_watermark",
    "get_audio_info",
    "FFMPEG_AVAILABLE",
    # Spectral functions
    "apply_audio_spectral_watermark",
    "extract_audio_spectral_watermark",
    "AudioWatermarkSpec",
    "LIBROSA_AVAILABLE",
    # Core functions
    "build_audio_artifact_evidence",
    # Verification functions
    "verify_audio_artifact",
]
