"""
Anthropic + CIAF Watermarking - FastAPI Integration

A complete REST API example showing:
- POST /generate - Generate and watermark Claude responses
- POST /verify - Verify watermarked content
- GET /evidence/{artifact_id} - Retrieve evidence

Usage:
    export ANTHROPIC_API_KEY="your-key-here"
    pip install fastapi uvicorn
    python 04_fastapi_api.py

    # Then in another terminal:
    curl -X POST http://localhost:8000/generate \
      -H "Content-Type: application/json" \
      -d '{"prompt": "Explain AI"}'
"""

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from anthropic import Anthropic
from ciaf_watermarks import watermark_ai_output
from ciaf_watermarks.text import verify_text_artifact
from ciaf_watermarks.models import ArtifactEvidence

# ============================================================================
# CONFIGURATION
# ============================================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
EVIDENCE_DIR = "evidence/api"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

if not ANTHROPIC_API_KEY:
    print("⚠️  Warning: ANTHROPIC_API_KEY not set")

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class GenerateRequest(BaseModel):
    """Request for content generation."""

    prompt: str
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 1.0
    max_tokens: int = 1024
    user_id: str = "anonymous"
    watermark_style: str = "footer"  # footer, header, inline


class GenerateResponse(BaseModel):
    """Response from generation endpoint."""

    content: str
    watermark_id: str
    artifact_id: str
    model: str
    timestamp: str
    usage: dict


class VerifyRequest(BaseModel):
    """Request for content verification."""

    content: str
    watermark_id: str


class VerifyResponse(BaseModel):
    """Response from verification endpoint."""

    is_authentic: bool
    confidence: float
    watermark_present: bool
    watermark_intact: bool
    content_modified: bool


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Anthropic + CIAF Watermarking API",
    description="Generate AI content with transparent watermarking using Claude",
    version="1.0.0",
)


@app.get("/")
async def root():
    """API information."""
    return {
        "name": "Anthropic + CIAF Watermarking API",
        "version": "1.0.0",
        "model": "Claude (Anthropic)",
        "endpoints": {
            "generate": "POST /generate - Generate watermarked content",
            "verify": "POST /verify - Verify content authenticity",
            "evidence": "GET /evidence/{artifact_id} - Get evidence record",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "anthropic_configured": ANTHROPIC_API_KEY is not None,
        "evidence_dir": EVIDENCE_DIR,
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    """
    Generate content with Claude and apply watermarking.

    Example:
        POST /generate
        {
            "prompt": "Explain quantum computing",
            "user_id": "user123",
            "watermark_style": "footer",
            "model": "claude-3-sonnet-20240229"
        }
    """

    if not anthropic_client:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    try:
        # Generate with Claude
        response = anthropic_client.messages.create(
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}],
        )

        # Extract text from Claude's response
        claude_text = response.content[0].text

        # Watermark the output
        evidence, watermarked = watermark_ai_output(
            artifact=claude_text,
            model_id=request.model,
            model_version="2024-02",
            actor_id=f"user:{request.user_id}",
            prompt=request.prompt,
            watermark_config={"text": {"style": request.watermark_style}},
            enable_forensic_fragments=True,
        )

        # Save evidence
        evidence_file = os.path.join(EVIDENCE_DIR, f"{evidence.artifact_id}.json")
        with open(evidence_file, "w") as f:
            json.dump(evidence.to_dict(), f, indent=2)

        # Return response
        return GenerateResponse(
            content=watermarked,
            watermark_id=evidence.watermark.watermark_id,
            artifact_id=evidence.artifact_id,
            model=request.model,
            timestamp=evidence.timestamp,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify", response_model=VerifyResponse)
async def verify_content(request: VerifyRequest):
    """
    Verify if content is authentic based on watermark.

    Example:
        POST /verify
        {
            "content": "Watermarked text...",
            "watermark_id": "wmk-abc123"
        }
    """

    try:
        # Find evidence file by watermark_id
        evidence_file = None
        for filename in os.listdir(EVIDENCE_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(EVIDENCE_DIR, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                    if data.get("watermark", {}).get("watermark_id") == request.watermark_id:
                        evidence_file = filepath
                        break

        if not evidence_file:
            raise HTTPException(
                status_code=404,
                detail=f"No evidence found for watermark_id: {request.watermark_id}",
            )

        # Load evidence
        with open(evidence_file, "r") as f:
            evidence_data = json.load(f)

        evidence = ArtifactEvidence(**evidence_data)

        # Verify content
        result = verify_text_artifact(request.content, evidence)

        return VerifyResponse(
            is_authentic=result.is_authentic(),
            confidence=result.confidence,
            watermark_present=result.watermark_present,
            watermark_intact=result.watermark_intact,
            content_modified=result.content_modified,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/evidence/{artifact_id}")
async def get_evidence(artifact_id: str):
    """
    Retrieve evidence record for an artifact.

    Example:
        GET /evidence/art-abc123def456
    """

    evidence_file = os.path.join(EVIDENCE_DIR, f"{artifact_id}.json")

    if not os.path.exists(evidence_file):
        raise HTTPException(
            status_code=404, detail=f"Evidence not found for artifact_id: {artifact_id}"
        )

    with open(evidence_file, "r") as f:
        evidence_data = json.load(f)

    return JSONResponse(content=evidence_data)


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("Anthropic + CIAF Watermarking API")
    print("=" * 70)
    print("\n🚀 Starting server on http://localhost:8000")
    print("\n📚 API Documentation:")
    print("   - Swagger UI: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")

    print("\n💡 Example Usage:")
    print("   # Generate content")
    print("   curl -X POST http://localhost:8000/generate \\")
    print("     -H 'Content-Type: application/json' \\")
    print('     -d \'{"prompt": "Explain AI watermarking"}\'')

    print("\n   # Verify content")
    print("   curl -X POST http://localhost:8000/verify \\")
    print("     -H 'Content-Type: application/json' \\")
    print('     -d \'{"content": "...", "watermark_id": "wmk-..."}\'')

    print("\n" + "=" * 70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
