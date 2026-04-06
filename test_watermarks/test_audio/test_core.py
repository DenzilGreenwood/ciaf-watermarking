"""
Tests for ciaf.watermarks.audio.core module.

Tests cover:
- Audio artifact evidence building
- Audio info extraction
- Metadata handling
- Watermark mode selection
"""

import pytest
from unittest.mock import patch


@pytest.mark.unit
class TestAudioArtifactEvidenceBuilding:
    """Test audio artifact evidence building."""

    def test_build_evidence_metadata_mode(
        self, sample_audio_bytes, common_watermark_params
    ):
        """Test building audio evidence with metadata mode."""
        from ciaf.watermarks.audio import build_audio_artifact_evidence
        from ciaf.watermarks.models import ArtifactType, WatermarkType

        with patch(
            "ciaf.watermarks.audio.core.apply_audio_metadata_watermark"
        ) as mock_apply:
            mock_apply.return_value = sample_audio_bytes + b"watermark"

            with patch("ciaf.watermarks.audio.core.get_audio_info") as mock_info:
                mock_info.return_value = {
                    "duration": 5.0,
                    "sample_rate": 44100,
                    "channels": 2,
                    "codec": "mp3",
                    "bitrate": 128000,
                    "size_bytes": len(sample_audio_bytes),
                    "format": "mp3",
                }

                evidence, watermarked = build_audio_artifact_evidence(
                    audio_bytes=sample_audio_bytes,
                    **common_watermark_params,
                    watermark_mode="metadata",
                )

                assert evidence is not None
                assert evidence.artifact_type == ArtifactType.AUDIO
                assert evidence.watermark.watermark_type == WatermarkType.METADATA
                assert evidence.metadata["watermark_mode"] == "metadata"
                assert isinstance(watermarked, bytes)

    def test_build_evidence_spectral_mode(
        self, sample_audio_bytes, common_watermark_params
    ):
        """Test building audio evidence with spectral mode."""
        from ciaf.watermarks.audio import (
            build_audio_artifact_evidence,
            AudioWatermarkSpec,
        )
        from ciaf.watermarks.models import WatermarkType

        spec = AudioWatermarkSpec(strength=0.1)  # noqa: F841

        with patch(
            "ciaf.watermarks.audio.core.apply_audio_metadata_watermark"
        ) as mock_meta:
            mock_meta.return_value = sample_audio_bytes + b"meta"

            with patch(
                "ciaf.watermarks.audio.core.apply_audio_spectral_watermark"
            ) as mock_apply:
                mock_apply.return_value = sample_audio_bytes + b"spectral"

                with patch("ciaf.watermarks.audio.core.get_audio_info") as mock_info:
                    mock_info.return_value = {
                        "duration": 5.0,
                        "sample_rate": 44100,
                        "channels": 2,
                        "codec": "mp3",
                        "bitrate": 128000,
                        "size_bytes": len(sample_audio_bytes),
                        "format": "mp3",
                    }

                    evidence, watermarked = build_audio_artifact_evidence(
                        audio_bytes=sample_audio_bytes,
                        **common_watermark_params,
                        watermark_mode="spectral",
                    )

                assert evidence.watermark.watermark_type == WatermarkType.EMBEDDED
        """Test building audio evidence with dual (metadata + spectral) mode."""
        from ciaf.watermarks.audio import (
            build_audio_artifact_evidence,
            AudioWatermarkSpec,
        )

        _spec = AudioWatermarkSpec(strength=0.1)  # noqa: F841

        with patch(
            "ciaf.watermarks.audio.core.apply_audio_metadata_watermark"
        ) as mock_meta:
            mock_meta.return_value = sample_audio_bytes + b"meta"

            with patch(
                "ciaf.watermarks.audio.core.apply_audio_spectral_watermark"
            ) as mock_spec:
                mock_spec.return_value = sample_audio_bytes + b"spectral"

                with patch("ciaf.watermarks.audio.core.get_audio_info") as mock_info:
                    mock_info.return_value = {
                        "duration": 5.0,
                        "sample_rate": 44100,
                        "channels": 2,
                        "codec": "mp3",
                        "bitrate": 128000,
                        "size_bytes": len(sample_audio_bytes),
                        "format": "mp3",
                    }

                    evidence, watermarked = build_audio_artifact_evidence(
                        audio_bytes=sample_audio_bytes,
                        **common_watermark_params,
                        watermark_mode="dual",
                    )

                    assert evidence.metadata["watermark_mode"] == "dual"


@pytest.mark.unit
class TestAudioInfoExtraction:
    """Test audio info extraction."""

    def test_get_audio_info_mock(self, sample_audio_bytes):
        """Test getting audio info with mocked ffmpeg."""
        from ciaf.watermarks.audio import get_audio_info

        pytest.importorskip("ffmpeg")

        with patch("ciaf.watermarks.audio.metadata.ffmpeg") as mock_ffmpeg:
            mock_ffmpeg.probe.return_value = {
                "format": {
                    "format_name": "mp3",
                    "duration": "5.0",
                    "size": str(len(sample_audio_bytes)),
                    "bit_rate": "128000",
                },
                "streams": [
                    {
                        "codec_type": "audio",
                        "codec_name": "mp3",
                        "sample_rate": "44100",
                        "channels": 2,
                    }
                ],
            }

            with patch("builtins.open", create=True):
                info = get_audio_info(sample_audio_bytes)

                assert info["format"] == "mp3"
                assert info["duration"] == 5.0
                assert info["sample_rate"] == 44100
                assert info["channels"] == 2

    def test_get_audio_info_invalid_audio(self):
        """Test get audio info with invalid audio data."""
        from ciaf.watermarks.audio import get_audio_info

        invalid_bytes = b"not valid audio data"

        with patch("ciaf.watermarks.audio.metadata.ffmpeg") as mock_ffmpeg:
            mock_ffmpeg.probe.side_effect = Exception("Invalid audio")

            with patch("builtins.open", create=True):
                with pytest.raises(Exception):
                    get_audio_info(invalid_bytes)


@pytest.mark.unit
class TestAudioMetadataHandling:
    """Test audio metadata handling."""

    def test_evidence_contains_audio_metadata(
        self, sample_audio_bytes, common_watermark_params
    ):
        """Test that evidence contains audio-specific metadata."""
        from ciaf.watermarks.audio import build_audio_artifact_evidence

        with patch(
            "ciaf.watermarks.audio.core.apply_audio_metadata_watermark"
        ) as mock_apply:
            mock_apply.return_value = sample_audio_bytes

            with patch("ciaf.watermarks.audio.core.get_audio_info") as mock_info:
                mock_info.return_value = {
                    "duration": 10.5,
                    "sample_rate": 48000,
                    "channels": 2,
                    "codec": "aac",
                    "bitrate": 256000,
                    "size_bytes": len(sample_audio_bytes),
                    "format": "m4a",
                }

                evidence, watermarked = build_audio_artifact_evidence(
                    audio_bytes=sample_audio_bytes,
                    **common_watermark_params,
                    watermark_mode="metadata",
                )

                # Check audio metadata
                assert evidence.metadata["duration_seconds"] == 10.5
                assert evidence.metadata["sample_rate"] == 48000
                assert evidence.metadata["channels"] == 2
                assert evidence.metadata["codec"] == "aac"
                assert evidence.metadata["bitrate"] == 256000

    def test_evidence_with_additional_metadata(
        self, sample_audio_bytes, common_watermark_params
    ):
        """Test evidence with additional custom metadata."""
        from ciaf.watermarks.audio import build_audio_artifact_evidence

        additional = {
            "voice_model": "voice-clone-v2",
            "language": "en-US",
            "speaker_id": "speaker-123",
        }

        with patch(
            "ciaf.watermarks.audio.core.apply_audio_metadata_watermark"
        ) as mock_apply:
            mock_apply.return_value = sample_audio_bytes

            with patch("ciaf.watermarks.audio.core.get_audio_info") as mock_info:
                mock_info.return_value = {
                    "duration": 5.0,
                    "sample_rate": 44100,
                    "channels": 2,
                    "codec": "mp3",
                    "bitrate": 128000,
                    "size_bytes": len(sample_audio_bytes),
                    "format": "mp3",
                }

                evidence, watermarked = build_audio_artifact_evidence(
                    audio_bytes=sample_audio_bytes,
                    **common_watermark_params,
                    watermark_mode="metadata",
                    additional_metadata=additional,
                )

                assert evidence.metadata["voice_model"] == "voice-clone-v2"
                assert evidence.metadata["language"] == "en-US"
                assert evidence.metadata["speaker_id"] == "speaker-123"


@pytest.mark.unit
class TestAudioHashComputation:
    """Test audio hash computation."""

    def test_audio_hashes_computed(self, sample_audio_bytes, common_watermark_params):
        """Test that audio hashes are properly computed."""
        from ciaf.watermarks.audio import build_audio_artifact_evidence

        with patch(
            "ciaf.watermarks.audio.core.apply_audio_metadata_watermark"
        ) as mock_apply:
            mock_apply.return_value = sample_audio_bytes + b"watermark"

            with patch("ciaf.watermarks.audio.core.get_audio_info") as mock_info:
                mock_info.return_value = {
                    "duration": 5.0,
                    "sample_rate": 44100,
                    "channels": 2,
                    "codec": "mp3",
                    "bitrate": 128000,
                    "size_bytes": len(sample_audio_bytes),
                    "format": "mp3",
                }

                evidence, watermarked = build_audio_artifact_evidence(
                    audio_bytes=sample_audio_bytes,
                    **common_watermark_params,
                    watermark_mode="metadata",
                )

                # Check hashes
                assert evidence.hashes.content_hash_before_watermark is not None
                assert evidence.hashes.content_hash_after_watermark is not None
                assert len(evidence.hashes.content_hash_before_watermark) == 64
                assert (
                    evidence.hashes.content_hash_before_watermark
                    != evidence.hashes.content_hash_after_watermark
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
