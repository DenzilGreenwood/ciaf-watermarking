"""
OpenAI + CIAF Watermarking - Basic Text Example

This example demonstrates the simplest integration:
1. Generate text with OpenAI
2. Watermark the output
3. Save evidence
4. Verify authenticity

Usage:
    export OPENAI_API_KEY="your-key-here"
    python 01_basic_text_watermarking.py

Requirements:
    pip install ciaf-watermarks openai
"""

import os
import json
from openai import OpenAI
from ciaf_watermarks import watermark_ai_output


def main():
    """Basic OpenAI watermarking example."""

    # ========================================================================
    # 1. SETUP
    # ========================================================================

    print("=" * 70)
    print("OpenAI + CIAF Watermarking - Basic Example")
    print("=" * 70)

    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # User prompt
    user_prompt = "Explain quantum computing in 2 paragraphs for a general audience."

    print(f"\n📝 Prompt: {user_prompt}")

    # ========================================================================
    # 2. GENERATE WITH OPENAI
    # ========================================================================

    print("\n🤖 Calling OpenAI API...")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that explains complex topics simply.",
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        # Extract generated text
        openai_text = response.choices[0].message.content

        print(f"✅ Generated {len(openai_text)} characters")
        print("\n📄 Original OpenAI Response:")
        print("-" * 70)
        print(openai_text)
        print("-" * 70)

    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return

    # ========================================================================
    # 3. WATERMARK THE OUTPUT
    # ========================================================================

    print("\n💧 Watermarking content...")

    try:
        evidence, watermarked_text = watermark_ai_output(
            artifact=openai_text,
            model_id="gpt-4",
            model_version="2024-04",  # Use your model version
            actor_id="user:demo",  # Who requested this generation
            prompt=user_prompt,
            verification_base_url="https://verify.example.com",
            enable_forensic_fragments=True,
        )

        print("✅ Watermarking successful!")
        print(f"   - Artifact ID: {evidence.artifact_id}")
        print(f"   - Watermark ID: {evidence.watermark.watermark_id}")
        print(f"   - Hash (before): {evidence.hashes.content_hash_before_watermark[:16]}...")
        print(f"   - Hash (after):  {evidence.hashes.content_hash_after_watermark[:16]}...")
        if evidence.hashes.forensic_fragments:
            print(
                f"   - Forensic fragments: {len(evidence.hashes.forensic_fragments.all_fragments)}"
            )

    except Exception as e:
        print(f"❌ Watermarking Error: {e}")
        return

    # ========================================================================
    # 4. DISPLAY WATERMARKED OUTPUT
    # ========================================================================

    print("\n📄 Watermarked Output:")
    print("=" * 70)
    print(watermarked_text)
    print("=" * 70)

    # ========================================================================
    # 5. SAVE ALL ARTIFACTS
    # ========================================================================

    print("\n💾 Saving all artifacts...")

    # Create output directory structure
    output_dir = f"outputs/openai_basic/{evidence.artifact_id}"
    os.makedirs(output_dir, exist_ok=True)

    # Save original text
    original_file = os.path.join(output_dir, "01_original.txt")
    with open(original_file, "w", encoding="utf-8") as f:
        f.write(openai_text)
    print(f"✅ Saved original: {original_file}")

    # Save watermarked text
    watermarked_file = os.path.join(output_dir, "02_watermarked.txt")
    with open(watermarked_file, "w", encoding="utf-8") as f:
        f.write(watermarked_text)
    print(f"✅ Saved watermarked: {watermarked_file}")

    # Save evidence
    evidence_file = os.path.join(output_dir, "03_evidence.json")
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence.to_dict(), f, indent=2)
    print(f"✅ Saved evidence: {evidence_file}")

    # ========================================================================
    # 6. VERIFY AUTHENTICITY (Demonstration)
    # ========================================================================

    print("\n🔍 Verifying watermarked content...")

    from ciaf_watermarks.text import verify_text_artifact

    # Verify the exact watermarked text (should match perfectly)
    verification_result = verify_text_artifact(watermarked_text, evidence)

    print("✅ Verification Result:")
    print(f"   - Authentic: {verification_result.is_authentic()}")
    print(f"   - Confidence: {verification_result.confidence:.2%}")
    print(f"   - Watermark Present: {verification_result.watermark_present}")
    print(f"   - Watermark Intact: {verification_result.watermark_intact}")

    # ========================================================================
    # 7. TEST WITH MODIFIED CONTENT
    # ========================================================================

    print("\n🔬 Testing with modified content...")

    # Slightly modify the text
    modified_text = watermarked_text.replace("quantum", "QUANTUM")

    # Show what was modified
    print("\n📝 Modified Content Sample (first 200 chars):")
    print("-" * 70)
    print(modified_text[:200] + "...")
    print("-" * 70)
    print(
        f"\nChanges: 'AI' → 'Artificial Intelligence' ({watermarked_text.count('AI')} replacements)"
    )

    verification_result_modified = verify_text_artifact(modified_text, evidence)

    print("\n✅ Modified Content Verification:")
    print(f"   - Authentic: {verification_result_modified.is_authentic()}")
    print(f"   - Confidence: {verification_result_modified.confidence:.2%}")
    print(f"   - Content Modified: {verification_result_modified.content_modified}")
    print(
        f"   - Confidence Drop: {verification_result.confidence - verification_result_modified.confidence:.2%}"
    )

    # Save modified text
    modified_file = os.path.join(output_dir, "04_modified.txt")
    with open(modified_file, "w", encoding="utf-8") as f:
        f.write(modified_text)
    print(f"\n💾 Saved modified text: {modified_file}")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("\n" + "=" * 70)
    print("✅ Example Complete!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   - Generated with: OpenAI GPT-4")
    print("   - Watermarked: Yes")
    print(f"   - All artifacts saved to: {output_dir}")
    print(
        f"   - Original verified: {verification_result.is_authentic()} ({verification_result.confidence:.0%})"
    )
    print(
        f"   - Modified detected: Confidence dropped to {verification_result_modified.confidence:.0%}"
    )
    print("\n📂 Output Structure:")
    print(f"   {output_dir}/")
    print("   ├── 01_original.txt      (Raw OpenAI output)")
    print("   ├── 02_watermarked.txt   (With provenance tag)")
    print("   ├── 03_evidence.json     (Forensic evidence)")
    print("   └── 04_modified.txt      (Test tampering)")
    print("\n💡 Next Steps:")
    print("   1. Review the watermarked text (notice the footer)")
    print("   2. Check the evidence JSON file")
    print("   3. Try modifying the text and verifying again")
    print("   4. Integrate this pattern into your application")


if __name__ == "__main__":
    main()
