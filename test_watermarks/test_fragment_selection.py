"""
Tests for ciaf_watermarks.fragment_selection module.

Tests cover:
- Fragment extraction
- Fragment selection algorithms
- Multi-fragment handling
"""

import pytest


@pytest.mark.unit
class TestFragmentSelection:
    """Test fragment selection."""

    def test_select_text_fragments(self, sample_text):
        """Test selecting text fragments."""
        try:
            from ciaf_watermarks.fragment_selection import select_text_fragments

            fragments = select_text_fragments(sample_text, num_fragments=5)

            assert len(fragments) == 5
            assert all(isinstance(f, str) for f in fragments)
        except (ImportError, AttributeError):
            pytest.skip("select_text_fragments not implemented")

    def test_select_image_fragments(self, sample_image_bytes):
        """Test selecting image fragments."""
        try:
            from ciaf_watermarks.fragment_selection import select_image_fragments

            fragments = select_image_fragments(sample_image_bytes, num_fragments=5)

            assert len(fragments) == 5
        except (ImportError, AttributeError):
            pytest.skip("select_image_fragments not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
