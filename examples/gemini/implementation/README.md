# Gemini + CIAF Watermarking Implementation Examples

Practical, runnable examples demonstrating Google Gemini integration with CIAF watermarking.

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install ciaf-watermarks google-generativeai

# Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Get your API key at: https://makersuite.google.com/app/apikey
```

### Run Your First Example

```bash
python 01_basic_text_watermarking.py
```

## 📚 Examples Overview

### 1️⃣ **Basic Text Watermarking** (`01_basic_text_watermarking.py`)
**Perfect for:** Getting started, understanding the basics

**What it does:**
- Generates text with Gemini
- Applies watermark with forensic fragments
- Saves evidence to JSON
- Verifies authenticity
- Tests with modified content

**Estimated runtime:** 5-10 seconds

```bash
python 01_basic_text_watermarking.py
```

**Key concepts:** Basic integration, evidence storage, verification

---

### 2️⃣ **Chat Conversation** (`02_chat_conversation.py`)
**Perfect for:** Chatbots, interactive applications

**What it does:**
- Multi-turn conversation with Gemini
- Watermarks each response separately
- Tracks conversation context
- Saves conversation history with evidence
- Verifies entire conversation

**Estimated runtime:** 15-20 seconds

```bash
python 02_chat_conversation.py
```

**Key concepts:** Conversation tracking, multi-turn watermarking, context preservation

---

### 3️⃣ **Streaming Response** (`03_streaming_response.py`)
**Perfect for:** Real-time UX, long-form content

**What it does:**
- Streams content from Gemini in real-time
- Displays chunks as they arrive
- Accumulates complete response
- Watermarks final output
- Demonstrates streaming + watermarking pattern

**Estimated runtime:** 10-15 seconds

```bash
python 03_streaming_response.py
```

**Key concepts:** Streaming API, response accumulation, UX optimization

---

### 4️⃣ **Batch Processing** (`04_batch_processing.py`)
**Perfect for:** Bulk generation, content pipelines

**What it does:**
- Processes multiple prompts efficiently
- Watermarks all outputs in batch
- Tracks success/failure rates
- Saves organized evidence files
- Generates batch summary report

**Estimated runtime:** 30-60 seconds

```bash
python 04_batch_processing.py
```

**Key concepts:** Batch operations, parallel processing, error handling

---

### 5️⃣ **Verification** (`05_verification.py`)
**Perfect for:** Content verification, authenticity checking

**What it does:**
- Demonstrates all 3 verification tiers
- Tests exact matches (Tier 1)
- Tests modified content (Tier 2)
- Tests paraphrased content (Tier 3)
- Detects fake/non-authentic content
- Shows confidence scoring

**Estimated runtime:** 2-5 seconds

```bash
python 05_verification.py
```

**Note:** Requires evidence from example 01 first

**Key concepts:** Multi-tier verification, forensic detection, confidence thresholds

---

### 6️⃣ **Image Watermarking** (`06_image_watermarking.py`)
**Perfect for:** AI-generated images, art, visual content

**What it does:**
- Generates or loads AI-generated images
- Applies visual watermark with transparency
- Embeds QR code for mobile verification
- Uses perceptual hashing (robust to edits)
- Tests tampering detection (crop, blur, text)
- Saves all artifacts (original, watermarked, evidence, modified)

**Estimated runtime:** 5-10 seconds

```bash
python 06_image_watermarking.py
```

**Output:** Saves 4 files in `outputs/gemini_image/<artifact_id>/`:
- `01_original.png` - AI-generated image
- `02_watermarked.png` - With visual watermark + QR code
- `03_evidence.json` - Forensic evidence record
- `04_modified.png` - Tampered version for testing

**Key concepts:** Visual watermarking, QR codes, perceptual hashing, tampering detection

**Requirements:**
```bash
pip install Pillow qrcode
```

---

### 7️⃣ **Video Watermarking** (`07_video_watermarking.py`)
**Perfect for:** AI-generated videos, video synthesis, animations

**What it does:**
- Generates or loads AI-generated videos
- Applies metadata watermark (fast, no re-encoding)
- Applies visual watermark overlay with QR code
- Uses temporal fingerprinting (I-frame sampling)
- Tests tampering detection (re-encoding, metadata stripping)
- Saves all artifacts (original, watermarked, evidence, stripped)

**Estimated runtime:** 20-40 seconds (depends on video length)

```bash
python 07_video_watermarking.py
```

**Output:** Saves files in `outputs/gemini_video/`:
- `01_original.mp4` - AI-generated video (simulated)
- `02_watermarked_metadata.mp4` - With metadata watermark
- `03_evidence.json` - Forensic evidence record
- `04_stripped_metadata.mp4` - Tampered version (metadata removed)
- `05_watermarked_visual.mp4` - With visual overlay + QR code (optional)

**Key concepts:** Video metadata, visual overlays, I-frame fingerprinting, re-encode resistance

**Requirements:**
```bash
pip install ffmpeg-python opencv-python qrcode[pil] Pillow

# Also requires FFmpeg installed on system:
# Windows: Download from ffmpeg.org
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
```

---

### 8️⃣ **Audio Watermarking** (`08_audio_watermarking.py`)
**Perfect for:** AI voice cloning, TTS, AI music generation

**What it does:**
- Generates or loads AI-generated audio
- Applies metadata watermark (fast, no re-encoding)
- Applies spectral watermark (inaudible, re-encode resistant)
- Uses audio fingerprinting (MFCC-based)
- Tests tampering detection (re-encoding, metadata stripping)
- Saves all artifacts (original, watermarked, evidence, stripped)

**Estimated runtime:** 10-20 seconds

```bash
python 08_audio_watermarking.py
```

**Output:** Saves files in `outputs/gemini_audio/`:
- `01_original.mp3` (or `.wav`) - AI-generated audio (simulated)
- `02_watermarked_metadata.mp3` - With metadata watermark
- `03_evidence.json` - Forensic evidence record
- `04_stripped_metadata.mp3` - Tampered version (metadata removed)
- `05_watermarked_spectral.mp3` - With spectral watermark (optional)

**Key concepts:** Audio metadata, spectral watermarking, MFCC fingerprints, inaudible watermarks

**Requirements:**
```bash
pip install ffmpeg-python librosa soundfile numpy

# Also requires FFmpeg installed on system
```

---

## 🎯 Use Case Guide

### For Chatbots
→ Start with `02_chat_conversation.py`
→ Add `03_streaming_response.py` for better UX
→ Use `05_verification.py` for moderation

### For Content Generation
→ Start with `01_basic_text_watermarking.py`
→ Scale with `04_batch_processing.py`
→ Verify with `05_verification.py`

### For Image Generation (AI Art, DALL-E, Stable Diffusion, Gemini Imagen)
→ Start with `06_image_watermarking.py`
→ Understand visual watermarking + QR codes
→ Test tampering detection capabilities

### For Video Generation (Veo, Sora, Runway, Pika)
→ Start with `07_video_watermarking.py`
→ Compare metadata vs. visual watermarking
→ Understand I-frame fingerprinting

### For Audio Generation (Voice Cloning, TTS, Music AI)
→ Start with `08_audio_watermarking.py`
→ Compare metadata vs. spectral watermarking
→ Understand MFCC fingerprints

### For Real-Time Applications
→ Focus on `03_streaming_response.py`
→ Monitor with `05_verification.py`

### For Bulk Operations
→ Use `04_batch_processing.py`
→ Verify batches with `05_verification.py`

---

## 📁 Generated Files

After running the examples, you'll find:

```
outputs/
├── gemini_basic/                  # Basic text examples
│   └── <artifact_id>/
│       ├── 01_original.txt
│       ├── 02_watermarked.txt
│       ├── 03_evidence.json
│       └── 04_modified.txt
├── gemini_conversation/           # Chat conversations
│   └── <conversation_id>/
│       ├── turn_01_original.txt
│       ├── turn_01_watermarked.txt
│       ├── turn_01_evidence.json
│       └── ...
├── gemini_image/                  # Image watermarking
│   └── <artifact_id>/
│       ├── 01_original.png
│       ├── 02_watermarked.png
│       ├── 03_evidence.json
│       └── 04_modified.png
├── gemini_video/                  # Video watermarking
│   ├── 01_original.mp4
│   ├── 02_watermarked_metadata.mp4
│   ├── 03_evidence.json
│   ├── 04_stripped_metadata.mp4
│   └── 05_watermarked_visual.mp4
├── gemini_audio/                  # Audio watermarking
│   ├── 01_original.mp3
│   ├── 02_watermarked_metadata.mp3
│   ├── 03_evidence.json
│   ├── 04_stripped_metadata.mp3
│   └── 05_watermarked_spectral.mp3
└── gemini_streaming/              # Streaming responses
    └── <artifact_id>/
        ├── 01_original.txt
        ├── 02_watermarked.txt
        ├── 03_evidence.json
        └── 04_modified.txt

evidence/                          # Legacy evidence directory
├── <artifact_id>.json             # Individual evidence files
├── conversations/                 # Chat conversation evidence
│   ├── conv_<timestamp>_turn1.json
│   ├── conv_<timestamp>_turn2.json
│   └── conv_<timestamp>_summary.json
└── batch/                         # Batch processing results
    └── batch_<timestamp>/
        ├── prompt_1_evidence.json
        ├── prompt_1_output.txt
        ├── ...
        └── batch_summary.json
```

**Note:** Examples now save complete artifacts (original, watermarked, evidence, modified) 
for comprehensive documentation and testing.

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
export GEMINI_API_KEY="your-key-here"

# Optional
export VERIFICATION_URL="https://verify.yourapp.com"
export EVIDENCE_DIR="./custom_evidence_path"
```

### Customizing Watermark Style

Edit the `watermark_config` parameter in any example:

```python
watermark_config = {
    "text": {
        "style": "footer",  # Options: "footer", "header", "inline"
        "include_simhash": True
    }
}

evidence, watermarked = watermark_ai_output(
    artifact=gemini_text,
    # ...
    watermark_config=watermark_config
)
```

### Using MongoDB Storage

```python
from ciaf_watermarks import watermark_ai_output

evidence, watermarked = watermark_ai_output(
    artifact=gemini_text,
    # ...
    store_in_vault=True  # Auto-save to MongoDB
)
```

**Note:** Requires MongoDB setup. See `../config_template.py` for configuration.

---

## 🚦 API Rate Limits

**Gemini API Free Tier:**
- 60 requests per minute
- 1,500 requests per day

**Tips:**
- Use `time.sleep()` between batch requests
- Implement exponential backoff for retries
- Monitor your quota at: https://console.cloud.google.com

---

## 🐛 Troubleshooting

### "GEMINI_API_KEY not set"
```bash
export GEMINI_API_KEY="your-key-here"
# Or add to ~/.bashrc or ~/.zshrc
```

### "Resource exhausted" error
- You've hit API rate limits
- Wait a minute or reduce batch size
- Consider upgrading to paid tier

### "Evidence file not found"
- Run `01_basic_text_watermarking.py` first
- Check that `evidence/` directory exists
- Verify file permissions

### Watermark not visible
- Check `watermark_config` style setting
- Ensure you're displaying the watermarked output, not original
- Some styles are less visible (e.g., "inline")

---

## 📊 Performance Benchmarks

| Operation | Time |
|-----------|------|
| Gemini API call | 2-5 seconds |
| Watermarking | 50-100 ms |
| Evidence save | 5-10 ms |
| Verification | 10-20 ms |

**Overhead:** Watermarking adds < 5% latency to Gemini calls

---

## 🎓 Learning Path

```
1. Start    → 01_basic_text_watermarking.py
              Understand: watermarking flow, evidence structure

2. Interact → 02_chat_conversation.py
              Understand: multi-turn tracking, conversation context

3. Stream   → 03_streaming_response.py
              Understand: UX optimization, streaming patterns

4. Scale    → 04_batch_processing.py
              Understand: bulk operations, error handling

5. Verify   → 05_verification.py
              Understand: detection tiers, confidence scoring

6. Images   → 06_image_watermarking.py
              Understand: visual watermarks, QR codes, perceptual hashing
```

---

## 🔐 Security Best Practices

1. **Store Evidence Securely**
   - Use encrypted storage for production
   - Consider MongoDB with authentication
   - Back up evidence regularly

2. **Protect API Keys**
   - Never commit API keys to git
   - Use environment variables
   - Rotate keys periodically

3. **Validate Inputs**
   - Sanitize user prompts
   - Check content for PII before storing
   - Hash sensitive prompts

4. **Monitor Usage**
   - Track API quota consumption
   - Log all watermarking operations
   - Alert on verification failures

---

## 🚀 Production Deployment

### Checklist

- [ ] Set up MongoDB or cloud storage for evidence
- [ ] Configure verification endpoint/URL
- [ ] Implement error handling and retries
- [ ] Add logging and monitoring
- [ ] Set up rate limiting
- [ ] Configure backup strategy
- [ ] Test verification across all tiers
- [ ] Document API endpoints
- [ ] Create user documentation

### Example API Structure

```python
# api/generate.py
@app.post("/generate")
async def generate_content(prompt: str, user_id: str):
    # Generate with Gemini
    response = model.generate_content(prompt)

    # Watermark
    evidence, watermarked = watermark_ai_output(
        artifact=response.text,
        model_id="gemini-pro",
        model_version="1.5",
        actor_id=f"user:{user_id}",
        prompt=prompt,
        store_in_vault=True
    )

    return {
        "content": watermarked,
        "watermark_id": evidence.watermark_id
    }

# api/verify.py
@app.post("/verify")
async def verify_content(text: str, watermark_id: str):
    # Load evidence
    evidence = load_evidence(watermark_id)

    # Verify
    result = verify_text_artifact(text, evidence)

    return {
        "is_authentic": result.is_authentic,
        "confidence": result.confidence,
        "tier": result.details.get("tier")
    }
```

---

## 💡 Tips & Tricks

### Tip 1: Invisible Watermarks
Use "inline" style for less intrusive watermarks:
```python
watermark_config={"text": {"style": "inline"}}
```

### Tip 2: Batch with Progress Bar
```python
from tqdm import tqdm
for prompt in tqdm(prompts, desc="Processing"):
    # ... watermark ...
```

### Tip 3: Async Processing
```python
import asyncio
results = await asyncio.gather(*[
    process_prompt_async(p) for p in prompts
])
```

### Tip 4: Cache Frequently Used Prompts
```python
from functools import lru_cache
@lru_cache(maxsize=100)
def get_watermarked_response(prompt):
    # ... (cache by prompt hash)
```

---

## 🤝 Contributing

Found a bug or have an improvement?

1. Create an issue describing the problem
2. Submit a PR with your fix
3. Add tests if applicable
4. Update documentation

---

## 📖 Additional Resources

### Documentation
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - 5-minute guide
- [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) - Complete reference
- [config_template.py](../config_template.py) - Configuration options

### Related Examples
- `examples/openai/` - OpenAI integration examples
- Main CIAF docs - Core watermarking concepts

### External Links
- [Gemini API Docs](https://ai.google.dev/docs)
- [CIAF Watermarking Package](https://pypi.org/project/ciaf-watermarks/)
- [Google AI Studio](https://makersuite.google.com/)

---

## 📝 License

Same as the ciaf-watermarking package. Check the main repository LICENSE file.

---

## ❓ Questions?

- Check the [troubleshooting section](#-troubleshooting)
- Review the [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md)
- Open an issue in the main repository

---

**Ready to build?** Start with `01_basic_text_watermarking.py`!

```bash
export GEMINI_API_KEY="your-key-here"
python 01_basic_text_watermarking.py
```
