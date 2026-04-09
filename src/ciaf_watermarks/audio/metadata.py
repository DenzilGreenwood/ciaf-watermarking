"""
CIAF Watermarking - Audio Metadata Functions

Audio metadata watermarking using ffmpeg (lossless).

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

import tempfile
import os
from typing import Optional, Dict, Any

# Check if ffmpeg-python is available
try:
    import ffmpeg

    FFMPEG_AVAILABLE = True
except ImportError:
    ffmpeg = None  # For mocking in tests
    FFMPEG_AVAILABLE = False


def apply_audio_metadata_watermark(
    audio_bytes: bytes,
    watermark_id: str,
    verification_url: str,
    model_id: str,
    timestamp: str,
    metadata: Optional[Dict[str, str]] = None,
) -> bytes:
    """
    Apply metadata watermark to audio file without re-encoding.

    Uses ffmpeg to inject metadata tags (ID3 for MP3, vorbis comments for OGG/OPUS, etc.)

    Args:
        audio_bytes: Original audio data
        watermark_id: Unique watermark identifier
        verification_url: Verification URL
        model_id: AI model identifier
        timestamp: ISO 8601 timestamp
        metadata: Additional metadata fields

    Returns:
        Watermarked audio bytes

    Raises:
        ImportError: If ffmpeg-python not installed
        RuntimeError: If ffmpeg processing fails

    Example:
        >>> watermarked = apply_audio_metadata_watermark(
        ...     audio_bytes=audio_data,
        ...     watermark_id="wmk-audio-123",
        ...     verification_url="https://vault.example.com/verify/wmk-audio-123",
        ...     model_id="voice-cloning-v1",
        ...     timestamp="2026-04-05T10:30:00Z"
        ... )
    """
    if not FFMPEG_AVAILABLE:
        raise ImportError(
            "ffmpeg-python is required for audio metadata watermarking. "
            "Install with: pip install ffmpeg-python"
        )
    # Handle invalid audio data gracefully
    if not audio_bytes or len(audio_bytes) < 100:
        raise ValueError("Audio data is too small or invalid")
    # Create temporary files
    _fd_input_path, input_path = tempfile.mkstemp(suffix=".mp3")
    os.close(_fd_input_path)
    _fd_output_path, output_path = tempfile.mkstemp(suffix=".mp3")
    os.close(_fd_output_path)

    try:
        # Write input audio
        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        # Build metadata dictionary
        meta_dict = {
            "comment": f"CIAF Watermark: {watermark_id}",
            "title": f"AI Generated Audio - {model_id}",
            "artist": "CIAF Watermarking System",
            "album": "AI Generated Content",
            "date": timestamp.split("T")[0],  # Extract date
            "copyright": f"Verification: {verification_url}",
            "description": f"Model: {model_id}, Watermark: {watermark_id}",
        }

        # Add custom metadata
        if metadata:
            for key, value in metadata.items():
                # Use custom tags
                meta_dict[f"CIAF_{key}"] = value

        # Apply metadata using ffmpeg (codec copy - no re-encoding!)
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            acodec="copy",  # Copy audio codec (no re-encoding)
            **{"metadata": f"comment={meta_dict['comment']}"},
            **{"metadata:g:0": f"title={meta_dict['title']}"},
            **{"metadata:g:1": f"artist={meta_dict['artist']}"},
            **{"metadata:g:2": f"album={meta_dict['album']}"},
            **{"metadata:g:3": f"copyright={meta_dict['copyright']}"},
        )

        # Run ffmpeg
        ffmpeg.run(
            stream,
            capture_stdout=True,
            capture_stderr=True,
            overwrite_output=True,
            quiet=True,
        )

        # Read output
        with open(output_path, "rb") as f:
            watermarked_bytes = f.read()

        return watermarked_bytes

    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else "Unknown error"
        raise RuntimeError(f"ffmpeg metadata injection failed: {stderr}")

    finally:
        # Cleanup
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)


def extract_audio_metadata_watermark(audio_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Extract CIAF watermark metadata from audio file.

    Args:
        audio_bytes: Audio data to check

    Returns:
        Dictionary with watermark metadata, or None if not found

    Example:
        >>> metadata = extract_audio_metadata_watermark(audio_bytes)
        >>> if metadata:
        ...     print(f"Watermark ID: {metadata['watermark_id']}")
    """
    if not FFMPEG_AVAILABLE:
        return None

    _fd_input_path, input_path = tempfile.mkstemp(suffix=".mp3")
    os.close(_fd_input_path)

    try:
        # Write audio to temp file
        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        # Probe metadata
        probe = ffmpeg.probe(input_path)

        # Extract format tags
        format_tags = probe.get("format", {}).get("tags", {})

        # Look for CIAF watermark in comment
        comment = format_tags.get("comment", "")

        if "CIAF Watermark:" in comment:
            # Extract watermark ID
            watermark_id = comment.replace("CIAF Watermark:", "").strip()

            # Extract other metadata
            return {
                "watermark_id": watermark_id,
                "title": format_tags.get("title"),
                "artist": format_tags.get("artist"),
                "album": format_tags.get("album"),
                "copyright": format_tags.get("copyright"),
                "description": format_tags.get("description"),
                "verification_url": (
                    format_tags.get("copyright", "").replace("Verification: ", "").strip()
                    if "Verification:" in format_tags.get("copyright", "")
                    else None
                ),
            }

        return None

    except Exception:
        return None

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


def has_audio_watermark(audio_bytes: bytes) -> bool:
    """
    Check if audio has CIAF watermark metadata.

    Args:
        audio_bytes: Audio data to check

    Returns:
        True if watermark detected
    """
    metadata = extract_audio_metadata_watermark(audio_bytes)
    return metadata is not None and "watermark_id" in metadata


def get_audio_info(audio_bytes: bytes) -> Dict[str, Any]:
    """
    Get audio file information using ffmpeg probe.

    Args:
        audio_bytes: Audio data

    Returns:
        Dictionary with audio properties
    """
    if not FFMPEG_AVAILABLE:
        return {
            "duration": 0,
            "size_bytes": len(audio_bytes),
            "codec": "unknown",
            "sample_rate": 0,
            "channels": 0,
            "bitrate": 0,
            "format": "unknown",
        }

    _fd_input_path, input_path = tempfile.mkstemp(suffix=".mp3")
    os.close(_fd_input_path)

    try:
        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        probe = ffmpeg.probe(input_path)

        # Get format info
        format_info = probe.get("format", {})

        # Get first audio stream
        audio_stream: Dict[str, Any] = next(
            (s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), {}
        )

        return {
            "duration": float(format_info.get("duration", 0)),
            "size_bytes": int(format_info.get("size", len(audio_bytes))),
            "codec": audio_stream.get("codec_name", "unknown"),
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": int(audio_stream.get("channels", 0)),
            "bitrate": int(format_info.get("bit_rate", 0)),
            "format": format_info.get("format_name", "unknown"),
        }

    except Exception:
        # Re-raise ffmpeg errors (invalid audio, unsupported format, etc.)
        raise

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


__all__ = [
    "apply_audio_metadata_watermark",
    "extract_audio_metadata_watermark",
    "has_audio_watermark",
    "get_audio_info",
    "FFMPEG_AVAILABLE",
]
