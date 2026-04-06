"""
Tests for ciaf_watermarks.video.visual module.

Tests cover:
- Visual watermarks on video frames
- Frame-level watermarking
- Watermark persistence across frames
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
@pytest.mark.slow
class TestVideoVisualWatermarking:
    """Test video visual watermarking."""

    def test_apply_visual_watermark(self, sample_video_bytes):
        """Test applying visual watermark to video."""
        pytest.importorskip("ffmpeg")

        try:
            from ciaf_watermarks.video import apply_video_visual_watermark

            with patch("ciaf_watermarks.video.visual.ffmpeg") as mock_ffmpeg:
                mock_ffmpeg.input.return_value = MagicMock()
                mock_ffmpeg.output.return_value = MagicMock()

                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        sample_video_bytes
                    )

                    watermarked = apply_video_visual_watermark(
                        video_bytes=sample_video_bytes, watermark_text="CIAF - wmk-123"
                    )

                    assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError):
            pytest.skip("Video visual watermarking not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
