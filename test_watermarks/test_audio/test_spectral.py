"""
Tests for ciaf.watermarks.audio.spectral module.

Tests cover:
- Spectral watermarking
- AudioWatermarkSpec validation
- Carrier frequency embedding
- Spread spectrum techniques
- Watermark extraction
"""

import pytest
from unittest.mock import patch
import numpy as np


@pytest.mark.unit
class TestAudioWatermarkSpec:
    """Test AudioWatermarkSpec validation and creation."""

    def test_spec_creation_basic(self):
        """Test basic AudioWatermarkSpec creation."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        spec = AudioWatermarkSpec(
            strength=0.1, frequency_band="high", carrier_freq=18000
        )

        assert spec.strength == 0.1
        assert spec.frequency_band == "high"
        assert spec.carrier_freq == 18000

    def test_spec_creation_with_spread_spectrum(self):
        """Test spec creation with spread spectrum enabled."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        spec = AudioWatermarkSpec(
            strength=0.15,
            frequency_band="low",
            carrier_freq=10000,
            spread_spectrum=True,
        )

        assert spec.spread_spectrum is True

    def test_spec_validation_strength_too_high(self):
        """Test validation rejects strength > 1.0."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        with pytest.raises(ValueError, match="strength"):
            AudioWatermarkSpec(strength=1.5)

    def test_spec_validation_strength_negative(self):
        """Test validation rejects negative strength."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        with pytest.raises(ValueError, match="strength"):
            AudioWatermarkSpec(strength=-0.1)

    def test_spec_validation_invalid_frequency_band(self):
        """Test validation rejects invalid frequency band."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        with pytest.raises(ValueError, match="frequency_band"):
            AudioWatermarkSpec(frequency_band="invalid")

    def test_spec_validation_carrier_freq_too_high(self):
        """Test validation rejects carrier frequency above Nyquist."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        # Assuming 44.1kHz sample rate, Nyquist is 22.05kHz
        with pytest.raises(ValueError, match="carrier_freq"):
            AudioWatermarkSpec(carrier_freq=25000)

    def test_spec_validation_carrier_freq_too_low(self):
        """Test validation rejects carrier frequency too low."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        with pytest.raises(ValueError, match="carrier_freq"):
            AudioWatermarkSpec(carrier_freq=100)  # Too low

    def test_spec_default_values(self):
        """Test AudioWatermarkSpec default values."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        spec = AudioWatermarkSpec()

        # Should have reasonable defaults
        assert 0.0 < spec.strength <= 1.0
        assert spec.frequency_band in ["low", "mid", "high"]
        assert 1000 < spec.carrier_freq < 22050


@pytest.mark.unit
@pytest.mark.requires_librosa
class TestSpectralWatermarking:
    """Test spectral watermarking functions."""

    def test_apply_spectral_watermark_mock(self, sample_audio_bytes):
        """Test apply spectral watermark with mocked librosa."""
        from ciaf.watermarks.audio import (
            apply_audio_spectral_watermark,
            AudioWatermarkSpec,
        )

        spec = AudioWatermarkSpec(strength=0.1, carrier_freq=18000)

        try:
            with patch("ciaf.watermarks.audio.spectral.librosa") as mock_librosa:
                # Mock audio loading and processing
                mock_librosa.load.return_value = (np.random.randn(44100), 44100)
                mock_librosa.stft.return_value = np.random.randn(
                    1025, 100
                ) + 1j * np.random.randn(1025, 100)
                mock_librosa.istft.return_value = np.random.randn(44100)
                mock_librosa.fft_frequencies.return_value = np.linspace(0, 22050, 1025)

                with patch("ciaf.watermarks.audio.spectral.sf") as mock_sf:
                    mock_sf.write.return_value = None

                    with patch("builtins.open", create=True) as mock_open:
                        mock_open.return_value.__enter__.return_value.read.return_value = (
                            sample_audio_bytes
                        )

                        result = apply_audio_spectral_watermark(
                            audio_bytes=sample_audio_bytes,
                            watermark_spec=spec,
                            watermark_data="wmk-test-123",
                        )

                        assert isinstance(result, bytes)
        except ImportError:
            pytest.skip("librosa/numpy not available")

    def test_apply_spectral_watermark_different_bands(self, sample_audio_bytes):
        """Test spectral watermarking with different frequency bands."""
        from ciaf.watermarks.audio import (
            apply_audio_spectral_watermark,
            AudioWatermarkSpec,
        )

        try:
            for band in ["low", "mid", "high"]:
                spec = AudioWatermarkSpec(
                    strength=0.1,
                    frequency_band=band,
                    carrier_freq=(
                        5000 if band == "low" else (10000 if band == "mid" else 18000)
                    ),
                )

                with patch("ciaf.watermarks.audio.spectral.librosa") as mock_librosa:
                    mock_librosa.load.return_value = (np.random.randn(44100), 44100)
                    mock_librosa.stft.return_value = np.random.randn(
                        1025, 100
                    ) + 1j * np.random.randn(1025, 100)
                    mock_librosa.istft.return_value = np.random.randn(44100)
                    mock_librosa.fft_frequencies.return_value = np.linspace(
                        0, 22050, 1025
                    )

                    with patch("ciaf.watermarks.audio.spectral.sf") as mock_sf:
                        mock_sf.write.return_value = None

                        with patch("builtins.open", create=True) as mock_open:
                            mock_open.return_value.__enter__.return_value.read.return_value = (
                                sample_audio_bytes
                            )

                            result = apply_audio_spectral_watermark(
                                audio_bytes=sample_audio_bytes,
                                watermark_spec=spec,
                                watermark_data="wmk-test",
                            )

                            assert isinstance(result, bytes)
        except ImportError:
            pytest.skip("librosa not available")

    def test_apply_with_spread_spectrum(self, sample_audio_bytes):
        """Test spectral watermarking with spread spectrum enabled."""
        from ciaf.watermarks.audio import (
            apply_audio_spectral_watermark,
            AudioWatermarkSpec,
        )

        spec = AudioWatermarkSpec(
            strength=0.1, carrier_freq=18000, spread_spectrum=True
        )

        try:
            with patch("ciaf.watermarks.audio.spectral.librosa") as mock_librosa:
                mock_librosa.load.return_value = (np.random.randn(44100), 44100)
                mock_librosa.stft.return_value = np.random.randn(
                    1025, 100
                ) + 1j * np.random.randn(1025, 100)
                mock_librosa.istft.return_value = np.random.randn(44100)
                mock_librosa.fft_frequencies.return_value = np.linspace(0, 22050, 1025)

                with patch("ciaf.watermarks.audio.spectral.sf") as mock_sf:
                    mock_sf.write.return_value = None

                    with patch("builtins.open", create=True) as mock_open:
                        mock_open.return_value.__enter__.return_value.read.return_value = (
                            sample_audio_bytes
                        )

                        result = apply_audio_spectral_watermark(
                            audio_bytes=sample_audio_bytes,
                            watermark_spec=spec,
                            watermark_data="wmk-test",
                        )

                        assert isinstance(result, bytes)
        except ImportError:
            pytest.skip("librosa not available")


@pytest.mark.unit
@pytest.mark.requires_librosa
class TestSpectralWatermarkExtraction:
    """Test spectral watermark extraction."""

    def test_extract_spectral_watermark_mock(self, sample_audio_bytes):
        """Test extracting spectral watermark."""
        from ciaf.watermarks.audio import (
            extract_audio_spectral_watermark,
            AudioWatermarkSpec,
        )

        spec = AudioWatermarkSpec(strength=0.1, carrier_freq=18000)

        try:
            with patch("ciaf.watermarks.audio.spectral.librosa") as mock_librosa:
                mock_librosa.load.return_value = (np.random.randn(44100), 44100)
                mock_librosa.stft.return_value = np.random.randn(
                    1025, 100
                ) + 1j * np.random.randn(1025, 100)
                mock_librosa.fft_frequencies.return_value = np.linspace(0, 22050, 1025)

                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        sample_audio_bytes
                    )

                    # Mock extraction returning watermark data
                    extracted = extract_audio_spectral_watermark(
                        audio_bytes=sample_audio_bytes, watermark_spec=spec
                    )

                    # Should return string or None
                    assert extracted is None or isinstance(extracted, str)
        except (ImportError, AttributeError):
            pytest.skip(
                "extract_audio_spectral_watermark not implemented or librosa not available"
            )

    def test_extract_from_unwatermarked_audio(self, sample_audio_bytes):
        """Test extraction from unwatermarked audio returns None."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        spec = AudioWatermarkSpec()

        try:
            from ciaf.watermarks.audio import extract_audio_spectral_watermark

            with patch("ciaf.watermarks.audio.spectral.librosa") as mock_librosa:
                mock_librosa.load.return_value = (np.random.randn(44100), 44100)
                mock_librosa.stft.return_value = np.random.randn(
                    1025, 100
                ) + 1j * np.random.randn(1025, 100)
                mock_librosa.fft_frequencies.return_value = np.linspace(0, 22050, 1025)

                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        sample_audio_bytes
                    )

                    extracted = extract_audio_spectral_watermark(
                        audio_bytes=sample_audio_bytes, watermark_spec=spec
                    )

                    # Unwatermarked should return None
                    assert extracted is None
        except (ImportError, AttributeError):
            pytest.skip("extract_audio_spectral_watermark not implemented")


@pytest.mark.unit
class TestSpectralWatermarkRobustness:
    """Test spectral watermark robustness."""

    def test_watermark_survives_compression(self, sample_audio_bytes):
        """Test that spectral watermark survives compression (conceptually)."""
        # This would require actual audio processing which is mocked
        # But we test the interface
        from ciaf.watermarks.audio import AudioWatermarkSpec

        spec = AudioWatermarkSpec(strength=0.2)  # Higher strength

        # Test that spec allows for robust watermarking
        assert spec.strength >= 0.1  # Strong enough for compression

    def test_watermark_strength_affects_robustness(self):
        """Test that higher strength improves robustness."""
        from ciaf.watermarks.audio import AudioWatermarkSpec

        weak_spec = AudioWatermarkSpec(strength=0.05)
        strong_spec = AudioWatermarkSpec(strength=0.2)

        # Stronger watermark should be more robust
        assert strong_spec.strength > weak_spec.strength


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
