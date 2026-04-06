"""
CIAF Watermarking - QR Code Generation

QR code generation for verification URLs and compact tokens.

Best practices:
- Keep payload small (verification URL preferred)
- Link to vault verification endpoint
- Include artifact ID for lookup
- Support both URL and compact token formats

Dependencies:
    pip install qrcode[pil]

Created: 2026-03-24
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

from io import BytesIO

try:
    import qrcode
    from qrcode.image.pil import PilImage

    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    qrcode = None
    PilImage = None


def make_qr_code_bytes(
    payload: str,
    box_size: int = 6,
    border: int = 2,
    fill_color: str = "black",
    back_color: str = "white",
) -> bytes:
    """
    Generate QR code as PNG bytes.

    Args:
        payload: Data to encode (URL or compact token)
        box_size: Size of each box in pixels (default 6)
        border: Border size in boxes (default 2)
        fill_color: Foreground color (default "black")
        back_color: Background color (default "white")

    Returns:
        PNG image bytes

    Raises:
        ImportError: If qrcode library not installed
    """
    if not QRCODE_AVAILABLE:
        raise ImportError(
            "qrcode library required for QR code generation. "
            "Install with: pip install qrcode[pil]"
        )

    qr = qrcode.QRCode(
        version=None,  # Auto-detect version
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    # Convert to bytes
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def make_verification_url_qr(
    artifact_id: str, base_url: str = "https://vault.cognitiveinsight.ai", **qr_kwargs
) -> bytes:
    """
    Generate QR code for artifact verification URL.

    Args:
        artifact_id: Artifact ID to verify
        base_url: Base verification URL
        **qr_kwargs: Additional arguments for make_qr_code_bytes

    Returns:
        QR code PNG bytes
    """
    url = f"{base_url.rstrip('/')}/verify/{artifact_id}"
    return make_qr_code_bytes(url, **qr_kwargs)


def make_compact_token_qr(
    artifact_id: str, watermark_id: str, receipt_hash_prefix: str, **qr_kwargs
) -> bytes:
    """
    Generate QR code for compact CIAF token.

    Format: ciaf:artifact-id:watermark-id:receipt-hash-prefix

    Args:
        artifact_id: Artifact identifier
        watermark_id: Watermark identifier
        receipt_hash_prefix: First 8 chars of receipt hash
        **qr_kwargs: Additional arguments for make_qr_code_bytes

    Returns:
        QR code PNG bytes
    """
    token = f"ciaf:{artifact_id}:{watermark_id}:{receipt_hash_prefix}"
    return make_qr_code_bytes(token, **qr_kwargs)


def get_qr_image(qr_bytes: bytes):
    """
    Convert QR code bytes to PIL Image (if available).

    Args:
        qr_bytes: QR code PNG bytes

    Returns:
        PIL Image object

    Raises:
        ImportError: If PIL not available
    """
    try:
        from PIL import Image

        return Image.open(BytesIO(qr_bytes))
    except ImportError:
        raise ImportError("PIL required. Install with: pip install Pillow")


__all__ = [
    "make_qr_code_bytes",
    "make_verification_url_qr",
    "make_compact_token_qr",
    "get_qr_image",
    "QRCODE_AVAILABLE",
]
