"""
CIAF Watermarking - Video Watermarking Package

Video watermarking with forensic provenance:
1. Metadata watermarking (XMP, container metadata)
2. Visual watermarking (frame overlays)
3. Keyframe-based verification
4. Temporal fragment sampling

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from .metadata import (
    apply_video_metadata_watermark,
    extract_video_metadata_watermark,
    has_video_watermark,
)

from .visual import (
    apply_video_visual_watermark,
    VideoWatermarkSpec,
)

from .core import (
    build_video_artifact_evidence,
)

from .verification import (
    verify_video_artifact,
)

# Check for optional dependencies
try:
    import ffmpeg

    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


__all__ = [
    # Core functions
    "build_video_artifact_evidence",
    "verify_video_artifact",
    # Metadata watermarking
    "apply_video_metadata_watermark",
    "extract_video_metadata_watermark",
    "has_video_watermark",
    # Visual watermarking
    "apply_video_visual_watermark",
    "VideoWatermarkSpec",
    # Availability flags
    "FFMPEG_AVAILABLE",
    "CV2_AVAILABLE",
]
