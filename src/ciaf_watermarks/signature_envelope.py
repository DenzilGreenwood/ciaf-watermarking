"""
CIAF Watermarking - Signature Envelope Models

Production-ready signature envelope structures matching CIAF JSON schemas.
Implements the signature-envelope.json and signature-metadata.json patterns
for consistent cryptographic signing across all CIAF objects.

Created: 2026-03-30
Last Modified: 2026-03-30
Author: Denzil James Greenwood
Version: 2.0.0 - Converted to Pydantic models
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class KeyBackend(str, Enum):
    """Key storage/custody backend for audit trail."""

    LOCAL = "local"  # Local key file (dev/test only)
    KMS = "kms"  # AWS KMS, Azure Key Vault, etc.
    HSM = "hsm"  # Hardware Security Module
    CLOUDHSM = "cloudhsm"  # AWS CloudHSM, etc.
    EXTERNAL_KMS = "external_kms"  # Third-party KMS


class SignatureEncoding(str, Enum):
    """Signature value encoding format."""

    BASE64 = "base64"
    BASE64URL = "base64url"
    HEX = "hex"


class SignatureMetadata(BaseModel):
    """
    Signature metadata describing how an object was signed.

    Maps to: ciaf/schemas/common/signature-metadata.json

    Mandatory fields ensure complete audit trail of signing operation,
    including key custody (key_backend) for compliance tracking.
    """

    # Required fields (per schema)
    signature_algorithm: str = Field(
        ..., min_length=1, description="Signature algorithm"
    )  # "Ed25519" (const)
    key_id: str = Field(
        ..., min_length=1, description="Key identifier"
    )  # Stable key identifier (e.g., "aws-kms:alias/ciaf-prod")
    canonicalization_version: str = Field(
        ..., min_length=1, description="Canonicalization version"
    )  # e.g., "RFC8785-like/1.0"
    key_backend: KeyBackend = Field(..., description="Key backend")  # Mandatory for audit trail

    # Optional but recommended
    signing_service: Optional[str] = Field(
        None, description="Signing service"
    )  # e.g., "ciaf-vault-signer"
    public_key_ref: Optional[str] = Field(
        None, description="Public key reference"
    )  # e.g., "jwks://example.com/keys/123"
    verification_method: Optional[str] = Field(
        None, description="Verification method"
    )  # e.g., "ciaf-verify/v1"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = self.model_dump()
        result["key_backend"] = self.key_backend.value
        # Remove None values for cleaner JSON
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignatureMetadata:
        """Create from dictionary."""
        data_copy = data.copy()
        if "key_backend" in data_copy:
            data_copy["key_backend"] = KeyBackend(data_copy["key_backend"])
        return cls(**data_copy)


class SignatureEnvelope(BaseModel):
    """
    Complete cryptographic signature payload for CIAF objects.

    Maps to: ciaf/schemas/common/signature-envelope.json

    This structure ensures:
    - Complete audit trail (what, when, how, by whom)
    - Unambiguous signature encoding
    - Consistent canonicalization tracking
    - Key backend declaration (mandatory for compliance)
    - Separation of signature value from metadata

    Usage:
        >>> envelope = SignatureEnvelope(
        ...     payload_hash="abc123...",
        ...     hash_algorithm="SHA-256",
        ...     signature_value="base64encodedstring",
        ...     signature_encoding=SignatureEncoding.BASE64,
        ...     signed_at="2026-03-30T18:00:00Z",
        ...     metadata=SignatureMetadata(
        ...         signature_algorithm="Ed25519",
        ...         key_id="aws-kms:alias/ciaf-prod",
        ...         canonicalization_version="RFC8785-like/1.0",
        ...         key_backend=KeyBackend.KMS,
        ...     )
        ... )
    """

    # Required fields (per schema)
    payload_hash: str = Field(
        ..., min_length=1, description="Payload hash"
    )  # SHA-256 hash (64 hex chars)
    hash_algorithm: str = Field(
        ..., min_length=1, description="Hash algorithm"
    )  # "SHA-256" (const)
    signature_value: str = Field(..., description="Signature value")  # Encoded Ed25519 signature
    signature_encoding: SignatureEncoding = Field(
        ..., description="Signature encoding"
    )  # base64, base64url, or hex
    signed_at: str = Field(..., description="Signing timestamp")  # RFC3339 timestamp
    metadata: SignatureMetadata = Field(..., description="Signature metadata")  # Signature metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "payload_hash": self.payload_hash,
            "hash_algorithm": self.hash_algorithm,
            "signature_value": self.signature_value,
            "signature_encoding": self.signature_encoding.value,
            "signed_at": self.signed_at,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignatureEnvelope:
        """Create from dictionary."""
        data_copy = data.copy()
        if "signature_encoding" in data_copy:
            data_copy["signature_encoding"] = SignatureEncoding(data_copy["signature_encoding"])
        if "metadata" in data_copy:
            data_copy["metadata"] = SignatureMetadata.from_dict(data_copy["metadata"])
        return cls(**data_copy)

    @classmethod
    def create_unsigned_placeholder(cls) -> SignatureEnvelope:
        """
        Create placeholder envelope for unsigned objects.

        Useful during object construction before signing.
        """
        return cls(
            payload_hash="0" * 64,  # Placeholder
            hash_algorithm="SHA-256",
            signature_value="",
            signature_encoding=SignatureEncoding.BASE64,
            signed_at=datetime.now(timezone.utc).isoformat(),
            metadata=SignatureMetadata(
                signature_algorithm="Ed25519",
                key_id="unsigned",
                canonicalization_version="RFC8785-like/1.0",
                key_backend=KeyBackend.LOCAL,
            ),
        )


def create_signature_envelope(
    evidence_or_payload_hash,
    signature_value: Optional[str] = None,
    key_id: Optional[str] = None,
    key_backend: KeyBackend = KeyBackend.LOCAL,
    signature_encoding: SignatureEncoding = SignatureEncoding.BASE64,
    signing_service: Optional[str] = None,
    public_key_ref: Optional[str] = None,
) -> SignatureEnvelope:
    """
    Factory function to create a signature envelope.

    Simplifies creation with sensible defaults.
    Supports two calling patterns:
    1. create_signature_envelope(evidence) - Creates unsigned envelope from ArtifactEvidence
    2. create_signature_envelope(payload_hash, signature_value, key_id, ...) - Full signature

    Args:
        evidence_or_payload_hash: Either ArtifactEvidence or SHA-256 hash string
        signature_value: Encoded signature (required if payload_hash is string)
        key_id: Key identifier (required if payload_hash is string)
        key_backend: Key custody backend (default: LOCAL)
        signature_encoding: Signature encoding format (default: BASE64)
        signing_service: Optional signing service name
        public_key_ref: Optional public key reference (jwks:// URL)

    Returns:
        SignatureEnvelope instance

    Example:
        >>> # From evidence (unsigned)
        >>> envelope = create_signature_envelope(evidence)
        >>>
        >>> # With full signature
        >>> envelope = create_signature_envelope(
        ...     payload_hash="abc123def456...",
        ...     signature_value="SGVsbG8gV29ybGQ...",
        ...     key_id="ciaf-watermark-key",
        ...     key_backend=KeyBackend.KMS,
        ... )
    """
    # Check if first argument is ArtifactEvidence
    if hasattr(evidence_or_payload_hash, "compute_receipt_hash"):
        # Create envelope from evidence (unsigned)
        evidence = evidence_or_payload_hash
        payload_hash = evidence.compute_receipt_hash()
        # Use placeholder signature for unsigned envelope
        signature_value = signature_value or "unsigned"
        key_id = key_id or "none"
    else:
        # Traditional usage with explicit hash
        payload_hash = evidence_or_payload_hash
        if not signature_value or not key_id:
            raise TypeError(
                "create_signature_envelope() missing required arguments: "
                "'signature_value' and 'key_id' when called with payload_hash"
            )

    return SignatureEnvelope(
        payload_hash=payload_hash,
        hash_algorithm="SHA-256",
        signature_value=signature_value,
        signature_encoding=signature_encoding,
        signed_at=datetime.now(timezone.utc).isoformat(),
        metadata=SignatureMetadata(
            signature_algorithm="Ed25519",
            key_id=key_id,
            canonicalization_version="RFC8785-like/1.0",
            key_backend=key_backend,
            signing_service=signing_service,
            public_key_ref=public_key_ref,
            verification_method="ciaf-verify/v1",
        ),
    )


__all__ = [
    "KeyBackend",
    "SignatureEncoding",
    "SignatureMetadata",
    "SignatureEnvelope",
    "create_signature_envelope",
]
