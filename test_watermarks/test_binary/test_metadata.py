"""
Tests for ciaf_watermarks.binary module.

Tests cover:
- Binary metadata block watermarking
- Binary verification
- File type detection
- Watermark removal
"""

import pytest
from ciaf_watermarks.binary import (
    apply_binary_metadata_watermark,
    extract_binary_metadata_watermark,
    has_binary_watermark,
)
from ciaf_watermarks.binary.metadata import remove_binary_watermark


@pytest.mark.unit
class TestBinaryMetadataWatermarking:
    """Test binary metadata watermarking."""

    def test_apply_binary_watermark(self, sample_binary_bytes):
        """Test applying binary watermark."""
        watermarked = apply_binary_metadata_watermark(
            binary_bytes=sample_binary_bytes,
            watermark_id="wmk-test-123",
            model_id="model-test",
            timestamp="2026-04-05T10:00:00Z",
        )

        assert isinstance(watermarked, bytes)
        assert len(watermarked) > len(sample_binary_bytes)
        assert b"CIAF\x00\x01" in watermarked

    def test_extract_binary_watermark(self, sample_binary_bytes):
        """Test extracting binary watermark metadata."""
        watermarked = apply_binary_metadata_watermark(
            binary_bytes=sample_binary_bytes,
            watermark_id="wmk-extract-123",
            model_id="model-test",
            timestamp="2026-04-05T10:00:00Z",
        )

        metadata = extract_binary_metadata_watermark(watermarked)

        assert metadata is not None
        assert metadata["watermark_id"] == "wmk-extract-123"
        assert metadata["model_id"] == "model-test"

    def test_has_binary_watermark_positive(self, sample_binary_bytes):
        """Test detecting watermark presence."""
        watermarked = apply_binary_metadata_watermark(
            binary_bytes=sample_binary_bytes,
            watermark_id="wmk-test",
            model_id="model-test",
            timestamp="2026-04-05T10:00:00Z",
        )

        assert has_binary_watermark(watermarked) is True

    def test_has_binary_watermark_negative(self, sample_binary_bytes):
        """Test detecting no watermark."""
        assert has_binary_watermark(sample_binary_bytes) is False

    def test_remove_binary_watermark(self, sample_binary_bytes):
        """Test removing binary watermark."""
        watermarked = apply_binary_metadata_watermark(
            binary_bytes=sample_binary_bytes,
            watermark_id="wmk-remove-test",
            model_id="model-test",
            timestamp="2026-04-05T10:00:00Z",
        )

        unwatermarked = remove_binary_watermark(watermarked)

        # Should match original
        assert unwatermarked == sample_binary_bytes
        assert has_binary_watermark(unwatermarked) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
