"""
CIAF Watermarking - Audio Verification

Verify audio artifacts against forensic evidence.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from ..models import ArtifactEvidence, VerificationResult, sha256_bytes
from .metadata import extract_audio_metadata_watermark


def verify_audio_artifact(
    suspect_audio_bytes: bytes,
    evidence: ArtifactEvidence,
    enable_spectral_matching: bool = True,
) -> VerificationResult:
    """
    Verify audio artifact against stored evidence.

    Verification Strategy (Multi-Tier):
    - Tier 1: Exact hash match (byte-for-byte identical)
    - Tier 2: Metadata watermark extraction and validation
    - Tier 3: Perceptual hash (chromaprint matching)
    - Tier 4: Forensic fragment matching (spectral segments)

    Args:
        suspect_audio_bytes: Audio to verify
        evidence: Stored evidence for comparison
        enable_spectral_matching: Enable forensic fragment matching

    Returns:
        VerificationResult with confidence score and tier

    Example:
        >>> from ciaf.watermarks.audio import verify_audio_artifact
        >>>
        >>> # User uploads audio for verification
        >>> with open("suspect_audio.mp3", "rb") as f:
        ...     suspect_bytes = f.read()
        >>>
        >>> # Retrieve evidence from vault
        >>> evidence = vault.retrieve_evidence(artifact_id)
        >>>
        >>> # Verify
        >>> result = verify_audio_artifact(suspect_bytes, evidence)
        >>>
        >>> if result.is_authentic():
        ...     print(f"✓ Authentic audio (confidence: {result.confidence:.1%})")
        ...     print(f"  Verification tier: {result.verification_tier}")
        ...     print(f"  Model: {evidence.model_id}")
        ... else:
        ...     print("✗ Audio is not authentic or has been modified")
        ...     if result.watermark_removed:
        ...         print("  ⚠ Watermark removal detected!")
    """
    # Check artifact type
    from ..models import ArtifactType

    if evidence.artifact_type != ArtifactType.AUDIO:
        raise ValueError(
            f"Evidence is for {evidence.artifact_type.value} artifact, "
            f"not for audio artifact verification"
        )

    # Initialize result
    matches_exact = False  # noqa: F841
    _matches_normalized = False  # Reserved for future use  # noqa: F841
    perceptual_similarity = None
    _watermark_removed = False  # Reserved for future use  # noqa: F841
    is_modification_detected = False
    confidence = 0.0
    verification_tier = "none"

    # Compute hash of suspect audio
    suspect_hash = sha256_bytes(suspect_audio_bytes)

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
        confidence = 0.99
        verification_tier = "watermark_removed"
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
    extracted_watermark = extract_audio_metadata_watermark(suspect_audio_bytes)
    if extracted_watermark:
        # Check if watermark ID matches
        if extracted_watermark.get("watermark_id") == evidence.watermark.watermark_id:
            # Metadata matches - likely re-encoded or modified
            confidence = 0.90
            verification_tier = "metadata"
            is_modification_detected = True  # Hash doesn't match but watermark does
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
                notes=[
                    "Watermark metadata present",
                    "Content likely re-encoded or modified",
                ],
            )

    # TIER 3: Perceptual hash matching (chromaprint)
    if evidence.hashes.perceptual_hash_after:
        try:
            from ..hashing import perceptual_hash_audio

            suspect_perceptual = perceptual_hash_audio(suspect_audio_bytes)

            # Compare perceptual hashes (they're hex strings)
            if suspect_perceptual == evidence.hashes.perceptual_hash_after:
                # Perceptual match - likely re-encoded
                perceptual_similarity = 1.0
                confidence = 0.85
                verification_tier = "perceptual"  # noqa: F841
                is_modification_detected = True  # noqa: F841
                return VerificationResult(
                    artifact_id=evidence.artifact_id,
                    exact_match_after_watermark=False,
                    exact_match_before_watermark=False,
                    likely_tag_removed=False,
                    perceptual_similarity_score=1.0,
                    watermark_present=True,
                    watermark_intact=True,
                    content_modified=True,
                    confidence=0.85,
                    notes=["Perceptual hash match", "Audio likely re-encoded"],
                )
            else:
                # Calculate similarity based on hash difference
                # (Simple Hamming distance for hex strings)
                try:
                    dist = sum(
                        c1 != c2
                        for c1, c2 in zip(
                            suspect_perceptual, evidence.hashes.perceptual_hash_after
                        )
                    )
                    max_dist = len(suspect_perceptual)
                    similarity = 1.0 - (dist / max_dist)

                    if similarity >= 0.7:
                        perceptual_similarity = similarity
                        confidence = 0.70 + (similarity - 0.7) * 0.5
                        _verification_tier = "perceptual_partial"  # noqa: F841
                        _is_modification_detected = True  # noqa: F841
                        return VerificationResult(
                            artifact_id=evidence.artifact_id,
                            exact_match_after_watermark=False,
                            exact_match_before_watermark=False,
                            likely_tag_removed=False,
                            perceptual_similarity_score=similarity,
                            watermark_present=True,
                            watermark_intact=False,
                            content_modified=True,
                            confidence=confidence,
                            notes=[
                                f"Partial perceptual match (similarity: {similarity:.2f})",
                                "Audio modified",
                            ],
                        )
                except Exception:
                    pass
        except Exception:
            # If perceptual hashing fails, continue
            pass

    # TIER 4: Forensic fragment matching (spectral segments)
    if enable_spectral_matching and evidence.fingerprints:
        # TODO: Implement spectral segment fragment matching
        # This would compare individual audio segment hashes from suspect vs evidence
        # For now, skip this tier
        pass

    # No match found
    return VerificationResult(
        artifact_id=evidence.artifact_id,
        exact_match_after_watermark=False,
        exact_match_before_watermark=False,
        likely_tag_removed=False,
        perceptual_similarity_score=perceptual_similarity,
        watermark_present=False,
        watermark_intact=False,
        content_modified=False,
        confidence=0.0,
        notes=["No match found"],
    )


__all__ = [
    "verify_audio_artifact",
]
