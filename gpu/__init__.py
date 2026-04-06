"""
CIAF Watermarking - GPU Accelerated Processing

GPU-accelerated implementations for high-performance watermarking.

Exports:
- GPU perceptual hashing
- GPU batch processing
- GPU fragment selection

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from .perceptual_hashing import (
    gpu_perceptual_hash_image,
    gpu_perceptual_hash_batch_images,
    gpu_perceptual_hash_video,
    CUDA_AVAILABLE,
    TORCH_AVAILABLE,
)

from .batch_processing import (
    gpu_watermark_batch,
    gpu_verify_batch,
    BatchResult,
)

from .fragment_selection import (
    gpu_select_image_fragments,
    gpu_select_video_fragments,
)

__all__ = [
    # Perceptual hashing
    "gpu_perceptual_hash_image",
    "gpu_perceptual_hash_batch_images",
    "gpu_perceptual_hash_video",
    "CUDA_AVAILABLE",
    "TORCH_AVAILABLE",
    # Batch processing
    "gpu_watermark_batch",
    "gpu_verify_batch",
    "BatchResult",
    # Fragment selection
    "gpu_select_image_fragments",
    "gpu_select_video_fragments",
]
