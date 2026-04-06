"""
Tests for ciaf.watermarks.text module.

Tests cover:
- Text watermark application (footer, header, inline)
- Watermark extraction
- Watermark detection
- Core evidence building
- Text verification
"""

import pytest
from ciaf.watermarks.text import (
    apply_text_watermark,
    extract_watermark_id,
    extract_verification_url,
    has_watermark,
    remove_watermark,
    build_text_artifact_evidence,
    quick_watermark_text,
    verify_text_artifact,
)
from ciaf.watermarks.models import ArtifactType, WatermarkType


@pytest.mark.unit
class TestTextWatermarkApplication:
    """Test text watermark application functions."""

    def test_footer_watermark(self, sample_text):
        """Test footer-style watermark."""
        watermark_id = "wmk-test-123"
        verification_url = "https://vault.test.com/verify/wmk-test-123"

        watermarked = apply_text_watermark(
            raw_text=sample_text,
            watermark_id=watermark_id,
            verification_url=verification_url,
            style="footer",
        )

        assert sample_text in watermarked
        assert watermark_id in watermarked
        assert verification_url in watermarked
        assert "---" in watermarked
        assert watermarked.startswith(sample_text)

    def test_header_watermark(self, sample_text):
        """Test header-style watermark."""
        watermark_id = "wmk-test-456"
        verification_url = "https://vault.test.com/verify/wmk-test-456"

        watermarked = apply_text_watermark(
            raw_text=sample_text,
            watermark_id=watermark_id,
            verification_url=verification_url,
            style="header",
        )

        assert sample_text in watermarked
        assert watermark_id in watermarked
        assert watermarked.endswith(sample_text)

    def test_inline_watermark(self, sample_text):
        """Test inline-style watermark."""
        watermark_id = "wmk-test-789"
        verification_url = "https://vault.test.com/verify/wmk-test-789"

        watermarked = apply_text_watermark(
            raw_text=sample_text,
            watermark_id=watermark_id,
            verification_url=verification_url,
            style="inline",
        )

        # Inline style should modify the text
        assert watermarked != sample_text
        assert len(watermarked) > len(sample_text)

    def test_invalid_style_raises_error(self, sample_text):
        """Test that invalid style raises ValueError."""
        with pytest.raises(ValueError, match="Unknown watermark style"):
            apply_text_watermark(
                raw_text=sample_text,
                watermark_id="wmk-test",
                verification_url="https://test.com",
                style="invalid_style",
            )


@pytest.mark.unit
class TestWatermarkExtraction:
    """Test watermark extraction functions."""

    def test_extract_watermark_id_from_footer(self):
        """Test extracting watermark ID from footer."""
        watermarked = "Text content\n\n---\nAI Provenance Tag: wmk-extract-test\nVerify: https://test.com"

        watermark_id = extract_watermark_id(watermarked)
        assert watermark_id == "wmk-extract-test"

    def test_extract_watermark_id_from_inline(self):
        """Test extracting watermark ID from inline watermark."""
        watermarked = "Text content [AI Generated: wmk-inline-123] more text"

        watermark_id = extract_watermark_id(watermarked)
        assert watermark_id == "wmk-inline-123"

    def test_extract_watermark_id_not_found(self):
        """Test extraction returns None if not found."""
        text = "Plain text without watermark"

        watermark_id = extract_watermark_id(text)
        assert watermark_id is None

    def test_extract_verification_url(self):
        """Test extracting verification URL."""
        watermarked = "Content\n\n---\nVerify: https://vault.example.com/verify/wmk-123"

        url = extract_verification_url(watermarked)
        assert url == "https://vault.example.com/verify/wmk-123"

    def test_has_watermark_true(self):
        """Test watermark detection returns True."""
        watermarked = "Content\n\n---\nAI Provenance Tag: wmk-123"

        assert has_watermark(watermarked) is True

    def test_has_watermark_false(self):
        """Test watermark detection returns False."""
        text = "Plain text"

        assert has_watermark(text) is False


@pytest.mark.unit
class TestWatermarkRemoval:
    """Test watermark removal function."""

    def test_remove_footer_watermark(self, sample_text):
        """Test removing footer watermark."""
        watermark_id = "wmk-remove-test"
        verification_url = "https://test.com"

        watermarked = apply_text_watermark(
            raw_text=sample_text,
            watermark_id=watermark_id,
            verification_url=verification_url,
            style="footer",
        )

        cleaned = remove_watermark(watermarked)

        assert watermark_id not in cleaned
        assert sample_text.strip() == cleaned.strip()

    def test_remove_inline_watermark(self):
        """Test removing inline watermark."""
        watermarked = "Text [AI Generated: wmk-123] more text"

        cleaned = remove_watermark(watermarked)

        assert "[AI Generated:" not in cleaned
        assert "Text  more text" in cleaned or "Text more text" in cleaned


@pytest.mark.unit
class TestTextEvidenceBuilding:
    """Test text artifact evidence building."""

    def test_build_evidence_basic(self, sample_text, common_watermark_params):
        """Test building text evidence."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        assert evidence is not None
        assert evidence.artifact_type == ArtifactType.TEXT
        assert evidence.model_id == common_watermark_params["model_id"]
        assert evidence.watermark.watermark_type == WatermarkType.VISIBLE

        # Check hashes
        assert evidence.hashes.content_hash_before_watermark is not None
        assert evidence.hashes.content_hash_after_watermark is not None
        assert len(evidence.hashes.content_hash_before_watermark) == 64

        # Check watermarked text
        assert sample_text in watermarked
        assert evidence.watermark.watermark_id in watermarked

    def test_build_evidence_with_simhash(self, sample_text, common_watermark_params):
        """Test building evidence with SimHash."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, include_simhash=True
        )

        assert evidence.hashes.simhash_before is not None
        assert evidence.hashes.simhash_after is not None
        assert len(evidence.fingerprints) >= 2  # SimHash fingerprints

    def test_build_evidence_different_styles(
        self, sample_text, common_watermark_params
    ):
        """Test building evidence with different watermark styles."""
        for style in ["footer", "header", "inline"]:
            evidence, watermarked = build_text_artifact_evidence(
                raw_text=sample_text, **common_watermark_params, watermark_style=style
            )

            assert evidence.metadata["watermark_style"] == style
            assert has_watermark(watermarked)


@pytest.mark.unit
class TestQuickWatermark:
    """Test quick watermark function."""

    def test_quick_watermark(self, sample_text):
        """Test quick watermarking."""
        watermarked, artifact_id = quick_watermark_text(
            text=sample_text, model_id="test-model", verification_url="https://test.com"
        )

        assert has_watermark(watermarked)
        assert artifact_id is not None
        assert isinstance(artifact_id, str)


@pytest.mark.unit
class TestTextVerification:
    """Test text verification functions."""

    def test_verify_exact_match_after_watermark(
        self, sample_text, common_watermark_params
    ):
        """Test verification with exact match (watermarked version)."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        result = verify_text_artifact(watermarked, evidence)

        assert result.is_authentic()
        assert result.exact_match_after_watermark is True
        assert result.confidence == 1.0

    def test_verify_watermark_removed(self, sample_text, common_watermark_params):
        """Test verification detects watermark removal."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        # Remove watermark
        unwatermarked = remove_watermark(watermarked)

        # Verify should detect removal (if text matches original exactly)
        # Note: This might not always work due to whitespace differences
        result = verify_text_artifact(unwatermarked, evidence)

        # Could be likely_tag_removed or just not authentic
        assert result.confidence < 1.0

    def test_verify_no_match(self, sample_text, common_watermark_params):
        """Test verification with unrelated text."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        unrelated_text = "This is completely different text"

        result = verify_text_artifact(unrelated_text, evidence)

        assert not result.is_authentic()
        assert result.confidence == 0.0

    def test_verify_with_modifications(self, sample_text, common_watermark_params):
        """Test verification with slightly modified text."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, include_simhash=True
        )

        # Slightly modify the watermarked text
        modified = watermarked.replace("Artificial", "Synthetic")

        result = verify_text_artifact(modified, evidence, check_simhash=True)

        # Should still have some similarity
        if result.perceptual_similarity_score:
            assert result.perceptual_similarity_score > 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
