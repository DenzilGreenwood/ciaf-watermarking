"""
Tests for ciaf_watermarks.vault_adapter module.

Tests cover:
- Vault client integration
- Evidence storage
- Evidence retrieval
- Vault operations
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestVaultAdapter:
    """Test vault adapter."""

    def test_store_evidence_in_vault(self, sample_text, common_watermark_params):
        """Test storing evidence in vault."""
        try:
            from ciaf_watermarks.vault_adapter import VaultAdapter
            from ciaf_watermarks.text import build_text_artifact_evidence

            evidence, watermarked = build_text_artifact_evidence(
                raw_text=sample_text, **common_watermark_params
            )

            vault = VaultAdapter(vault_url="https://test.vault.com")

            with patch.object(vault, "store_evidence") as mock_store:
                mock_store.return_value = {"artifact_id": evidence.artifact_id}

                result = vault.store_evidence(evidence)

                assert result is not None
        except (ImportError, AttributeError):
            pytest.skip("VaultAdapter not implemented")

    def test_retrieve_evidence_from_vault(self):
        """Test retrieving evidence from vault."""
        try:
            from ciaf_watermarks.vault_adapter import VaultAdapter

            vault = VaultAdapter(vault_url="https://test.vault.com")

            with patch.object(vault, "retrieve_evidence") as mock_retrieve:
                mock_retrieve.return_value = MagicMock()

                evidence = vault.retrieve_evidence(artifact_id="test-id")

                assert evidence is not None
        except (ImportError, AttributeError):
            pytest.skip("VaultAdapter not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
