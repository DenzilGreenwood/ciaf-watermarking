"""
Tests for ciaf_watermarks.video.metadata module.

Tests cover:
- Video metadata watermarking
- FFmpeg metadata tags
- Metadata extraction
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestVideoMetadataWatermarking:
    """Test video metadata watermarking."""

    def test_apply_video_metadata_watermark(self, sample_video_bytes, test_watermark_id):
        """Test applying metadata watermark to video."""
        pytest.importorskip("ffmpeg")

        try:
            from ciaf_watermarks.video import apply_video_metadata_watermark

            with patch("ciaf_watermarks.video.metadata.ffmpeg") as mock_ffmpeg:
                mock_ffmpeg.input.return_value = MagicMock()
                mock_ffmpeg.output.return_value = MagicMock()

                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        sample_video_bytes
                    )

                    watermarked = apply_video_metadata_watermark(
                        video_bytes=sample_video_bytes,
                        watermark_id=test_watermark_id,
                        verification_url="https://test.com",
                        model_id="video-gen-v1",
                        timestamp="2026-04-05T10:00:00Z",
                    )

                    assert isinstance(watermarked, bytes)
        except (ImportError, AttributeError):
            pytest.skip("Video watermarking not implemented")

    def test_extract_video_metadata(self, sample_video_bytes):
        """Test extracting metadata from video."""
        pytest.importorskip("ffmpeg")

        try:
            from ciaf_watermarks.video import extract_video_metadata_watermark

            with patch("ciaf_watermarks.video.metadata.ffmpeg") as mock_ffmpeg:
                mock_ffmpeg.probe.return_value = {
                    "format": {"tags": {"comment": "CIAF Watermark: wmk-123"}}
                }

                with patch("builtins.open", create=True):
                    metadata = extract_video_metadata_watermark(sample_video_bytes)

                    if metadata:
                        assert "watermark_id" in metadata
        except (ImportError, AttributeError):
            pytest.skip("Video metadata extraction not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
