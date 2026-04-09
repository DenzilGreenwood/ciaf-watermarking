# Example Outputs Structure

All examples save comprehensive outputs for documentation and testing purposes.

## Directory Structure

```
outputs/
├── gemini_basic/
│   └── {artifact_id}/
│       ├── 01_original.txt      # Raw Gemini output
│       ├── 02_watermarked.txt   # With CIAF watermark
│       ├── 03_evidence.json     # Forensic evidence record
│       └── 04_modified.txt      # Test tampering/modifications
│
├── openai_basic/
│   └── {artifact_id}/
│       ├── 01_original.txt      # Raw OpenAI output
│       ├── 02_watermarked.txt   # With CIAF watermark
│       ├── 03_evidence.json     # Forensic evidence record
│       └── 04_modified.txt      # Test tampering/modifications
│
├── anthropic_basic/
│   └── {artifact_id}/
│       ├── 01_original.txt      # Raw Claude output
│       ├── 02_watermarked.txt   # With CIAF watermark
│       ├── 03_evidence.json     # Forensic evidence record
│       └── 04_modified.txt      # Test tampering/modifications
│
├── gemini_conversation/
│   └── {conversation_id}/
│       ├── turn_01_original.txt
│       ├── turn_01_watermarked.txt
│       ├── turn_01_evidence.json
│       ├── turn_02_original.txt
│       ├── turn_02_watermarked.txt
│       ├── turn_02_evidence.json
│       └── conversation_summary.json
│
├── image_watermarking/
│   └── {artifact_id}/
│       ├── 01_original.png      # Generated image
│       ├── 02_watermarked.png   # With visual/steganographic watermark
│       ├── 03_evidence.json     # Forensic evidence
│       ├── 04_qr_overlay.png    # QR code version (if applicable)
│       └── 05_modified.png      # Test image modification
│
├── video_watermarking/
│   └── {artifact_id}/
│       ├── 01_original.mp4      # Generated video
│       ├── 02_watermarked.mp4   # With temporal watermark
│       ├── 03_evidence.json     # Forensic evidence
│       ├── 04_keyframes/        # Extracted keyframes
│       └── 05_modified.mp4      # Test video modification
│
└── audio_watermarking/
    └── {artifact_id}/
        ├── 01_original.wav      # Generated audio
        ├── 02_watermarked.wav   # With spectral watermark
        ├── 03_evidence.json     # Forensic evidence
        ├── 04_spectrogram.png   # Visual representation
        └── 05_modified.wav      # Test audio modification
```

## File Types

### Text Files

**01_original.txt**
- Raw AI model output
- No watermarking applied
- Original hash stored in evidence

**02_watermarked.txt**
- Contains visible watermark (footer/header/inline)
- Includes forensic fragments
- Verification URL included

**03_evidence.json**
- Complete forensic record
- Hashes (before/after watermark)
- Forensic fragment locations
- Model metadata
- Actor information
- Signature envelope

**04_modified.txt**
- Test case for tampering detection
- Shows how verification handles modifications
- Used to demonstrate confidence scoring

### Image Files

**01_original.png/jpg**
- Generated image from AI model
- Pixel-level hash calculated
- Perceptual hash stored

**02_watermarked.png/jpg**
- Visual watermark overlay OR
- Steganographic embedding OR
- QR code watermark
- Maintains image quality

**03_evidence.json**
- Image fingerprints
- Spatial fragment locations
- High-entropy patch hashes
- Model and generation metadata

**04_qr_overlay.png** (if applicable)
- QR code version for easy verification
- Scannable with standard QR readers
- Links to verification portal

**05_modified.png**
- Test image with alterations
- Cropping, filters, compression tests
- Demonstrates robustness

### Video Files

**01_original.mp4**
- Generated video content
- Frame-by-frame metadata
- Audio track (if applicable)

**02_watermarked.mp4**
- Temporal watermarks embedded
- Keyframe fingerprints
- Optional visual overlay

**03_evidence.json**
- Video metadata
- Keyframe hashes
- Temporal fragment positions
- Motion signatures

**04_keyframes/**
- Extracted frames for verification
- Critical scene fingerprints
- Used for similarity matching

**05_modified.mp4**
- Test edits (cuts, speed changes, filters)
- Frame insertion/deletion tests
- Compression artifact simulation

### Audio Files

**01_original.wav/mp3**
- Generated audio content
- High-fidelity recording
- Waveform metadata

**02_watermarked.wav/mp3**
- Spectral watermark embedded
- Imperceptible to human ear
- Robust to format conversion

**03_evidence.json**
- Audio fingerprints
- Spectral hashes
- Temporal segment locations
- Generation parameters

**04_spectrogram.png**
- Visual representation
- Shows watermark embedding (if visible)
- Analysis tool for verification

**05_modified.wav**
- Test modifications
- Pitch shift, tempo change, noise addition
- Format conversion tests

## Evidence JSON Structure

Each `evidence.json` file contains:

```json
{
  "artifact_id": "unique-identifier",
  "artifact_type": "text|image|video|audio|pdf|binary",
  "mime_type": "text/plain|image/png|video/mp4|audio/wav",
  "created_at": "ISO 8601 timestamp",
  "model_id": "gemini-1.5-flash",
  "model_version": "1.5",
  "actor_id": "user:demo",
  "prompt_hash": "sha256-hash-of-input",
  "output_hash_raw": "hash-before-watermark",
  "output_hash_distributed": "hash-after-watermark",
  "watermark": {
    "watermark_id": "wmk-unique-id",
    "watermark_type": "visible|metadata|embedded|hybrid",
    "tag_text": "Human-readable tag",
    "verification_url": "https://verify.example.com/...",
    "embed_method": "footer_append_v1|steganography|spectral",
    "removal_resistance": "low|medium|high"
  },
  "hashes": {
    "content_hash_before_watermark": "sha256-hash",
    "content_hash_after_watermark": "sha256-hash",
    "normalized_hash_before": "normalized-hash",
    "normalized_hash_after": "normalized-hash",
    "simhash_before": "simhash-value",
    "simhash_after": "simhash-value",
    "forensic_fragments": {
      "fragment_count": 5,
      "sampling_strategy": "multi_point",
      "text_fragments": [...],
      "image_fragments": [...],
      "video_snippets": [...],
      "audio_segments": [...]
    }
  },
  "fingerprints": [
    {
      "algorithm": "simhash",
      "value": "hash-value",
      "role": "exact_content_before_watermark"
    }
  ],
  "metadata": {
    "distribution_state": "watermarked",
    "artifact_format_version": "1.0",
    "text_length_before": 1234,
    "text_length_after": 1456
  }
}
```

## Usage

### Viewing Outputs

```bash
# Text examples
cat outputs/gemini_basic/{artifact_id}/02_watermarked.txt

# View evidence
cat outputs/gemini_basic/{artifact_id}/03_evidence.json | jq

# Compare original and watermarked
diff outputs/gemini_basic/{artifact_id}/01_original.txt \
     outputs/gemini_basic/{artifact_id}/02_watermarked.txt
```

### Image Examples

```bash
# View images
open outputs/image_watermarking/{artifact_id}/02_watermarked.png

# Compare images
compare outputs/image_watermarking/{artifact_id}/01_original.png \
        outputs/image_watermarking/{artifact_id}/02_watermarked.png \
        diff.png
```

### Verification Testing

```python
from ciaf_watermarks.models import ArtifactEvidence
from ciaf_watermarks.text import verify_text_artifact
import json

# Load evidence
with open("outputs/gemini_basic/{artifact_id}/03_evidence.json") as f:
    evidence_data = json.load(f)
evidence = ArtifactEvidence(**evidence_data)

# Load watermarked content
with open("outputs/gemini_basic/{artifact_id}/02_watermarked.txt") as f:
    watermarked_text = f.read()

# Verify
result = verify_text_artifact(watermarked_text, evidence)
print(f"Authentic: {result.is_authentic()}")
print(f"Confidence: {result.confidence:.2%}")
```

## Cleanup

Outputs are saved for documentation and testing. To clean up:

```bash
# Remove all outputs
rm -rf outputs/

# Remove specific example outputs
rm -rf outputs/gemini_basic/

# Keep evidence, remove content
find outputs/ -name "*.txt" -delete
find outputs/ -name "*.png" -delete
find outputs/ -name "*.mp4" -delete
find outputs/ -name "*.wav" -delete
```

## Git Ignore

Outputs are typically git-ignored to avoid repository bloat:

```gitignore
# Example outputs
outputs/
**/01_original.*
**/02_watermarked.*
**/04_modified.*
**/05_modified.*

# Keep evidence for testing
!**/03_evidence.json
```

## Best Practices

1. **Review outputs regularly** - Verify watermarks are working
2. **Check file sizes** - Ensure watermarks don't bloat files
3. **Test modifications** - Always run tampering tests
4. **Archive important evidence** - Keep evidence.json for audits
5. **Document anomalies** - Note any unexpected behavior

## Support

For issues with output generation or structure:
- Check example code for proper output directory creation
- Verify file permissions
- Ensure sufficient disk space
- Review evidence.json for errors
