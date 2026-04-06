"""
CIAF Watermarking Module

Forensic provenance system for AI-generated artifacts with dual-state integrity
model and DNA-level sub-segment verification.

This module implements watermarking and verification for AI outputs,
enabling detection of watermark removal, content tampering,
and mix-and-match attacks.

Key Features (v1.3.0):
- ✅ Dual-state hashing (before/after watermark)
- ✅ Sub-segment forensic records (DNA sampling)
- ✅ SignatureEnvelope pattern (production-ready signatures) ⭐ NEW
- ✅ Multiple verification strategies
- ✅ Format-resilient matching
- ✅ Content similarity detection
- ✅ Vault integration for persistent storage

Multi-Point Sampling Strategy:

- Text: 3 high-entropy fragments (begin/middle/end) → 2+ matches = 99.9%+ confidence
- Image: 4-6 spatial complexity patches → defeats splicing attacks
- Video: Temporal keyframe sampling (Phase 2)
- Audio: Spectral frequency segments (Phase 2)

Quick Start (Type-Specific):
    from ciaf.watermarks import (
        build_text_artifact_evidence,
        verify_text_artifact,
        select_text_forensic_fragments
    )

    # Create watermarked artifact with forensic fragments
    evidence, watermarked_text = build_text_artifact_evidence(
        raw_text="AI generated content...",
        model_id="gpt-4",
        model_version="2026-03",
        actor_id="user:analyst-17",
        prompt="Generate a summary...",
        verification_base_url="https://vault.example.com",
        enable_forensic_fragments=True
    )

    # Later: verify suspect text with DNA sampling
    result = verify_text_artifact(suspect_text, evidence)
    print(f"Authentic: {result.is_authentic()}")
    print(f"Confidence: {result.confidence:.1%}")

Quick Start (Unified Interface - ANY artifact type): ⭐ NEW v1.4.0
    from ciaf.watermarks import watermark_ai_output

    # Works for text, images, PDF - auto-detects type!
    evidence, watermarked = watermark_ai_output(
        artifact=ai_model_output,  # str or bytes, any type
        model_id="gpt-4",
        model_version="2026-03",
        actor_id="user:analyst-17",
        prompt="Generate content",
        verification_base_url="https://vault.example.com"
    )

Created: 2026-03-24
Updated: 2026-04-04 (Unified Interface)
Author: Denzil James Greenwood
Version: 1.4.0
"""

# Signature envelope (v1.3.0) ⭐ NEW
from .signature_envelope import (
    KeyBackend,
    SignatureEncoding,
    SignatureMetadata,
    SignatureEnvelope,
    create_signature_envelope,
)

# Context management (v1.7.0) ⭐ NEW
from .context import (
    WatermarkContext,
    watermark_context,
    get_current_context,
    get_context,
    require_context,
    set_global_context,
    set_context,
    get_global_context,
    clear_global_context,
    auto_detect_context,
)

# Core models (updated with forensic fragments and SignatureEnvelope)
from .models import (
    ArtifactType,
    WatermarkType,
    ArtifactEvidence,
    ArtifactHashSet,
    ArtifactFingerprint,
    WatermarkDescriptor,
    VerificationResult,
    ForensicArtifactProfile,
    ForensicFragment,  # ⭐ NEW
    TextForensicFragment,  # ⭐ NEW
    ImageForensicFragment,  # ⭐ NEW
    VideoForensicSnippet,  # ⭐ NEW
    AudioForensicSegment,  # ⭐ NEW
    ForensicFragmentSet,  # ⭐ NEW
    utc_now_iso,
    sha256_bytes,
    sha256_text,
    canonical_json,
)

# Hashing utilities
from .hashing import (
    normalize_text_for_forensics,
    normalized_text_hash,
    strip_common_watermarks,
    text_with_watermark_stripped_hash,
    SimHash,
    simhash_text,
    simhash_distance,
    MinHash,
    minhash_text,
    minhash_similarity,
    perceptual_hash_audio,  # ✅ chromaprint implementation
    perceptual_hash_video,  # ✅ ffmpeg+imagehash implementation
)

# Text watermarking and verification
from .text import (
    # Watermark functions
    apply_text_watermark,
    extract_watermark_id,
    extract_verification_url,
    has_watermark,
    remove_watermark,
    # Core functions
    build_text_artifact_evidence,
    quick_watermark_text,
    # Verification functions
    verify_text_artifact,
    verify_against_multiple_evidence,
    quick_verify,
    analyze_suspect_text,
    format_verification_report,
)

# Vault integration
from .vault_adapter import (
    WatermarkVaultAdapter,
    create_watermark_vault,
)

# Image watermarking (Phase 1)
from .images import (
    ImageWatermarkSpec,
    Position,
    apply_visual_watermark,
    apply_qr_watermark,
    apply_combined_watermark,
    build_image_artifact_evidence,
    PIL_AVAILABLE,
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
    make_qr_code_bytes,
    make_verification_url_qr,
    make_compact_token_qr,
    QRCODE_AVAILABLE,
    # Steganography (LSB embedding) - v1.4.0 ⭐ NEW
    embed_watermark_lsb,
    extract_watermark_lsb,
    verify_lsb_watermark,
    has_lsb_watermark,
    SteganographyError,
)

# PDF watermarking (Phase 1)
from .pdf import (
    apply_pdf_metadata_watermark,
    build_pdf_artifact_evidence,
    extract_pdf_metadata_watermark,
    has_pdf_watermark,
    verify_pdf_artifact,
    PYPDF_AVAILABLE,
)

# Video watermarking (v1.5.0) ⭐ NEW
from .video import (
    build_video_artifact_evidence,
    apply_video_metadata_watermark,
    apply_video_visual_watermark,
    extract_video_metadata_watermark,
    has_video_watermark,
    verify_video_artifact,
    VideoWatermarkSpec,
    FFMPEG_AVAILABLE,
    CV2_AVAILABLE,
)

# Forensic fragment selection (v1.2.0) ⭐ NEW
from .fragment_selection import (
    compute_text_entropy,
    select_text_fragment,
    select_text_forensic_fragments,
    compute_image_patch_entropy,
    select_image_forensic_patches,
    select_video_forensic_snippets,
    select_audio_forensic_segments,
    create_forensic_fragment_set,
)

# Forensic fragment verification (v1.2.0) ⭐ NEW
from .fragment_verification import (
    verify_text_fragments,
    verify_image_fragments,
    verify_video_fragments,
    verify_audio_fragments,
    FragmentMatchResult,
    ForensicVerificationSummary,
)

# Hierarchical verification strategy (v1.2.0) ⭐ NEW
from .hierarchical_verification import (
    VerificationTier,
    VerificationStep,
    HierarchicalVerificationResult,
    verify_text_artifact_hierarchical,
    verify_image_artifact_hierarchical,
    format_hierarchical_verification_report,
    VerificationStatistics,
)

# Unified Interface (v1.4.0) ⭐ NEW
from .unified_interface import (
    detect_artifact_type,
    watermark_ai_output,
    quick_watermark,
    WatermarkDispatcher,
    set_default_watermark_config,
    get_default_watermark_config,
)

# Async Processing & Caching (v1.4.1) ⭐ NEW
from .async_processing import (
    ProcessingStatus,
    ProcessingTask,
    InMemoryCache,
    BackgroundWorker,
    watermark_ai_output_async,
    get_processing_status,
    finalize_forensics_offline,
    get_async_infrastructure,
)

# Schema Validation (v1.4.0) ⭐ NEW
from .schema_validation import (
    validate_artifact_id,
    validate_watermark_id,
    validate_fragment_id,
    validate_sha256_hash,
    validate_iso8601_timestamp,
    validate_confidence_score,
    validate_entropy_score,
    validate_artifact_evidence,
    validate_forensic_fragment_set,
    validate_watermark_descriptor,
    validate_evidence_batch,
    generate_compliance_report,
)

__version__ = "1.4.0"

__all__ = [
    # Signature Envelope (v1.3.0) ⭐ NEW
    "KeyBackend",
    "SignatureEncoding",
    "SignatureMetadata",
    "SignatureEnvelope",
    "create_signature_envelope",
    # Enums
    "ArtifactType",
    "WatermarkType",
    # Models
    "ArtifactEvidence",
    "ArtifactHashSet",
    "ArtifactFingerprint",
    "WatermarkDescriptor",
    "VerificationResult",
    "ForensicArtifactProfile",
    # Forensic Fragment Models (v1.2.0) ⭐ NEW
    "ForensicFragment",
    "TextForensicFragment",
    "ImageForensicFragment",
    "VideoForensicSnippet",
    "AudioForensicSegment",
    "ForensicFragmentSet",
    # Utility functions
    "utc_now_iso",
    "sha256_bytes",
    "sha256_text",
    "canonical_json",
    # Hashing
    "normalize_text_for_forensics",
    "normalized_text_hash",
    "strip_common_watermarks",
    "text_with_watermark_stripped_hash",
    "SimHash",
    "simhash_text",
    "simhash_distance",
    "MinHash",
    "minhash_text",
    "minhash_similarity",
    # Perceptual Hashing (v1.4.1) ✅ Complete implementations
    "perceptual_hash_audio",  # chromaprint-based
    "perceptual_hash_video",  # ffmpeg+imagehash-based
    # Text watermarking
    "apply_text_watermark",
    "build_text_artifact_evidence",
    "quick_watermark_text",
    "extract_watermark_id",
    "extract_verification_url",
    "has_watermark",
    "remove_watermark",
    # Verification
    "verify_text_artifact",
    "verify_against_multiple_evidence",
    "quick_verify",
    "analyze_suspect_text",
    "format_verification_report",
    # Vault integration
    "WatermarkVaultAdapter",
    "create_watermark_vault",
    # Image watermarking (Phase 1)
    "ImageWatermarkSpec",
    "Position",
    "apply_visual_watermark",
    "apply_qr_watermark",
    "apply_combined_watermark",
    "build_image_artifact_evidence",
    "PIL_AVAILABLE",
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
    "make_qr_code_bytes",
    "make_verification_url_qr",
    "make_compact_token_qr",
    "QRCODE_AVAILABLE",
    # Steganography (LSB embedding) - v1.4.0 ⭐ NEW
    "embed_watermark_lsb",
    "extract_watermark_lsb",
    "verify_lsb_watermark",
    "has_lsb_watermark",
    "SteganographyError",
    # PDF watermarking (Phase 1)
    "apply_pdf_metadata_watermark",
    "build_pdf_artifact_evidence",
    "extract_pdf_metadata_watermark",
    "has_pdf_watermark",
    "verify_pdf_artifact",
    "PYPDF_AVAILABLE",
    # Video watermarking (v1.5.0) ⭐ NEW
    "build_video_artifact_evidence",
    "apply_video_metadata_watermark",
    "apply_video_visual_watermark",
    "extract_video_metadata_watermark",
    "has_video_watermark",
    "verify_video_artifact",
    "VideoWatermarkSpec",
    "FFMPEG_AVAILABLE",
    "CV2_AVAILABLE",
    # Forensic Fragment Selection (v1.2.0) ⭐ NEW
    "compute_text_entropy",
    "select_text_fragment",
    "select_text_forensic_fragments",
    "compute_image_patch_entropy",
    "select_image_forensic_patches",
    "select_video_forensic_snippets",
    "select_audio_forensic_segments",
    "create_forensic_fragment_set",
    # Forensic Fragment Verification (v1.2.0) ⭐ NEW
    "verify_text_fragments",
    "verify_image_fragments",
    "verify_video_fragments",
    "verify_audio_fragments",
    "FragmentMatchResult",
    "ForensicVerificationSummary",
    # Hierarchical Verification Strategy (v1.2.0) ⭐ NEW
    "VerificationTier",
    "VerificationStep",
    "HierarchicalVerificationResult",
    "verify_text_artifact_hierarchical",
    "verify_image_artifact_hierarchical",
    "format_hierarchical_verification_report",
    "VerificationStatistics",
    # Unified Interface (v1.4.0) ⭐ NEW
    "detect_artifact_type",
    "watermark_ai_output",
    "quick_watermark",
    "WatermarkDispatcher",
    "set_default_watermark_config",
    "get_default_watermark_config",
    # Async Processing & Caching (v1.4.1) ⭐ NEW
    "ProcessingStatus",
    "ProcessingTask",
    "InMemoryCache",
    "BackgroundWorker",
    "watermark_ai_output_async",
    "get_processing_status",
    "finalize_forensics_offline",
    "get_async_infrastructure",
    # Schema Validation (v1.4.0) ⭐ NEW
    "validate_artifact_id",
    "validate_watermark_id",
    "validate_fragment_id",
    "validate_sha256_hash",
    "validate_iso8601_timestamp",
    "validate_confidence_score",
    "validate_entropy_score",
    "validate_artifact_evidence",
    "validate_forensic_fragment_set",
    "validate_watermark_descriptor",
    "validate_evidence_batch",
    "generate_compliance_report",
]
