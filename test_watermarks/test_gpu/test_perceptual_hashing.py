"""
Tests for ciaf.watermarks.gpu module.

Tests cover:
- GPU perceptual hashing
- Batch processing
- Fragment selection
- Performance comparisons

Note: Most GPU tests are skipped if CUDA is not available.
"""

import pytest


@pytest.mark.gpu
@pytest.mark.unit
class TestGPUPerceptualHashing:
    """Test GPU perceptual hashing."""

    def test_cuda_availability_check(self):
        """Test CUDA availability detection."""
        from ciaf.watermarks.gpu import CUDA_AVAILABLE, TORCH_AVAILABLE

        assert isinstance(CUDA_AVAILABLE, bool)
        assert isinstance(TORCH_AVAILABLE, bool)

        if TORCH_AVAILABLE:
            import torch

            assert CUDA_AVAILABLE == torch.cuda.is_available()

    @pytest.mark.requires_pil
    def test_gpu_perceptual_hash_cpu_mode(self, sample_image_bytes):
        """Test GPU perceptual hashing in CPU mode."""
        try:
            from ciaf.watermarks.gpu import gpu_perceptual_hash_image

            hash_value = gpu_perceptual_hash_image(
                image_bytes=sample_image_bytes, device="cpu"
            )

            assert isinstance(hash_value, str)
            assert len(hash_value) == 16  # 16 hex characters
            assert all(c in "0123456789abcdef" for c in hash_value)
        except ImportError:
            pytest.skip("torch or PIL not available")

    @pytest.mark.skipif(
        not pytest.importorskip(
            "torch", reason="torch not available"
        ).cuda.is_available(),
        reason="CUDA not available",
    )
    def test_gpu_perceptual_hash_cuda_mode(self, sample_image_bytes):
        """Test GPU perceptual hashing in CUDA mode."""
        try:
            from ciaf.watermarks.gpu import gpu_perceptual_hash_image, CUDA_AVAILABLE

            if not CUDA_AVAILABLE:
                pytest.skip("CUDA not available")

            hash_value = gpu_perceptual_hash_image(
                image_bytes=sample_image_bytes, device="cuda"
            )

            assert isinstance(hash_value, str)
            assert len(hash_value) == 16
        except ImportError:
            pytest.skip("torch or PIL not available")

    def test_hash_consistency_cpu(self, sample_image_bytes):
        """Test that CPU hash is consistent."""
        try:
            from ciaf.watermarks.gpu import gpu_perceptual_hash_image

            hash1 = gpu_perceptual_hash_image(
                image_bytes=sample_image_bytes, device="cpu"
            )
            hash2 = gpu_perceptual_hash_image(
                image_bytes=sample_image_bytes, device="cpu"
            )

            assert hash1 == hash2
        except ImportError:
            pytest.skip("torch or PIL not available")


@pytest.mark.gpu
@pytest.mark.integration
class TestGPUBatchProcessing:
    """Test GPU batch processing."""

    @pytest.mark.requires_pil
    def test_batch_hash_images_cpu(self, sample_image_bytes):
        """Test batch hashing on CPU."""
        try:
            from ciaf.watermarks.gpu import batch_perceptual_hash_images

            # Create multiple image variants
            image_list = [sample_image_bytes] * 5

            hashes = batch_perceptual_hash_images(images_bytes=image_list, device="cpu")

            assert len(hashes) == 5
            assert all(isinstance(h, str) for h in hashes)
            # All should be identical for same image
            assert len(set(hashes)) == 1
        except ImportError:
            pytest.skip("torch or PIL not available")

    @pytest.mark.skipif(
        not pytest.importorskip(
            "torch", reason="torch not available"
        ).cuda.is_available(),
        reason="CUDA not available",
    )
    def test_batch_hash_images_cuda(self, sample_image_bytes):
        """Test batch hashing on CUDA."""
        try:
            from ciaf.watermarks.gpu import batch_perceptual_hash_images, CUDA_AVAILABLE

            if not CUDA_AVAILABLE:
                pytest.skip("CUDA not available")

            image_list = [sample_image_bytes] * 10

            hashes = batch_perceptual_hash_images(
                images_bytes=image_list, device="cuda"
            )

            assert len(hashes) == 10
            assert all(isinstance(h, str) for h in hashes)
        except ImportError:
            pytest.skip("torch or PIL not available")


@pytest.mark.gpu
@pytest.mark.unit
class TestGPUFragmentSelection:
    """Test GPU-accelerated fragment selection."""

    def test_gpu_fragment_selector_init(self):
        """Test GPUFragmentSelector initialization."""
        try:
            from ciaf.watermarks.gpu import GPUFragmentSelector

            selector = GPUFragmentSelector(device="cpu")
            assert selector is not None
            assert selector.device in ["cpu", "cuda"]
        except ImportError:
            pytest.skip("torch not available")

    @pytest.mark.requires_pil
    def test_select_image_fragments_cpu(self, sample_image_bytes):
        """Test fragment selection on CPU."""
        try:
            from ciaf.watermarks.gpu import GPUFragmentSelector

            selector = GPUFragmentSelector(device="cpu")
            fragments = selector.select_image_fragments(
                image_bytes=sample_image_bytes, num_fragments=5
            )

            assert len(fragments) == 5
            assert all(isinstance(f, bytes) for f in fragments)
        except ImportError:
            pytest.skip("torch or PIL not available")


@pytest.mark.gpu
@pytest.mark.slow
class TestGPUPerformance:
    """Test GPU performance characteristics."""

    @pytest.mark.requires_pil
    def test_cpu_vs_gpu_performance_comparison(self, sample_image_bytes):
        """Compare CPU vs GPU performance (when CUDA available)."""
        try:
            from ciaf.watermarks.gpu import gpu_perceptual_hash_image, CUDA_AVAILABLE
            import time

            # Test CPU performance
            start = time.time()
            for _ in range(10):
                gpu_perceptual_hash_image(sample_image_bytes, device="cpu")
            cpu_time = time.time() - start

            assert cpu_time > 0

            # If CUDA available, compare
            if CUDA_AVAILABLE:
                start = time.time()
                for _ in range(10):
                    gpu_perceptual_hash_image(sample_image_bytes, device="cuda")
                gpu_time = time.time() - start

                # GPU should be faster or comparable
                # (Note: For small batches, CPU might actually be faster due to overhead)
                assert gpu_time > 0
        except ImportError:
            pytest.skip("torch or PIL not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
