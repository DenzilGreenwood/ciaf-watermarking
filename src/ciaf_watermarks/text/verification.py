"""
CIAF Watermarking - Text Verification

Forensic verification of suspect text artifacts against stored evidence.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.5.0
"""

import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

from ..models import (
    ArtifactEvidence,
    VerificationResult,
    ArtifactType,
)
from ..hashing import (
    sha256_text,
    normalized_text_hash,
    simhash_text,
    simhash_distance,
)
from .watermark import (
    has_watermark,
    extract_watermark_id,
)


def verify_text_artifact(
    suspect_text: str,
    evidence: ArtifactEvidence,
    check_normalized: bool = True,
    check_simhash: bool = True,
    simhash_threshold: int = 10,
) -> VerificationResult:
    """
    Verify suspect text against stored evidence record.

    This is the main forensic verification function.

    Checks:
    1. Exact match to distributed (watermarked) version
    2. Exact match to original (pre-watermark) version
    3. Normalized match (resilient to formatting)
    4. SimHash similarity (resilient to minor edits)
    5. Watermark presence/removal detection

    Args:
        suspect_text: Text to verify
        evidence: Stored evidence record
        check_normalized: Whether to check normalized hashes
        check_simhash: Whether to compute SimHash similarity
        simhash_threshold: Max hamming distance for SimHash match (default 10)

    Returns:
        VerificationResult with detailed analysis
    """
    if evidence.artifact_type != ArtifactType.TEXT:
        raise ValueError(f"Evidence is not for text artifact: {evidence.artifact_type}")

    notes = []
    suspect_hash = sha256_text(suspect_text)

    # Check 1: Exact match to distributed version (with watermark)
    match_after = suspect_hash == evidence.hashes.content_hash_after_watermark
    if match_after:
        notes.append("[OK] Exact match to distributed watermarked version.")
        notes.append("  This is the authentic distributed copy.")

    # Check 2: Exact match to original version (without watermark)
    match_before = suspect_hash == evidence.hashes.content_hash_before_watermark
    if match_before:
        notes.append("[OK] Exact match to original pre-watermark version.")
        notes.append("  Core content is authentic.")

    # Check 3: Watermark removal detection
    likely_removed = False
    if match_before and not match_after:
        likely_removed = True
        notes.append("[WARN] Watermark likely removed!")
        notes.append("  Content matches pre-watermark version but watermark is missing.")

    # Check 4: Watermark presence
    watermark_present = has_watermark(suspect_text)
    watermark_intact = False

    if watermark_present:
        extracted_id = extract_watermark_id(suspect_text)
        if extracted_id == evidence.watermark.watermark_id:
            watermark_intact = True
            notes.append("[OK] Original watermark present and intact.")
        else:
            notes.append("[WARN] Different watermark detected (possible forgery).")
    elif not match_after:
        notes.append("[FAIL] No watermark detected in suspect text.")

    # Check 5: Normalized hash matching (format-resilient)
    normalized_match_before = False
    normalized_match_after = False

    if check_normalized and evidence.hashes.normalized_hash_before:
        suspect_normalized = normalized_text_hash(suspect_text)

        if suspect_normalized == evidence.hashes.normalized_hash_before:
            normalized_match_before = True
            notes.append("[OK] Normalized hash matches pre-watermark version.")
            notes.append("  Content is authentic despite formatting differences.")

        if evidence.hashes.normalized_hash_after:
            if suspect_normalized == evidence.hashes.normalized_hash_after:
                normalized_match_after = True
                notes.append("[OK] Normalized hash matches post-watermark version.")

    # Check 6: SimHash similarity (content-resilient)
    simhash_dist = None
    perceptual_similarity = None

    if check_simhash and evidence.hashes.simhash_before:
        suspect_simhash = simhash_text(suspect_text)
        simhash_dist = simhash_distance(suspect_simhash, evidence.hashes.simhash_before)

        if simhash_dist <= simhash_threshold:
            # Calculate similarity score (0.0-1.0)
            perceptual_similarity = 1.0 - (simhash_dist / 64.0)
            notes.append(
                f"[OK] SimHash similarity detected (distance={simhash_dist}, score={perceptual_similarity:.3f})."
            )
            notes.append("  Content is likely modified version of original.")
        else:
            notes.append(
                f"[FAIL] SimHash distance too large: {simhash_dist} (threshold: {simhash_threshold})."
            )

    # Check 6.5: Distinctive Anchor Similarity (forensic layer)
    # Validated at 1.19 × 10⁻⁸ collision rate on 104k document corpus
    # Zero human-LLM collisions observed, zero cross-model LLM collisions
    anchor_match_score = None
    anchor_match = False

    try:
        from ..forensics.text import (
            compare_anchor_fingerprints,
            DistinctiveAnchorFingerprint,
        )

        # Check if evidence has forensic anchor data
        if "forensic_anchor" in evidence.metadata:
            forensic_meta = evidence.metadata["forensic_anchor"]

            # Reconstruct fingerprint from metadata with proper hash preservation
            evidence_fingerprint = DistinctiveAnchorFingerprint.from_dict(
                {
                    "config": {
                        "zone_word_size": forensic_meta.get("zone_words", 400),
                        "top_k": forensic_meta.get("top_k", 10),
                        "strong_threshold": forensic_meta.get("strong_threshold", 0.40),
                        "zone_match_requirement": forensic_meta.get("zone_match_requirement", 2),
                    },
                    "zone_anchors": forensic_meta.get("zone_anchors", {}),
                    "fingerprint_hash": forensic_meta.get(
                        "fingerprint_hash", ""
                    ),  # Use stored hash
                    "metadata": forensic_meta.get(
                        "fingerprint_metadata", {}
                    ),  # Includes short_document flags
                }
            )

            # Compare suspect text against evidence fingerprint
            anchor_result = compare_anchor_fingerprints(
                suspect_text,
                evidence_fingerprint,
            )

            anchor_match = anchor_result.overall_match
            anchor_match_score = (
                anchor_result.match_score
            )  # Mean zone similarity, not calibrated confidence

            if anchor_match:
                notes.append(
                    f"[OK] Distinctive anchor fingerprint matches (zones: {anchor_result.matched_zones}/{anchor_result.required_zones}, match score: {anchor_match_score:.3f})."
                )
                notes.append(
                    "  Forensic analysis: Text exhibits same zone-level distinctive patterns."
                )
                notes.append(
                    f"  Zone scores: beginning={anchor_result.zone_scores.get('beginning', 0):.2f}, middle={anchor_result.zone_scores.get('middle', 0):.2f}, end={anchor_result.zone_scores.get('end', 0):.2f}"
                )
            else:
                notes.append(
                    f"[INFO] Anchor fingerprint weak match (zones: {anchor_result.matched_zones}/{anchor_result.required_zones}, match score: {anchor_match_score:.3f})."
                )
    except Exception as e:
        # Forensic analysis is optional; don't fail verification if it doesn't work
        logger.warning(f"Forensic anchor comparison failed: {e}", exc_info=True)
        notes.append("[INFO] Forensic anchor comparison skipped due to error.")

    # Check 7: Content modification analysis
    content_modified = False
    if not match_before and not match_after:
        if normalized_match_before or (perceptual_similarity and perceptual_similarity > 0.8):
            content_modified = True
            notes.append("[WARN] Content appears modified from original.")
        else:
            notes.append("[FAIL] No match found - content may be unrelated or heavily modified.")

    # Determine overall confidence
    # Combines multiple verification layers for robust assessment
    confidence = 0.0
    if match_after:
        confidence = 1.0  # Perfect match to distributed version
    elif match_before:
        confidence = 0.95  # Original content, watermark removed
    elif normalized_match_after or normalized_match_before:
        confidence = 0.90  # Formatting changes, content intact
    elif anchor_match and anchor_match_score:
        # Forensic anchor match (validated method)
        # 0.85 multiplier is a heuristic policy decision, not from validation study
        confidence = max(confidence, 0.85 * anchor_match_score)
    elif perceptual_similarity:
        # SimHash similarity
        confidence = max(confidence, perceptual_similarity)
    else:
        confidence = 0.0  # No match found

    return VerificationResult(
        artifact_id=evidence.artifact_id,
        exact_match_after_watermark=match_after,
        exact_match_before_watermark=match_before,
        likely_tag_removed=likely_removed,
        normalized_match_before=normalized_match_before,
        normalized_match_after=normalized_match_after,
        perceptual_similarity_score=perceptual_similarity,
        simhash_distance=simhash_dist,
        watermark_present=watermark_present,
        watermark_intact=watermark_intact,
        content_modified=content_modified,
        notes=notes,
        confidence=confidence,
        evidence_record=evidence,
    )


def verify_against_multiple_evidence(
    suspect_text: str,
    evidence_records: List[ArtifactEvidence],
    min_confidence: float = 0.8,
) -> List[VerificationResult]:
    """
    Verify suspect text against multiple evidence records.

    Use case: Check if suspect text matches any known artifact.

    Args:
        suspect_text: Text to verify
        evidence_records: List of evidence records to check
        min_confidence: Minimum confidence threshold (0.0-1.0)

    Returns:
        List of VerificationResults with confidence >= min_confidence,
        sorted by confidence (highest first)
    """
    results = []

    for evidence in evidence_records:
        if evidence.artifact_type != ArtifactType.TEXT:
            continue

        result = verify_text_artifact(suspect_text, evidence)

        if result.confidence >= min_confidence:
            results.append(result)

    # Sort by confidence (highest first)
    results.sort(key=lambda r: r.confidence, reverse=True)

    return results


def quick_verify(suspect_text: str, evidence: ArtifactEvidence) -> bool:
    """
    Quick verification - just check if authentic.

    Args:
        suspect_text: Text to verify
        evidence: Evidence record

    Returns:
        True if authentic (any match found), False otherwise
    """
    result = verify_text_artifact(suspect_text, evidence)
    return result.is_authentic()


def analyze_suspect_text(suspect_text: str) -> dict:
    """
    Analyze suspect text for forensic indicators.

    Provides insights without requiring evidence record:
    - Watermark presence
    - Text characteristics
    - Potential tampering indicators

    Args:
        suspect_text: Text to analyze

    Returns:
        Dictionary of analysis results
    """
    analysis: Dict[str, Any] = {
        "text_length": len(suspect_text),
        "has_ciaf_watermark": has_watermark(suspect_text),
        "watermark_id": extract_watermark_id(suspect_text),
        "characteristics": {},
        "tampering_indicators": [],
    }

    # Detect suspicious patterns
    if re.search(r"---.*removed.*---", suspect_text, re.IGNORECASE):
        analysis["tampering_indicators"].append("Text contains 'removed' marker")

    if re.search(r"\[.*stripped.*\]", suspect_text, re.IGNORECASE):
        analysis["tampering_indicators"].append("Text contains 'stripped' marker")

    # Check for common AI output patterns
    ai_patterns = [
        r"As an AI",
        r"I'm sorry, but",
        r"I cannot",
        r"I don't have the ability",
        r"based on the provided information",
    ]

    for pattern in ai_patterns:
        if re.search(pattern, suspect_text, re.IGNORECASE):
            analysis["characteristics"]["likely_ai_generated"] = True
            break

    return analysis


def format_verification_report(result: VerificationResult, detailed: bool = True) -> str:
    """
    Format verification result as human-readable report.

    Args:
        result: VerificationResult to format
        detailed: Whether to include detailed notes

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("CIAF Artifact Verification Report")
    lines.append("=" * 60)
    lines.append(f"Artifact ID: {result.artifact_id}")
    lines.append(f"Confidence: {result.confidence:.1%}")
    lines.append("")

    # Overall verdict
    if result.is_authentic():
        lines.append("VERDICT: [OK] AUTHENTIC")
    else:
        lines.append("VERDICT: [FAIL] NOT VERIFIED")

    lines.append("")
    lines.append("Checks:")
    lines.append(
        f"  Exact match (watermarked):  {'[OK]' if result.exact_match_after_watermark else '[FAIL]'}"
    )
    lines.append(
        f"  Exact match (original):     {'[OK]' if result.exact_match_before_watermark else '[FAIL]'}"
    )
    lines.append(
        f"  Watermark present:          {'[OK]' if result.watermark_present else '[FAIL]'}"
    )
    lines.append(f"  Watermark intact:           {'[OK]' if result.watermark_intact else '[FAIL]'}")

    if result.likely_tag_removed:
        lines.append("")
        lines.append("[WARN] WARNING: Watermark likely removed!")

    if result.content_modified:
        lines.append("")
        lines.append("[WARN] WARNING: Content appears modified!")

    if detailed and result.notes:
        lines.append("")
        lines.append("Detailed Analysis:")
        for note in result.notes:
            lines.append(f"  {note}")

    if result.simhash_distance is not None:
        lines.append("")
        lines.append(f"SimHash Distance: {result.simhash_distance}/64")

    if result.perceptual_similarity_score is not None:
        lines.append(f"Similarity Score: {result.perceptual_similarity_score:.1%}")

    lines.append("=" * 60)

    return "\n".join(lines)


__all__ = [
    "verify_text_artifact",
    "verify_against_multiple_evidence",
    "quick_verify",
    "analyze_suspect_text",
    "format_verification_report",
]
