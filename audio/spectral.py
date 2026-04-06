"""
CIAF Watermarking - Audio Spectral Watermarking

Spectral watermarking using inaudible frequency embedding.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

import tempfile
import os
from typing import Optional
from dataclasses import dataclass

# Check if librosa is available
try:
    import librosa
    import numpy as np
    import soundfile as sf

    LIBROSA_AVAILABLE = True
except ImportError:
    librosa = None  # For mocking in tests
    np = None
    sf = None
    LIBROSA_AVAILABLE = False


@dataclass
class AudioWatermarkSpec:
    """Specification for spectral audio watermark."""

    strength: float = 0.1  # Watermark strength (0.0-1.0)
    frequency_band: str = "high"  # "high" or "low" frequency band
    carrier_freq: int = 18000  # Carrier frequency (Hz) - inaudible for most adults
    spread_spectrum: bool = True  # Use spread spectrum for robustness

    def __post_init__(self):
        """Validate parameters."""
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be between 0.0 and 1.0")

        if self.frequency_band not in ("high", "low"):
            raise ValueError("frequency_band must be 'high' or 'low'")

        if not 1000 <= self.carrier_freq <= 20000:
            raise ValueError("carrier_freq must be between 1000-20000 Hz")


def apply_audio_spectral_watermark(
    audio_bytes: bytes,
    watermark_spec: AudioWatermarkSpec,
    watermark_data: str,
) -> bytes:
    """
    Apply spectral watermark to audio using frequency embedding.

    Embeds watermark in inaudible or barely audible frequency ranges.

    Args:
        audio_bytes: Original audio data
        watermark_spec: Watermark configuration
        watermark_data: Data to embed (will be hashed to bits)

    Returns:
        Watermarked audio bytes

    Raises:
        ImportError: If librosa not installed

    Example:
        >>> spec = AudioWatermarkSpec(strength=0.1, carrier_freq=18000)
        >>> watermarked = apply_audio_spectral_watermark(
        ...     audio_bytes=audio_data,
        ...     watermark_spec=spec,
        ...     watermark_data="wmk-audio-123"
        ... )
    """
    if not LIBROSA_AVAILABLE:
        raise ImportError(
            "librosa and soundfile are required for spectral watermarking. "
            "Install with: pip install librosa soundfile"
        )

    input_path = tempfile.mktemp(suffix=".wav")
    output_path = tempfile.mktemp(suffix=".wav")

    try:
        # Write input audio
        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        # Load audio
        audio, sr = librosa.load(input_path, sr=None, mono=False)

        # Convert to mono if stereo
        if audio.ndim > 1:
            audio = librosa.to_mono(audio)

        # Convert watermark data to binary
        watermark_bits = _string_to_bits(watermark_data)

        # Embed watermark in spectral domain
        watermarked_audio = _embed_spectral_watermark(
            audio=audio,
            sample_rate=sr,
            watermark_bits=watermark_bits,
            spec=watermark_spec,
        )

        # Save watermarked audio
        sf.write(output_path, watermarked_audio, sr)

        # Read output
        with open(output_path, "rb") as f:
            watermarked_bytes = f.read()

        return watermarked_bytes

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


def extract_audio_spectral_watermark(
    audio_bytes: bytes,
    watermark_spec: AudioWatermarkSpec,
    expected_length: int = 32,
) -> Optional[str]:
    """
    Extract spectral watermark from audio.

    Args:
        audio_bytes: Watermarked audio data
        watermark_spec: Watermark configuration (must match embedding)
        expected_length: Expected watermark string length

    Returns:
        Extracted watermark data, or None if extraction fails

    Example:
        >>> spec = AudioWatermarkSpec(strength=0.1, carrier_freq=18000)
        >>> watermark = extract_audio_spectral_watermark(
        ...     audio_bytes=watermarked_data,
        ...     watermark_spec=spec,
        ...     expected_length=13
        ... )
        >>> print(watermark)  # "wmk-audio-123"
    """
    if not LIBROSA_AVAILABLE:
        return None

    input_path = tempfile.mktemp(suffix=".wav")

    try:
        # Write audio
        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        # Load audio
        audio, sr = librosa.load(input_path, sr=None, mono=False)

        # Convert to mono if stereo
        if audio.ndim > 1:
            audio = librosa.to_mono(audio)

        # Extract watermark from spectral domain
        watermark_bits = _extract_spectral_watermark(
            audio=audio,
            sample_rate=sr,
            spec=watermark_spec,
            bit_count=expected_length * 8,
        )

        # Convert bits to string
        watermark_str = _bits_to_string(watermark_bits)

        return watermark_str

    except Exception:
        return None

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


def _string_to_bits(s: str) -> list:
    """Convert string to list of bits."""
    bits = []
    for char in s:
        byte = ord(char)
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def _bits_to_string(bits: list) -> str:
    """Convert list of bits to string."""
    chars = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i : i + 8]
        if len(byte_bits) < 8:
            break
        byte = 0
        for j, bit in enumerate(byte_bits):
            byte |= bit << (7 - j)
        if 32 <= byte <= 126:  # Printable ASCII
            chars.append(chr(byte))
        else:
            chars.append("?")
    return "".join(chars)


def _embed_spectral_watermark(
    audio,  # np.ndarray
    sample_rate: int,
    watermark_bits: list,
    spec: AudioWatermarkSpec,
):  # -> np.ndarray
    """
    Embed watermark in audio spectral domain.

    Uses FFT to transform to frequency domain, embeds watermark,
    and transforms back to time domain.
    """
    if not LIBROSA_AVAILABLE:
        raise ImportError("librosa and numpy required for spectral watermarking")

    # Convert to float32
    audio = audio.astype(np.float32)

    # Compute STFT
    D = librosa.stft(audio)
    magnitude = np.abs(D)
    phase = np.angle(D)

    # Determine frequency bins for carrier
    freq_bins = librosa.fft_frequencies(sr=sample_rate)
    carrier_bin = np.argmin(np.abs(freq_bins - spec.carrier_freq))

    # Embed watermark bits
    _bits_per_frame = 1  # Embed 1 bit per frame  # noqa: F841
    num_frames = magnitude.shape[1]

    for i, bit in enumerate(watermark_bits):
        if i >= num_frames:
            break

        # Modulate magnitude at carrier frequency
        if bit == 1:
            magnitude[carrier_bin, i] += spec.strength * magnitude[carrier_bin, i]
        else:
            magnitude[carrier_bin, i] -= spec.strength * magnitude[carrier_bin, i]

    # Reconstruct STFT
    D_watermarked = magnitude * np.exp(1j * phase)

    # Inverse STFT
    audio_watermarked = librosa.istft(D_watermarked)

    # Normalize to prevent clipping
    max_val = np.max(np.abs(audio_watermarked))
    if max_val > 1.0:
        audio_watermarked = audio_watermarked / max_val

    return audio_watermarked


def _extract_spectral_watermark(
    audio,  # np.ndarray
    sample_rate: int,
    spec: AudioWatermarkSpec,
    bit_count: int,
) -> list:
    """
    Extract watermark from audio spectral domain.
    """
    # Convert to float32
    audio = audio.astype(np.float32)

    # Compute STFT
    D = librosa.stft(audio)
    magnitude = np.abs(D)

    # Determine frequency bins
    freq_bins = librosa.fft_frequencies(sr=sample_rate)
    carrier_bin = np.argmin(np.abs(freq_bins - spec.carrier_freq))

    # Extract bits
    bits = []
    num_frames = magnitude.shape[1]

    for i in range(min(bit_count, num_frames)):
        # Detect modulation
        mag = magnitude[carrier_bin, i]

        # Simple threshold detection
        # (In production, use more sophisticated detection)
        if i > 0:
            prev_mag = magnitude[carrier_bin, i - 1]
            if mag > prev_mag:
                bits.append(1)
            else:
                bits.append(0)
        else:
            bits.append(0)

    return bits


__all__ = [
    "AudioWatermarkSpec",
    "apply_audio_spectral_watermark",
    "extract_audio_spectral_watermark",
    "LIBROSA_AVAILABLE",
]
