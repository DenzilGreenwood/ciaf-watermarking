"""
Shared fixtures and configuration for watermarking tests.

This module provides common fixtures, test data, and utilities
used across all watermarking tests.
"""

import pytest
import io
from typing import Dict, Any

# ============================================================================
# Test Data Generators
# ============================================================================


@pytest.fixture
def sample_text() -> str:
    """Generate sample text for testing."""
    return """
    Artificial Intelligence has revolutionized various industries,
    from healthcare to finance. Machine learning algorithms can now
    process vast amounts of data and make predictions with remarkable
    accuracy. This technology continues to evolve rapidly.
    """.strip()


@pytest.fixture
def sample_long_text() -> str:
    """Generate longer sample text for fragment testing."""
    text = []
    for i in range(10):
        text.append(f"Paragraph {i + 1}: " + "Lorem ipsum dolor sit amet. " * 20)
    return "\n\n".join(text)


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate sample PNG image bytes."""
    try:
        from PIL import Image
        import numpy as np

        # Create 256x256 RGB image
        img_array = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)

        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        return img_bytes.getvalue()
    except ImportError:
        # Return minimal valid PNG if PIL not available
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate minimal valid PDF bytes."""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] >>
endobj
4 0 obj
<< >>
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
235
%%EOF
"""


@pytest.fixture
def sample_audio_bytes() -> bytes:
    """Generate minimal valid MP3 bytes (header only)."""
    # MP3 header
    return b"\xff\xfb\x90\x00" + b"\x00" * 1000


@pytest.fixture
def sample_video_bytes() -> bytes:
    """Generate minimal valid MP4 bytes (header only)."""
    # MP4 header (ftyp box)
    return (
        b"\x00\x00\x00\x20\x66\x74\x79\x70"  # ftyp
        b"\x69\x73\x6f\x6d\x00\x00\x02\x00"  # isom
        b"\x69\x73\x6f\x6d\x69\x73\x6f\x32"
        b"\x61\x76\x63\x31\x6d\x70\x34\x31" + b"\x00" * 1000
    )


@pytest.fixture
def sample_binary_bytes() -> bytes:
    """Generate ELF executable header."""
    return b"\x7fELF" + b"\x00" * 1000


# ============================================================================
# Common Parameters
# ============================================================================


@pytest.fixture
def common_watermark_params() -> Dict[str, Any]:
    """Common parameters for watermarking operations."""
    return {
        "model_id": "test-model-v1",
        "model_version": "2026-03",
        "actor_id": "user:test-123",
        "prompt": "Test generation prompt",
        "verification_base_url": "https://vault.test.com",
    }


@pytest.fixture
def test_watermark_id() -> str:
    """Fixed watermark ID for testing."""
    return "wmk-test-123abc"


@pytest.fixture
def test_verification_url() -> str:
    """Fixed verification URL for testing."""
    return "https://vault.test.com/verify/wmk-test-123abc"


# ============================================================================
# Mock External Dependencies
# ============================================================================


@pytest.fixture
def mock_ffmpeg(monkeypatch):
    """Mock ffmpeg-python for tests that don't need real ffmpeg."""
    import pytest

    pytest.importorskip("unittest.mock")

    from unittest.mock import MagicMock

    mock_ffmpeg_module = MagicMock()
    monkeypatch.setattr("ffmpeg.input", mock_ffmpeg_module.input)
    monkeypatch.setattr("ffmpeg.output", mock_ffmpeg_module.output)
    monkeypatch.setattr("ffmpeg.run", mock_ffmpeg_module.run)

    return mock_ffmpeg_module


@pytest.fixture
def mock_librosa(monkeypatch):
    """Mock librosa for audio tests."""
    import pytest

    pytest.importorskip("unittest.mock")

    from unittest.mock import MagicMock
    import numpy as np

    mock_librosa_module = MagicMock()

    # Mock load to return dummy audio
    def mock_load(*args, **kwargs):
        return np.random.randn(44100), 44100  # 1 second of audio

    mock_librosa_module.load = mock_load
    monkeypatch.setattr("librosa.load", mock_load)

    return mock_librosa_module


@pytest.fixture
def mock_torch(monkeypatch):
    """Mock PyTorch for GPU tests."""
    import pytest

    pytest.importorskip("unittest.mock")

    from unittest.mock import MagicMock

    mock_torch_module = MagicMock()
    mock_torch_module.cuda.is_available.return_value = False

    monkeypatch.setattr("torch.cuda.is_available", lambda: False)

    return mock_torch_module


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "gpu: marks tests requiring GPU/CUDA")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line(
        "markers", "requires_ffmpeg: marks tests requiring ffmpeg binary"
    )
    config.addinivalue_line(
        "markers", "requires_librosa: marks tests requiring librosa"
    )
    config.addinivalue_line("markers", "requires_pil: marks tests requiring Pillow")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on patterns."""
    for item in items:
        # Mark GPU tests
        if "gpu" in item.nodeid.lower():
            item.add_marker(pytest.mark.gpu)

        # Mark slow tests (can be overridden)
        if "slow" in item.nodeid.lower() or "large" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)

        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


# ============================================================================
# Utility Functions
# ============================================================================


@pytest.fixture
def assert_watermark_present():
    """Helper to assert watermark is present in content."""

    def _assert(content: str, watermark_id: str):
        assert (
            watermark_id in content
        ), f"Watermark ID {watermark_id} not found in content"
        assert "CIAF" in content or "AI Provenance" in content

    return _assert


@pytest.fixture
def assert_hashes_computed():
    """Helper to assert all required hashes are computed."""

    def _assert(evidence):
        assert evidence.hashes is not None
        assert evidence.hashes.content_hash_before_watermark is not None
        assert evidence.hashes.content_hash_after_watermark is not None
        # SHA-256
        assert len(evidence.hashes.content_hash_before_watermark) == 64
        assert len(evidence.hashes.content_hash_after_watermark) == 64

    return _assert


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary directory for test outputs."""
    output_dir = tmp_path / "watermark_outputs"
    output_dir.mkdir()
    return output_dir
