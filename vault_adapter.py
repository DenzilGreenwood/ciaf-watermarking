"""
CIAF Watermarking - Vault Storage Adapter

Integration layer between watermarking system and CIAF vault storage.

Provides:
- Storage of ArtifactEvidence records
- Retrieval by artifact ID, model ID, watermark ID
- Batch operations
- Search functionality

Created: 2026-03-24
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from pathlib import Path
import json

from .models import ArtifactEvidence, ArtifactType, WatermarkType


class WatermarkVaultAdapter:
    """
    Adapter for storing watermark evidence in CIAF vault.

    Supports both file-based and PostgreSQL vault backends.
    """

    def __init__(self, vault_storage=None, storage_path: str = "ciaf_vault/watermarks"):
        """
        Initialize vault adapter.

        Args:
            vault_storage: MetadataStorage instance (optional)
            storage_path: Path for file-based storage if vault_storage not provided
        """
        self.vault_storage = vault_storage
        self.storage_path = Path(storage_path)

        if not vault_storage:
            # Use simple file-based storage
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._use_files = True
        else:
            self._use_files = False

    def store_evidence(self, evidence: ArtifactEvidence) -> bool:
        """
        Store artifact evidence in vault.

        Args:
            evidence: ArtifactEvidence to store

        Returns:
            True if successful
        """
        if self._use_files:
            return self._store_evidence_file(evidence)
        else:
            return self._store_evidence_vault(evidence)

    def _store_evidence_file(self, evidence: ArtifactEvidence) -> bool:
        """Store evidence as JSON file."""
        try:
            file_path = self.storage_path / f"{evidence.artifact_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(evidence.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error storing evidence to file: {e}")
            return False

    def _store_evidence_vault(self, evidence: ArtifactEvidence) -> bool:
        """Store evidence in vault storage."""
        try:
            # Store in vault's watermark/artifact table
            evidence_dict = evidence.to_dict()

            # Use vault's storage API
            self.vault_storage.save_metadata(
                model_name=evidence.model_id,
                stage="watermarking",
                event_type="artifact_created",
                metadata={
                    "artifact_id": evidence.artifact_id,
                    "artifact_type": evidence.artifact_type.value,
                    "watermark_id": evidence.watermark.watermark_id,
                    "watermark_type": evidence.watermark.watermark_type.value,
                    "evidence": evidence_dict,
                },
            )
            return True
        except Exception as e:
            print(f"Error storing evidence to vault: {e}")
            return False

    def retrieve_evidence(self, artifact_id: str) -> Optional[ArtifactEvidence]:
        """
        Retrieve evidence by artifact ID.

        Args:
            artifact_id: Artifact identifier

        Returns:
            ArtifactEvidence if found, None otherwise
        """
        if self._use_files:
            return self._retrieve_evidence_file(artifact_id)
        else:
            return self._retrieve_evidence_vault(artifact_id)

    def _retrieve_evidence_file(self, artifact_id: str) -> Optional[ArtifactEvidence]:
        """Retrieve evidence from JSON file."""
        try:
            file_path = self.storage_path / f"{artifact_id}.json"
            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return self._dict_to_evidence(data)
        except Exception as e:
            print(f"Error retrieving evidence from file: {e}")
            return None

    def _retrieve_evidence_vault(self, artifact_id: str) -> Optional[ArtifactEvidence]:
        """Retrieve evidence from vault storage with indexed query."""
        try:
            # PERFORMANCE FIX: Use indexed query instead of iterating all records
            # If vault supports SQL-like queries, use WHERE clause
            if hasattr(self.vault_storage, "query_metadata"):
                # Use indexed query if available
                results = self.vault_storage.query_metadata(
                    filters={"artifact_id": artifact_id}, limit=1
                )
                if results:
                    evidence_dict = results[0].get("metadata", {}).get("evidence")
                    if evidence_dict:
                        return self._dict_to_evidence(evidence_dict)
                return None

            # Fallback: Search vault for artifact (less efficient, but works)
            # NOTE: This will be slow for large vaults - recommend adding indexed queries
            records = self.vault_storage.get_model_metadata(limit=100)

            for record in records:
                metadata = record.get("metadata", {})
                if metadata.get("artifact_id") == artifact_id:
                    evidence_dict = metadata.get("evidence")
                    if evidence_dict:
                        return self._dict_to_evidence(evidence_dict)

            return None
        except Exception as e:
            print(f"Error retrieving evidence from vault: {e}")
            return None

    def search_by_model(
        self, model_id: str, model_version: Optional[str] = None, limit: int = 100
    ) -> List[ArtifactEvidence]:
        """
        Search for artifacts by model.

        Args:
            model_id: Model identifier
            model_version: Model version (optional)
            limit: Maximum results

        Returns:
            List of ArtifactEvidence records
        """
        if self._use_files:
            return self._search_by_model_file(model_id, model_version, limit)
        else:
            return self._search_by_model_vault(model_id, model_version, limit)

    def _search_by_model_file(
        self, model_id: str, model_version: Optional[str], limit: int
    ) -> List[ArtifactEvidence]:
        """Search files by model."""
        results = []

        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if data.get("model_id") == model_id:
                    if (
                        model_version is None
                        or data.get("model_version") == model_version
                    ):
                        evidence = self._dict_to_evidence(data)
                        results.append(evidence)

                        if len(results) >= limit:
                            break
            except Exception:
                continue

        return results

    def _search_by_model_vault(
        self, model_id: str, model_version: Optional[str], limit: int
    ) -> List[ArtifactEvidence]:
        """Search vault by model."""
        results = []

        try:
            records = self.vault_storage.get_model_metadata(
                model_name=model_id, limit=limit
            )

            for record in records:
                metadata = record.get("metadata", {})
                evidence_dict = metadata.get("evidence")

                if evidence_dict:
                    if (
                        model_version is None
                        or evidence_dict.get("model_version") == model_version
                    ):
                        evidence = self._dict_to_evidence(evidence_dict)
                        results.append(evidence)

        except Exception as e:
            print(f"Error searching vault: {e}")

        return results

    def search_by_watermark(self, watermark_id: str) -> Optional[ArtifactEvidence]:
        """
        Find artifact by watermark ID.

        Args:
            watermark_id: Watermark identifier

        Returns:
            ArtifactEvidence if found
        """
        if self._use_files:
            # Search all files
            for file_path in self.storage_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if data.get("watermark", {}).get("watermark_id") == watermark_id:
                        return self._dict_to_evidence(data)
                except Exception:
                    continue
        else:
            # Search vault with indexed query
            try:
                # PERFORMANCE FIX: Use indexed query if available
                if hasattr(self.vault_storage, "query_metadata"):
                    results = self.vault_storage.query_metadata(
                        filters={"watermark_id": watermark_id}, limit=1
                    )
                    if results:
                        evidence_dict = results[0].get("metadata", {}).get("evidence")
                        if evidence_dict:
                            return self._dict_to_evidence(evidence_dict)
                    return None

                # Fallback: Iterate (slower)
                records = self.vault_storage.get_model_metadata(limit=1000)

                for record in records:
                    metadata = record.get("metadata", {})
                    if metadata.get("watermark_id") == watermark_id:
                        evidence_dict = metadata.get("evidence")
                        if evidence_dict:
                            return self._dict_to_evidence(evidence_dict)
            except Exception as e:
                print(f"Error searching vault by watermark: {e}")

        return None

    def _dict_to_evidence(self, data: Dict[str, Any]) -> ArtifactEvidence:
        """Convert dictionary to ArtifactEvidence object."""
        from .models import (
            ArtifactHashSet,
            WatermarkDescriptor,
            ArtifactFingerprint,
        )

        # Reconstruct hash set
        hashes_data = data["hashes"]
        hashes = ArtifactHashSet(
            content_hash_before_watermark=hashes_data["content_hash_before_watermark"],
            content_hash_after_watermark=hashes_data["content_hash_after_watermark"],
            canonical_receipt_hash=hashes_data.get("canonical_receipt_hash"),
            normalized_hash_before=hashes_data.get("normalized_hash_before"),
            normalized_hash_after=hashes_data.get("normalized_hash_after"),
            perceptual_hash_before=hashes_data.get("perceptual_hash_before"),
            perceptual_hash_after=hashes_data.get("perceptual_hash_after"),
            simhash_before=hashes_data.get("simhash_before"),
            simhash_after=hashes_data.get("simhash_after"),
        )

        # Reconstruct watermark descriptor
        wm_data = data["watermark"]
        watermark = WatermarkDescriptor(
            watermark_id=wm_data["watermark_id"],
            watermark_type=WatermarkType(wm_data["watermark_type"]),
            tag_text=wm_data.get("tag_text"),
            verification_url=wm_data.get("verification_url"),
            qr_payload=wm_data.get("qr_payload"),
            metadata_fields=wm_data.get("metadata_fields", {}),
            embed_method=wm_data.get("embed_method"),
            removal_resistance=wm_data.get("removal_resistance"),
            location=wm_data.get("location"),
        )

        # Reconstruct fingerprints
        fingerprints = []
        for fp_data in data.get("fingerprints", []):
            fingerprints.append(
                ArtifactFingerprint(
                    algorithm=fp_data["algorithm"],
                    value=fp_data["value"],
                    role=fp_data["role"],
                    confidence=fp_data.get("confidence"),
                )
            )

        # Create evidence object
        evidence = ArtifactEvidence(
            artifact_id=data["artifact_id"],
            artifact_type=ArtifactType(data["artifact_type"]),
            mime_type=data["mime_type"],
            created_at=data["created_at"],
            model_id=data["model_id"],
            model_version=data["model_version"],
            actor_id=data["actor_id"],
            prompt_hash=data["prompt_hash"],
            output_hash_raw=data["output_hash_raw"],
            output_hash_distributed=data["output_hash_distributed"],
            watermark=watermark,
            hashes=hashes,
            fingerprints=fingerprints,
            metadata=data.get("metadata", {}),
            prior_receipt_hash=data.get("prior_receipt_hash"),
            signature=data.get("signature"),
            merkle_leaf_hash=data.get("merkle_leaf_hash"),
        )

        return evidence

    def count_artifacts(self, model_id: Optional[str] = None) -> int:
        """
        Count stored artifacts.

        Args:
            model_id: Filter by model (optional)

        Returns:
            Number of artifacts
        """
        if self._use_files:
            if model_id:
                return len(self._search_by_model_file(model_id, None, 10000))
            else:
                return len(list(self.storage_path.glob("*.json")))
        else:
            # For vault, estimate from metadata
            try:
                records = self.vault_storage.get_model_metadata(
                    model_name=model_id if model_id else None, limit=10000
                )
                return len(records)
            except Exception:
                return 0

    def list_models(self) -> List[str]:
        """
        List all models with stored artifacts.

        Returns:
            List of model IDs
        """
        models = set()

        if self._use_files:
            for file_path in self.storage_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    models.add(data.get("model_id"))
                except Exception:
                    continue
        else:
            try:
                records = self.vault_storage.get_model_metadata(limit=1000)
                for record in records:
                    models.add(record.get("model_name"))
            except Exception:
                pass

        return sorted(list(models))


def create_watermark_vault(
    vault_storage=None, storage_path: str = "ciaf_vault/watermarks"
) -> WatermarkVaultAdapter:
    """
    Factory function to create watermark vault adapter.

    Args:
        vault_storage: MetadataStorage instance (optional)
        storage_path: Path for file storage

    Returns:
        WatermarkVaultAdapter instance
    """
    return WatermarkVaultAdapter(vault_storage=vault_storage, storage_path=storage_path)


__all__ = [
    "WatermarkVaultAdapter",
    "create_watermark_vault",
]
