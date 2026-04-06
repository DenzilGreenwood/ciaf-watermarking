"""
CIAF Watermarking - Video Core Functions

Main video watermarking evidence building.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional, Tuple
import uuid

from ..models import (
    ArtifactEvidence,
    ArtifactType,
    ArtifactFingerprint,
    ArtifactHashSet,
    ForensicFragmentSet,
    WatermarkDescriptor,
    WatermarkType,
    sha256_bytes,
    sha256_text,
    utc_now_iso,
)
from .metadata import apply_video_metadata_watermark, get_video_info
from .visual import VideoWatermarkSpec, apply_video_visual_watermark


def build_video_artifact_evidence(
    video_bytes: bytes,
    model_id: str,
    model_version: str,
    actor_id: str,
    prompt: str,
    verification_base_url: str,
    watermark_mode: str = "metadata",
    watermark_config: Optional[Dict[str, Any]] = None,
    enable_forensic_fragments: bool = True,
) -> Tuple[ArtifactEvidence, bytes]:
    """
    Build forensic evidence for watermarked video artifact.

    Watermarking Modes:
    - "metadata": Inject metadata without re-encoding (recommended)
    - "visual": Add visible text overlay (requires re-encoding)
    - "qr": Add QR code overlay (requires re-encoding)
    - "hybrid": Metadata + visual (requires re-encoding)

    Args:
        video_bytes: Original video data (MP4, AVI, MOV, etc.)
        model_id: AI model identifier
        model_version: Model version
        actor_id: User/system identifier
        prompt: Generation prompt
        verification_base_url: Base URL for verification
        watermark_mode: Watermarking strategy
        watermark_config: Mode-specific configuration
        enable_forensic_fragments: Extract keyframe fragments

    Returns:
        Tuple of (evidence, watermarked_video_bytes)

    Raises:
        ImportError: If ffmpeg-python not installed
        ValueError: If video format unsupported

    Example:
        >>> with open("ai_generated_video.mp4", "rb") as f:
        ...     video_bytes = f.read()
        >>>
        >>> evidence, watermarked = build_video_artifact_evidence(
        ...     video_bytes=video_bytes,
        ...     model_id="sora-v1",
        ...     model_version="2026-03",
        ...     actor_id="user:director-123",
        ...     prompt="Create cinematic intro",
        ...     verification_base_url="https://vault.openai.com",
        ...     watermark_mode="metadata",
        ... )
        >>>
        >>> # Save watermarked video
        >>> with open("watermarked.mp4", "wb") as f:
        ...     f.write(watermarked)
        >>>
        >>> # Verify later
        >>> from ciaf.watermarks.video import verify_video_artifact
        >>> result = verify_video_artifact(watermarked, evidence)
        >>> print(f"Authentic: {result.is_authenticated()}")
    """
    config = watermark_config or {}

    config = watermark_config or {}

    watermark_id = f"wmk-{uuid.uuid4().hex[:12]}"
    timestamp = utc_now_iso()
    artifact_id = f"art-{uuid.uuid4().hex[:12]}"

    verification_url = f"{verification_base_url.rstrip('/')}/verify/{artifact_id}"

    hash_before = sha256_bytes(video_bytes)

    try:
        video_info = get_video_info(video_bytes)
    except Exception:
        video_info = {
            "duration": 0,
            "size_bytes": len(video_bytes),
            "codec": "unknown",
            "width": 0,
            "height": 0,
            "format": "mp4",
        }
    if watermark_mode == "metadata":
        watermarked_bytes = apply_video_metadata_watermark(
            video_bytes=video_bytes,
            watermark_id=watermark_id,
            verification_url=verification_url,
            model_id=model_id,
            timestamp=timestamp,
            metadata=config.get("extra_metadata"),
        )
        watermark_type = WatermarkType.METADATA
        embed_method = "video_container_metadata"
        location = "metadata"

    elif watermark_mode == "visual":
        watermarked_bytes = apply_video_metadata_watermark(
            video_bytes=video_bytes,
            watermark_id=watermark_id,
            verification_url=verification_url,
            model_id=model_id,
            timestamp=timestamp,
        )

        spec = VideoWatermarkSpec(
            text=config.get("text", f"AI Generated - {model_id}"),
            opacity=config.get("opacity", 0.5),
            position=config.get("position", "bottom_right"),
            font_size=config.get("font_size", 24),
            font_color=config.get("font_color", (255, 255, 255)),
        )

        watermarked_bytes = apply_video_visual_watermark(
            video_bytes=watermarked_bytes,
            watermark_spec=spec,
            verification_url=verification_url,
        )
        watermark_type = WatermarkType.VISIBLE
        embed_method = "video_drawtext_overlay"
        location = spec.position

    elif watermark_mode == "hybrid":
        watermarked_bytes = apply_video_metadata_watermark(
            video_bytes=video_bytes,
            watermark_id=watermark_id,
            verification_url=verification_url,
            model_id=model_id,
            timestamp=timestamp,
        )

        spec = VideoWatermarkSpec(
            text=config.get("text", "AI Generated"),
            opacity=config.get("opacity", 0.3),
            position=config.get("position", "bottom_right"),
            font_size=config.get("font_size", 18),
        )

        watermarked_bytes = apply_video_visual_watermark(
            video_bytes=watermarked_bytes,
            watermark_spec=spec,
            verification_url=verification_url,
        )
        watermark_type = WatermarkType.HYBRID
        embed_method = "video_metadata_plus_overlay"
        location = spec.position

    else:
        raise ValueError(
            f"Unknown watermark mode: {watermark_mode}. "
            f"Use 'metadata', 'visual', or 'hybrid'"
        )

    hash_after = sha256_bytes(watermarked_bytes)

    perceptual_hash_before = None
    perceptual_hash_after = None
    try:
        from ..hashing import perceptual_hash_video

        perceptual_hash_before = perceptual_hash_video(video_bytes)
        perceptual_hash_after = perceptual_hash_video(watermarked_bytes)
    except Exception:
        pass

    hashes = ArtifactHashSet(
        content_hash_before_watermark=hash_before,
        content_hash_after_watermark=hash_after,
        perceptual_hash_before=perceptual_hash_before,
        perceptual_hash_after=perceptual_hash_after,
    )

    fingerprints: List[ArtifactFingerprint] = []

    if enable_forensic_fragments:
        try:
            from ..fragment_selection import select_video_forensic_snippets

            fragments = select_video_forensic_snippets(
                video_bytes=video_bytes,
                num_keyframes=config.get("num_keyframes", 3),
            )

            for frag in fragments:
                fingerprints.append(
                    ArtifactFingerprint(
                        algorithm="keyframe_phash",
                        value=frag.model_dump_json(),
                        role="video_keyframe_fragment",
                        confidence=frag.motion_confidence,
                    )
                )

            hashes.forensic_fragments = ForensicFragmentSet(
                fragment_count=len(fragments),
                sampling_strategy="temporal_keyframes",
                total_coverage_percent=float(config.get("coverage_percent", 15.0)),
                video_snippets=fragments,
                cumulative_entropy_score=0.0,
            )
        except Exception:
            pass

    watermark = WatermarkDescriptor(
        watermark_id=watermark_id,
        watermark_type=watermark_type,
        tag_text=f"Video Watermark: {watermark_id}",
        verification_url=verification_url,
        embed_method=embed_method,
        removal_resistance="medium" if watermark_mode == "metadata" else "high",
        location=location,
    )

    evidence = ArtifactEvidence(
        artifact_id=artifact_id,
        artifact_type=ArtifactType.VIDEO,
        mime_type=f"video/{video_info.get('format', 'mp4').split(',')[0]}",
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
            "video_duration_seconds": video_info.get("duration", 0),
            "video_codec": video_info.get("codec", "unknown"),
            "video_resolution": f"{video_info.get('width', 0)}x{video_info.get('height', 0)}",
            "video_size_bytes": len(video_bytes),
            "watermarked_size_bytes": len(watermarked_bytes),
            "watermark_mode": watermark_mode,
        },
    )

    evidence.hashes.canonical_receipt_hash = sha256_bytes(evidence.to_canonical_bytes())

    return evidence, watermarked_bytes
