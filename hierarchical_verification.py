"""
CIAF Watermarking - Hierarchical Verification Strategy

Three-tier verification approach for optimal cost/accuracy trade-off:

Level 1 (FAST - ~1ms): Full hash matching
  - Check if exact distributed copy (content_hash_after_watermark)
  - Check if exact pre-watermark (content_hash_before_watermark)
  - Cost: Minimal, instant verification

Level 2 (MEDIUM - ~50-200ms): DNA sampling (forensic fragments)
  - Sliding window search for high-entropy text fragments
  - Spatial patch search for image regions
  - Detects: Splicing, partial use, major edits
  - Cost: Medium (fraction of KB to match against)

Level 3 (EXPENSIVE - ~500ms+): Perceptual/Similarity matching
  - SimHash for text (semantic similarity)
  - pHash for images (perceptual matching)
  - MinHash for large documents
  - Cost: High (full content analysis)

Hierarchical Logic:
  IF Level1_ExactMatch() → Return with Confidence 100%
  ELSE IF Level2_FragmentMatch() → Return with Confidence 90-99%
  ELSE IF Level3_SimilarityMatch() → Return with Confidence 70-90%
  ELSE → Not Authentic

This approach ensures:
- 95%+ of artifacts verified in <10ms (exact matches)
- Potential splicing detected quickly via fragments
- Heavy rewrites caught via similarity
- Cost scales with verification difficulty

Created: 2026-03-28
Last Modified: 2026-03-30
Author: Denzil James Greenwood
Version: 2.0.0 - Converted to Pydantic models
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field

from .models import ArtifactEvidence
from .hashing import sha256_text, normalized_text_hash, simhash_text, simhash_distance
from .fragment_verification import (
    verify_text_fragments,
    ForensicVerificationSummary,
)


class VerificationTier(str, Enum):
    """Verification tier reached."""

    TIER1_EXACT = "tier1_exact"  # Full hash match
    TIER2_FRAGMENTS = "tier2_fragments"  # DNA sampling match
    TIER3_SIMILARITY = "tier3_similarity"  # Perceptual/semantic match
    NO_MATCH = "no_match"  # No match at any tier


class VerificationStep(BaseModel):
    """Single step in hierarchical verification."""

    tier: VerificationTier = Field(..., description="Verification tier")
    step_name: str = Field(..., min_length=1, description="Step name")
    matched: bool = Field(..., description="Whether step matched")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Step confidence")
    execution_time_ms: float = Field(..., ge=0.0, description="Execution time in ms")
    details: str = Field("", description="Step details")


class HierarchicalVerificationResult(BaseModel):
    """
    Result of three-tier hierarchical verification.

    Shows which tier matched, confidence, and cost breakdown.
    """

    artifact_id: str = Field(..., min_length=1, description="Artifact identifier")
    final_tier: VerificationTier = Field(..., description="Final tier reached")
    is_authentic: bool = Field(..., description="Is artifact authentic")
    overall_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence"
    )

    # Tier execution details
    tier1_result: Optional[VerificationStep] = Field(None, description="Tier 1 result")
    tier2_result: Optional[VerificationStep] = Field(None, description="Tier 2 result")
    tier3_result: Optional[VerificationStep] = Field(None, description="Tier 3 result")

    # Cost tracking
    total_execution_time_ms: float = Field(
        0.0, ge=0.0, description="Total execution time"
    )
    tier1_cost_ms: float = Field(0.0, ge=0.0, description="Tier 1 cost")
    tier2_cost_ms: float = Field(0.0, ge=0.0, description="Tier 2 cost")
    tier3_cost_ms: float = Field(0.0, ge=0.0, description="Tier 3 cost")

    # Detailed findings
    steps: List[VerificationStep] = Field(
        default_factory=list, description="Verification steps"
    )
    tier2_fragment_results: Optional[ForensicVerificationSummary] = Field(
        None, description="Tier 2 fragment results"
    )
    tier3_similarity_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Tier 3 similarity score"
    )

    # Notes for audit trail
    notes: List[str] = Field(default_factory=list, description="Verification notes")
    evidence_record: Optional[ArtifactEvidence] = Field(
        None, description="Evidence record"
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/logging."""
        return {
            "artifact_id": self.artifact_id,
            "final_tier": self.final_tier.value,
            "is_authentic": self.is_authentic,
            "overall_confidence": self.overall_confidence,
            "total_execution_time_ms": self.total_execution_time_ms,
            "tier1_cost_ms": self.tier1_cost_ms,
            "tier2_cost_ms": self.tier2_cost_ms,
            "tier3_cost_ms": self.tier3_cost_ms,
            "steps": [
                {
                    "tier": s.tier.value,
                    "step_name": s.step_name,
                    "matched": s.matched,
                    "confidence": s.confidence,
                    "execution_time_ms": s.execution_time_ms,
                    "details": s.details,
                }
                for s in self.steps
            ],
            "notes": self.notes,
        }


# ============================================================================
# TIER 1: EXACT HASH MATCHING (FAST)
# ============================================================================


def _verify_tier1_exact_hash(
    suspect_text: str,
    evidence: ArtifactEvidence,
) -> Tuple[bool, float, str, float]:
    """
    Tier 1 Verification: Exact hash matching (fastest).

    Checks:
    1. Exact match to distributed version (with watermark)
    2. Exact match to pre-watermark version
    3. Normalized hash matching

    Cost: ~1-5 ms
    Confidence if match: 100%

    Returns:
        Tuple of (matched, confidence, details, execution_time_ms)
    """
    start_time = time.time()

    # Compute suspect hash
    suspect_hash = sha256_text(suspect_text)

    # Check 1: Exact match to distributed version (with watermark)
    if suspect_hash == evidence.hashes.content_hash_after_watermark:
        elapsed_ms = (time.time() - start_time) * 1000
        return (
            True,
            1.0,
            "Exact match to distributed watermarked version",
            elapsed_ms,
        )

    # Check 2: Exact match to pre-watermark version
    if suspect_hash == evidence.hashes.content_hash_before_watermark:
        elapsed_ms = (time.time() - start_time) * 1000
        return (
            True,
            1.0,
            "Exact match to pre-watermark version (watermark removed)",
            elapsed_ms,
        )

    # Check 3: Normalized hash matching (format-resilient)
    if evidence.hashes.normalized_hash_before:
        suspect_normalized = normalized_text_hash(suspect_text)

        if suspect_normalized == evidence.hashes.normalized_hash_before:
            elapsed_ms = (time.time() - start_time) * 1000
            return (
                True,
                0.95,
                "Normalized hash match (format variations only)",
                elapsed_ms,
            )

        if evidence.hashes.normalized_hash_after:
            if suspect_normalized == evidence.hashes.normalized_hash_after:
                elapsed_ms = (time.time() - start_time) * 1000
                return (
                    True,
                    0.95,
                    "Normalized hash match to watermarked version",
                    elapsed_ms,
                )

    elapsed_ms = (time.time() - start_time) * 1000
    return (False, 0.0, "No exact or normalized hash match", elapsed_ms)


# ============================================================================
# TIER 2: DNA FRAGMENT MATCHING (MEDIUM COST)
# ============================================================================


def _verify_tier2_fragments(
    suspect_text: str,
    evidence: ArtifactEvidence,
) -> Tuple[bool, float, str, float, Optional[ForensicVerificationSummary]]:
    """
    Tier 2 Verification: DNA fragment sampling (medium cost).

    Runs sliding window search on high-entropy fragments if available.

    Cost: ~50-200 ms (depending on document size)
    Confidence if 2+ match: 99.9%
    Confidence if 1 match: 95%

    Returns:
        Tuple of (matched, confidence, details, execution_time_ms, fragment_results)
    """
    start_time = time.time()

    # Check if forensic fragments available
    if not evidence.hashes.forensic_fragments:
        elapsed_ms = (time.time() - start_time) * 1000
        return (
            False,
            0.0,
            "No forensic fragments available",
            elapsed_ms,
            None,
        )

    # Verify text fragments if present
    if evidence.hashes.forensic_fragments.text_fragments:
        frag_result = verify_text_fragments(
            suspect_text,
            evidence.hashes.forensic_fragments.text_fragments,
        )

        elapsed_ms = (time.time() - start_time) * 1000

        # Determine confidence based on fragment matches
        if frag_result.fragments_matched >= 2:
            # 2+ fragments match: extremely high confidence
            return (
                True,
                0.999,
                f"{frag_result.fragments_matched} of {frag_result.total_fragments_checked} fragments matched",
                elapsed_ms,
                frag_result,
            )

        elif frag_result.fragments_matched == 1:
            # 1 fragment matches: good confidence
            return (
                True,
                0.95,
                f"1 of {frag_result.total_fragments_checked} fragments matched",
                elapsed_ms,
                frag_result,
            )

        else:
            # No fragments match
            return (
                False,
                0.0,
                f"0 of {frag_result.total_fragments_checked} fragments matched",
                elapsed_ms,
                frag_result,
            )

    elapsed_ms = (time.time() - start_time) * 1000
    return (False, 0.0, "Fragment matching not applicable", elapsed_ms, None)


# ============================================================================
# TIER 3: PERCEPTUAL/SIMILARITY MATCHING (EXPENSIVE)
# ============================================================================


def _verify_tier3_similarity(
    suspect_text: str,
    evidence: ArtifactEvidence,
) -> Tuple[bool, float, str, float]:
    """
    Tier 3 Verification: Perceptual/similarity matching (high cost).

    Uses SimHash to detect heavy rewrites and paraphrasing.

    Cost: ~200-500 ms (full document analysis)
    Confidence: 70-95% depending on similarity score

    Returns:
        Tuple of (matched, confidence, details, execution_time_ms)
    """
    start_time = time.time()

    if not evidence.hashes.simhash_before:
        elapsed_ms = (time.time() - start_time) * 1000
        return (False, 0.0, "No SimHash available", elapsed_ms)

    # Compute suspect SimHash
    suspect_simhash = simhash_text(suspect_text)

    # Compute distance
    distance = simhash_distance(suspect_simhash, evidence.hashes.simhash_before)

    # Interpret distance (64-bit hash)
    # Distance 0-10: Very similar (92-100%)
    # Distance 10-15: Similar (76-92%)
    # Distance 15-25: Moderately similar (50-76%)
    # Distance 25+: Likely different

    if distance <= 10:
        similarity = 1.0 - (distance / 100.0)
        confidence = 0.95
        matched = True
        details = (
            f"SimHash similarity: distance={distance}, similarity={similarity:.1%}"
        )

    elif distance <= 15:
        similarity = 1.0 - (distance / 64.0)
        confidence = 0.85
        matched = True
        details = f"SimHash similarity: distance={distance}, similarity={similarity:.1%} (edited)"

    elif distance <= 25:
        similarity = max(0.5, 1.0 - (distance / 64.0))
        confidence = 0.70
        matched = True
        details = f"SimHash similarity: distance={distance}, similarity={similarity:.1%} (heavily modified)"

    else:
        similarity = 0.4
        confidence = 0.0
        matched = False
        details = f"SimHash distance too large: {distance} (threshold: 25)"

    elapsed_ms = (time.time() - start_time) * 1000
    return (matched, confidence, details, elapsed_ms)


# ============================================================================
# HIERARCHICAL ORCHESTRATOR
# ============================================================================


def verify_text_artifact_hierarchical(
    suspect_text: str,
    evidence: ArtifactEvidence,
    force_all_tiers: bool = False,
) -> HierarchicalVerificationResult:
    """
    Verify suspect text using three-tier hierarchical strategy.

    Strategy:
    1. Try Tier 1 (exact hash) - ~1-5 ms
       If match: Return with 100% confidence (98% of cases)

    2. Try Tier 2 (DNA fragments) - ~50-200 ms
       If 2+ fragments match: Return with 99.9% confidence
       If 1 fragment matches: Return with 95% confidence

    3. Try Tier 3 (similarity) - ~200-500 ms
       If SimHash distance < 15: Return with 70-95% confidence

    4. No match at any tier: Return not authentic

    Args:
        suspect_text: Text to verify
        evidence: Stored evidence record
        force_all_tiers: For testing, run all tiers even if earlier match

    Returns:
        HierarchicalVerificationResult with cost breakdown and findings
    """
    result = HierarchicalVerificationResult(
        artifact_id=evidence.artifact_id,
        final_tier=VerificationTier.NO_MATCH,
        is_authentic=False,
        overall_confidence=0.0,
    )

    total_start = time.time()

    # ========================================================================
    # TIER 1: EXACT HASH MATCHING (FASTEST)
    # ========================================================================

    tier1_matched, tier1_conf, tier1_details, tier1_time = _verify_tier1_exact_hash(
        suspect_text, evidence
    )

    tier1_step = VerificationStep(
        tier=VerificationTier.TIER1_EXACT,
        step_name="Exact Hash Matching",
        matched=tier1_matched,
        confidence=tier1_conf,
        execution_time_ms=tier1_time,
        details=tier1_details,
    )
    result.tier1_result = tier1_step
    result.tier1_cost_ms = tier1_time
    result.steps.append(tier1_step)

    if tier1_matched and not force_all_tiers:
        result.final_tier = VerificationTier.TIER1_EXACT
        result.is_authentic = True
        result.overall_confidence = tier1_conf
        result.total_execution_time_ms = time.time() - total_start * 1000
        result.notes.append(f"✓ Tier 1 Match: {tier1_details}")
        result.notes.append(f"  Execution: {tier1_time:.2f} ms")
        return result

    # ========================================================================
    # TIER 2: DNA FRAGMENT SAMPLING (MEDIUM COST)
    # ========================================================================

    tier2_matched, tier2_conf, tier2_details, tier2_time, frag_results = (
        _verify_tier2_fragments(suspect_text, evidence)
    )

    tier2_step = VerificationStep(
        tier=VerificationTier.TIER2_FRAGMENTS,
        step_name="DNA Fragment Matching",
        matched=tier2_matched,
        confidence=tier2_conf,
        execution_time_ms=tier2_time,
        details=tier2_details,
    )
    result.tier2_result = tier2_step
    result.tier2_cost_ms = tier2_time
    result.steps.append(tier2_step)
    if frag_results:
        result.tier2_fragment_results = frag_results

    if tier2_matched and not force_all_tiers:
        result.final_tier = VerificationTier.TIER2_FRAGMENTS
        result.is_authentic = True
        result.overall_confidence = tier2_conf
        result.total_execution_time_ms = (time.time() - total_start) * 1000
        result.notes.append(f"✓ Tier 2 Match: {tier2_details}")
        result.notes.append(f"  Execution: {tier2_time:.2f} ms")
        if frag_results:
            result.notes.append(
                f"  Legal defensibility: {frag_results.legal_defensibility}"
            )
        return result

    # ========================================================================
    # TIER 3: PERCEPTUAL/SIMILARITY MATCHING (EXPENSIVE)
    # ========================================================================

    tier3_matched, tier3_conf, tier3_details, tier3_time = _verify_tier3_similarity(
        suspect_text, evidence
    )

    tier3_step = VerificationStep(
        tier=VerificationTier.TIER3_SIMILARITY,
        step_name="Perceptual/Similarity Matching",
        matched=tier3_matched,
        confidence=tier3_conf,
        execution_time_ms=tier3_time,
        details=tier3_details,
    )
    result.tier3_result = tier3_step
    result.tier3_cost_ms = tier3_time
    result.steps.append(tier3_step)

    if tier3_matched:
        result.final_tier = VerificationTier.TIER3_SIMILARITY
        result.is_authentic = True
        result.overall_confidence = tier3_conf
        result.total_execution_time_ms = (time.time() - total_start) * 1000
        result.notes.append(f"⚠ Tier 3 Match: {tier3_details}")
        result.notes.append(f"  Execution: {tier3_time:.2f} ms")
        return result

    # ========================================================================
    # NO MATCH AT ANY TIER
    # ========================================================================

    result.final_tier = VerificationTier.NO_MATCH
    result.is_authentic = False
    result.overall_confidence = 0.0
    result.total_execution_time_ms = (time.time() - total_start) * 1000

    result.notes.append("✗ No match at any verification tier")
    result.notes.append(f"  Tier 1 (Exact): {tier1_details}")
    if tier2_step.matched is not None:
        result.notes.append(f"  Tier 2 (Fragments): {tier2_details}")
    result.notes.append(f"  Tier 3 (Similarity): {tier3_details}")
    result.notes.append(f"  Total execution: {result.total_execution_time_ms:.2f} ms")

    return result


# ============================================================================
# IMAGE VERIFICATION (Placeholders - Phase 2)
# ============================================================================


def verify_image_artifact_hierarchical(
    suspect_image_bytes: bytes,
    evidence: ArtifactEvidence,
) -> HierarchicalVerificationResult:
    """
    Verify suspect image using three-tier hierarchical strategy.

    Phase 2 implementation - currently stubbed.
    """
    result = HierarchicalVerificationResult(
        artifact_id=evidence.artifact_id,
        final_tier=VerificationTier.NO_MATCH,
        is_authentic=False,
        overall_confidence=0.0,
    )
    result.notes.append(
        "Image hierarchical verification: Phase 2 - Not yet implemented"
    )
    return result


# ============================================================================
# COST ANALYSIS & REPORTING
# ============================================================================


def format_hierarchical_verification_report(
    result: HierarchicalVerificationResult,
) -> str:
    """
    Format hierarchical verification result into human-readable report.
    """
    lines = []

    lines.append("=" * 70)
    lines.append("HIERARCHICAL VERIFICATION REPORT")
    lines.append("=" * 70)

    lines.append(f"\nArtifact ID: {result.artifact_id}")
    lines.append(
        f"Result: {'✓ AUTHENTIC' if result.is_authentic else '✗ NOT AUTHENTIC'}"
    )
    lines.append(f"Overall Confidence: {result.overall_confidence:.1%}")
    lines.append(f"Final Tier: {result.final_tier.value.upper()}")

    lines.append("\n" + "-" * 70)
    lines.append("EXECUTION BREAKDOWN")
    lines.append("-" * 70)

    for step in result.steps:
        status = "✓" if step.matched else "✗"
        lines.append(f"\n{status} {step.tier.value.upper()}: {step.step_name}")
        lines.append(f"   Matched: {step.matched}")
        lines.append(f"   Confidence: {step.confidence:.1%}")
        lines.append(f"   Time: {step.execution_time_ms:.2f} ms")
        if step.details:
            lines.append(f"   Details: {step.details}")

    lines.append("\n" + "-" * 70)
    lines.append("COST ANALYSIS")
    lines.append("-" * 70)

    if result.tier1_cost_ms > 0:
        lines.append(f"Tier 1 (Exact Hash):     {result.tier1_cost_ms:.2f} ms")
    if result.tier2_cost_ms > 0:
        lines.append(f"Tier 2 (Fragments):      {result.tier2_cost_ms:.2f} ms")
    if result.tier3_cost_ms > 0:
        lines.append(f"Tier 3 (Similarity):     {result.tier3_cost_ms:.2f} ms")

    lines.append(f"Total Execution Time:    {result.total_execution_time_ms:.2f} ms")

    # Cost breakdown
    total = result.total_execution_time_ms
    if total > 0:
        if result.tier1_cost_ms > 0:
            pct1 = (result.tier1_cost_ms / total) * 100
            lines.append(f"  → Tier 1: {pct1:.1f}%")
        if result.tier2_cost_ms > 0:
            pct2 = (result.tier2_cost_ms / total) * 100
            lines.append(f"  → Tier 2: {pct2:.1f}%")
        if result.tier3_cost_ms > 0:
            pct3 = (result.tier3_cost_ms / total) * 100
            lines.append(f"  → Tier 3: {pct3:.1f}%")

    if result.tier2_fragment_results:
        lines.append("\nFragment Analysis:")
        fl = result.tier2_fragment_results
        lines.append(f"  Matched: {fl.fragments_matched}/{fl.total_fragments_checked}")
        lines.append(f"  Legal Defensibility: {fl.legal_defensibility}")

    lines.append("\n" + "-" * 70)
    lines.append("FINDINGS")
    lines.append("-" * 70)

    for note in result.notes:
        lines.append(f"{note}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)


# ============================================================================
# STATISTICS & OPTIMIZATION
# ============================================================================


class VerificationStatistics(BaseModel):
    """Track verification statistics across multiple verifications."""

    total_verifications: int = Field(0, ge=0, description="Total verifications")
    tier1_matches: int = Field(0, ge=0, description="Tier 1 exact hash matches")
    tier2_matches: int = Field(0, ge=0, description="Tier 2 fragment matches")
    tier3_matches: int = Field(0, ge=0, description="Tier 3 similarity matches")
    no_matches: int = Field(0, ge=0, description="No matches")

    total_time_ms: float = Field(0.0, ge=0.0, description="Total time")
    avg_tier1_time_ms: float = Field(0.0, ge=0.0, description="Avg tier 1 time")
    avg_tier2_time_ms: float = Field(0.0, ge=0.0, description="Avg tier 2 time")
    avg_tier3_time_ms: float = Field(0.0, ge=0.0, description="Avg tier 3 time")

    def add_result(self, result: HierarchicalVerificationResult) -> None:
        """Add a verification result to statistics."""
        self.total_verifications += 1

        if result.final_tier == VerificationTier.TIER1_EXACT:
            self.tier1_matches += 1
        elif result.final_tier == VerificationTier.TIER2_FRAGMENTS:
            self.tier2_matches += 1
        elif result.final_tier == VerificationTier.TIER3_SIMILARITY:
            self.tier3_matches += 1
        else:
            self.no_matches += 1

        self.total_time_ms += result.total_execution_time_ms

    def get_summary(self) -> str:
        """Get human-readable statistics summary."""
        lines = []
        lines.append("Verification Statistics")
        lines.append("=" * 50)
        lines.append(f"Total Verifications: {self.total_verifications}")
        lines.append(
            f"  Tier 1 (Exact): {self.tier1_matches} ({self.tier1_matches/max(1, self.total_verifications)*100:.1f}%)"
        )
        lines.append(
            f"  Tier 2 (Fragments): {self.tier2_matches} ({self.tier2_matches/max(1, self.total_verifications)*100:.1f}%)"
        )
        lines.append(
            f"  Tier 3 (Similarity): {self.tier3_matches} ({self.tier3_matches/max(1, self.total_verifications)*100:.1f}%)"
        )
        lines.append(
            f"  No Match: {self.no_matches} ({self.no_matches/max(1, self.total_verifications)*100:.1f}%)"
        )
        lines.append(
            f"Average Execution: {self.total_time_ms/max(1, self.total_verifications):.2f} ms"
        )
        return "\n".join(lines)
