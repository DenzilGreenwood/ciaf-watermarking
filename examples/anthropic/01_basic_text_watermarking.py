"""
Anthropic + CIAF Watermarking - Basic Text Example

The simplest possible integration showing:
1. Generate text with Claude
2. Watermark the output
3. Save evidence
4. Verify authenticity

Usage:
    export ANTHROPIC_API_KEY="your-key-here"
    python 01_basic_text_watermarking.py
"""

import os
import json
from anthropic import Anthropic
from ciaf_watermarks import watermark_ai_output
from ciaf_watermarks.text import verify_text_artifact

# ============================================================================
# CONFIGURATION
# ============================================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
EVIDENCE_DIR = "evidence/basic"

# Create evidence directory
os.makedirs(EVIDENCE_DIR, exist_ok=True)

if not ANTHROPIC_API_KEY:
    print("⚠️  Error: ANTHROPIC_API_KEY environment variable not set")
    print("Please set it with: export ANTHROPIC_API_KEY='your-key-here'")
    exit(1)


# ============================================================================
# STEP 1: Generate Content with Claude
# ============================================================================

print("=" * 70)
print("Anthropic + CIAF Watermarking - Basic Example")
print("=" * 70)

print("\n📝 Step 1: Generating content with Claude...")

# Initialize Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# User's prompt
user_prompt = "Explain artificial intelligence in 2-3 sentences."

# Generate with Claude
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=200,
    messages=[{"role": "user", "content": user_prompt}],
)

# Extract the text from Claude's response
original_text = response.content[0].text

print(f"✅ Generated {len(original_text)} characters")
print(f"\nOriginal Claude response:\n{original_text}")


# ============================================================================
# STEP 2: Watermark the Content
# ============================================================================

print("\n🔒 Step 2: Watermarking the content...")

# Apply watermark with full forensic capabilities
evidence, watermarked_text = watermark_ai_output(
    artifact=original_text,
    model_id="claude-3-sonnet-20240229",
    model_version="2024-02",
    actor_id="user:alice@example.com",
    prompt=user_prompt,
    watermark_config={
        "text": {
            "style": "footer",  # Adds visible footer
            "include_timestamp": True,
            "include_model_info": True,
        }
    },
    enable_forensic_fragments=True,
)

print(f"✅ Watermark ID: {evidence.watermark.watermark_id}")
print(f"✅ Artifact ID: {evidence.artifact_id}")
print(f"\nWatermarked text:\n{watermarked_text}")


# ============================================================================
# STEP 3: Save All Artifacts
# ============================================================================

print("\n💾 Step 3: Saving all artifacts...")

# Create output directory structure
output_dir = f"outputs/anthropic_basic/{evidence.artifact_id}"
os.makedirs(output_dir, exist_ok=True)

# Save original text
original_file = os.path.join(output_dir, "01_original.txt")
with open(original_file, "w", encoding="utf-8") as f:
    f.write(original_text)
print(f"✅ Saved original: {original_file}")

# Save watermarked text
watermarked_file = os.path.join(output_dir, "02_watermarked.txt")
with open(watermarked_file, "w", encoding="utf-8") as f:
    f.write(watermarked_text)
print(f"✅ Saved watermarked: {watermarked_file}")

# Save evidence
evidence_file = os.path.join(output_dir, "03_evidence.json")
with open(evidence_file, "w") as f:
    json.dump(evidence.to_dict(), f, indent=2)
print(f"✅ Saved evidence: {evidence_file}")


# ============================================================================
# STEP 4: Verify the Watermarked Content
# ============================================================================

print("\n✓ Step 4: Verifying the watermarked content...")

# Verify the watermarked text
result = verify_text_artifact(watermarked_text, evidence)

print("✅ Verification Result:")
print(f"   - Authentic: {result.is_authentic()}")
print(f"   - Confidence: {result.confidence:.2%}")
print(f"   - Watermark Present: {result.watermark_present}")
print(f"   - Watermark Intact: {result.watermark_intact}")


# ============================================================================
# STEP 5: Test with Modified Content
# ============================================================================

print("\n🔬 Step 5: Testing with modified content...")

# Simulate tampering
modified_text = watermarked_text + "\n\nThis sentence was added by someone else."

# Show what was modified
print("\n📝 Modified Content (showing addition):")
print("-" * 70)
print("... (original content) ...")
print("\n[ADDED:] This sentence was added by someone else.")
print("-" * 70)
print(f"\nModification: Added {len('This sentence was added by someone else.')} characters")

# Verify the modified text
result_modified = verify_text_artifact(modified_text, evidence)

print("\n❌ Verification Result for Modified Content:")
print(f"   - Authentic: {result_modified.is_authentic()}")
print(f"   - Confidence: {result_modified.confidence:.2%}")
print(f"   - Content Modified: {result_modified.content_modified}")
print(f"   - Confidence Drop: {result.confidence - result_modified.confidence:.2%}")

# Save modified text
modified_file = os.path.join(output_dir, "04_modified.txt")
with open(modified_file, "w", encoding="utf-8") as f:
    f.write(modified_text)
print(f"\n💾 Saved modified text: {modified_file}")


# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("✅ SUMMARY")
print("=" * 70)
print("✓ Generated text with Claude (claude-3-sonnet)")
print("✓ Applied watermark with forensic fragments")
print(f"✓ All artifacts saved to: {output_dir}")
print(f"✓ Verified authentic content: {result.is_authentic()}")
print(f"✓ Detected modified content: {not result_modified.is_authentic()}")
print("\n📂 Output Structure:")
print("   {output_dir}/")
print("   ├── 01_original.txt      (Raw Claude output)")
print("   ├── 02_watermarked.txt   (With provenance tag)")
print("   ├── 03_evidence.json     (Forensic evidence)")
print("   └── 04_modified.txt      (Test tampering)")
print("\n💡 Next Steps:")
print("   - Try 02_chat_conversation.py for multi-turn conversations")
print("   - Try 03_watermark_styles.py to see different styles")
print("   - Try 04_fastapi_api.py for a production API")
print("=" * 70)
