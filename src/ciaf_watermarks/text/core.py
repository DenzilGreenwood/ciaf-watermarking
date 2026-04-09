"""
CIAF Watermarking - Text Core Functions

Main text artifact evidence building.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.5.0
"""

import uuid
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

from ..models import (
    ArtifactEvidence,
    ArtifactType,
    ArtifactHashSet,
    WatermarkDescriptor,
    WatermarkType,
    ArtifactFingerprint,
    utc_now_iso,
)
from ..hashing import (
    sha256_text,
    normalized_text_hash,
    simhash_text,
    sha256_bytes,
)
from ..context import get_context_or_params

from .watermark import apply_text_watermark


def build_text_artifact_evidence(
    raw_text: str,
    prompt: str,
    verification_base_url: str,
    model_id: Optional[str] = None,
    model_version: Optional[str] = None,
    actor_id: Optional[str] = None,
    watermark_style: str = "footer",
    include_simhash: bool = True,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[ArtifactEvidence, str]:
    """
    Build complete artifact evidence for text with watermarking.

    This is the main function for creating watermarked text artifacts.

    Args:
        raw_text: Original AI-generated text (before watermark)
        prompt: Input prompt
        verification_base_url: Base URL for verification
        model_id: Model identifier (optional if context is set)
        model_version: Model version (optional if context is set)
        actor_id: User/system identifier (optional if context is set)
        watermark_style: Watermark style ("footer", "header", "inline")
        include_simhash: Whether to compute SimHash fingerprints
        additional_metadata: Extra metadata to store

    Returns:
        Tuple of (ArtifactEvidence, watermarked_text)

    Note:
        If model_id, model_version, or actor_id are not provided, they will
        be resolved from the active watermark context. Use watermark_context()
        context manager or set_global_context() to set the context.

    Example:
        >>> from ciaf.watermarks.context import watermark_context
        >>> with watermark_context(
        ...     model_id="gpt-4",
        ...     model_version="2024-03",
        ...     actor_id="user:alice"
        ... ):
        ...     evidence, watermarked = build_text_artifact_evidence(
        ...         raw_text="AI generated content",
        ...         prompt="Generate a summary",
        ...         verification_base_url="https://vault.example.com"
        ...     )
    """
    # Resolve context parameters
    context_params = get_context_or_params(model_id, model_version, actor_id)
    model_id = context_params["model_id"]
    model_version = context_params["model_version"]
    actor_id = context_params["actor_id"]
    # Generate unique IDs
    artifact_id = str(uuid.uuid4())
    watermark_id = f"wmk-{uuid.uuid4()}"
    verification_url = f"{verification_base_url.rstrip('/')}/verify/{artifact_id}"

    # Apply watermark
    watermarked_text = apply_text_watermark(
        raw_text=raw_text,
        watermark_id=watermark_id,
        verification_url=verification_url,
        style=watermark_style,
    )

    # Compute hashes
    prompt_hash = sha256_text(prompt)
    hash_before = sha256_text(raw_text)
    hash_after = sha256_text(watermarked_text)

    # Compute normalized hashes
    norm_before = normalized_text_hash(raw_text)
    norm_after = normalized_text_hash(watermarked_text)

    # Build hash set
    hash_set = ArtifactHashSet(
        content_hash_before_watermark=hash_before,
        content_hash_after_watermark=hash_after,
        normalized_hash_before=norm_before,
        normalized_hash_after=norm_after,
    )

    # Optional: SimHash fingerprints
    fingerprints = []
    if include_simhash:
        simhash_before = simhash_text(raw_text)
        simhash_after = simhash_text(watermarked_text)

        hash_set.simhash_before = simhash_before
        hash_set.simhash_after = simhash_after

        fingerprints.append(
            ArtifactFingerprint(
                algorithm="simhash",
                value=simhash_before,
                role="exact_content_before_watermark",
            )
        )
        fingerprints.append(
            ArtifactFingerprint(
                algorithm="simhash",
                value=simhash_after,
                role="exact_content_after_watermark",
            )
        )

    # Distinctive Anchor Fingerprints (Forensic Layer)
    # Validated at 1.19 × 10⁻⁸ collision rate on 104k document corpus
    # Import and execution are optional - graceful degradation if unavailable
    try:
        from ..forensics.text import compute_distinctive_anchor_fingerprint, VALIDATION_METADATA

        anchor_fingerprint = compute_distinctive_anchor_fingerprint(raw_text)

        # Add anchor fingerprint to evidence
        # Note: 0.95 is a heuristic policy weight, not a calibrated probability
        fingerprints.append(
            ArtifactFingerprint(
                algorithm="distinctive_anchor_v1",
                value=anchor_fingerprint.fingerprint_hash,
                role="forensic_anchor_before_watermark",
                confidence=0.95,  # Heuristic weight (collision rate is 1.19e-8, not a confidence)
            )
        )
    except Exception as e:
        # Forensic analysis is optional; don't fail if it doesn't work
        logger.warning(
            f"Forensic anchor fingerprinting failed (module or computation): {e}", exc_info=True
        )

    # Build watermark descriptor
    watermark = WatermarkDescriptor(
        watermark_id=watermark_id,
        watermark_type=WatermarkType.VISIBLE,
        tag_text=f"AI Provenance Tag: {watermark_id}",
        verification_url=verification_url,
        embed_method=f"{watermark_style}_append_v1",
        removal_resistance="low",  # Text watermarks are easy to remove
        location=watermark_style,
    )

    # Build metadata
    metadata = {
        "distribution_state": "watermarked",
        "artifact_format_version": "1.0",
        "watermark_style": watermark_style,
        "text_length_before": len(raw_text),
        "text_length_after": len(watermarked_text),
    }

    # Add forensic anchor metadata if available
    try:
        if "anchor_fingerprint" in locals():
            metadata["forensic_anchor"] = {
                "version": "distinctive_anchor_v1",
                "zone_words": anchor_fingerprint.config.zone_word_size,
                "top_k": anchor_fingerprint.config.top_k,
                "strong_threshold": anchor_fingerprint.config.strong_threshold,
                "zone_match_requirement": anchor_fingerprint.config.zone_match_requirement,
                "validation": VALIDATION_METADATA,
                "zone_anchors": anchor_fingerprint.to_dict()["zone_anchors"],
                "fingerprint_hash": anchor_fingerprint.fingerprint_hash,  # Preserve hash for verification
                "fingerprint_metadata": anchor_fingerprint.metadata,  # Include short_document flags etc
            }
    except Exception as e:
        # Forensic metadata is optional
        logger.warning(f"Failed to serialize forensic anchor metadata: {e}", exc_info=True)

    if additional_metadata:
        metadata.update(additional_metadata)

    # Create evidence record
    evidence = ArtifactEvidence(
        artifact_id=artifact_id,
        artifact_type=ArtifactType.TEXT,
        mime_type="text/plain",
        created_at=utc_now_iso(),
        model_id=model_id,
        model_version=model_version,
        actor_id=actor_id,
        prompt_hash=prompt_hash,
        output_hash_raw=hash_before,
        output_hash_distributed=hash_after,
        watermark=watermark,
        hashes=hash_set,
        fingerprints=fingerprints,
        metadata=metadata,
    )

    # Compute receipt hash
    receipt_hash = sha256_bytes(evidence.to_canonical_bytes())
    evidence.hashes.canonical_receipt_hash = receipt_hash

    return evidence, watermarked_text


def quick_watermark_text(
    text: str,
    model_id: str,
    verification_url: str = "https://vault.cognitiveinsight.ai",
) -> Tuple[str, str]:
    """
    Quick watermarking for simple use cases.

    Args:
        text: Text to watermark
        model_id: Model identifier
        verification_url: Base verification URL

    Returns:
        Tuple of (watermarked_text, artifact_id)
    """
    artifact_id = str(uuid.uuid4())
    watermark_id = f"wmk-{uuid.uuid4()}"
    verify_url = f"{verification_url.rstrip('/')}/verify/{artifact_id}"

    watermarked = apply_text_watermark(
        raw_text=text,
        watermark_id=watermark_id,
        verification_url=verify_url,
    )

    return watermarked, artifact_id


__all__ = [
    "build_text_artifact_evidence",
    "quick_watermark_text",
]
