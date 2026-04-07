"""
CIAF Watermarking - PDF Metadata Watermarking

Embeds provenance information in PDF metadata fields.

Metadata fields used:
- /Subject: Watermark ID and verification URL
- /Keywords: AI provenance tags
- /Creator: CIAF system identifier
- /Producer: Original preserved
- /CustomProperties: Full evidence JSON (if supported)

Uses pypdf for PDF manipulation (successor to PyPDF2).

Created: 2026-03-24
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

from typing import Tuple, Optional, Dict, Any, TYPE_CHECKING
from io import BytesIO
import uuid

if TYPE_CHECKING:
    from ciaf.watermarks.models import ArtifactEvidence, VerificationResult

try:
    from pypdf import PdfReader, PdfWriter  # type: ignore[import-untyped, assignment]

    PYPDF_AVAILABLE = True
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter  # type: ignore[import-untyped, assignment, no-redef]

        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False
        PdfReader = None  # type: ignore[assignment, misc]
        PdfWriter = None  # type: ignore[assignment, misc]


def apply_pdf_metadata_watermark(
    pdf_bytes: bytes,
    watermark_id: str,
    model_id: str,
    artifact_id: str,
    verification_url: Optional[str] = None,
    timestamp: Optional[str] = None,
    additional_metadata: Optional[Dict[str, str]] = None,
) -> bytes:
    """
    Apply metadata watermark to PDF.

    Embeds provenance information in PDF metadata without visible changes.

    Args:
        pdf_bytes: Original PDF bytes
        watermark_id: Watermark identifier
        model_id: Model identifier
        artifact_id: Artifact identifier
        verification_url: Optional verification URL
        timestamp: Optional ISO 8601 timestamp (ignored for compatibility)
        additional_metadata: Optional additional metadata fields

    Returns:
        Watermarked PDF bytes

    Raises:
        ImportError: If pypdf/PyPDF2 not available
    """
    if not PYPDF_AVAILABLE:
        raise ImportError(
            "pypdf or PyPDF2 required for PDF watermarking. " "Install with: pip install pypdf"
        )

    # Read PDF
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)

    # Preserve existing metadata
    existing_metadata: Dict[str, Any] = reader.metadata or {}  # type: ignore[assignment]

    # Build watermark metadata
    metadata = {
        "/Subject": f"AI Generated Content | Watermark: {watermark_id}",
        "/Creator": f"CIAF Framework (Model: {model_id})",
    }

    # Add verification URL if provided
    if verification_url:
        metadata["/Keywords"] = f"AI-Generated, CIAF-Watermarked, Verify: {verification_url}"

    # Preserve original producer if exists
    if "/Producer" in existing_metadata:
        metadata["/Producer"] = str(existing_metadata["/Producer"])
    else:
        metadata["/Producer"] = "CIAF Watermarking System v1.0"

    # Preserve title if exists
    if "/Title" in existing_metadata:
        metadata["/Title"] = str(existing_metadata["/Title"])

    # Preserve author if exists
    if "/Author" in existing_metadata:
        metadata["/Author"] = str(existing_metadata["/Author"])

    # Add custom metadata if provided
    if additional_metadata:
        for key, value in additional_metadata.items():
            if not key.startswith("/"):
                key = f"/{key}"
            metadata[key] = value

    # Add CIAF-specific metadata
    metadata["/CIAF_ArtifactID"] = artifact_id
    metadata["/CIAF_WatermarkID"] = watermark_id
    metadata["/CIAF_VerificationURL"] = verification_url or ""
    metadata["/CIAF_ModelID"] = model_id

    # Set metadata
    writer.add_metadata(metadata)

    # Write to bytes
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def extract_pdf_metadata_watermark(pdf_bytes: bytes) -> Optional[Dict[str, str]]:
    """
    Extract watermark information from PDF metadata.

    Args:
        pdf_bytes: PDF bytes to examine

    Returns:
        Dictionary with watermark fields if found, None otherwise
    """
    if not PYPDF_AVAILABLE:
        raise ImportError("pypdf or PyPDF2 required")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        metadata = reader.metadata

        if not metadata:
            return None

        # Extract CIAF fields
        watermark_info = {}

        if "/CIAF_ArtifactID" in metadata:
            watermark_info["artifact_id"] = str(metadata["/CIAF_ArtifactID"])  # type: ignore[index]

        if "/CIAF_WatermarkID" in metadata:
            watermark_info["watermark_id"] = str(metadata["/CIAF_WatermarkID"])  # type: ignore[index]

        if "/CIAF_VerificationURL" in metadata:
            watermark_info["verification_url"] = str(metadata["/CIAF_VerificationURL"])  # type: ignore[index]

        if "/CIAF_ModelID" in metadata:
            watermark_info["model_id"] = str(metadata["/CIAF_ModelID"])  # type: ignore[index]

        # Also check Subject field for watermark
        if "/Subject" in metadata:  # type: ignore[operator]
            subject = str(metadata["/Subject"])
            if "Watermark:" in subject or "CIAF" in subject:
                watermark_info["subject"] = subject

        # Check Keywords field
        if "/Keywords" in metadata:  # type: ignore[operator]
            keywords = str(metadata["/Keywords"])
            if "CIAF-Watermarked" in keywords or "AI-Generated" in keywords:
                watermark_info["keywords"] = keywords

        return watermark_info if watermark_info else None  # type: ignore[return-value]

    except Exception:
        return None


def has_pdf_watermark(pdf_bytes: bytes) -> bool:
    """
    Check if PDF has CIAF watermark.

    Args:
        pdf_bytes: PDF bytes to check

    Returns:
        True if watermark detected
    """
    watermark = extract_pdf_metadata_watermark(pdf_bytes)
    return watermark is not None and "watermark_id" in watermark


def build_pdf_artifact_evidence(
    pdf_bytes: bytes,
    model_id: str,
    model_version: str,
    actor_id: str,
    prompt: str,
    verification_base_url: str,
    additional_metadata: Optional[Dict[str, str]] = None,
) -> Tuple["ArtifactEvidence", bytes]:
    """
    Build complete artifact evidence for PDF with metadata watermark.

    This is the main function for creating watermarked PDF artifacts.
    Follows the dual-state hashing pattern.

    Args:
        pdf_bytes: Original PDF bytes
        model_id: Model identifier
        model_version: Model version
        actor_id: User/system identifier
        prompt: Input prompt
        verification_base_url: Base URL for verification
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

    # Generate IDs
    artifact_id = str(uuid.uuid4())
    watermark_id = f"wmk-{uuid.uuid4()}"
    verification_url = f"{verification_base_url.rstrip('/')}/verify/{artifact_id}"

    # Apply watermark
    watermarked_bytes = apply_pdf_metadata_watermark(
        pdf_bytes=pdf_bytes,
        watermark_id=watermark_id,
        verification_url=verification_url,
        model_id=model_id,
        artifact_id=artifact_id,
        additional_metadata=additional_metadata,
    )

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
        watermark_type=WatermarkType.METADATA,
        tag_text=f"PDF Metadata Watermark: {watermark_id}",
        verification_url=verification_url,
        embed_method="pdf_metadata",
        removal_resistance="medium",  # Metadata can be stripped but requires tools
        location="metadata",
    )

    # Build metadata
    metadata = {
        "distribution_state": "watermarked",
        "artifact_format_version": "1.0",
        "watermark_mode": "metadata",
        "pdf_metadata_fields": ["/Subject", "/Keywords", "/Creator", "/CIAF_*"],
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

    # Compute receipt hash
    receipt_hash = sha256_bytes(evidence.to_canonical_bytes())
    evidence.hashes.canonical_receipt_hash = receipt_hash

    return evidence, watermarked_bytes


def verify_pdf_artifact(
    suspect_pdf_bytes: bytes,
    evidence: "ArtifactEvidence",
) -> "VerificationResult":
    """
    Verify suspect PDF against stored evidence.

    Checks:
    1. Exact hash match (before/after watermark)
    2. Watermark presence in metadata
    3. Watermark integrity

    Args:
        suspect_pdf_bytes: PDF to verify
        evidence: Stored evidence record

    Returns:
        VerificationResult with analysis
    """
    from ..models import ArtifactType, VerificationResult
    from ..hashing import sha256_bytes

    if evidence.artifact_type != ArtifactType.PDF:
        raise ValueError(f"Evidence is not for PDF artifact: {evidence.artifact_type}")

    notes = []
    suspect_hash = sha256_bytes(suspect_pdf_bytes)

    # Check 1: Exact match to distributed version
    match_after = suspect_hash == evidence.hashes.content_hash_after_watermark
    if match_after:
        notes.append("[OK] Exact match to distributed watermarked version.")

    # Check 2: Exact match to original version
    match_before = suspect_hash == evidence.hashes.content_hash_before_watermark
    if match_before:
        notes.append("[OK] Exact match to original pre-watermark version.")

    # Check 3: Watermark removal detection
    likely_removed = False
    if match_before and not match_after:
        likely_removed = True
        notes.append("[WARN] Watermark likely removed!")
        notes.append("  Content matches pre-watermark version but metadata watermark is missing.")

    # Check 4: Watermark presence in metadata
    watermark_present = has_pdf_watermark(suspect_pdf_bytes)
    watermark_intact = False

    if watermark_present:
        extracted = extract_pdf_metadata_watermark(suspect_pdf_bytes)
        if extracted and extracted.get("watermark_id") == evidence.watermark.watermark_id:
            watermark_intact = True
            notes.append("[OK] Original watermark present in metadata.")
        else:
            notes.append("[WARN] Different watermark detected in metadata.")
    elif not match_after:
        notes.append("[FAIL] No watermark detected in PDF metadata.")

    # Determine confidence
    confidence = 0.0
    if match_after:
        confidence = 1.0  # Perfect match
    elif match_before:
        confidence = 0.95  # Original content, watermark removed
    else:
        confidence = 0.0  # No match

    # Create result
    result = VerificationResult(
        artifact_id=evidence.artifact_id,
        exact_match_after_watermark=match_after,
        exact_match_before_watermark=match_before,
        likely_tag_removed=likely_removed,
        normalized_match_before=False,  # N/A for PDFs
        normalized_match_after=False,
        perceptual_similarity_score=None,  # N/A for PDFs (could add page count matching)
        simhash_distance=None,
        watermark_present=watermark_present,
        watermark_intact=watermark_intact,
        content_modified=not (match_before or match_after),
        notes=notes,
        confidence=confidence,
        evidence_record=evidence,
    )

    return result


__all__ = [
    # Watermarking
    "apply_pdf_metadata_watermark",
    "build_pdf_artifact_evidence",
    # Extraction
    "extract_pdf_metadata_watermark",
    "has_pdf_watermark",
    # Verification
    "verify_pdf_artifact",
    # Constants
    "PYPDF_AVAILABLE",
]
