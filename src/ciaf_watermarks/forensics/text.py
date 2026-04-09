"""
CIAF Forensics - Text Distinctive Anchor Analysis

IDF-scored zone-based fingerprinting for text artifacts.

Validation Status:
- Corpus: 104,724 documents (news, essays, 63 LLM models)
- Collision rate: 1.19 × 10⁻⁸ (65 collisions in 5.48B pairs)
- Human-LLM collisions: 0 observed (2.74B cross-type pairs)
- Cross-model LLM collisions: 0 observed (1.25B pairs)
- Configuration: 0.40 threshold, 2-of-3 zone matching

Reference: validation_experiments/OPENAI/ciaf_validated_collision_test/docs/EXECUTIVE_SUMMARY.md

Created: 2026-04-09
Author: Denzil James Greenwood
Version: 1.5.0
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Tuple, Any
import re
import math
import hashlib
import json

# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class DistinctiveAnchorConfig:
    """
    Configuration for distinctive anchor fingerprinting.

    These parameters are validated on 104k document corpus:
    - Overall collision rate: 1.19 × 10⁻⁸
    - Zero human-LLM collisions observed
    - Zero cross-model LLM collisions observed
    """

    zone_word_size: int = 400
    """Word count per zone (beginning/middle/end)"""

    top_k: int = 10
    """Top distinctive anchors per zone"""

    strong_threshold: float = 0.40
    """Jaccard similarity threshold (validated: 0.40)"""

    zone_match_requirement: int = 2
    """Required matching zones (2-of-3 or 3-of-3)"""

    min_shingle_size: int = 5
    """Minimum shingle size (words)"""

    max_shingle_size: int = 10
    """Maximum shingle size (words)"""

    stopwords: Optional[Set[str]] = None
    """Optional stopwords set (default: common English stopwords)"""

    def __post_init__(self):
        """Initialize default stopwords if not provided."""
        if self.stopwords is None:
            self.stopwords = {
                "the",
                "be",
                "to",
                "of",
                "and",
                "a",
                "in",
                "that",
                "have",
                "i",
                "it",
                "for",
                "not",
                "on",
                "with",
                "he",
                "as",
                "you",
                "do",
                "at",
                "this",
                "but",
                "his",
                "by",
                "from",
                "they",
                "we",
                "say",
                "her",
                "she",
                "or",
                "an",
                "will",
                "my",
                "one",
                "all",
                "would",
                "there",
                "their",
                "what",
                "so",
                "up",
                "out",
                "if",
                "about",
                "who",
                "get",
                "which",
                "go",
                "me",
                "when",
                "make",
                "can",
                "like",
                "time",
                "no",
                "just",
                "him",
                "know",
                "take",
                "people",
                "into",
                "year",
                "your",
                "good",
                "some",
                "could",
                "them",
                "see",
                "other",
                "than",
                "then",
                "now",
                "look",
                "only",
                "come",
                "its",
                "over",
                "think",
                "also",
                "back",
                "after",
                "use",
                "two",
                "how",
                "our",
                "work",
                "first",
                "well",
                "way",
                "even",
                "new",
                "want",
                "because",
                "any",
                "these",
                "give",
                "day",
                "most",
                "us",
                "is",
                "was",
                "are",
                "been",
                "has",
                "had",
                "were",
                "said",
                "did",
                "having",
            }


@dataclass
class DistinctiveAnchorFingerprint:
    """
    Distinctive anchor fingerprint for a text artifact.

    Contains zone-based anchors and their scores for forensic verification.
    """

    config: DistinctiveAnchorConfig
    """Configuration used to generate this fingerprint"""

    zone_anchors: Dict[str, List[Tuple[str, float]]]
    """Anchors per zone: {zone_name: [(anchor_text, idf_score), ...]}"""

    fingerprint_hash: str
    """SHA-256 hash of the complete fingerprint"""

    metadata: Dict[str, Any] = None
    """Optional metadata (word count, zones analyzed, etc.)"""

    def to_dict(self) -> Dict:
        """Serialize to dictionary for storage."""
        return {
            "config": {
                "zone_word_size": self.config.zone_word_size,
                "top_k": self.config.top_k,
                "strong_threshold": self.config.strong_threshold,
                "zone_match_requirement": self.config.zone_match_requirement,
            },
            "zone_anchors": {
                zone: [(anchor, score) for anchor, score in anchors]
                for zone, anchors in self.zone_anchors.items()
            },
            "fingerprint_hash": self.fingerprint_hash,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DistinctiveAnchorFingerprint":
        """Deserialize from dictionary."""
        config = DistinctiveAnchorConfig(**data["config"])
        zone_anchors = {
            zone: [(anchor, score) for anchor, score in anchors]
            for zone, anchors in data["zone_anchors"].items()
        }
        return cls(
            config=config,
            zone_anchors=zone_anchors,
            fingerprint_hash=data["fingerprint_hash"],
            metadata=data.get("metadata"),
        )


@dataclass
class AnchorSimilarityResult:
    """
    Result of comparing two distinctive anchor fingerprints.
    """

    overall_match: bool
    """True if fingerprints match according to zone requirements"""

    zone_scores: Dict[str, float]
    """Jaccard similarity per zone"""

    matched_zones: int
    """Number of zones that met the threshold"""

    required_zones: int
    """Required zones for a match"""

    match_score: float
    """Aggregate similarity score (0.0-1.0) - mean of zone scores, NOT a calibrated confidence"""

    details: Dict[str, Any]
    """Additional details (matched anchors, etc.)"""


# ============================================================================
# TEXT TOKENIZATION
# ============================================================================


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into words.

    Args:
        text: Input text

    Returns:
        List of lowercase words
    """
    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    # Split and lowercase
    words = text.lower().split()

    return [w for w in words if len(w) > 1]  # Filter single-char words


def extract_zones(words: List[str], zone_word_size: int) -> Dict[str, List[str]]:
    """
    Extract beginning/middle/end zones from word list.

    Args:
        words: List of words
        zone_word_size: Words per zone

    Returns:
        Dictionary mapping zone names to word lists
    """
    total_words = len(words)

    if total_words < zone_word_size:
        # Document too short, use entire text as all zones
        return {
            "beginning": words,
            "middle": words,
            "end": words,
        }

    # Beginning: first zone_word_size words
    beginning = words[:zone_word_size]

    # End: last zone_word_size words
    end = words[-zone_word_size:]

    # Middle: center zone_word_size words
    mid_start = (total_words - zone_word_size) // 2
    middle = words[mid_start : mid_start + zone_word_size]

    return {
        "beginning": beginning,
        "middle": middle,
        "end": end,
    }


# ============================================================================
# SHINGLE GENERATION
# ============================================================================


def generate_shingles(
    words: List[str],
    min_size: int = 5,
    max_size: int = 10,
) -> Set[str]:
    """
    Generate all shingles (n-grams) of varying lengths.

    Args:
        words: List of words
        min_size: Minimum shingle size
        max_size: Maximum shingle size

    Returns:
        Set of shingle strings
    """
    shingles = set()

    for size in range(min_size, max_size + 1):
        for i in range(len(words) - size + 1):
            shingle = " ".join(words[i : i + size])
            shingles.add(shingle)

    return shingles


# ============================================================================
# IDF SCORING
# ============================================================================


def compute_idf_scores(
    zone_shingles: Dict[str, Set[str]],
    document_frequency: Optional[Dict[str, int]] = None,
    total_documents: int = 1,
) -> Dict[str, Dict[str, float]]:
    """
    Compute IDF scores for shingles in each zone.

    For single-document fingerprinting, we use entropy as a proxy for IDF.
    For corpus-based analysis (if document_frequency provided), use true IDF.

    Args:
        zone_shingles: Shingles per zone
        document_frequency: Optional pre-computed DF from corpus
        total_documents: Total documents in corpus (if using DF)

    Returns:
        IDF scores per zone: {zone: {shingle: idf_score}}
    """
    idf_scores = {}

    for zone, shingles in zone_shingles.items():
        zone_scores = {}

        for shingle in shingles:
            if document_frequency and shingle in document_frequency:
                # True IDF from corpus
                df = document_frequency[shingle]
                idf = math.log((total_documents + 1) / (df + 1))
            else:
                # Entropy-based proxy (for single document)
                idf = compute_shingle_entropy(shingle)

            zone_scores[shingle] = idf

        idf_scores[zone] = zone_scores

    return idf_scores


def compute_shingle_entropy(shingle: str) -> float:
    """
    Compute entropy score for a shingle (proxy for IDF when no corpus).

    Args:
        shingle: Shingle text

    Returns:
        Entropy score (higher = more distinctive)
    """
    # Character frequency
    freq = {}
    for char in shingle:
        freq[char] = freq.get(char, 0) + 1

    # Shannon entropy
    entropy = 0.0
    total = len(shingle)

    for count in freq.values():
        p = count / total
        entropy -= p * math.log2(p) if p > 0 else 0

    return entropy


# ============================================================================
# STOPWORD FILTERING
# ============================================================================


def compute_stopword_ratio(shingle: str, stopwords: Set[str]) -> float:
    """
    Compute ratio of stopwords in shingle.

    Args:
        shingle: Shingle text
        stopwords: Set of stopword strings

    Returns:
        Ratio of stopwords (0.0-1.0)
    """
    words = shingle.split()
    if not words:
        return 1.0  # Penalize empty shingles

    stopword_count = sum(1 for w in words if w in stopwords)
    return stopword_count / len(words)


# ============================================================================
# DISTINCTIVE ANCHOR SELECTION
# ============================================================================


def select_distinctive_anchors(
    zone_shingles: Dict[str, Set[str]],
    config: DistinctiveAnchorConfig,
    document_frequency: Optional[Dict[str, int]] = None,
    total_documents: int = 1,
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Select top-k distinctive anchors per zone using IDF scoring.

    Scoring formula: IDF × entropy × (1 - stopword_ratio)

    Args:
        zone_shingles: Shingles per zone
        config: Distinctive anchor configuration
        document_frequency: Optional corpus DF
        total_documents: Total documents in corpus

    Returns:
        Top-k anchors per zone: {zone: [(anchor, score), ...]}
    """
    # Compute IDF scores
    idf_scores = compute_idf_scores(zone_shingles, document_frequency, total_documents)

    zone_anchors = {}

    for zone, shingles in zone_shingles.items():
        scored_anchors = []

        for shingle in shingles:
            idf = idf_scores[zone].get(shingle, 0.0)
            entropy = compute_shingle_entropy(shingle)
            stopword_ratio = compute_stopword_ratio(shingle, config.stopwords)

            # Combined score: IDF × entropy × (1 - stopword_ratio)
            score = idf * entropy * (1.0 - stopword_ratio)

            scored_anchors.append((shingle, score))

        # Sort by score and take top-k
        scored_anchors.sort(key=lambda x: x[1], reverse=True)
        top_anchors = scored_anchors[: config.top_k]

        zone_anchors[zone] = top_anchors

    return zone_anchors


# ============================================================================
# FINGERPRINT GENERATION
# ============================================================================


def compute_distinctive_anchor_fingerprint(
    text: str,
    config: Optional[DistinctiveAnchorConfig] = None,
    document_frequency: Optional[Dict[str, int]] = None,
    total_documents: int = 1,
) -> DistinctiveAnchorFingerprint:
    """
    Compute distinctive anchor fingerprint for text.

    This is the main entry point for generating forensic fingerprints.
    Uses validated parameters: 0.40 threshold, 2-of-3 zone matching.

    Args:
        text: Input text to fingerprint
        config: Optional configuration (uses validated defaults if None)
        document_frequency: Optional corpus DF for IDF calculation
        total_documents: Total documents in corpus (if using DF)

    Returns:
        DistinctiveAnchorFingerprint object

    Example:
        >>> fingerprint = compute_distinctive_anchor_fingerprint(text)
        >>> print(f"Zones: {list(fingerprint.zone_anchors.keys())}")
        >>> print(f"Hash: {fingerprint.fingerprint_hash[:16]}...")
    """
    if config is None:
        config = DistinctiveAnchorConfig()  # Use validated defaults

    # Tokenize
    words = tokenize_text(text)

    # Detect short documents (zones would be identical)
    is_short_document = len(words) < config.zone_word_size

    # Extract zones
    zones = extract_zones(words, config.zone_word_size)

    # Generate shingles per zone
    zone_shingles = {
        zone: generate_shingles(zone_words, config.min_shingle_size, config.max_shingle_size)
        for zone, zone_words in zones.items()
    }

    # Select distinctive anchors
    zone_anchors = select_distinctive_anchors(
        zone_shingles, config, document_frequency, total_documents
    )

    # Compute fingerprint hash
    fingerprint_data = json.dumps(zone_anchors, sort_keys=True)
    fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()

    # Metadata
    metadata = {
        "total_words": len(words),
        "zones_analyzed": list(zone_anchors.keys()),
        "anchors_per_zone": {zone: len(anchors) for zone, anchors in zone_anchors.items()},
        "short_document": is_short_document,
    }

    # Short-document handling: operational adjustment, not part of validated study
    # For short documents, effectively require only 1 zone match (all zones identical)
    # This is a policy decision to avoid false precision when zones are duplicate
    if is_short_document:
        metadata["effective_zone_requirement"] = 1
        metadata["note"] = (
            "Document shorter than zone size; all zones identical (policy adjustment)"
        )

    return DistinctiveAnchorFingerprint(
        config=config,
        zone_anchors=zone_anchors,
        fingerprint_hash=fingerprint_hash,
        metadata=metadata,
    )


# ============================================================================
# FINGERPRINT COMPARISON
# ============================================================================


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Compute Jaccard similarity between two sets.

    Args:
        set1: First set
        set2: Second set

    Returns:
        Jaccard similarity (0.0-1.0)
    """
    if not set1 and not set2:
        return 1.0  # Both empty = identical

    if not set1 or not set2:
        return 0.0  # One empty = no similarity

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def compare_anchor_fingerprints(
    suspect_text: str,
    evidence_fingerprint: DistinctiveAnchorFingerprint,
    document_frequency: Optional[Dict[str, int]] = None,
    total_documents: int = 1,
) -> AnchorSimilarityResult:
    """
    Compare suspect text against stored distinctive anchor fingerprint.

    Uses validated thresholds from 104k document corpus validation:
    - Similarity threshold: 0.40 (Jaccard)
    - Zone requirement: 2-of-3 zones must match

    Args:
        suspect_text: Text to verify
        evidence_fingerprint: Stored fingerprint from evidence
        document_frequency: Optional corpus DF
        total_documents: Total documents in corpus

    Returns:
        AnchorSimilarityResult with match status and aggregate match_score

    Example:
        >>> result = compare_anchor_fingerprints(suspect, evidence_fp)
        >>> if result.overall_match:
        ...     print(f"Match! Score: {result.match_score:.2%}")
        >>> print(f"Zones matched: {result.matched_zones}/{result.required_zones}")
    """
    # Generate fingerprint for suspect text using same config
    suspect_fp = compute_distinctive_anchor_fingerprint(
        suspect_text,
        config=evidence_fingerprint.config,
        document_frequency=document_frequency,
        total_documents=total_documents,
    )

    config = evidence_fingerprint.config
    zone_scores = {}
    matched_zones = 0
    matched_anchors_details = {}

    # Compare each zone
    for zone in ["beginning", "middle", "end"]:
        evidence_anchors = set(
            anchor for anchor, _ in evidence_fingerprint.zone_anchors.get(zone, [])
        )
        suspect_anchors = set(anchor for anchor, _ in suspect_fp.zone_anchors.get(zone, []))

        # Jaccard similarity
        similarity = jaccard_similarity(evidence_anchors, suspect_anchors)
        zone_scores[zone] = similarity

        # Check if zone meets threshold
        if similarity >= config.strong_threshold:
            matched_zones += 1

        # Track matched anchors
        matched = evidence_anchors & suspect_anchors
        matched_anchors_details[zone] = {
            "similarity": similarity,
            "matched_count": len(matched),
            "matched_anchors": list(matched)[:5],  # Top 5 for brevity
        }

    # Overall match: Does it meet zone requirement?
    # Short-document adjustment: operational policy, not part of validated study
    # If evidence document was short (all zones identical), use adjusted requirement
    effective_requirement = config.zone_match_requirement
    if evidence_fingerprint.metadata and evidence_fingerprint.metadata.get("short_document"):
        effective_requirement = evidence_fingerprint.metadata.get("effective_zone_requirement", 1)

    overall_match = matched_zones >= effective_requirement

    # Match score: Average of zone scores (simple aggregate, not calibrated confidence)
    if matched_zones > 0:
        match_score = sum(zone_scores.values()) / len(zone_scores)
    else:
        match_score = 0.0

    return AnchorSimilarityResult(
        overall_match=overall_match,
        zone_scores=zone_scores,
        matched_zones=matched_zones,
        required_zones=effective_requirement,
        match_score=match_score,
        details={
            "matched_anchors": matched_anchors_details,
            "suspect_fingerprint_hash": suspect_fp.fingerprint_hash,
            "evidence_fingerprint_hash": evidence_fingerprint.fingerprint_hash,
            "short_document_adjustment": evidence_fingerprint.metadata.get("short_document", False),
        },
    )


# ============================================================================
# VALIDATION METADATA
# ============================================================================


VALIDATION_METADATA = {
    "version": "distinctive_anchor_v1",
    "validation_date": "2026-04-08",
    "validation_corpus_size": 104724,
    "total_pairs_audited": 5483505726,
    "collision_rate": 1.19e-08,
    "human_llm_collisions": 0,
    "cross_model_llm_collisions": 0,
    "validated_configuration": {
        "zone_word_size": 400,
        "top_k": 10,
        "strong_threshold": 0.40,
        "zone_match_requirement": 2,
    },
    "reference": "validation_experiments/OPENAI/ciaf_validated_collision_test/docs/EXECUTIVE_SUMMARY.md",
}
