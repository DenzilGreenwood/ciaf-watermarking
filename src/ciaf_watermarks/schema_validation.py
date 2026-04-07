"""
CIAF Watermarking - Schema Validation Utilities

Utilities to validate data structures against the CIAF schema specification.
See SCHEMA.md for complete schema documentation.

Created: 2026-04-06
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from .models import (
    ArtifactEvidence,
    WatermarkType,
    WatermarkDescriptor,
    ForensicFragmentSet,
)

# ============================================================================
# ID VALIDATION
# ============================================================================


def validate_artifact_id(artifact_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate artifact_id follows UUID v4 format.

    Args:
        artifact_id: Artifact identifier to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not artifact_id:
        return False, "artifact_id cannot be empty"

    # UUID v4 pattern
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    if not uuid_pattern.match(artifact_id):
        return False, "artifact_id must be valid UUID v4"

    return True, None


def validate_watermark_id(watermark_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate watermark_id follows wmk-{uuid} format.

    Args:
        watermark_id: Watermark identifier to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not watermark_id:
        return False, "watermark_id cannot be empty"

    if not watermark_id.startswith("wmk-"):
        return False, "watermark_id must start with 'wmk-'"

    # Extract UUID part
    uuid_part = watermark_id[4:]
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    if not uuid_pattern.match(uuid_part):
        return False, "watermark_id must be wmk-{valid-uuid}"

    return True, None


def validate_fragment_id(fragment_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate fragment_id follows frag_{index}_{location} format.

    Args:
        fragment_id: Fragment identifier to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not fragment_id:
        return False, "fragment_id cannot be empty"

    if not fragment_id.startswith("frag_"):
        return False, "fragment_id must start with 'frag_'"

    # Pattern: frag_{number}_{location}
    pattern = re.compile(r"^frag_\d+_[a-z_]+$", re.IGNORECASE)

    if not pattern.match(fragment_id):
        return False, "fragment_id must follow pattern: frag_{index}_{location}"

    return True, None


# ============================================================================
# HASH VALIDATION
# ============================================================================


def validate_sha256_hash(hash_value: str) -> Tuple[bool, Optional[str]]:
    """
    Validate hash is 64-character lowercase hex string (SHA-256).

    Args:
        hash_value: Hash to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not hash_value:
        return False, "hash cannot be empty"

    if len(hash_value) != 64:
        return False, f"SHA-256 hash must be 64 characters, got {len(hash_value)}"

    if not re.match(r"^[0-9a-f]{64}$", hash_value):
        return False, "SHA-256 hash must be lowercase hex"

    return True, None


# ============================================================================
# TIMESTAMP VALIDATION
# ============================================================================


def validate_iso8601_timestamp(timestamp: str) -> Tuple[bool, Optional[str]]:
    """
    Validate timestamp follows ISO 8601 format.

    Args:
        timestamp: Timestamp to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not timestamp:
        return False, "timestamp cannot be empty"

    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return True, None
    except ValueError as e:
        return False, f"Invalid ISO 8601 timestamp: {e}"


# ============================================================================
# FIELD VALIDATION
# ============================================================================


def validate_confidence_score(score: float) -> Tuple[bool, Optional[str]]:
    """
    Validate confidence score is between 0.0 and 1.0.

    Args:
        score: Confidence score to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(score, (int, float)):
        return False, "confidence must be numeric"

    if not 0.0 <= score <= 1.0:
        return False, f"confidence must be between 0.0 and 1.0, got {score}"

    return True, None


def validate_entropy_score(score: float) -> Tuple[bool, Optional[str]]:
    """
    Validate entropy score is between 0.0 and 1.0.

    Args:
        score: Entropy score to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(score, (int, float)):
        return False, "entropy_score must be numeric"

    if not 0.0 <= score <= 1.0:
        return False, f"entropy_score must be between 0.0 and 1.0, got {score}"

    return True, None


# ============================================================================
# EVIDENCE VALIDATION
# ============================================================================


def validate_artifact_evidence(evidence: ArtifactEvidence) -> List[str]:
    """
    Validate complete artifact evidence against schema.

    Args:
        evidence: ArtifactEvidence to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Validate artifact_id
    valid, error = validate_artifact_id(evidence.artifact_id)
    if not valid:
        errors.append(f"artifact_id: {error}")

    # Validate timestamps
    valid, error = validate_iso8601_timestamp(evidence.created_at)
    if not valid:
        errors.append(f"created_at: {error}")

    # Validate hashes
    for hash_field in ["prompt_hash", "output_hash_raw", "output_hash_distributed"]:
        hash_value = getattr(evidence, hash_field)
        valid, error = validate_sha256_hash(hash_value)
        if not valid:
            errors.append(f"{hash_field}: {error}")

    # Validate dual-state hashes
    valid, error = validate_sha256_hash(evidence.hashes.content_hash_before_watermark)
    if not valid:
        errors.append(f"hashes.content_hash_before_watermark: {error}")

    valid, error = validate_sha256_hash(evidence.hashes.content_hash_after_watermark)
    if not valid:
        errors.append(f"hashes.content_hash_after_watermark: {error}")

    # Validate watermark_id
    valid, error = validate_watermark_id(evidence.watermark.watermark_id)
    if not valid:
        errors.append(f"watermark.watermark_id: {error}")

    # Validate forensic fragments if present
    if evidence.hashes.forensic_fragments:
        fragment_errors = validate_forensic_fragment_set(evidence.hashes.forensic_fragments)
        errors.extend(fragment_errors)

    return errors


def validate_forensic_fragment_set(
    fragment_set: ForensicFragmentSet,
) -> List[str]:
    """
    Validate forensic fragment set.

    Args:
        fragment_set: ForensicFragmentSet to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Validate fragment count
    actual_count = len(fragment_set.all_fragments)
    if fragment_set.fragment_count != actual_count:
        errors.append(
            f"fragment_count mismatch: declared {fragment_set.fragment_count}, "
            f"actual {actual_count}"
        )

    # Validate entropy threshold
    if not 0.0 <= fragment_set.min_entropy_threshold <= 1.0:
        errors.append(
            f"min_entropy_threshold must be 0.0-1.0, " f"got {fragment_set.min_entropy_threshold}"
        )

    # Validate individual fragments
    for fragment in fragment_set.all_fragments:
        # Validate fragment_id
        valid, error = validate_fragment_id(fragment.fragment_id)
        if not valid:
            errors.append(f"fragment {fragment.fragment_id}: {error}")

        # Validate entropy_score
        valid, error = validate_entropy_score(fragment.entropy_score)
        if not valid:
            errors.append(f"fragment {fragment.fragment_id}: {error}")

    return errors


def validate_watermark_descriptor(descriptor: WatermarkDescriptor) -> List[str]:
    """
    Validate watermark descriptor.

    Args:
        descriptor: WatermarkDescriptor to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Validate watermark_id
    valid, error = validate_watermark_id(descriptor.watermark_id)
    if not valid:
        errors.append(f"watermark_id: {error}")

    # Validate watermark_type
    if not isinstance(descriptor.watermark_type, WatermarkType):
        errors.append("watermark_type must be WatermarkType enum")

    # Validate removal_resistance if present
    if descriptor.removal_resistance:
        valid_levels = ["low", "medium", "high"]
        if descriptor.removal_resistance not in valid_levels:
            errors.append(
                f"removal_resistance must be one of {valid_levels}, "
                f"got {descriptor.removal_resistance}"
            )

    return errors


# ============================================================================
# BATCH VALIDATION
# ============================================================================


def validate_evidence_batch(evidence_list: List[ArtifactEvidence]) -> Dict[str, Any]:
    """
    Validate batch of evidence records.

    Args:
        evidence_list: List of ArtifactEvidence records

    Returns:
        Dictionary with validation results:
        - total: Total records validated
        - valid: Number of valid records
        - invalid: Number of invalid records
        - errors: Dict mapping artifact_id -> list of errors
    """
    results: Dict[str, Any] = {
        "total": len(evidence_list),
        "valid": 0,
        "invalid": 0,
        "errors": {},
    }

    for evidence in evidence_list:
        errors = validate_artifact_evidence(evidence)
        if errors:
            results["invalid"] += 1
            results["errors"][evidence.artifact_id] = errors
        else:
            results["valid"] += 1

    return results


# ============================================================================
# SCHEMA COMPLIANCE REPORT
# ============================================================================


def generate_compliance_report(evidence: ArtifactEvidence) -> Dict[str, Any]:
    """
    Generate comprehensive schema compliance report.

    Args:
        evidence: ArtifactEvidence to analyze

    Returns:
        Dictionary with compliance details
    """
    errors = validate_artifact_evidence(evidence)

    report = {
        "artifact_id": evidence.artifact_id,
        "is_compliant": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "checks": {
            "artifact_id_format": validate_artifact_id(evidence.artifact_id)[0],
            "watermark_id_format": validate_watermark_id(evidence.watermark.watermark_id)[0],
            "timestamp_format": validate_iso8601_timestamp(evidence.created_at)[0],
            "dual_state_hashes_present": bool(
                evidence.hashes.content_hash_before_watermark
                and evidence.hashes.content_hash_after_watermark
            ),
            "forensic_fragments_present": bool(evidence.hashes.forensic_fragments),
            "signature_present": bool(evidence.signature),
        },
    }

    return report


__all__ = [
    "validate_artifact_id",
    "validate_watermark_id",
    "validate_fragment_id",
    "validate_sha256_hash",
    "validate_iso8601_timestamp",
    "validate_confidence_score",
    "validate_entropy_score",
    "validate_artifact_evidence",
    "validate_forensic_fragment_set",
    "validate_watermark_descriptor",
    "validate_evidence_batch",
    "generate_compliance_report",
]
