"""
CIAF Watermarking - Binary Metadata Functions

Binary file watermarking using custom metadata blocks.

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

import json
import struct
from typing import Optional, Dict, Any

# Magic bytes for CIAF watermark blocks
CIAF_MAGIC = b"CIAF\x00\x01"  # CIAF + version
WATERMARK_SECTION = b"WMRK"


def apply_binary_metadata_watermark(
    binary_bytes: bytes,
    watermark_id: str,
    model_id: str,
    timestamp: str,
    verification_url: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> bytes:
    """
    Apply metadata watermark to binary file.

    Appends a custom CIAF watermark section to the end of the binary file.
    This approach works for most binary formats and doesn't corrupt the original file.

    Format:
    [Original Binary Data]
    [CIAF_MAGIC (6 bytes)]
    [WATERMARK_SECTION marker (4 bytes)]
    [Metadata JSON length (4 bytes, little-endian)]
    [Metadata JSON (variable length)]
    [Footer: CIAF_MAGIC (6 bytes)]

    Args:
        binary_bytes: Original binary data
        watermark_id: Unique watermark identifier
        model_id: AI model identifier
        timestamp: ISO 8601 timestamp
        verification_url: Optional verification URL
        metadata: Additional metadata fields

    Returns:
        Watermarked binary bytes

    Example:
        >>> watermarked = apply_binary_metadata_watermark(
        ...     binary_bytes=binary_data,
        ...     watermark_id="wmk-binary-123",
        ...     model_id="code-gen-v1",
        ...     timestamp="2026-04-05T10:30:00Z",
        ...     verification_url="https://vault.example.com/verify/wmk-binary-123"
        ... )
    """
    # Build metadata dictionary
    meta_dict = {
        "watermark_id": watermark_id,
        "model_id": model_id,
        "timestamp": timestamp,
        "ciaf_version": "1.5.0",
    }

    # Add verification URL if provided
    if verification_url:
        meta_dict["verification_url"] = verification_url

    # Add custom metadata
    if metadata:
        meta_dict.update(metadata)

    # Serialize metadata to JSON
    metadata_json = json.dumps(meta_dict, separators=(",", ":")).encode("utf-8")

    # Build watermark block
    watermark_block = bytearray()
    watermark_block.extend(CIAF_MAGIC)  # Magic header
    watermark_block.extend(WATERMARK_SECTION)  # Section marker
    watermark_block.extend(struct.pack("<I", len(metadata_json)))  # Metadata length
    watermark_block.extend(metadata_json)  # Metadata
    watermark_block.extend(CIAF_MAGIC)  # Footer magic

    # Append watermark at END to preserve original file magic bytes
    # This ensures file type detection still works
    watermarked_bytes = binary_bytes + bytes(watermark_block)

    return watermarked_bytes


def extract_binary_metadata_watermark(binary_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Extract CIAF watermark metadata from binary file.

    Args:
        binary_bytes: Binary data to check

    Returns:
        Dictionary with watermark metadata, or None if not found

    Example:
        >>> metadata = extract_binary_metadata_watermark(binary_bytes)
        >>> if metadata:
        ...     print(f"Watermark ID: {metadata['watermark_id']}")
    """
    # Look for CIAF magic footer (last 6 bytes should match)
    if len(binary_bytes) < 20:  # Minimum size for watermark
        return None

    # Check footer magic
    if binary_bytes[-6:] != CIAF_MAGIC:
        return None

    # Search backwards for header magic
    pos = -6  # Start before footer
    while abs(pos) < len(binary_bytes):
        # Look for CIAF_MAGIC followed by WATERMARK_SECTION
        search_pos = len(binary_bytes) + pos - len(CIAF_MAGIC) - len(WATERMARK_SECTION)
        if search_pos < 0:
            break

        if binary_bytes[search_pos : search_pos + len(CIAF_MAGIC)] == CIAF_MAGIC:
            if (
                binary_bytes[
                    search_pos
                    + len(CIAF_MAGIC) : search_pos
                    + len(CIAF_MAGIC)
                    + len(WATERMARK_SECTION)
                ]
                == WATERMARK_SECTION
            ):
                # Found watermark block
                metadata_len_pos = search_pos + len(CIAF_MAGIC) + len(WATERMARK_SECTION)

                if metadata_len_pos + 4 > len(binary_bytes) - 6:
                    break

                # Extract metadata length
                metadata_len = struct.unpack(
                    "<I", binary_bytes[metadata_len_pos : metadata_len_pos + 4]
                )[0]

                # Extract metadata JSON
                json_start = metadata_len_pos + 4
                json_end = json_start + metadata_len

                if json_end > len(binary_bytes) - 6:
                    break

                try:
                    metadata_json = binary_bytes[json_start:json_end].decode("utf-8")
                    metadata = json.loads(metadata_json)
                    return metadata
                except Exception:
                    return None

        pos -= 1

    return None


def has_binary_watermark(binary_bytes: bytes) -> bool:
    """
    Check if binary has CIAF watermark metadata.

    Args:
        binary_bytes: Binary data to check

    Returns:
        True if watermark detected
    """
    metadata = extract_binary_metadata_watermark(binary_bytes)
    return metadata is not None and "watermark_id" in metadata


def get_binary_info(binary_bytes: bytes) -> Dict[str, Any]:
    """
    Get binary file information.

    Args:
        binary_bytes: Binary data

    Returns:
        Dictionary with binary properties
    """
    # Try to detect file type by magic bytes
    file_type = "unknown"

    # More lenient magic byte checks
    if len(binary_bytes) >= 4:
        if binary_bytes[:4] == b"\x7fELF":
            file_type = "ELF"
        elif binary_bytes[:2] == b"MZ":
            file_type = "PE executable"
        elif binary_bytes[:4] == b"\x89PNG":
            file_type = "PNG"
        elif binary_bytes[:3] == b"\xff\xd8\xff":
            file_type = "JPEG image"
        elif binary_bytes[:4] == b"%PDF":
            file_type = "PDF document"
        elif binary_bytes[:4] == b"PK\x03\x04":
            file_type = "ZIP"
        elif binary_bytes[:2] == b"\x1f\x8b":
            file_type = "GZIP compressed"
        elif binary_bytes[:4] == b"Rar!":
            file_type = "RAR archive"

    return {
        "size_bytes": len(binary_bytes),
        "file_type": file_type,
        "has_watermark": has_binary_watermark(binary_bytes),
    }


def remove_binary_watermark(binary_bytes: bytes) -> bytes:
    """
    Remove CIAF watermark from binary file.

    Args:
        binary_bytes: Watermarked binary data

    Returns:
        Original binary without watermark
    """
    metadata = extract_binary_metadata_watermark(binary_bytes)

    if not metadata:
        return binary_bytes

    # Find watermark block start
    pos = len(binary_bytes) - 6  # Start before footer
    while pos > 0:
        search_pos = pos - len(CIAF_MAGIC) - len(WATERMARK_SECTION)
        if search_pos < 0:
            break

        if binary_bytes[search_pos : search_pos + len(CIAF_MAGIC)] == CIAF_MAGIC:
            if (
                binary_bytes[
                    search_pos
                    + len(CIAF_MAGIC) : search_pos
                    + len(CIAF_MAGIC)
                    + len(WATERMARK_SECTION)
                ]
                == WATERMARK_SECTION
            ):
                # Found watermark block - return everything before it
                return binary_bytes[:search_pos]

        pos -= 1

    return binary_bytes


__all__ = [
    "apply_binary_metadata_watermark",
    "extract_binary_metadata_watermark",
    "has_binary_watermark",
    "get_binary_info",
    "remove_binary_watermark",
]
