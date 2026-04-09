# Gemini + CIAF Watermarking - Complete Examples Index

**🎯 Quick Navigation | 📚 All 8 Examples | ⏱️ Estimated Total: ~2-3 hours to complete all**

---

## 📖 Table of Contents

| # | Example | Type | Difficulty | Time | Status |
|---|---------|------|------------|------|--------|
| 1 | [Basic Text Watermarking](#1-basic-text-watermarking) | Text | ⭐ Beginner | 5-10 min | ✅ Complete |
| 2 | [Chat Conversation](#2-chat-conversation) | Text | ⭐⭐ Intermediate | 15-20 min | ✅ Complete |
| 3 | [Streaming Response](#3-streaming-response) | Text | ⭐⭐ Intermediate | 10-15 min | ✅ Complete |
| 4 | [Batch Processing](#4-batch-processing) | Text | ⭐⭐⭐ Advanced | 30-60 min | ✅ Complete |
| 5 | [Verification](#5-verification) | All | ⭐⭐ Intermediate | 5-10 min | ✅ Complete |
| 6 | [Image Watermarking](#6-image-watermarking) | Image | ⭐⭐ Intermediate | 10-15 min | ✅ Complete |
| 7 | [Video Watermarking](#7-video-watermarking) | Video | ⭐⭐⭐ Advanced | 20-40 min | ✅ Complete |
| 8 | [Audio Watermarking](#8-audio-watermarking) | Audio | ⭐⭐⭐ Advanced | 10-20 min | ✅ Complete |

---

## 🚀 Getting Started

### Prerequisites (All Examples)

```bash
# 1. Install core package
pip install ciaf-watermarks google-generativeai

# 2. Set API key
export GEMINI_API_KEY="your-api-key-here"

# 3. Optional: Install additional dependencies as needed
```

### Learning Path Recommendation

**🟢 Beginners:** Start here
1. Run Example 1 (Basic Text)
2. Run Example 5 (Verification)
3. Run Example 2 (Chat)

**🟡 Intermediate:** Ready for more
4. Run Example 3 (Streaming)
5. Run Example 6 (Images)
6. Run Example 8 (Audio)

**🔴 Advanced:** Full capabilities
7. Run Example 4 (Batch)
8. Run Example 7 (Video)

---

## 📋 Detailed Example Descriptions

### 1. Basic Text Watermarking
**File:** `01_basic_text_watermarking.py`  
**Difficulty:** ⭐ Beginner  
**Time:** 5-10 minutes  
**API Calls:** 1 Gemini request  

**What you'll learn:**
- ✅ How to watermark AI-generated text
- ✅ Forensic fragment selection (DNA sampling)
- ✅ Evidence record structure
- ✅ Hash-based verification (Tier 1)
- ✅ Testing with modified content

**Output files:**
```
outputs/gemini_basic/<artifact_id>/
├── 01_original.txt          - Raw Gemini output
├── 02_watermarked.txt       - With footer watermark
├── 03_evidence.json         - Forensic evidence
└── 04_modified.txt          - Test case (edited)
```

**Run it:**
```bash
python 01_basic_text_watermarking.py
```

**Key Concepts:**
- Dual-state hashing (before/after watermark)
- Forensic fragment selection
- Evidence persistence

---

### 2. Chat Conversation
**File:** `02_chat_conversation.py`  
**Difficulty:** ⭐⭐ Intermediate  
**Time:** 15-20 minutes  
**API Calls:** 3 Gemini requests (3-turn conversation)  

**What you'll learn:**
- ✅ Multi-turn conversation watermarking
- ✅ Context preservation across turns
- ✅ Conversation-level evidence records
- ✅ Individual turn verification
- ✅ Conversation reconstruction

**Output files:**
```
outputs/gemini_conversation/<conversation_id>/
├── turn_01_original.txt
├── turn_01_watermarked.txt
├── turn_01_evidence.json
├── turn_02_original.txt
├── ...
└── conversation_summary.json
```

**Run it:**
```bash
python 02_chat_conversation.py
```

**Key Concepts:**
- Conversation tracking
- Multi-artifact evidence chains
- Context management

---

### 3. Streaming Response
**File:** `03_streaming_response.py`  
**Difficulty:** ⭐⭐ Intermediate  
**Time:** 10-15 minutes  
**API Calls:** 1 Gemini streaming request  

**What you'll learn:**
- ✅ Real-time streaming with Gemini
- ✅ Progressive display while accumulating
- ✅ Watermarking complete streamed output
- ✅ UX optimization patterns
- ✅ Production streaming architecture

**Output files:**
```
outputs/gemini_streaming/<artifact_id>/
├── 01_original.txt
├── 02_watermarked.txt
└── 03_evidence.json
```

**Run it:**
```bash
python 03_streaming_response.py
```

**Key Concepts:**
- Streaming vs. batch generation
- Response accumulation
- Watermark deferral until complete

---

### 4. Batch Processing
**File:** `04_batch_processing.py`  
**Difficulty:** ⭐⭐⭐ Advanced  
**Time:** 30-60 minutes  
**API Calls:** 10+ Gemini requests (configurable)  

**What you'll learn:**
- ✅ High-volume content generation
- ✅ Parallel watermarking
- ✅ Error handling and retries
- ✅ Batch evidence management
- ✅ Success rate tracking
- ✅ Summary reports

**Output files:**
```
outputs/gemini_batch/batch_<timestamp>/
├── prompt_001_original.txt
├── prompt_001_watermarked.txt
├── prompt_001_evidence.json
├── prompt_002_original.txt
├── ...
└── batch_summary.json
```

**Run it:**
```bash
python 04_batch_processing.py
```

**Key Concepts:**
- Production pipelines
- Batch optimization
- Evidence aggregation

---

### 5. Verification
**File:** `05_verification.py`  
**Difficulty:** ⭐⭐ Intermediate  
**Time:** 5-10 minutes  
**API Calls:** 0 (uses existing evidence)  

**What you'll learn:**
- ✅ Three-tier verification system
- ✅ Tier 1: Exact hash matching (100% confidence)
- ✅ Tier 2: Forensic fragment matching (90-95%)
- ✅ Tier 3: Perceptual similarity (0-90%)
- ✅ Watermark removal detection
- ✅ Confidence scoring

**Prerequisites:**
- Run Example 1 first (creates evidence)

**Output files:**
- Uses evidence from Example 1
- No new files created

**Run it:**
```bash
# First run Example 1
python 01_basic_text_watermarking.py

# Then run verification
python 05_verification.py
```

**Key Concepts:**
- Multi-tier verification cascade
- Graduated confidence levels
- Forensic analysis

---

### 6. Image Watermarking
**File:** `06_image_watermarking.py`  
**Difficulty:** ⭐⭐ Intermediate  
**Time:** 10-15 minutes  
**API Calls:** 0 (generates synthetic image)  

**What you'll learn:**
- ✅ Visual watermark overlays
- ✅ QR code embedding for mobile verification
- ✅ Perceptual hashing (pHash)
- ✅ Tampering detection (crop, blur, text)
- ✅ Robust verification methods

**Dependencies:**
```bash
pip install Pillow qrcode
```

**Output files:**
```
outputs/gemini_image/<artifact_id>/
├── 01_original.png
├── 02_watermarked.png
├── 03_evidence.json
└── 04_modified.png
```

**Run it:**
```bash
python 06_image_watermarking.py
```

**Key Concepts:**
- Visual watermarking
- QR code integration
- Perceptual fingerprinting

---

### 7. Video Watermarking
**File:** `07_video_watermarking.py`  
**Difficulty:** ⭐⭐⭐ Advanced  
**Time:** 20-40 minutes  
**API Calls:** 0 (generates synthetic video)  

**What you'll learn:**
- ✅ Metadata watermarking (fast, lossless)
- ✅ Visual overlay watermarking (re-encode resistant)
- ✅ I-frame temporal fingerprinting
- ✅ Re-encoding tampering detection
- ✅ Format conversion resilience

**Dependencies:**
```bash
pip install ffmpeg-python opencv-python qrcode[pil] Pillow

# System requirement: FFmpeg installed
# Windows: Download from ffmpeg.org
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
```

**Output files:**
```
outputs/gemini_video/
├── 01_original.mp4
├── 02_watermarked_metadata.mp4
├── 03_evidence.json
├── 04_stripped_metadata.mp4
└── 05_watermarked_visual.mp4
```

**Run it:**
```bash
python 07_video_watermarking.py
```

**Key Concepts:**
- Video metadata injection
- Visual overlay encoding
- Temporal fingerprints

---

### 8. Audio Watermarking
**File:** `08_audio_watermarking.py`  
**Difficulty:** ⭐⭐⭐ Advanced  
**Time:** 10-20 minutes  
**API Calls:** 0 (generates synthetic audio)  

**What you'll learn:**
- ✅ Metadata watermarking (fast, lossless)
- ✅ Spectral watermarking (inaudible, robust)
- ✅ MFCC audio fingerprinting
- ✅ Re-encoding tampering detection
- ✅ Format conversion resilience

**Dependencies:**
```bash
pip install ffmpeg-python librosa soundfile numpy

# System requirement: FFmpeg installed
```

**Output files:**
```
outputs/gemini_audio/
├── 01_original.mp3
├── 02_watermarked_metadata.mp3
├── 03_evidence.json
├── 04_stripped_metadata.mp3
└── 05_watermarked_spectral.mp3
```

**Run it:**
```bash
python 08_audio_watermarking.py
```

**Key Concepts:**
- Audio metadata tags
- Spectral embedding
- MFCC fingerprints

---

## 🎯 Use Case Matrix

| Use Case | Recommended Examples | Reason |
|----------|---------------------|--------|
| **Chatbot Development** | 2, 3, 5 | Conversation tracking + streaming + verification |
| **Content Pipeline** | 1, 4, 5 | Basic watermarking + batch processing + verification |
| **Image Generation** | 6 | Visual watermarking for AI art |
| **Video Synthesis** | 7 | Temporal fingerprinting for AI video |
| **Voice Cloning/TTS** | 8 | Spectral watermarking for AI audio |
| **Real-time Apps** | 3 | Streaming optimization |
| **Compliance** | All | Full audit trail across all modalities |

---

## 📊 Feature Comparison

| Feature | Text (1-5) | Image (6) | Video (7) | Audio (8) |
|---------|-----------|-----------|-----------|-----------|
| **Watermark Type** | Footer/Header | Visual Overlay | Metadata/Visual | Metadata/Spectral |
| **Speed** | 50-100ms | 200-500ms | 2-10s | 200-500ms |
| **Removal Resistance** | Low-Medium | High | Medium-High | Medium-High |
| **Format Resilience** | Medium | High (pHash) | Medium | High (MFCC) |
| **Verification Tiers** | 3 | 2 | 2 | 2 |
| **Storage Overhead** | 2-4 KB | 200 KB | 5-10 KB | 3-8 KB |
| **GPU Acceleration** | No | Optional | Yes | No |

---

## 🛠️ Troubleshooting

### Common Issues

**❌ Error: `ModuleNotFoundError: No module named 'google.generativeai'`**
```bash
pip install google-generativeai
```

**❌ Error: `Invalid API key`**
```bash
export GEMINI_API_KEY="your-actual-api-key"
# Get key: https://makersuite.google.com/app/apikey
```

**❌ Error: `FFmpeg not found` (Examples 7, 8)**
- Windows: Download from https://ffmpeg.org/download.html
- Linux: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`

**❌ Error: `Evidence file not found` (Example 5)**
- Run Example 1 first to generate evidence

**❌ Slow performance on video/audio**
- Reduce video duration in Example 7 (default: 5s)
- Reduce audio duration in Example 8 (default: 5s)
- Use GPU acceleration for video processing

---

## 📚 Additional Resources

- **Main Documentation:** [../../README.md](../../README.md)
- **Schema Reference:** [../../../SCHEMA.md](../../../SCHEMA.md)
- **Technical Whitepaper:** [../../../CIAF_TECHNICAL_WHITEPAPER.md](../../../CIAF_TECHNICAL_WHITEPAPER.md)
- **Quick Reference:** [../../../QUICK_REFERENCE.md](../../../QUICK_REFERENCE.md)

---

## 🤝 Contributing

Found a bug or have a suggestion? Please:
1. Check existing issues
2. Create a new issue with detailed description
3. Submit PR with fix/improvement

**Repository:** https://github.com/DenzilGreenwood/ciaf-watermarking

---

## 📝 License

Business Source License 1.1 (BUSL-1.1)  
See [LICENSE](../../../LICENSE) for details

---

**Last Updated:** April 7, 2026  
**Version:** 1.4.0  
**Examples Status:** 8/8 Complete ✅
