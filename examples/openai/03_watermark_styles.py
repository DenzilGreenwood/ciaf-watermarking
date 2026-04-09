"""
OpenAI + CIAF Watermarking - Watermark Styles Demo

Demonstrates different watermarking styles and their use cases.

Usage:
    export OPENAI_API_KEY="your-key-here"
    python 03_watermark_styles.py

Styles Demonstrated:
    1. Footer (default) - Visible tag at bottom
    2. Header - Tag at top
    3. Inline - Embedded marker (subtle)
"""

import os
from openai import OpenAI
from ciaf_watermarks import watermark_ai_output, set_default_watermark_config


def generate_sample_text(client, prompt):
    """Helper to generate text with OpenAI."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150,
    )
    return response.choices[0].message.content


def demo_style(client, style_name, style_config, prompt):
    """Demonstrate a specific watermark style."""

    print(f"\n{'=' * 70}")
    print(f"Style: {style_name.upper()}")
    print(f"{'=' * 70}")

    # Generate content
    print("📝 Generating content...")
    original_text = generate_sample_text(client, prompt)

    # Watermark with specific style
    evidence, watermarked = watermark_ai_output(
        artifact=original_text,
        model_id="gpt-3.5-turbo",
        model_version="2024-03",
        actor_id="user:demo",
        prompt=prompt,
        watermark_config={"text": {"style": style_config}},
    )

    print(f"\n📄 Result ({len(watermarked)} chars):")
    print("-" * 70)
    print(watermarked)
    print("-" * 70)

    print("\n💧 Watermark Info:")
    print(f"   - Watermark ID: {evidence.watermark.watermark_id}")
    print(f"   - Style: {style_config}")
    print(f"   - Size increase: {len(watermarked) - len(original_text)} chars")

    return evidence, watermarked


def main():
    """Demonstrate different watermark styles."""

    print("=" * 70)
    print("OpenAI + CIAF - Watermark Styles Demo")
    print("=" * 70)

    # Setup
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    client = OpenAI(api_key=api_key)

    # Sample prompt
    prompt = "Explain the benefits of renewable energy in 2 sentences."

    # ========================================================================
    # STYLE 1: FOOTER (DEFAULT)
    # ========================================================================

    evidence_footer, watermarked_footer = demo_style(
        client, style_name="Footer", style_config="footer", prompt=prompt
    )

    print("\n✅ Best for:")
    print("   - Blog posts")
    print("   - Reports")
    print("   - Documents where footer is acceptable")

    # ========================================================================
    # STYLE 2: HEADER
    # ========================================================================

    evidence_header, watermarked_header = demo_style(
        client, style_name="Header", style_config="header", prompt=prompt
    )

    print("\n✅ Best for:")
    print("   - Articles")
    print("   - Emails")
    print("   - Content where upfront disclosure is important")

    # ========================================================================
    # STYLE 3: INLINE (SUBTLE)
    # ========================================================================

    evidence_inline, watermarked_inline = demo_style(
        client, style_name="Inline", style_config="inline", prompt=prompt
    )

    print("\n✅ Best for:")
    print("   - Chat messages")
    print("   - Social media posts")
    print("   - Content where visible tags are unwanted")
    print("   - (Still verifiable via forensic fragments)")

    # ========================================================================
    # COMPARISON
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Style Comparison")
    print(f"{'=' * 70}")

    print("\n📊 Visibility:")
    print("   Footer:  ⭐⭐⭐⭐⭐ (Very visible)")
    print("   Header:  ⭐⭐⭐⭐⭐ (Very visible)")
    print("   Inline:  ⭐⭐☆☆☆ (Subtle)")

    print("\n📏 Size Impact:")
    footer_size = len(watermarked_footer)
    header_size = len(watermarked_header)
    inline_size = len(watermarked_inline)

    print(f"   Footer:  {footer_size} chars")
    print(f"   Header:  {header_size} chars")
    print(f"   Inline:  {inline_size} chars")

    print("\n🔒 Verification:")
    print("   All styles: Fully verifiable via forensic fragments")

    # ========================================================================
    # VERIFY ALL STYLES
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Verification Test")
    print(f"{'=' * 70}")

    from ciaf_watermarks.text import verify_text_artifact

    styles_to_verify = [
        ("Footer", watermarked_footer, evidence_footer),
        ("Header", watermarked_header, evidence_header),
        ("Inline", watermarked_inline, evidence_inline),
    ]

    for style_name, watermarked, evidence in styles_to_verify:
        result = verify_text_artifact(watermarked, evidence)
        print(f"\n✅ {style_name}: {result.is_authentic()} ({result.confidence:.0%})")

    # ========================================================================
    # CUSTOM CONFIGURATION
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Custom Configuration Example")
    print(f"{'=' * 70}")

    # Set global default
    set_default_watermark_config(
        {"text": {"style": "footer", "include_simhash": True}}  # Enable similarity matching
    )

    print("\n💡 You can set global defaults:")
    print("   set_default_watermark_config({")
    print("       'text': {'style': 'footer'},")
    print("       'verification_base_url': 'https://your-api.com/verify'")
    print("   })")

    print("\n💡 Or override per-request:")
    print("   watermark_ai_output(..., watermark_config={'text': {'style': 'header'}})")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print(f"\n{'=' * 70}")
    print("Summary")
    print(f"{'=' * 70}")

    print("\n📝 Recommendation:")
    print("   - Public content → Footer or Header (transparency)")
    print("   - Chat/messaging → Inline (user experience)")
    print("   - Legal documents → Footer (clear provenance)")
    print("   - Social media → Inline (aesthetics)")

    print("\n🔐 Remember:")
    print("   Even if visible watermark is removed, forensic fragments")
    print("   can still detect authenticity!")


if __name__ == "__main__":
    main()
