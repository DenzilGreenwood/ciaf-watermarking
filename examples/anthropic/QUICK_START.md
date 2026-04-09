# Anthropic + CIAF Watermarking - Quick Reference

## 🚀 30-Second Start

```bash
# 1. Install
pip install anthropic ciaf-watermarks

# 2. Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# 3. Run
python 01_basic_text_watermarking.py
```

---

## 📚 All Examples at a Glance

### 1️⃣ Basic Text Watermarking
**File:** [01_basic_text_watermarking.py](01_basic_text_watermarking.py)  
**Time:** 2 minutes  
**Learns:** Generate → Watermark → Verify

```python
# The core pattern
response = client.messages.create(...)
evidence, watermarked = watermark_ai_output(artifact=response.content[0].text, ...)
result = verify_text_artifact(watermarked, evidence)
```

---

### 2️⃣ Chat Conversation
**File:** [02_chat_conversation.py](02_chat_conversation.py)  
**Time:** 5 minutes  
**Learns:** Multi-turn conversations, state tracking

```python
# Watermark each turn
for user_input in conversation:
    response = client.messages.create(...)
    evidence, watermarked = watermark_ai_output(...)
    conversation_history.append({"role": "assistant", "content": watermarked})
```

---

### 3️⃣ Watermark Styles
**File:** [03_watermark_styles.py](03_watermark_styles.py)  
**Time:** 3 minutes  
**Learns:** Footer vs Header vs Inline styles

| Style | Visibility | Best For |
|-------|-----------|----------|
| Footer | 🔵🔵🔵 | Public content |
| Header | 🔵🔵🔵 | Legal documents |
| Inline | 🔵 | Chat messages |

---

### 4️⃣ REST API (FastAPI)
**File:** [04_fastapi_api.py](04_fastapi_api.py)  
**Time:** 10 minutes  
**Learns:** Production-ready API, endpoints, error handling

```bash
python 04_fastapi_api.py
# Visit: http://localhost:8000/docs
```

---

## 🎯 Choose Your Path

### Path A: "I just want to try it"
1. Run `01_basic_text_watermarking.py`
2. Done! ✅

### Path B: "I'm building a chatbot"
1. Run `01_basic_text_watermarking.py` (understand basics)
2. Run `02_chat_conversation.py` (see multi-turn)
3. Run `03_watermark_styles.py` (choose inline style)
4. Integrate into your chatbot! 🤖

### Path C: "I'm building an API"
1. Run `01_basic_text_watermarking.py` (understand basics)
2. Run `04_fastapi_api.py` (see API structure)
3. Copy and customize for your API! 🚀

### Path D: "I want to understand everything"
1. Read [README.md](README.md) (full documentation)
2. Run all examples in order
3. Explore [config.py](config.py) (configuration helper)
4. Customize for your use case! 🎓

---

## 💡 Common Code Patterns

### Pattern: Single Request

```python
from anthropic import Anthropic
from ciaf_watermarks import watermark_ai_output

client = Anthropic()
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=200,
    messages=[{"role": "user", "content": "Your prompt"}]
)

evidence, watermarked = watermark_ai_output(
    artifact=response.content[0].text,
    model_id="claude-3-sonnet-20240229",
    model_version="2024-02",
    actor_id="user:alice",
    prompt="Your prompt",
    enable_forensic_fragments=True
)

print(watermarked)  # Return this to user
```

### Pattern: Verification

```python
from ciaf_watermarks.text import verify_text_artifact

# Load evidence (saved earlier)
with open("evidence/art-abc123.json") as f:
    evidence_data = json.load(f)
evidence = ArtifactEvidence(**evidence_data)

# Verify content
result = verify_text_artifact(content, evidence)
print(f"Authentic: {result.is_authentic}")
print(f"Confidence: {result.confidence}")
```

---

## 🔧 Configuration Cheat Sheet

### Claude Models

```python
# Most capable (best quality, expensive)
model = "claude-3-opus-20240229"

# Balanced (recommended for most use cases)
model = "claude-3-sonnet-20240229"

# Fastest (cost-effective)
model = "claude-3-haiku-20240307"
```

### Using config.py Helper

```python
from config import get_anthropic_client, get_full_config

# Get configured client
client = get_anthropic_client()

# Get complete config for watermark_ai_output()
config = get_full_config(
    user_id="alice@example.com",
    prompt="Your prompt",
    style="footer"  # or "header", "inline"
)

evidence, watermarked = watermark_ai_output(
    artifact=text,
    **config  # Unpack all config
)
```

### Manual Configuration

```python
evidence, watermarked = watermark_ai_output(
    artifact=text,
    model_id="claude-3-sonnet-20240229",
    model_version="2024-02",
    actor_id="user:alice",
    prompt="Your prompt",
    watermark_config={
        "text": {
            "style": "footer",  # footer, header, inline
            "include_timestamp": True,
            "include_model_info": True
        }
    },
    enable_forensic_fragments=True
)
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| `ANTHROPIC_API_KEY not set` | `export ANTHROPIC_API_KEY="sk-ant-..."`  |
| `No module named 'anthropic'` | `pip install anthropic ciaf-watermarks` |
| `Evidence file not found` | Run the generation script first |
| `Verification failed` | Content was likely modified |
| `FastAPI not found` | `pip install fastapi uvicorn` |

---

## 📖 Full Documentation

See [README.md](README.md) for:
- Detailed example explanations
- Complete API reference
- Security best practices
- Advanced patterns
- Troubleshooting guide

---

## 🎓 Learning Resources

- **CIAF Watermarks Docs:** [GitHub](https://github.com/DenzilGreenwood/ciaf-watermarking)
- **Anthropic API Docs:** https://docs.anthropic.com/
- **Claude Models:** https://docs.anthropic.com/claude/docs/models-overview
- **FastAPI Tutorial:** https://fastapi.tiangolo.com/tutorial/

---

**Ready to watermark? Start with `01_basic_text_watermarking.py`! 🚀**
