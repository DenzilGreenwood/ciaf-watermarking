"""
CIAF Watermarking - Image Package

Image watermarking with visual overlays and perceptual fingerprinting.

Components:
- visual.py: Visual watermarking (text, QR codes)
- fingerprints.py: Perceptual hashing (pHash, aHash, dHash, wHash)
- qr.py: QR code generation

Main Functions:
- build_image_artifact_evidence(): Complete watermarked artifact with evidence
- apply_visual_watermark(): Text overlay
- apply_qr_watermark(): QR code overlay
- compute_all_hashes(): Perceptual fingerprints

Created: 2026-03-24
Author: Denzil James Greenwood
Version: 1.0.0
"""

from .visual import (
    ImageWatermarkSpec,
    Position,
    apply_visual_watermark,
    apply_qr_watermark,
    apply_combined_watermark,
    build_image_artifact_evidence,
    PIL_AVAILABLE,
)

from .fingerprints import (
    compute_all_hashes,
    compute_perceptual_hash,
    compute_average_hash,
    compute_difference_hash,
    compute_wavelet_hash,
    hamming_distance,
    similarity_score,
    is_similar_image,
    ImageFingerprintSet,
    IMAGEHASH_AVAILABLE,
)

from .qr import (
    make_qr_code_bytes,
    make_verification_url_qr,
    make_compact_token_qr,
    QRCODE_AVAILABLE,
)

from .steganography import (
    embed_watermark_lsb,
    extract_watermark_lsb,
    verify_lsb_watermark,
    has_lsb_watermark,
    SteganographyError,
)

__all__ = [
    # Visual watermarking
    "ImageWatermarkSpec",
    "Position",
    "apply_visual_watermark",
    "apply_qr_watermark",
    "apply_combined_watermark",
    "build_image_artifact_evidence",
    "PIL_AVAILABLE",
    # Perceptual fingerprinting
    "compute_all_hashes",
    "compute_perceptual_hash",
    "compute_average_hash",
    "compute_difference_hash",
    "compute_wavelet_hash",
    "hamming_distance",
    "similarity_score",
    "is_similar_image",
    "ImageFingerprintSet",
    "IMAGEHASH_AVAILABLE",
    # QR codes
    "make_qr_code_bytes",
    "make_verification_url_qr",
    "make_compact_token_qr",
    "QRCODE_AVAILABLE",
    # Steganography (LSB embedding)
    "embed_watermark_lsb",
    "extract_watermark_lsb",
    "verify_lsb_watermark",
    "has_lsb_watermark",
    "SteganographyError",
]
