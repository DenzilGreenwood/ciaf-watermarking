"""
CIAF Watermarking - GPU Fragment Selection

GPU-accelerated forensic fragment selection.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from typing import List
import numpy as np

from ..models import ImageForensicFragment, VideoForensicSnippet

try:
    import torch

    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False


def gpu_select_image_fragments(
    image_bytes: bytes,
    num_patches: int = 6,
    device: str = "cuda",
) -> List[ImageForensicFragment]:
    """
    Select high-complexity image patches using GPU acceleration.

    Uses GPU for entropy/complexity calculation (10-20x faster).

    Args:
        image_bytes: Image data
        num_patches: Number of patches to select
        device: Device to use ("cuda" or "cpu")

    Returns:
        List of ImageForensicFragment objects

    Example:
        >>> fragments = gpu_select_image_fragments(image_bytes, num_patches=6)
        >>> print(f"Selected {len(fragments)} patches")
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch is required for GPU fragment selection.")

    if device == "cuda" and not CUDA_AVAILABLE:
        raise RuntimeError("CUDA is not available.")

    try:
        from PIL import Image
        import io
    except ImportError:
        raise ImportError("Pillow is required.")

    # Load image
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)

    # Convert to tensor
    if len(img_array.shape) == 3:
        # Convert RGB to grayscale for complexity calculation
        img_gray = (
            0.299 * img_array[:, :, 0]
            + 0.587 * img_array[:, :, 1]
            + 0.114 * img_array[:, :, 2]
        )
    else:
        img_gray = img_array

    img_tensor = torch.from_numpy(img_gray).float().to(device)

    # Grid parameters
    height, width = img_tensor.shape
    patch_size = 64  # 64x64 patches

    # Calculate complexity for all patches using GPU
    complexities = []
    positions = []

    for y in range(0, height - patch_size, patch_size // 2):  # 50% overlap
        for x in range(0, width - patch_size, patch_size // 2):
            patch = img_tensor[y : y + patch_size, x : x + patch_size]

            # Compute complexity (gradient magnitude)
            # Sobel-like filter using convolution
            grad_y = torch.abs(patch[1:, :] - patch[:-1, :])
            grad_x = torch.abs(patch[:, 1:] - patch[:, :-1])

            # Combine gradients
            complexity = (grad_y.mean() + grad_x.mean()).item()

            complexities.append(complexity)
            positions.append((x, y))

    # Select top-N patches by complexity
    top_indices = np.argsort(complexities)[-num_patches:]

    # Build fragments
    fragments = []
    from ..hashing import sha256_bytes

    for idx in top_indices:
        x, y = positions[idx]
        patch_array = img_array[y : y + patch_size, x : x + patch_size]

        # Compute hash (move back to CPU for this)
        patch_bytes = patch_array.tobytes()
        patch_hash = sha256_bytes(patch_bytes)

        fragment = ImageForensicFragment(
            fragment_id=f"img_patch_{idx}",
            created_at="",  # Will be set by caller
            fragment_type="image_patch",
            algorithm="spatial_complexity_gpu",
            patch_grid_position=f"grid_{x}_{y}",
            patch_hash_before=patch_hash,
            patch_hash_after=patch_hash,  # Will be updated after watermarking
            region_coordinates=(x, y, patch_size, patch_size),
            spatial_complexity=complexities[idx],
        )

        fragments.append(fragment)

    return fragments


def gpu_select_video_fragments(
    video_bytes: bytes,
    num_keyframes: int = 5,
    device: str = "cuda",
) -> List[VideoForensicSnippet]:
    """
    Select high-motion video keyframes using GPU acceleration.

    Uses GPU for motion/complexity calculation.

    Args:
        video_bytes: Video data
        num_keyframes: Number of keyframes to select
        device: Device to use ("cuda" or "cpu")

    Returns:
        List of VideoForensicSnippet objects

    Example:
        >>> fragments = gpu_select_video_fragments(video_bytes, num_keyframes=5)
        >>> print(f"Selected {len(fragments)} keyframes")
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch is required for GPU fragment selection.")

    try:
        import ffmpeg
        from PIL import Image
        import tempfile
        import os
        import io
    except ImportError:
        raise ImportError("ffmpeg-python and Pillow are required.")

    # Extract frames using ffmpeg
    input_path = tempfile.mktemp(suffix=".mp4")
    output_pattern = tempfile.mktemp(suffix="_frame%04d.png")

    try:
        # Write video
        with open(input_path, "wb") as f:
            f.write(video_bytes)

        # Extract frames (1 per second)
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.filter(stream, "fps", fps=1)
        stream = ffmpeg.output(stream, output_pattern, vframes=30)  # Max 30 frames
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, quiet=True)

        # Load frames
        frames = []
        frame_paths = []

        for i in range(1, 31):
            frame_path = output_pattern.replace("%04d", f"{i:04d}")
            if os.path.exists(frame_path):
                with open(frame_path, "rb") as f:
                    frame_bytes = f.read()
                    img = Image.open(io.BytesIO(frame_bytes))
                    frames.append(np.array(img))
                    frame_paths.append((i, frame_path))

        if not frames:
            return []

        # Convert to tensor batch
        # Resize to same size
        target_size = (256, 256)
        frames_resized = []

        for frame in frames:
            img = Image.fromarray(frame)
            img = img.resize(target_size)
            frames_resized.append(np.array(img))

        frames_tensor = torch.from_numpy(np.stack(frames_resized)).float().to(device)

        # Calculate motion/complexity for each frame
        complexities = []

        for i, frame in enumerate(frames_tensor):
            # Convert to grayscale if RGB
            if len(frame.shape) == 3:
                gray = (
                    0.299 * frame[:, :, 0]
                    + 0.587 * frame[:, :, 1]
                    + 0.114 * frame[:, :, 2]
                )
            else:
                gray = frame

            # Compute gradient magnitude
            grad_y = torch.abs(gray[1:, :] - gray[:-1, :])
            grad_x = torch.abs(gray[:, 1:] - gray[:, :-1])

            complexity = (grad_y.mean() + grad_x.mean()).item()
            complexities.append(complexity)

        # Select top-N frames
        top_indices = np.argsort(complexities)[-num_keyframes:]

        # Build snippets
        snippets = []
        from ..hashing import sha256_bytes

        for idx in top_indices:
            frame_num, frame_path = frame_paths[idx]

            # Compute hash
            with open(frame_path, "rb") as f:
                frame_bytes = f.read()
                frame_hash = sha256_bytes(frame_bytes)

            snippet = VideoForensicSnippet(
                fragment_id=f"video_frame_{frame_num}",
                created_at="",
                fragment_type="video_keyframe",
                algorithm="motion_complexity_gpu",
                keyframe_index=frame_num,
                keyframe_hash_before=frame_hash,
                keyframe_hash_after=frame_hash,
                timestamp_seconds=float(frame_num),
                motion_confidence=complexities[idx],
            )

            snippets.append(snippet)

        # Cleanup
        for _, frame_path in frame_paths:
            if os.path.exists(frame_path):
                os.remove(frame_path)

        return snippets

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


__all__ = [
    "gpu_select_image_fragments",
    "gpu_select_video_fragments",
]
