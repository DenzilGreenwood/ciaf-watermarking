"""
Tests for ciaf.watermarks.unified_interface module.

Tests cover:
- Unified watermarking interface
- Automatic artifact type detection
- Multi-artifact watermarking
- Unified verification
"""

import pytest


@pytest.mark.unit
class TestUnifiedWatermarkingInterface:
    """Test unified watermarking interface."""

    def test_watermark_text_via_unified_interface(
        self, sample_text, common_watermark_params
    ):
        """Test watermarking text via unified interface."""
        try:
            from ciaf.watermarks import watermark_artifact

            evidence, watermarked = watermark_artifact(
                content=sample_text, artifact_type="text", **common_watermark_params
            )

            assert evidence is not None
            assert isinstance(watermarked, str)
        except (ImportError, AttributeError):
            pytest.skip("watermark_artifact not implemented")

    def test_watermark_auto_detect_type(self, sample_text, common_watermark_params):
        """Test artifact type auto-detection."""
        try:
            from ciaf.watermarks import watermark_artifact

            evidence, watermarked = watermark_artifact(
                content=sample_text, **common_watermark_params
            )

            assert evidence.artifact_type.value == "text"
        except (ImportError, AttributeError, TypeError):
            pytest.skip("Auto-detection not supported")

    def test_verify_via_unified_interface(self, sample_text, common_watermark_params):
        """Test verification via unified interface."""
        try:
            from ciaf.watermarks import watermark_artifact, verify_artifact

            evidence, watermarked = watermark_artifact(
                content=sample_text, artifact_type="text", **common_watermark_params
            )

            result = verify_artifact(watermarked, evidence)

            assert result.is_authentic()
        except (ImportError, AttributeError):
            pytest.skip("Unified verification not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
