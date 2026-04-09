# Gemini + CIAF Quick Reference

## 5-Minute Integration

### 1. Install
```bash
pip install ciaf-watermarks google-generativeai
export GEMINI_API_KEY="your-key-here"
```

### 2. Basic Usage Pattern
```python
import google.generativeai as genai
from ciaf_watermarks import watermark_ai_output

# Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')  # Latest recommended model

# Generate content
gemini_response = model.generate_content("Explain AI watermarking")
gemini_text = gemini_response.text

# Watermark it
evidence, watermarked_text = watermark_ai_output(
    artifact=gemini_text,
    model_id="gemini-1.5-flash",
    model_version="1.5",
    actor_id="user:your-app",
    prompt="Explain AI watermarking",
    verification_base_url="https://verify.yourapp.com"
)

# Save evidence
with open(f"evidence/{evidence.artifact_id}.json", "w") as f:
    f.write(evidence.to_json())

# Return to user
print(watermarked_text)
```

### 3. Verification Later
```python
from ciaf_watermarks.text import verify_text_artifact
from ciaf_watermarks.models import ArtifactEvidence
import json

# Load evidence
with open("evidence/{artifact_id}.json", "r") as f:
    evidence = ArtifactEvidence(**json.load(f))

# Verify suspect text
result = verify_text_artifact(suspect_text, evidence)

print(f"Authentic: {result.is_authentic}")
print(f"Confidence: {result.confidence}")
print(f"Method: {result.verification_method}")
```

---

## Key Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `artifact` | ✅ | Gemini's output (text or bytes) | `gemini_response.text` |
| `model_id` | ✅ | Which model generated it | `"gemini-pro"` |
| `model_version` | ✅ | Model version | `"1.5"` or `"2024-03"` |
| `actor_id` | ✅ | Who requested generation | `"user:analyst@company.com"` |
| `prompt` | ✅ | User's input prompt | Full prompt or hash |
| `verification_base_url` | ❌ | Verification endpoint | `"https://verify.app.com"` |
| `artifact_type` | ❌ | Type (None = auto-detect) | `ArtifactType.TEXT` |
| `watermark_config` | ❌ | Style overrides | `{"text": {"style": "header"}}` |
| `enable_forensic_fragments` | ❌ | DNA sampling (default True) | `True` |
| `store_in_vault` | ❌ | Auto-save to MongoDB | `False` |

---

## Watermark Styles

### Text Artifacts
```python
# Footer (default)
watermark_config = {"text": {"style": "footer"}}
# Output: "Content...\n\n---\nAI Provenance Tag: wmk-abc123..."

# Header
watermark_config = {"text": {"style": "header"}}
# Output: "---\nAI Generated Content...\n---\nContent..."

# Inline
watermark_config = {"text": {"style": "inline"}}
# Output: Content with embedded marker
```

### Image Artifacts
```python
# Visual watermark
watermark_config = {
    "image": {
        "mode": "visual",
        "opacity": 0.4,
        "position": "bottom_right"
    }
}

# QR code
watermark_config = {
    "image": {
        "include_qr": True,
        "qr_position": "top_right"
    }
}
```

---

## Common Workflows

### Workflow 1: Chat Application
```
1. User sends message → Gemini generates response
2. Watermark response text
3. Save evidence to JSON/DB
4. Return watermarked text to user
5. Display with optional verification link
```

### Workflow 2: Document Generator
```
1. User requests report → Gemini generates long-form content
2. Watermark complete document
3. Evidence includes multiple forensic fragments
4. Save as PDF or text file
5. Provide verification for authenticity
```

### Workflow 3: Batch Processing
```
1. Collect N user requests
2. Generate all with Gemini (parallel)
3. Watermark all outputs (parallel)
4. Save evidence batch
5. Return all watermarked results
```

### Workflow 4: API Service
```
Endpoint: POST /generate
Input: {"prompt": "...", "user_id": "..."}
Process:
  - Call Gemini
  - Watermark output
  - Store evidence
  - Return: {"content": watermarked, "watermark_id": "..."}

Endpoint: POST /verify
Input: {"content": "...", "watermark_id": "..."}
Process:
  - Load evidence by watermark_id
  - Verify content
  - Return: {"authentic": true, "confidence": 0.99}
```

---

## Evidence Object Structure

```json
{
  "artifact_id": "art-e3b0c442...",
  "watermark_id": "wmk-a8f5e2d1...",
  "artifact_type": "TEXT",
  "hash_before": "sha256:original_content_hash",
  "hash_after": "sha256:watermarked_content_hash",
  "forensic_fragments": [
    {
      "fragment_id": "frag_1",
      "fragment_type": "text",
      "position": "beginning",
      "fragment_hash": "sha256:..."
    }
  ],
  "fingerprints": [
    {
      "algorithm": "simhash",
      "value": "abc123...",
      "role": "perceptual"
    }
  ],
  "metadata": {
    "model_id": "gemini-pro",
    "model_version": "1.5",
    "actor_id": "user:analyst",
    "prompt": "Explain AI...",
    "timestamp": "2026-04-06T12:00:00Z"
  },
  "watermark": {
    "watermark_id": "wmk-a8f5e2d1...",
    "watermark_type": "VISIBLE_TEXT",
    "verification_url": "https://verify.app.com/wmk-a8f5e2d1"
  }
}
```

---

## Verification Tiers

| Tier | Method | Speed | Use Case |
|------|--------|-------|----------|
| **Tier 1** | Exact hash match | Fastest (~1ms) | Unchanged content |
| **Tier 2** | Forensic fragments | Fast (~10ms) | Minor edits detected |
| **Tier 3** | Perceptual similarity | Slower (~100ms) | Heavy modifications |

### Interpretation
- **Confidence 1.0**: Perfect match (Tier 1)
- **Confidence 0.85-0.99**: High confidence (Tier 2 fragments matched)
- **Confidence 0.70-0.84**: Moderate (Tier 3 similarity)
- **Confidence <0.70**: Likely not authentic or heavily modified

---

## Configuration Setup

### One-Time Global Config
```python
from ciaf_watermarks import set_default_watermark_config

set_default_watermark_config({
    "verification_base_url": "https://verify.myapp.com",
    "store_in_vault": False,  # Set True if using MongoDB
    "enable_forensic_fragments": True,
    "text": {
        "style": "footer",
        "include_simhash": True
    }
})
```

### Per-Request Override
```python
evidence, watermarked = watermark_ai_output(
    artifact=gemini_text,
    # ... required params ...
    watermark_config={"text": {"style": "header"}}  # Override
)
```

---

## Error Handling

```python
import logging
from ciaf_watermarks import watermark_ai_output

try:
    # Generate with Gemini
    response = model.generate_content(prompt)
    
    if not response.text:
        raise ValueError("Empty Gemini response")
    
    # Watermark
    evidence, watermarked = watermark_ai_output(
        artifact=response.text,
        model_id="gemini-pro",
        model_version="1.5",
        actor_id=f"user:{user_id}",
        prompt=prompt
    )
    
    # Save evidence (with retry)
    try:
        save_evidence(evidence)
    except Exception as e:
        logging.error(f"Evidence save failed: {e}")
        # Queue for retry or continue
    
    return watermarked

except Exception as e:
    logging.error(f"Watermarking failed: {e}")
    # Decide: return unwatermarked content or error
    return response.text  # Graceful degradation
```

---

## Testing Checklist

- [ ] Test basic text watermarking
- [ ] Verify evidence JSON structure
- [ ] Test verification with same content (should pass)
- [ ] Test verification with modified content (should fail/lower confidence)
- [ ] Test with empty Gemini response
- [ ] Test with very long content (>10K chars)
- [ ] Test storage save/load
- [ ] Test concurrent watermarking requests
- [ ] Measure latency
- [ ] Test error handling

---

## Quick Decisions

### Storage: JSON or MongoDB?
- **JSON**: Simple, local, good for <10K artifacts
- **MongoDB**: Scalable, searchable, production-ready

### Watermark Visibility: Visible or Hidden?
- **Visible**: User sees provenance tag (transparency)
- **Hidden**: Invisible, detected via forensic analysis

### When to Verify?
- **On upload**: User submits content claiming AI origin
- **On demand**: User clicks "Verify authenticity"
- **Automated**: Batch scan for watermarked content

### Async or Sync?
- **Sync**: Watermark before returning to user (adds <100ms)
- **Async**: Return quickly, watermark in background (complex)

---

## Example Integration Points

### Chat API (FastAPI)
```python
@app.post("/chat")
async def chat(request: ChatRequest):
    # Gemini
    response = model.generate_content(request.message)
    
    # Watermark
    evidence, watermarked = watermark_ai_output(
        artifact=response.text,
        model_id="gemini-pro",
        model_version="1.5",
        actor_id=f"user:{request.user_id}",
        prompt=request.message
    )
    
    # Save
    save_evidence(evidence)
    
    return {
        "response": watermarked,
        "watermark_id": evidence.watermark_id
    }
```

### CLI Tool
```bash
# Generate
python gemini_watermark.py generate \
  --prompt "Explain quantum computing" \
  --model gemini-pro \
  --user analyst@company.com \
  --output response.txt

# Verify
python gemini_watermark.py verify \
  --file suspect.txt \
  --watermark-id wmk-abc123
```

---

## Resources

- **Package docs**: ciaf-watermarking/README.md
- **Full guide**: examples/gemini/IMPLEMENTATION_GUIDE.md
- **API reference**: ciaf_watermarks.unified_interface module
- **Gemini docs**: https://ai.google.dev/docs

---

## Get Help

1. Check troubleshooting in IMPLEMENTATION_GUIDE.md
2. Review error messages and stack traces
3. Test with minimal example first
4. Verify all required parameters provided
5. Check evidence JSON structure if storage fails

**Start simple, iterate, scale!**
