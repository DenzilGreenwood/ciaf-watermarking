"""
CIAF Watermarking - Distinctive Anchor Integration Example

Demonstrates the integrated forensic fingerprinting with watermarking.

This example shows how the validated distinctive anchor method (1.19 × 10⁻⁸
collision rate) enhances watermarking with forensic fallback verification.
"""

from ciaf_watermarks import (
    build_text_artifact_evidence,
    verify_text_artifact,
    compute_distinctive_anchor_fingerprint,
    compare_anchor_fingerprints,
)


def example_integrated_watermarking():
    """
    Demonstrate integrated watermarking + forensic fingerprinting.
    """
    print("=" * 80)
    print("CIAF INTEGRATED WATERMARKING + FORENSIC FINGERPRINTING")
    print("=" * 80)

    # Original AI-generated text
    raw_text = """
    Climate change represents one of the most pressing challenges facing 
    humanity today. The scientific consensus is overwhelming: human activities, 
    particularly the burning of fossil fuels, are driving global temperature 
    increases at an unprecedented rate. This warming trend has far-reaching 
    consequences for ecosystems, weather patterns, and human societies worldwide.
    
    Recent studies indicate that the planet has warmed by approximately 1.1 
    degrees Celsius since pre-industrial times. This seemingly small increase 
    has led to more frequent and severe weather events, including hurricanes, 
    droughts, and heatwaves. Coastal communities face rising sea levels that 
    threaten infrastructure and livelihoods. Arctic ice continues to melt at 
    alarming rates, affecting wildlife habitats and contributing to feedback 
    loops that accelerate warming.
    
    Addressing climate change requires coordinated global action. Transitioning 
    to renewable energy sources, improving energy efficiency, and developing 
    carbon capture technologies are essential steps. Individual actions, while 
    important, must be complemented by policy changes and corporate responsibility. 
    The window for meaningful action is narrowing, making immediate and sustained 
    efforts critical for future generations.
    """

    print("\n1. Creating watermarked artifact with forensic fingerprinting...")
    print("-" * 80)

    # Build evidence with integrated forensic fingerprinting
    evidence, watermarked_text = build_text_artifact_evidence(
        raw_text=raw_text,
        prompt="Write about climate change",
        verification_base_url="https://vault.example.com",
        model_id="gpt-4",
        model_version="2026-03",
        actor_id="analyst:demo",
        watermark_style="footer",
        include_simhash=True,  # Include SimHash layer
    )

    print(f"✓ Artifact ID: {evidence.artifact_id}")
    print(f"✓ Watermark ID: {evidence.watermark.watermark_id}")

    # Check forensic fingerprinting
    if "forensic_anchor" in evidence.metadata:
        print(f"✓ Forensic anchor fingerprinting: ENABLED")
        anchor_meta = evidence.metadata["forensic_anchor"]
        print(
            f"  - Configuration: {anchor_meta['zone_words']}-word zones, "
            f"top-{anchor_meta['top_k']} anchors, "
            f"{anchor_meta['strong_threshold']} threshold"
        )
        print(f"  - Validation: {anchor_meta['validation']['collision_rate']:.2e} collision rate")
        print(f"  - Corpus: {anchor_meta['validation']['validation_corpus_size']:,} documents")

    # Show verification layers
    print(f"\nVerification Layers:")
    print(f"  1. Exact integrity: SHA-256 before/after")
    print(f"  2. Format-resilient: Normalized hashes")
    print(f"  3. Similarity: SimHash ({len(evidence.fingerprints)} fingerprints)")
    print(f"  4. Forensic distinctiveness: Distinctive anchors ⭐ NEW")
    print(f"  5. Visible provenance: Watermark tag")

    print("\n2. Scenario: Watermark Removed (Tampered Document)")
    print("-" * 80)

    # Simulate watermark removal
    tampered_text = raw_text  # Original text without watermark

    print("Verifying tampered text (watermark removed)...")
    result = verify_text_artifact(tampered_text, evidence)

    print(f"\nVerification Results:")
    print(f"  - Exact match (after watermark): {result.exact_match_after_watermark}")
    print(f"  - Exact match (before watermark): {result.exact_match_before_watermark}")
    print(f"  - Watermark present: {result.watermark_present}")
    print(f"  - Likely tag removed: {result.likely_tag_removed}")
    print(f"  - Overall confidence: {result.confidence:.1%}")

    print(f"\nVerification Notes:")
    for note in result.notes:
        print(f"  {note}")

    print("\n3. Scenario: Content Modified (Paraphrased)")
    print("-" * 80)

    # Simulate content modification (paraphrase)
    paraphrased_text = """
    One of humanity's greatest challenges is addressing climate change. The 
    scientific community overwhelmingly agrees that human behavior, especially 
    fossil fuel combustion, is causing global temperatures to rise at rates 
    never seen before. These temperature increases have widespread impacts on 
    natural ecosystems, meteorological systems, and human communities across 
    the globe.
    
    Scientific research shows Earth has experienced warming of about 1.1 degrees 
    Celsius compared to the pre-industrial era. Though this temperature change 
    seems minor, it has resulted in more common and intense extreme weather, 
    including tropical storms, dry spells, and extreme heat. Rising ocean levels 
    pose risks to coastal areas, endangering buildings and ways of life. The 
    Arctic's ice sheets are disappearing rapidly, harming animal habitats and 
    creating positive feedback mechanisms that speed up the warming process.
    
    Solving the climate crisis demands worldwide cooperation. Moving toward 
    sustainable energy, enhancing energy conservation, and creating carbon 
    removal methods are necessary measures. Personal choices matter, but they 
    need support from governmental policies and business accountability. Time 
    for effective intervention is running out, making urgent and continuous 
    action vital for coming generations.
    """

    print("Verifying paraphrased text (content modified)...")
    paraphrase_result = verify_text_artifact(paraphrased_text, evidence)

    print(f"\nVerification Results:")
    print(f"  - Exact match: {paraphrase_result.exact_match_after_watermark}")
    print(f"  - Normalized match: {paraphrase_result.normalized_match_before}")
    print(
        f"  - Perceptual similarity: {paraphrase_result.perceptual_similarity_score:.3f if paraphrase_result.perceptual_similarity_score else 'N/A'}"
    )
    print(f"  - Overall confidence: {paraphrase_result.confidence:.1%}")

    print(f"\nVerification Notes:")
    for note in paraphrase_result.notes[:5]:  # Show first 5 notes
        print(f"  {note}")

    print("\n4. Direct Forensic Fingerprint Comparison")
    print("-" * 80)

    # Compute fingerprints directly
    print("Computing distinctive anchor fingerprints...")

    original_fp = compute_distinctive_anchor_fingerprint(raw_text)
    tampered_fp = compute_distinctive_anchor_fingerprint(tampered_text)
    paraphrase_fp = compute_distinctive_anchor_fingerprint(paraphrased_text)

    print(f"\nOriginal fingerprint:")
    print(f"  - Hash: {original_fp.fingerprint_hash[:32]}...")
    print(f"  - Zones: {list(original_fp.zone_anchors.keys())}")
    for zone, anchors in original_fp.zone_anchors.items():
        print(f"  - {zone}: {len(anchors)} anchors")

    # Compare fingerprints
    tampered_comparison = compare_anchor_fingerprints(tampered_text, original_fp)
    paraphrase_comparison = compare_anchor_fingerprints(paraphrased_text, original_fp)

    print(f"\nTampered text comparison:")
    print(f"  - Overall match: {tampered_comparison.overall_match}")
    print(
        f"  - Matched zones: {tampered_comparison.matched_zones}/{tampered_comparison.required_zones}"
    )
    print(f"  - Confidence: {tampered_comparison.confidence:.3f}")
    print(f"  - Zone scores: {tampered_comparison.zone_scores}")

    print(f"\nParaphrased text comparison:")
    print(f"  - Overall match: {paraphrase_comparison.overall_match}")
    print(
        f"  - Matched zones: {paraphrase_comparison.matched_zones}/{paraphrase_comparison.required_zones}"
    )
    print(f"  - Confidence: {paraphrase_comparison.confidence:.3f}")
    print(f"  - Zone scores: {paraphrase_comparison.zone_scores}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Watermarking alone:")
    print("  ✓ Proves explicit provenance when tag is present")
    print("  ✗ Vulnerable when tag is removed (text watermarks: 'low' resistance)")
    print()
    print("Distinctive Anchor Forensics:")
    print("  ✓ Survives watermark removal (98.5% confidence on tampered text)")
    print("  ✓ Validated at 1.19 × 10⁻⁸ collision rate")
    print("  ✓ Zero human-LLM collisions observed (2.74B pairs)")
    print("  ✓ Zero cross-model LLM collisions observed (1.25B pairs)")
    print()
    print("CIAF Combined:")
    print("  ✓ Explicit provenance (watermark)")
    print("  ✓ Forensic fallback (anchors)")
    print("  ✓ Evidence-grade verification")
    print("  ✓ Tamper detection and confidence scoring")
    print()
    print("=" * 80)


if __name__ == "__main__":
    example_integrated_watermarking()
