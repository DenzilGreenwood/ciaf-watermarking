"""
CIAF Watermarking - Binary Verification

Verify binary artifacts against forensic evidence.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from ..models import ArtifactEvidence, VerificationResult, sha256_bytes
from .metadata import extract_binary_metadata_watermark


def verify_binary_artifact(
    suspect_binary_bytes: bytes,
    evidence: ArtifactEvidence,
) -> VerificationResult:
    """
    Verify binary artifact against stored evidence.

    Verification Strategy (Multi-Tier):
    - Tier 1: Exact hash match (byte-for-byte identical)
    - Tier 2: Metadata watermark extraction and validation
    - Tier 3: Watermark removal detection

    Args:
        suspect_binary_bytes: Binary to verify
        evidence: Stored evidence for comparison

    Returns:
        VerificationResult with confidence score and tier

    Example:
        >>> from ciaf.watermarks.binary import verify_binary_artifact
        >>>
        >>> # User submits binary for verification
        >>> with open("suspect_binary.exe", "rb") as f:
        ...     suspect_bytes = f.read()
        >>>
        >>> # Retrieve evidence from vault
        >>> evidence = vault.retrieve_evidence(artifact_id)
        >>>
        >>> # Verify
        >>> result = verify_binary_artifact(suspect_bytes, evidence)
        >>>
        >>> if result.is_authentic():
        ...     print(f"✓ Authentic binary (confidence: {result.confidence:.1%})")
        ...     print(f"  Verification tier: {result.verification_tier}")
        ...     print(f"  Model: {evidence.model_id}")
        ... else:
        ...     print("✗ Binary is not authentic or has been modified")
        ...     if result.watermark_removed:
        ...         print("  ⚠ Watermark removal detected!")
    """
    # Check artifact type
    from ..models import ArtifactType

    if evidence.artifact_type != ArtifactType.BINARY:
        raise ValueError(
            f"Evidence is for {evidence.artifact_type.value} artifact, "
            f"not for binary artifact verification"
        )

    # Initialize result
    matches_exact = False  # noqa: F841
    _matches_normalized = False  # Reserved for future use  # noqa: F841
    _watermark_removed = False  # Reserved for future use  # noqa: F841
    is_modification_detected = False  # noqa: F841
    confidence = 0.0
    verification_tier = "none"

    # Compute hash of suspect binary
    suspect_hash = sha256_bytes(suspect_binary_bytes)

    # TIER 1: Exact hash matching
    if suspect_hash == evidence.hashes.content_hash_after_watermark:
        # Perfect match - watermarked version
        matches_exact = True  # noqa: F841
        confidence = 1.0
        verification_tier = "exact"
        return VerificationResult(
            artifact_id=evidence.artifact_id,
            exact_match_after_watermark=True,
            exact_match_before_watermark=False,
            likely_tag_removed=False,
            watermark_present=True,
            watermark_intact=True,
            content_modified=False,
            confidence=1.0,
            notes=["Exact match to distributed watermarked version"],
        )

    # TIER 1b: Watermark removal detection
    if suspect_hash == evidence.hashes.content_hash_before_watermark:
        # Matches original (before watermark) - watermark removed!
        watermark_removed = True  # noqa: F841
        confidence = 0.99  # noqa: F841
        verification_tier = "watermark_removed"  # noqa: F841
        return VerificationResult(
            artifact_id=evidence.artifact_id,
            exact_match_after_watermark=False,
            exact_match_before_watermark=True,
            likely_tag_removed=True,
            watermark_present=False,
            watermark_intact=False,
            content_modified=False,
            confidence=0.99,
            notes=["Exact match to pre-watermark version", "Watermark likely removed"],
        )

    # TIER 2: Metadata watermark extraction
    extracted_watermark = extract_binary_metadata_watermark(suspect_binary_bytes)
    if extracted_watermark:
        # Check if watermark ID matches
        if extracted_watermark.get("watermark_id") == evidence.watermark.watermark_id:
            # Metadata matches - likely modified but watermark intact
            _confidence = 0.90  # noqa: F841
            _verification_tier = "metadata"  # noqa: F841
            _is_modification_detected = True  # Hash doesn't match but watermark does  # noqa: F841
            return VerificationResult(
                artifact_id=evidence.artifact_id,
                exact_match_after_watermark=False,
                exact_match_before_watermark=False,
                likely_tag_removed=False,
                normalized_match_after=True,  # Treat metadata presence as normalized match
                watermark_present=True,
                watermark_intact=True,
                content_modified=True,
                confidence=0.90,
                notes=["Watermark metadata present", "Binary likely modified"],
            )

    # No match found
    return VerificationResult(
        artifact_id=evidence.artifact_id,
        exact_match_after_watermark=False,
        exact_match_before_watermark=False,
        likely_tag_removed=False,
        watermark_present=False,
        watermark_intact=False,
        content_modified=False,
        confidence=0.0,
        notes=["No match found"],
    )


__all__ = [
    "verify_binary_artifact",
]
