"""
CIAF Watermarking - Data Models

Forensic provenance models for AI artifact watermarking and verification.

This module implements a dual-state artifact integrity model with sub-segment
forensic records (DNA sampling):
- State 1: pre-watermark artifact (original AI output)
- State 2: distributed/watermarked artifact (with provenance tags)
- State 3+: High-entropy forensic fragments for granular verification

Both states are cryptographically bound into one signed CIAF receipt,
enabling detection of watermark removal and content tampering.

Additionally, forensic fragments enable:
- Detection of mix-and-match attacks (spliced documents)
- Legal defensibility through DNA-level provenanceation
- Privacy protection (don't store entire documents in vault)

Created: 2026-03-24
Updated: 2026-03-30 (Signature Envelope migration)
Author: Denzil James Greenwood
Version: 1.3.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import hashlib
import json

from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    pass


class ArtifactType(str, Enum):
    """Type of AI-generated artifact."""

    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    JSON = "json"
    BINARY = "binary"
    VIDEO = "video"
    AUDIO = "audio"


class WatermarkType(str, Enum):
    """Watermarking technique applied to artifact."""

    NONE = "none"
    VISIBLE = "visible"  # Visible tag/footer/header
    METADATA = "metadata"  # Embedded in file metadata
    EMBEDDED = "embedded"  # Steganographic embedding
    HYBRID = "hybrid"  # Multiple techniques combined
    QR_CODE = "qr_code"  # QR code watermark


def utc_now_iso() -> str:
    """Generate ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    """Compute SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(data: Dict[str, Any]) -> bytes:
    """
    Generate canonical JSON bytes for cryptographic hashing.

    Ensures consistent serialization by:
    - Sorting keys alphabetically
    - Using minimal separators
    - Preserving Unicode
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


class ArtifactFingerprint(BaseModel):
    """
    Forensic fingerprint for artifact similarity matching.

    Used when exact hash matching fails (content modified after generation).
    """

    model_config = ConfigDict(protected_namespaces=())

    algorithm: str  # e.g., "simhash", "perceptual_hash", "minihash"
    value: str  # Fingerprint value
    role: str  # e.g., "exact_content", "perceptual", "simhash", "embedding_ref"
    confidence: Optional[float] = None  # Matching confidence threshold (0.0-1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class WatermarkDescriptor(BaseModel):
    """
    Complete watermark metadata for provenance tracking.

    Describes how the watermark was applied and how to verify it.
    """

    model_config = ConfigDict(protected_namespaces=())

    watermark_id: str  # Unique watermark identifier
    watermark_type: WatermarkType  # Technique used
    tag_text: Optional[str] = None  # Human-readable tag text
    verification_url: Optional[str] = None  # URL for online verification
    qr_payload: Optional[str] = None  # QR code data
    metadata_fields: Dict[str, str] = Field(default_factory=dict)  # Custom metadata
    embed_method: Optional[str] = None  # Technical embedding method
    removal_resistance: Optional[str] = None  # "low", "medium", "high"
    location: Optional[str] = None  # Where watermark appears

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.model_dump()
        result["watermark_type"] = self.watermark_type.value
        return result


class ForensicFragment(BaseModel):
    """
    Base forensic fragment for DNA-level artifact verification.

    Stores hash of a high-entropy sub-segment of an artifact, enabling:
    - Detection of mix-and-match attacks (spliced content)
    - Legal defensibility ("we can prove THIS section is AI-generated")
    - Privacy protection (don't store entire artifacts in vault)

    Fragment selection uses entropy scoring to ensure we're not hashing
    generic boilerplate text or blank image regions.
    """

    model_config = ConfigDict(protected_namespaces=())

    fragment_id: str  # Unique fragment identifier (e.g., 'frag_0_begin')
    fragment_type: str  # 'text', 'image_patch', 'video_frame', 'audio_segment'
    entropy_score: float  # 0.0-1.0 (1.0 = highest unique content)
    sampling_method: str  # e.g., 'begin', 'middle', 'end' for text; 'spatial' for images
    content_position: int  # For text: char offset; for image: patch index; for video: frame number


class TextForensicFragment(ForensicFragment):
    """
    High-entropy text fragment for granular verification.

    Stores:
    - Fragment text for sliding window matching
    - Fragment hash before/after watermark for integrity verification
    - Character position in original document
    - Fragment length and entropy score
    """

    offset_start: int  # Character offset in document
    offset_end: int  # End offset
    fragment_length: int  # Length of fragment
    sample_location: str  # 'beginning', 'middle', 'end'

    # ✅ FIX #161: Store actual fragment text for sliding window matching
    fragment_text: str  # The actual sampled text (critical for verification)

    # Dual-state fragment hashing (for integrity verification)
    fragment_hash_before: str  # SHA-256 of fragment before watermark
    fragment_hash_after: str  # SHA-256 of fragment after watermark

    # Optional similarity hashing
    fragment_simhash_before: Optional[str] = None
    fragment_simhash_after: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.model_dump()
        result.pop("fragment_type", None)  # Avoid duplication
        return result


class ImageForensicFragment(ForensicFragment):
    """
    High-entropy image patch for granular verification.

    Stores:
    - Patch hash before/after watermark
    - Spatial region coordinates
    - Entropy score (to avoid blank sky or uniform regions)
    """

    # Required fields (no defaults) must come first
    patch_grid_position: str  # e.g., 'grid_2_4' (row/col in block grid)
    patch_hash_before: str  # pHash of region before watermark
    patch_hash_after: str  # pHash of region after watermark

    # Optional fields with defaults
    region_coordinates: tuple = (0, 0, 64, 64)  # (x, y, width, height)

    # Alternative hashes
    patch_ahash_before: Optional[str] = None
    patch_dhash_before: Optional[str] = None
    patch_whash_before: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.model_dump()
        result.pop("fragment_type", None)
        return result


class VideoForensicSnippet(ForensicFragment):
    """
    Temporal keyframe sample for video verification.

    Stores:
    - Selected I-frame (keyframe) hashes
    - Temporal position and frame type
    - Motion signature over 2-second window
    """

    timestamp_ms: int  # Position in timeline (milliseconds)
    frame_index: int  # Frame number
    frame_type: str  # 'I-Frame' (keyframe), identifies GOP structure
    frame_duration_ms: int  # Duration from prior frame

    # Keyframe patch hashes (visual DNA)
    frame_patch_hashes: List[str] = Field(default_factory=list)

    # Motion signature (sequence of frames over 2-second window)
    temporal_motion_hash: Optional[str] = None  # Signature of movement
    motion_confidence: float = 0.0  # Confidence in motion hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.model_dump()
        result.pop("fragment_type", None)
        return result


class AudioForensicSegment(ForensicFragment):
    """
    Spectrogram fingerprint for audio verification.

    Stores:
    - Spectral hash (frequency-domain fingerprint)
    - Temporal position in audio
    - Frequency characteristics for entropy scoring
    """

    start_time_ms: int  # Position in track (milliseconds)
    segment_duration_ms: int  # Length of segment (typical: 2000-5000 ms)

    # Spectral analysis
    spectrogram_hash: str  # Perceptual hash of spectrogram (pHash magnitude)
    frequency_centroid: float  # Average frequency (Hz) - for entropy scoring
    spectral_flatness: float  # 0.0-1.0 (higher = more noise/variety)

    # Before/after for dual-state
    spectrogram_hash_before: Optional[str] = None
    spectrogram_hash_after: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.model_dump()
        result.pop("fragment_type", None)
        return result


class ForensicFragmentSet(BaseModel):
    """
    Collection of forensic fragments forming the "DNA" of an artifact.

    Multi-point sampling approach:
    - Text: 3 fragments (beginning, middle, end) - any 2 matches = 99.9% confidence
    - Image: 4-6 high-complexity patches - spatial diversity
    - Video: Keyframes at 25%, 50%, 75% + motion signatures
    - Audio: Spectral samples at multiple timestamps

    This provides legal defensibility: "We can prove AI origin of specific,
    verifiable sections of this artifact with P < 10^-15."
    """

    model_config = ConfigDict(protected_namespaces=())

    fragment_count: int
    sampling_strategy: str  # 'multi_point', 'spatial_diversity', 'temporal'
    total_coverage_percent: float  # Estimated % of content represented

    # Typed fragment lists
    text_fragments: List[TextForensicFragment] = Field(default_factory=list)
    image_fragments: List[ImageForensicFragment] = Field(default_factory=list)
    video_snippets: List[VideoForensicSnippet] = Field(default_factory=list)
    audio_segments: List[AudioForensicSegment] = Field(default_factory=list)

    # Statistics
    min_entropy_threshold: float = 0.6  # Minimum entropy to include
    cumulative_entropy_score: float = 0.0  # Average entropy of selected fragments

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.model_dump()
        return result

    @property
    def all_fragments(self) -> List[ForensicFragment]:
        """Get all fragments regardless of type."""
        return (
            self.text_fragments + self.image_fragments + self.video_snippets + self.audio_segments
        )


class ArtifactHashSet(BaseModel):
    """
    Dual-state hashing for forensic provenance.

    Critical feature: stores hashes BEFORE and AFTER watermark application.
    This enables detection of watermark removal attacks.

    If suspect artifact matches:
    - content_hash_after_watermark: Exact distributed copy
    - content_hash_before_watermark: Watermark removed but content intact
    - Neither: Content was modified (use similarity fingerprints)

    Additionally stores forensic fragments for DNA-level verification.
    """

    model_config = ConfigDict(protected_namespaces=())

    content_hash_before_watermark: str  # SHA-256 of original AI output
    content_hash_after_watermark: str  # SHA-256 of watermarked version
    canonical_receipt_hash: Optional[str] = None  # Hash of complete receipt

    # Optional normalized hashing (resilient to formatting changes)
    normalized_hash_before: Optional[str] = None  # Normalized pre-watermark
    normalized_hash_after: Optional[str] = None  # Normalized post-watermark

    # Optional perceptual/similarity hashing
    perceptual_hash_before: Optional[str] = None  # pHash/dHash for images
    perceptual_hash_after: Optional[str] = None
    simhash_before: Optional[str] = None  # SimHash for text
    simhash_after: Optional[str] = None

    # NEW: Forensic fragments (sub-segment DNA records)
    forensic_fragments: Optional[ForensicFragmentSet] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.model_dump()
        if self.forensic_fragments:
            result["forensic_fragments"] = self.forensic_fragments.to_dict()
        return result


class ArtifactEvidence(BaseModel):
    """
    Complete forensic provenance record for AI-generated artifact.

    This is the core evidence structure stored in CIAF vault.
    It binds together:
    - What model generated it
    - When and by whom
    - Original and watermarked content hashes
    - Watermark description
    - Forensic fingerprints
    - Link to previous artifacts (chain)

    This record enables:
    1. Proving genuine origin from your system
    2. Detecting watermark removal
    3. Identifying modified versions via similarity
    4. Complete audit trail
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())

    artifact_id: str  # Unique artifact ID
    artifact_type: ArtifactType  # Type of artifact
    mime_type: str  # MIME type
    created_at: str  # ISO 8601 timestamp

    # Model provenance
    model_id: str  # Model identifier
    model_version: str  # Model version
    actor_id: str  # User/system that generated it

    # Cryptographic linkage
    prompt_hash: str  # SHA-256 of input prompt
    output_hash_raw: str  # Hash of raw output (pre-watermark)
    output_hash_distributed: str  # Hash of distributed output (post-watermark)

    # Watermark details
    watermark: WatermarkDescriptor

    # Dual-state hashing
    hashes: ArtifactHashSet

    # Forensic fingerprints (for similarity matching)
    fingerprints: List[ArtifactFingerprint] = Field(default_factory=list)

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Receipt chaining (link to previous artifact)
    prior_receipt_hash: Optional[str] = None

    # Signature (✅ Updated to SignatureEnvelope pattern for v1.3.0)
    signature: Optional[Any] = None  # SignatureEnvelope type - using Any to avoid circular import
    merkle_leaf_hash: Optional[str] = None

    def to_canonical_dict(self) -> Dict[str, Any]:
        """
        Convert to canonical dictionary for hashing/signing.

        Ensures consistent serialization for cryptographic operations.

        Note: Signature field is excluded from canonical dict as it's
        computed over the content (not self-referential).
        """
        result = self.model_dump()
        result["artifact_type"] = self.artifact_type.value
        result["watermark"] = self.watermark.to_dict()
        result["hashes"] = self.hashes.to_dict()
        result["fingerprints"] = [fp.model_dump() for fp in self.fingerprints]

        # Remove signature from canonical form (computed after canonicalization)
        result.pop("signature", None)
        result.pop("merkle_leaf_hash", None)  # Also computed after

        return result

    def to_canonical_bytes(self) -> bytes:
        """Generate canonical bytes for signing/hashing."""
        return canonical_json(self.to_canonical_dict())

    def compute_receipt_hash(self) -> str:
        """Compute canonical receipt hash."""
        return sha256_bytes(self.to_canonical_bytes())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to full dictionary including signature.

        This includes the signature envelope if present.
        """
        result = self.to_canonical_dict()

        # Add signature back in (for serialization)
        if self.signature:
            from .signature_envelope import SignatureEnvelope

            if isinstance(self.signature, SignatureEnvelope):
                result["signature"] = self.signature.to_dict()
            else:
                result["signature"] = self.signature

        if self.merkle_leaf_hash:
            result["merkle_leaf_hash"] = self.merkle_leaf_hash

        return result


class VerificationResult(BaseModel):
    """
    Result of artifact verification against stored evidence.

    Answers the questions:
    - Is this the exact distributed version?
    - Is this the original without watermark?
    - Was the watermark likely removed?
    - How closely does it match?
    """

    model_config = ConfigDict(protected_namespaces=())

    artifact_id: str = ""  # ID of evidence record checked against
    exact_match_after_watermark: bool = False  # Matches distributed version exactly
    exact_match_before_watermark: bool = False  # Matches pre-watermark version exactly
    likely_tag_removed: bool = False  # True if matches pre-watermark but not post

    # Similarity matching results
    normalized_match_before: bool = False
    normalized_match_after: bool = False
    perceptual_similarity_score: Optional[float] = None  # 0.0-1.0
    simhash_distance: Optional[int] = None  # Hamming distance for text

    # Forensic analysis
    watermark_present: bool = False
    watermark_intact: bool = False
    content_modified: bool = False

    # Explanation
    notes: List[str] = Field(default_factory=list)
    confidence: float = 0.0  # Overall confidence (0.0-1.0)

    # Evidence reference
    evidence_record: Optional[ArtifactEvidence] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.model_dump()
        if self.evidence_record:
            result["evidence_record"] = self.evidence_record.to_dict()
        return result

    def is_authentic(self) -> bool:
        """
        Determine if artifact is authentic (from our system).

        True if:
        - Exact match to distributed version, OR
        - Exact match to pre-watermark version, OR
        - High similarity with good confidence
        """
        return (
            self.exact_match_after_watermark
            or self.exact_match_before_watermark
            or (self.perceptual_similarity_score and self.perceptual_similarity_score > 0.9)
            or (self.normalized_match_before or self.normalized_match_after)
        )


class ForensicArtifactProfile(BaseModel):
    """
    Extended forensic profile with full hash suite.

    This is an enhanced version of ArtifactHashSet with more forensic features.
    Used for high-security scenarios where multiple matching methods are needed.
    """

    model_config = ConfigDict(protected_namespaces=())

    # Core hashes
    exact_hash_before_watermark: str
    exact_hash_after_watermark: str

    # Normalized hashes (resilient to formatting)
    normalized_hash_before_watermark: Optional[str] = None
    normalized_hash_after_watermark: Optional[str] = None

    # Perceptual hashes (resilient to modifications)
    perceptual_hash_before_watermark: Optional[str] = None
    perceptual_hash_after_watermark: Optional[str] = None

    # Watermark detection
    watermark_presence_expected: bool = True
    watermark_locator: Optional[Dict[str, Any]] = None  # Describes where to find watermark

    # Embedding reference (for neural network similarity)
    embedding_reference: Optional[str] = None  # Reference to stored embedding vector

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


# Type aliases for clarity
ArtifactID = str
WatermarkID = str
ReceiptHash = str
ContentHash = str

__all__ = [
    # Enums
    "ArtifactType",
    "WatermarkType",
    # Core models
    "ArtifactEvidence",
    "ArtifactHashSet",
    "ArtifactFingerprint",
    "WatermarkDescriptor",
    "VerificationResult",
    "ForensicArtifactProfile",
    # Utility functions
    "utc_now_iso",
    "sha256_bytes",
    "sha256_text",
    "canonical_json",
    # Type aliases
    "ArtifactID",
    "WatermarkID",
    "ReceiptHash",
    "ContentHash",
]
