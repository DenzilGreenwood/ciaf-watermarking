# CIAF: Executive Summary

**Cognitive Insight Audit Framework**  
**Version 1.4.0 | April 7, 2026**

---

## The Problem

Traditional AI watermarks fail when:
- Users strip attribution via copy-paste
- Content is reformatted or partially edited  
- Metadata is removed during format conversion

**Result:** No cryptographic proof of AI generation remains.

---

## The CIAF Solution

A **three-tiered forensic verification system** that maintains authenticity detection even when watermarks are removed:

### **Tier 1: Exact Hash Matching** (100% Confidence)
- SHA-256 cryptographic hashing
- Bit-for-bit verification
- Fastest verification (2ms)

### **Tier 2: Forensic Fragment Matching** (90-95% Confidence)
- DNA-level sampling of high-entropy content regions
- 3-6 strategic fragments per artifact
- Detects tampering even when watermarks stripped
- Resilient to partial edits and mix-and-match attacks

### **Tier 3: Perceptual Fingerprinting** (0-90% Confidence)
- SimHash for text similarity
- pHash for image similarity
- Detects paraphrased or heavily modified content
- Lower confidence but high coverage

---

## Key Innovation: Dual-State Hashing

CIAF records **both** the original (pre-watermark) and distributed (post-watermark) versions:

```
Original Content → Hash A
    ↓ (watermark applied)
Distributed Content → Hash B

Storage: {hash_before: A, hash_after: B, fragments: [f1, f2, f3]}
```

**Detection Capability:**
- Suspect matches Hash B → **Authentic distributed copy** (100%)
- Suspect matches Hash A → **Watermark removed** (95% + alert)
- Suspect matches fragments → **Content modified** (90%)
- No match → **Not authentic** (0%)

---

## Multi-Modal Support

| Artifact Type | Watermark Method | Forensic Strategy | Performance |
|---------------|------------------|-------------------|-------------|
| **Text** | Footer/header tags | 3 high-entropy fragments | 50-100ms ✅ |
| **Images** | Visual overlay + metadata | 4-6 spatial patches | 20-50ms (GPU) ✅ |
| **PDFs** | Metadata + visual QR | Page-level fingerprints | 200ms ✅ |
| **Video** | FFmpeg metadata injection | SHA-256 + metadata hash | 100-500ms ✅ |
| **Audio** | ID3v2/Vorbis metadata | SHA-256 + MFCC (dev) | 50-200ms ✅ |

---

## Production-Ready Features

✅ **Minimal Overhead:** 50-100ms for text watermarking  
✅ **GPU Acceleration:** 10-20x speedup for images/video  
✅ **Async Processing:** High-throughput batch operations  
✅ **RESTful API:** Standard HTTP verification endpoints  
✅ **Vault Integration:** Persistent evidence storage  
✅ **Cryptographic Signatures:** Optional RSA/ECDSA signing  
✅ **Merkle Tree Batching:** Blockchain-ready anchoring  
✅ **Video Support:** FFmpeg metadata watermarking (production-ready)  
✅ **Audio Support:** Metadata watermarking + forensic fingerprinting (beta)  

---

## Regulatory Compliance

| Regulation | Requirement | CIAF Feature |
|------------|-------------|--------------|
| **EU AI Act** | Provenance tracking | Cryptographic evidence records |
| **California AB 2013** | AI content labeling | Visible watermarks + verification API |
| **China Deep Synthesis** | Traceable attribution | Persistent watermark IDs + removal detection |
| **NIST AI RMF** | Transparency & accountability | Audit trails, tamper detection |

---

## Licensing: Business Source License 1.1

**Current Status (until Jan 1, 2029):**
- ✅ Source code publicly available
- ✅ Free for research, academic, personal use
- ✅ 90-day evaluation period for commercial testing
- ❌ Production commercial use requires license

**Post-Change Date (Jan 1, 2029):**
- Automatically converts to **Apache License 2.0**
- Fully open source

**Commercial Licensing:** founder@cognitiveinsight.ai

---

## Technical Specifications

**Programming Language:** Python 3.8+  
**Core Dependencies:** Pydantic (data models)  
**Optional Dependencies:** Pillow (images), PyPDF (PDFs), ffmpeg-python (video), opencv-python (visual), librosa + soundfile (audio)  
**System Requirements:** FFmpeg 7.0+ binary (Windows/Linux/macOS)  
**Storage:** 2-8 KB per evidence record (text), ~200 KB (images with patches)  
**Latency:** 50-100ms (text), 20-50ms (images/GPU), 100-500ms (video metadata), 50-200ms (audio)  
**Throughput:** 450 text artifacts/sec, 720 images/sec (GPU), 100-200 video/sec (metadata mode)  

---

## Integration Example

```python
from ciaf_watermarks import watermark_ai_output

# Generate AI content
ai_output = model.generate("Explain quantum computing")

# Watermark + create forensic evidence
evidence, watermarked_content = watermark_ai_output(
    artifact=ai_output,
    model_id="gpt-4",
    model_version="2026-03",
    actor_id="user:alice",
    prompt="Explain quantum computing"
)

# Later: Verify suspect content
from ciaf_watermarks.text import verify_text_artifact

result = verify_text_artifact(suspect_text, evidence)

print(f"Authentic: {result.is_authentic()}")
print(f"Confidence: {result.confidence:.1%}")
print(f"Watermark Present: {result.watermark_present}")
print(f"Likely Removed: {result.likely_tag_removed}")
```

---

## Use Cases

**Content Platforms:**
- Detect unauthorized AI-generated spam
- Enforce attribution policies
- Comply with AI labeling laws

**Enterprise AI:**
- Audit trail for AI-generated reports
- Prevent plagiarism of AI content
- Track document provenance

**Legal & Compliance:**
- Cryptographic proof for litigation
- Regulatory compliance documentation
- Non-repudiation of AI generation

**Research & Academia:**
- Prevent AI-generated paper mills
- Citation tracking for AI contributions
- Dataset provenance verification

---

## Performance Benchmarks

| Operation | Duration | Configuration |
|-----------|----------|---------------|
| Text watermark (1KB) | 8ms | Single-threaded CPU |
| Text watermark (10KB) | 65ms | With forensic fragments |
| Image watermark (1024×1024) | 22ms | GPU acceleration (RTX 4090) |
| Video watermark (30s 1080p) | 380ms | GPU acceleration |
| Tier 1 verification | 2ms | Hash comparison only |
| Tier 2 verification (10KB text) | 15ms | Fragment matching |

**Throughput (8-worker async pool):**
- Text: 450 artifacts/sec
- Images (GPU): 720 artifacts/sec
- PDFs: 45 artifacts/sec

---

## Security Model

**Cryptographic Foundation:**
- SHA-256 for all hash operations (FIPS 180-4 compliant)
- Collision probability: 10^-154 for 2-of-3 fragment match
- Optional RSA/ECDSA signatures for non-repudiation

**Attack Resistance:**
- **Copy-paste:** Detected via watermark removal alerts
- **Partial editing:** Fragments provide 90%+ confidence with 2/3 match
- **Mix-and-match:** Spatial/temporal diversity in fragment selection
- **Forgery:** Entropy-based sampling prevents generic fragment collisions

---

## Comparison to Alternatives

| Feature | Traditional Watermarks | C2PA | SynthID | CIAF |
|---------|----------------------|------|---------|------|
| Removal detection | ❌ | ⚠️ Limited | ❌ | ✅ Strong |
| Multi-tier verification | ❌ | ❌ | ⚠️ Binary | ✅ 3 tiers |
| Fragment-based matching | ❌ | ❌ | ❌ | ✅ Yes |
| Multi-modal support | ⚠️ Limited | ✅ Yes | ⚠️ Images only | ✅ Yes |
| Open source (future) | N/A | ✅ Yes | ❌ Proprietary | ✅ After 2029 |

---

## Getting Started

**Installation:**
```bash
pip install ciaf-watermarks
```

**Documentation:**
- Full Whitepaper: [CIAF_TECHNICAL_WHITEPAPER.md](CIAF_TECHNICAL_WHITEPAPER.md)
- Schema Reference: [SCHEMA.md](SCHEMA.md)
- Quick Start: [README.md](README.md)

**Repository:** https://github.com/DenzilGreenwood/ciaf-watermarking  
**PyPI Package:** https://pypi.org/project/ciaf-watermarks/  
**Commercial Inquiries:** founder@cognitiveinsight.ai  

---

**Document Version:** 1.4.0  
**Last Updated:** April 7, 2026  
**License:** Business Source License 1.1  
**© 2025-2026 Cognitive Insight. All rights reserved.**
