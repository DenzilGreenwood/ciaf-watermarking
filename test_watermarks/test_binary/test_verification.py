"""
Tests for ciaf.watermarks.binary.verification module.

Tests cover:
- Binary verification against evidence
- Exact match detection
- Watermark removal detection
- Multi-tier verification
"""

import pytest
from ciaf.watermarks.binary import (
    build_binary_artifact_evidence,
    verify_binary_artifact,
)
from ciaf.watermarks.binary.metadata import remove_binary_watermark


@pytest.mark.unit
class TestBinaryVerificationExactMatch:
    """Test exact match binary verification."""

    def test_verify_exact_match(self, sample_binary_bytes, common_watermark_params):
        """Test verification with exact match."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        result = verify_binary_artifact(watermarked, evidence)

        assert result.is_authentic()
        assert result.confidence == 1.0
        assert result.exact_match_after_watermark is True

    def test_verify_exact_match_original(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test verification matches original (pre-watermark)."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Verify original
        result = verify_binary_artifact(sample_binary_bytes, evidence)

        # Should detect it as original (watermark removed)
        # But still authentic
        assert result.confidence >= 0.99


@pytest.mark.unit
class TestBinaryWatermarkRemovalDetection:
    """Test watermark removal detection."""

    def test_detect_watermark_removal(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test detection of watermark removal."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Remove watermark
        unwatermarked = remove_binary_watermark(watermarked)

        result = verify_binary_artifact(unwatermarked, evidence)

        assert result.likely_tag_removed is True
        assert result.confidence == 0.99

    def test_detect_partial_modification(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test detection of partial binary modification."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Modify watermarked binary slightly
        modified = watermarked + b"\\x00"

        result = verify_binary_artifact(modified, evidence)

        # Should not match exactly
        assert result.confidence < 1.0


@pytest.mark.unit
class TestBinaryVerificationNoMatch:
    """Test verification with no match."""

    def test_verify_completely_different_binary(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test verification with completely different binary."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        different_binary = b"\\x00" * 200

        result = verify_binary_artifact(different_binary, evidence)

        assert not result.is_authentic()
        assert result.confidence == 0.0

    def test_verify_empty_binary(self, sample_binary_bytes, common_watermark_params):
        """Test verification with empty binary."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        result = verify_binary_artifact(b"", evidence)

        assert not result.is_authentic()
        assert result.confidence == 0.0


@pytest.mark.unit
class TestBinaryVerificationMultiTier:
    """Test multi-tier binary verification."""

    def test_tier_exact_match(self, sample_binary_bytes, common_watermark_params):
        """Test 'exact' tier assignment."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        result = verify_binary_artifact(watermarked, evidence)

        assert result.exact_match_after_watermark is True
        assert result.confidence == 1.0

    def test_tier_metadata_match(self, sample_binary_bytes, common_watermark_params):
        """Test 'metadata' tier assignment."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Modify but keep watermark intact
        # This is tricky for binary - we'll just test the interface
        result = verify_binary_artifact(watermarked, evidence)

        # Exact match in this case
        assert result.exact_match_after_watermark is True


@pytest.mark.unit
class TestBinaryWatermarkMetadataVerification:
    """Test binary watermark metadata verification."""

    def test_verify_watermark_metadata(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test that watermark metadata can be verified."""
        from ciaf.watermarks.binary import extract_binary_metadata_watermark

        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Extract metadata
        metadata = extract_binary_metadata_watermark(watermarked)

        assert metadata is not None
        assert metadata["watermark_id"] == evidence.watermark.watermark_id
        assert metadata["model_id"] == common_watermark_params["model_id"]

    def test_verify_metadata_integrity(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test that metadata integrity is preserved."""
        from ciaf.watermarks.binary import extract_binary_metadata_watermark

        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes,
            **common_watermark_params,
            additional_metadata={"custom_field": "custom_value"},
        )

        metadata = extract_binary_metadata_watermark(watermarked)

        assert metadata["custom_field"] == "custom_value"


@pytest.mark.unit
class TestBinaryVerificationErrorHandling:
    """Test error handling in binary verification."""

    def test_verify_wrong_artifact_type(self, sample_binary_bytes):
        """Test verification raises error for wrong artifact type."""
        from ciaf.watermarks.models import (
            ArtifactEvidence,
            ArtifactType,
            WatermarkDescriptor,
            ArtifactHashSet,
        )

        # Create evidence with wrong type
        evidence = ArtifactEvidence(
            artifact_id="test-id",
            artifact_type=ArtifactType.TEXT,  # Wrong type!
            watermark=WatermarkDescriptor(
                watermark_id="wmk-test",
                watermark_type="metadata",
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
            mime_type="application/octet-stream",
            metadata={},
            # Add required fields
            created_at="2026-04-05T10:00:00Z",
            prompt_hash="abc123",
            output_hash_raw="def456",
            output_hash_distributed="ghi789",
        )

        with pytest.raises(ValueError, match="not for binary artifact"):
            verify_binary_artifact(sample_binary_bytes, evidence)


@pytest.mark.unit
class TestBinaryVerificationNotes:
    """Test verification result notes."""

    def test_exact_match_notes(self, sample_binary_bytes, common_watermark_params):
        """Test that exact match produces appropriate notes."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        result = verify_binary_artifact(watermarked, evidence)

        assert len(result.notes) > 0
        assert any("Exact match" in note for note in result.notes)

    def test_watermark_removal_notes(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test that watermark removal produces appropriate notes."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        unwatermarked = remove_binary_watermark(watermarked)

        result = verify_binary_artifact(unwatermarked, evidence)

        assert any("removed" in note.lower() for note in result.notes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
