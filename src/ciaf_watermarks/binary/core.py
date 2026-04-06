"""
CIAF Watermarking - Binary Core Functions

Main binary artifact evidence building.

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

from .metadata import apply_binary_metadata_watermark, get_binary_info


def build_binary_artifact_evidence(
    binary_bytes: bytes,
    model_id: str,
    model_version: str,
    actor_id: str,
    prompt: str,
    verification_base_url: str,
    watermark_config: Optional[Dict[str, Any]] = None,
    enable_forensic_fragments: bool = False,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[ArtifactEvidence, bytes]:
    """
    Build forensic evidence for watermarked binary artifact.

    Watermarking Mode:
    - Metadata: Append custom CIAF watermark block (doesn't corrupt binary)

    Args:
        binary_bytes: Original binary data
        model_id: AI model identifier
        model_version: Model version
        actor_id: User/system identifier
        prompt: Generation prompt
        verification_base_url: Base URL for verification
        watermark_config: Configuration options
        enable_forensic_fragments: Extract binary fragments (not recommended)
        additional_metadata: Additional metadata to include in evidence

    Returns:
        Tuple of (evidence, watermarked_binary_bytes)

    Raises:
        ValueError: If binary format unsupported

    Example:
        >>> with open("ai_generated_code.exe", "rb") as f:
        ...     binary_bytes = f.read()
        >>>
        >>> evidence, watermarked = build_binary_artifact_evidence(
        ...     binary_bytes=binary_bytes,
        ...     model_id="code-gen-v1",
        ...     model_version="2026-03",
        ...     actor_id="user:developer-123",
        ...     prompt="Generate compiler binary",
        ...     verification_base_url="https://vault.example.com",
        ... )
        >>>
        >>> # Save watermarked binary
        >>> with open("watermarked_code.exe", "wb") as f:
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
    hash_before = sha256_bytes(binary_bytes)

    # Get binary info
    binary_info = get_binary_info(binary_bytes)

    # 2. Apply watermark (metadata only for binary files)
    # Merge additional_metadata into watermark metadata
    watermark_metadata = config.get("extra_metadata", {})
    if additional_metadata:
        watermark_metadata.update(additional_metadata)

    watermarked_bytes = apply_binary_metadata_watermark(
        binary_bytes=binary_bytes,
        watermark_id=watermark_id,
        model_id=model_id,
        timestamp=timestamp,
        verification_url=verification_url,
        metadata=watermark_metadata if watermark_metadata else None,
    )

    # 3. Compute hash AFTER watermarking
    hash_after = sha256_bytes(watermarked_bytes)

    # 4. Create hash set
    hashes = ArtifactHashSet(
        content_hash_before_watermark=hash_before,
        content_hash_after_watermark=hash_after,
    )

    # 5. Forensic fragments (generally not recommended for binary files)
    fingerprints: List[ArtifactFingerprint] = []

    if enable_forensic_fragments:
        # For binary files, we could sample random blocks
        # But this is generally not useful for verification
        # Skip for now
        pass

    # 6. Create watermark descriptor
    watermark = WatermarkDescriptor(
        watermark_id=watermark_id,
        watermark_type=WatermarkType.METADATA,
        watermark_location="appended_block",
        verification_url=verification_url,
        applied_at=timestamp,
    )

    # 7. Build evidence
    evidence = ArtifactEvidence(
        artifact_id=artifact_id,
        artifact_type=ArtifactType.BINARY,
        mime_type="application/octet-stream",
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
            "binary_size_bytes": len(binary_bytes),
            "watermarked_size_bytes": len(watermarked_bytes),
            "file_type": binary_info.get("file_type", "unknown"),  # Use 'file_type' to match tests
            "binary_file_type": binary_info.get(
                "file_type", "unknown"
            ),  # Keep both for compatibility
            "watermark_overhead_bytes": len(watermarked_bytes) - len(binary_bytes),
            **(additional_metadata or {}),
        },
    )

    return evidence, watermarked_bytes


__all__ = [
    "build_binary_artifact_evidence",
]
