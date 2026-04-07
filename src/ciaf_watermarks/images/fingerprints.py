"""
CIAF Watermarking - Image Perceptual Hashing

Perceptual image fingerprinting for similarity detection even when:
- Image is resized
- Image is compressed
- Watermark is removed
- Colors are slightly adjusted
- Image is cropped (partially)

Uses multiple hashing algorithms:
- pHash (perceptual hash) - Robust to minor modifications
- aHash (average hash) - Fast, good for exact duplicates
- dHash (difference hash) - Good for detecting edits
- wHash (wavelet hash) - Very robust to modifications

Dependencies:
    pip install imagehash Pillow

Created: 2026-03-24
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

from typing import Optional, Tuple
from io import BytesIO
from dataclasses import dataclass

try:
    from PIL import Image
    import imagehash

    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    Image = None  # type: ignore
    imagehash = None  # type: ignore


@dataclass
class ImageFingerprintSet:
    """
    Complete set of image fingerprints for forensic matching.

    Includes multiple hashing algorithms for different use cases.
    """

    # Exact hashes
    exact_hash_before: str  # SHA-256 of original image bytes
    exact_hash_after: str  # SHA-256 of watermarked image bytes

    # Perceptual hashes (resilient to modifications)
    phash_before: Optional[str] = None  # Perceptual hash (most robust)
    phash_after: Optional[str] = None

    # Average hashes (fast similarity)
    ahash_before: Optional[str] = None  # Average hash
    ahash_after: Optional[str] = None

    # Difference hashes (edge detection)
    dhash_before: Optional[str] = None  # Difference hash
    dhash_after: Optional[str] = None

    # Wavelet hashes (very robust)
    whash_before: Optional[str] = None  # Wavelet hash
    whash_after: Optional[str] = None


def compute_perceptual_hash(image_bytes: bytes, hash_size: int = 8) -> str:
    """
    Compute perceptual hash (pHash) of image.

    pHash is robust to:
    - Resizing
    - Compression
    - Minor modifications
    - Color adjustments

    Args:
        image_bytes: Image data as bytes
        hash_size: Hash size (default 8, produces 64-bit hash)

    Returns:
        Hex string of perceptual hash

    Raises:
        ImportError: If imagehash not available
    """
    if not IMAGEHASH_AVAILABLE:
        raise ImportError("imagehash library required. Install with: pip install imagehash Pillow")

    img = Image.open(BytesIO(image_bytes))
    return str(imagehash.phash(img, hash_size=hash_size))


def compute_average_hash(image_bytes: bytes, hash_size: int = 8) -> str:
    """
    Compute average hash (aHash) of image.

    aHash is fast and good for exact duplicates and near-duplicates.

    Args:
        image_bytes: Image data as bytes
        hash_size: Hash size (default 8)

    Returns:
        Hex string of average hash
    """
    if not IMAGEHASH_AVAILABLE:
        raise ImportError("imagehash library required.")

    img = Image.open(BytesIO(image_bytes))
    return str(imagehash.average_hash(img, hash_size=hash_size))


def compute_difference_hash(image_bytes: bytes, hash_size: int = 8) -> str:
    """
    Compute difference hash (dHash) of image.

    dHash tracks gradients and is good for detecting edits.

    Args:
        image_bytes: Image data as bytes
        hash_size: Hash size (default 8)

    Returns:
        Hex string of difference hash
    """
    if not IMAGEHASH_AVAILABLE:
        raise ImportError("imagehash library required.")

    img = Image.open(BytesIO(image_bytes))
    return str(imagehash.dhash(img, hash_size=hash_size))


def compute_wavelet_hash(image_bytes: bytes, hash_size: int = 8) -> str:
    """
    Compute wavelet hash (wHash) of image.

    wHash is very robust to modifications and compression.

    Args:
        image_bytes: Image data as bytes
        hash_size: Hash size (default 8)

    Returns:
        Hex string of wavelet hash
    """
    if not IMAGEHASH_AVAILABLE:
        raise ImportError("imagehash library required.")

    img = Image.open(BytesIO(image_bytes))
    return str(imagehash.whash(img, hash_size=hash_size))


def compute_all_hashes(image_bytes: bytes, hash_size: int = 8) -> Tuple[str, str, str, str]:
    """
    Compute all perceptual hashes for image.

    Args:
        image_bytes: Image data as bytes
        hash_size: Hash size for all hashes

    Returns:
        Tuple of (phash, ahash, dhash, whash)
    """
    if not IMAGEHASH_AVAILABLE:
        raise ImportError("imagehash library required.")

    img = Image.open(BytesIO(image_bytes))

    phash = str(imagehash.phash(img, hash_size=hash_size))
    ahash = str(imagehash.average_hash(img, hash_size=hash_size))
    dhash = str(imagehash.dhash(img, hash_size=hash_size))
    whash = str(imagehash.whash(img, hash_size=hash_size))

    return phash, ahash, dhash, whash


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Compute Hamming distance between two perceptual hashes.

    Lower distance = more similar images.

    Typical thresholds:
    - 0-5: Near identical
    - 6-10: Very similar
    - 11-15: Similar
    - 16-20: Somewhat similar
    - >20: Different

    Args:
        hash1: First hash (hex string)
        hash2: Second hash (hex string)

    Returns:
        Hamming distance (number of differing bits)
    """
    if len(hash1) != len(hash2):
        raise ValueError("Hashes must be same length")

    # Convert hex to binary and count differences
    int1 = int(hash1, 16)
    int2 = int(hash2, 16)
    xor = int1 ^ int2
    return bin(xor).count("1")


def similarity_score(hash1: str, hash2: str, max_distance: int = 64) -> float:
    """
    Compute similarity score (0.0-1.0) from hash distance.

    Args:
        hash1: First hash
        hash2: Second hash
        max_distance: Maximum possible distance (default 64 for 8x8 hash)

    Returns:
        Similarity score (1.0 = identical, 0.0 = completely different)
    """
    distance = hamming_distance(hash1, hash2)
    return 1.0 - (distance / max_distance)


def is_similar_image(hash1: str, hash2: str, threshold: int = 10) -> bool:
    """
    Check if two images are similar based on hash distance.

    Args:
        hash1: First perceptual hash
        hash2: Second perceptual hash
        threshold: Maximum distance to consider similar (default 10)

    Returns:
        True if images are similar
    """
    return hamming_distance(hash1, hash2) <= threshold


__all__ = [
    # Data models
    "ImageFingerprintSet",
    # Hash computation
    "compute_perceptual_hash",
    "compute_average_hash",
    "compute_difference_hash",
    "compute_wavelet_hash",
    "compute_all_hashes",
    # Similarity matching
    "hamming_distance",
    "similarity_score",
    "is_similar_image",
    # Constants
    "IMAGEHASH_AVAILABLE",
]
