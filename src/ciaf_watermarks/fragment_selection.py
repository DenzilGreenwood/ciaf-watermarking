"""
CIAF Watermarking - Forensic Fragment Selection

Entropy-based selection of high-information-density fragments for DNA-level
forensic verification across all artifact types.

Strategy: Don't verify the body; verify the DNA.

By storing high-entropy fragments, we enable:
- Detection of mix-and-match attacks (spliced documents)
- Legal defensibility through multi-point sampling
- Privacy protection (compact DNA records vs full document storage)

Multi-Point Sampling Rule:
- Text: 3 fragments (begin, middle, end) → any 2 matches = ~99.9% confidence
- Image: 4-6 high-complexity patches → spatial diversity
- Video: I-frames at temporal boundaries + motion signatures
- Audio: Spectral segments with high frequency variation

Created: 2026-03-28
Author: Denzil James Greenwood
Version: 1.2.0
"""

from __future__ import annotations

from typing import List, Tuple, Optional

from .models import (
    TextForensicFragment,
    ImageForensicFragment,
    VideoForensicSnippet,
    AudioForensicSegment,
    ForensicFragmentSet,
    sha256_text,
    sha256_bytes,
)

# ============================================================================
# TEXT FRAGMENT SELECTION
# ============================================================================


def compute_text_entropy(text: str) -> float:
    """
    Compute Shannon entropy of text (0.0-1.0).

    Higher entropy = more unique/diverse content
    Lower entropy = boilerplate/repetitive content

    Avoids selecting generic phrases like "In conclusion..."
    """
    if not text or len(text) < 10:
        return 0.0

    # Normalize text
    text = text.lower()

    # Count character frequencies
    char_freq: Dict[str, int] = {}
    for char in text:
        char_freq[char] = char_freq.get(char, 0) + 1

    # Compute Shannon entropy
    import math

    entropy = 0.0
    for count in char_freq.values():
        if count > 0:
            p = count / len(text)
            entropy -= p * math.log2(p)

    # Normalize to 0.0-1.0 (max for 256 chars ≈ 8)
    return min(1.0, entropy / 8.0)


def select_text_fragment(
    text: str,
    location: str = "middle",  # 'beginning', 'middle', 'end'
    fragment_length: int = 200,
) -> Optional[Tuple[int, int, str, float]]:
    """
    Select a high-entropy text fragment from specified location.

    Args:
        text: Full text content
        location: Where to sample ('beginning', 'middle', 'end')
        fragment_length: Target length of fragment (chars)

    Returns:
        Tuple of (offset_start, offset_end, fragment_text, entropy_score)
        or None if text too short
    """
    if len(text) < fragment_length * 1.5:
        return None

    # Define search regions
    total_len = len(text)

    if location == "beginning":
        search_start = 0
        search_end = max(fragment_length, int(total_len * 0.2))
    elif location == "middle":
        quarter = int(total_len * 0.25)
        search_start = quarter
        search_end = min(total_len - fragment_length, quarter + int(total_len * 0.5))
    else:  # 'end'
        search_start = max(0, int(total_len * 0.8) - fragment_length)
        search_end = total_len - fragment_length

    if search_start >= search_end:
        return None

    # Find high-entropy fragment in region
    best_entropy = 0.0
    best_start = search_start
    best_end = search_start + fragment_length

    # Sample positions in the region
    step = max(1, (search_end - search_start) // 10)

    for pos in range(search_start, search_end, step):
        end_pos = min(pos + fragment_length, total_len)
        fragment = text[pos : end_pos + 1]

        if len(fragment) < fragment_length * 0.8:
            continue

        entropy = compute_text_entropy(fragment)

        if entropy > best_entropy:
            best_entropy = entropy
            best_start = pos
            best_end = end_pos

    if best_entropy < 0.4:
        # Fall back to any fragment in region
        best_start = search_start
        best_end = min(search_start + fragment_length, total_len)

    fragment = text[best_start : best_end + 1]
    return (best_start, best_end, fragment, best_entropy)


def select_text_forensic_fragments(
    raw_text: str,
    fragment_hash_before: str,  # Will be injected by caller
    fragment_hash_after: str,  # Will be injected by caller
    min_entropy: float = 0.4,
) -> List[TextForensicFragment]:
    """
    Select three high-entropy text fragments for multi-point verification.

    Strategy:
    - Beginning fragment (introduction/setup)
    - Middle fragment (core content)
    - End fragment (conclusion/results)

    Multi-point rule: If ANY 2 match, confidence > 99.9%

    Args:
        raw_text: Full text content
        fragment_hash_before: Pre-computed hash before watermark
        fragment_hash_after: Pre-computed hash after watermark
        min_entropy: Minimum entropy threshold

    Returns:
        List of TextForensicFragment records (typically 3)
    """
    fragments: List[TextForensicFragment] = []

    for location in ["beginning", "middle", "end"]:
        result = select_text_fragment(raw_text, location=location, fragment_length=200)

        if result is None:
            continue

        offset_start, offset_end, fragment_text, entropy = result

        if entropy < min_entropy:
            continue

        # Compute hashes for this fragment
        # In practice, these would be computed from the actual watermarked/unwatermarked versions
        frag_hash_before = sha256_text(fragment_text)
        frag_hash_after = sha256_text(
            fragment_text
        )  # Placeholder - actual would vary based on watermark

        fragment = TextForensicFragment(
            fragment_id=f"text_frag_{location}_{offset_start}",
            fragment_type="text",
            entropy_score=entropy,
            sampling_method=location,
            content_position=offset_start,
            offset_start=offset_start,
            offset_end=offset_end,
            fragment_length=len(fragment_text),
            sample_location=location,
            fragment_text=fragment_text,  # ✅ FIX #161: Store actual text for sliding window matching
            fragment_hash_before=frag_hash_before,
            fragment_hash_after=frag_hash_after,
        )

        fragments.append(fragment)

    return fragments


# ============================================================================
# IMAGE FRAGMENT SELECTION
# ============================================================================


def compute_image_patch_entropy(
    image_data: bytes, patch_x: int, patch_y: int, patch_w: int = 64, patch_h: int = 64
) -> float:
    """
    Compute entropy of an image patch (0.0-1.0).

    Higher entropy = more complex/detailed region
    Lower entropy = uniform color or blank region (avoid these)

    This prevents selecting blank sky or solid-color backgrounds.
    """
    try:
        from PIL import Image
        import numpy as np

        img = Image.open(__import__("io").BytesIO(image_data))
        img_array = np.array(img.convert("RGB"))

        # Extract patch
        x_end = min(patch_x + patch_w, img_array.shape[1])
        y_end = min(patch_y + patch_h, img_array.shape[0])

        patch = img_array[patch_y : y_end + 1, patch_x : x_end + 1]

        if patch.size < 32:
            return 0.0

        # Compute entropy: higher variance + diversity = higher entropy
        # Channels: standard deviation across RGB
        r_std = np.std(patch[:, :, 0])
        g_std = np.std(patch[:, :, 1])
        b_std = np.std(patch[:, :, 2])

        avg_std = (r_std + g_std + b_std) / 3.0 / 128.0  # Normalize to 0-1

        # Spatial diversity: gradient edges
        edges = np.zeros_like(patch[:, :, 0], dtype=float)
        edges[:-1, :] += np.abs(patch[1:, :, 0].astype(float) - patch[:-1, :, 0].astype(float))
        edges[:, :-1] += np.abs(patch[:, 1:, 0].astype(float) - patch[:, :-1, 0].astype(float))

        edge_strength = np.mean(edges) / 255.0

        # Combined entropy score
        entropy = 0.6 * avg_std + 0.4 * edge_strength
        return min(1.0, entropy)

    except Exception:
        # PIL not available or parsing error
        return 0.0


def select_image_forensic_patches(
    image_bytes: bytes,
    num_patches: int = 4,
    patch_size: int = 64,
    min_entropy: float = 0.5,
) -> List[ImageForensicFragment]:
    """
    Select high-complexity image patches for DNA-level verification.

    Strategy:
    - Divide image into grid
    - Compute entropy for each patch
    - Select most complex patches (avoid blank sky, solid colors)

    Args:
        image_bytes: Image file content
        num_patches: Number of patches to select (typically 4-6)
        patch_size: Patch dimensions (64x64 default)
        min_entropy: Minimum entropy threshold

    Returns:
        List of ImageForensicFragment records
    """
    try:
        from PIL import Image
        import numpy as np

        img = Image.open(__import__("io").BytesIO(image_bytes))
        img_array = np.array(img.convert("RGB"))

        img_h, img_w = img_array.shape[:2]

        # Create grid of potential patches
        grid_cols = max(1, img_w // patch_size)
        grid_rows = max(1, img_h // patch_size)

        patches_with_entropy = []

        for row in range(grid_rows):
            for col in range(grid_cols):
                patch_x = col * patch_size
                patch_y = row * patch_size

                entropy = compute_image_patch_entropy(
                    image_bytes, patch_x, patch_y, patch_size, patch_size
                )

                if entropy >= min_entropy:
                    patches_with_entropy.append((patch_x, patch_y, entropy))

        # Select top N patches by entropy
        patches_with_entropy.sort(key=lambda x: x[2], reverse=True)
        selected = patches_with_entropy[:num_patches]

        # Create fragment records
        fragments: List[ImageForensicFragment] = []

        for idx, (patch_x, patch_y, entropy) in enumerate(selected):
            # Extract patch and compute hash (fixed off-by-one error)
            patch_image = img_array[patch_y : patch_y + patch_size, patch_x : patch_x + patch_size]
            patch_bytes = patch_image.tobytes()
            patch_hash = sha256_bytes(patch_bytes)

            fragment = ImageForensicFragment(
                fragment_id=f"img_patch_{idx}_{patch_x}_{patch_y}",
                fragment_type="image_patch",
                entropy_score=entropy,
                sampling_method="spatial",
                content_position=idx,
                region_coordinates=(patch_x, patch_y, patch_size, patch_size),
                patch_grid_position=f"grid_{patch_y // patch_size}_{patch_x // patch_size}",
                patch_hash_before=patch_hash,
                patch_hash_after=patch_hash,  # Placeholder
            )

            fragments.append(fragment)

        return fragments

    except Exception:
        return []


# ============================================================================
# VIDEO FRAGMENT SELECTION
# ============================================================================

# Optional video processing dependencies
try:
    import cv2
    import numpy as np

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def select_video_forensic_snippets(
    video_bytes: bytes,
    num_keyframes: int = 3,
) -> List[VideoForensicSnippet]:
    """
    Select keyframe samples for video DNA verification.

    Strategy:
    - Extract frames at temporal positions (25%, 50%, 75%, etc.)
    - Compute perceptual hashes for each keyframe
    - Extract patch hashes from high-entropy regions
    - Compute motion signatures (frame differences)

    Args:
        video_bytes: Video file content (MP4, AVI, MOV, etc.)
        num_keyframes: Number of keyframes to sample

    Returns:
        List of VideoForensicSnippet records

    Raises:
        ImportError: If opencv-python is not installed
        ValueError: If video cannot be decoded
    """
    if not CV2_AVAILABLE:
        raise ImportError(
            "Video fragment selection requires opencv-python. "
            "Install with: pip install opencv-python"
        )

    import tempfile
    import os

    # Write video bytes to temporary file (OpenCV requires file path)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
        tmp_file.write(video_bytes)
        tmp_path = tmp_file.name

    try:
        # Open video with OpenCV
        cap = cv2.VideoCapture(tmp_path)

        if not cap.isOpened():
            raise ValueError("Failed to open video file - may be corrupted or unsupported format")

        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        if total_frames <= 0 or fps <= 0:
            raise ValueError("Invalid video properties - cannot extract frames")

        # Calculate frame positions (evenly distributed)
        if num_keyframes >= total_frames:
            frame_indices = list(range(total_frames))
        else:
            # Distribute evenly: 25%, 50%, 75%, etc.
            frame_indices = [
                int(total_frames * (i + 1) / (num_keyframes + 1)) for i in range(num_keyframes)
            ]

        snippets: List[VideoForensicSnippet] = []

        for idx, frame_idx in enumerate(frame_indices):
            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if not ret or frame is None:
                continue

            # Convert frame to bytes for hashing
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_bytes = frame_rgb.tobytes()

            # Compute frame hash
            _frame_hash = sha256_bytes(frame_bytes)  # noqa: F841

            # Calculate timestamp
            timestamp_ms = int((frame_idx / fps) * 1000)

            # Extract high-entropy patches from frame (similar to image fragments)
            # Use a simplified approach: divide frame into grid and hash patches
            patch_hashes = _extract_frame_patch_hashes(frame_rgb, num_patches=4)

            # Compute motion signature (if not first frame)
            motion_hash = None
            motion_confidence = 0.0

            if idx > 0:
                # Get previous frame for motion comparison
                prev_frame_idx = frame_indices[idx - 1]
                cap.set(cv2.CAP_PROP_POS_FRAMES, prev_frame_idx)
                ret_prev, prev_frame = cap.read()

                if ret_prev and prev_frame is not None:
                    prev_frame_rgb = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2RGB)
                    motion_hash, motion_confidence = _compute_motion_signature(
                        prev_frame_rgb, frame_rgb
                    )

            # Create snippet
            snippet = VideoForensicSnippet(
                fragment_id=f"video_keyframe_{idx}_{timestamp_ms}",
                fragment_type="video_keyframe",
                entropy_score=_estimate_frame_entropy(frame_rgb),
                sampling_method="temporal_keyframe",
                content_position=frame_idx,
                timestamp_ms=timestamp_ms,
                frame_index=frame_idx,
                frame_type="I-Frame",  # Simplified - treating all samples as keyframes
                frame_duration_ms=(
                    int(1000 / fps) if idx == 0 else timestamp_ms - snippets[idx - 1].timestamp_ms
                ),
                frame_patch_hashes=patch_hashes,
                temporal_motion_hash=motion_hash,
                motion_confidence=motion_confidence,
            )

            snippets.append(snippet)

        cap.release()
        return snippets

    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _extract_frame_patch_hashes(frame: np.ndarray, num_patches: int = 4) -> List[str]:
    """
    Extract hashes from high-entropy patches in a video frame.

    Args:
        frame: RGB frame as numpy array (H, W, 3)
        num_patches: Number of patches to extract

    Returns:
        List of SHA-256 hashes (hex strings)
    """
    height, width = frame.shape[:2]

    # Use a grid-based approach for simplicity
    patch_size = min(64, width // 4, height // 4)  # 64x64 or smaller

    if patch_size < 8:
        # Frame too small, hash entire frame
        return [sha256_bytes(frame.tobytes())]

    patches_found = []

    # Sample patches from grid positions
    positions = [
        (width // 4, height // 4),  # Top-left
        (3 * width // 4, height // 4),  # Top-right
        (width // 4, 3 * height // 4),  # Bottom-left
        (3 * width // 4, 3 * height // 4),  # Bottom-right
    ]

    for x, y in positions[:num_patches]:
        # Extract patch
        x_start = max(0, x - patch_size // 2)
        y_start = max(0, y - patch_size // 2)
        x_end = min(width, x_start + patch_size)
        y_end = min(height, y_start + patch_size)

        patch = frame[y_start:y_end, x_start:x_end]
        patch_hash = sha256_bytes(patch.tobytes())
        patches_found.append(patch_hash)

    return patches_found


def _compute_motion_signature(prev_frame: np.ndarray, curr_frame: np.ndarray) -> tuple:
    """
    Compute motion signature between two frames.

    Args:
        prev_frame: Previous frame (RGB)
        curr_frame: Current frame (RGB)

    Returns:
        Tuple of (motion_hash, confidence)
    """
    # Compute frame difference
    diff = cv2.absdiff(prev_frame, curr_frame)

    # Calculate motion magnitude (mean absolute difference)
    motion_magnitude = np.mean(diff)

    # Hash the difference
    motion_hash = sha256_bytes(diff.tobytes())

    # Confidence based on motion magnitude (higher diff = more confident motion)
    confidence = min(1.0, motion_magnitude / 50.0)  # Normalize to 0-1

    return motion_hash, confidence


def _estimate_frame_entropy(frame: np.ndarray) -> float:
    """
    Estimate entropy of a video frame.

    Args:
        frame: RGB frame as numpy array

    Returns:
        Entropy score (0.0-1.0)
    """
    # Convert to grayscale for entropy calculation
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    # Compute histogram
    hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
    hist = hist / hist.sum()  # Normalize

    # Calculate Shannon entropy
    entropy: float = float(-np.sum(hist * np.log2(hist + 1e-10)))

    # Normalize to 0-1 (max entropy for 8-bit = 8.0)
    return entropy / 8.0


# AUDIO FRAGMENT SELECTION
# ============================================================================

# Optional audio processing dependencies
try:
    import wave
    import struct  # noqa: F401

    WAVE_AVAILABLE = True
except ImportError:
    WAVE_AVAILABLE = False


def select_audio_forensic_segments(
    audio_bytes: bytes,
    num_segments: int = 3,
    segment_duration_ms: int = 2000,
) -> List[AudioForensicSegment]:
    """
    Select spectral segments for audio DNA verification.

    Strategy:
    - Extract audio segments at temporal positions (25%, 50%, 75%, etc.)
    - Compute hash signatures for each segment
    - Calculate basic spectral features (if possible)
    - Provide forensic fingerprints for verification

    This is a simplified implementation that works with basic audio formats (WAV).
    For advanced spectral analysis, install librosa: pip install librosa

    Args:
        audio_bytes: Audio file content (WAV format recommended)
        num_segments: Number of segments to select
        segment_duration_ms: Duration per segment in milliseconds

    Returns:
        List of AudioForensicSegment records

    Raises:
        ValueError: If audio cannot be decoded
    """
    from io import BytesIO

    # Try to parse as WAV file
    try:
        with BytesIO(audio_bytes) as audio_stream:
            with wave.open(audio_stream, "rb") as wav_file:
                # Get audio properties
                num_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                num_frames = wav_file.getnframes()

                if num_frames <= 0:
                    raise ValueError("Invalid audio file - no frames found")

                # Calculate duration
                duration_ms = int((num_frames / frame_rate) * 1000)

                # Calculate segment positions (evenly distributed)
                segment_positions_ms = [
                    int(duration_ms * (i + 1) / (num_segments + 1)) for i in range(num_segments)
                ]

                segments = []

                for idx, start_ms in enumerate(segment_positions_ms):
                    # Calculate frame position
                    start_frame = int((start_ms / 1000) * frame_rate)
                    segment_frames = int((segment_duration_ms / 1000) * frame_rate)

                    # Seek to position
                    wav_file.setpos(start_frame)

                    # Read segment data
                    try:
                        audio_data = wav_file.readframes(segment_frames)
                    except Exception:
                        # End of file or read error
                        break

                    if len(audio_data) == 0:
                        break

                    # Compute hash of audio segment
                    segment_hash = sha256_bytes(audio_data)

                    # Calculate basic spectral features
                    spectral_features = _compute_basic_spectral_features(
                        audio_data, sample_width, num_channels, frame_rate
                    )

                    # Create segment
                    segment = AudioForensicSegment(
                        fragment_id=f"audio_segment_{idx}_{start_ms}",
                        fragment_type="audio_spectral_segment",
                        entropy_score=spectral_features["entropy"],
                        sampling_method="temporal_spectral",
                        content_position=start_frame,
                        start_time_ms=start_ms,
                        segment_duration_ms=min(segment_duration_ms, duration_ms - start_ms),
                        spectrogram_hash=segment_hash,
                        frequency_centroid=spectral_features["frequency_centroid"],
                        spectral_flatness=spectral_features["spectral_flatness"],
                        spectrogram_hash_before=segment_hash,  # Same for now
                        spectrogram_hash_after=segment_hash,  # Would change after watermarking
                    )

                    segments.append(segment)

                return segments

    except wave.Error as e:
        raise ValueError(f"Failed to parse audio file as WAV: {e}")
    except Exception as e:
        raise ValueError(f"Failed to process audio file: {e}")


def _compute_basic_spectral_features(
    audio_data: bytes, sample_width: int, num_channels: int, frame_rate: int
) -> dict:
    """
    Compute basic spectral features from audio data.

    This is a simplified implementation without librosa.
    For full spectral analysis, use librosa.

    Args:
        audio_data: Raw audio bytes
        sample_width: Bytes per sample (1, 2, or 4)
        num_channels: Number of audio channels
        frame_rate: Sample rate (Hz)

    Returns:
        Dictionary with basic spectral features
    """
    # Convert bytes to numpy array
    if sample_width == 1:
        dtype = np.uint8
    elif sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32
    else:
        # Unsupported sample width, return defaults
        return {
            "entropy": 0.5,
            "frequency_centroid": frame_rate / 2,
            "spectral_flatness": 0.5,
        }

    try:
        # Parse audio samples
        samples = np.frombuffer(audio_data, dtype=dtype)

        # If stereo, average channels
        if num_channels > 1:
            samples = samples.reshape(-1, num_channels).mean(axis=1)

        # Normalize to float
        if dtype == np.uint8:
            samples = (samples - 128) / 128.0
        elif dtype == np.int16:
            samples = samples / 32768.0
        elif dtype == np.int32:
            samples = samples / 2147483648.0

        # Compute entropy from amplitude distribution
        hist, _ = np.histogram(samples, bins=256, range=(-1, 1))
        hist = hist / (hist.sum() + 1e-10)  # Normalize
        entropy: float = float(-np.sum(hist * np.log2(hist + 1e-10)))
        entropy_normalized = entropy / 8.0  # Normalize to 0-1

        # Compute FFT for spectral features (simplified)
        if len(samples) > 0:
            fft = np.fft.rfft(samples)
            magnitude = np.abs(fft)

            # Frequency centroid (weighted average frequency)
            frequencies = np.fft.rfftfreq(len(samples), 1 / frame_rate)
            if magnitude.sum() > 0:
                frequency_centroid = np.sum(frequencies * magnitude) / magnitude.sum()
            else:
                frequency_centroid = frame_rate / 2

            # Spectral flatness (geometric mean / arithmetic mean)
            if len(magnitude) > 0 and magnitude.sum() > 0:
                geometric_mean = np.exp(np.mean(np.log(magnitude + 1e-10)))
                arithmetic_mean = np.mean(magnitude)
                spectral_flatness = geometric_mean / (arithmetic_mean + 1e-10)
            else:
                spectral_flatness = 0.5
        else:
            frequency_centroid = frame_rate / 2
            spectral_flatness = 0.5

        return {
            "entropy": min(1.0, max(0.0, entropy_normalized)),
            "frequency_centroid": float(frequency_centroid),
            "spectral_flatness": min(1.0, max(0.0, float(spectral_flatness))),
        }

    except Exception:
        # Fallback to defaults if computation fails
        return {
            "entropy": 0.5,
            "frequency_centroid": frame_rate / 2,
            "spectral_flatness": 0.5,
        }


# ============================================================================
# FORENSIC FRAGMENT SET ASSEMBLY
# ============================================================================


def create_forensic_fragment_set(
    artifact: bytes,
    artifact_type: str,
    enable_fragments: bool = True,
) -> Optional[ForensicFragmentSet]:
    """
    Create a ForensicFragmentSet (DNA records) for an artifact.

    This assembles the multi-point samples for legal-grade verification.

    Args:
        artifact: Artifact content (bytes or will be converted)
        artifact_type: 'text', 'image', 'pdf', 'video', 'audio'
        enable_fragments: Whether to generate fragments

    Returns:
        ForensicFragmentSet with all selected fragments, or None
    """
    if not enable_fragments:
        return None

    # Convert if needed
    if isinstance(artifact, str):
        artifact_bytes = artifact.encode("utf-8")
    else:
        artifact_bytes = artifact

    fragment_set = ForensicFragmentSet(
        fragment_count=0,
        sampling_strategy="multi_point",
        total_coverage_percent=0.0,
    )

    try:
        if artifact_type == "text":
            artifact_text = artifact.decode("utf-8") if isinstance(artifact, bytes) else artifact
            fragments = select_text_forensic_fragments(
                artifact_text,
                fragment_hash_before="",  # Computed by caller
                fragment_hash_after="",  # Computed by caller
            )
            fragment_set.text_fragments = fragments
            fragment_set.sampling_strategy = "multi_point"  # 3-point sampling
            fragment_set.fragment_count = len(fragments)

        elif artifact_type == "image":
            fragments = select_image_forensic_patches(artifact_bytes, num_patches=4)
            fragment_set.image_fragments = fragments
            fragment_set.sampling_strategy = "spatial_diversity"
            fragment_set.fragment_count = len(fragments)

        elif artifact_type == "video":
            # Phase 2
            pass

        elif artifact_type == "audio":
            # Phase 2
            pass

        # Compute aggregate statistics
        if fragment_set.all_fragments:
            avg_entropy = sum(f.entropy_score for f in fragment_set.all_fragments) / len(
                fragment_set.all_fragments
            )
            fragment_set.cumulative_entropy_score = avg_entropy

        return fragment_set if fragment_set.fragment_count > 0 else None

    except Exception:
        return None
