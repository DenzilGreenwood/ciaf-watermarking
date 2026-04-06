"""
Tests for ciaf_watermarks.audio module.

Tests cover:
- Audio metadata watermarking
- Audio spectral watermarking
- Audio verification
- Multi-tier verification
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestAudioMetadataWatermarking:
    """Test audio metadata watermarking."""

    def test_apply_metadata_watermark_mock(self, sample_audio_bytes, test_watermark_id):
        """Test metadata watermarking with mocked ffmpeg."""
        from ciaf_watermarks.audio import apply_audio_metadata_watermark

        # Skip if ffmpeg not available
        pytest.importorskip("ffmpeg")

        with patch("ciaf_watermarks.audio.metadata.ffmpeg") as mock_ffmpeg:
            # Mock ffmpeg operations
            mock_ffmpeg.input.return_value = MagicMock()
            mock_ffmpeg.output.return_value = MagicMock()
            mock_ffmpeg.run.return_value = None

            # Mock file operations
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = sample_audio_bytes

                try:
                    result = apply_audio_metadata_watermark(
                        audio_bytes=sample_audio_bytes,
                        watermark_id=test_watermark_id,
                        verification_url="https://test.com",
                        model_id="voice-clone-v1",
                        timestamp="2026-04-05T10:00:00Z",
                    )

                    assert isinstance(result, bytes)
                except ImportError:
                    pytest.skip("ffmpeg-python not available")

    def test_extract_metadata_watermark_mock(self, sample_audio_bytes):
        """Test extracting metadata watermark."""
        from ciaf_watermarks.audio import extract_audio_metadata_watermark

        pytest.importorskip("ffmpeg")

        with patch("ciaf_watermarks.audio.metadata.ffmpeg") as mock_ffmpeg:
            # Mock probe result
            mock_ffmpeg.probe.return_value = {
                "format": {
                    "tags": {
                        "comment": "CIAF Watermark: wmk-audio-test-123",
                        "title": "AI Generated Audio - voice-clone-v1",
                        "copyright": "Verification: https://test.com",
                    }
                }
            }

            with patch("builtins.open", create=True):
                try:
                    metadata = extract_audio_metadata_watermark(sample_audio_bytes)

                    if metadata:
                        assert metadata["watermark_id"] == "wmk-audio-test-123"
                except ImportError:
                    pytest.skip("ffmpeg-python not available")

    def test_has_audio_watermark(self, sample_audio_bytes):
        """Test checking if audio has watermark."""
        from ciaf_watermarks.audio import has_audio_watermark

        pytest.importorskip("ffmpeg")

        with patch(
            "ciaf_watermarks.audio.metadata.extract_audio_metadata_watermark"
        ) as mock_extract:
            mock_extract.return_value = {"watermark_id": "wmk-123"}

            assert has_audio_watermark(sample_audio_bytes) is True

            mock_extract.return_value = None
            assert has_audio_watermark(sample_audio_bytes) is False


@pytest.mark.unit
class TestAudioSpectralWatermarking:
    """Test audio spectral watermarking."""

    def test_audio_watermark_spec(self):
        """Test AudioWatermarkSpec creation."""
        from ciaf_watermarks.audio import AudioWatermarkSpec

        spec = AudioWatermarkSpec(
            strength=0.1,
            frequency_band="high",
            carrier_freq=18000,
            spread_spectrum=True,
        )

        assert spec.strength == 0.1
        assert spec.carrier_freq == 18000

    def test_audio_watermark_spec_validation(self):
        """Test AudioWatermarkSpec validation."""
        from ciaf_watermarks.audio import AudioWatermarkSpec

        # Invalid strength
        with pytest.raises(ValueError):
            AudioWatermarkSpec(strength=1.5)

        # Invalid frequency band
        with pytest.raises(ValueError):
            AudioWatermarkSpec(frequency_band="invalid")

        # Invalid carrier frequency
        with pytest.raises(ValueError):
            AudioWatermarkSpec(carrier_freq=25000)

    @pytest.mark.requires_librosa
    def test_apply_spectral_watermark_mock(self, sample_audio_bytes):
        """Test spectral watermarking with mocked librosa."""
        from ciaf_watermarks.audio import (
            apply_audio_spectral_watermark,
            AudioWatermarkSpec,
        )

        try:
            import numpy as np

            spec = AudioWatermarkSpec(strength=0.1, carrier_freq=18000)

            with patch("ciaf_watermarks.audio.spectral.librosa") as mock_librosa:
                # Mock audio loading
                mock_librosa.load.return_value = (np.random.randn(44100), 44100)
                mock_librosa.stft.return_value = np.random.randn(1025, 100) + 1j * np.random.randn(
                    1025, 100
                )
                mock_librosa.istft.return_value = np.random.randn(44100)
                mock_librosa.fft_frequencies.return_value = np.linspace(0, 22050, 1025)

                with patch("ciaf_watermarks.audio.spectral.sf") as mock_sf:
                    mock_sf.write.return_value = None

                    with patch("builtins.open", create=True) as mock_open:
                        mock_open.return_value.__enter__.return_value.read.return_value = (
                            sample_audio_bytes
                        )

                        result = apply_audio_spectral_watermark(
                            audio_bytes=sample_audio_bytes,
                            watermark_spec=spec,
                            watermark_data="wmk-spectral-test",
                        )

                        assert isinstance(result, bytes)
        except ImportError:
            pytest.skip("librosa/numpy not available")


@pytest.mark.unit
class TestAudioEvidenceBuilding:
    """Test audio evidence building."""

    def test_build_audio_evidence_metadata_mode(self, sample_audio_bytes, common_watermark_params):
        """Test building audio evidence with metadata mode."""
        from ciaf_watermarks.audio import build_audio_artifact_evidence
        from ciaf_watermarks.models import ArtifactType, WatermarkType

        pytest.importorskip("ffmpeg")

        with patch("ciaf_watermarks.audio.core.apply_audio_metadata_watermark") as mock_apply:
            mock_apply.return_value = sample_audio_bytes + b"watermark"

            with patch("ciaf_watermarks.audio.core.get_audio_info") as mock_info:
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

                assert evidence.artifact_type == ArtifactType.AUDIO
                assert evidence.watermark.watermark_type == WatermarkType.METADATA
                assert evidence.metadata["watermark_mode"] == "metadata"
                assert isinstance(watermarked, bytes)


@pytest.mark.unit
class TestAudioVerification:
    """Test audio verification."""

    def test_verify_exact_match(self, sample_audio_bytes, common_watermark_params):
        """Test verification with exact hash match."""
        from ciaf_watermarks.audio import (
            build_audio_artifact_evidence,
            verify_audio_artifact,
        )

        with patch("ciaf_watermarks.audio.core.apply_audio_metadata_watermark") as mock_apply:
            mock_apply.return_value = sample_audio_bytes + b"watermark"

            with patch("ciaf_watermarks.audio.core.get_audio_info") as mock_info:
                mock_info.return_value = {
                    "duration": 5.0,
                    "size_bytes": len(sample_audio_bytes),
                    "codec": "mp3",
                    "sample_rate": 44100,
                    "channels": 2,
                    "bitrate": 128000,
                    "format": "mp3",
                }

                evidence, watermarked = build_audio_artifact_evidence(
                    audio_bytes=sample_audio_bytes,
                    **common_watermark_params,
                    watermark_mode="metadata",
                )

                # Verify exact match
                result = verify_audio_artifact(watermarked, evidence)

                assert result.is_authentic()
                assert result.confidence == 1.0
                assert result.exact_match_after_watermark is True

    def test_verify_watermark_removed(self, sample_audio_bytes, common_watermark_params):
        """Test verification detects watermark removal."""
        from ciaf_watermarks.audio import (
            build_audio_artifact_evidence,
            verify_audio_artifact,
        )

        with patch("ciaf_watermarks.audio.core.apply_audio_metadata_watermark") as mock_apply:
            mock_apply.return_value = sample_audio_bytes + b"watermark"

            with patch("ciaf_watermarks.audio.core.get_audio_info") as mock_info:
                mock_info.return_value = {
                    "duration": 5.0,
                    "size_bytes": len(sample_audio_bytes),
                    "codec": "mp3",
                    "sample_rate": 44100,
                    "channels": 2,
                    "bitrate": 128000,
                    "format": "mp3",
                }

                evidence, watermarked = build_audio_artifact_evidence(
                    audio_bytes=sample_audio_bytes,
                    **common_watermark_params,
                    watermark_mode="metadata",
                )

                # Verify original (watermark removed)
                result = verify_audio_artifact(sample_audio_bytes, evidence)

                assert result.likely_tag_removed is True
                assert result.confidence == 0.99


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
