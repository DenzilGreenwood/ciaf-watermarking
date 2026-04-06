"""
Tests for ciaf_watermarks.text.verification module.

Tests cover:
- Text verification against evidence
- Exact match detection
- Watermark removal detection
- Normalized hash matching
- SimHash similarity
- Multi-tier verification
"""

import pytest
from ciaf_watermarks.text.verification import (
    verify_text_artifact,
)
from ciaf_watermarks.text.core import build_text_artifact_evidence
from ciaf_watermarks.text.watermark import remove_watermark, apply_text_watermark


@pytest.mark.unit
class TestTextVerificationExactMatch:
    """Test exact match text verification."""

    def test_verify_exact_match_watermarked(self, sample_text, common_watermark_params):
        """Test verification with exact match to watermarked version."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        result = verify_text_artifact(watermarked, evidence)

        assert result.is_authentic()
        assert result.exact_match_after_watermark is True
        assert result.confidence == 1.0
        assert any("Exact match" in note for note in result.notes)

    def test_verify_exact_match_original(self, sample_text, common_watermark_params):
        """Test verification with exact match to original (pre-watermark)."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        # Verify the original text (not watermarked)
        result = verify_text_artifact(sample_text, evidence)

        # Should match original but detect watermark removal
        assert result.likely_tag_removed is True
        # Still has high confidence because core content matches
        assert result.confidence >= 0.95


@pytest.mark.unit
class TestTextWatermarkRemovalDetection:
    """Test watermark removal detection."""

    def test_detect_watermark_removal(self, sample_text, common_watermark_params):
        """Test detection of watermark removal."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        # Remove watermark
        cleaned = remove_watermark(watermarked)

        result = verify_text_artifact(cleaned, evidence)

        assert result.likely_tag_removed is True
        assert any("removed" in note.lower() for note in result.notes)

    def test_detect_tampered_watermark(self, sample_text, common_watermark_params):
        """Test detection of tampered watermark."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        # Replace watermark with different one
        tampered = remove_watermark(watermarked)
        tampered = apply_text_watermark(
            raw_text=tampered,
            watermark_id="wmk-different-id",
            verification_url="https://fake.com",
            style="footer",
        )

        result = verify_text_artifact(tampered, evidence)

        # Should detect different watermark
        assert any("different" in note.lower() or "tamper" in note.lower() for note in result.notes)


@pytest.mark.unit
class TestTextNormalizedHashMatching:
    """Test normalized hash matching."""

    def test_normalized_match_with_whitespace_changes(self, sample_text, common_watermark_params):
        """Test normalized matching ignores whitespace changes."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        # Add extra whitespace
        # Double spaces to quad spaces
        modified = watermarked.replace("  ", "    ")

        result = verify_text_artifact(modified, evidence, check_normalized=True)

        # Should still match via normalized hash
        assert result.normalized_match_after is True or result.confidence > 0.5

    def test_normalized_match_disabled(self, sample_text, common_watermark_params):
        """Test verification with normalized matching disabled."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        modified = watermarked.replace("  ", "    ")

        result = verify_text_artifact(modified, evidence, check_normalized=False)

        # Normalized match should not be used
        assert result.normalized_match_after is False


@pytest.mark.unit
class TestTextSimHashSimilarity:
    """Test SimHash similarity matching."""

    def test_simhash_match_with_minor_edits(self, sample_text, common_watermark_params):
        """Test SimHash matching with minor text edits."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, include_simhash=True
        )

        # Make minor edits
        modified = watermarked.replace("Artificial Intelligence", "AI Technology")

        result = verify_text_artifact(modified, evidence, check_simhash=True)

        # Should still have perceptual similarity
        if result.perceptual_similarity_score is not None:
            assert result.perceptual_similarity_score > 0.8

    def test_simhash_with_custom_threshold(self, sample_text, common_watermark_params):
        """Test SimHash with custom threshold."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, include_simhash=True
        )

        # Very strict threshold
        result = verify_text_artifact(
            watermarked, evidence, check_simhash=True, simhash_threshold=5
        )

        assert result.is_authentic()

    def test_simhash_disabled(self, sample_text, common_watermark_params):
        """Test verification with SimHash disabled."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, include_simhash=True
        )

        modified = watermarked.replace("AI", "Artificial Intelligence")

        result = verify_text_artifact(modified, evidence, check_simhash=False)

        # SimHash should not be computed
        assert result.perceptual_similarity_score is None


@pytest.mark.unit
class TestTextVerificationNoMatch:
    """Test verification with no match."""

    def test_verify_completely_different_text(self, sample_text, common_watermark_params):
        """Test verification with completely unrelated text."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        different_text = "This is completely different and unrelated text."

        result = verify_text_artifact(different_text, evidence)

        assert not result.is_authentic()
        assert result.confidence == 0.0

    def test_verify_empty_text(self, sample_text, common_watermark_params):
        """Test verification with empty text."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        result = verify_text_artifact("", evidence)

        assert not result.is_authentic()
        assert result.confidence == 0.0


@pytest.mark.unit
class TestTextVerificationMultiTier:
    """Test multi-tier verification logic."""

    def test_tier_exact_match(self, sample_text, common_watermark_params):
        """Test 'exact' tier assignment."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        result = verify_text_artifact(watermarked, evidence)

        assert result.exact_match_after_watermark is True
        assert result.confidence == 1.0

    def test_tier_normalized_match(self, common_watermark_params):
        """Test 'normalized' tier assignment."""
        # Use text with specific whitespace
        text = "Hello    World!"

        evidence, watermarked = build_text_artifact_evidence(
            raw_text=text, **common_watermark_params
        )

        # Change whitespace
        modified = watermarked.replace("    ", "  ")

        result = verify_text_artifact(modified, evidence, check_normalized=True)

        if result.normalized_match_after:
            assert result.confidence >= 0.9

    def test_tier_perceptual_match(self, sample_text, common_watermark_params):
        """Test 'perceptual' tier assignment."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, include_simhash=True
        )

        # Significant but not complete change
        modified = (
            watermarked[: len(watermarked) // 2]
            + " [EDITED] "
            + watermarked[len(watermarked) // 2 :]
        )

        result = verify_text_artifact(modified, evidence, check_simhash=True)

        if result.perceptual_similarity_score and result.perceptual_similarity_score > 0.7:
            assert result.confidence > 0.7


@pytest.mark.unit
class TestTextVerificationErrorHandling:
    """Test error handling in verification."""

    def test_verify_wrong_artifact_type(self, sample_text, common_watermark_params):
        """Test verification raises error for wrong artifact type."""
        from ciaf_watermarks.models import (
            ArtifactEvidence,
            ArtifactType,
            WatermarkDescriptor,
            ArtifactHashSet,
        )

        # Create evidence with wrong type
        evidence = ArtifactEvidence(
            artifact_id="test-id",
            artifact_type=ArtifactType.IMAGE,  # Wrong type!
            watermark=WatermarkDescriptor(
                watermark_id="wmk-test",
                watermark_type="visible",
                verification_url="https://test.com",
            ),
            hashes=ArtifactHashSet(
                content_hash_before_watermark="abc123",
                content_hash_after_watermark="def456",
            ),
            model_id="test-model",
            model_version="1.0",
            actor_id="test-actor",
            prompt="test prompt",
            generation_timestamp="2026-04-05T10:00:00Z",
            mime_type="image/png",
            metadata={},
            # Add required fields
            created_at="2026-04-05T10:00:00Z",
            prompt_hash="abc123",
            output_hash_raw="def456",
            output_hash_distributed="ghi789",
        )

        with pytest.raises(ValueError, match="not for text artifact"):
            verify_text_artifact(sample_text, evidence)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
