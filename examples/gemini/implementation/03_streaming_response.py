"""
Google Gemini + CIAF Watermarking - Streaming Response Example

Demonstrates watermarking streaming responses from Google Gemini.
Accumulates the streamed chunks and applies watermarking to the complete response.

Usage:
    export GEMINI_API_KEY="your-key-here"
    python 03_streaming_response.py

Features:
    - Stream content from Gemini for better UX
    - Accumulate complete response
    - Watermark after streaming completes
    - Display both real-time streaming and watermarked result
"""

import json
import os
import sys
import google.generativeai as genai
from ciaf_watermarks import watermark_ai_output


def main():
    """Streaming response watermarking example."""

    print("=" * 70)
    print("Google Gemini Streaming with Watermarking")
    print("=" * 70)

    # Setup
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        print("   Get your key at: https://makersuite.google.com/app/apikey")
        return

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

    # User prompt
    user_prompt = "Write a detailed explanation of how neural networks learn, including backpropagation and gradient descent."

    print(f"\n📝 Prompt: {user_prompt}")
    print("\n" + "=" * 70)
    print("🌊 Streaming Response (real-time)")
    print("=" * 70)
    print()

    # ========================================================================
    # 1. STREAM RESPONSE FROM GEMINI
    # ========================================================================

    accumulated_text = ""
    chunk_count = 0

    try:
        # Generate content with streaming
        response = model.generate_content(user_prompt, stream=True)

        # Stream and display chunks
        for chunk in response:
            if chunk.text:
                chunk_text = chunk.text
                accumulated_text += chunk_text
                chunk_count += 1

                # Display streaming output in real-time
                print(chunk_text, end="", flush=True)
                sys.stdout.flush()

        print()  # New line after streaming

        print("\n✅ Streaming complete!")
        print(f"   - Total chunks: {chunk_count}")
        print(f"   - Total characters: {len(accumulated_text)}")

    except Exception as e:
        print(f"\n❌ Gemini API Error: {e}")
        return

    # ========================================================================
    # 2. WATERMARK THE COMPLETE RESPONSE
    # ========================================================================

    print("\n" + "=" * 70)
    print("💧 Watermarking Complete Response")
    print("=" * 70)

    try:
        evidence, watermarked_text = watermark_ai_output(
            artifact=accumulated_text,
            model_id="gemini-1.5-flash",
            model_version="1.5",
            actor_id="user:streaming_demo",
            prompt=user_prompt,
            verification_base_url="https://verify.example.com",
            enable_forensic_fragments=True,
        )

        print("\n✅ Watermarking successful!")
        print(f"   - Artifact ID: {evidence.artifact_id}")
        print(f"   - Watermark ID: {evidence.watermark.watermark_id}")
        if evidence.hashes.forensic_fragments:
            print(
                f"   - Forensic fragments: {len(evidence.hashes.forensic_fragments.all_fragments)}"
            )

    except Exception as e:
        print(f"❌ Watermarking Error: {e}")
        return

    # ========================================================================
    # 3. DISPLAY WATERMARKED OUTPUT
    # ========================================================================

    print("\n" + "=" * 70)
    print("📄 Final Watermarked Output")
    print("=" * 70)
    print(watermarked_text)
    print("=" * 70)

    # ========================================================================
    # 4. SAVE EVIDENCE
    # ========================================================================

    evidence_dir = "evidence/streaming_responses"
    os.makedirs(evidence_dir, exist_ok=True)

    evidence_file = os.path.join(evidence_dir, f"{evidence.artifact_id}.json")

    print(f"\n💾 Saving evidence to: {evidence_file}")

    with open(evidence_file, "w") as f:
        json.dump(evidence.to_dict(), f, indent=2)

    print("✅ Evidence saved successfully")

    # ========================================================================
    # 5. VERIFY AUTHENTICITY
    # ========================================================================

    print("\n" + "=" * 70)
    print("🔍 Verification")
    print("=" * 70)

    from ciaf_watermarks.text import verify_text_artifact

    verification_result = verify_text_artifact(watermarked_text, evidence)

    print("\n✅ Verification Result:")
    print(f"   - Authentic: {verification_result.is_authentic()}")
    print(f"   - Confidence: {verification_result.confidence:.2%}")
    print(f"   - Watermark Present: {verification_result.watermark_present}")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("\n" + "=" * 70)
    print("✅ Streaming Example Complete!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   - Model: Google Gemini Pro")
    print(f"   - Streaming chunks: {chunk_count}")
    print(f"   - Total length: {len(accumulated_text)} chars")
    print("   - Watermarked: Yes")
    print(f"   - Evidence saved: {evidence_file}")
    print(f"   - Verified: {verification_result.is_authentic()}")

    print("\n💡 Key Points:")
    print("   1. Stream content for better user experience")
    print("   2. Accumulate complete response before watermarking")
    print("   3. Watermark adds negligible overhead (~50-100ms)")
    print("   4. Users see streaming, then get watermarked final output")

    print("\n🎯 Best Practices:")
    print("   - Show streaming output to user in real-time")
    print("   - Store watermarked version in database/logs")
    print("   - Return watermarked version as final response")
    print("   - Save evidence for later verification")

    print("\n📚 Related Examples:")
    print("   - 01_basic_text_watermarking.py - Simple watermarking")
    print("   - 02_chat_conversation.py - Multi-turn chats")
    print("   - 04_batch_processing.py - Batch multiple requests")


if __name__ == "__main__":
    main()
