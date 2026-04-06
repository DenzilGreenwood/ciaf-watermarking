"""
CIAF Watermarking - PDF Package

PDF watermarking with metadata embedding and visual QR codes.

Components:
- metadata.py: Metadata watermarking (invisible)
- visual.py: Visual watermarking with QR codes (NEW)

Main Functions:
- build_pdf_artifact_evidence(): Complete watermarked PDF with metadata
- build_pdf_artifact_with_visual_watermark(): PDF with QR code + metadata
- apply_pdf_metadata_watermark(): Embed watermark in PDF metadata
- apply_qr_watermark_to_pdf(): Add QR codes to PDF pages
- extract_pdf_metadata_watermark(): Extract watermark from metadata
- verify_pdf_artifact(): Verify PDF against evidence

Created: 2026-03-24
Updated: 2026-03-30 (added visual watermarking)
Author: Denzil James Greenwood
Version: 1.1.0
"""

from .metadata import (
    apply_pdf_metadata_watermark,
    extract_pdf_metadata_watermark,
    has_pdf_watermark,
    build_pdf_artifact_evidence,
    verify_pdf_artifact,
    PYPDF_AVAILABLE,
)

from .visual import (
    apply_qr_watermark_to_pdf,
    apply_text_stamp_to_pdf,
    build_pdf_artifact_with_visual_watermark,
    verify_pdf_qr_watermark,
    create_qr_overlay_page,
)

__all__ = [
    # Metadata Watermarking
    "apply_pdf_metadata_watermark",
    "build_pdf_artifact_evidence",
    "extract_pdf_metadata_watermark",
    "has_pdf_watermark",
    "verify_pdf_artifact",
    # Visual Watermarking (NEW)
    "apply_qr_watermark_to_pdf",
    "apply_text_stamp_to_pdf",
    "build_pdf_artifact_with_visual_watermark",
    "verify_pdf_qr_watermark",
    "create_qr_overlay_page",
    # Constants
    "PYPDF_AVAILABLE",
]
