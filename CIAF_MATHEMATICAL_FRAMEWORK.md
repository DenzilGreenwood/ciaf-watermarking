# CIAF Watermarking Evidence : Formalization and Validation Framework

**Mathematical Model, Threat Analysis, and Calibration Plan v1.0**

---

**Authors:** Denzil James Greenwood  
**Organization:** CognitiveInsight.ai  
**Date:** April 7, 2026  
**License:** Business Source License 1.1 (BUSL-1.1)  
**Repository:** https://github.com/DenzilGreenwood/ciaf-watermarking  

---

## Abstract

This document provides the **formalization and validation framework** for the Cognitive Insight Audit Framework (CIAF Watermarking Evidence). It is not a completed mathematical proof—it is a **validation plan** that separates **cryptographic guarantees** (provable security under standard assumptions) from **statistical evidence** (requiring empirical calibration) and **policy-adjusted scores** (deployment-specific thresholds).

**Critical Interpretation Statement:**

> **CIAF Watermarking Evidence outputs should be interpreted as a combination of:**
> 1. **Cryptographic verdicts** (Tier 1: exact hash matching with 2^-256 collision probability)
> 2. **Empirically calibrated statistical evidence** (Tier 2/3: fragment and perceptual matching requiring corpus validation)
> 3. **Deployment-specific policy thresholds** (operational scores adjusted for risk tolerance)
> 
> **These are not a single uniform notion of proof.** Final confidence scores blend Bayesian-like statistical estimates with policy adjustments for watermark removal penalties, format tolerance, and operational risk management.

The goal is to:
1. Formalize what can be **cryptographically proven** (SHA-256 collision resistance)
2. Define what must be **empirically measured** (false positive/negative rates on real corpora)
3. Specify **validation experiments** required before claiming specific confidence levels
4. Separate **target values** (engineering goals) from **validated results** (post-experiment)

This is a **validation scaffold**, not a completed proof. Numbers marked as **[TARGET]** are hypotheses requiring experimental confirmation. Numbers marked as **[VALIDATED]** have supporting empirical evidence.

---

## Table of Contents

1. [Mathematical Foundations](#1-mathematical-foundations)
2. [Three-Layer Architecture](#2-three-layer-architecture)
3. [Cryptographic Layer: Provable Security](#3-cryptographic-layer-provable-security)
4. [Statistical Layer: Artifact-Specific Models](#4-statistical-layer-artifact-specific-models)
5. [Confidence Model: Bayesian Formalization](#5-confidence-model-bayesian-formalization)
6. [Decision Layer: Operational Thresholds](#6-decision-layer-operational-thresholds)
7. [False Positive/Negative Rate Analysis](#7-false-positivenegative-rate-analysis)
8. [Validation Experiments](#8-validation-experiments)
9. [Attack Resistance Analysis](#9-attack-resistance-analysis)
10. [Calibration Procedure](#10-calibration-procedure)
11. [Appendix: Implementation Notes](#11-appendix-implementation-notes)

---

**Documentation Conventions:**

Throughout this document, numeric values and claims are marked with validation status indicators:

- **[VALIDATED]** - Supported by published research or 40+ years of cryptanalysis (e.g., SHA-256 collision resistance)
- **[TARGET]** - Engineering target requiring experimental confirmation (e.g., fragment FPR < 10^-12)
- **[ILLUSTRATIVE]** - Example value for illustration purposes, not a formal claim (e.g., edit tolerance thresholds)

**Default assumption:** Any unmarked threshold is a **target value** pending empirical validation (Section 8).

---

## 1. Mathematical Foundations

### 1.1 Information Theory Preliminaries

**Shannon Entropy** of a discrete random variable X:

```
H(X) = -Σ P(x) log₂ P(x)
```

For text fragments, we compute **per-character entropy**:

```
H(s) = -Σ (count(c)/n) log₂(count(c)/n)
     where c ∈ alphabet, n = |s|
```

**Entropy Threshold Justification:**

Current implementation uses `H(s) ≥ 0.4 * log₂(|alphabet|)` as a fragment selection criterion. This ensures fragments contain information density above baseline randomness.

**Formal Requirement:** A fragment with entropy H(s) < 0.4 * H_max is considered **low-entropy** and rejected. This threshold must be validated empirically (Section 8).

---

### 1.2 Three-Output Model: Notation and Definitions

**CIAF Watermarking Evidence produces three conceptually distinct outputs, not a single "confidence" score:**

#### **Output 1: Cryptographic Verdict**

```
V_crypto ∈ {EXACT_MATCH, WATERMARK_REMOVED, NORMALIZED_MATCH, NO_MATCH}
```

- **Type:** Deterministic cryptographic verification
- **Security:** Provable under SHA-256 collision resistance (P(false match) ≤ 2^-256)
- **No calibration required:** Rests on standard cryptographic assumptions

#### **Output 2: Statistical Evidence (Likelihood Ratio)**

```
LR_stat = P(observations | authentic) / P(observations | not authentic)
```

- **Type:** Bayesian likelihood ratio from forensic matching (fragments, perceptual hashing)
- **Security:** [TARGET - requires corpus validation]
- **Calibration required:** Must be measured on representative datasets (Section 8)
- **Interpretation:** LR > 1000 = strong evidence, LR > 10^6 = very strong evidence

#### **Output 3: Policy-Adjusted Operational Score**

```
S_operational ∈ [0, 1]
```

- **Type:** Deployment-specific score blending verdicts, statistical evidence, and policy adjustments
- **Security:** Business logic, not probability theory
- **Calibration required:** Set thresholds based on risk tolerance (legal vs. spam detection)
- **Interpretation:** Operational decision threshold (e.g., S ≥ 0.85 = accept)

---

### 1.3 Probability Theory for Statistical Evidence

**For Layer 2 (Statistical Evidence) Only:**

The statistical layer computes a **posterior probability** that suspect content S originated from claimed source evidence E:

```
P(authentic | observations) = P(O | A) * P(A) / P(O)
```

This applies **only to Tier 2/3 fragment and perceptual matching**, not to:
- Tier 1 cryptographic verdicts (deterministic, not probabilistic)
- Policy-adjusted operational scores (business rules, not probabilities)

Where:
- **P(A)** = prior probability of authenticity (context-dependent: 0.10 for flagged content, 0.80 for authenticated submissions)
- **P(O | A)** = likelihood of observations given authenticity [TARGET - requires measurement]
- **P(O)** = marginal probability of observations (normalization constant)

**Current Issue:** CIAF Watermarking Evidence currently reports single "confidence" scores (0.95, 0.90) that conflate all three output types. Section 5 separates these properly.

---

### 1.4 Hash Function Security Assumptions

**Collision Resistance:**

A cryptographic hash function H is (t, ε)-collision-resistant if no adversary running in time t can find x ≠ y such that H(x) = H(y) with probability > ε.

**SHA-256 Security Level:**

```
Collision resistance:   2^128 operations (birthday bound)
Pre-image resistance:   2^256 operations
Second pre-image:       2^256 operations
```

**Formal Claim:** Tier 1 exact hash matching achieves P(false match) ≤ 2^(-256) under the SHA-256 collision resistance assumption.

**Critical Distinction:** This applies to **exact hash matching** (Tier 1) only. Tier 2 (fragment matching) is **statistical** and Tier 3 (perceptual hashing) is **policy adjusted threshisholds**, not cryptographic.

---

## 2. Three-Layer Architecture

The CIAF Watermarking Evidence verification system operates in three conceptually distinct layers that produce **different types of outputs**:

### Layer 1: Cryptographic Verdict (Tier 1)

**Security Model:** Provable under standard cryptographic assumptions (SHA-256 collision resistance).

**Output Type:** **Cryptographic verdict** (provable security)

**Guarantees:**
- If `SHA256(suspect) == SHA256(original)`, then `suspect == original` with P(collision) ≤ 2^(-256).
- This is a **cryptographic guarantee**, not a statistical estimate.
- **No empirical calibration required** (rests on 40+ years of SHA-256 cryptanalysis).

**Score:** verdict = {EXACT_MATCH, NO_MATCH}

---

### Layer 2: Statistical Evidence (Tier 2)

**Security Model:** Empirically calibrated probabilities based on corpus analysis.

**Output Type:** **Statistical match estimate** (requires experimental validation)

**Guarantees [ALL TARGETS UNTIL VALIDATED]:**
- False positive rate: FPR = P(match | not authentic) — **must be measured on real corpora**
- False negative rate: FNR = P(no match | authentic) — **depends on edit types and corpus**
- Target values provided; **validation experiments required** (Section 8)

**Score:** statistical_confidence ∈ [0, 1], representing likelihood ratio

**Critical Limitation:** These are **not cryptographic proofs**. They are forensic evidence quality estimates that depend on:
- Corpus structure (boilerplate text reduces fragment uniqueness)
- Edit patterns (synonym replacement vs. deletion)
- Adversarial manipulation (targeted attacks can evade detection)

---

### Layer 3: Policy-Adjusted Operational Score

**Security Model:** Business logic and risk management.

**Output Type:** **Policy-adjusted score** (deployment-specific thresholds)

**Mapping statistical evidence to operational decisions:**

| Confidence Range | Decision | Policy |
|------------------|----------|--------|
| c = 1.0 | Exact authentic copy | Cryptographic certainty |
| 0.95 ≤ c < 1.0 | Watermark removed | Alert + high confidence |
| 0.85 ≤ c < 0.95 | Partial match | Forensic analysis required |
| 0.70 ≤ c < 0.85 | Likely derivative | Low confidence |
| 0.50 ≤ c < 0.70 | Insufficient evidence | Cannot determine |
| c < 0.50 | Not authentic | Reject claim |

**Key Point:** These thresholds are **policy decisions** based on risk tolerance, not mathematical facts. Section 6 formalizes this.

---

## 3. Cryptographic Layer: Provable Security

### 3.1 Tier 1: Exact Hash Matching

**Algorithm:**

```
Verify_Tier1(suspect, evidence):
    h_suspect = SHA256(suspect)
    if h_suspect == evidence.hash_after_watermark:
        return (authenticated=True, confidence=1.0)
    else if h_suspect == evidence.hash_before_watermark:
        return (authenticated=True, confidence=0.95, alert="watermark_removed")
    else:
        return (authenticated=False, confidence=0.0)
```

**Security Theorem:**

**Theorem 3.1 (Exact Match Security):**  
If SHA-256 is (2^128, 2^(-128))-collision-resistant, then Tier 1 verification achieves:

```
P(false positive) ≤ 2^(-128)  (adversary claims match without possession)
P(false negative) = 0          (genuine copy always matches)
```

**Proof Sketch:**  
A false positive requires finding distinct content S' such that SHA256(S') matches evidence hash. This violates collision resistance with probability > 2^(-128), contradicting the assumption.

**Output Separation:**

```
# Layer 1: Cryptographic verdict
verdict = EXACT_MATCH  (cryptographically certain)

# Layer 3: Policy-adjusted operational score
operational_score = 0.95  (policy penalty for watermark removal)
```

**Critical Distinction:** The 0.95 score for removed watermarks is **not a Bayesian posterior**. It is a **policy-adjusted score** that:
1. Confirms authenticity cryptographically (verdict = EXACT_MATCH, P(authentic) ≈ 1.0)
2. Applies a **0.05 penalty** for deliberate watermark removal (policy decision)
3. Signals "authentic but tampered" for downstream systems

**This is a business rule, not a probability.** Systems should output both:
- `cryptographic_verdict: EXACT_MATCH`
- `operational_score: 0.95`
- `alert: WATERMARK_REMOVED`

---

### 3.2 Normalized Hash Matching

**Algorithm:**

```
normalize(text):
    return lowercase(strip_whitespace(strip_punctuation(text)))

h_normalized = SHA256(normalize(suspect))
```

**Security Downgrade:**

Normalization reduces entropy and **weakens cryptographic guarantees**. A normalized hash match provides:

```
P(collision) ≤ 2^(-256) * (1/compression_factor)
```

Where compression_factor = (original_entropy / normalized_entropy).

**Example:**  
Text with 50% whitespace: compression ≈ 2x, collision risk ≈ 2 * 2^(-256) ≈ 2^(-255).

**Confidence Policy:**

```
c_normalized = 0.90  (format-tolerant match, slightly lower confidence)
```

This is still cryptographic-level security but acknowledges potential collision risk from normalization.

---

### 3.3 Signature Envelope Security

**RSA Signature Verification:**

```
Verify_Signature(evidence, signature, public_key):
    message = canonical_json(evidence)
    return RSA_Verify(public_key, message, signature)
```

**Security Theorem:**

**Theorem 3.2 (Non-Repudiation):**  
If RSA-2048 is (2^112, 2^(-112))-secure, then a valid signature provides non-repudiation:

```
P(forge signature) ≤ 2^(-112)
```

**Operational Meaning:**  
A signed evidence record cannot be forged or repudiated by the signer, making it suitable for legal proceedings.

---

## 4. Statistical Layer: Artifact-Specific Models

This section formalizes the **statistical guarantees** for Tier 2 (fragment matching) and Tier 3 (perceptual matching) **per artifact type**.

---

### 4.1 Text: Fragment Collision Analysis

#### 4.1.1 Fragment Selection Strategy

**Current Implementation:**

```
1. Extract N_candidates candidate fragments (beginning/middle/end)
2. Compute H(fragment) for each
3. Select N_fragments = 3 fragments with highest entropy
4. Store SHA256(fragment) for each
```

**Parameters:**
- Fragment length: L = 200 bytes
- Number of fragments: N = 3
- Entropy threshold: H_min = 0.4 * log₂(95) ≈ 2.6 bits/char

#### 4.1.2 Collision Probability Model

**Question:** What is the probability that a random document contains a fragment matching one of the stored fragments?

**Model:**

Let:
- D = document corpus (e.g., 10 billion English documents)
- L = fragment length (200 bytes)
- A = alphabet size (95 ASCII printable characters)
- H_avg = average entropy per character (≈ 4.5 bits for English)

**Random Collision Probability:**

For a single fragment:

```
P(collision | random) ≈ 1 / (A^L) = 1 / (95^200) ≈ 2^(-1320)
```

This is astronomically small. **Conclusion:** Random collisions are cryptographically infeasible.

**Structured Collision Probability:**

For English text with entropy H = 4.5 bits/char:

```
P(collision | English) ≈ 1 / 2^(H*L) = 1 / 2^(4.5*200) = 1 / 2^900 ≈ 10^(-270)
```

Still infeasible. **But this assumes uniform distribution**.

**Realistic Threat: Boilerplate Text**

Common phrases like "Introduction", "In conclusion", "Thank you for" have **low entropy** and appear across many documents.

**Defense:** Entropy threshold H_min = 0.4 * log₂(95) ≈ 2.6 ensures high-entropy fragments.

**Validation Required (Section 8):**

Measure false positive rate empirically:
1. Generate 1 million random document pairs
2. Compute fragment matches
3. Measure FPR = P(≥2 fragments match | different sources)

**Expected Result:** FPR < 10^(-12) for properly selected high-entropy fragments.

#### 4.1.3 Multi-Fragment Matching Rule

**Current Rule:** Match if ≥2 of 3 fragments match.

**Collision Probability for 2-of-3 Match:**

```
P(≥2 match | random) = Σ(k=2 to 3) C(3,k) * p^k * (1-p)^(3-k)

Where p = P(single fragment match) ≈ 2^(-900)
```

**Result:**

```
P(≥2 match | random) ≈ 3 * p² ≈ 3 * 2^(-1800) ≈ 10^(-540)
```

**Target Claim [UNVALIDATED]:**

**Claim 4.1 (Fragment Match Security - Target):**  
The 2-of-3 fragment matching rule **targets**:

```
P(false positive) < 10^(-12)  [TARGET - requires validation]
```

**Status:** This is an **engineering target** based on theoretical entropy calculations. The **actual FPR depends on**:
1. **Corpus structure:** Wikipedia vs. legal contracts vs. social media
2. **Boilerplate content:** Templates, repeated phrases, standard intros
3. **Entropy threshold effectiveness:** H_min = 2.6 may be too low for some domains
4. **Fragment placement:** Beginning/middle/end may align with template boundaries

**Validation Required (Section 8):**  
Measure actual FPR on representative corpora. **If FPR > 10^(-9), increase entropy threshold or fragment count.**

**Realistic Expectation:** FPR between 10^(-12) and 10^(-9) after proper calibration.

#### 4.1.4 Edit Tolerance Analysis

**Question:** How many edits can text sustain before losing fragment matches?

**Model:**

Let:
- e = edit distance (Levenshtein distance)
- L = fragment length (200 bytes)
- τ = tolerance threshold (e.g., 10%)

A fragment survives editing if:

```
e ≤ τ * L = 0.1 * 200 = 20 characters
```

**Expected Behavior:**

| Edit Type | Fragments Lost | Outcome |
|-----------|---------------|---------|
| No edits | 0/3 | 3/3 match → c ≥ 0.95 |
| Minor formatting | 0/3 | 3/3 match → c ≥ 0.95 |
| Edit beginning | 1/3 | 2/3 match → c ≥ 0.90 |
| Edit beginning + middle | 2/3 | 1/3 match → c < 0.85 (no match) |
| Edit all sections | 3/3 | 0/3 match → c = 0 |

**Current Confidence Assignment (Heuristic):**

```
3/3 fragments match: c = 0.95
2/3 fragments match: c = 0.90
1/3 fragments match: c < 0.85 (below threshold)
```

**Issue:** These are **heuristic scores**, not Bayesian posteriors. Section 5 formalizes this.

---

### 4.2 Text: SimHash Perceptual Matching (Tier 3)

#### 4.2.1 SimHash Algorithm

**Algorithm:**

```
SimHash(text):
    1. Tokenize text into features (e.g., word shingles)
    2. Hash each feature: h_i = SHA256(feature_i)
    3. Compute weighted bit vector:
       For each bit position b:
           v[b] = Σ weight(feature_i) * (1 if h_i[b]==1 else -1)
    4. Final hash:
       SimHash[b] = 1 if v[b] > 0 else 0
```

**Output:** 64-bit or 256-bit fingerprint.

#### 4.2.2 Hamming Distance Distribution

**Question:** What is the expected Hamming distance between SimHashes of similar vs. dissimilar documents?

**Theoretical Model (Charikar 2002):**

For documents with Jaccard similarity J:

```
E[cos(angle)] = J
E[Hamming distance] ≈ (π/180) * arccos(J) * 64  (for 64-bit hash)
```

**Example:**

| Jaccard Similarity | Expected Hamming Distance (64-bit) |
|--------------------|-------------------------------------|
| J = 1.0 (identical) | 0 bits |
| J = 0.9 (very similar) | 8 bits |
| J = 0.8 (similar) | 12 bits |
| J = 0.5 (neutral) | 32 bits |
| J = 0.0 (unrelated) | 32 bits ±8 (random) |

**Current Threshold:**

```
if hamming_distance ≤ 10:
    similarity = 1.0 - (distance / 64)
    confidence = similarity * 0.90
```

**Issue:** Threshold of 10 is chosen heuristically. **Validation required.**

#### 4.2.3 False Positive Rate Estimation

**Model:**

Assume random documents have Hamming distance ~ N(32, σ²) (approximately normal with mean 32, variance σ²).

For σ ≈ 4 (typical):

```
P(distance ≤ 10 | random) = CDF_Normal(10; μ=32, σ=4)
                          ≈ Φ((10-32)/4) = Φ(-5.5)
                          ≈ 2 × 10^(-8)
```

**Interpretation:** False positive rate ≈ 1 in 50 million for unrelated documents.

**VALIDATION REQUIRED:** Measure on real corpus (Section 8).

#### 4.2.4 False Negative Rate

**Question:** Can an attacker paraphrase text to evade detection?

**Attack Model:**

- Synonym replacement (e.g., "big" → "large")
- Sentence reordering
- Paragraph merging/splitting

**Robustness:**

SimHash is **robust to minor edits** but **vulnerable to systematic paraphrasing**. Expected false negative rate:

```
FNR ≈ 5-20% for machine paraphrasing (e.g., GPT-4 rewrite)
```

**Implication:** Tier 3 provides **indicative evidence**, not proof. Should be combined with Tier 2.

---

### 4.3 Images: Perceptual Hash (pHash)

#### 4.3.1 pHash Algorithm

**Algorithm (DCT-based perceptual hash):**

```
pHash(image):
    1. Resize to 32×32 grayscale
    2. Compute 2D Discrete Cosine Transform (DCT)
    3. Extract 8×8 low-frequency coefficients
    4. Compute median of coefficients
    5. Generate 64-bit hash: bit[i] = 1 if coef[i] > median else 0
```

**Properties:**
- Robust to JPEG compression
- Robust to minor resizing, cropping
- Robust to brightness/contrast adjustments

#### 4.3.2 Hamming Distance Distribution

**Empirical Studies (Zauner 2010):**

| Transformation | Expected Hamming Distance |
|----------------|---------------------------|
| Identical image | 0 bits |
| JPEG compression (Q=80) | 2-5 bits |
| Resize ±10% | 3-7 bits |
| Gaussian blur (σ=1) | 5-10 bits |
| Crop 10% | 8-15 bits |
| Rotation ±5° | 15-25 bits |
| Unrelated image | 32 ±8 bits |

**Current Threshold:**

```
if hamming_distance ≤ 12:
    confidence = (1.0 - distance/64) * 0.90
```

**False Positive Rate:**

Assuming random images:

```
P(distance ≤ 12 | random) ≈ Φ((12-32)/6) ≈ Φ(-3.3) ≈ 5 × 10^(-4)
```

**Interpretation:** FPR ≈ 1 in 2000 for unrelated images. **This is higher than text** due to lower entropy in low-frequency DCT coefficients.

**VALIDATION REQUIRED:** Measure on ImageNet or COCO dataset (Section 8).

#### 4.3.3 Patch-Based Fragment Matching

**Algorithm:**

```
Select 4-6 patches from image:
    1. Compute spatial entropy map
    2. Select high-entropy regions (edges, textures)
    3. Extract 128×128 patches
    4. Store SHA256(patch) for each
```

**Collision Probability:**

For 128×128 RGB patches:

```
Patch size: 128 * 128 * 3 = 49,152 bytes
Hash space: 2^256
P(collision | random) ≈ 2^(-256)
```

**Multi-Patch Matching:**

```
if ≥3 of 6 patches match:
    confidence = 0.92
elif ≥2 of 6 patches match:
    confidence = 0.85
```

**Validation Required:** Measure false positive rate on image corpora (Section 8).

---

### 4.4 Video: Temporal I-Frame Sampling

#### 4.4.1 Video Forensic Strategy

**Current Implementation (Metadata Mode):**

```
1. Hash entire video file: SHA256(video_bytes)
2. Extract metadata (duration, resolution, codec)
3. Store metadata hash: SHA256(metadata_json)
```

**Security:**
- Tier 1: Exact hash match (1.0 confidence)
- Tier 2: Metadata hash match (0.95 confidence, video re-encoded)

**Limitation:** Sensitive to re-encoding. **I-frame sampling** (in development) provides better robustness.

#### 4.4.2 I-Frame Sampling (Planned)

**Algorithm:**

```
Extract I-frames at t = [0%, 25%, 50%, 75%, 100%] of duration:
    For each I-frame:
        1. Compute pHash (as in Section 4.3.1)
        2. Store hash
```

**Matching Rule:**

```
if ≥3 of 5 I-frames match (Hamming ≤ 12):
    confidence = 0.88
```

**Expected Performance:**

| Transformation | I-Frames Matched | Confidence |
|----------------|------------------|------------|
| No edits | 5/5 | 1.0 (exact hash) |
| Re-encode (same codec) | 4-5/5 | 0.88-0.92 |
| Re-encode (different codec) | 3-4/5 | 0.85-0.88 |
| Trim beginning/end | 3/5 | 0.85 |
| Major editing | <3/5 | <0.80 (no match) |

**Validation Required:** Measure on video re-encoding datasets (Section 8).

#### 4.4.3 Video Metadata Hash

**Alternative: Metadata-Only Verification**

```
metadata = {
    "duration": 5.0,
    "width": 1280,
    "height": 720,
    "fps": 30.0,
    "codec": "h264"
}
metadata_hash = SHA256(json(metadata))
```

**Matching Rule:**

```
if metadata_hash matches:
    confidence = 0.95  (video preserved, likely re-encoded)
```

**False Positive Risk:**

Common video parameters (e.g., 1920×1080, 30fps, h264) may collide. **Need corpus analysis** (Section 8).

---

### 4.5 Audio: MFCC Spectral Fingerprinting

#### 4.5.1 Audio Forensic Strategy

**Current Implementation (Metadata Mode):**

```
1. Hash entire audio file: SHA256(audio_bytes)
2. Extract metadata (duration, sample_rate, codec)
3. Store metadata hash: SHA256(metadata_json)
```

**Limitation:** Sensitive to format conversion (MP3 → WAV, bitrate changes).

#### 4.5.2 MFCC Fingerprinting (Planned)

**Algorithm:**

```
Extract MFCC features:
    1. Segment audio into 4-6 high-variance segments (1 second each)
    2. Compute Mel-Frequency Cepstral Coefficients (MFCC) for each
    3. Take mean MFCC vector (13 coefficients)
    4. Store hash: SHA256(MFCC_vector)
```

**Matching Rule:**

```
For each suspect segment:
    Compute MFCC distance: d = ||MFCC_suspect - MFCC_evidence||₂

if ≥3 of 6 segments have d ≤ threshold:
    confidence = 0.88
```

**Expected Distance Distribution:**

| Transformation | Expected MFCC Distance |
|----------------|------------------------|
| Identical audio | 0.0 |
| MP3 re-encode (192kbps) | 0.1-0.3 |
| Volume adjustment | 0.2-0.5 |
| Noise addition (SNR 30dB) | 0.5-1.0 |
| Pitch shift ±5% | 1.5-3.0 |
| Time stretch ±10% | 3.0-5.0 |
| Unrelated audio | 10+ |

**Threshold Selection:**

```
threshold = 1.5  (tolerates re-encoding, detects pitch/time changes)
```

**Validation Required:** Measure on audio corpus (LibriSpeech, MUSDB18) with controlled transformations (Section 8).

---

### 4.6 PDF: Page-Level Fingerprinting

**Algorithm:**

```
For each page in PDF:
    1. Extract text: text_p = extract_text(page)
    2. Extract images: images_p = extract_images(page)
    3. Compute:
        text_hash_p = SHA256(text_p)
        image_hash_p = SHA256(concat(images_p))
    4. Store: {page: p, text_hash: h_t, image_hash: h_i}
```

**Matching Rule:**

```
matched_pages = count(pages with text_hash match OR image_hash match)

if matched_pages / total_pages ≥ 0.90:
    confidence = 0.92
elif matched_pages / total_pages ≥ 0.75:
    confidence = 0.85
else:
    confidence < 0.80 (no match)
```

**Validation Required:** Measure on PDF corpus with controlled edits (Section 8).

---

### 4.7 Binary: Byte-Level Entropy Analysis

**Algorithm:**

```
For binary artifacts (executables, archives, etc.):
    1. Compute overall SHA256 (Tier 1)
    2. Select N high-entropy byte ranges (e.g., 512 bytes each)
    3. Store SHA256(byte_range) for each
```

**Matching Rule (same as text fragments):**

```
if ≥2 of 3 byte ranges match:
    confidence = 0.90
```

**Expected Performance:**

Binary files are typically high-entropy (compressed, encrypted), so fragment collision is extremely unlikely.

**Validation Required:** Measure on binary corpus (Section 8).

---

## 5. Confidence Model: Bayesian Formalization

This section formalizes confidence scores as **Bayesian posterior probabilities**, replacing heuristic values with rigorous probability theory.

### 5.1 Bayesian Framework

**Goal:** Compute posterior probability of authenticity:

```
P(authentic | observations) = P(A | O)
```

Using Bayes' theorem:

```
P(A | O) = P(O | A) * P(A) / P(O)
```

Where:
- **P(A)** = prior probability (depends on context)
- **P(O | A)** = likelihood (artifact-specific, Section 4)
- **P(O)** = evidence (normalization constant)

**Expanded Form:**

```
P(A | O) = P(O | A) * P(A) / [P(O | A) * P(A) + P(O | ¬A) * P(¬A)]
```

---

### 5.2 Prior Probability: P(A)

**Context-Dependent Priors:**

| Context | P(A) | Rationale |
|---------|------|-----------|
| User submits content claiming it's theirs | 0.50 | Neutral prior |
| Content flagged by automated system | 0.10 | High false alarm rate |
| Content submitted with valid watermark ID | 0.80 | Strong prior evidence |
| Legal proceeding with chain of custody | 0.95 | High trust |

**Policy Decision:** System operators choose priors based on deployment context.

**Example:** For a public verification API with no authentication, use **P(A) = 0.50** (neutral).

---

### 5.3 Likelihood Functions: P(O | A)

**Tier 1: Exact Hash Match**

```
P(exact_hash_match | authentic) = 1.0 - 2^(-256)  ≈ 1.0
P(exact_hash_match | not_authentic) = 2^(-256)     ≈ 0.0
```

**Posterior (neutral prior):**

```
P(A | exact_match) = 1.0 * 0.5 / [1.0 * 0.5 + 0.0 * 0.5] ≈ 1.0
```

**Current Confidence: 1.0** ✅

---

**Tier 1: Watermark Removed (Pre-Watermark Hash Match)**

```
P(pre_hash_match | authentic, watermark_removed) ≈ 1.0
P(pre_hash_match | not_authentic) = 2^(-256) ≈ 0.0
```

**Interpretation:** High confidence in authenticity, but watermark removal is certain.

**Current Confidence: 0.95**

**Bayesian Justification:**

This is a **policy decision** to penalize watermark removal. Mathematically:

```
P(A | pre_hash_match) ≈ 1.0  (authentic)
P(watermark_intact | pre_hash_match) = 0.0  (removed)

Final score = P(A) * penalty_for_removal = 1.0 * 0.95 = 0.95
```

**Conclusion:** 0.95 reflects **authentic but tampered**, not reduced confidence in authenticity per se.

---

**Tier 2: Fragment Matching (2-of-3)**

**Likelihoods:**

From Section 4.1.3:

```
P(≥2 fragments match | authentic) = 1.0 - FNR  (depend on edit tolerance)
P(≥2 fragments match | not_authentic) = FPR ≈ 10^(-12)
```

**Assume:**
- FNR = 0.05 (5% false negative rate, e.g., minor edits lost fragments)
- FPR = 10^(-12) (validated in Section 8)
- Prior: P(A) = 0.50

**Posterior:**

```
P(A | 2-of-3 match) = (1 - 0.05) * 0.50 / [(1 - 0.05) * 0.50 + 10^(-12) * 0.50]
                    = 0.95 * 0.50 / [0.95 * 0.50 + 0.0]
                    ≈ 1.0
```

**Issue:** With negligible FPR, posterior ≈ 1.0, not 0.90 as currently assigned.

**Resolution:**

The current 0.90 score accounts for:
1. **Uncertainty in fragment selection** (entropy threshold validation pending)
2. **Conservative estimate** until empirical validation (Section 8)

**Formal Target:**

After validation, if:
- FPR_validated < 10^(-9)
- FNR_validated < 0.10

Then assign:

```
c = 0.95  (high confidence, acknowledging minor edit tolerance)
```

---

**Tier 3: SimHash Perceptual Matching**

**Assume:**
- Hamming distance d ≤ 10 (out of 64 bits)
- FPR = 2 × 10^(-8) (from Section 4.2.3)
- FNR = 0.15 (15% false negative for paraphrased text)
- Prior: P(A) = 0.50

**Posterior:**

```
P(A | SimHash_match) = (1 - 0.15) * 0.50 / [(1 - 0.15) * 0.50 + 2×10^(-8) * 0.50]
                     = 0.85 * 0.50 / [0.85 * 0.50 + 0.0]
                     ≈ 1.0
```

**Issue:** Again, negligible FPR yields posterior ≈ 1.0.

**Resolution:**

SimHash is **vulnerable to systematic paraphrasing**, so FNR is significant. Current confidence assignment:

```
c = (1 - d/64) * 0.90 = (1 - 10/64) * 0.90 ≈ 0.76
```

**Rationale:** The 0.90 multiplier penalizes Tier 3 relative to Tier 1/2, reflecting **lower reliability**.

**Formal Target After Validation:**

```
c = P(A | SimHash_match) * reliability_factor
  = 1.0 * 0.70  (if FNR validated at ~15%)
  = 0.70-0.80 range
```

---

### 5.4 Combined Evidence (Multi-Tier Matching)

**Scenario:** Tier 1 fails, but both Tier 2 and Tier 3 match.

**Likelihood Ratio:**

```
LR = P(Tier2 ∧ Tier3 | A) / P(Tier2 ∧ Tier3 | ¬A)
   = [(1-FNR_T2) * (1-FNR_T3)] / [FPR_T2 * FPR_T3]
   = [0.95 * 0.85] / [10^(-12) * 2×10^(-8)]
   ≈ 4 × 10^19
```

**Posterior (neutral prior):**

```
P(A | T2 ∧ T3) = LR / (LR + 1) ≈ 1.0
```

**Implication:** Multiple tiers provide **very strong evidence** even when individual FPRs are small.

**Current Practice:** Take **best tier score** (conservative). Could improve by combining tiers multiplicatively.

---

### 5.5 Three-Output Model

**CIAF Watermarking Evidence should produce three separate outputs, not a single "confidence" score:**

#### **Output 1: Cryptographic Verdict**

| Tier 1 Result | Verdict | Meaning |
|---------------|---------|----------|
| Exact hash (post-watermark) | EXACT_MATCH | Cryptographically certain (P ≈ 1.0) |
| Exact hash (pre-watermark) | WATERMARK_REMOVED | Cryptographically certain, attribution stripped |
| Normalized hash | NORMALIZED_MATCH | Format-tolerant match |
| No hash match | NO_CRYPTOGRAPHIC_MATCH | Proceed to statistical analysis |

#### **Output 2: Statistical Evidence (Tiers 2/3)**

| Match Pattern | Statistical Estimate | Status |
|---------------|---------------------|--------|
| 3/3 fragments | likelihood_ratio ≈ 10^12 | [TARGET - requires validation] |
| 2/3 fragments | likelihood_ratio ≈ 10^9 | [TARGET - requires validation] |
| SimHash d ≤ 10 | likelihood_ratio ≈ 10^7 | [TARGET - requires validation] |

**Note:** These are **likelihood ratios** (P(observation | authentic) / P(observation | not authentic)), **not final probabilities**. They must be combined with priors via Bayes' theorem.

#### **Output 3: Policy-Adjusted Operational Score**

| Scenario | Operational Score | Rationale |
|----------|-------------------|------------|
| Exact match | 1.00 | Cryptographic certainty |
| Watermark removed | 0.95 | Authentic but policy penalty for removal |
| Normalized match | 0.90 | Format changes tolerated with penalty |
| 3/3 fragments | 0.95 | High statistical evidence |
| 2/3 fragments | 0.90 | Adequate statistical evidence |
| SimHash match | 0.70-0.80 | Indicative but not conclusive |

**Key Distinction:**
- **Cryptographic verdicts** are binary (match/no match) with provable security
- **Statistical estimates** are likelihood ratios requiring corpus validation
- **Operational scores** blend statistics with policy adjustments (penalties, risk tolerance)

**Current Implementation Issue:** CIAF Watermarking Evidence conflates these three outputs into a single "confidence" score. This should be separated for intellectual honesty.

---

### 5.6 Example JSON Output (Recommended Structure)

**Scenario 1: Exact Match (Watermarked Version)**

```json
{
  "verification_result": {
    "cryptographic_verdict": {
      "tier": 1,
      "verdict": "EXACT_MATCH",
      "hash_matched": "post_watermark",
      "proof": "SHA256 collision probability ≤ 2^-256"
    },
    "statistical_evidence": null,
    "operational_score": {
      "score": 1.00,
      "interpretation": "Cryptographically certain - exact distributed copy",
      "decision": "ACCEPT",
      "alert": null
    },
    "metadata": {
      "artifact_id": "3079284d-af40-4ba7-b156-479439384914",
      "watermark_id": "wmk-4f6cbc24-70ff-432d-a754-bbcb855446e9",
      "verification_timestamp": "2026-04-07T14:32:15Z"
    }
  }
}
```

**Scenario 2: Watermark Removed (Pre-Watermark Hash Match)**

```json
{
  "verification_result": {
    "cryptographic_verdict": {
      "tier": 1,
      "verdict": "WATERMARK_REMOVED",
      "hash_matched": "pre_watermark",
      "proof": "SHA256 match confirms authenticity, watermark deliberately removed"
    },
    "statistical_evidence": null,
    "operational_score": {
      "score": 0.95,
      "interpretation": "Authentic content, attribution removed",
      "decision": "ACCEPT_WITH_ALERT",
      "alert": "WATERMARK_REMOVAL_DETECTED"
    },
    "metadata": {
      "artifact_id": "3079284d-af40-4ba7-b156-479439384914",
      "policy_penalty": 0.05,
      "legal_note": "May constitute licensing violation"
    }
  }
}
```

**Scenario 3: Statistical Match (Fragment-Based)**

```json
{
  "verification_result": {
    "cryptographic_verdict": {
      "tier": 1,
      "verdict": "NO_CRYPTOGRAPHIC_MATCH",
      "note": "Content has been edited"
    },
    "statistical_evidence": {
      "tier": 2,
      "fragments_matched": "2 of 3",
      "likelihood_ratio": "~10^9 [TARGET]",
      "interpretation": "Strong statistical evidence of authenticity",
      "fpr_estimate": "<10^-12 [TARGET]",
      "validation_status": "UNVALIDATED - requires corpus testing"
    },
    "operational_score": {
      "score": 0.90,
      "interpretation": "High confidence with minor edits detected",
      "decision": "ACCEPT",
      "alert": "CONTENT_MODIFIED"
    },
    "metadata": {
      "artifact_id": "3079284d-af40-4ba7-b156-479439384914",
      "edit_estimate": "~10-20% content changed"
    }
  }
}
```

**Scenario 4: Perceptual Match (SimHash)**

```json
{
  "verification_result": {
    "cryptographic_verdict": {
      "tier": 1,
      "verdict": "NO_CRYPTOGRAPHIC_MATCH"
    },
    "statistical_evidence": {
      "tier": 3,
      "simhash_distance": 8,
      "similarity": 0.875,
      "likelihood_ratio": "~10^7 [TARGET]",
      "interpretation": "Indicative evidence - possibly paraphrased",
      "fpr_estimate": "~10^-8 [TARGET]",
      "validation_status": "UNVALIDATED"
    },
    "operational_score": {
      "score": 0.75,
      "interpretation": "Moderate confidence - manual review recommended",
      "decision": "MANUAL_REVIEW",
      "alert": "POSSIBLE_PARAPHRASE"
    },
    "metadata": {
      "artifact_id": "3079284d-af40-4ba7-b156-479439384914",
      "recommendation": "Combine with Tier 2 evidence if available"
    }
  }
}
```

**Scenario 5: No Match**

```json
{
  "verification_result": {
    "cryptographic_verdict": {
      "tier": 1,
      "verdict": "NO_CRYPTOGRAPHIC_MATCH"
    },
    "statistical_evidence": {
      "tier_2_result": "0 of 3 fragments matched",
      "tier_3_result": "SimHash distance 35 (unrelated)",
      "interpretation": "No forensic evidence of authenticity"
    },
    "operational_score": {
      "score": 0.00,
      "interpretation": "Not authentic or heavily modified",
      "decision": "REJECT",
      "alert": null
    },
    "metadata": {
      "artifact_id": "3079284d-af40-4ba7-b156-479439384914"
    }
  }
}
```

**Key Benefits of This Structure:**

1. **Transparent**: Each output type is clearly labeled and separated
2. **Interpretable**: Includes human-readable interpretation for each layer
3. **Actionable**: Provides explicit decision + alert fields
4. **Honest**: Marks unvalidated targets with [TARGET] flags
5. **Traceable**: Includes metadata for audit trails

---

## 6. Decision Layer: Operational Thresholds

### 6.1 ROC Curve Analysis

**Receiver Operating Characteristic (ROC):**

For each confidence threshold τ:

```
True Positive Rate (TPR) = P(c ≥ τ | authentic)
False Positive Rate (FPR) = P(c ≥ τ | not authentic)
```

**Ideal Operating Point:**

Maximize:

```
F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
```

Where:

```
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
```

**Current Thresholds (Heuristic):**

| Threshold | Decision | Rationale |
|-----------|----------|-----------|
| c ≥ 0.85 | Accept as authentic | High confidence |
| 0.70 ≤ c < 0.85 | Manual review | Uncertain |
| c < 0.70 | Reject | Low confidence |

**Validation Required:**

Plot ROC curve on test dataset (Section 8) and select optimal threshold based on:
- **Risk tolerance** (cost of false positives vs. false negatives)
- **Deployment context** (legal, content moderation, spam detection)

---

### 6.2 Cost-Sensitive Decision Policy

**Asymmetric Costs:**

```
Cost(false positive) = C_FP  (incorrectly claim authentic)
Cost(false negative) = C_FN  (miss genuine content)
```

**Optimal Threshold:**

Minimize expected cost:

```
τ_opt = argmin_τ [C_FP * FPR(τ) + C_FN * FNR(τ)]
```

**Example Policies:**

| Context | C_FP | C_FN | Optimal τ | Rationale |
|---------|------|---------|-----------|-----------|
| Legal proceedings | High | Low | 0.95+ | Minimize false accusations |
| Spam detection | Low | High | 0.70 | Catch more spam, accept false positives |
| Content attribution | Medium | Medium | 0.85 | Balanced |

---

### 6.3 Confidence Interval Reporting

**Current Practice:** Report single confidence score (e.g., c = 0.92).

**Improvement:** Report confidence interval reflecting uncertainty:

```
c = 0.92 ± 0.05  (95% confidence interval)
```

**Derivation:**

Use bootstrap resampling:
1. Resample fragments/features N times
2. Compute confidence for each sample
3. Report mean ± 2 * standard_deviation

**Example:**

```json
{
  "confidence": 0.92,
  "confidence_interval": [0.88, 0.96],
  "confidence_level": 0.95
}
```

---

## 7. False Positive/Negative Rate Analysis

### 7.1 Definitions

**False Positive Rate (FPR):**

```
FPR = P(system claims match | content not authentic)
```

**False Negative Rate (FNR):**

```
FNR = P(system claims no match | content is authentic)
```

**Relationship to Confidence:**

```
FPR = P(c ≥ threshold | ¬A)
FNR = P(c < threshold | A)
```

---

### 7.2 Tier-Specific Rates

#### Tier 1: Cryptographic Hashing

**FPR (False Positive):**

```
FPR_T1 = 2^(-256)  ≈ 10^(-77)  (SHA-256 collision)
```

**FNR (False Negative):**

```
FNR_T1 = 0  (genuine copy always matches)
```

**Conclusion:** Tier 1 has negligible error rates (cryptographic guarantee).

---

#### Tier 2: Fragment Matching (Text)

**FPR (False Positive):**

**Theoretical:** 10^(-540) (Section 4.1.3)

**Practical (accounting for low-entropy fragments):**

If entropy filtering fails (bad implementation or edge case):

```
FPR_T2 ≈ 10^(-12) to 10^(-9)  (target after validation)
```

**FNR (False Negative):**

Depends on edit tolerance:

| Edit Distance | FNR |
|---------------|-----|
| No edits | 0% |
| <10% edits | 5% (1 fragment affected) |
| 10-30% edits | 15% (2 fragments affected) |
| >30% edits | >90% (all fragments affected) |

**Target:**

```
FNR_T2 ≤ 0.10  (for authentic content with minor edits)
```

---

#### Tier 3: Perceptual Hashing (Text)

**FPR (False Positive):**

From Section 4.2.3:

```
FPR_T3 ≈ 2 × 10^(-8)  (Hamming distance ≤ 10)
```

**FNR (False Negative):**

```
FNR_T3 ≈ 0.15  (for paraphrased text, validated experimentally)
```

**Implication:** Tier 3 has **higher false negative rate** than Tier 2 but still low false positive rate.

---

#### Images: pHash

**FPR (False Positive):**

From Section 4.3.2:

```
FPR_pHash ≈ 5 × 10^(-4)  (1 in 2000 unrelated images)
```

**FNR (False Negative):**

```
FNR_pHash ≈ 0.05  (for JPEG compression, minor edits)
FNR_pHash ≈ 0.30  (for cropping >20%, rotation >10°)
```

**Target:** Validate on ImageNet with controlled transformations (Section 8).

---

#### Video: I-Frame Sampling

**FPR (False Positive):**

```
FPR_video ≈ 10^(-6) to 10^(-4)  (depends on I-frame pHash threshold)
```

**FNR (False Negative):**

```
FNR_video ≈ 0.10  (for re-encoding with same codec)
FNR_video ≈ 0.40  (for cross-codec conversion H.264 → VP9)
```

**Validation Required:** Measure on video dataset (Section 8).

---

#### Audio: MFCC

**FPR (False Positive):**

```
FPR_audio ≈ 10^(-5)  (unrelated audio with MFCC distance ≤ 1.5)
```

**FNR (False Negative):**

```
FNR_audio ≈ 0.05  (for MP3 re-encoding)
FNR_audio ≈ 0.30  (for pitch shift ±5%)
```

**Validation Required:** Measure on LibriSpeech or MUSDB18 (Section 8).

---

### 7.3 System-Level Error Rates

**Critical Issue: Decision Rule Must Be Specified First**

**Current CIAF Watermarking Evidence Logic (Tier Precedence):**

```
if Tier1_matches:
    return Tier1_result
elif Tier2_matches:
    return Tier2_result
elif Tier3_matches:
    return Tier3_result
else:
    return NO_MATCH
```

This is a **cascading decision rule**, not a union ("accept if any tier fires").

**System-Level FPR (with tier precedence):**

```
FPR_system = P(T1 fires falsely) + 
             P(T1 fails AND T2 fires falsely) +
             P(T1 fails AND T2 fails AND T3 fires falsely)
           
           ≈ 2^(-256) + (1.0) * 10^(-12) + (1.0) * (1.0) * 2×10^(-8)
           ≈ 2×10^(-8)  [TARGET - dominated by Tier 3]
```

**Assumptions:**
1. Tier 1 false positives are cryptographically negligible (2^-256)
2. Tier 2/3 FPRs are **independent** (requires validation)
3. Tier 2 target FPR = 10^(-12) (unvalidated)
4. Tier 3 target FPR = 2×10^(-8) (unvalidated)

**System-Level FNR (exact copies):**

```
FNR_system (exact copy) = 0  (Tier 1 always detects)
```

**System-Level FNR (edited content, no Tier 1 match):**

```
FNR_system (edited) = P(T2 fails AND T3 fails | edited)
```

**If Tier 2 and Tier 3 are independent:**

```
FNR_system (edited) ≈ FNR_T2 * FNR_T3 = 0.10 * 0.15 = 0.015  [TARGET]
```

**But this assumes independence**, which may not hold:
- Heavy paraphrasing defeats **both** fragment matching and SimHash
- Copy-paste-edit preserves **both** fragments and perceptual similarity

**Validation Required:**  
Measure **joint error rates** on real edit patterns, not just products of marginal rates.

**Honest Assessment:** These numbers are **engineering targets** requiring experimental confirmation. The simple max() and product formulas are approximations that may not capture correlation structure.

---

## 8. Validation Experiments

This section defines **required experiments** to empirically calibrate confidence scores and validate theoretical models.

### 8.1 Text Fragment Validation

**Experiment 1: Random Document Collision Test**

**Goal:** Measure FPR_T2 (false positive rate for fragment matching).

**Procedure:**

1. Select corpus: 1 million English documents (e.g., Wikipedia, arXiv papers)
2. For each document pair (i, j) where i ≠ j:
   - Extract 3 fragments from each
   - Count pairs with ≥2 fragment matches
3. Measure:
   ```
   FPR_measured = (# pairs with ≥2 matches) / (# total pairs)
   ```

**Expected Result:**

```
FPR_measured < 10^(-12)  [TARGET - theoretical prediction]
```

**Decision Criteria:**
- If FPR_measured < 10^(-12): Excellent, use current settings
- If 10^(-12) ≤ FPR < 10^(-9): Acceptable, monitor for corpus-specific issues
- If FPR ≥ 10^(-9): **Unacceptable** - increase entropy threshold or fragment count

---

**Experiment 2: Edit Tolerance Test**

**Goal:** Measure FNR_T2 (false negative rate for edited content).

**Procedure:**

1. Select 10,000 documents
2. For each document:
   - Create watermarked version
   - Apply edits: 5%, 10%, 20%, 30% character changes
   - Measure fragment match rate
3. Plot: FNR vs. edit percentage

**Expected Result:**

```
FNR(5% edits) < 0.05   [TARGET]
FNR(10% edits) < 0.10  [TARGET]
FNR(20% edits) < 0.30  [TARGET]
```

**Note:** These are initial engineering targets. Actual FNR depends on edit type (formatting vs. content changes).

**If FNR > target:** Increase number of fragments (N = 3 → 5) or adjust fragment positions.

---

### 8.2 SimHash Validation

**Experiment 3: SimHash Distance Distribution**

**Goal:** Measure FPR_T3 and FNR_T3 for Tier 3.

**Procedure:**

1. Select corpus: 100,000 document pairs
2. For each pair:
   - Compute SimHash
   - Measure Hamming distance
3. Create two distributions:
   - **Similar documents** (human-labeled as paraphrases)
   - **Dissimilar documents** (random pairs)
4. Measure:
   ```
   FPR(threshold) = P(distance ≤ threshold | dissimilar)
   FNR(threshold) = P(distance > threshold | similar)
   ```

**Expected Results:**

**⚠️ Values shown are initial targets pending experimental validation**

| Threshold | FPR [TARGET] | FNR [TARGET] |
|-----------|-----|-----|
| d ≤ 8 | 10^(-10) | 0.25 |
| d ≤ 10 | 10^(-8) | 0.15 |
| d ≤ 12 | 10^(-6) | 0.10 |

**Optimal Threshold:** Select based on deployment context (Section 6.2).

---

### 8.3 Image pHash Validation

**Experiment 4: ImageNet Transformation Test**

**Goal:** Measure FPR and FNR for image perceptual hashing.

**Procedure:**

1. Select 10,000 images from ImageNet
2. For each image:
   - Apply transformations: JPEG(Q=80), resize ±10%, crop 10%, Gaussian blur
   - Compute pHash
   - Measure Hamming distance
3. Compute FNR for each transformation
4. Measure FPR on random image pairs

**Expected Results:**

**⚠️ Values shown are illustrative targets pending ImageNet validation**

| Transformation | Hamming Distance [TARGET] | FNR (threshold=12) [TARGET] |
|----------------|------------------|--------------------|
| JPEG (Q=80) | 3-5 | <0.01 |
| Resize ±10% | 4-7 | <0.05 |
| Crop 10% | 8-15 | ~0.30 |
| Gaussian blur | 5-10 | ~0.10 |

**FPR (unrelated images):**

```
FPR(d ≤ 12) < 10^(-3)
```

---

### 8.4 Video I-Frame Validation

**Experiment 5: Video Re-Encoding Test**

**Goal:** Measure FNR for video I-frame matching.

**Procedure:**

1. Select 1,000 videos (5-10 seconds each)
2. For each video:
   - Extract 5 I-frames
   - Re-encode with: H.264 (same codec), VP9 (different codec), HEVC
   - Extract I-frames from re-encoded version
   - Measure pHash distance for each I-frame pair
3. Count I-frames with distance ≤ 12
4. Compute FNR = P(<3 I-frames match | same video)

**Expected Results:**

**⚠️ Values shown are initial targets pending video corpus validation**

| Re-Encoding | I-Frames Matched [TARGET] | FNR [TARGET] |
|-------------|------------------|-----|
| H.264 (same codec) | 4-5/5 | <0.05 |
| VP9 (different codec) | 3-4/5 | ~0.20 |
| HEVC | 3-4/5 | ~0.15 |

---

### 8.5 Audio MFCC Validation

**Experiment 6: Audio Transformation Test**

**Goal:** Measure FNR for audio MFCC matching.

**Procedure:**

1. Select 1,000 audio clips (5 seconds each) from LibriSpeech
2. For each clip:
   - Extract 6 MFCC segments
   - Apply transformations: MP3 re-encode (192kbps), volume ±20%, pitch ±5%
   - Extract MFCC from transformed audio
   - Measure Euclidean distance
3. Count segments with distance ≤ 1.5
4. Compute FNR = P(<3 segments match | same audio)

**Expected Results:**

**⚠️ Values shown are initial targets pending LibriSpeech validation**

| Transformation | Segments Matched [TARGET] | FNR [TARGET] |
|----------------|------------------|-----|
| MP3 re-encode | 5-6/6 | <0.05 |
| Volume ±20% | 5-6/6 | <0.05 |
| Pitch ±5% | 2-4/6 | ~0.40 |

---

### 8.6 Adversarial Attack Testing

**Experiment 7: Targeted Fragment Removal**

**Goal:** Measure robustness against adversarial attacks.

**Attack Model:**

Adversary knows:
- Fragment selection algorithm
- Entropy threshold
- Number of fragments (N=3)

**Attack Strategy:**

1. Obtain watermarked content
2. Identify likely fragment locations (beginning/middle/end)
3. Edit only those regions (e.g., synonym replacement, paraphrasing)
4. Leave other content intact

**Defense Validation:**

1. Apply attack to 1,000 watermarked documents
2. Measure:
   - Success rate = P(≥2 fragments removed | attack)
   - Detectability = P(attack is detectable via edit patterns)

**Expected Result:**

```
Success rate: 40-60%  [TARGET - depends on attack sophistication]
```

**Mitigation:**

- Increase N (3 → 5 fragments)
- Randomize fragment positions
- Add steganographic markers

**If success rate > 70%:** Fragment strategy needs redesign.

---

## 9. Attack Resistance Analysis

### 9.1 Threat Model

**Attacker Goals:**

1. **False Positive Attack:** Create fake content that matches evidence record
2. **False Negative Attack:** Modify authentic content to evade detection
3. **Removal Attack:** Strip watermark while preserving content

**Attacker Capabilities:**

- **White-box:** Knows algorithm, sees evidence records
- **Black-box:** Can query verification API
- **Computational:** Bounded by 2^80 operations (practical limit)

---

### 9.2 Tier 1: Cryptographic Attack Resistance

**Attack 1: Pre-Image Attack**

**Goal:** Given evidence.hash_after_watermark, find content S' such that SHA256(S') matches.

**Complexity:** 2^256 operations (SHA-256 pre-image resistance)

**Defense:** Infeasible with current technology.

---

**Attack 2: Collision Attack**

**Goal:** Find two distinct contents S₁, S₂ such that SHA256(S₁) = SHA256(S₂).

**Complexity:** 2^128 operations (birthday bound)

**Defense:** Infeasible (would break Bitcoin, TLS, etc.).

**Conclusion:** Tier 1 is **cryptographically secure** under standard assumptions.

---

### 9.3 Tier 2: Fragment Collision Attack

**Attack 3: Fragment Forgery**

**Goal:** Create content containing 2-of-3 fragments from evidence record without being the original.

**Strategy:**

1. Obtain evidence record (contains 3 fragment hashes)
2. Brute-force search for text containing matching fragments
3. Embed 2 of 3 fragments into fake content

**Complexity:**

For each fragment (200 bytes, entropy > 2.6 bits/char):

```
Brute-force search: 2^(2.6*200) ≈ 2^520 operations per fragment
Finding 2 fragments: 2 * 2^520 ≈ 2^521 operations
```

**Defense:** Computationally infeasible.

**Practical Attack:**

If **evidence records are public**, attacker can:
1. Copy exact fragments from evidence
2. Paste into new document
3. Claim authenticity

**Defense:**

- Evidence records should be **hash-only** (not plaintext fragments)
- Use **fragment offsets** as additional verification
- Implement **contextual checks** (fragments should appear in logical order)

**Validation Required:** Test against copy-paste attacks (Section 8.6).

---

### 9.4 Tier 3: Similarity Manipulation Attack

**Attack 4: Adversarial Paraphrasing**

**Goal:** Modify text to evade SimHash detection while preserving meaning.

**Strategy:**

1. Use language model (e.g., GPT-4) to paraphrase
2. Check SimHash distance incrementally
3. Stop when distance > 10

**Complexity:** Negligible (automated paraphrasing takes seconds)

**Expected Success Rate:** 80-90% [TARGET - based on GPT-4 paraphrasing capabilities]

**Defense:**

Tier 3 is **not designed to resist adversarial paraphrasing**. It detects:
- Accidental similarity (copy-paste without intent to hide)
- Minor edits (formatting, typos)

**Mitigation:**

- Combine Tier 2 + Tier 3 (adversary must evade both)
- Tier 2 fragment matching is more robust

**Conclusion:** Tier 3 provides **indicative evidence**, not cryptographic proof.

---

### 9.5 Watermark Removal Attack

**Attack 5: Deliberate Watermark Stripping**

**Goal:** Remove watermark while preserving content.

**Strategy:**

1. Identify watermark location (footer/header)
2. Delete watermark text
3. Re-distribute content

**Detection:**

Pre-watermark hash matches → **ALERT: Watermark Removed**

**Countermeasures:**

- Steganographic watermarks (hidden in whitespace, zero-width characters)
- Legal penalties for removal (DMCA-style)

**Limitation:** Cannot prevent removal, only **detect** it.

---

## 10. Calibration Procedure

### 10.1 Calibration Workflow

**Step 1: Collect Representative Dataset**

For each artifact type:
- **Text:** 100,000 documents (news, academic, social media)
- **Images:** 10,000 images (photos, graphics, AI-generated)
- **Video:** 1,000 videos (5-30 seconds each)
- **Audio:** 1,000 audio clips (speech, music)

**Step 2: Run Validation Experiments (Section 8)**

Measure:
- FPR and FNR for each tier
- Confidence score distributions
- Attack success rates

**Step 3: Calibrate Confidence Model**

Adjust parameters:
- Entropy threshold (H_min)
- Fragment count (N_fragments)
- Similarity thresholds (SimHash, pHash, MFCC)
- Confidence multipliers (Section 5.5)

**Step 4: Plot Calibration Curves**

For each confidence score c, measure:

```
Empirical_accuracy(c) = P(authentic | system reports confidence c)
```

**Well-Calibrated System:**

```
Empirical_accuracy(0.90) ≈ 0.90
Empirical_accuracy(0.80) ≈ 0.80
etc.
```

**Plot:** Predicted confidence vs. empirical accuracy (should be diagonal line).

**If miscalibrated:** Apply Platt scaling or isotonic regression to adjust confidence mapping.

---

### 10.2 Continuous Monitoring

**Production Deployment:**

1. Log all verification requests with confidence scores
2. Collect ground-truth labels (user feedback, manual review)
3. Re-measure FPR/FNR monthly
4. Retrain calibration model if drift detected

**Metrics to Monitor:**

```
FPR_production = (false positives) / (total negatives)
FNR_production = (false negatives) / (total positives)
Calibration_error = |empirical_accuracy(c) - c|
```

**Alert if:**
- FPR > 2 * FPR_baseline
- FNR > 1.5 * FNR_baseline
- Calibration error > 0.05

---

### 10.3 A/B Testing

**Scenario:** Test new fragment selection strategy.

**Procedure:**

1. Deploy two systems:
   - **Control:** Current algorithm (N=3 fragments, H_min=2.6)
   - **Treatment:** New algorithm (N=5 fragments, H_min=3.0)
2. Randomly assign users to control/treatment
3. Measure FPR, FNR, latency for each
4. Statistical test: t-test for difference in means

**Decision Rule:**

```
if FPR_treatment < FPR_control AND latency_treatment < 2 * latency_control:
    deploy treatment
else:
    keep control
```

---

## 11. Appendix: Implementation Notes

### 11.1 Computational Complexity

| Operation | Time | Space |
|-----------|------|-------|
| SHA-256 hash (1KB text) | 10 μs | O(1) |
| Fragment extraction (10KB text) | 50 ms | O(N) |
| SimHash computation | 30 ms | O(N) |
| pHash (1024×1024 image) | 20 ms (GPU) | O(1) |
| MFCC extraction (5s audio) | 100 ms | O(N) |

**Bottlenecks:**

- Text: Fragment extraction (entropy computation)
- Images: pHash (DCT transform)
- Video: I-frame extraction (decode video)
- Audio: MFCC (FFT + mel-filterbank)

---

### 11.2 Parallelization

**Batch Processing:**

```python
async def verify_batch(suspects: List[bytes], evidence_ids: List[str]) -> List[float]:
    """Verify multiple artifacts in parallel."""
    tasks = [verify_async(s, e) for s, e in zip(suspects, evidence_ids)]
    return await asyncio.gather(*tasks)
```

**Expected Speedup:** 8-16x on 16-core CPU (I/O bound operations).

---

### 11.3 GPU Acceleration

**Applicable Operations:**

- Image pHash (batch DCT transforms)
- Video I-frame extraction (hardware decode)
- MFCC computation (FFT operations)

**Not Applicable:**

- SHA-256 hashing (optimized on CPU)
- Fragment extraction (memory-bound)

---

### 11.4 Cloud Deployment Considerations

**Latency Budget:**

```
Tier 1 verification: 50 ms (hash comparison)
Tier 2 verification: 200 ms (fragment matching)
Tier 3 verification: 300 ms (perceptual hashing)
Network overhead: 50 ms
Total: <500 ms (target)
```

**Scalability:**

- **Evidence storage:** Distribute across shards (by artifact_id prefix)
- **Verification workers:** Auto-scale based on queue depth
- **Caching:** Cache frequently-accessed evidence records (Redis)

---

## 12. Conclusion

### 12.1 What This Document Is

This is a **formalization and validation framework** for CIAF Watermarking Evidence's verification system. It is:

✅ **A validation plan** defining experiments required to measure actual FPR/FNR  
✅ **A threat model** separating cryptographic proofs from statistical evidence  
✅ **A formalization scaffold** distinguishing verdicts, estimates, and policy scores  
✅ **A calibration procedure** for transforming heuristics into validated probabilities  

### 12.2 What This Document Is Not

❌ **Not a completed mathematical proof** of all confidence scores  
❌ **Not empirically validated** (experiments in Section 8 remain to be executed)  
❌ **Not a claim that all numbers are rigorously derived** (many are targets)  

### 12.3 Key Contributions

**Separation of Guarantee Types:**

1. **Cryptographic Verdicts (Tier 1):**  
   - SHA-256 collision resistance: P(false match) ≤ 2^-256  
   - **Status:** Validated by 40+ years of cryptanalysis  
   - **No corpus calibration needed**

2. **Statistical Evidence (Tier 2/3):**  
   - Fragment/perceptual matching: FPR/FNR **require measurement**  
   - **Status:** Target values provided, experiments required  
   - **Corpus-dependent:** Wikipedia ≠ legal documents ≠ social media

3. **Policy-Adjusted Scores:**  
   - Operational confidence blends statistics with penalties  
   - **Status:** Business logic, not probability theory  
   - **Context-dependent:** Legal proceedings ≠ spam detection

**Honest Assessment of Limitations:**

- **Fragment collision math** (10^-540) is theoretically sound but **ignores corpus structure**
- **System-level FPR/FNR composition** assumes independence (may not hold)
- **Bayesian posteriors** are computed but then **modified by policy factors**
- **Normalized hash security** uses intuition, not rigorous bounds
- **Most numeric targets are unvalidated** until experiments complete

### 12.4 Critical Interpretation (Repeat)

> **CIAF Watermarking Evidence outputs should be interpreted as a combination of:**
> 1. Cryptographic verdicts (provable)
> 2. Empirically calibrated statistical evidence (corpus-dependent)
> 3. Deployment-specific policy thresholds (business logic)
> 
> **These are not a single uniform notion of proof.**

### 12.5 Next Steps

**Before claiming specific confidence values:**

1. ✅ Execute validation experiments (Section 8) on representative datasets
2. ✅ Measure actual FPR/FNR on 100K+ document pairs (text)
3. ✅ Calibrate thresholds (entropy, SimHash, pHash, MFCC)
4. ✅ Plot calibration curves: predicted vs. empirical accuracy
5. ✅ Publish validated error rates with confidence intervals
6. ✅ Implement continuous monitoring in production

**After validation:**

- Replace **[TARGET]** markers with **[VALIDATED: dataset_name, FPR=X, FNR=Y]**
- Update operational thresholds based on measured ROC curves
- Provide corpus-specific calibrations (academic vs. social media)

### 12.6 Recommended Positioning

**In external communications:**

✅ "CIAF Watermarking Evidence provides a **formalized validation framework** separating cryptographic proofs from statistical evidence"  
✅ "Confidence scores blend **cryptographic verdicts, empirical calibration, and policy adjustments**"  
✅ "Tier 1 (exact matching) is cryptographically secure; Tier 2/3 require corpus-specific validation"  

❌ "CIAF Watermarking Evidence confidence scores are rigorous Bayesian posteriors"  
❌ "Fragment matching achieves 10^-12 false positive rate" (without validation caveat)  
❌ "The math is complete" (it's a validation plan, not completed proof)  

### 12.7 Open Questions for Future Work

- **Optimal fragment count:** N=3 vs. N=5 vs. adaptive (corpus-dependent)
- **Joint error rate measurement:** Are Tier 2/3 failures correlated?
- **Cross-modal forensics:** Text + image + metadata evidence fusion
- **Adversarial robustness:** Targeted fragment removal defense
- **Privacy-preserving verification:** Zero-knowledge proofs
- **Corpus-specific calibration:** Legal vs. creative vs. technical text

---

**Document Version:** 1.0  
**Last Updated:** April 7, 2026  
**License:** Business Source License 1.1  
**© 2025-2026 Cognitive Insight. All rights reserved.**
