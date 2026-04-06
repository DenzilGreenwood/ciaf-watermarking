# CIAF Watermarking - Quick Schema Reference

**For Developer Reference** - See [SCHEMA.md](SCHEMA.md) for complete documentation.

---

## Essential Field Names

### **IDs** (Always Required)
```python
artifact_id: str        # UUID v4
watermark_id: str       # "wmk-{uuid}"
fragment_id: str        # "frag_{index}_{location}"
```

### **Hashes** (Always SHA-256, 64-char hex, lowercase)
```python
content_hash_before_watermark: str
content_hash_after_watermark: str
prompt_hash: str
output_hash_raw: str           # Same as content_hash_before_watermark
output_hash_distributed: str   # Same as content_hash_after_watermark
```

### **Provenance** (Always Required)
```python
model_id: str           # "gpt-4", "claude-3", etc.
model_version: str      # "2026-03", "1.5", etc.
actor_id: str           # "user:{name}", "system:{service}"
```

### **Timestamps** (Always ISO 8601 UTC)
```python
created_at: str         # "2026-04-06T10:30:00Z"
signed_at: str          # "2026-04-06T10:30:00Z"
```

### **Scores** (Always 0.0-1.0 float)
```python
entropy_score: float
confidence: float
match_confidence: float
```

---

## Quick Code Examples

### Creating Evidence

```python
from ciaf.watermarks import build_text_artifact_evidence

evidence, watermarked = build_text_artifact_evidence(
    raw_text="AI content",
    prompt="Generate summary",
    verification_base_url="https://vault.example.com",
    model_id="gpt-4",
    model_version="2026-03",
    actor_id="user:alice",
    enable_forensic_fragments=True  # DNA sampling
)
```

### Validating Evidence

```python
from ciaf.watermarks import validate_artifact_evidence, generate_compliance_report

# Quick validation
errors = validate_artifact_evidence(evidence)
if errors:
    print(f"Validation errors: {errors}")

# Full compliance report
report = generate_compliance_report(evidence)
print(f"Compliant: {report['is_compliant']}")
print(f"Checks: {report['checks']}")
```

### Batch Validation

```python
from ciaf.watermarks import validate_evidence_batch

results = validate_evidence_batch([evidence1, evidence2, evidence3])
print(f"Valid: {results['valid']} / {results['total']}")
print(f"Errors: {results['errors']}")
```

---

## Common Patterns

### ✅ DO Use These Patterns

```python
# IDs
artifact_id = str(uuid.uuid4())
watermark_id = f"wmk-{uuid.uuid4()}"
fragment_id = f"frag_{index}_{location}"

# Timestamps
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat()

# Hashes
from ciaf.watermarks import sha256_text, sha256_bytes
content_hash = sha256_text(text)
content_hash = sha256_bytes(data)
```

### ❌ DON'T Use These Anti-Patterns

```python
# ❌ Sequential IDs
artifact_id = f"artifact_{counter}"

# ❌ Local timestamps
timestamp = datetime.now().isoformat()

# ❌ Wrong hash format
content_hash = hashlib.md5(data).hexdigest()  # Use SHA-256!

# ❌ Missing dual-state hashes
hashes = {"content_hash": sha256(data)}  # Need BOTH before AND after!
```

---

## Field Cheat Sheet

| Field | Required? | Type | Format |
|-------|-----------|------|--------|
| `artifact_id` | ✅ Yes | str | UUID v4 (36 chars) |
| `watermark_id` | ✅ Yes | str | `wmk-{uuid}` |
| `content_hash_before_watermark` | ✅ Yes | str | SHA-256 (64 hex) |
| `content_hash_after_watermark` | ✅ Yes | str | SHA-256 (64 hex) |
| `model_id` | ✅ Yes | str | 1-100 chars |
| `model_version` | ✅ Yes | str | 1-50 chars |
| `actor_id` | ✅ Yes | str | 1-200 chars |
| `created_at` | ✅ Yes | str | ISO 8601 UTC |
| `forensic_fragments` | ⚠️ Conditional | ForensicFragmentSet | If enabled |
| `signature` | ⚠️ Conditional | SignatureEnvelope | Production only |
| `metadata` | ❌ Optional | Dict | Any JSON-serializable |
| `prior_receipt_hash` | ❌ Optional | str | SHA-256 (64 hex) |

---

## Validation Checklist

Before storing evidence:

- [ ] `artifact_id` is valid UUID v4
- [ ] `watermark_id` starts with `wmk-`
- [ ] Both `content_hash_before_watermark` and `content_hash_after_watermark` present
- [ ] All hashes are 64-character hex strings
- [ ] `created_at` is ISO 8601 UTC format
- [ ] `model_id`, `model_version`, `actor_id` are non-empty
- [ ] If fragments enabled: `fragment_id` follows `frag_{n}_{location}` pattern
- [ ] All confidence/entropy scores are 0.0-1.0
- [ ] `forensic_fragments.fragment_count` matches actual count

---

## Quick Validation

```bash
# Run validation script
python -c "
from ciaf.watermarks import validate_artifact_evidence, ArtifactEvidence
import json

# Load evidence
with open('evidence.json') as f:
    data = json.load(f)
evidence = ArtifactEvidence(**data)

# Validate
errors = validate_artifact_evidence(evidence)
print('✓ Valid' if not errors else f'✗ Errors: {errors}')
"
```

---

## Import Quick Reference

```python
# Validation functions
from ciaf.watermarks import (
    validate_artifact_evidence,      # Main validator
    validate_evidence_batch,          # Batch validator
    generate_compliance_report,       # Full report
)

# Field validators
from ciaf.watermarks import (
    validate_artifact_id,
    validate_watermark_id,
    validate_fragment_id,
    validate_sha256_hash,
    validate_iso8601_timestamp,
    validate_confidence_score,
    validate_entropy_score,
)

# Evidence builders
from ciaf.watermarks import (
    build_text_artifact_evidence,
    build_image_artifact_evidence,
    build_audio_artifact_evidence,
    build_video_artifact_evidence,
)
```

---

## Need More Details?

See [SCHEMA.md](SCHEMA.md) for:
- Complete field specifications
- All data models
- Detailed validation rules
- Migration guides
- Best practices

---

**Last Updated:** 2026-04-06  
**Version:** 1.4.0
