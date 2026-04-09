# Gemini + CIAF Watermarking Implementation Guide

## Overview
This guide shows how to integrate Google Gemini with ciaf-watermarking using the **unified interface** for transparent AI content provenance.

---

## Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Gemini    │         │  Your            │         │  CIAF           │
│   API       │────────▶│  Application     │────────▶│  Watermarking   │
│             │ output  │                  │ unified │  Package        │
└─────────────┘         └──────────────────┘         └─────────────────┘
                              │                              │
                              │                              ▼
                              │                     ┌─────────────────┐
                              │                     │  Evidence       │
                              │                     │  Storage        │
                              │                     │  (JSON/Vault)   │
                              │                     └─────────────────┘
                              │                              │
                              ▼                              │
                        ┌────────────────┐◀─────────────────┘
                        │  Watermarked   │   verification
                        │  Output to     │   flow
                        │  User          │
                        └────────────────┘
```

---

## Core API: `watermark_ai_output()`

### What It Does
Single function that:
1. **Auto-detects** artifact type (text, image, PDF, etc.)
2. **Applies** appropriate watermarking strategy
3. **Generates** forensic evidence (hashes, DNA fragments)
4. **Returns** both evidence and watermarked content

### Function Signature
```python
from ciaf_watermarks import watermark_ai_output

evidence, watermarked_artifact = watermark_ai_output(
    artifact=<gemini_output>,           # Auto-detects: text or bytes
    model_id="gemini-pro",              # Which Gemini model
    model_version="1.5",                # Model version
    actor_id="user:email@example.com",  # Who made the request
    prompt="<user's prompt>",           # Original prompt
    verification_base_url="https://...", # Where to verify (optional)
    artifact_type=None,                  # None = auto-detect
    watermark_config=None,               # Type-specific settings
    enable_forensic_fragments=True,      # DNA sampling for verification
    store_in_vault=False                 # Auto-store in MongoDB (optional)
)
```

### Return Values
- **`evidence`**: `ArtifactEvidence` object containing:
  - `artifact_id`: Unique identifier
  - `watermark_id`: Watermark identifier
  - `artifact_type`: Detected type (TEXT, IMAGE, etc.)
  - `hash_before`: SHA-256 of original content
  - `hash_after`: SHA-256 of watermarked content
  - `forensic_fragments`: DNA samples for verification
  - `fingerprints`: Perceptual hashes (for similarity matching)
  - `metadata`: Model info, timestamp, etc.

- **`watermarked_artifact`**: Same type as input (str or bytes)

---

## Basic Example Flow

### Step 1: Setup
```
Requirements:
- pip install ciaf-watermarks
- pip install google-generativeai
- GEMINI_API_KEY environment variable
```

### Step 2: Generate with Gemini
```
Input: User prompt → "Explain quantum computing"
Process: Call Gemini API
Output: Text response from Gemini
```

### Step 3: Watermark Output
```
Input: Gemini's text response
Process: watermark_ai_output(artifact=gemini_text, ...)
Output: (evidence, watermarked_text)
```

### Step 4: Store Evidence
```
Option A: Save to JSON file
  - evidence.to_json() → save to disk
  
Option B: Store in MongoDB vault
  - Set store_in_vault=True
  - Or manually: vault_adapter.store_evidence(evidence)
```

### Step 5: Return to User
```
Return: watermarked_text (with visible footer or embedded marker)
User sees: Content + provenance tag
```

### Step 6: Verification (Later)
```
Input: Suspect text
Process: verify_text_artifact(suspect_text, evidence)
Output: VerificationResult with confidence score
```

---

## Configuration Options

### Global Config (Set Once)
```python
from ciaf_watermarks import set_default_watermark_config

set_default_watermark_config({
    "verification_base_url": "https://vault.mycompany.com",
    "store_in_vault": True,
    "enable_forensic_fragments": True,
    "text": {
        "style": "footer",          # "footer", "header", "inline"
        "include_simhash": True     # For similarity matching
    },
    "image": {
        "mode": "visual",           # "visual" or "qr"
        "opacity": 0.4,
        "position": "bottom_right",
        "include_qr": True
    }
})
```

### Per-Request Config (Override)
```python
custom_config = {
    "text": {
        "style": "header",  # Override default
    }
}

evidence, watermarked = watermark_ai_output(
    artifact=gemini_output,
    # ... other params ...
    watermark_config=custom_config
)
```

---

## Example Scenarios

### Scenario 1: Text Generation (Article, Email, Summary)
**Gemini Model**: `gemini-pro`
**Output Type**: Text string
**Watermark Strategy**: Footer with provenance tag
**Evidence**: SHA-256 hash + 3 text fragments (DNA)
**Use Case**: Blog posts, reports, emails

### Scenario 2: Code Generation
**Gemini Model**: `gemini-pro`
**Output Type**: Text (code)
**Watermark Strategy**: Comment block at top/bottom
**Evidence**: Hash of code + fragments
**Use Case**: Generated functions, scripts, configs

### Scenario 3: Multi-modal (Text + Image Description)
**Gemini Model**: `gemini-pro-vision` hypothetically
**Output Type**: Text (if image analysis) or bytes (if image gen)
**Watermark Strategy**: Auto-detected by type
**Evidence**: Separate evidence records if multiple outputs
**Use Case**: Image captioning, visual Q&A

### Scenario 4: Long-form Content
**Gemini Model**: `gemini-1.5-pro`
**Output Type**: Text (multi-page document)
**Watermark Strategy**: Footer + forensic fragments from multiple sections
**Evidence**: Multiple DNA samples across document
**Use Case**: Research reports, documentation

---

## Key Integration Points

### 1. Capture Gemini Metadata
Track these from your Gemini API call:
- Model name (`gemini-pro`, `gemini-1.5-pro`)
- Generation config (temperature, top_p, top_k)
- Safety settings applied
- Generation timestamp
- Token count

Store in `watermark_ai_output()` via:
- `model_id`: Gemini model name
- `model_version`: Version or date
- `prompt`: User's input prompt
- Can extend with additional metadata dict

### 2. Handle Different Response Types
```
Gemini responses can be:
- Text string → watermark_ai_output() auto-detects as TEXT
- Image bytes → auto-detects as IMAGE (if Gemini generates images)
- Error/empty → Handle before watermarking
```

### 3. Error Handling Flow
```
Try:
  1. Call Gemini API
  2. Check response validity
  3. Watermark output
  4. Save evidence
Catch:
  - Gemini API errors → Log, return error to user
  - Watermarking errors → Log, optionally return unwatermarked content
  - Storage errors → Continue, queue retry
```

### 4. Verification Endpoint
```
Create API endpoint: POST /verify
Input: { "artifact": "suspected text...", "watermark_id": "wmk-..." }
Process:
  1. Load evidence from storage using watermark_id
  2. Call verify_text_artifact(artifact, evidence)
  3. Return VerificationResult
Output: { "is_authentic": true, "confidence": 0.99, "tier": "TIER1_EXACT" }
```

---

## File Structure Recommendation

```
your_project/
├── gemini_integration/
│   ├── __init__.py
│   ├── watermarking.py          # Wrapper around watermark_ai_output()
│   ├── verification.py          # Verification logic
│   └── config.py                # Configuration management
├── storage/
│   ├── evidence_store.py        # JSON or MongoDB storage
│   └── evidence/                # JSON files (if not using vault)
├── api/
│   ├── generate_endpoint.py     # POST /generate (Gemini + watermark)
│   └── verify_endpoint.py       # POST /verify
└── examples/
    ├── basic_chat.py             # Simple chatbot example
    ├── document_generator.py     # Long-form content
    └── batch_processing.py       # Multiple requests
```

---

## Implementation Checklist

### Phase 1: Basic Integration
- [ ] Install dependencies (`ciaf-watermarks`, `google-generativeai`)
- [ ] Set up Gemini API credentials
- [ ] Create wrapper function for `watermark_ai_output()`
- [ ] Test with simple text prompt
- [ ] Verify evidence JSON structure
- [ ] Test verification with same content

### Phase 2: Configuration
- [ ] Define watermark styles (footer/header)
- [ ] Set up global config with `set_default_watermark_config()`
- [ ] Configure verification URL (or local storage path)
- [ ] Test different artifact types (if using multi-modal)

### Phase 3: Storage
- [ ] Choose storage: JSON files or MongoDB vault
- [ ] Implement evidence save/load functions
- [ ] Add error handling for storage failures
- [ ] Test evidence retrieval by watermark_id

### Phase 4: Verification
- [ ] Create verification function
- [ ] Test Tier 1 (exact match)
- [ ] Test Tier 2 (fragment matching)
- [ ] Test Tier 3 (similarity/perceptual)
- [ ] Handle "not authentic" cases

### Phase 5: Production Readiness
- [ ] Add logging for all watermarking operations
- [ ] Implement retry logic for transient failures
- [ ] Add metrics/monitoring
- [ ] Set up rate limiting (if needed)
- [ ] Create API documentation
- [ ] Write unit tests

---

## Common Patterns

### Pattern 1: Simple Synchronous Flow
```
Flow: User request → Gemini → Watermark → Response → Evidence saved
Latency: Gemini time + watermark time (~<100ms)
Best for: Real-time chat, interactive apps
```

### Pattern 2: Async Evidence Generation
```
Flow: User request → Gemini → Quick watermark → Response
      Background job → Full evidence + fragments → Save
Latency: Reduced user-facing latency
Best for: High-throughput APIs, batch processing
```

### Pattern 3: Batch Watermarking
```
Flow: Collect N Gemini outputs → Watermark all → Save evidence batch
Benefit: Amortize overhead across multiple requests
Best for: Report generation, bulk content creation
```

### Pattern 4: Stream + Watermark
```
Flow: Gemini streaming response → Accumulate → Watermark complete output
Alternative: Watermark each chunk (less common)
Best for: Long-form content, user experience
```

---

## Testing Strategy

### Unit Tests
- Test `watermark_ai_output()` with mock Gemini responses
- Test evidence serialization/deserialization
- Test verification with known artifacts
- Test error handling

### Integration Tests
- Real Gemini API call → watermark → verify round-trip
- Test all supported artifact types
- Test evidence storage and retrieval
- Test verification across tiers

### Load Tests
- Measure watermarking latency under load
- Test concurrent requests
- Monitor memory usage with many evidences
- Test storage system limits

---

## Security Considerations

### 1. Evidence Integrity
- Evidence contains cryptographic hashes (SHA-256)
- Forensic fragments provide DNA-level verification
- Perceptual hashes detect alterations

### 2. Privacy
- Hash prompts if they contain PII
- Store evidence securely (encrypted storage)
- Consider GDPR compliance for actor_id

### 3. Watermark Resistance
- Text watermarks can be manually removed
- Forensic fragments detect removal attempts
- Perceptual matching catches paraphrasing

### 4. API Security
- Authenticate verification requests
- Rate limit to prevent abuse
- Validate watermark_id format
- Sanitize inputs before verification

---

## Troubleshooting

### Issue: "TypeError: artifact must be str or bytes"
- Check Gemini response format
- Ensure you're passing raw content, not wrapper object

### Issue: Text watermark not visible
- Check `style` config ("footer", "header", "inline")
- Verify watermark wasn't stripped before display

### Issue: Verification returns low confidence
- Content may have been modified
- Check which tier is matching (1/2/3)
- Review forensic fragments

### Issue: Storage errors with MongoDB
- Verify `store_in_vault=True` and vault configured
- Check MongoDB connection string
- Ensure WatermarkVault initialized

---

## Next Steps

1. **Start Simple**: Single Gemini call → watermark → print result
2. **Add Storage**: Save evidence to JSON file
3. **Test Verification**: Load evidence → verify same content
4. **Build API**: Create endpoints for generate + verify
5. **Scale**: Add async processing, batching, monitoring

---

## Resources

### CIAF Watermarking Package
- Main interface: `ciaf_watermarks.unified_interface`
- Text verification: `ciaf_watermarks.text.verification`
- Models: `ciaf_watermarks.models`
- Vault storage: `ciaf_watermarks.vault_adapter`

### Gemini API
- Documentation: https://ai.google.dev/docs
- Python SDK: `google-generativeai`
- Models: gemini-pro, gemini-1.5-pro, etc.

### Example Code Structure
```
See examples/ folder for:
- Basic text watermarking
- Batch processing
- Verification flows
- API integration patterns
```

---

## Questions for Your Implementation

1. **Which Gemini model(s)** will you use?
   - gemini-pro (text)
   - gemini-pro-vision (multi-modal)
   - gemini-1.5-pro (long context)

2. **Storage preference**?
   - JSON files (simple, local)
   - MongoDB (scalable, production)
   - S3/Cloud (distributed)

3. **Watermark visibility**?
   - Visible footer (default)
   - Embedded/invisible (requires fragments)
   - User-selectable

4. **Verification strategy**?
   - API endpoint
   - CLI tool
   - Web interface

5. **Integration point**?
   - Live chat application
   - Batch document generation
   - API wrapper service
   - Other?

---

**Ready to implement!** Use this guide as a reference while building in your separate folder.
