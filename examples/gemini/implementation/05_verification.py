"""
Google Gemini + CIAF Watermarking - Verification Example

Demonstrates how to verify watermarked content from Gemini generations.
Shows all three verification tiers and how to handle different scenarios.

Usage:
    python 05_verification.py

Features:
    - Load evidence from storage
    - Verify exact matches (Tier 1)
    - Verify modified content with fragments (Tier 2)
    - Verify paraphrased content with similarity (Tier 3)
    - Detect fake/non-authentic content
"""

import os
import json
from ciaf_watermarks.text import verify_text_artifact
from ciaf_watermarks.models import ArtifactEvidence


def load_evidence_from_file(evidence_file):
    """Load evidence from JSON file."""
    if not os.path.exists(evidence_file):
        raise FileNotFoundError(f"Evidence file not found: {evidence_file}")

    with open(evidence_file, "r") as f:
        evidence_data = json.load(f)

    return ArtifactEvidence(**evidence_data)


def verify_content(suspect_text, evidence, description):
    """
    Verify suspect content against evidence.

    Args:
        suspect_text: The text to verify
        evidence: ArtifactEvidence object
        description: Description of the test case
    """
    print(f"\n{'=' * 70}")
    print(f"Test Case: {description}")
    print(f"{'=' * 70}")

    print("\n📄 Suspect Text (first 150 chars):")
    print(f"{suspect_text[:150]}...")

    result = verify_text_artifact(suspect_text, evidence)

    print("\n🔍 Verification Result:")
    print(f"   - Authentic: {result.is_authentic()}")
    print(f"   - Confidence: {result.confidence:.2%}")
    print(f"   - Watermark Present: {result.watermark_present}")
    print(f"   - Notes: {result.notes[0] if result.notes else 'No notes'}")

    return result


def main():
    """Verification example."""

    print("=" * 70)
    print("Google Gemini Content Verification Example")
    print("=" * 70)

    # ========================================================================
    # 1. SETUP - Generate sample content or load existing
    # ========================================================================

    print("\n📋 Setup:")
    print("   This example requires existing watermarked content.")
    print("   Run 01_basic_text_watermarking.py first to generate test data.\n")

    # Check for existing evidence files in outputs directory
    outputs_base = "outputs/gemini_basic"
    if not os.path.exists(outputs_base):
        print(f"❌ Outputs directory not found: {outputs_base}")
        print("   Please run 01_basic_text_watermarking.py first.")
        return

    # Find artifact directories
    artifact_dirs = [
        d for d in os.listdir(outputs_base) if os.path.isdir(os.path.join(outputs_base, d))
    ]
    if not artifact_dirs:
        print(f"❌ No artifact directories found in: {outputs_base}")
        print("   Please run 01_basic_text_watermarking.py first.")
        return

    # Use the first artifact directory
    artifact_id = artifact_dirs[0]
    artifact_dir = os.path.join(outputs_base, artifact_id)
    print(f"✅ Using artifact directory: {artifact_dir}")

    # Load evidence
    evidence_file = os.path.join(artifact_dir, "03_evidence.json")
    if not os.path.exists(evidence_file):
        print(f"❌ Evidence file not found: {evidence_file}")
        return

    evidence = load_evidence_from_file(evidence_file)
    print(f"✅ Loaded evidence for artifact: {evidence.artifact_id}")

    # Load the actual watermarked text
    watermarked_file = os.path.join(artifact_dir, "02_watermarked.txt")
    if not os.path.exists(watermarked_file):
        print(f"❌ Watermarked text file not found: {watermarked_file}")
        return

    with open(watermarked_file, "r", encoding="utf-8") as f:
        watermarked_text = f.read()
    print(f"✅ Loaded watermarked text from: {watermarked_file}")

    # Load the original text for creating test scenarios
    original_file = os.path.join(artifact_dir, "01_original.txt")
    if os.path.exists(original_file):
        with open(original_file, "r", encoding="utf-8") as f:
            base_text = f.read()
    else:
        # Fallback: extract base text by removing watermark footer
        base_text = (
            watermarked_text.split("\n---\n")[0]
            if "\n---\n" in watermarked_text
            else watermarked_text
        )

    print("\n⚠️  Note: For this demo, we'll use the actual watermarked content.")
    print("   In production, you'd receive suspect content from users.\n")

    # ========================================================================
    # 2. TEST SCENARIOS
    # ========================================================================

    # ========================================================================
    # 3. TIER 1 - EXACT MATCH VERIFICATION
    # ========================================================================

    result_tier1 = verify_content(watermarked_text, evidence, "Tier 1 - Exact Match")

    assert result_tier1.is_authentic(), "Tier 1 verification should pass!"

    # ========================================================================
    # 4. TIER 2 - MODIFIED CONTENT (Fragment Matching)
    # ========================================================================

    # Simulate minor modifications
    modified_text = watermarked_text.replace("quantum computing", "QUANTUM COMPUTING")
    modified_text = modified_text.replace("classical computers", "traditional computers")

    result_tier2 = verify_content(
        modified_text, evidence, "Tier 2 - Modified Content (Minor Edits)"
    )

    # ========================================================================
    # 5. TIER 3 - HEAVILY MODIFIED (Similarity Matching)
    # ========================================================================

    # Simulate paraphrasing or heavy editing
    paraphrased_text = """Quantum computers represent groundbreaking technology utilizing quantum physics principles for data processing. While traditional computing systems rely on binary bits, quantum systems employ qubits that leverage superposition to exist in multiple states at once.

These advanced machines show promise in tackling challenging computational tasks beyond the reach of conventional systems, including pharmaceutical research, secure communications, and resource allocation problems. Yet, this technology remains nascent, confronting hurdles like error mitigation and qubit stability."""

    result_tier3 = verify_content(paraphrased_text, evidence, "Tier 3 - Paraphrased Content")

    # ========================================================================
    # 6. NON-AUTHENTIC CONTENT
    # ========================================================================

    fake_text = """Artificial intelligence is a branch of computer science that aims to create machines capable of intelligent behavior. Machine learning, a subset of AI, enables computers to learn from data without explicit programming.

Deep learning uses neural networks with multiple layers to analyze data patterns. This technology powers many modern applications including image recognition, natural language processing, and autonomous vehicles."""

    result_fake = verify_content(
        fake_text, evidence, "Non-Authentic - Completely Different Content"
    )

    # ========================================================================
    # 7. WATERMARK REMOVED (Forensic Detection)
    # ========================================================================

    watermark_removed = base_text  # Original text without visible watermark

    result_removed = verify_content(
        watermark_removed, evidence, "Watermark Removed - Forensic Fragment Detection"
    )

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)

    print("\n📊 Test Results:")
    print(
        f"   1. Exact Match (Tier 1):      {result_tier1.is_authentic()} ({result_tier1.confidence:.0%})"
    )
    print(
        f"   2. Minor Modifications (Tier 2): {result_tier2.is_authentic()} ({result_tier2.confidence:.0%})"
    )
    print(
        f"   3. Paraphrased (Tier 3):      {result_tier3.is_authentic()} ({result_tier3.confidence:.0%})"
    )
    print(
        f"   4. Non-Authentic Content:     {result_fake.is_authentic()} ({result_fake.confidence:.0%})"
    )
    print(
        f"   5. Watermark Removed:         {result_removed.is_authentic()} ({result_removed.confidence:.0%})"
    )

    print("\n💡 Understanding Verification Tiers:")
    print("   • Tier 1 (Exact): Hash-based, 100% confidence")
    print("   • Tier 2 (Fragment): DNA fragments match, high confidence")
    print("   • Tier 3 (Similarity): Perceptual matching, medium confidence")

    print("\n🎯 Production Implementation:")
    print("   1. Set confidence thresholds based on your use case")
    print("   2. High-stakes: Require Tier 1 or high Tier 2")
    print("   3. Content monitoring: Accept Tier 3 for detection")
    print("   4. Always log verification results for audit")

    print("\n⚙️  API Endpoint Pattern:")
    print("""
    POST /verify
    {
        "suspect_text": "...",
        "watermark_id": "wmk-..."
    }

    Response:
    {
        "is_authentic": true,
        "confidence": 0.99,
        "tier": "TIER1_EXACT",
        "timestamp": "2024-..."
    }
    """)

    print("\n📚 Related Examples:")
    print("   - 01_basic_text_watermarking.py - Generate watermarked content")
    print("   - 02_chat_conversation.py - Verify conversations")
    print("   - 04_batch_processing.py - Batch verification")


if __name__ == "__main__":
    main()
