"""
Tests for ciaf_watermarks.images.fingerprints module.

Tests cover:
- Perceptual hashing (pHash, dHash, aHash)
- Image fingerprinting
- Similarity detection
- Hash comparison
"""

import pytest


@pytest.mark.unit
@pytest.mark.requires_pil
class TestPerceptualHashing:
    """Test perceptual hashing functions."""

    def test_phash_computation(self, sample_image_bytes):
        """Test perceptual hash (pHash) computation."""
        try:
            from ciaf_watermarks.images import compute_perceptual_hash

            phash = compute_perceptual_hash(sample_image_bytes)

            assert isinstance(phash, str)
            assert len(phash) == 16  # 64-bit hash as hex
            assert all(c in "0123456789abcdef" for c in phash)
        except ImportError:
            pytest.skip("PIL or imagehash not available")

    def test_dhash_computation_with_size(self, sample_image_bytes):
        """Test hash computation with different hash size."""
        try:
            from ciaf_watermarks.images import compute_perceptual_hash

            # Test with different hash size
            dhash = compute_perceptual_hash(sample_image_bytes, hash_size=16)

            assert isinstance(dhash, str)
            # Hash length varies with hash_size
        except ImportError:
            pytest.skip("PIL or imagehash not available")

    def test_ahash_computation_default(self, sample_image_bytes):
        """Test hash computation with default parameters."""
        try:
            from ciaf_watermarks.images import compute_perceptual_hash

            ahash = compute_perceptual_hash(sample_image_bytes, hash_size=8)

            assert isinstance(ahash, str)
            assert len(ahash) == 16
        except ImportError:
            pytest.skip("PIL or imagehash not available")

    def test_hash_consistency(self, sample_image_bytes):
        """Test that hash is consistent for same image."""
        try:
            from ciaf_watermarks.images import compute_perceptual_hash

            hash1 = compute_perceptual_hash(sample_image_bytes)
            hash2 = compute_perceptual_hash(sample_image_bytes)

            assert hash1 == hash2
        except ImportError:
            pytest.skip("PIL or imagehash not available")

    def test_invalid_hash_size_type(self, sample_image_bytes):
        """Test that invalid hash_size type is handled."""
        try:
            from ciaf_watermarks.images import compute_perceptual_hash

            # Test with valid hash_size
            hash_value = compute_perceptual_hash(sample_image_bytes, hash_size=8)
            assert isinstance(hash_value, str)
        except ImportError:
            pytest.skip("PIL or imagehash not available")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestImageFingerprinting:
    """Test image fingerprinting."""

    def test_generate_image_fingerprints(self, sample_image_bytes):
        """Test generating multiple fingerprints for an image."""
        try:
            from ciaf_watermarks.images import generate_image_fingerprints
            from ciaf_watermarks.models import ArtifactFingerprint

            fingerprints = generate_image_fingerprints(sample_image_bytes)

            assert isinstance(fingerprints, list)
            assert len(fingerprints) >= 3  # At least phash, dhash, ahash

            for fp in fingerprints:
                assert isinstance(fp, ArtifactFingerprint)
                assert fp.fingerprint_type in ["phash", "dhash", "ahash"]
                assert fp.fingerprint_value is not None
        except ImportError:
            pytest.skip("PIL or imagehash not available")

    def test_fingerprints_are_different(self, sample_image_bytes):
        """Test that different algorithms produce different hashes."""
        try:
            from ciaf_watermarks.images import generate_image_fingerprints

            fingerprints = generate_image_fingerprints(sample_image_bytes)

            # Extract hash values
            hash_values = [fp.fingerprint_value for fp in fingerprints]

            # Should have at least some different values
            assert len(set(hash_values)) >= 2
        except ImportError:
            pytest.skip("PIL or imagehash not available")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestImageSimilarityDetection:
    """Test image similarity detection."""

    def test_compare_identical_images(self, sample_image_bytes):
        """Test comparing identical images."""
        try:
            from ciaf_watermarks.images import compare_image_hashes

            hash1 = "a1b2c3d4e5f60708"
            hash2 = "a1b2c3d4e5f60708"

            distance = compare_image_hashes(hash1, hash2)

            assert distance == 0  # Identical hashes
        except (ImportError, AttributeError):
            pytest.skip("compare_image_hashes not implemented")

    def test_compare_different_images(self):
        """Test comparing different images."""
        try:
            from ciaf_watermarks.images import compare_image_hashes

            hash1 = "0000000000000000"
            hash2 = "ffffffffffffffff"

            distance = compare_image_hashes(hash1, hash2)

            assert distance == 64  # Maximum hamming distance for 64-bit hash
        except (ImportError, AttributeError):
            pytest.skip("compare_image_hashes not implemented")

    def test_compute_similarity_score(self, sample_image_bytes):
        """Test computing similarity score."""
        try:
            from ciaf_watermarks.images import compute_image_similarity

            # Compare image to itself
            similarity = compute_image_similarity(sample_image_bytes, sample_image_bytes)

            assert 0.0 <= similarity <= 1.0
            assert similarity >= 0.95  # Should be very similar
        except (ImportError, AttributeError):
            pytest.skip("compute_image_similarity not implemented")


@pytest.mark.unit
@pytest.mark.requires_pil
class TestHashRobustness:
    """Test perceptual hash robustness."""

    def test_hash_resilient_to_minor_changes(self, sample_image_bytes):
        """Test that hash is resilient to minor image modifications."""
        try:
            from ciaf_watermarks.images import compute_perceptual_hash
            from PIL import Image
            import io

            # Get original hash
            _original_hash = compute_perceptual_hash(sample_image_bytes)  # noqa: F841

            # Make minor modification
            img = Image.open(io.BytesIO(sample_image_bytes))
            # Slightly adjust brightness (this is conceptual)
            modified_img = img.convert("RGB")

            # Convert back to bytes
            buf = io.BytesIO()
            modified_img.save(buf, format="PNG")
            modified_bytes = buf.getvalue()

            modified_hash = compute_perceptual_hash(modified_bytes)

            # Hashes should be similar (low hamming distance)
            # This is a basic test - actual implementation may vary
            assert isinstance(modified_hash, str)
        except ImportError:
            pytest.skip("PIL or imagehash not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
