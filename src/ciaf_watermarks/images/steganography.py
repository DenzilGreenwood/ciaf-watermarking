"""
CIAF Watermarking - Image Steganography (LSB Embedding)

Implements Least Significant Bit (LSB) steganography for invisible watermarking.

LSB steganography hides data by replacing the least significant bits of pixel
values with message bits. This creates imperceptible changes to the image while
embedding verifiable provenance data.

Key Features:
- Invisible watermarking (no visible artifacts)
- Lossless embedding (use PNG format)
- Supports RGB and RGBA images
- Embeds: watermark ID, verification URL, timestamp
- Error detection via checksum

Security Note:
- LSB watermarks are NOT robust to lossy compression (JPEG)
- NOT robust to image manipulation (cropping, resizing, filters)
- Best for: Legal evidence, forensic trails, pristine archival
- Use visual watermarks for public distribution

Created: 2026-04-04
Author: Denzil James Greenwood
Version: 1.0.0 (MVP)
"""

from __future__ import annotations

from typing import Optional, Tuple
from io import BytesIO
import hashlib
import json

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore


class SteganographyError(Exception):
    """Raised when steganography operations fail."""

    pass


def _text_to_bits(text: str) -> str:
    """Convert text to binary string."""
    bits = "".join(format(byte, "08b") for byte in text.encode("utf-8"))
    return bits


def _bits_to_text(bits: str) -> str:
    """Convert binary string back to text."""
    chars = []
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits):
            byte = bits[i : i + 8]
            char_code = int(byte, 2)
            if char_code > 0:  # Skip null bytes
                chars.append(chr(char_code))

    return "".join(chars)


def _compute_checksum(data: str) -> str:
    """Compute SHA-256 checksum (first 8 chars)."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:8]


def embed_watermark_lsb(
    image_bytes: bytes,
    watermark_id: str,
    verification_url: str,
    created_at: str,
    artifact_id: Optional[str] = None,
) -> bytes:
    """
    Embed invisible watermark using LSB steganography.

    Embeds a JSON payload containing:
    - watermark_id: Unique watermark identifier
    - verification_url: URL for online verification
    - created_at: ISO 8601 timestamp
    - artifact_id: Optional artifact identifier
    - checksum: Data integrity verification

    The payload is prefixed with a length marker and suffixed with a delimiter
    to enable reliable extraction.

    Args:
        image_bytes: Original image (PNG recommended for lossless)
        watermark_id: Watermark identifier
        verification_url: Verification URL
        created_at: ISO timestamp
        artifact_id: Optional artifact ID

    Returns:
        Watermarked image bytes (PNG format)

    Raises:
        SteganographyError: If embedding fails or image too small
    """
    if not PIL_AVAILABLE:
        raise SteganographyError("Pillow not installed. Install with: pip install Pillow")

    # Create payload
    payload = {
        "watermark_id": watermark_id,
        "verification_url": verification_url,
        "created_at": created_at,
    }
    if artifact_id:
        payload["artifact_id"] = artifact_id

    payload_json = json.dumps(payload, separators=(",", ":"))
    payload["checksum"] = _compute_checksum(payload_json)

    # Final payload with checksum
    final_payload = json.dumps(payload, separators=(",", ":"))

    # Add length prefix and delimiter
    length = len(final_payload)
    message = f"{length:08d}:{final_payload}:END"

    # Convert to bits
    message_bits = _text_to_bits(message)

    # Load image
    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception as e:
        raise SteganographyError(f"Failed to load image: {e}")

    # Convert to RGB if needed (steganography works best with RGB)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")  # type: ignore[assignment]

    # Get pixel data
    pixels = list(img.getdata())
    width, height = img.size
    max_bits = width * height * 3  # 3 channels (RGB)

    if len(message_bits) > max_bits:
        raise SteganographyError(
            f"Image too small to embed watermark. "
            f"Need {len(message_bits)} bits, have {max_bits} bits available. "
            f"Try a larger image or shorter message."
        )

    # Embed bits in LSB of RGB channels
    new_pixels = []
    bit_index = 0

    for pixel in pixels:
        if img.mode == "RGBA":
            r, g, b, a = pixel
            new_pixel = list([r, g, b, a])
        else:
            r, g, b = pixel
            new_pixel = list([r, g, b])

        # Embed in R, G, B channels
        for channel_idx in range(3):
            if bit_index < len(message_bits):
                # Clear LSB and set to message bit
                new_pixel[channel_idx] = (new_pixel[channel_idx] & 0xFE) | int(
                    message_bits[bit_index]
                )
                bit_index += 1

        new_pixels.append(tuple(new_pixel))

    # Create new image
    new_img = Image.new(img.mode, (width, height))
    new_img.putdata(new_pixels)

    # Save as PNG (lossless)
    output = BytesIO()
    new_img.save(output, format="PNG")
    return output.getvalue()


def extract_watermark_lsb(image_bytes: bytes) -> Optional[dict]:
    """
    Extract invisible watermark from LSB-embedded image.

    Args:
        image_bytes: Watermarked image bytes

    Returns:
        Dictionary containing watermark data, or None if no watermark found

    Raises:
        SteganographyError: If extraction fails
    """
    if not PIL_AVAILABLE:
        raise SteganographyError("Pillow not installed. Install with: pip install Pillow")

    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception as e:
        raise SteganographyError(f"Failed to load image: {e}")

    # Convert to RGB if needed
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")  # type: ignore[assignment]

    pixels = list(img.getdata())

    # Extract bits from LSB
    bits = []
    for pixel in pixels:
        if img.mode == "RGBA":
            r, g, b, a = pixel
        else:
            r, g, b = pixel

        # Extract LSB from R, G, B
        bits.append(str(r & 1))
        bits.append(str(g & 1))
        bits.append(str(b & 1))

    bit_string = "".join(bits)

    # Try to extract length prefix (8 digits + colon)
    try:
        # Convert first 72 bits to text (9 chars: "00000123:")
        length_bits = bit_string[:72]
        length_str = _bits_to_text(length_bits)

        if ":" not in length_str:
            return None  # No valid watermark

        # Parse length
        parts = length_str.split(":", 1)
        if len(parts) < 2:
            return None

        length = int(parts[0].strip())

        # Extract the full message (9 chars for header + length chars + 4 for ":END")
        total_chars_needed = 9 + length + 4
        message_bits = bit_string[: total_chars_needed * 8]
        full_message = _bits_to_text(message_bits)

        # Find the payload between first : and :END
        if ":" not in full_message:
            return None

        # Skip the length prefix
        after_first_colon = full_message.find(":") + 1
        payload_and_end = full_message[after_first_colon:]

        # Find :END marker
        end_marker_pos = payload_and_end.find(":END")
        if end_marker_pos == -1:
            return None

        payload_json = payload_and_end[:end_marker_pos]

        # Parse JSON
        payload = json.loads(payload_json)

        # Verify checksum if present
        if "checksum" in payload:
            stored_checksum = payload.pop("checksum")
            computed_checksum = _compute_checksum(json.dumps(payload, separators=(",", ":")))

            if stored_checksum != computed_checksum:
                raise SteganographyError(
                    f"Checksum mismatch: watermark data may be corrupted. "
                    f"Expected {computed_checksum}, got {stored_checksum}"
                )

        return payload

    except (ValueError, json.JSONDecodeError, IndexError):
        # No valid watermark found
        return None


def verify_lsb_watermark(
    image_bytes: bytes,
    expected_watermark_id: str,
) -> Tuple[bool, Optional[dict]]:
    """
    Verify LSB watermark matches expected watermark ID.

    Args:
        image_bytes: Image to verify
        expected_watermark_id: Expected watermark identifier

    Returns:
        Tuple of (is_valid, watermark_data)
    """
    try:
        watermark_data = extract_watermark_lsb(image_bytes)

        if watermark_data is None:
            return (False, None)

        if watermark_data.get("watermark_id") == expected_watermark_id:
            return (True, watermark_data)
        else:
            return (False, watermark_data)

    except SteganographyError:
        return (False, None)


def has_lsb_watermark(image_bytes: bytes) -> bool:
    """
    Quick check if image contains an LSB watermark.

    Args:
        image_bytes: Image to check

    Returns:
        True if watermark detected, False otherwise
    """
    try:
        watermark_data = extract_watermark_lsb(image_bytes)
        return watermark_data is not None
    except Exception:
        return False


# Export public API
__all__ = [
    "embed_watermark_lsb",
    "extract_watermark_lsb",
    "verify_lsb_watermark",
    "has_lsb_watermark",
    "SteganographyError",
    "PIL_AVAILABLE",
]
