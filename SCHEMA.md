# CIAF Watermarking - Data Schema Specification

**Version:** 1.4.0  
**Last Updated:** 2026-04-06  
**Author:** Denzil James Greenwood  

---

## Overview

This document defines the **canonical data schema** for the CIAF Watermarking system, ensuring consistency across all variables, evidence structures, and information flows. All modules must conform to these specifications.

---

## Table of Contents

1. [Core Identifiers](#1-core-identifiers)
2. [Artifact Evidence Schema](#2-artifact-evidence-schema)
3. [Watermark Descriptor Schema](#3-watermark-descriptor-schema)
4. [Hash Set Schema](#4-hash-set-schema)
5. [Forensic Fragment Schema](#5-forensic-fragment-schema)
6. [Signature Envelope Schema](#6-signature-envelope-schema)
7. [Verification Result Schema](#7-verification-result-schema)
8. [Watermark Specification Schema](#8-watermark-specification-schema)
9. [Context Schema](#9-context-schema)
10. [Naming Conventions](#10-naming-conventions)
11. [Field Validation Rules](#11-field-validation-rules)
12. [Type Mappings](#12-type-mappings)

---

## 1. Core Identifiers

### 1.1 Required ID Formats

All identifiers must follow these patterns:

```python
# Primary Identifiers
artifact_id: str        # UUID v4 format: "550e8400-e29b-41d4-a716-446655440000"
watermark_id: str       # Prefixed UUID: "wmk-{uuid}"
fragment_id: str        # Fragment descriptor: "frag_{index}_{location}"
model_id: str           # Model identifier: "gpt-4", "claude-3", etc.
actor_id: str           # Actor identifier: "user:{username}", "system:{name}"
key_id: str             # Key identifier: "aws-kms:alias/{name}", "local:key-{uuid}"

# Temporal Identifiers
timestamp: str          # ISO 8601 UTC: "2026-04-06T10:30:00Z"
created_at: str         # ISO 8601 UTC timestamp
signed_at: str          # ISO 8601 UTC timestamp

# Content Identifiers
content_hash: str       # SHA-256 hex: 64 characters, lowercase
receipt_hash: str       # SHA-256 hex: 64 characters, lowercase
```

### 1.2 ID Generation Rules

```python
# Artifact ID
import uuid
artifact_id = str(uuid.uuid4())

# Watermark ID
watermark_id = f"wmk-{uuid.uuid4()}"

# Fragment ID
fragment_id = f"frag_{index}_{location}"  # e.g., "frag_0_beginning"

# Timestamp
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat()
```

---

## 2. Artifact Evidence Schema

### 2.1 Core Evidence Structure

```python
class ArtifactEvidence(BaseModel):
    """Primary evidence record for AI-generated artifacts."""
    
    # === REQUIRED FIELDS ===
    artifact_id: str                    # Primary key (UUID v4)
    artifact_type: ArtifactType         # Enum: TEXT, IMAGE, PDF, etc.
    mime_type: str                      # Standard MIME type
    created_at: str                     # ISO 8601 UTC timestamp
    
    # === MODEL PROVENANCE (REQUIRED) ===
    model_id: str                       # Model identifier
    model_version: str                  # Model version string
    actor_id: str                       # Actor/user identifier
    
    # === CRYPTOGRAPHIC LINKAGE (REQUIRED) ===
    prompt_hash: str                    # SHA-256 of input prompt
    output_hash_raw: str                # SHA-256 before watermark
    output_hash_distributed: str        # SHA-256 after watermark
    
    # === WATERMARK DETAILS (REQUIRED) ===
    watermark: WatermarkDescriptor      # Watermark metadata
    
    # === DUAL-STATE HASHING (REQUIRED) ===
    hashes: ArtifactHashSet             # Complete hash set
    
    # === FORENSIC FINGERPRINTS (OPTIONAL) ===
    fingerprints: List[ArtifactFingerprint] = []
    
    # === METADATA (OPTIONAL) ===
    metadata: Dict[str, Any] = {}
    
    # === CHAINING (OPTIONAL) ===
    prior_receipt_hash: Optional[str] = None
    
    # === SIGNATURE (OPTIONAL) ===
    signature: Optional[SignatureEnvelope] = None
    merkle_leaf_hash: Optional[str] = None
```

### 2.2 Evidence Field Constraints

| Field | Type | Required | Format | Validation |
|-------|------|----------|--------|------------|
| `artifact_id` | str | ✅ | UUID v4 | 36 chars, valid UUID |
| `artifact_type` | ArtifactType | ✅ | Enum | Must be valid enum value |
| `mime_type` | str | ✅ | MIME | Valid MIME type string |
| `created_at` | str | ✅ | ISO 8601 | RFC 3339 compliant |
| `model_id` | str | ✅ | String | Min 1 char, max 100 |
| `model_version` | str | ✅ | String | Min 1 char, max 50 |
| `actor_id` | str | ✅ | String | Min 1 char, max 200 |
| `prompt_hash` | str | ✅ | SHA-256 | 64 hex chars, lowercase |
| `output_hash_raw` | str | ✅ | SHA-256 | 64 hex chars, lowercase |
| `output_hash_distributed` | str | ✅ | SHA-256 | 64 hex chars, lowercase |
| `watermark` | WatermarkDescriptor | ✅ | Object | Valid WatermarkDescriptor |
| `hashes` | ArtifactHashSet | ✅ | Object | Valid ArtifactHashSet |

### 2.3 Artifact Type Enum

```python
class ArtifactType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    JSON = "json"
    BINARY = "binary"
    VIDEO = "video"
    AUDIO = "audio"
```

---

## 3. Watermark Descriptor Schema

### 3.1 Structure

```python
class WatermarkDescriptor(BaseModel):
    """Complete watermark metadata."""
    
    # === REQUIRED ===
    watermark_id: str                   # Unique watermark ID
    watermark_type: WatermarkType       # Enum: VISIBLE, METADATA, etc.
    
    # === OPTIONAL ===
    tag_text: Optional[str] = None      # Human-readable tag
    verification_url: Optional[str] = None  # Verification endpoint
    qr_payload: Optional[str] = None    # QR code data
    metadata_fields: Dict[str, str] = {}  # Custom metadata
    embed_method: Optional[str] = None  # Technical method
    removal_resistance: Optional[str] = None  # "low", "medium", "high"
    location: Optional[str] = None      # Watermark location
```

### 3.2 Watermark Type Enum

```python
class WatermarkType(str, Enum):
    NONE = "none"
    VISIBLE = "visible"           # Visible tag/footer/header
    METADATA = "metadata"         # Embedded in file metadata
    EMBEDDED = "embedded"         # Steganographic embedding
    HYBRID = "hybrid"             # Multiple techniques
    QR_CODE = "qr_code"          # QR code watermark
```

---

## 4. Hash Set Schema

### 4.1 Dual-State Hash Structure

```python
class ArtifactHashSet(BaseModel):
    """Dual-state cryptographic hashing."""
    
    # === REQUIRED: DUAL-STATE HASHES ===
    content_hash_before_watermark: str  # SHA-256 before watermark
    content_hash_after_watermark: str   # SHA-256 after watermark
    
    # === OPTIONAL: CANONICAL HASH ===
    canonical_receipt_hash: Optional[str] = None
    
    # === OPTIONAL: NORMALIZED HASHES ===
    normalized_hash_before: Optional[str] = None
    normalized_hash_after: Optional[str] = None
    
    # === OPTIONAL: PERCEPTUAL HASHES ===
    perceptual_hash_before: Optional[str] = None
    perceptual_hash_after: Optional[str] = None
    
    # === OPTIONAL: SIMHASH (TEXT) ===
    simhash_before: Optional[str] = None
    simhash_after: Optional[str] = None
    
    # === OPTIONAL: FORENSIC FRAGMENTS ===
    forensic_fragments: Optional[ForensicFragmentSet] = None
```

### 4.2 Hash Computation Standards

```python
# SHA-256 (Content Hash)
def sha256_bytes(data: bytes) -> str:
    """Return: 64-char lowercase hex string"""
    return hashlib.sha256(data).hexdigest()

def sha256_text(text: str) -> str:
    """Return: 64-char lowercase hex string"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# Canonical JSON Hash
def canonical_json(data: Dict[str, Any]) -> bytes:
    """Return: UTF-8 encoded canonical JSON bytes"""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
```

---

## 5. Forensic Fragment Schema

### 5.1 Fragment Base Structure

```python
class ForensicFragment(BaseModel):
    """Base forensic fragment."""
    
    # === REQUIRED ===
    fragment_id: str            # Unique fragment ID
    fragment_type: str          # Type: "text", "image_patch", etc.
    entropy_score: float        # 0.0-1.0
    sampling_method: str        # e.g., "begin", "spatial"
    content_position: int       # Position in artifact
```

### 5.2 Text Fragment Schema

```python
class TextForensicFragment(ForensicFragment):
    """High-entropy text fragment."""
    
    # === REQUIRED ===
    offset_start: int                   # Character offset
    offset_end: int                     # End offset
    fragment_length: int                # Length
    sample_location: str                # "beginning", "middle", "end"
    fragment_text: str                  # CRITICAL: Actual text
    fragment_hash_before: str           # SHA-256 before watermark
    fragment_hash_after: str            # SHA-256 after watermark
    
    # === OPTIONAL ===
    fragment_simhash_before: Optional[str] = None
    fragment_simhash_after: Optional[str] = None
```

### 5.3 Image Fragment Schema

```python
class ImageForensicFragment(ForensicFragment):
    """High-entropy image patch."""
    
    # === REQUIRED ===
    patch_grid_position: str            # e.g., "grid_2_4"
    patch_hash_before: str              # pHash before watermark
    patch_hash_after: str               # pHash after watermark
    region_coordinates: tuple           # (x, y, width, height)
    
    # === OPTIONAL ===
    patch_ahash_before: Optional[str] = None
    patch_dhash_before: Optional[str] = None
    patch_whash_before: Optional[str] = None
```

### 5.4 Video Fragment Schema

```python
class VideoForensicSnippet(ForensicFragment):
    """Temporal keyframe sample."""
    
    # === REQUIRED ===
    timestamp_ms: int                   # Position in timeline
    frame_index: int                    # Frame number
    frame_type: str                     # "I-Frame"
    frame_duration_ms: int              # Duration from prior frame
    frame_patch_hashes: List[str]       # Visual DNA
    
    # === OPTIONAL ===
    temporal_motion_hash: Optional[str] = None
    motion_confidence: float = 0.0
```

### 5.5 Audio Fragment Schema

```python
class AudioForensicSegment(ForensicFragment):
    """Spectrogram fingerprint."""
    
    # === REQUIRED ===
    start_time_ms: int                  # Position in track
    segment_duration_ms: int            # Length (2000-5000ms typical)
    spectrogram_hash: str               # pHash of spectrogram
    frequency_centroid: float           # Average frequency (Hz)
    spectral_flatness: float            # 0.0-1.0
    
    # === OPTIONAL ===
    spectrogram_hash_before: Optional[str] = None
    spectrogram_hash_after: Optional[str] = None
```

### 5.6 Fragment Set Schema

```python
class ForensicFragmentSet(BaseModel):
    """Collection of forensic fragments."""
    
    # === REQUIRED ===
    fragment_count: int
    sampling_strategy: str              # "multi_point", "spatial_diversity"
    total_coverage_percent: float       # Estimated coverage
    
    # === TYPED FRAGMENT LISTS ===
    text_fragments: List[TextForensicFragment] = []
    image_fragments: List[ImageForensicFragment] = []
    video_snippets: List[VideoForensicSnippet] = []
    audio_segments: List[AudioForensicSegment] = []
    
    # === STATISTICS ===
    min_entropy_threshold: float = 0.6
    cumulative_entropy_score: float = 0.0
```

---

## 6. Signature Envelope Schema

### 6.1 Signature Structure

```python
class SignatureEnvelope(BaseModel):
    """Complete cryptographic signature payload."""
    
    # === REQUIRED ===
    payload_hash: str                   # SHA-256 of payload (64 hex)
    hash_algorithm: str                 # "SHA-256"
    signature_value: str                # Encoded signature
    signature_encoding: SignatureEncoding  # Enum: BASE64, HEX
    signed_at: str                      # RFC 3339 timestamp
    metadata: SignatureMetadata         # Signature metadata
```

### 6.2 Signature Metadata Schema

```python
class SignatureMetadata(BaseModel):
    """Signature metadata for audit trail."""
    
    # === REQUIRED ===
    signature_algorithm: str            # "Ed25519"
    key_id: str                         # Key identifier
    canonicalization_version: str       # "RFC8785-like/1.0"
    key_backend: KeyBackend             # Enum: LOCAL, KMS, HSM
    
    # === OPTIONAL ===
    signing_service: Optional[str] = None
    public_key_ref: Optional[str] = None
    verification_method: Optional[str] = None
```

### 6.3 Key Backend Enum

```python
class KeyBackend(str, Enum):
    LOCAL = "local"
    KMS = "kms"
    HSM = "hsm"
    CLOUDHSM = "cloudhsm"
    EXTERNAL_KMS = "external_kms"
```

---

## 7. Verification Result Schema

### 7.1 Basic Verification Result

```python
class VerificationResult(BaseModel):
    """Result of artifact verification."""
    
    # === IDENTIFICATION ===
    artifact_id: str = ""
    
    # === EXACT MATCHING ===
    exact_match_after_watermark: bool = False
    exact_match_before_watermark: bool = False
    likely_tag_removed: bool = False
    
    # === NORMALIZED MATCHING ===
    normalized_match_before: bool = False
    normalized_match_after: bool = False
    
    # === SIMILARITY MATCHING ===
    perceptual_similarity_score: Optional[float] = None  # 0.0-1.0
    simhash_distance: Optional[int] = None
    
    # === FORENSIC ANALYSIS ===
    watermark_present: bool = False
    watermark_intact: bool = False
    content_modified: bool = False
    
    # === EXPLANATION ===
    notes: List[str] = []
    confidence: float = 0.0             # 0.0-1.0
    
    # === EVIDENCE REFERENCE ===
    evidence_record: Optional[ArtifactEvidence] = None
```

### 7.2 Fragment Match Result

```python
class FragmentMatchResult(BaseModel):
    """Result of single fragment matching."""
    
    # === REQUIRED ===
    fragment_id: str
    matched: bool
    confidence: float                   # 0.0-1.0
    
    # === OPTIONAL ===
    match_position: Optional[int] = None
    match_details: str = ""
```

### 7.3 Forensic Verification Summary

```python
class ForensicVerificationSummary(BaseModel):
    """Summary of forensic fragment verification."""
    
    # === COUNTS ===
    total_fragments_checked: int
    fragments_matched: int
    fragments_not_matched: int
    
    # === CONFIDENCE ===
    match_confidence: float             # 0.0-1.0
    legal_defensibility: str            # "high", "medium", "low"
    
    # === DETAILS ===
    forensic_matches: List[FragmentMatchResult] = []
    notes: List[str] = []
```

### 7.4 Hierarchical Verification Result

```python
class HierarchicalVerificationResult(BaseModel):
    """Three-tier hierarchical verification result."""
    
    # === IDENTIFICATION ===
    artifact_id: str
    
    # === TIER RESULTS ===
    final_tier: VerificationTier        # Enum: TIER1, TIER2, TIER3, NO_MATCH
    is_authentic: bool
    overall_confidence: float           # 0.0-1.0
    
    # === TIER EXECUTION DETAILS ===
    tier1_result: Optional[VerificationStep] = None
    tier2_result: Optional[VerificationStep] = None
    tier3_result: Optional[VerificationStep] = None
    
    # === COST TRACKING ===
    total_execution_time_ms: float
    tier1_cost_ms: float
    tier2_cost_ms: float
    tier3_cost_ms: float
    
    # === DETAILED FINDINGS ===
    steps: List[VerificationStep] = []
    tier2_fragment_results: Optional[ForensicVerificationSummary] = None
    tier3_similarity_score: Optional[float] = None
    
    # === AUDIT TRAIL ===
    notes: List[str] = []
    evidence_record: Optional[ArtifactEvidence] = None
```

---

## 8. Watermark Specification Schema

### 8.1 Text Watermark Spec

**Not explicitly modeled** - uses function parameters directly:
```python
def apply_text_watermark(
    raw_text: str,
    watermark_id: str,
    verification_url: str,
    style: str = "footer",  # "footer", "header", "inline"
) -> str:
    ...
```

### 8.2 Image Watermark Spec

```python
@dataclass
class ImageWatermarkSpec:
    """Image watermarking specification."""
    
    mode: Literal["visual", "steganographic", "hybrid"] = "visual"
    text: Optional[str] = None
    opacity: float = 0.3                # 0.0-1.0
    position: Position = "bottom_right"
    font_size: int = 18
    margin: int = 24
    include_qr: bool = False
    qr_payload: Optional[str] = None
    qr_position: Position = "top_right"
    qr_size: int = 100
    text_color: Tuple[int, int, int] = (255, 255, 255)
```

### 8.3 Audio Watermark Spec

```python
@dataclass
class AudioWatermarkSpec:
    """Audio spectral watermark specification."""
    
    strength: float = 0.1               # 0.0-1.0
    frequency_band: str = "high"        # "high" or "low"
    carrier_freq: int = 18000           # Hz (1000-20000)
    spread_spectrum: bool = True
```

### 8.4 Video Watermark Spec

```python
@dataclass
class VideoWatermarkSpec:
    """Video watermarking specification."""
    
    mode: Literal["overlay", "metadata", "hybrid"] = "overlay"
    text: Optional[str] = None
    opacity: float = 0.3
    position: str = "bottom_right"
    qr_enabled: bool = False
    qr_payload: Optional[str] = None
    qr_size: int = 80
```

---

## 9. Context Schema

### 9.1 Watermark Context

```python
@dataclass
class WatermarkContext:
    """Watermarking context for auto-injection."""
    
    # === REQUIRED ===
    model_id: str
    model_version: str
    actor_id: str
    
    # === OPTIONAL ===
    metadata: Dict[str, Any] = None
```

---

## 10. Naming Conventions

### 10.1 Variable Naming Standards

| Category | Pattern | Examples |
|----------|---------|----------|
| **IDs** | `{type}_id` | `artifact_id`, `watermark_id`, `fragment_id` |
| **Hashes** | `{content}_hash` | `content_hash`, `prompt_hash`, `receipt_hash` |
| **Timestamps** | `{event}_at` | `created_at`, `signed_at`, `verified_at` |
| **Counts** | `{noun}_count` or `num_{nouns}` | `fragment_count`, `num_frames` |
| **Flags** | `is_{condition}` or `has_{feature}` | `is_authentic`, `has_watermark` |
| **URLs** | `{purpose}_url` | `verification_url`, `callback_url` |
| **Scores** | `{metric}_score` | `entropy_score`, `confidence_score` |
| **Positions** | `{context}_position` | `match_position`, `content_position` |

### 10.2 Function Naming Standards

| Category | Pattern | Examples |
|----------|---------|----------|
| **Builders** | `build_{type}_evidence` | `build_text_artifact_evidence()` |
| **Appliers** | `apply_{type}_watermark` | `apply_text_watermark()` |
| **Extractors** | `extract_{content}` | `extract_watermark()`, `extract_metadata()` |
| **Verifiers** | `verify_{type}` | `verify_text_artifact()`, `verify_fragments()` |
| **Selectors** | `select_{type}_fragments` | `select_text_forensic_fragments()` |
| **Computations** | `compute_{metric}` | `compute_perceptual_hash()`, `compute_entropy()` |
| **Generators** | `generate_{output}` | `generate_watermark_id()` |

### 10.3 Module Organization

```
artifact_type/
    ├── core.py              # Evidence building (build_*_artifact_evidence)
    ├── watermark.py         # Watermark application (apply_*_watermark)
    ├── verification.py      # Verification logic (verify_*_artifact)
    ├── metadata.py          # Metadata operations
    └── {specific}.py        # Type-specific features
```

---

## 11. Field Validation Rules

### 11.1 String Fields

| Field Type | Min Length | Max Length | Pattern |
|------------|------------|------------|---------|
| `artifact_id` | 36 | 36 | UUID v4 |
| `watermark_id` | 40 | 50 | `wmk-{uuid}` |
| `fragment_id` | 8 | 100 | `frag_{index}_{location}` |
| `model_id` | 1 | 100 | Alphanumeric + `-_` |
| `model_version` | 1 | 50 | Semantic versioning preferred |
| `actor_id` | 1 | 200 | `{type}:{identifier}` |
| `content_hash` | 64 | 64 | Hex lowercase |
| `timestamp` | 20 | 35 | ISO 8601 |

### 11.2 Numeric Fields

| Field Type | Min | Max | Type |
|------------|-----|-----|------|
| `entropy_score` | 0.0 | 1.0 | float |
| `confidence` | 0.0 | 1.0 | float |
| `opacity` | 0.0 | 1.0 | float |
| `timestamp_ms` | 0 | ∞ | int |
| `offset_start` | 0 | ∞ | int |
| `fragment_length` | 1 | ∞ | int |

### 11.3 Required vs Optional Fields

**ALWAYS REQUIRED:**
- `artifact_id`
- `artifact_type`
- `created_at`
- `model_id`
- `model_version`
- `actor_id`
- All dual-state hashes (`content_hash_before_watermark`, `content_hash_after_watermark`)

**CONDITIONALLY REQUIRED:**
- `forensic_fragments` - Required if `enable_forensic_fragments=True`
- `signature` - Required for production vault storage
- `perceptual_hash_*` - Required for images/video/audio

**OPTIONAL:**
- `metadata`
- `prior_receipt_hash`
- `fingerprints`
- Most `Optional[...]` typed fields

---

## 12. Type Mappings

### 12.1 Artifact Type → MIME Type Mapping

```python
MIME_TYPE_MAPPING = {
    ArtifactType.TEXT: "text/plain",
    ArtifactType.IMAGE: "image/png",
    ArtifactType.PDF: "application/pdf",
    ArtifactType.JSON: "application/json",
    ArtifactType.BINARY: "application/octet-stream",
    ArtifactType.VIDEO: "video/mp4",
    ArtifactType.AUDIO: "audio/wav",
}
```

### 12.2 Watermark Type → Implementation Mapping

```python
WATERMARK_IMPLEMENTATION = {
    WatermarkType.VISIBLE: "text_overlay",
    WatermarkType.METADATA: "metadata_embedding",
    WatermarkType.EMBEDDED: "steganographic",
    WatermarkType.QR_CODE: "qr_code_generation",
    WatermarkType.HYBRID: "combined_methods",
}
```

### 12.3 Fragment Type → Class Mapping

```python
FRAGMENT_CLASS_MAPPING = {
    "text": TextForensicFragment,
    "image_patch": ImageForensicFragment,
    "video_frame": VideoForensicSnippet,
    "audio_segment": AudioForensicSegment,
}
```

---

## 13. Consistency Checklist

### 13.1 When Creating New Evidence

- [ ] Use UUID v4 for `artifact_id`
- [ ] Generate `watermark_id` as `wmk-{uuid}`
- [ ] Set `created_at` to `utc_now_iso()`
- [ ] Compute SHA-256 for all hash fields
- [ ] Include both `content_hash_before_watermark` and `content_hash_after_watermark`
- [ ] Validate all required fields are present
- [ ] Ensure `artifact_type` matches actual content type
- [ ] Set appropriate `mime_type`

### 13.2 When Adding Forensic Fragments

- [ ] Set `fragment_id` following pattern: `frag_{index}_{location}`
- [ ] Compute `entropy_score` between 0.0-1.0
- [ ] Store actual `fragment_text` for text fragments
- [ ] Include both `fragment_hash_before` and `fragment_hash_after`
- [ ] Validate fragment count matches strategy
- [ ] Ensure minimum entropy threshold (default: 0.6)

### 13.3 When Verifying Artifacts

- [ ] Return `VerificationResult` with all required fields
- [ ] Set `confidence` between 0.0-1.0
- [ ] Include explanatory `notes` for audit trail
- [ ] Reference original `evidence_record` if available
- [ ] Update all boolean flags correctly

### 13.4 When Signing Evidence

- [ ] Use `SignatureEnvelope` pattern (v1.3.0+)
- [ ] Compute `payload_hash` from canonical representation
- [ ] Set `signed_at` to current UTC timestamp
- [ ] Include complete `SignatureMetadata`
- [ ] Declare `key_backend` for compliance

---

## 14. Migration Guide

### 14.1 From Old Schema → Current Schema

If migrating older evidence records:

```python
def migrate_evidence_v1_to_v2(old_evidence: Dict) -> ArtifactEvidence:
    """Migrate old evidence format to current schema."""
    
    # Map old field names to new
    new_evidence = {
        "artifact_id": old_evidence.get("id"),
        "artifact_type": old_evidence.get("type"),
        "created_at": old_evidence.get("timestamp"),
        # ... etc
    }
    
    # Validate and construct
    return ArtifactEvidence(**new_evidence)
```

---

## 15. Best Practices

### 15.1 Do's

✅ **DO** always use UUID v4 for `artifact_id`  
✅ **DO** compute dual-state hashes (before and after watermark)  
✅ **DO** store actual fragment text in `TextForensicFragment.fragment_text`  
✅ **DO** use ISO 8601 UTC timestamps  
✅ **DO** validate all required fields before storing  
✅ **DO** use pydantic models for all data structures  
✅ **DO** include audit trail in `notes` fields  

### 15.2 Don'ts

❌ **DON'T** use sequential integers for `artifact_id`  
❌ **DON'T** store only post-watermark hashes  
❌ **DON'T** omit `fragment_text` from text fragments  
❌ **DON'T** use local timestamps (always UTC)  
❌ **DON'T** bypass validation with `.construct()`  
❌ **DON'T** use raw dicts instead of models  
❌ **DON'T** modify evidence after signing  

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-24 | Initial schema definition |
| 1.1.0 | 2026-03-28 | Added forensic fragments |
| 1.2.0 | 2026-03-30 | Added hierarchical verification |
| 1.3.0 | 2026-03-30 | Migrated to SignatureEnvelope pattern |
| 1.4.0 | 2026-04-06 | Complete schema documentation |

---

## References

- **Models:** [models.py](models.py)
- **Signature Envelope:** [signature_envelope.py](signature_envelope.py)
- **Fragment Selection:** [fragment_selection.py](fragment_selection.py)
- **Fragment Verification:** [fragment_verification.py](fragment_verification.py)
- **Hierarchical Verification:** [hierarchical_verification.py](hierarchical_verification.py)

---

**Maintained by:** Denzil James Greenwood  
**Contact:** via GitHub repository  
**License:** BUSL-1.1 (converts to Apache 2.0 on 2029-01-01)
