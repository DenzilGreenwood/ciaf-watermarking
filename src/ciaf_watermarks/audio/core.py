"""
CIAF Watermarking - Audio Core Functions

Main audio artifact evidence building.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from typing import Tuple, Optional, Dict, Any, List
import uuid

from ..models import (
    ArtifactEvidence,
    ArtifactType,
    WatermarkType,
    WatermarkDescriptor,
    ArtifactHashSet,
    ArtifactFingerprint,
    utc_now_iso,
    sha256_bytes,
    sha256_text,
)

from .metadata import apply_audio_metadata_watermark, get_audio_info
from .spectral import apply_audio_spectral_watermark, AudioWatermarkSpec

# Import ffmpeg at module level for testing/mocking
try:
    import ffmpeg
except ImportError:
    ffmpeg = None


def build_audio_artifact_evidence(
    audio_bytes: bytes,
    model_id: str,
    model_version: str,
    actor_id: str,
    prompt: str,
    verification_base_url: str,
    watermark_mode: str = "metadata",
    watermark_config: Optional[Dict[str, Any]] = None,
    watermark_spec: Optional[Any] = None,
    enable_forensic_fragments: bool = True,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[ArtifactEvidence, bytes]:
    """
    Build forensic evidence for watermarked audio artifact.

    Watermarking Modes:
    - "metadata": Inject metadata without re-encoding (recommended)
    - "spectral": Inaudible frequency watermark (requires re-encoding)
    - "hybrid": Metadata + spectral (requires re-encoding)

    Args:
        audio_bytes: Original audio data (MP3, WAV, OGG, etc.)
        model_id: AI model identifier
        model_version: Model version
        actor_id: User/system identifier
        prompt: Generation prompt
        verification_base_url: Base URL for verification
        watermark_mode: Watermarking strategy
        watermark_config: Mode-specific configuration
        watermark_spec: Pre-configured AudioWatermarkSpec (overrides watermark_config)
        enable_forensic_fragments: Extract audio segments
        additional_metadata: Additional metadata to include in evidence

    Returns:
        Tuple of (evidence, watermarked_audio_bytes)

    Raises:
        ImportError: If ffmpeg-python or librosa not installed
        ValueError: If audio format unsupported

    Example:
        >>> with open("ai_generated_audio.mp3", "rb") as f:
        ...     audio_bytes = f.read()
        >>>
        >>> evidence, watermarked = build_audio_artifact_evidence(
        ...     audio_bytes=audio_bytes,
        ...     model_id="voice-cloning-v1",
        ...     model_version="2026-03",
        ...     actor_id="user:speaker-123",
        ...     prompt="Clone voice reading script",
        ...     verification_base_url="https://vault.example.com",
        ...     watermark_mode="metadata",
        ... )
        >>>
        >>> # Save watermarked audio
        >>> with open("watermarked.mp3", "wb") as f:
        ...     f.write(watermarked)
    """
    config = watermark_config or {}

    # Generate watermark ID
    watermark_id = f"wmk-{uuid.uuid4().hex[:12]}"
    timestamp = utc_now_iso()
    artifact_id = f"art-{uuid.uuid4().hex[:12]}"

    # Build verification URL
    verification_url = f"{verification_base_url}/verify/{watermark_id}"

    # 1. Compute hash BEFORE watermarking
    hash_before = sha256_bytes(audio_bytes)

    # Get audio info
    try:
        audio_info = get_audio_info(audio_bytes)
    except Exception:
        # If we can't get info, use defaults
        audio_info = {
            "duration": 0,
            "size_bytes": len(audio_bytes),
            "codec": "unknown",
            "sample_rate": 0,
            "channels": 0,
            "bitrate": 0,
        }

    # 2. Apply watermark based on mode
    if watermark_mode == "metadata":
        # Metadata-only watermarking (no re-encoding)
        watermarked_bytes = apply_audio_metadata_watermark(
            audio_bytes=audio_bytes,
            watermark_id=watermark_id,
            verification_url=verification_url,
            model_id=model_id,
            timestamp=timestamp,
            metadata=config.get("extra_metadata"),
        )
        watermark_type = WatermarkType.METADATA

    elif watermark_mode == "spectral":
        # Spectral watermarking (requires re-encoding)
        # First apply metadata
        watermarked_bytes = apply_audio_metadata_watermark(
            audio_bytes=audio_bytes,
            watermark_id=watermark_id,
            verification_url=verification_url,
            model_id=model_id,
            timestamp=timestamp,
        )

        # Use provided watermark_spec or create from config
        if watermark_spec is not None:
            spec = watermark_spec
        else:
            spec = AudioWatermarkSpec(
                strength=config.get("strength", 0.1),
                frequency_band=config.get("frequency_band", "high"),
                carrier_freq=config.get("carrier_freq", 18000),
                spread_spectrum=config.get("spread_spectrum", True),
            )

        watermarked_bytes = apply_audio_spectral_watermark(
            audio_bytes=watermarked_bytes,
            watermark_spec=spec,
            watermark_data=watermark_id,
        )
        watermark_type = WatermarkType.EMBEDDED

    elif watermark_mode == "hybrid" or watermark_mode == "dual":
        # Metadata + spectral ("dual" is alias for "hybrid")
        watermarked_bytes = apply_audio_metadata_watermark(
            audio_bytes=audio_bytes,
            watermark_id=watermark_id,
            verification_url=verification_url,
            model_id=model_id,
            timestamp=timestamp,
        )

        spec = AudioWatermarkSpec(
            strength=config.get("strength", 0.05),
            frequency_band=config.get("frequency_band", "high"),
            carrier_freq=config.get("carrier_freq", 18000),
        )

        watermarked_bytes = apply_audio_spectral_watermark(
            audio_bytes=watermarked_bytes,
            watermark_spec=spec,
            watermark_data=watermark_id,
        )
        watermark_type = WatermarkType.HYBRID

    else:
        raise ValueError(
            f"Unknown watermark mode: {watermark_mode}. "
            f"Use 'metadata', 'spectral', 'hybrid', or 'dual'"
        )

    # 3. Compute hash AFTER watermarking
    hash_after = sha256_bytes(watermarked_bytes)

    # 4. Compute perceptual hash (chromaprint-based)
    perceptual_hash_before = None
    perceptual_hash_after = None

    try:
        from ..hashing import perceptual_hash_audio

        perceptual_hash_before = perceptual_hash_audio(audio_bytes)
        perceptual_hash_after = perceptual_hash_audio(watermarked_bytes)
    except Exception:
        # If perceptual hashing fails, continue without it
        pass

    # 5. Create hash set
    hashes = ArtifactHashSet(
        content_hash_before_watermark=hash_before,
        content_hash_after_watermark=hash_after,
        perceptual_hash_before=perceptual_hash_before,
        perceptual_hash_after=perceptual_hash_after,
    )

    # 6. Extract forensic fragments (audio segments)
    fingerprints: List[ArtifactFingerprint] = []

    if enable_forensic_fragments:
        try:
            from ..fragment_selection import select_audio_forensic_segments

            fragments = select_audio_forensic_segments(
                audio_bytes=audio_bytes,
                num_segments=config.get("num_segments", 3),
            )
            # Convert to ArtifactFingerprint
            for frag in fragments:
                fingerprint = ArtifactFingerprint(
                    role="audio_segment",
                    value=frag.model_dump_json(),
                    algorithm="spectral_hash",
                    confidence=frag.entropy_score,
                )
                fingerprints.append(fingerprint)
        except Exception:
            # If fragment selection fails, continue without it
            pass

    # 7. Create watermark descriptor
    watermark = WatermarkDescriptor(
        watermark_id=watermark_id,
        watermark_type=watermark_type,
        location=watermark_mode,
        verification_url=verification_url,
    )

    # 8. Build evidence
    evidence = ArtifactEvidence(
        artifact_id=artifact_id,
        artifact_type=ArtifactType.AUDIO,
        mime_type=f"audio/{audio_info.get('format', 'mpeg')}",
        created_at=timestamp,
        model_id=model_id,
        model_version=model_version,
        actor_id=actor_id,
        prompt_hash=sha256_text(prompt),
        output_hash_raw=hash_before,
        output_hash_distributed=hash_after,
        watermark=watermark,
        hashes=hashes,
        fingerprints=fingerprints,
        metadata={
            "duration_seconds": audio_info.get("duration", 0),
            "audio_duration_seconds": audio_info.get("duration", 0),
            "codec": audio_info.get("codec", "unknown"),
            "audio_codec": audio_info.get("codec", "unknown"),
            "sample_rate": audio_info.get("sample_rate", 0),
            "audio_sample_rate": audio_info.get("sample_rate", 0),
            "channels": audio_info.get("channels", 0),
            "audio_channels": audio_info.get("channels", 0),
            "bitrate": audio_info.get("bitrate", 0),
            "audio_bitrate": audio_info.get("bitrate", 0),
            "audio_size_bytes": len(audio_bytes),
            "watermarked_size_bytes": len(watermarked_bytes),
            "watermark_mode": watermark_mode,
            **(additional_metadata or {}),
        },
    )

    return evidence, watermarked_bytes


__all__ = [
    "build_audio_artifact_evidence",
]
