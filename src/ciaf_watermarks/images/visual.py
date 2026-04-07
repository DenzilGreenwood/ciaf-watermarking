"""
CIAF Watermarking - Image Visual Watermarking

Visual watermarking for images using Pillow.

Watermark types:
- Text overlay (corner or center)
- Logo overlay
- QR code embedding
- Combined (text + QR)

Features:
- Configurable position, opacity, margins
- Multiple font sizes
- Semi-transparent overlays
- QR code integration

Dependencies:
    pip install Pillow

Created: 2026-03-24
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal, Tuple, TYPE_CHECKING
from io import BytesIO
import uuid

if TYPE_CHECKING:
    from ciaf.watermarks.models import ArtifactEvidence

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance  # type: ignore[import-untyped]

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore[assignment, misc]
    ImageDraw = None  # type: ignore[assignment, misc]
    ImageFont = None  # type: ignore[assignment, misc]
    ImageEnhance = None  # type: ignore[assignment, misc]


Position = Literal[
    "top_left",
    "top_right",
    "top_center",
    "bottom_left",
    "bottom_right",
    "bottom_center",
    "center",
    "center_left",
    "center_right",
]


@dataclass
class ImageWatermarkSpec:
    """
    Specification for image watermarking.

    Defines how the watermark should be applied.
    """

    mode: Literal["visual", "steganographic", "hybrid"] = "visual"
    text: Optional[str] = None
    opacity: float = 0.3  # 0.0-1.0 (0 = invisible, 1 = opaque)
    position: Position = "bottom_right"
    font_size: int = 18
    margin: int = 24
    include_qr: bool = False
    qr_payload: Optional[str] = None
    qr_position: Position = "top_right"
    qr_size: int = 100
    text_color: Tuple[int, int, int] = (255, 255, 255)  # RGB white


def apply_visual_watermark(
    image_bytes: bytes,
    text: str,
    opacity: float = 0.3,
    position: Position = "bottom_right",
    margin: int = 24,
    font_size: int = 18,
    text_color: Tuple[int, int, int] = (255, 255, 255),
) -> bytes:
    """
    Apply visual text watermark to image.

    Args:
        image_bytes: Original image bytes
        text: Watermark text
        opacity: Transparency (0.0-1.0)
        position: Where to place watermark
        margin: Margin from edge in pixels
        font_size: Font size
        text_color: RGB color tuple

    Returns:
        Watermarked image bytes (PNG format)

    Raises:
        ImportError: If PIL not available
    """
    if not PIL_AVAILABLE:
        raise ImportError(
            "Pillow required for image watermarking. " "Install with: pip install Pillow"
        )

    # Open image
    img = Image.open(BytesIO(image_bytes))
    base = img.convert("RGBA")

    # Create transparent overlay
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Load font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()  # type: ignore[assignment]

    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Calculate position
    x, y = _calculate_position(position, base.width, base.height, int(text_w), int(text_h), margin)

    # Draw text with opacity
    alpha = max(0, min(255, int(255 * opacity)))
    color_with_alpha = (*text_color, alpha)
    draw.text((x, y), text, fill=color_with_alpha, font=font)

    # Composite
    combined = Image.alpha_composite(base, overlay)
    result = combined.convert("RGB")

    # Convert to bytes
    out = BytesIO()
    result.save(out, format="PNG")
    return out.getvalue()


def apply_qr_watermark(
    image_bytes: bytes,
    qr_bytes: bytes,
    position: Position = "top_right",
    margin: int = 24,
    qr_size: int = 100,
) -> bytes:
    """
    Apply QR code watermark to image.

    Args:
        image_bytes: Original image bytes
        qr_bytes: QR code PNG bytes
        position: Where to place QR code
        margin: Margin from edge
        qr_size: QR code size in pixels

    Returns:
        Image with QR code overlay (PNG)
    """
    if not PIL_AVAILABLE:
        raise ImportError("Pillow required.")

    # Open images
    img: Image.Image = Image.open(BytesIO(image_bytes))  # type: ignore[assignment]
    qr_img = Image.open(BytesIO(qr_bytes))

    # Resize QR code (use LANCZOS if available, otherwise BICUBIC)
    try:
        qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)  # type: ignore[attr-defined, assignment]
    except AttributeError:
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)  # type: ignore[attr-defined, assignment]

    # Convert to RGBA
    base = img.convert("RGBA")
    qr_rgba = qr_img.convert("RGBA")

    # Calculate position
    x, y = _calculate_position(position, base.width, base.height, qr_size, qr_size, margin)

    # Paste QR code
    base.paste(qr_rgba, (x, y), qr_rgba)

    # Convert back to RGB
    result = base.convert("RGB")

    # Convert to bytes
    out = BytesIO()
    result.save(out, format="PNG")
    return out.getvalue()


def apply_combined_watermark(
    image_bytes: bytes,
    text: str,
    qr_bytes: Optional[bytes] = None,
    spec: Optional[ImageWatermarkSpec] = None,
) -> bytes:
    """
    Apply combined text + QR watermark.

    Args:
        image_bytes: Original image bytes
        text: Watermark text
        qr_bytes: QR code bytes (optional)
        spec: Watermark specification

    Returns:
        Watermarked image bytes
    """
    if spec is None:
        spec = ImageWatermarkSpec()

    # Apply text watermark
    result = apply_visual_watermark(
        image_bytes=image_bytes,
        text=text,
        opacity=spec.opacity,
        position=spec.position,
        margin=spec.margin,
        font_size=spec.font_size,
        text_color=spec.text_color,
    )

    # Apply QR if provided
    if qr_bytes:
        result = apply_qr_watermark(
            image_bytes=result,
            qr_bytes=qr_bytes,
            position=spec.qr_position,
            margin=spec.margin,
            qr_size=spec.qr_size,
        )

    return result


def _calculate_position(
    position: Position,
    img_width: int,
    img_height: int,
    element_width: int,
    element_height: int,
    margin: int,
) -> Tuple[int, int]:
    """Calculate x, y coordinates for watermark placement."""
    positions = {
        "top_left": (margin, margin),
        "top_center": ((img_width - element_width) // 2, margin),
        "top_right": (img_width - element_width - margin, margin),
        "center_left": (margin, (img_height - element_height) // 2),
        "center": (
            (img_width - element_width) // 2,
            (img_height - element_height) // 2,
        ),
        "center_right": (
            img_width - element_width - margin,
            (img_height - element_height) // 2,
        ),
        "bottom_left": (margin, img_height - element_height - margin),
        "bottom_center": (
            (img_width - element_width) // 2,
            img_height - element_height - margin,
        ),
        "bottom_right": (
            img_width - element_width - margin,
            img_height - element_height - margin,
        ),
    }
    return positions.get(position, positions["bottom_right"])


def build_image_artifact_evidence(
    image_bytes: bytes,
    model_id: str,
    model_version: str,
    actor_id: str,
    prompt: str,
    verification_base_url: str,
    watermark_spec: Optional[ImageWatermarkSpec] = None,
    include_perceptual_hashes: bool = True,
) -> Tuple["ArtifactEvidence", bytes]:
    """
    Build complete artifact evidence for watermarked image.

    This is the main function for creating watermarked image artifacts.

    Args:
        image_bytes: Original image bytes
        model_id: Model identifier
        model_version: Model version
        actor_id: User/system identifier
        prompt: Input prompt
        verification_base_url: Base URL for verification
        watermark_spec: Watermark specification
        include_perceptual_hashes: Whether to compute perceptual hashes

    Returns:
        Tuple of (ArtifactEvidence, watermarked_image_bytes)
    """
    from ..models import (
        ArtifactEvidence,
        ArtifactType,
        ArtifactHashSet,
        WatermarkDescriptor,
        WatermarkType,
        ArtifactFingerprint,
        utc_now_iso,
        sha256_bytes,
        sha256_text,
    )
    from .qr import make_verification_url_qr, QRCODE_AVAILABLE

    if watermark_spec is None:
        watermark_spec = ImageWatermarkSpec()

    # Generate IDs
    artifact_id = str(uuid.uuid4())
    watermark_id = f"wmk-{uuid.uuid4()}"
    verification_url = f"{verification_base_url.rstrip('/')}/verify/{artifact_id}"

    # Create watermark text
    watermark_text = f"AI Generated | ID: {artifact_id[:8]}"
    if watermark_spec.text:
        watermark_text = watermark_spec.text

    # Generate QR code if requested
    qr_bytes = None
    if watermark_spec.include_qr and QRCODE_AVAILABLE:
        try:
            qr_bytes = make_verification_url_qr(artifact_id, verification_base_url)
        except Exception:
            pass  # QR generation failed, continue without it

    # Apply watermark based on mode
    if watermark_spec.mode == "steganographic":
        # LSB steganography only (invisible)
        from .steganography import embed_watermark_lsb

        watermarked_bytes = embed_watermark_lsb(
            image_bytes=image_bytes,
            watermark_id=watermark_id,
            verification_url=verification_url,
            created_at=utc_now_iso(),
            artifact_id=artifact_id,
        )
    elif watermark_spec.mode == "hybrid":
        # Apply visual watermark first
        visual_watermarked = apply_combined_watermark(
            image_bytes=image_bytes,
            text=watermark_text,
            qr_bytes=qr_bytes,
            spec=watermark_spec,
        )
        # Then embed LSB watermark
        from .steganography import embed_watermark_lsb

        watermarked_bytes = embed_watermark_lsb(
            image_bytes=visual_watermarked,
            watermark_id=watermark_id,
            verification_url=verification_url,
            created_at=utc_now_iso(),
            artifact_id=artifact_id,
        )
    else:
        # Visual only (default)
        watermarked_bytes = apply_combined_watermark(
            image_bytes=image_bytes,
            text=watermark_text,
            qr_bytes=qr_bytes,
            spec=watermark_spec,
        )

    # Compute hashes
    prompt_hash = sha256_text(prompt)
    hash_before = sha256_bytes(image_bytes)
    hash_after = sha256_bytes(watermarked_bytes)

    # Build hash set
    hash_set = ArtifactHashSet(
        content_hash_before_watermark=hash_before,
        content_hash_after_watermark=hash_after,
    )

    # Compute perceptual hashes if requested
    fingerprints = []
    if include_perceptual_hashes:
        try:
            from .fingerprints import compute_all_hashes, IMAGEHASH_AVAILABLE

            if IMAGEHASH_AVAILABLE:
                phash_b, ahash_b, dhash_b, whash_b = compute_all_hashes(image_bytes)
                phash_a, ahash_a, dhash_a, whash_a = compute_all_hashes(watermarked_bytes)

                # Store in hash set
                hash_set.perceptual_hash_before = phash_b
                hash_set.perceptual_hash_after = phash_a

                # Add fingerprints
                fingerprints.extend(
                    [
                        ArtifactFingerprint(
                            algorithm="phash",
                            value=phash_b,
                            role="perceptual_before_watermark",
                        ),
                        ArtifactFingerprint(
                            algorithm="phash",
                            value=phash_a,
                            role="perceptual_after_watermark",
                        ),
                        ArtifactFingerprint(
                            algorithm="ahash",
                            value=ahash_b,
                            role="average_before_watermark",
                        ),
                        ArtifactFingerprint(
                            algorithm="dhash",
                            value=dhash_b,
                            role="difference_before_watermark",
                        ),
                    ]
                )
        except Exception:
            pass  # Perceptual hashing failed, continue without it

    # Build watermark descriptor
    if watermark_spec.mode == "steganographic":
        watermark_type = WatermarkType.EMBEDDED
        embed_method = "lsb_steganography"
        removal_resistance = "medium"  # Survives viewing, not compression
    elif watermark_spec.mode == "hybrid":
        watermark_type = WatermarkType.HYBRID
        embed_method = f"pillow_visual_{watermark_spec.position}+lsb"
        removal_resistance = "medium"
    else:
        watermark_type = WatermarkType.VISIBLE
        embed_method = f"pillow_visual_{watermark_spec.position}"
        removal_resistance = "low"

    watermark = WatermarkDescriptor(
        watermark_id=watermark_id,
        watermark_type=watermark_type,
        tag_text=watermark_text if watermark_spec.mode != "steganographic" else None,
        verification_url=verification_url,
        qr_payload=verification_url if qr_bytes else None,
        embed_method=embed_method,
        removal_resistance=removal_resistance,
        location=(watermark_spec.position if watermark_spec.mode != "steganographic" else None),
    )

    # Build metadata
    metadata = {
        "distribution_state": "watermarked",
        "artifact_format_version": "1.0",
        "watermark_mode": watermark_spec.mode,
        "watermark_position": watermark_spec.position,
        "watermark_opacity": watermark_spec.opacity,
        "has_qr_code": qr_bytes is not None,
    }

    # Create evidence
    evidence = ArtifactEvidence(
        artifact_id=artifact_id,
        artifact_type=ArtifactType.IMAGE,
        mime_type="image/png",
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

    return evidence, watermarked_bytes


__all__ = [
    # Data models
    "ImageWatermarkSpec",
    "Position",
    # Watermarking functions
    "apply_visual_watermark",
    "apply_qr_watermark",
    "apply_combined_watermark",
    "build_image_artifact_evidence",
    # Constants
    "PIL_AVAILABLE",
]
