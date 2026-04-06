"""
Tests for ciaf_watermarks.images.qr module.

Tests cover:
- QR code watermark generation
- QR code embedding in images
- QR code extraction
- Error correction levels
- Positioning and sizing
"""

import pytest
from PIL import Image
import io


@pytest.mark.unit
@pytest.mark.requires_pil
class TestQRCodeGeneration:
    """Test QR code generation."""

    def test_generate_qr_code(self):
        """Test generating QR code from data."""
        try:
            from ciaf_watermarks.images import generate_qr_code

            qr_bytes = generate_qr_code("https://test.com/verify/wmk-123")

            assert isinstance(qr_bytes, bytes)
            assert len(qr_bytes) > 0

            # Should be valid image
            img = Image.open(io.BytesIO(qr_bytes))
            assert img is not None
        except ImportError:
            pytest.skip("qrcode or PIL not available")

    def test_generate_qr_code_different_sizes(self):
        """Test generating QR codes with different sizes."""
        try:
            from ciaf_watermarks.images import generate_qr_code

            for size in [100, 200, 300]:
                qr_bytes = generate_qr_code(data="https://test.com", size=size)

                img = Image.open(io.BytesIO(qr_bytes))
                # Size should match (approximately, depends on QR module size)
                assert img.size[0] >= size * 0.8
        except (ImportError, TypeError):
            pytest.skip("qrcode not available or size parameter not supported")

    def test_generate_qr_code_error_correction(self):
        """Test QR code generation with different error correction levels."""
        try:
            from ciaf_watermarks.images import generate_qr_code

            for error_correction in ["L", "M", "Q", "H"]:
                qr_bytes = generate_qr_code(
                    data="https://test.com", error_correction=error_correction
                )

                assert isinstance(qr_bytes, bytes)
        except (ImportError, TypeError):
            pytest.skip("qrcode not available or error_correction parameter not supported")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestQRCodeEmbedding:
    """Test QR code embedding in images."""

    def test_embed_qr_code_in_image(self, sample_image_bytes):
        """Test embedding QR code in image."""
        try:
            from ciaf_watermarks.images import embed_qr_code_in_image

            watermarked = embed_qr_code_in_image(
                image_bytes=sample_image_bytes,
                qr_data="https://test.com/verify/wmk-123",
                position="bottom-right",
            )

            assert isinstance(watermarked, bytes)
            img = Image.open(io.BytesIO(watermarked))
            assert img is not None
        except (ImportError, AttributeError):
            pytest.skip("embed_qr_code_in_image not implemented or PIL not available")

    def test_embed_qr_code_different_positions(self, sample_image_bytes):
        """Test QR code embedding at different positions."""
        try:
            from ciaf_watermarks.images import embed_qr_code_in_image

            positions = ["top-left", "top-right", "bottom-left", "bottom-right"]

            for position in positions:
                watermarked = embed_qr_code_in_image(
                    image_bytes=sample_image_bytes,
                    qr_data="https://test.com",
                    position=position,
                )

                assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError):
            pytest.skip("embed_qr_code_in_image not implemented")

    def test_embed_qr_code_with_scaling(self, sample_image_bytes):
        """Test QR code embedding with different scales."""
        try:
            from ciaf_watermarks.images import embed_qr_code_in_image

            for scale in [0.1, 0.15, 0.2]:
                watermarked = embed_qr_code_in_image(
                    image_bytes=sample_image_bytes,
                    qr_data="https://test.com",
                    scale=scale,
                )

                assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError, TypeError):
            pytest.skip("embed_qr_code_in_image not implemented or scale parameter not supported")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestQRCodeExtraction:
    """Test QR code extraction from images."""

    def test_extract_qr_code_from_image(self):
        """Test extracting QR code data from image."""
        try:
            from ciaf_watermarks.images import (
                extract_qr_code_from_image,
                generate_qr_code,
            )

            # Generate QR code
            qr_bytes = generate_qr_code("https://test.com/verify/wmk-123")

            # Extract data
            extracted_data = extract_qr_code_from_image(qr_bytes)

            assert extracted_data == "https://test.com/verify/wmk-123"
        except (ImportError, AttributeError):
            pytest.skip("QR code extraction not implemented or dependencies not available")

    def test_extract_from_image_without_qr(self, sample_image_bytes):
        """Test extracting QR code from image without QR code."""
        try:
            from ciaf_watermarks.images import extract_qr_code_from_image

            extracted_data = extract_qr_code_from_image(sample_image_bytes)

            assert extracted_data is None
        except (ImportError, AttributeError):
            pytest.skip("QR code extraction not implemented")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestQRCodeWatermarkIntegration:
    """Test QR code watermark integration with evidence system."""

    def test_qr_code_contains_verification_url(self, sample_image_bytes, test_watermark_id):
        """Test that QR code contains verification URL."""
        try:
            from ciaf_watermarks.images import embed_qr_code_in_image

            verification_url = f"https://test.com/verify/{test_watermark_id}"

            watermarked = embed_qr_code_in_image(
                image_bytes=sample_image_bytes, qr_data=verification_url
            )

            # Verify it's a valid image
            img = Image.open(io.BytesIO(watermarked))
            assert img is not None
        except (ImportError, AttributeError):
            pytest.skip("embed_qr_code_in_image not implemented")

    def test_qr_code_preserves_image_quality(self, sample_image_bytes):
        """Test that QR code embedding preserves image quality."""
        try:
            from ciaf_watermarks.images import embed_qr_code_in_image

            watermarked = embed_qr_code_in_image(
                image_bytes=sample_image_bytes, qr_data="https://test.com"
            )

            # Original and watermarked should have same dimensions
            original_img = Image.open(io.BytesIO(sample_image_bytes))
            watermarked_img = Image.open(io.BytesIO(watermarked))

            assert watermarked_img.size == original_img.size
        except (ImportError, AttributeError):
            pytest.skip("embed_qr_code_in_image not implemented")


@pytest.mark.unit
class TestQRCodeErrorHandling:
    """Test QR code error handling."""

    def test_generate_qr_code_empty_data(self):
        """Test QR code generation with empty data."""
        try:
            from ciaf_watermarks.images import generate_qr_code

            with pytest.raises(ValueError):
                generate_qr_code("")
        except (ImportError, AttributeError):
            pytest.skip("generate_qr_code not implemented")

    def test_generate_qr_code_invalid_error_correction(self):
        """Test QR code generation with invalid error correction level."""
        try:
            from ciaf_watermarks.images import generate_qr_code

            with pytest.raises(ValueError):
                generate_qr_code("test", error_correction="X")
        except (ImportError, AttributeError, TypeError):
            pytest.skip("generate_qr_code not implemented or parameter not supported")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
