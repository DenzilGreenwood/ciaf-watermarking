"""
Tests for ciaf_watermarks.text.core module.

Tests cover:
- Text artifact evidence building
- Hash computation
- Fingerprint generation
- Metadata handling
"""

import pytest
from ciaf_watermarks.text.core import (
    build_text_artifact_evidence,
)
from ciaf_watermarks.models import ArtifactType, WatermarkType
from ciaf_watermarks.text import has_watermark


@pytest.mark.unit
class TestTextArtifactEvidenceBuilding:
    """Test text artifact evidence building."""

    def test_build_evidence_basic(self, sample_text, common_watermark_params):
        """Test basic evidence building."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        assert evidence is not None
        assert evidence.artifact_type == ArtifactType.TEXT
        assert evidence.model_id == common_watermark_params["model_id"]
        assert evidence.watermark.watermark_type == WatermarkType.VISIBLE

        # Check IDs
        assert evidence.artifact_id is not None
        assert evidence.watermark.watermark_id is not None

        # Check watermarked text
        assert isinstance(watermarked, str)
        assert has_watermark(watermarked)
        assert sample_text in watermarked

    def test_build_evidence_with_simhash(self, sample_text, common_watermark_params):
        """Test evidence building with SimHash enabled."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, include_simhash=True
        )

        # Check SimHash values
        assert evidence.hashes.simhash_before is not None
        assert evidence.hashes.simhash_after is not None
        assert isinstance(evidence.hashes.simhash_before, str)
        assert isinstance(evidence.hashes.simhash_after, str)

        # Check fingerprints
        assert len(evidence.fingerprints) >= 2
        simhash_fingerprints = [f for f in evidence.fingerprints if f.algorithm == "simhash"]
        assert len(simhash_fingerprints) >= 2

    def test_build_evidence_without_simhash(self, sample_text, common_watermark_params):
        """Test evidence building with SimHash disabled."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, include_simhash=False
        )

        # SimHash should not be present
        assert evidence.hashes.simhash_before is None
        assert evidence.hashes.simhash_after is None

    def test_build_evidence_footer_style(self, sample_text, common_watermark_params):
        """Test evidence building with footer watermark style."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, watermark_style="footer"
        )

        assert evidence.metadata["watermark_style"] == "footer"
        # Footer watermark appears at end
        assert watermarked.startswith(sample_text.split("\n")[0])

    def test_build_evidence_header_style(self, sample_text, common_watermark_params):
        """Test evidence building with header watermark style."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, watermark_style="header"
        )

        assert evidence.metadata["watermark_style"] == "header"
        # Header watermark appears at start
        assert watermarked.endswith(sample_text.split("\n")[-1])

    def test_build_evidence_inline_style(self, sample_text, common_watermark_params):
        """Test evidence building with inline watermark style."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params, watermark_style="inline"
        )

        assert evidence.metadata["watermark_style"] == "inline"
        # Check for inline style marker (may vary by implementation)
        assert watermarked != sample_text  # Should be modified

    def test_build_evidence_additional_metadata(self, sample_text, common_watermark_params):
        """Test evidence building with additional metadata."""
        additional = {"temperature": 0.7, "max_tokens": 1000, "custom_field": "value"}

        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text,
            **common_watermark_params,
            additional_metadata=additional,
        )

        # Check additional metadata is preserved
        assert evidence.metadata["temperature"] == 0.7
        assert evidence.metadata["max_tokens"] == 1000
        assert evidence.metadata["custom_field"] == "value"


@pytest.mark.unit
class TestTextHashComputation:
    """Test text hash computation."""

    def test_hash_computation(self, sample_text, common_watermark_params):
        """Test that hashes are properly computed."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        # All hash fields should be populated
        assert evidence.hashes.content_hash_before_watermark is not None
        assert evidence.hashes.content_hash_after_watermark is not None
        assert evidence.hashes.normalized_hash_before is not None
        assert evidence.hashes.normalized_hash_after is not None

        # Hashes should be different before and after watermarking
        assert (
            evidence.hashes.content_hash_before_watermark
            != evidence.hashes.content_hash_after_watermark
        )

    def test_hash_format(self, sample_text, common_watermark_params):
        """Test that hashes are in correct format."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        # SHA256 hashes should be 64 hex characters
        assert len(evidence.hashes.content_hash_before_watermark) == 64
        assert len(evidence.hashes.content_hash_after_watermark) == 64
        assert all(c in "0123456789abcdef" for c in evidence.hashes.content_hash_before_watermark)

    def test_normalized_hash_stability(self, common_watermark_params):
        """Test that normalized hashes are stable for similar text."""
        text1 = "Hello World!"
        text2 = "Hello  World!"  # Extra space

        evidence1, _ = build_text_artifact_evidence(raw_text=text1, **common_watermark_params)

        evidence2, _ = build_text_artifact_evidence(raw_text=text2, **common_watermark_params)

        # Normalized hashes should be identical (ignoring whitespace)
        assert evidence1.hashes.normalized_hash_before == evidence2.hashes.normalized_hash_before


@pytest.mark.unit
class TestTextEvidenceMetadata:
    """Test text evidence metadata."""

    def test_evidence_has_required_metadata(self, sample_text, common_watermark_params):
        """Test that evidence has all required metadata fields."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        # Required metadata fields
        assert "watermark_style" in evidence.metadata
        assert "text_length_before" in evidence.metadata
        assert "text_length_after" in evidence.metadata

    def test_text_length_metadata(self, sample_text, common_watermark_params):
        """Test text length metadata is accurate."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        assert evidence.metadata["text_length_before"] == len(sample_text)
        assert evidence.metadata["text_length_after"] == len(watermarked)
        # Watermark overhead is the difference
        assert len(watermarked) > len(sample_text)

    def test_mime_type(self, sample_text, common_watermark_params):
        """Test that MIME type is set correctly."""
        evidence, watermarked = build_text_artifact_evidence(
            raw_text=sample_text, **common_watermark_params
        )

        assert evidence.mime_type == "text/plain"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
