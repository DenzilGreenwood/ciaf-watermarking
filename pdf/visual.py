"""
CIAF Watermarking - PDF Visual Watermarking

Adds visible watermarks to PDF pages, including QR codes in footers.

Visual watermark options:
- QR code in footer (near page numbers)
- Text stamp overlays
- Header/footer text watermarks
- Custom positioning

Uses pypdf for PDF manipulation and ReportLab for drawing.

Created: 2026-03-30
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

from typing import Tuple, Optional, Dict, Literal, TYPE_CHECKING
from io import BytesIO
import uuid

if TYPE_CHECKING:
    from ciaf.watermarks.models import ArtifactEvidence

try:
    from pypdf import PdfReader, PdfWriter, PageObject, Transformation
    from pypdf.generic import RectangleObject

    PYPDF_AVAILABLE = True
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from PyPDF2.generic import RectangleObject

        PageObject = None
        Transformation = None
        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False
        PdfReader = None
        PdfWriter = None
        PageObject = None
        RectangleObject = None
        Transformation = None

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from PIL import Image as PILImage

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    canvas = None
    letter = None
    inch = None
    PILImage = None


QRPosition = Literal["bottom-left", "bottom-center", "bottom-right"]


def _check_dependencies():
    """Check if required dependencies are available."""
    if not PYPDF_AVAILABLE:
        raise ImportError(
            "pypdf or PyPDF2 required for PDF watermarking. "
            "Install with: pip install pypdf"
        )
    if not REPORTLAB_AVAILABLE:
        raise ImportError(
            "reportlab required for PDF visual watermarking. "
            "Install with: pip install reportlab pillow"
        )


def create_qr_overlay_page(
    qr_image_bytes: bytes,
    page_width: float,
    page_height: float,
    qr_position: QRPosition = "bottom-right",
    qr_size: float = 0.5,  # inches
    margin: float = 0.3,  # inches from edges
    page_number: Optional[int] = None,
    add_text: bool = True,
) -> bytes:
    """
    Create a transparent overlay with QR code for one PDF page.

    Args:
        qr_image_bytes: QR code PNG bytes
        page_width: Page width in points
        page_height: Page height in points
        qr_position: Position of QR code ("bottom-left", "bottom-center", "bottom-right")
        qr_size: QR code size in inches
        margin: Margin from page edges in inches
        page_number: Optional page number to display
        add_text: Whether to add "Verify" text below QR code

    Returns:
        PDF overlay bytes
    """
    _check_dependencies()

    # Create in-memory buffer
    buffer = BytesIO()

    # Create canvas matching page size
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Calculate QR position
    qr_size_pts = qr_size * inch
    margin_pts = margin * inch

    if qr_position == "bottom-left":
        x = margin_pts
    elif qr_position == "bottom-center":
        x = (page_width - qr_size_pts) / 2
    else:  # bottom-right
        x = page_width - qr_size_pts - margin_pts

    y = margin_pts

    # Load QR image
    qr_img = PILImage.open(BytesIO(qr_image_bytes))

    # Draw QR code
    c.drawInlineImage(
        qr_img,
        x,
        y,
        width=qr_size_pts,
        height=qr_size_pts,
        preserveAspectRatio=True,
    )

    # Add text if requested
    if add_text:
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.3, 0.3, 0.3)  # Dark gray
        text_x = x + (qr_size_pts / 2)
        text_y = y - 10  # 10 points below QR code
        c.drawCentredString(text_x, text_y, "Verify")

    # Add page number near QR code if provided
    if page_number is not None:
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.4, 0.4, 0.4)  # Gray

        # Position page number based on QR position
        if qr_position == "bottom-left":
            num_x = x + qr_size_pts + 15  # To the right of QR
            num_y = y + (qr_size_pts / 2) - 5
            c.drawString(num_x, num_y, f"Page {page_number}")
        elif qr_position == "bottom-right":
            num_x = x - 40  # To the left of QR
            num_y = y + (qr_size_pts / 2) - 5
            c.drawRightString(num_x, num_y, f"Page {page_number}")
        else:  # bottom-center
            num_x = page_width - margin_pts
            num_y = y + (qr_size_pts / 2) - 5
            c.drawRightString(num_x, num_y, f"Page {page_number}")

    # Finalize
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def apply_qr_watermark_to_pdf(
    pdf_bytes: bytes,
    qr_image_bytes: bytes,
    qr_position: QRPosition = "bottom-right",
    qr_size: float = 0.5,
    margin: float = 0.3,
    add_page_numbers: bool = True,
    add_verify_text: bool = True,
) -> bytes:
    """
    Apply QR code watermark to all pages of a PDF.

    Args:
        pdf_bytes: Original PDF bytes
        qr_image_bytes: QR code PNG bytes
        qr_position: Position of QR code on each page
        qr_size: QR code size in inches
        margin: Margin from page edges in inches
        add_page_numbers: Whether to add page numbers near QR codes
        add_verify_text: Whether to add "Verify" text

    Returns:
        Watermarked PDF bytes

    Raises:
        ImportError: If required libraries not available
    """
    _check_dependencies()

    # Read original PDF
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    # Process each page
    for page_num, page in enumerate(reader.pages, start=1):
        # Get page dimensions
        page_box = page.mediabox
        page_width = float(page_box.width)
        page_height = float(page_box.height)

        # Create QR overlay for this page
        overlay_bytes = create_qr_overlay_page(
            qr_image_bytes=qr_image_bytes,
            page_width=page_width,
            page_height=page_height,
            qr_position=qr_position,
            qr_size=qr_size,
            margin=margin,
            page_number=page_num if add_page_numbers else None,
            add_text=add_verify_text,
        )

        # Load overlay as PDF
        overlay_pdf = PdfReader(BytesIO(overlay_bytes))
        overlay_page = overlay_pdf.pages[0]

        # Merge overlay onto original page
        page.merge_page(overlay_page)

        # Add to writer
        writer.add_page(page)

    # Preserve metadata if exists
    if reader.metadata:
        writer.add_metadata(reader.metadata)

    # Write to bytes
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def apply_text_stamp_to_pdf(
    pdf_bytes: bytes,
    stamp_text: str,
    position: Literal["header", "footer"] = "footer",
    font_size: int = 8,
    color: Tuple[float, float, float] = (0.7, 0.7, 0.7),
    margin: float = 0.5,
) -> bytes:
    """
    Apply text stamp to all pages of a PDF.

    Args:
        pdf_bytes: Original PDF bytes
        stamp_text: Text to stamp on each page
        position: "header" or "footer"
        font_size: Font size in points
        color: RGB color tuple (0-1 range)
        margin: Margin from page edge in inches

    Returns:
        Stamped PDF bytes
    """
    _check_dependencies()

    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        # Get page dimensions
        page_box = page.mediabox
        page_width = float(page_box.width)
        page_height = float(page_box.height)

        # Create stamp overlay
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Set font and color
        c.setFont("Helvetica", font_size)
        c.setFillColorRGB(*color)

        # Calculate position
        margin_pts = margin * inch
        x = page_width / 2  # Center horizontally

        if position == "header":
            y = page_height - margin_pts
        else:  # footer
            y = margin_pts

        # Draw centered text
        c.drawCentredString(x, y, stamp_text)
        c.save()

        # Merge overlay
        buffer.seek(0)
        overlay_pdf = PdfReader(buffer)
        overlay_page = overlay_pdf.pages[0]
        page.merge_page(overlay_page)

        writer.add_page(page)

    # Preserve metadata
    if reader.metadata:
        writer.add_metadata(reader.metadata)

    # Write output
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_pdf_artifact_with_visual_watermark(
    pdf_bytes: bytes,
    model_id: str,
    model_version: str,
    actor_id: str,
    prompt: str,
    verification_base_url: str,
    qr_position: QRPosition = "bottom-right",
    qr_size: float = 0.5,
    add_page_numbers: bool = True,
    add_text_stamp: bool = False,
    stamp_text: Optional[str] = None,
    additional_metadata: Optional[Dict[str, str]] = None,
) -> Tuple["ArtifactEvidence", bytes]:
    """
    Build complete artifact evidence for PDF with visual QR watermark.

    This combines:
    1. Metadata watermarking (invisible)
    2. QR code in footer (visible, scannable)
    3. Optional text stamp

    Args:
        pdf_bytes: Original PDF bytes
        model_id: Model identifier
        model_version: Model version
        actor_id: User/system identifier
        prompt: Input prompt
        verification_base_url: Base URL for verification
        qr_position: Position of QR code ("bottom-left", "bottom-center", "bottom-right")
        qr_size: QR code size in inches (default 0.5)
        add_page_numbers: Whether to add page numbers near QR codes
        add_text_stamp: Whether to add text stamp to all pages
        stamp_text: Custom stamp text (default: "AI Generated Content | Verify at {url}")
        additional_metadata: Optional additional PDF metadata

    Returns:
        Tuple of (ArtifactEvidence, watermarked_pdf_bytes)
    """
    from ..models import (
        ArtifactEvidence,
        ArtifactType,
        ArtifactHashSet,
        WatermarkDescriptor,
        WatermarkType,
        utc_now_iso,
        sha256_bytes,
        sha256_text,
    )
    from ..images.qr import make_verification_url_qr

    # Generate IDs
    artifact_id = str(uuid.uuid4())
    watermark_id = f"wmk-{uuid.uuid4()}"
    verification_url = f"{verification_base_url.rstrip('/')}/verify/{artifact_id}"

    # Step 1: Apply metadata watermark
    from .metadata import apply_pdf_metadata_watermark

    pdf_with_metadata = apply_pdf_metadata_watermark(
        pdf_bytes=pdf_bytes,
        watermark_id=watermark_id,
        verification_url=verification_url,
        model_id=model_id,
        artifact_id=artifact_id,
        additional_metadata=additional_metadata,
    )

    # Step 2: Generate QR code
    qr_bytes = make_verification_url_qr(
        artifact_id=artifact_id,
        base_url=verification_base_url,
        box_size=4,
        border=1,
    )

    # Step 3: Apply QR watermark
    pdf_with_qr = apply_qr_watermark_to_pdf(
        pdf_bytes=pdf_with_metadata,
        qr_image_bytes=qr_bytes,
        qr_position=qr_position,
        qr_size=qr_size,
        add_page_numbers=add_page_numbers,
        add_verify_text=True,
    )

    # Step 4: Optional text stamp
    if add_text_stamp:
        if stamp_text is None:
            stamp_text = f"AI Generated Content | Verify at {verification_base_url}"

        watermarked_bytes = apply_text_stamp_to_pdf(
            pdf_bytes=pdf_with_qr,
            stamp_text=stamp_text,
            position="footer",
            font_size=7,
            color=(0.6, 0.6, 0.6),
        )
    else:
        watermarked_bytes = pdf_with_qr

    # Compute dual-state hashes
    prompt_hash = sha256_text(prompt)
    hash_before = sha256_bytes(pdf_bytes)
    hash_after = sha256_bytes(watermarked_bytes)

    # Build hash set
    hash_set = ArtifactHashSet(
        content_hash_before_watermark=hash_before,
        content_hash_after_watermark=hash_after,
    )

    # Build watermark descriptor
    watermark = WatermarkDescriptor(
        watermark_id=watermark_id,
        watermark_type=WatermarkType.VISIBLE,
        tag_text=f"QR Code Watermark: {watermark_id}",
        verification_url=verification_url,
        embed_method="qr_code_footer",
        removal_resistance="high",  # Visual watermarks harder to remove cleanly
        location=f"footer_{qr_position}",
    )

    # Build metadata
    metadata = {
        "distribution_state": "watermarked",
        "artifact_format_version": "1.0",
        "watermark_mode": "visual_qr",
        "qr_position": qr_position,
        "qr_size_inches": qr_size,
        "has_page_numbers": add_page_numbers,
        "has_text_stamp": add_text_stamp,
    }

    # Create evidence
    evidence = ArtifactEvidence(
        artifact_id=artifact_id,
        artifact_type=ArtifactType.PDF,
        mime_type="application/pdf",
        created_at=utc_now_iso(),
        model_id=model_id,
        model_version=model_version,
        actor_id=actor_id,
        prompt_hash=prompt_hash,
        output_hash_raw=hash_before,
        output_hash_distributed=hash_after,
        watermark=watermark,
        hashes=hash_set,
        fingerprints=[],
        metadata=metadata,
    )

    return evidence, watermarked_bytes


def verify_pdf_qr_watermark(pdf_bytes: bytes) -> bool:
    """
    Check if PDF has visible QR watermark.

    This is a simple check - for full verification, use verify_pdf_artifact()
    from metadata.py which validates against stored evidence.

    Args:
        pdf_bytes: PDF bytes to check

    Returns:
        True if PDF appears to have QR watermark (heuristic check)
    """
    _check_dependencies()

    try:
        reader = PdfReader(BytesIO(pdf_bytes))

        # Check if any page has images (QR codes are embedded as images)
        for page in reader.pages:
            if hasattr(page, "images") and len(page.images) > 0:
                return True

        # Alternative: Check resources for XObject images
        for page in reader.pages:
            if "/XObject" in page["/Resources"]:
                xobjects = page["/Resources"]["/XObject"].get_object()
                for obj in xobjects.values():
                    if obj["/Subtype"] == "/Image":
                        return True

        return False
    except Exception:
        return False
