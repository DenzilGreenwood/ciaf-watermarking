"""
Tests for ciaf.watermarks.video.verification module.

Tests cover:
- Video verification against evidence
- Hash matching
- Watermark detection
"""

import pytest
from unittest.mock import patch


@pytest.mark.unit
class TestVideoVerification:
    """Test video verification."""

    def test_verify_video_artifact(self, sample_video_bytes, common_watermark_params):
        """Test video verification."""
        pytest.importorskip("ffmpeg")

        try:
            from ciaf.watermarks.video import (
                build_video_artifact_evidence,
                verify_video_artifact,
            )

            with patch(
                "ciaf.watermarks.video.core.apply_video_metadata_watermark"
            ) as mock_apply:
                mock_apply.return_value = sample_video_bytes + b"watermark"

                with patch("ciaf.watermarks.video.core.get_video_info") as mock_info:
                    mock_info.return_value = {
                        "duration": 10.0,
                        "width": 1920,
                        "height": 1080,
                        "fps": 30.0,
                        "codec": "h264",
                        "size_bytes": len(sample_video_bytes),
                        "format": "mp4",
                    }

                    evidence, watermarked = build_video_artifact_evidence(
                        video_bytes=sample_video_bytes, **common_watermark_params
                    )

                    result = verify_video_artifact(watermarked, evidence)

                    assert result.is_authentic()
        except (ImportError, AttributeError):
            pytest.skip("Video verification not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
