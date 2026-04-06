"""
Tests for ciaf.watermarks.audio.verification module.

Tests cover:
- Audio verification against evidence
- Exact match detection
- Watermark removal detection
- Multi-tier verification
- Spectral watermark verification
"""

import pytest
from unittest.mock import patch


@pytest.mark.unit
class TestAudioVerificationExactMatch:
    """Test exact match audio verification."""

    def test_verify_exact_match(self, sample_audio_bytes, common_watermark_params):
        """Test verification with exact match."""
        from ciaf.watermarks.audio import (
            build_audio_artifact_evidence,
            verify_audio_artifact,
        )

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

                # Verify exact match
                result = verify_audio_artifact(watermarked, evidence)

                assert result.is_authentic()
                assert result.confidence == 1.0
                assert result.exact_match_after_watermark is True

    def test_verify_exact_match_original(
        self, sample_audio_bytes, common_watermark_params
    ):
        """Test verification matches original (pre-watermark)."""
        from ciaf.watermarks.audio import (
            build_audio_artifact_evidence,
            verify_audio_artifact,
        )

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

                # Verify original
                result = verify_audio_artifact(sample_audio_bytes, evidence)

                # Should detect watermark removal
                assert result.likely_tag_removed is True
                assert result.confidence == 0.99


@pytest.mark.unit
class TestAudioWatermarkRemovalDetection:
    """Test watermark removal detection."""

    def test_detect_metadata_removal(self, sample_audio_bytes, common_watermark_params):
        """Test detection of metadata watermark removal."""
        from ciaf.watermarks.audio import (
            build_audio_artifact_evidence,
            verify_audio_artifact,
        )

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

                # Verify original (watermark removed)
                result = verify_audio_artifact(sample_audio_bytes, evidence)

                assert result.likely_tag_removed is True


@pytest.mark.unit
class TestAudioVerificationNoMatch:
    """Test verification with no match."""

    def test_verify_completely_different_audio(
        self, sample_audio_bytes, common_watermark_params
    ):
        """Test verification with completely different audio."""
        from ciaf.watermarks.audio import (
            build_audio_artifact_evidence,
            verify_audio_artifact,
        )

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

                # Different audio
                different_audio = b"completely different audio data"

                result = verify_audio_artifact(different_audio, evidence)

                assert not result.is_authentic()
                assert result.confidence == 0.0


@pytest.mark.unit
class TestAudioVerificationMultiTier:
    """Test multi-tier audio verification."""

    def test_tier_exact_match(self, sample_audio_bytes, common_watermark_params):
        """Test 'exact' tier assignment."""
        from ciaf.watermarks.audio import (
            build_audio_artifact_evidence,
            verify_audio_artifact,
        )

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

                result = verify_audio_artifact(watermarked, evidence)

                assert result.exact_match_after_watermark is True
                assert result.confidence == 1.0


@pytest.mark.unit
@pytest.mark.requires_librosa
class TestAudioSpectralVerification:
    """Test spectral watermark verification."""

    def test_verify_spectral_watermark(
        self, sample_audio_bytes, common_watermark_params
    ):
        """Test verification of spectral watermark."""
        from ciaf.watermarks.audio import (
            build_audio_artifact_evidence,
            verify_audio_artifact,
            AudioWatermarkSpec,
        )

        spec = AudioWatermarkSpec(strength=0.1)

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
                        watermark_spec=spec,
                    )

                    # Mock spectral watermark extraction
                    with patch(
                        "ciaf.watermarks.audio.spectral.extract_audio_spectral_watermark"
                    ) as mock_extract:
                        mock_extract.return_value = evidence.watermark.watermark_id

                        result = verify_audio_artifact(
                            watermarked,
                            evidence,
                            enable_spectral_matching=True,
                        )

                        assert result.is_authentic()
                        assert result.confidence >= 0.9


@pytest.mark.unit
class TestAudioVerificationErrorHandling:
    """Test error handling in audio verification."""

    def test_verify_wrong_artifact_type(self, sample_audio_bytes):
        """Test verification raises error for wrong artifact type."""
        from ciaf.watermarks.audio import verify_audio_artifact
        from ciaf.watermarks.models import (
            ArtifactEvidence,
            ArtifactType,
            WatermarkDescriptor,
            ArtifactHashSet,
        )

        # Create evidence with wrong type
        from datetime import datetime, timezone

        evidence = ArtifactEvidence(
            artifact_id="test-id",
            artifact_type=ArtifactType.IMAGE,  # Wrong type!
            watermark=WatermarkDescriptor(
                watermark_id="wmk-test",
                watermark_type="metadata",
                verification_url="https://test.com",
            ),
            hashes=ArtifactHashSet(
                content_hash_before_watermark="abc123",
                content_hash_after_watermark="def456",
            ),
            model_id="test-model",
            model_version="1.0",
            actor_id="test-actor",
            prompt="test prompt",
            prompt_hash="hash123",
            output_hash_raw="raw456",
            output_hash_distributed="dist789",
            created_at=datetime.now(timezone.utc).isoformat(),
            generation_timestamp="2026-04-05T10:00:00Z",
            mime_type="audio/mpeg",
            metadata={},
        )

        with pytest.raises(ValueError, match="not for audio artifact"):
            verify_audio_artifact(sample_audio_bytes, evidence)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
