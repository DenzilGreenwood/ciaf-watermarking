"""
CIAF Watermarking - Unified Interface

Provides a single entry point for watermarking any AI-generated artifact
at the point of inference, with automatic type detection and dispatch.

This module enables:
- Single API call for all artifact types (text, images, PDF, etc.)
- Automatic type detection based on content
- Type-specific watermarking with appropriate strategies
- Seamless integration at model inference points

Quick Start:
    from ciaf.watermarks import watermark_ai_output

    # Works for any artifact type
    evidence, watermarked = watermark_ai_output(
        artifact=ai_model_output,  # Auto-detects type
        model_id="gpt-4",
        model_version="2026-03",
        actor_id="user:analyst-17",
        prompt="Generate content",
        verification_base_url="https://vault.example.com"
    )

Created: 2026-04-04
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple, Union

from .models import ArtifactEvidence, ArtifactType

# ============================================================================
# TYPE DETECTION
# ============================================================================


def detect_artifact_type(artifact: Union[str, bytes]) -> ArtifactType:
    """
    Automatically detect the type of artifact based on content.

    Detection Logic:
    1. If string → TEXT
    2. If bytes → Inspect magic bytes:
       - PNG: b'\\x89PNG'
       - JPEG: b'\\xff\\xd8\\xff'
       - PDF: b'%PDF'
       - WebP: b'RIFF' + b'WEBP'
       - MP4: b'ftyp' at offset 4
       - WAV: b'RIFF' + b'WAVE'
       - MP3: b'ID3' or b'\\xff\\xfb'
       - JSON: Starts with { or [ (validated)
       - Fallback: BINARY

    Args:
        artifact: Raw artifact (string or bytes)

    Returns:
        ArtifactType enum value

    Raises:
        TypeError: If artifact is neither str nor bytes

    Examples:
        >>> detect_artifact_type("Hello world")
        ArtifactType.TEXT

        >>> detect_artifact_type(b'\\x89PNG\\r\\n\\x1a\\n...')
        ArtifactType.IMAGE

        >>> detect_artifact_type(b'%PDF-1.4...')
        ArtifactType.PDF
    """
    # Text detection (simplest case)
    if isinstance(artifact, str):
        return ArtifactType.TEXT

    # Ensure bytes type
    if not isinstance(artifact, bytes):
        raise TypeError(f"Artifact must be str or bytes, got {type(artifact).__name__}")

    # Empty bytes
    if len(artifact) == 0:
        return ArtifactType.BINARY

    # PNG image
    if artifact.startswith(b"\x89PNG\r\n\x1a\n"):
        return ArtifactType.IMAGE

    # JPEG image
    if artifact.startswith(b"\xff\xd8\xff"):
        return ArtifactType.IMAGE

    # WebP image
    if artifact.startswith(b"RIFF") and len(artifact) > 12:
        if b"WEBP" in artifact[8:16]:
            return ArtifactType.IMAGE

    # GIF image
    if artifact.startswith((b"GIF87a", b"GIF89a")):
        return ArtifactType.IMAGE

    # PDF
    if artifact.startswith(b"%PDF"):
        return ArtifactType.PDF

    # MP4/MOV video
    if len(artifact) > 8 and artifact[4:8] == b"ftyp":
        return ArtifactType.VIDEO

    # WAV audio
    if artifact.startswith(b"RIFF") and len(artifact) > 12:
        if b"WAVE" in artifact[8:16]:
            return ArtifactType.AUDIO

    # MP3 audio
    if artifact.startswith((b"ID3", b"\xff\xfb", b"\xff\xf3")):
        return ArtifactType.AUDIO

    # FLAC audio
    if artifact.startswith(b"fLaC"):
        return ArtifactType.AUDIO

    # JSON detection (optimized for large files)
    # Only check first 8KB for performance - avoid parsing huge text blobs
    try:
        # Limit decode to first 8KB for performance
        sample_size = min(len(artifact), 8192)
        text_sample = artifact[:sample_size].decode("utf-8", errors="strict")
        text_stripped = text_sample.strip()

        if text_stripped and text_stripped[0] in ("{", "["):
            # For small artifacts, validate fully
            if len(artifact) <= 8192:
                json.loads(text_stripped)
                return ArtifactType.JSON
            else:
                # For large artifacts, quick structural check only
                # Check for JSON-like structure without full parse
                if text_stripped[0] == "{" and "}" in text_stripped[:1024]:
                    return ArtifactType.JSON
                elif text_stripped[0] == "[" and "]" in text_stripped[:1024]:
                    return ArtifactType.JSON
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        pass

    # Fallback: binary
    return ArtifactType.BINARY


# ============================================================================
# CONFIGURATION SYSTEM
# ============================================================================

# Global default configuration
_DEFAULT_CONFIG: Dict[str, Any] = {
    "verification_base_url": "https://vault.example.com",
    "store_in_vault": False,
    "enable_forensic_fragments": True,
    "text": {
        "style": "footer",
        "include_simhash": True,
    },
    "image": {
        "mode": "visual",
        "opacity": 0.4,
        "position": "bottom_right",
        "include_qr": True,
        "qr_position": "top_right",
    },
    "pdf": {
        "mode": "metadata",
        "add_visual_qr": False,
    },
}


def set_default_watermark_config(config: Dict[str, Any]) -> None:
    """
    Set global default watermark configuration.

    This configuration will be used as defaults for all watermark_ai_output()
    calls unless overridden per-call.

    Args:
        config: Configuration dictionary with keys:
            - verification_base_url: Default vault URL
            - store_in_vault: Auto-store in vault (default False)
            - enable_forensic_fragments: Enable DNA sampling (default True)
            - text: Text-specific config dict
            - image: Image-specific config dict
            - pdf: PDF-specific config dict

    Example:
        >>> set_default_watermark_config({
        ...     "verification_base_url": "https://vault.mycompany.com",
        ...     "store_in_vault": True,
        ...     "text": {"style": "header"},
        ...     "image": {"opacity": 0.5, "include_qr": True}
        ... })
    """
    _DEFAULT_CONFIG.update(config)


def get_default_watermark_config() -> Dict[str, Any]:
    """
    Get current global default watermark configuration.

    Returns:
        Copy of default configuration dictionary
    """
    return _DEFAULT_CONFIG.copy()


# ============================================================================
# WATERMARK DISPATCHER
# ============================================================================


class WatermarkDispatcher:
    """
    Dispatches watermarking requests to type-specific handlers.

    This class routes artifacts to the appropriate watermarking function
    based on their type, handling configuration parsing and parameter mapping.
    """

    def dispatch(
        self,
        artifact: Union[str, bytes],
        artifact_type: ArtifactType,
        model_id: str,
        model_version: str,
        actor_id: str,
        prompt: str,
        verification_base_url: str,
        watermark_config: Optional[Dict[str, Any]] = None,
        enable_forensic_fragments: bool = True,
    ) -> Tuple[ArtifactEvidence, Union[str, bytes]]:
        """
        Dispatch to appropriate watermarker based on artifact type.

        Args:
            artifact: Raw artifact (text or bytes)
            artifact_type: Detected or specified artifact type
            model_id: Model identifier
            model_version: Model version
            actor_id: User/system identifier
            prompt: Input prompt
            verification_base_url: Base URL for verification
            watermark_config: Type-specific configuration
            enable_forensic_fragments: Enable DNA sampling

        Returns:
            Tuple of (evidence, watermarked_artifact)

        Raises:
            NotImplementedError: For unsupported artifact types
            ValueError: For invalid artifact type
        """
        # Common parameters for all watermarkers
        common_params = {
            "model_id": model_id,
            "model_version": model_version,
            "actor_id": actor_id,
            "prompt": prompt,
            "verification_base_url": verification_base_url,
        }

        # Dispatch based on artifact type
        if artifact_type == ArtifactType.TEXT:
            return self._watermark_text(
                artifact,
                common_params,
                watermark_config,
                enable_forensic_fragments,
            )

        elif artifact_type == ArtifactType.IMAGE:
            return self._watermark_image(
                artifact,
                common_params,
                watermark_config,
            )

        elif artifact_type == ArtifactType.PDF:
            return self._watermark_pdf(
                artifact,
                common_params,
                watermark_config,
            )

        elif artifact_type == ArtifactType.JSON:
            # JSON watermarking not yet implemented
            raise NotImplementedError(
                "JSON watermarking not yet implemented. "
                "JSON artifacts can be watermarked as text by converting to string first."
            )

        elif artifact_type == ArtifactType.AUDIO:
            # Audio not implemented
            raise NotImplementedError(
                "Audio watermarking not yet implemented. "
                "This is a roadmap item for future development."
            )

        elif artifact_type == ArtifactType.VIDEO:
            return self._watermark_video(
                artifact,
                common_params,
                watermark_config,
            )

        elif artifact_type == ArtifactType.BINARY:
            # Binary not implemented
            raise NotImplementedError(
                "Binary watermarking not yet implemented. "
                "Consider converting to a supported format (text, image, PDF)."
            )

        else:
            raise ValueError(f"Unknown artifact type: {artifact_type}")

    def _watermark_text(
        self,
        text: str,
        common_params: Dict[str, Any],
        config: Optional[Dict[str, Any]],
        enable_forensic_fragments: bool,
    ) -> Tuple[ArtifactEvidence, str]:
        """Watermark text artifact."""
        from .text import build_text_artifact_evidence

        # Merge with default text config
        style = "footer"
        include_simhash = True

        if config:
            if "style" in config:
                style = config["style"]
            if "include_simhash" in config:
                include_simhash = config["include_simhash"]
        else:
            # Use defaults
            default_text_config = _DEFAULT_CONFIG.get("text", {})
            style = default_text_config.get("style", "footer")
            include_simhash = default_text_config.get("include_simhash", True)

        return build_text_artifact_evidence(
            raw_text=text,
            **common_params,
            watermark_style=style,
            include_simhash=include_simhash,
        )

    def _watermark_image(
        self,
        image_bytes: bytes,
        common_params: Dict[str, Any],
        config: Optional[Dict[str, Any]],
    ) -> Tuple[ArtifactEvidence, bytes]:
        """Watermark image artifact."""
        from .images import build_image_artifact_evidence, ImageWatermarkSpec

        # Merge config with defaults
        default_image_config = _DEFAULT_CONFIG.get("image", {})
        merged_config = {**default_image_config, **(config or {})}

        # Create watermark spec
        spec = ImageWatermarkSpec(
            mode=merged_config.get("mode", "visual"),
            text=merged_config.get("text"),
            opacity=merged_config.get("opacity", 0.4),
            position=merged_config.get("position", "bottom_right"),
            font_size=merged_config.get("font_size", 18),
            margin=merged_config.get("margin", 24),
            include_qr=merged_config.get("include_qr", True),
            qr_position=merged_config.get("qr_position", "top_right"),
            qr_size=merged_config.get("qr_size", 100),
            text_color=merged_config.get("text_color", (255, 255, 255)),
        )

        return build_image_artifact_evidence(
            image_bytes=image_bytes,
            **common_params,
            watermark_spec=spec,
            include_perceptual_hashes=True,
        )

    def _watermark_pdf(
        self,
        pdf_bytes: bytes,
        common_params: Dict[str, Any],
        config: Optional[Dict[str, Any]],
    ) -> Tuple[ArtifactEvidence, bytes]:
        """Watermark PDF artifact."""
        from .pdf import build_pdf_artifact_evidence

        # Merge config with defaults
        default_pdf_config = _DEFAULT_CONFIG.get("pdf", {})
        merged_config = {**default_pdf_config, **(config or {})}

        # Additional metadata from config
        additional_metadata = merged_config.get("additional_metadata", {})

        return build_pdf_artifact_evidence(
            pdf_bytes=pdf_bytes,
            **common_params,
            additional_metadata=additional_metadata,
        )

    def _watermark_video(
        self,
        video_bytes: bytes,
        common_params: Dict[str, Any],
        config: Optional[Dict[str, Any]],
    ) -> Tuple[ArtifactEvidence, bytes]:
        """Watermark video artifact."""
        from .video import build_video_artifact_evidence

        # Merge config with defaults
        default_video_config = _DEFAULT_CONFIG.get("video", {})
        merged_config = {**default_video_config, **(config or {})}

        return build_video_artifact_evidence(
            video_bytes=video_bytes,
            **common_params,
            watermark_mode=merged_config.get("mode", "metadata"),
            watermark_config=merged_config,
            enable_forensic_fragments=merged_config.get(
                "enable_forensic_fragments", True
            ),
        )


# ============================================================================
# UNIFIED ENTRY POINT
# ============================================================================


def watermark_ai_output(
    artifact: Union[str, bytes],
    model_id: str,
    model_version: str,
    actor_id: str,
    prompt: str,
    verification_base_url: Optional[str] = None,
    artifact_type: Optional[ArtifactType] = None,
    watermark_config: Optional[Dict[str, Any]] = None,
    enable_forensic_fragments: bool = True,
    store_in_vault: bool = False,
) -> Tuple[ArtifactEvidence, Union[str, bytes]]:
    """
    Watermark any AI-generated artifact with automatic type detection.

    This is the UNIFIED INTERFACE for watermarking all artifact types at the
    point of inference. It automatically detects the artifact type and applies
    the appropriate watermarking strategy.

    Args:
        artifact: The raw AI output (text string or bytes)
        model_id: Model identifier (e.g., "gpt-4", "stable-diffusion-v3")
        model_version: Model version (e.g., "2026-03", "v1.5")
        actor_id: User/system that requested generation (e.g., "user:analyst-17")
        prompt: Input prompt (or hash of prompt for privacy)
        verification_base_url: Base URL for verification (uses default if None)
        artifact_type: Explicit type (None = auto-detect)
        watermark_config: Type-specific watermark configuration dict
        enable_forensic_fragments: Enable DNA sampling (default True)
        store_in_vault: Automatically store evidence in vault (default False)

    Returns:
        Tuple of (evidence, watermarked_artifact):
            - evidence: Complete ArtifactEvidence record with dual-state hashing
            - watermarked_artifact: Artifact with watermark applied (same type as input)

    Raises:
        TypeError: If artifact is neither str nor bytes
        NotImplementedError: For unsupported artifact types (audio, video, JSON)
        ValueError: If artifact_type is invalid

    Examples:
        # Text watermarking
        >>> evidence, watermarked = watermark_ai_output(
        ...     artifact="AI generated content...",
        ...     model_id="gpt-4",
        ...     model_version="2026-03",
        ...     actor_id="user:analyst-17",
        ...     prompt="Summarize the quarterly report",
        ...     verification_base_url="https://vault.example.com"
        ... )
        >>> print(watermarked)
        'AI generated content...\\n\\n---\\nAI Provenance Tag: wmk-...'

        # Image watermarking (auto-detected)
        >>> with open("generated_image.png", "rb") as f:
        ...     image_bytes = f.read()
        >>> evidence, watermarked = watermark_ai_output(
        ...     artifact=image_bytes,
        ...     model_id="stable-diffusion-v3",
        ...     model_version="2026-03",
        ...     actor_id="user:artist-42",
        ...     prompt="Generate landscape painting",
        ...     verification_base_url="https://vault.example.com",
        ...     watermark_config={"opacity": 0.5, "include_qr": True}
        ... )

        # PDF watermarking with vault storage
        >>> with open("report.pdf", "rb") as f:
        ...     pdf_bytes = f.read()
        >>> evidence, watermarked = watermark_ai_output(
        ...     artifact=pdf_bytes,
        ...     model_id="gpt-report-gen",
        ...     model_version="2.0",
        ...     actor_id="system:report-bot",
        ...     prompt="Generate compliance report",
        ...     store_in_vault=True  # Auto-store evidence
        ... )

        # Using global defaults
        >>> set_default_watermark_config({
        ...     "verification_base_url": "https://vault.mycompany.com",
        ...     "store_in_vault": True
        ... })
        >>> evidence, watermarked = watermark_ai_output(
        ...     artifact=ai_output,
        ...     model_id="gpt-4",
        ...     model_version="2026-03",
        ...     actor_id="user:123",
        ...     prompt="Generate"
        ... )  # Uses default URL and auto-stores
    """
    # Use default verification URL if not provided
    if verification_base_url is None:
        verification_base_url = _DEFAULT_CONFIG["verification_base_url"]

    # Step 1: Detect artifact type if not specified
    if artifact_type is None:
        artifact_type = detect_artifact_type(artifact)

    # Step 2: Create dispatcher and dispatch to appropriate watermarker
    dispatcher = WatermarkDispatcher()
    evidence, watermarked = dispatcher.dispatch(
        artifact=artifact,
        artifact_type=artifact_type,
        model_id=model_id,
        model_version=model_version,
        actor_id=actor_id,
        prompt=prompt,
        verification_base_url=verification_base_url,
        watermark_config=watermark_config,
        enable_forensic_fragments=enable_forensic_fragments,
    )

    # Step 3: Optional vault storage
    if store_in_vault:
        from .vault_adapter import create_watermark_vault

        vault = create_watermark_vault()
        vault.store_evidence(evidence)

    return evidence, watermarked


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def quick_watermark(
    artifact: Union[str, bytes],
    model_id: str,
) -> Tuple[Union[str, bytes], str]:
    """
    Quick watermarking with minimal configuration.

    Simplified interface for rapid watermarking with sensible defaults.
    Returns only the watermarked artifact and artifact ID.

    Args:
        artifact: Raw AI output (text or bytes)
        model_id: Model identifier

    Returns:
        Tuple of (watermarked_artifact, artifact_id)

    Example:
        >>> watermarked, artifact_id = quick_watermark(
        ...     artifact="AI content",
        ...     model_id="gpt-4"
        ... )
    """
    evidence, watermarked = watermark_ai_output(
        artifact=artifact,
        model_id=model_id,
        model_version="unknown",
        actor_id="system",
        prompt="",
        verification_base_url=_DEFAULT_CONFIG["verification_base_url"],
    )

    return watermarked, evidence.artifact_id


__all__ = [
    "detect_artifact_type",
    "watermark_ai_output",
    "quick_watermark",
    "WatermarkDispatcher",
    "set_default_watermark_config",
    "get_default_watermark_config",
]
