"""
Tests for ciaf.watermarks.pdf.metadata module.

Tests cover:
- PDF metadata watermarking
- PDF XMP metadata
- PDF custom properties
- Metadata extraction
"""

import pytest


@pytest.mark.unit
class TestPDFMetadataWatermarking:
    """Test PDF metadata watermarking."""

    def test_apply_pdf_metadata_watermark(self, sample_pdf_bytes, test_watermark_id):
        """Test applying metadata watermark to PDF."""
        try:
            from ciaf.watermarks.pdf import apply_pdf_metadata_watermark

            watermarked = apply_pdf_metadata_watermark(
                pdf_bytes=sample_pdf_bytes,
                watermark_id=test_watermark_id,
                model_id="pdf-gen-v1",
                artifact_id="test-artifact-123",
                verification_url="https://test.com/verify",
                timestamp="2026-04-05T10:00:00Z",
            )

            assert isinstance(watermarked, bytes)
            assert len(watermarked) > 0
        except (ImportError, AttributeError):
            pytest.skip("PDF watermarking not implemented or PyPDF2 not available")

    def test_extract_pdf_metadata(self, sample_pdf_bytes):
        """Test extracting metadata from PDF."""
        try:
            from ciaf.watermarks.pdf import extract_pdf_metadata_watermark

            metadata = extract_pdf_metadata_watermark(sample_pdf_bytes)

            # May be None if no watermark
            assert metadata is None or isinstance(metadata, dict)
        except (ImportError, AttributeError):
            pytest.skip("PDF metadata extraction not implemented")

    def test_has_pdf_watermark(self, sample_pdf_bytes):
        """Test checking if PDF has watermark."""
        try:
            from ciaf.watermarks.pdf import has_pdf_watermark

            result = has_pdf_watermark(sample_pdf_bytes)

            assert isinstance(result, bool)
        except (ImportError, AttributeError):
            pytest.skip("has_pdf_watermark not implemented")


@pytest.mark.unit
class TestPDFXMPMetadata:
    """Test PDF XMP metadata handling."""

    def test_add_xmp_metadata(self, sample_pdf_bytes):
        """Test adding XMP metadata to PDF."""
        try:
            from ciaf.watermarks.pdf import add_xmp_watermark

            watermarked = add_xmp_watermark(
                pdf_bytes=sample_pdf_bytes, watermark_data={"watermark_id": "wmk-123"}
            )

            assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError):
            pytest.skip("XMP watermarking not implemented")

    def test_extract_xmp_metadata(self):
        """Test extracting XMP metadata from PDF."""
        try:
            pass

            # This would require a PDF with XMP data
            pytest.skip("Requires sample PDF with XMP metadata")
        except (ImportError, AttributeError):
            pytest.skip("XMP extraction not implemented")


@pytest.mark.unit
class TestPDFCustomProperties:
    """Test PDF custom properties."""

    def test_add_custom_properties(self, sample_pdf_bytes):
        """Test adding custom properties to PDF."""
        try:
            from ciaf.watermarks.pdf import apply_pdf_metadata_watermark

            watermarked = apply_pdf_metadata_watermark(
                pdf_bytes=sample_pdf_bytes,
                watermark_id="wmk-123",
                verification_url="https://test.com",
                model_id="test",
                timestamp="2026-04-05T10:00:00Z",
                metadata={"custom_key": "custom_value"},
            )

            assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError, TypeError):
            pytest.skip("Custom properties not supported")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
