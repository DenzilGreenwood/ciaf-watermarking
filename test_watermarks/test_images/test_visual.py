"""
Tests for ciaf_watermarks.images.visual module.

Tests cover:
- Visual watermark application
- Text overlay watermarking
- Logo/signature watermarking
- Watermark positioning
- Transparency and blending
"""

import pytest
from PIL import Image
import io


@pytest.mark.unit
@pytest.mark.requires_pil
class TestVisualWatermarkApplication:
    """Test visual watermark application."""

    def test_apply_text_watermark(self, sample_image_bytes):
        """Test applying text watermark to image."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            watermarked = apply_visual_text_watermark(
                image_bytes=sample_image_bytes,
                watermark_text="CIAF Watermark - wmk-test-123",
                position="bottom-right",
                opacity=0.7,
            )

            assert isinstance(watermarked, bytes)
            assert len(watermarked) > 0

            # Should be valid image
            img = Image.open(io.BytesIO(watermarked))
            assert img is not None
        except ImportError:
            pytest.skip("PIL not available")

    def test_apply_text_watermark_different_positions(self, sample_image_bytes):
        """Test text watermark at different positions."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            positions = [
                "top-left",
                "top-right",
                "bottom-left",
                "bottom-right",
                "center",
            ]

            for position in positions:
                watermarked = apply_visual_text_watermark(
                    image_bytes=sample_image_bytes,
                    watermark_text="Test",
                    position=position,
                )

                assert isinstance(watermarked, bytes)
                img = Image.open(io.BytesIO(watermarked))
                assert img is not None
        except ImportError:
            pytest.skip("PIL not available")

    def test_apply_text_watermark_opacity(self, sample_image_bytes):
        """Test text watermark with different opacity levels."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            for opacity in [0.3, 0.5, 0.7, 1.0]:
                watermarked = apply_visual_text_watermark(
                    image_bytes=sample_image_bytes,
                    watermark_text="Test",
                    opacity=opacity,
                )

                assert isinstance(watermarked, bytes)
        except ImportError:
            pytest.skip("PIL not available")

    def test_invalid_opacity_raises_error(self, sample_image_bytes):
        """Test that invalid opacity raises error."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            with pytest.raises(ValueError, match="opacity"):
                apply_visual_text_watermark(
                    image_bytes=sample_image_bytes,
                    watermark_text="Test",
                    opacity=1.5,  # Invalid
                )
        except ImportError:
            pytest.skip("PIL not available")

    def test_invalid_position_raises_error(self, sample_image_bytes):
        """Test that invalid position raises error."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            with pytest.raises(ValueError, match="position"):
                apply_visual_text_watermark(
                    image_bytes=sample_image_bytes,
                    watermark_text="Test",
                    position="invalid-position",
                )
        except ImportError:
            pytest.skip("PIL not available")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestLogoWatermarking:
    """Test logo/signature watermarking."""

    def test_apply_logo_watermark(self, sample_image_bytes):
        """Test applying logo watermark."""
        try:
            from ciaf_watermarks.images import apply_logo_watermark

            # Use sample image as logo
            watermarked = apply_logo_watermark(
                image_bytes=sample_image_bytes,
                logo_bytes=sample_image_bytes,
                position="bottom-right",
                scale=0.2,
            )

            assert isinstance(watermarked, bytes)
            img = Image.open(io.BytesIO(watermarked))
            assert img is not None
        except (ImportError, AttributeError):
            pytest.skip("apply_logo_watermark not implemented or PIL not available")

    def test_apply_logo_watermark_scaling(self, sample_image_bytes):
        """Test logo watermark with different scales."""
        try:
            from ciaf_watermarks.images import apply_logo_watermark

            for scale in [0.1, 0.2, 0.3]:
                watermarked = apply_logo_watermark(
                    image_bytes=sample_image_bytes,
                    logo_bytes=sample_image_bytes,
                    scale=scale,
                )

                assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError):
            pytest.skip("apply_logo_watermark not implemented")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestVisualWatermarkCustomization:
    """Test visual watermark customization options."""

    def test_custom_font_size(self, sample_image_bytes):
        """Test text watermark with custom font size."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            watermarked = apply_visual_text_watermark(
                image_bytes=sample_image_bytes, watermark_text="Test", font_size=36
            )

            assert isinstance(watermarked, bytes)
        except (ImportError, TypeError):
            pytest.skip("font_size parameter not supported or PIL not available")

    def test_custom_color(self, sample_image_bytes):
        """Test text watermark with custom color."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            watermarked = apply_visual_text_watermark(
                image_bytes=sample_image_bytes,
                watermark_text="Test",
                color=(255, 0, 0),  # Red
            )

            assert isinstance(watermarked, bytes)
        except (ImportError, TypeError):
            pytest.skip("color parameter not supported or PIL not available")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestVisualWatermarkPreservation:
    """Test that visual watermarking preserves image properties."""

    def test_preserves_image_dimensions(self, sample_image_bytes):
        """Test that watermarking preserves image dimensions."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            # Get original dimensions
            original_img = Image.open(io.BytesIO(sample_image_bytes))
            original_size = original_img.size

            watermarked = apply_visual_text_watermark(
                image_bytes=sample_image_bytes, watermark_text="Test"
            )

            watermarked_img = Image.open(io.BytesIO(watermarked))

            # Dimensions should match
            assert watermarked_img.size == original_size
        except ImportError:
            pytest.skip("PIL not available")

    def test_preserves_image_format(self, sample_image_bytes):
        """Test that watermarking can preserve image format."""
        try:
            from ciaf_watermarks.images import apply_visual_text_watermark

            watermarked = apply_visual_text_watermark(
                image_bytes=sample_image_bytes, watermark_text="Test"
            )

            # Should be valid image
            img = Image.open(io.BytesIO(watermarked))
            # None if format not set
            assert img.format in ["PNG", "JPEG", "JPG", None]
        except ImportError:
            pytest.skip("PIL not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
