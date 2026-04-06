"""
Tests for ciaf_watermarks.models module.

Tests cover:
- Data model creation and validation
- Serialization/deserialization
- Hash computation
- Utility functions
"""

import pytest
from datetime import datetime

from ciaf_watermarks.models import (
    ArtifactType,
    WatermarkType,
    ArtifactEvidence,
    ArtifactHashSet,
    WatermarkDescriptor,
    VerificationResult,
    TextForensicFragment,
    ImageForensicFragment,
    ForensicFragmentSet,
    utc_now_iso,
    sha256_bytes,
    sha256_text,
    canonical_json,
)


class TestEnums:
    """Test enumeration types."""

    def test_artifact_type_values(self):
        """Test ArtifactType enum has all required values."""
        assert ArtifactType.TEXT.value == "text"
        assert ArtifactType.IMAGE.value == "image"
        assert ArtifactType.PDF.value == "pdf"
        assert ArtifactType.VIDEO.value == "video"
        assert ArtifactType.AUDIO.value == "audio"
        assert ArtifactType.BINARY.value == "binary"

    def test_watermark_type_values(self):
        """Test WatermarkType enum has all required values."""
        assert WatermarkType.VISIBLE.value == "visible"
        assert WatermarkType.METADATA.value == "metadata"
        assert WatermarkType.EMBEDDED.value == "embedded"
        assert WatermarkType.HYBRID.value == "hybrid"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_utc_now_iso(self):
        """Test ISO 8601 timestamp generation."""
        timestamp = utc_now_iso()

        assert isinstance(timestamp, str)
        assert "T" in timestamp
        assert "Z" in timestamp or "+" in timestamp

        # Should be parseable
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_sha256_bytes(self):
        """Test SHA-256 hashing of bytes."""
        data = b"test data"
        hash_value = sha256_bytes(data)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
        assert hash_value.isalnum()

        # Same input should produce same hash
        assert sha256_bytes(data) == hash_value

    def test_sha256_text(self):
        """Test SHA-256 hashing of text."""
        text = "test text"
        hash_value = sha256_text(text)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

        # Same input should produce same hash
        assert sha256_text(text) == hash_value

    def test_canonical_json(self):
        """Test canonical JSON serialization."""
        obj = {"b": 2, "a": 1, "c": {"z": 26, "y": 25}}
        json_bytes = canonical_json(obj)

        assert isinstance(json_bytes, bytes)
        # Should be sorted
        assert json_bytes == b'{"a":1,"b":2,"c":{"y":25,"z":26}}'


class TestArtifactHashSet:
    """Test ArtifactHashSet model."""

    def test_creation(self):
        """Test creating hash set."""
        hashes = ArtifactHashSet(
            content_hash_before_watermark="a" * 64,
            content_hash_after_watermark="b" * 64,
        )

        assert hashes.content_hash_before_watermark == "a" * 64
        assert hashes.content_hash_after_watermark == "b" * 64

    def test_optional_fields(self):
        """Test optional hash fields."""
        hashes = ArtifactHashSet(
            content_hash_before_watermark="a" * 64,
            content_hash_after_watermark="b" * 64,
            simhash_before="c" * 16,
            simhash_after="d" * 16,
        )

        assert hashes.simhash_before == "c" * 16


class TestWatermarkDescriptor:
    """Test WatermarkDescriptor model."""

    def test_creation(self):
        """Test creating watermark descriptor."""
        descriptor = WatermarkDescriptor(
            watermark_id="wmk-123",
            watermark_type=WatermarkType.VISIBLE,
            verification_url="https://test.com/verify/wmk-123",
        )

        assert descriptor.watermark_id == "wmk-123"
        assert descriptor.watermark_type == WatermarkType.VISIBLE


class TestArtifactEvidence:
    """Test ArtifactEvidence model."""

    def test_creation(self):
        """Test creating artifact evidence."""
        watermark = WatermarkDescriptor(
            watermark_id="wmk-123",
            watermark_type=WatermarkType.VISIBLE,
            verification_url="https://test.com",
        )

        hashes = ArtifactHashSet(
            content_hash_before_watermark="a" * 64,
            content_hash_after_watermark="b" * 64,
        )

        evidence = ArtifactEvidence(
            artifact_id="art-123",
            artifact_type=ArtifactType.TEXT,
            created_at=utc_now_iso(),
            model_id="model-2026-03",
            model_version="2026-03",
            actor_id="user:test",
            prompt_hash="c" * 64,
            output_hash_raw="a" * 64,
            output_hash_distributed="b" * 64,
            watermark=watermark,
            hashes=hashes,
            mime_type="text/plain",
            metadata={},
        )

        assert evidence.artifact_id == "art-123"
        assert evidence.artifact_type == ArtifactType.TEXT

    def test_serialization(self):
        """Test JSON serialization."""
        watermark = WatermarkDescriptor(
            watermark_id="wmk-123",
            watermark_type=WatermarkType.VISIBLE,
            verification_url="https://test.com",
        )

        hashes = ArtifactHashSet(
            content_hash_before_watermark="a" * 64,
            content_hash_after_watermark="b" * 64,
        )

        evidence = ArtifactEvidence(
            artifact_id="art-123",
            artifact_type=ArtifactType.TEXT,
            created_at=utc_now_iso(),
            model_id="model-2026-03",
            model_version="2026-03",
            actor_id="user:test",
            prompt_hash="c" * 64,
            output_hash_raw="a" * 64,
            output_hash_distributed="b" * 64,
            watermark=watermark,
            hashes=hashes,
            mime_type="text/plain",
            metadata={},
        )

        # Should be serializable
        json_str = evidence.model_dump_json()
        assert isinstance(json_str, str)

        # Should be deserializable
        evidence_reloaded = ArtifactEvidence.model_validate_json(json_str)
        assert evidence_reloaded.artifact_id == evidence.artifact_id


class TestVerificationResult:
    """Test VerificationResult model."""

    def test_creation(self):
        """Test creating verification result."""
        result = VerificationResult(
            artifact_id="test-artifact-123",
            exact_match_after_watermark=True,
            exact_match_before_watermark=False,
            likely_tag_removed=False,
            watermark_present=True,
            watermark_intact=True,
            notes=["Exact match to distributed version"],
        )

        assert result.artifact_id == "test-artifact-123"
        assert result.exact_match_after_watermark is True

    def test_is_authentic(self):
        """Test is_authentic() method."""
        # Exact match
        result = VerificationResult(
            artifact_id="test",
            exact_match_after_watermark=True,
            exact_match_before_watermark=False,
            likely_tag_removed=False,
        )
        assert result.is_authentic() is True


class TestForensicFragments:
    """Test forensic fragment models."""

    def test_text_fragment(self):
        """Test TextForensicFragment model."""
        fragment = TextForensicFragment(
            fragment_id="frag-1",
            fragment_type="text",
            entropy_score=0.85,
            sampling_method="high_entropy",
            content_position=0,  # int position
            offset_start=0,
            offset_end=100,
            fragment_length=100,
            sample_location="beginning",
            fragment_text="Sample text...",
            fragment_hash_before="a" * 64,
            fragment_hash_after="b" * 64,
        )

        assert fragment.fragment_id == "frag-1"
        assert fragment.offset_start == 0
        assert fragment.entropy_score == 0.85

    def test_image_fragment(self):
        """Test ImageForensicFragment model."""
        fragment = ImageForensicFragment(
            fragment_id="frag-img-1",
            fragment_type="image_patch",
            entropy_score=0.92,
            sampling_method="spatial_complexity",
            content_position=10,  # int position (patch index)
            patch_grid_position="grid_2_3",
            patch_hash_before="a" * 16,
            patch_hash_after="b" * 16,
            region_coordinates=(100, 100, 64, 64),
            spatial_complexity=0.92,
        )

        assert fragment.fragment_id == "frag-img-1"
        assert fragment.patch_grid_position == "grid_2_3"


class TestFragmentSet:
    """Test ForensicFragmentSet model."""

    def test_creation(self):
        """Test creating fragment set."""
        fragments = [
            TextForensicFragment(
                fragment_id=f"frag-{i}",
                fragment_type="text",
                entropy_score=0.85,
                sampling_method="high_entropy",
                content_position=i * 100,  # int position
                offset_start=i * 100,
                offset_end=(i + 1) * 100,
                fragment_length=100,
                sample_location="middle",
                fragment_text="x" * 100,
                fragment_hash_before="a" * 64,
                fragment_hash_after="b" * 64,
            )
            for i in range(5)
        ]

        fragment_set = ForensicFragmentSet(
            fragment_count=5,
            sampling_strategy="high_entropy",
            total_coverage_percent=50.0,
            text_fragments=fragments,
        )

        assert fragment_set.fragment_count == 5
        assert len(fragment_set.text_fragments) == 5
        # Should combine all fragment types
        assert len(fragment_set.all_fragments) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
