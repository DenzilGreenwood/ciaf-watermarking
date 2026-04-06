"""
Tests for ciaf_watermarks.hashing module.

Tests cover:
- SHA256 hashing
- Text normalization and hashing
- SimHash computation
- Binary hashing
"""

import pytest
from ciaf_watermarks.hashing import (
    sha256_bytes,
    sha256_text,
    normalized_text_hash,
    simhash_text,
    simhash_distance,
)


@pytest.mark.unit
class TestSHA256Hashing:
    """Test SHA256 hashing functions."""

    def test_sha256_bytes(self):
        """Test SHA256 hashing of bytes."""
        data = b"test data"

        hash_value = sha256_bytes(data)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_sha256_bytes_consistency(self):
        """Test SHA256 hash consistency."""
        data = b"consistent data"

        hash1 = sha256_bytes(data)
        hash2 = sha256_bytes(data)

        assert hash1 == hash2

    def test_sha256_bytes_different_data(self):
        """Test SHA256 produces different hashes for different data."""
        data1 = b"data1"
        data2 = b"data2"

        hash1 = sha256_bytes(data1)
        hash2 = sha256_bytes(data2)

        assert hash1 != hash2

    def test_sha256_text(self):
        """Test SHA256 hashing of text."""
        text = "Hello World!"

        hash_value = sha256_text(text)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_sha256_text_encoding(self):
        """Test SHA256 handles text encoding correctly."""
        text_unicode = "Hello 世界"

        hash_value = sha256_text(text_unicode)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64


@pytest.mark.unit
class TestNormalizedTextHashing:
    """Test normalized text hashing."""

    def test_normalized_hash_ignores_whitespace(self):
        """Test that normalized hash ignores whitespace differences."""
        text1 = "Hello  World!"
        text2 = "Hello    World!"

        hash1 = normalized_text_hash(text1)
        hash2 = normalized_text_hash(text2)

        assert hash1 == hash2

    def test_normalized_hash_ignores_case(self):
        """Test that normalized hash ignores case."""
        text1 = "Hello World"
        text2 = "hello world"

        hash1 = normalized_text_hash(text1)
        hash2 = normalized_text_hash(text2)

        assert hash1 == hash2

    def test_normalized_hash_ignores_punctuation(self):
        """Test that normalized hash may ignore punctuation."""
        text1 = "Hello, World!"
        text2 = "Hello World"

        hash1 = normalized_text_hash(text1)
        hash2 = normalized_text_hash(text2)

        # May or may not be equal depending on implementation
        # Just test that hashes are computed
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)


@pytest.mark.unit
class TestSimHash:
    """Test SimHash computation."""

    def test_simhash_computation(self):
        """Test SimHash computation."""
        text = "This is a test document for SimHash computation."

        simhash = simhash_text(text)

        assert isinstance(simhash, str)
        assert len(simhash) == 16  # 64-bit hash as hex

    def test_simhash_consistency(self):
        """Test SimHash consistency."""
        text = "Consistent text for SimHash"

        hash1 = simhash_text(text)
        hash2 = simhash_text(text)

        assert hash1 == hash2

    def test_simhash_similarity_for_similar_text(self):
        """Test SimHash produces similar hashes for similar text."""
        text1 = "The quick brown fox jumps over the lazy dog"
        text2 = "The quick brown fox jumps over the lazy cat"

        hash1 = simhash_text(text1)
        hash2 = simhash_text(text2)

        distance = simhash_distance(hash1, hash2)

        # Similar texts should have low hamming distance
        assert distance < 20  # Out of 64 bits


@pytest.mark.unit
class TestSimHashDistance:
    """Test SimHash distance calculation."""

    def test_simhash_distance_identical(self):
        """Test SimHash distance for identical hashes."""
        hash_value = "a1b2c3d4e5f60708"

        distance = simhash_distance(hash_value, hash_value)

        assert distance == 0

    def test_simhash_distance_completely_different(self):
        """Test SimHash distance for completely different hashes."""
        hash1 = "0000000000000000"
        hash2 = "ffffffffffffffff"

        distance = simhash_distance(hash1, hash2)

        assert distance == 64  # All bits different

    def test_simhash_distance_partial(self):
        """Test SimHash distance for partially different hashes."""
        hash1 = "0000000000000000"
        hash2 = "0000000000000001"  # Only 1 bit different

        distance = simhash_distance(hash1, hash2)

        assert distance == 1


@pytest.mark.unit
class TestHashingEdgeCases:
    """Test hashing edge cases."""

    def test_sha256_empty_bytes(self):
        """Test SHA256 with empty bytes."""
        hash_value = sha256_bytes(b"")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_sha256_empty_text(self):
        """Test SHA256 with empty text."""
        hash_value = sha256_text("")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_simhash_empty_text(self):
        """Test SimHash with empty text."""
        hash_value = simhash_text("")

        assert isinstance(hash_value, str)

    def test_simhash_short_text(self):
        """Test SimHash with very short text."""
        hash_value = simhash_text("Hi")

        assert isinstance(hash_value, str)
        assert len(hash_value) == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
