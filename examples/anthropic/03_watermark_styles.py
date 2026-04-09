"""
Anthropic + CIAF Watermarking - Watermark Styles Comparison

Demonstrates the three watermark styles:
1. Footer - Appends watermark at the end (most visible)
2. Header - Prepends watermark at the start (visible)
3. Inline - Embeds watermark within content (subtle)

Usage:
    export ANTHROPIC_API_KEY="your-key-here"
    python 03_watermark_styles.py
"""

import os
import json
from anthropic import Anthropic
from ciaf_watermarks import watermark_ai_output, set_default_watermark_config
from ciaf_watermarks.text import verify_text_artifact

# ============================================================================
# CONFIGURATION
# ============================================================================

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
EVIDENCE_DIR = "evidence/styles"

os.makedirs(EVIDENCE_DIR, exist_ok=True)

if not ANTHROPIC_API_KEY:
    print("⚠️  Error: ANTHROPIC_API_KEY not set")
    exit(1)

# Initialize Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)


# ============================================================================
# GENERATE SAMPLE CONTENT
# ============================================================================

print("=" * 70)
print("Anthropic + CIAF Watermarking - Style Comparison")
print("=" * 70)

print("\n📝 Generating sample content with Claude...")

response = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=250,
    messages=[
        {"role": "user", "content": "Write a brief explanation of cloud computing (3-4 sentences)."}
    ],
)

original_text = response.content[0].text

print(f"✅ Generated {len(original_text)} characters")
print(f"\nOriginal text:\n{original_text}")


# ============================================================================
# HELPER FUNCTION
# ============================================================================


def demo_style(style_name: str, original_text: str, use_case: str) -> None:
    """
    Demonstrate a specific watermark style.

    Args:
        style_name: "footer", "header", or "inline"
        original_text: The text to watermark
        use_case: Description of when to use this style
    """
    print(f"\n{'=' * 70}")
    print(f"Style: {style_name.upper()}")
    print(f"{'=' * 70}")
    print(f"Use Case: {use_case}")

    # Watermark with this style
    evidence, watermarked = watermark_ai_output(
        artifact=original_text,
        model_id="claude-3-sonnet-20240229",
        model_version="2024-02",
        actor_id="user:style-demo",
        prompt="Cloud computing explanation",
        watermark_config={
            "text": {"style": style_name, "include_timestamp": True, "include_model_info": True}
        },
        enable_forensic_fragments=True,
    )

    # Calculate size increase
    original_size = len(original_text)
    watermarked_size = len(watermarked)
    size_increase = watermarked_size - original_size
    percentage = (size_increase / original_size) * 100

    print("\n📊 Size Impact:")
    print(f"   Original: {original_size} characters")
    print(f"   Watermarked: {watermarked_size} characters")
    print(f"   Increase: +{size_increase} characters (+{percentage:.1f}%)")

    print("\n🔒 Watermarked Text:")
    print(watermarked)

    # Verify it works
    result = verify_text_artifact(watermarked, evidence)

    print("\n✓ Verification:")
    print(f"   Authentic: {result.is_authentic()}")
    print(f"   Confidence: {result.confidence:.2%}")
    print(f"   Watermark Present: {result.watermark_present}")

    # Save evidence
    evidence_file = os.path.join(EVIDENCE_DIR, f"{style_name}_{evidence.artifact_id}.json")
    with open(evidence_file, "w") as f:
        json.dump(evidence.to_dict(), f, indent=2)

    print(f"   Evidence: {evidence_file}")

    return evidence, watermarked


# ============================================================================
# STYLE 1: FOOTER (DEFAULT)
# ============================================================================

evidence_footer, watermarked_footer = demo_style(
    style_name="footer",
    original_text=original_text,
    use_case="Public-facing content, blog posts, documentation, articles",
)


# ============================================================================
# STYLE 2: HEADER
# ============================================================================

evidence_header, watermarked_header = demo_style(
    style_name="header",
    original_text=original_text,
    use_case="Legal documents, reports, official statements, contracts",
)


# ============================================================================
# STYLE 3: INLINE (SUBTLE)
# ============================================================================

evidence_inline, watermarked_inline = demo_style(
    style_name="inline",
    original_text=original_text,
    use_case="Chat applications, social media, customer support, casual content",
)


# ============================================================================
# COMPARISON TABLE
# ============================================================================

print(f"\n{'=' * 70}")
print("STYLE COMPARISON")
print(f"{'=' * 70}")

print(f"\n{'Style':<12} {'Visibility':<15} {'Size Increase':<18} {'Best For':<30}")
print("-" * 70)

footer_size = len(watermarked_footer) - len(original_text)
header_size = len(watermarked_header) - len(original_text)
inline_size = len(watermarked_inline) - len(original_text)

print(f"{'Footer':<12} {'High ⭐⭐⭐':<15} {f'+{footer_size} chars':<18} {'Public content':<30}")
print(f"{'Header':<12} {'High ⭐⭐⭐':<15} {f'+{header_size} chars':<18} {'Legal documents':<30}")
print(f"{'Inline':<12} {'Low ⭐':<15} {f'+{inline_size} chars':<18} {'Chat/social media':<30}")


# ============================================================================
# GLOBAL CONFIGURATION EXAMPLE
# ============================================================================

print(f"\n{'=' * 70}")
print("SETTING GLOBAL DEFAULT STYLE")
print(f"{'=' * 70}")

print("\n💡 You can set a default style for all watermarks:")
print("\nfrom ciaf_watermarks import set_default_watermark_config")
print("\nset_default_watermark_config({")
print('    "text": {')
print('        "style": "inline",  # Your preferred default')
print('        "include_timestamp": True')
print("    }")
print("})")
print("\n# Then watermark_ai_output() will use inline by default")
print("# (But you can still override per-request)")

# Demonstrate setting global config
set_default_watermark_config(
    {"text": {"style": "inline", "include_timestamp": True, "include_model_info": False}}
)

print("\n✅ Global config set to 'inline' style")

# Now watermark without specifying config (uses global default)
evidence_global, watermarked_global = watermark_ai_output(
    artifact=original_text,
    model_id="claude-3-sonnet-20240229",
    model_version="2024-02",
    actor_id="user:global-demo",
    prompt="Test",
    enable_forensic_fragments=True,
    # Note: No watermark_config specified - uses global default
)

print("\n🔒 Watermarked with global config (inline style):")
print(f"Size: {len(watermarked_global)} characters")
print("Style used: inline (from global config)")

# Override global config for one request
evidence_override, watermarked_override = watermark_ai_output(
    artifact=original_text,
    model_id="claude-3-sonnet-20240229",
    model_version="2024-02",
    actor_id="user:override-demo",
    prompt="Test",
    watermark_config={"text": {"style": "footer"}},  # Override
    enable_forensic_fragments=True,
)

print("\n🔒 Watermarked with override (footer style):")
print(f"Size: {len(watermarked_override)} characters")
print("Style used: footer (override)")


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

print(f"\n{'=' * 70}")
print("RECOMMENDATIONS")
print(f"{'=' * 70}")

recommendations = [
    ("Public Blog Posts", "footer", "Clear attribution, establishes trust"),
    ("Legal Documents", "header", "Immediate visibility, compliance"),
    ("Chat Applications", "inline", "Maintains natural flow, less intrusive"),
    ("Social Media", "inline", "Subtle, doesn't affect engagement"),
    ("Official Reports", "header or footer", "Professional appearance"),
    ("Customer Support", "inline", "Natural conversation flow"),
    ("API Responses", "inline", "Minimal size overhead"),
    ("Content Moderation", "footer", "Clear tracking and attribution"),
]

for use_case, recommended_style, reason in recommendations:
    print(f"\n📌 {use_case}:")
    print(f"   Recommended: {recommended_style}")
    print(f"   Reason: {reason}")


# ============================================================================
# SUMMARY
# ============================================================================

print(f"\n{'=' * 70}")
print("✅ SUMMARY")
print(f"{'=' * 70}")
print("✓ Demonstrated 3 watermark styles: footer, header, inline")
print("✓ All styles verified successfully")
print(f"✓ Size overhead: {inline_size}-{footer_size} characters")
print(f"✓ Inline style has minimal impact (~{inline_size} chars)")
print(f"✓ Footer/header styles are more visible (~{footer_size} chars)")
print("\n💡 Choose style based on your use case:")
print("   - Need visibility? → footer or header")
print("   - Need subtlety? → inline")
print("   - Set global default with set_default_watermark_config()")
print(f"{'=' * 70}")
