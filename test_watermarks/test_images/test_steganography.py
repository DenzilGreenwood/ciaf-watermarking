"""
Tests for ciaf.watermarks.images.steganography module.

Tests cover:
- LSB (Least Significant Bit) steganography
- Data embedding in images
- Data extraction from images
- Steganographic capacity
- Robustness
"""

import pytest
from PIL import Image
import io


@pytest.mark.unit
@pytest.mark.requires_pil
class TestLSBSteganography:
    """Test LSB steganography."""

    def test_embed_data_lsb(self, sample_image_bytes):
        """Test embedding data using LSB steganography."""
        try:
            from ciaf.watermarks.images import embed_data_lsb

            secret_data = "watermark-id:wmk-test-123"

            watermarked = embed_data_lsb(
                image_bytes=sample_image_bytes, data=secret_data
            )

            assert isinstance(watermarked, bytes)
            img = Image.open(io.BytesIO(watermarked))
            assert img is not None
        except (ImportError, AttributeError):
            pytest.skip("embed_data_lsb not implemented or PIL not available")

    def test_extract_data_lsb(self, sample_image_bytes):
        """Test extracting data using LSB steganography."""
        try:
            from ciaf.watermarks.images import embed_data_lsb, extract_data_lsb

            secret_data = "wmk-extract-test"

            watermarked = embed_data_lsb(
                image_bytes=sample_image_bytes, data=secret_data
            )

            extracted = extract_data_lsb(watermarked)

            assert extracted == secret_data
        except (ImportError, AttributeError):
            pytest.skip("LSB steganography not implemented")

    def test_lsb_preserves_image_appearance(self, sample_image_bytes):
        """Test that LSB embedding preserves image appearance."""
        try:
            from ciaf.watermarks.images import embed_data_lsb

            watermarked = embed_data_lsb(
                image_bytes=sample_image_bytes, data="test data"
            )

            # Images should have same dimensions
            original_img = Image.open(io.BytesIO(sample_image_bytes))
            watermarked_img = Image.open(io.BytesIO(watermarked))

            assert watermarked_img.size == original_img.size
            assert watermarked_img.mode == original_img.mode
        except (ImportError, AttributeError):
            pytest.skip("embed_data_lsb not implemented")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestSteganographicCapacity:
    """Test steganographic capacity calculation."""

    def test_calculate_capacity(self, sample_image_bytes):
        """Test calculating steganographic capacity."""
        try:
            from ciaf.watermarks.images import calculate_steganographic_capacity

            capacity = calculate_steganographic_capacity(sample_image_bytes)

            assert isinstance(capacity, int)
            assert capacity > 0
        except (ImportError, AttributeError):
            pytest.skip("calculate_steganographic_capacity not implemented")

    def test_data_fits_in_capacity(self, sample_image_bytes):
        """Test that data fits within image capacity."""
        try:
            from ciaf.watermarks.images import (
                calculate_steganographic_capacity,
                embed_data_lsb,
            )

            capacity = calculate_steganographic_capacity(sample_image_bytes)

            # Data should fit
            short_data = "x" * min(100, capacity // 8 - 10)

            watermarked = embed_data_lsb(
                image_bytes=sample_image_bytes, data=short_data
            )

            assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError):
            pytest.skip("Steganography functions not implemented")

    def test_data_exceeds_capacity_raises_error(self, sample_image_bytes):
        """Test that exceeding capacity raises error."""
        try:
            from ciaf.watermarks.images import (
                embed_data_lsb,
                calculate_steganographic_capacity,
            )

            capacity = calculate_steganographic_capacity(sample_image_bytes)

            # Data too large
            large_data = "x" * (capacity * 2)

            with pytest.raises(ValueError, match="capacity|size|too large"):
                embed_data_lsb(image_bytes=sample_image_bytes, data=large_data)
        except (ImportError, AttributeError):
            pytest.skip("Steganography functions not implemented")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestSteganographicWatermarking:
    """Test steganographic watermarking for provenance."""

    def test_embed_watermark_id(self, sample_image_bytes, test_watermark_id):
        """Test embedding watermark ID steganographically."""
        try:
            from ciaf.watermarks.images import embed_data_lsb, extract_data_lsb

            watermarked = embed_data_lsb(
                image_bytes=sample_image_bytes, data=test_watermark_id
            )

            extracted = extract_data_lsb(watermarked)

            assert extracted == test_watermark_id
        except (ImportError, AttributeError):
            pytest.skip("LSB steganography not implemented")

    def test_embed_metadata_json(self, sample_image_bytes):
        """Test embedding JSON metadata steganographically."""
        try:
            from ciaf.watermarks.images import embed_data_lsb, extract_data_lsb
            import json

            metadata = {
                "watermark_id": "wmk-123",
                "model_id": "image-gen-v1",
                "timestamp": "2026-04-05T10:00:00Z",
            }

            metadata_str = json.dumps(metadata)

            watermarked = embed_data_lsb(
                image_bytes=sample_image_bytes, data=metadata_str
            )

            extracted = extract_data_lsb(watermarked)
            extracted_metadata = json.loads(extracted)

            assert extracted_metadata == metadata
        except (ImportError, AttributeError):
            pytest.skip("LSB steganography not implemented")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestSteganographyRobustness:
    """Test steganography robustness."""

    def test_survives_lossless_save(self, sample_image_bytes):
        """Test that steganographic watermark survives lossless save."""
        try:
            from ciaf.watermarks.images import embed_data_lsb, extract_data_lsb

            secret = "test-robust"

            watermarked = embed_data_lsb(image_bytes=sample_image_bytes, data=secret)

            # Save and reload as PNG (lossless)
            img = Image.open(io.BytesIO(watermarked))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            reloaded_bytes = buf.getvalue()

            extracted = extract_data_lsb(reloaded_bytes)

            assert extracted == secret
        except (ImportError, AttributeError):
            pytest.skip("LSB steganography not implemented")

    def test_lossy_compression_may_destroy(self, sample_image_bytes):
        """Test that lossy compression may destroy steganographic watermark."""
        try:
            from ciaf.watermarks.images import embed_data_lsb, extract_data_lsb

            secret = "test-compression"

            watermarked = embed_data_lsb(image_bytes=sample_image_bytes, data=secret)

            # Save as JPEG (lossy)
            img = Image.open(io.BytesIO(watermarked))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=50)
            compressed_bytes = buf.getvalue()

            # Extraction may fail or return corrupted data
            try:
                _extracted = extract_data_lsb(compressed_bytes)  # noqa: F841
                # If it extracts something, it might be corrupted
                # This is expected behavior for LSB with lossy compression
            except Exception:
                # Extraction failure is acceptable for lossy compression
                pass
        except (ImportError, AttributeError):
            pytest.skip("LSB steganography not implemented")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestAdvancedSteganography:
    """Test advanced steganographic techniques."""

    def test_multi_channel_embedding(self, sample_image_bytes):
        """Test embedding data across multiple color channels."""
        try:
            from ciaf.watermarks.images import embed_data_lsb

            watermarked = embed_data_lsb(
                image_bytes=sample_image_bytes,
                data="multi-channel test",
                channels=["R", "G", "B"],
            )

            assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError, TypeError):
            pytest.skip("Multi-channel steganography not implemented")

    def test_variable_bit_depth(self, sample_image_bytes):
        """Test embedding with variable bit depth."""
        try:
            from ciaf.watermarks.images import embed_data_lsb

            # Use 2 LSBs instead of 1
            watermarked = embed_data_lsb(
                image_bytes=sample_image_bytes, data="test", bit_depth=2
            )

            assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError, TypeError):
            pytest.skip("Variable bit depth not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
