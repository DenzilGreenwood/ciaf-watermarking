"""
CIAF Watermarking - Forensic Analysis Module

Forensic fingerprinting methods for artifact verification beyond visible watermarking.

Provides:
- Distinctive anchor analysis for text (validated at 1.19 × 10⁻⁸ collision rate)
- Zone-based fingerprinting with IDF scoring
- Population-tested discrimination thresholds

Created: 2026-04-09
Author: Denzil James Greenwood
Version: 1.5.0
"""

from .text import (
    compute_distinctive_anchor_fingerprint,
    compare_anchor_fingerprints,
    DistinctiveAnchorConfig,
    DistinctiveAnchorFingerprint,
    AnchorSimilarityResult,
)

__all__ = [
    "compute_distinctive_anchor_fingerprint",
    "compare_anchor_fingerprints",
    "DistinctiveAnchorConfig",
    "DistinctiveAnchorFingerprint",
    "AnchorSimilarityResult",
]
