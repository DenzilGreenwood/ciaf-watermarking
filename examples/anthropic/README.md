# Anthropic + CIAF Watermarking Integration Examples

Complete, production-ready examples showing how to integrate **ciaf-watermarks** with **Anthropic's Claude** API.

## 📋 What's Included

| Example | Description | Complexity |
|---------|-------------|------------|
| [01_basic_text_watermarking.py](01_basic_text_watermarking.py) | Simple text generation with watermarking | ⭐ Beginner |
| [02_chat_conversation.py](02_chat_conversation.py) | Multi-turn chat with per-response watermarking | ⭐⭐ Intermediate |
| [03_watermark_styles.py](03_watermark_styles.py) | Different watermark styles (footer/header/inline) | ⭐⭐ Intermediate |
| [04_fastapi_api.py](04_fastapi_api.py) | Complete REST API with FastAPI | ⭐⭐⭐ Advanced |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Core dependencies
pip install anthropic ciaf-watermarks

# For API example
pip install fastapi uvicorn
```

### 2. Set Anthropic API Key

Get your API key from: https://console.anthropic.com/settings/keys

```bash
# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-..."

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run Any Example

```bash
# Basic text watermarking
python 01_basic_text_watermarking.py

# Chat conversation
python 02_chat_conversation.py

# Watermark styles comparison
python 03_watermark_styles.py

# FastAPI server
python 04_fastapi_api.py
# Then visit: http://localhost:8000/docs
```

---

## 📖 Example Details

### Example 1: Basic Text Watermarking

**What it demonstrates:**
- Anthropic Messages API
- `watermark_ai_output()` function
- Evidence saving to JSON
- Content verification
- Modified content detection

**Key code snippet:**
```python
from anthropic import Anthropic
from ciaf_watermarks import watermark_ai_output
from ciaf_watermarks.text import verify_text_artifact

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Generate content
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=200,
    messages=[{"role": "user", "content": "Explain AI"}]
)
original_text = response.content[0].text

# Watermark it
evidence, watermarked = watermark_ai_output(
    artifact=original_text,
    model_id="claude-3-sonnet-20240229",
    model_version="2024-02",
    actor_id="user:alice@example.com",
    prompt="Explain AI",
    enable_forensic_fragments=True
)

# Verify it
result = verify_text_artifact(watermarked, evidence)
print(f"Authentic: {result.is_authentic}")
```

**Output:**
- `evidence/basic/art-abc123.json` - Complete evidence record
- Console output showing verification results

---

### Example 2: Chat Conversation

**What it demonstrates:**
- Multi-turn conversations with Claude
- Per-response watermarking
- Conversation state tracking
- Evidence aggregation
- Inline watermark style (subtle for chat)

**Key code snippet:**
```python
conversation_history = []

for user_input in ["Tell me about AI", "How does it work?"]:
    # Add user message
    conversation_history.append({"role": "user", "content": user_input})
    
    # Get Claude response
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        messages=conversation_history
    )
    
    claude_message = response.content[0].text
    
    # Watermark it
    evidence, watermarked = watermark_ai_output(
        artifact=claude_message,
        model_id="claude-3-sonnet-20240229",
        model_version="2024-02",
        actor_id="user:alice",
        prompt=user_input,
        watermark_config={"text": {"style": "inline"}},  # Subtle
        enable_forensic_fragments=True
    )
    
    # Add watermarked response to history
    conversation_history.append({"role": "assistant", "content": watermarked})
```

**Output:**
- `evidence/conversation/turn_1_art-abc123.json` - Evidence per turn
- `evidence/conversation/conversation_summary.json` - Full conversation metadata

---

### Example 3: Watermark Styles

**What it demonstrates:**
- Three watermark styles: **footer**, **header**, **inline**
- Use case recommendations
- Size impact comparison
- Verification of all styles

**Styles:**

| Style | Visibility | Size Impact | Best For |
|-------|-----------|-------------|----------|
| **Footer** | High | ~600 bytes | Public content, blog posts |
| **Header** | High | ~600 bytes | Legal docs, reports |
| **Inline** | Low | ~400 bytes | Chat, social media |

**Key code snippet:**
```python
# Footer style (default)
evidence, watermarked = watermark_ai_output(
    artifact=text,
    model_id="claude-3-sonnet-20240229",
    model_version="2024-02",
    actor_id="user:alice",
    prompt="...",
    watermark_config={"text": {"style": "footer"}}
)

# Header style
evidence, watermarked = watermark_ai_output(
    # ... same params ...
    watermark_config={"text": {"style": "header"}}
)

# Inline style (subtle)
evidence, watermarked = watermark_ai_output(
    # ... same params ...
    watermark_config={"text": {"style": "inline"}}
)
```

---

### Example 4: FastAPI REST API

**What it demonstrates:**
- Production-ready REST API
- Three endpoints: `/generate`, `/verify`, `/evidence/{artifact_id}`
- Async request handling
- Error handling
- Evidence storage and retrieval

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| POST | `/generate` | Generate watermarked content |
| POST | `/verify` | Verify content authenticity |
| GET | `/evidence/{artifact_id}` | Retrieve evidence record |

**API Usage:**

```bash
# Generate content
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing",
    "user_id": "alice@example.com",
    "watermark_style": "footer",
    "model": "claude-3-sonnet-20240229"
  }'

# Response:
{
  "content": "Quantum computing is...\n\n[AI Generated Content]...",
  "watermark_id": "wmk-abc123",
  "artifact_id": "art-def456",
  "model": "claude-3-sonnet-20240229",
  "timestamp": "2024-01-15T10:30:00Z",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 120
  }
}

# Verify content
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Quantum computing is...",
    "watermark_id": "wmk-abc123"
  }'

# Response:
{
  "is_authentic": true,
  "confidence": 1.0,
  "verification_method": "forensic_fragment",
  "details": "Content verified successfully"
}

# Get evidence
curl http://localhost:8000/evidence/art-def456

# Response: Full evidence JSON
```

**Running the API:**

```bash
python 04_fastapi_api.py

# Visit these URLs:
# - API Docs (Swagger): http://localhost:8000/docs
# - Alternative Docs (ReDoc): http://localhost:8000/redoc
```

---

## 🔧 Configuration

### Available Claude Models

```python
# Most capable (expensive)
model = "claude-3-opus-20240229"

# Balanced (recommended)
model = "claude-3-sonnet-20240229"

# Fastest (cost-effective)
model = "claude-3-haiku-20240307"
```

### Using config.py Helper

Create a config module for reuse across examples:

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

## 📁 Directory Structure After Running

```
examples/anthropic/
├── 01_basic_text_watermarking.py
├── 02_chat_conversation.py
├── 03_watermark_styles.py
├── 04_fastapi_api.py
├── README.md  ← You are here
├── config.py
├── requirements.txt
├── .env.example
├── evidence/
│   ├── basic/
│   │   └── art-abc123def456.json
│   ├── conversation/
│   │   ├── turn_1_art-abc123.json
│   │   ├── turn_2_art-def456.json
│   │   └── conversation_summary.json
│   ├── styles/
│   │   ├── footer_art-abc123.json
│   │   ├── header_art-def456.json
│   │   └── inline_art-ghi789.json
│   └── api/
│       ├── art-abc123.json
│       └── art-def456.json
```

---

## 🎯 Common Patterns

### Pattern 1: Single Request Watermarking

```python
# 1. Generate with Claude
response = client.messages.create(...)
text = response.content[0].text

# 2. Watermark
evidence, watermarked = watermark_ai_output(artifact=text, ...)

# 3. Save evidence
with open(f"evidence/{evidence.artifact_id}.json", "w") as f:
    f.write(evidence.to_json())

# 4. Return watermarked content to user
return watermarked
```

### Pattern 2: Batch Processing

```python
prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
results = []

for prompt in prompts:
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    evidence, watermarked = watermark_ai_output(
        artifact=response.content[0].text,
        model_id="claude-3-sonnet-20240229",
        actor_id="batch-job",
        prompt=prompt
    )
    
    results.append({
        "prompt": prompt,
        "content": watermarked,
        "artifact_id": evidence.artifact_id
    })
```

### Pattern 3: Verification Pipeline

```python
def verify_content(content: str, watermark_id: str) -> bool:
    """Verify content authenticity."""
    
    # 1. Find evidence by watermark_id
    evidence = find_evidence_by_watermark_id(watermark_id)
    
    # 2. Verify
    result = verify_text_artifact(content, evidence)
    
    # 3. Return result
    return result.is_authentic
```

---

## 🛡️ Security Best Practices

### 1. Protect API Keys

```python
# ✅ Good: Use environment variables
api_key = os.environ.get("ANTHROPIC_API_KEY")

# ❌ Bad: Hardcode API keys
api_key = "sk-ant-abc123..."  # DON'T DO THIS
```

### 2. Validate User Input

```python
# FastAPI example
class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = Field(default=1024, le=4096)  # Limit tokens
    temperature: float = Field(default=1.0, ge=0.0, le=1.0)  # Validate range
```

### 3. Store Evidence Securely

```python
# Use secure directory permissions
import os
import stat

evidence_dir = "evidence"
os.makedirs(evidence_dir, exist_ok=True)
os.chmod(evidence_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # 0700
```

### 4. Rate Limiting (FastAPI)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/generate")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def generate_content(request: Request, ...):
    # ...
```

---

## 🐛 Troubleshooting

### Issue: "Anthropic API key not configured"

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
python 01_basic_text_watermarking.py
```

### Issue: "Evidence file not found"

**Solution:**
```python
# Ensure evidence directory exists
import os
os.makedirs("evidence/basic", exist_ok=True)
```

### Issue: "Watermark verification failed"

**Possible causes:**
1. Content was modified after watermarking
2. Evidence file doesn't match content
3. Wrong watermark_id provided

**Debug:**
```python
result = verify_text_artifact(content, evidence)
print(f"Verification method: {result.verification_method}")
print(f"Details: {result.details}")
```

---

## 📚 Additional Resources

- **ciaf-watermarks Documentation**: [GitHub Repository](https://github.com/DenzilGreenwood/ciaf-watermarking)
- **Anthropic API Reference**: https://docs.anthropic.com/claude/reference
- **Claude Models**: https://docs.anthropic.com/claude/docs/models-overview
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

---

## 💡 Next Steps

1. **Run the basic example** to understand the core workflow
2. **Experiment with different watermark styles** to see what fits your use case
3. **Try the chat conversation example** for multi-turn applications
4. **Deploy the FastAPI example** to production with proper authentication and rate limiting

---

## 📝 License

These examples are provided under the same license as ciaf-watermarks (MIT).

---

## 🤝 Contributing

Found a bug or have an improvement? Please open an issue or submit a pull request!

---

**Happy watermarking with Claude! 🎉**
