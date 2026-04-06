"""
Tests for ciaf.watermarks.binary.core module.

Tests cover:
- Binary artifact evidence building
- Binary info extraction
- File type detection
- Metadata handling
"""

import pytest
from ciaf.watermarks.binary import (
    build_binary_artifact_evidence,
    get_binary_info,
    has_binary_watermark,
)
from ciaf.watermarks.binary.metadata import remove_binary_watermark
from ciaf.watermarks.models import ArtifactType, WatermarkType


@pytest.mark.unit
class TestBinaryArtifactEvidenceBuilding:
    """Test binary artifact evidence building."""

    def test_build_evidence_basic(self, sample_binary_bytes, common_watermark_params):
        """Test basic binary evidence building."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        assert evidence is not None
        assert evidence.artifact_type == ArtifactType.BINARY
        assert evidence.watermark.watermark_type == WatermarkType.METADATA
        assert evidence.mime_type == "application/octet-stream"

        # Check watermarked binary
        assert len(watermarked) > len(sample_binary_bytes)
        assert isinstance(watermarked, bytes)

    def test_build_evidence_preserves_original(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test that evidence building preserves original binary."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Original content should be at the start
        assert watermarked.startswith(sample_binary_bytes)

    def test_build_evidence_with_additional_metadata(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test evidence with additional metadata."""
        additional = {
            "compiler": "gcc-14",
            "optimization": "O3",
            "target_arch": "x86_64",
        }

        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes,
            **common_watermark_params,
            additional_metadata=additional,
        )

        assert evidence.metadata["compiler"] == "gcc-14"
        assert evidence.metadata["optimization"] == "O3"
        assert evidence.metadata["target_arch"] == "x86_64"


@pytest.mark.unit
class TestBinaryInfoExtraction:
    """Test binary info extraction."""

    def test_get_binary_info_elf(self):
        """Test getting info for ELF binary."""
        elf_binary = b"\x7fELF" + b"\x00" * 100

        info = get_binary_info(elf_binary)

        assert "ELF" in info["file_type"]
        assert "size_bytes" in info
        assert info["size_bytes"] == len(elf_binary)

    def test_get_binary_info_pe(self):
        """Test getting info for PE executable."""
        pe_binary = b"MZ" + b"\x00" * 100

        info = get_binary_info(pe_binary)

        assert "PE" in info["file_type"]

    def test_get_binary_info_png(self):
        """Test getting info for PNG image file."""
        png_binary = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        info = get_binary_info(png_binary)

        assert "PNG" in info["file_type"]

    def test_get_binary_info_pdf(self):
        """Test getting info for PDF file."""
        pdf_binary = b"%PDF" + b"\x00" * 100

        info = get_binary_info(pdf_binary)

        assert "PDF" in info["file_type"]

    def test_get_binary_info_zip(self):
        """Test getting info for ZIP archive."""
        zip_binary = b"PK\x03\x04" + b"\x00" * 100

        info = get_binary_info(zip_binary)

        assert "ZIP" in info["file_type"]

    def test_get_binary_info_unknown(self):
        """Test getting info for unknown binary."""
        unknown_binary = b"\xab\xcd\xef" + b"\x00" * 100

        info = get_binary_info(unknown_binary)

        assert info["file_type"] == "unknown"


@pytest.mark.unit
class TestBinaryMetadataHandling:
    """Test binary metadata handling."""

    def test_evidence_contains_binary_metadata(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test that evidence contains binary-specific metadata."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Check binary metadata
        assert "binary_size_bytes" in evidence.metadata
        assert "watermarked_size_bytes" in evidence.metadata
        assert "watermark_overhead_bytes" in evidence.metadata

        assert evidence.metadata["binary_size_bytes"] == len(sample_binary_bytes)
        assert evidence.metadata["watermarked_size_bytes"] == len(watermarked)
        assert evidence.metadata["watermark_overhead_bytes"] == len(watermarked) - len(
            sample_binary_bytes
        )

    def test_evidence_file_type_detection(self):
        """Test that evidence includes file type detection."""
        elf_binary = b"\x7fELF" + b"\x00" * 100

        from ciaf.watermarks.binary import build_binary_artifact_evidence

        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=elf_binary,
            model_id="test-model",
            model_version="1.0",
            actor_id="test-actor",
            prompt="test prompt",
            verification_base_url="https://test.com",
        )

        assert "file_type" in evidence.metadata
        assert "ELF" in evidence.metadata["file_type"]


@pytest.mark.unit
class TestBinaryHashComputation:
    """Test binary hash computation."""

    def test_binary_hashes_computed(self, sample_binary_bytes, common_watermark_params):
        """Test that binary hashes are properly computed."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Check hashes
        assert evidence.hashes.content_hash_before_watermark is not None
        assert evidence.hashes.content_hash_after_watermark is not None
        assert len(evidence.hashes.content_hash_before_watermark) == 64

        # Hashes should be different
        assert (
            evidence.hashes.content_hash_before_watermark
            != evidence.hashes.content_hash_after_watermark
        )

    def test_hash_format(self, sample_binary_bytes, common_watermark_params):
        """Test that hashes are in correct format."""
        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Should be lowercase hex
        assert all(
            c in "0123456789abcdef"
            for c in evidence.hashes.content_hash_before_watermark
        )
        assert all(
            c in "0123456789abcdef"
            for c in evidence.hashes.content_hash_after_watermark
        )


@pytest.mark.unit
class TestBinaryWatermarkIntegrity:
    """Test binary watermark integrity."""

    def test_watermark_has_magic_bytes(
        self, sample_binary_bytes, common_watermark_params
    ):
        """Test that watermark contains CIAF magic bytes."""

        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Should have watermark
        assert has_binary_watermark(watermarked)

        # Should contain magic bytes
        assert b"CIAF\x00\x01" in watermarked

    def test_watermark_is_removable(self, sample_binary_bytes, common_watermark_params):
        """Test that watermark can be removed to restore original."""

        evidence, watermarked = build_binary_artifact_evidence(
            binary_bytes=sample_binary_bytes, **common_watermark_params
        )

        # Remove watermark
        unwatermarked = remove_binary_watermark(watermarked)

        # Should match original
        assert unwatermarked == sample_binary_bytes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
