# CIAF Forensic Fingerprinting Integration

## Overview

CIAF v1.5.0 integrates **validated distinctive anchor analysis** as a complementary forensic layer to watermarking, providing robust verification even when visible watermarks are removed.

## Architecture: Dual-Layer Proof System

### Layer 1: Watermarking (Explicit Provenance)
**Purpose:** Proves "this text was generated, tagged, hashed, and can be verified against its evidence record."

**Components:**
- Visible watermark (footer/header/inline)
- Watermark ID + verification URL
- Exact hash matching (before/after)

**Strength:** Explicit, unambiguous proof when present  
**Weakness:** Easy to remove (text watermarks: "low" resistance)

### Layer 2: Forensic Fingerprinting (Population-Level Distinctiveness)
**Purpose:** Proves "the fingerprinting method separates human and LLM text well enough to be useful as an additional forensic signal."

**Components:**
- Distinctive anchor analysis (IDF-scored zone matching)
- Zone-based fingerprinting (beginning/middle/end)
- Population-validated thresholds

**Strength:** Survives watermark removal, validated at scale  
**Weakness:** Not standalone proof (supporting forensic signal)

---

## Validation Status

### Large-Scale Corpus Validation
- **Documents tested:** 104,724
- **Pairs audited:** 5,483,505,726 (5.48 billion)
- **Collision rate:** 1.19 × 10⁻⁸ (65 collisions)
- **Configuration:** 0.40 threshold, 2-of-3 zone matching

### Key Findings
✅ **Zero human-LLM cross-type collisions** (2.74B pairs)  
✅ **Zero cross-model LLM collisions** (1.25B pairs)  
✅ **13 LLM-LLM collisions** (all same-model: GPT-3.5, Mistral, GPT-4)  
✅ **Population-specific rates validated**

**Reference:** `validation_experiments/OPENAI/ciaf_validated_collision_test/docs/EXECUTIVE_SUMMARY.md`

---

## Evidence Record Structure

When you create a watermarked artifact with `build_text_artifact_evidence()`, the evidence record includes:

### Tier 1: Exact Integrity Layer
```python
{
  "hashes": {
    "content_hash_before_watermark": "sha256:...",
    "content_hash_after_watermark": "sha256:...",
    "canonical_receipt_hash": "sha256:..."
  }
}
```

### Tier 2: Format-Resilient Layer
```python
{
  "hashes": {
    "normalized_hash_before": "sha256:...",
    "normalized_hash_after": "sha256:..."
  }
}
```

### Tier 3: Similarity Layer
```python
{
  "fingerprints": [
    {
      "algorithm": "simhash",
      "value": "uint64",
      "role": "exact_content_before_watermark"
    }
  ]
}
```

### Tier 4: Forensic Distinctiveness Layer ⭐ NEW
```python
{
  "fingerprints": [
    {
      "algorithm": "distinctive_anchor_v1",
      "value": "sha256:fingerprint_hash",
      "role": "forensic_anchor_before_watermark",
      "confidence": 0.95
    }
  ],
  "metadata": {
    "forensic_anchor": {
      "version": "distinctive_anchor_v1",
      "zone_words": 400,
      "top_k": 10,
      "strong_threshold": 0.40,
      "zone_match_requirement": 2,
      "zone_anchors": {
        "beginning": [["anchor phrase", 12.34], ...],
        "middle": [["anchor phrase", 10.56], ...],
        "end": [["anchor phrase", 11.23], ...]
      },
      "validation": {
        "collision_rate": 1.19e-08,
        "validation_corpus_size": 104724,
        "human_llm_collisions": 0,
        "cross_model_llm_collisions": 0
      }
    }
  }
}
```

### Tier 5: Visible Provenance Layer
```python
{
  "watermark": {
    "watermark_id": "wmk-...",
    "verification_url": "https://...",
    "embed_method": "footer_append_v1",
    "removal_resistance": "low"
  }
}
```

---

## Verification Flow

### 7-Step Verification Process

When verifying suspect text with `verify_text_artifact()`, CIAF checks:

1. **Exact post-watermark hash**
   - Perfect match to distributed version
   - Confidence: 1.0

2. **Exact pre-watermark hash**
   - Watermark removed but content intact
   - Confidence: 0.95

3. **Watermark presence/intactness**
   - Detects removal or tampering
   - Sets `likely_tag_removed` flag

4. **Normalized hashes**
   - Format-resilient matching
   - Confidence: 0.90

5. **SimHash similarity**
   - Content-resilient to minor edits
   - Confidence: variable (0.0-1.0)

6. **Distinctive Anchor similarity** ⭐ NEW
   - Zone-based forensic matching
   - Confidence: 0.85 × anchor_similarity
   - Validated thresholds applied

7. **Combined confidence verdict**
   - Weighted combination of all layers
   - Final assessment with detailed notes

---

## Usage Examples

### Basic Integration (Automatic)

```python
from ciaf_watermarks import build_text_artifact_evidence, verify_text_artifact

# Create watermarked artifact (forensic fingerprinting automatic)
evidence, watermarked = build_text_artifact_evidence(
    raw_text="AI generated content...",
    prompt="Write about climate change",
    verification_base_url="https://vault.example.com",
    model_id="gpt-4",
    model_version="2026-03",
    actor_id="user:analyst"
)

# Forensic anchor fingerprint is automatically included
assert "forensic_anchor" in evidence.metadata
print(f"Fingerprint hash: {evidence.metadata['forensic_anchor']['fingerprint_hash']}")

# Later: verify suspect text
suspect_text = "..."  # Text with watermark removed
result = verify_text_artifact(suspect_text, evidence)

# Check all layers
print(f"Exact match: {result.exact_match_after_watermark}")
print(f"Watermark removed: {result.likely_tag_removed}")
print(f"Forensic confidence: {result.confidence:.1%}")

# Detailed notes include anchor analysis
for note in result.notes:
    print(note)
```

### Advanced: Direct Fingerprint Comparison

```python
from ciaf_watermarks import (
    compute_distinctive_anchor_fingerprint,
    compare_anchor_fingerprints,
    DistinctiveAnchorConfig
)

# Custom configuration (uses validated defaults if not specified)
config = DistinctiveAnchorConfig(
    zone_word_size=400,       # Validated
    top_k=10,                  # Validated
    strong_threshold=0.40,     # Validated
    zone_match_requirement=2,  # Validated (2-of-3)
)

# Generate fingerprint
fingerprint = compute_distinctive_anchor_fingerprint(text, config=config)

print(f"Fingerprint hash: {fingerprint.fingerprint_hash}")
print(f"Zones: {list(fingerprint.zone_anchors.keys())}")
print(f"Total words: {fingerprint.metadata['total_words']}")

# Compare suspect text
result = compare_anchor_fingerprints(suspect_text, fingerprint)

print(f"Overall match: {result.overall_match}")
print(f"Matched zones: {result.matched_zones}/{result.required_zones}")
print(f"Confidence: {result.confidence:.3f}")
print(f"Zone scores: {result.zone_scores}")

# Example output:
# {
#   'beginning': 0.85,  # Strong match
#   'middle': 0.42,     # Meets 0.40 threshold
#   'end': 0.38         # Below threshold
# }
# Matched zones: 2/2 → Overall match: True
```

---

## Operational Interpretation

### Scenario 1: Watermark Present and Intact
**Detection:**
- `exact_match_after_watermark: True`
- `watermark_present: True`
- `watermark_intact: True`

**Interpretation:** Authentic distributed copy  
**Confidence:** 1.0 (100%)  
**Action:** Accept without reservation

### Scenario 2: Watermark Removed
**Detection:**
- `exact_match_before_watermark: True`
- `watermark_present: False`
- `likely_tag_removed: True`
- Anchor similarity: 0.95+ (high)

**Interpretation:** Original content, watermark stripped  
**Confidence:** 0.95 (95%)  
**Action:** Flag as tampered, but content verified

### Scenario 3: Content Modified (Paraphrase)
**Detection:**
- `exact_match: False`
- `normalized_match: False`
- SimHash: 0.7-0.9 (moderate-high)
- Anchor similarity: 0.3-0.6 (variable)

**Interpretation:** Derived from original, paraphrased  
**Confidence:** 0.5-0.8 (variable)  
**Action:** Flag as suspicious derivative

### Scenario 4: Unrelated Content
**Detection:**
- `exact_match: False`
- `watermark_present: False`
- SimHash: < 0.3 (low)
- Anchor similarity: < 0.2 (low)

**Interpretation:** No relationship to evidence  
**Confidence:** 0.0 (0%)  
**Action:** Reject

---

## Validation-Based Claims

### What You Can Claim

✅ **Corpus-level performance:**
> "On a 104,724-document corpus, the distinctive anchor method achieved an observed collision rate of 1.19 × 10⁻⁸."

✅ **Zero observations:**
> "No human-LLM collisions were observed in this audit (2.74B cross-type pairs)."
> "No cross-model LLM collisions were observed in this audit (1.25B pairs)."

✅ **Validated configuration:**
> "The 0.40 threshold and 2-of-3 zone matching were validated on 104k documents."

✅ **Supporting forensic signal:**
> "Anchor similarity provides additional forensic evidence when combined with other verification layers."

### What You Cannot Claim

❌ **Universal guarantees:**
> ~~"Distinctive anchors universally distinguish human from LLM text."~~

❌ **Standalone attribution:**
> ~~"Anchor fingerprints alone prove authorship."~~

❌ **Domain-independent performance:**
> ~~"This method works equally well on all text types."~~

❌ **Adversarial robustness:**
> ~~"Anchors are robust to adversarial attacks."~~

### Honest Framing

**Use this:**
> "CIAF combines watermarking (explicit provenance) with distinctive anchor analysis (forensic fallback validated on 104k documents). When watermarks are removed, anchor similarity provides additional verification confidence based on population-tested distinctiveness thresholds (1.19 × 10⁻⁸ collision rate, zero cross-type collisions observed)."

**Not this:**
> ~~"CIAF's distinctive anchors can definitively identify AI-generated text."~~

---

## Technical Details

### Algorithm Overview

1. **Tokenization:** Text → lowercase words (2+ chars)
2. **Zone extraction:** beginning/middle/end (400 words each)
3. **Shingle generation:** 5-10 word n-grams per zone
4. **IDF scoring:** IDF × entropy × (1 - stopword_ratio)
5. **Anchor selection:** Top 10 per zone
6. **Fingerprint hash:** SHA-256 of complete fingerprint
7. **Comparison:** Jaccard similarity per zone, 2-of-3 match

### Configuration Parameters

| Parameter | Default | Range | Validated |
|-----------|---------|-------|-----------|
| `zone_word_size` | 400 | 100-1000 | ✅ 400 |
| `top_k` | 10 | 5-20 | ✅ 10 |
| `strong_threshold` | 0.40 | 0.30-0.50 | ✅ 0.40 |
| `zone_match_requirement` | 2 | 2-3 | ✅ 2 (2-of-3) |
| `min_shingle_size` | 5 | 3-7 | ✅ 5 |
| `max_shingle_size` | 10 | 8-15 | ✅ 10 |

**Validated configuration** (bold) is recommended for production use based on large-scale corpus validation.

### Performance

**Single document fingerprinting:**
- Computation: ~10-50ms (average text, 2000 words)
- Memory: ~1-5 MB (temporary, released after fingerprint)

**Verification:**
- Comparison: ~10-50ms (re-fingerprinting + Jaccard similarity)
- Memory: ~1-5 MB (temporary)

**Corpus-level audit:**
- 104,724 documents: ~1.5 hours (consumer CPU)
- 5.48B pairs: ~1.4M comparisons/sec (inverted index)

---

## Migration Guide

### Existing CIAF Users

**No breaking changes.** Forensic fingerprinting is automatically added to new evidence records.

**Existing evidence records** without forensic anchors will still verify correctly using the existing layers (exact hash, normalized hash, SimHash).

**To enable for existing records:**
1. Evidence records created before v1.5.0 won't have `forensic_anchor` metadata
2. Verification will skip anchor analysis (graceful degradation)
3. To add retrofitted fingerprints, regenerate evidence or use `compute_distinctive_anchor_fingerprint()` directly

### New Implementations

**Just use the normal workflow:**

```python
# Nothing changes in your code
evidence, watermarked = build_text_artifact_evidence(...)

# Forensic anchors are now included automatically
# Verification uses them automatically if present
result = verify_text_artifact(suspect, evidence)
```

---

## References

### Validation Reports
- **Executive Summary:** `validation_experiments/OPENAI/ciaf_validated_collision_test/docs/EXECUTIVE_SUMMARY.md`
- **Full Technical Report:** `validation_experiments/OPENAI/ciaf_validated_collision_test/docs/STRATIFIED_VALIDATION_REPORT.md`
- **Integration Guide:** `validation_experiments/OPENAI/ciaf_validated_collision_test/docs/DISTINCTIVE_ANCHOR_INTEGRATION.md`

### Code
- **Forensic Module:** `src/ciaf_watermarks/forensics/text.py`
- **Integration:** `src/ciaf_watermarks/text/core.py` (evidence building)
- **Verification:** `src/ciaf_watermarks/text/verification.py` (anchor comparison)
- **Example:** `examples/distinctive_anchor_integration.py`

### Algorithm
- **Audit Script:** `validation_experiments/OPENAI/ciaf_validated_collision_test/distinctive_anchor_audit.py`
- **Analysis:** `validation_experiments/OPENAI/ciaf_validated_collision_test/analyze_stratified_collisions.py`

---

## License and Attribution

This forensic fingerprinting method is part of CIAF (Cognitive Insight Audit Framework) and follows the same license as the main project.

**Validation performed:** April 8, 2026  
**Integration version:** CIAF v1.5.0  
**Author:** Denzil James Greenwood
