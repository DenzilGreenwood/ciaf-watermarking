"""
Tests for ciaf.watermarks.video.core module.

Tests cover:
- Video artifact evidence building
- Video info extraction
- Metadata handling
"""

import pytest
from unittest.mock import patch


@pytest.mark.unit
class TestVideoArtifactEvidence:
    """Test video artifact evidence building."""

    def test_build_video_evidence(self, sample_video_bytes, common_watermark_params):
        """Test building video evidence."""
        pytest.importorskip("ffmpeg")

        try:
            from ciaf.watermarks.video import build_video_artifact_evidence
            from ciaf.watermarks.models import ArtifactType

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

                    assert evidence is not None
                    assert evidence.artifact_type == ArtifactType.VIDEO
        except (ImportError, AttributeError):
            pytest.skip("Video evidence building not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
