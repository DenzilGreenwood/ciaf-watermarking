"""
CIAF Watermarking - Asynchronous Processing & Caching

Provides background processing capabilities for large file watermarking,
decoupling immediate user response from compute-intensive forensic analysis.

This module enables:
- Immediate watermark delivery to users
- Background forensic fragment generation (DNA, perceptual hashes)
- In-memory caching with TTL for pending artifacts
- Retry logic with idempotency guarantees
- Processing status tracking

Architecture:
    1. User requests watermark → Returns immediately with "Tier 1" watermark
    2. Evidence + artifact cached in Redis/memory
    3. Background worker processes Tier 2 (DNA) and Tier 3 (perceptual hashes)
    4. Worker stores complete evidence in vault
    5. Cache evicted after successful storage

Security Considerations:
    - All cached data should be encrypted at rest
    - Cache TTL prevents memory leaks
    - Verification API returns "Processing" status during window of vulnerability

Created: 2026-04-05
Author: Denzil James Greenwood
Version: 1.0.0
"""

from __future__ import annotations

import threading
import time
from enum import Enum
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import queue

from .models import ArtifactEvidence

# ============================================================================
# PROCESSING STATUS
# ============================================================================


class ProcessingStatus(str, Enum):
    """Status of background forensic processing."""

    PENDING = "pending"  # Queued but not started
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed with error
    RETRY = "retry"  # Scheduled for retry


@dataclass
class ProcessingTask:
    """Represents a background processing task."""

    artifact_id: str
    evidence: ArtifactEvidence
    artifact: Union[str, bytes]
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    priority: int = 0  # Higher = higher priority (for legal-grade requests)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "artifact_id": self.artifact_id,
            "evidence": self.evidence.to_dict(),
            "artifact": (self.artifact if isinstance(self.artifact, str) else self.artifact.hex()),
            "artifact_is_bytes": isinstance(self.artifact, bytes),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProcessingTask:
        """Reconstruct from dictionary."""
        from .vault_adapter import WatermarkVaultAdapter

        # Reconstruct evidence
        adapter = WatermarkVaultAdapter()
        evidence = adapter._dict_to_evidence(data["evidence"])

        # Reconstruct artifact
        artifact = data["artifact"]
        if data.get("artifact_is_bytes", False):
            artifact = bytes.fromhex(artifact)

        return cls(
            artifact_id=data["artifact_id"],
            evidence=evidence,
            artifact=artifact,
            status=ProcessingStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=(
                datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error_message=data.get("error_message"),
            priority=data.get("priority", 0),
        )


# ============================================================================
# IN-MEMORY CACHE
# ============================================================================


class InMemoryCache:
    """
    Thread-safe in-memory cache for pending tasks.

    Uses TTL to prevent memory leaks. For production, this should be replaced
    with Redis or similar distributed cache.
    """

    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            default_ttl_seconds: Default time-to-live in seconds (default 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl_seconds

        # Start background cleanup thread
        self._cleanup_running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to store
            ttl_seconds: Time-to-live in seconds (uses default if None)
        """
        with self._lock:
            expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds or self.default_ttl)
            self._cache[key] = {
                "value": value,
                "expiry": expiry,
            }

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check expiry
            if datetime.utcnow() > entry["expiry"]:
                del self._cache[key]
                return None

            return entry["value"]

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def _cleanup_loop(self) -> None:
        """Background cleanup of expired entries."""
        while self._cleanup_running:
            time.sleep(60)  # Check every minute

            with self._lock:
                now = datetime.utcnow()
                expired_keys = [key for key, entry in self._cache.items() if now > entry["expiry"]]

                for key in expired_keys:
                    del self._cache[key]

    def shutdown(self) -> None:
        """Stop cleanup thread."""
        self._cleanup_running = False
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2)


# ============================================================================
# BACKGROUND WORKER
# ============================================================================


class BackgroundWorker:
    """
    Background worker for processing forensic fragments.

    Runs in separate thread, picks up tasks from queue, processes them,
    and stores results in vault.
    """

    def __init__(self, cache: InMemoryCache, vault_adapter=None, max_workers: int = 2):
        """
        Initialize background worker.

        Args:
            cache: Cache instance for task storage
            vault_adapter: WatermarkVaultAdapter instance
            max_workers: Maximum concurrent workers
        """
        self.cache = cache
        self.vault_adapter = vault_adapter
        self.max_workers = max_workers

        # Priority queue for tasks
        self._task_queue: queue.PriorityQueue[Any] = queue.PriorityQueue()
        self._running = False
        self._workers: List[threading.Thread] = []

    def start(self) -> None:
        """Start background worker threads."""
        if self._running:
            return

        self._running = True

        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop, name=f"WatermarkWorker-{i}", daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def stop(self) -> None:
        """Stop background workers."""
        self._running = False

        # Wait for workers to finish
        for worker in self._workers:
            if worker.is_alive():
                worker.join(timeout=5)

        self._workers.clear()

    def enqueue_task(self, task: ProcessingTask) -> None:
        """
        Add task to processing queue.

        Args:
            task: ProcessingTask to execute
        """
        # Higher priority = lower number for queue (inverted)
        priority = -task.priority
        self._task_queue.put((priority, task.artifact_id, task))

        # Cache the task
        self.cache.set(f"task:{task.artifact_id}", task.to_dict(), ttl_seconds=7200)  # 2 hours

    def _worker_loop(self) -> None:
        """Main worker loop - processes tasks from queue."""
        while self._running:
            try:
                # Get task with timeout
                try:
                    _, artifact_id, task = self._task_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # Update status to processing
                task.status = ProcessingStatus.PROCESSING
                task.started_at = datetime.utcnow()
                self.cache.set(f"task:{artifact_id}", task.to_dict())

                # Process the task
                try:
                    self._process_task(task)

                    # Mark as completed
                    task.status = ProcessingStatus.COMPLETED
                    task.completed_at = datetime.utcnow()
                    self.cache.set(f"task:{artifact_id}", task.to_dict())

                    # Clean up after successful completion
                    # Keep task for 10 minutes for status queries
                    self.cache.set(f"task:{artifact_id}", task.to_dict(), ttl_seconds=600)

                except Exception as e:
                    # Handle failure
                    task.error_message = str(e)

                    if task.retry_count < task.max_retries:
                        # Retry
                        task.retry_count += 1
                        task.status = ProcessingStatus.RETRY
                        self.enqueue_task(task)
                    else:
                        # Max retries reached
                        task.status = ProcessingStatus.FAILED
                        self.cache.set(f"task:{artifact_id}", task.to_dict())

            except Exception as e:
                # Worker error - log and continue
                print(f"Worker error: {e}")

    def _process_task(self, task: ProcessingTask) -> None:
        """
        Process a single task - generate forensic fragments.

        Args:
            task: Task to process
        """
        from .advanced_features import enhance_evidence_with_forensic_fragments

        # Generate advanced forensic fragments (Tier 2 & 3)
        enhanced_evidence = enhance_evidence_with_forensic_fragments(
            evidence=task.evidence, raw_artifact=task.artifact
        )

        # Store in vault
        if self.vault_adapter:
            success = self.vault_adapter.store_evidence(enhanced_evidence)
            if not success:
                raise RuntimeError("Failed to store evidence in vault")

        # Update task with enhanced evidence
        task.evidence = enhanced_evidence


# ============================================================================
# ASYNC WATERMARK INTERFACE
# ============================================================================


# Global instances (singleton pattern)
_GLOBAL_CACHE: Optional[InMemoryCache] = None
_GLOBAL_WORKER: Optional[BackgroundWorker] = None


def get_async_infrastructure() -> tuple[InMemoryCache, BackgroundWorker]:
    """
    Get or create global async infrastructure.

    Returns:
        Tuple of (cache, worker)
    """
    global _GLOBAL_CACHE, _GLOBAL_WORKER

    if _GLOBAL_CACHE is None:
        _GLOBAL_CACHE = InMemoryCache(default_ttl_seconds=3600)

    if _GLOBAL_WORKER is None:
        from .vault_adapter import create_watermark_vault

        vault = create_watermark_vault()
        _GLOBAL_WORKER = BackgroundWorker(cache=_GLOBAL_CACHE, vault_adapter=vault, max_workers=2)
        _GLOBAL_WORKER.start()

    return _GLOBAL_CACHE, _GLOBAL_WORKER


def watermark_ai_output_async(
    artifact: Union[str, bytes],
    model_id: str,
    model_version: str,
    actor_id: str,
    prompt: str,
    verification_base_url: str,
    priority: int = 0,
    **kwargs,
) -> tuple[ArtifactEvidence, Union[str, bytes], str]:
    """
    Watermark artifact with asynchronous forensic processing.

    Returns watermarked artifact immediately while processing advanced
    forensic fragments in background.

    Args:
        artifact: Raw AI output
        model_id: Model identifier
        model_version: Model version
        actor_id: User/system identifier
        prompt: Input prompt
        verification_base_url: Vault verification URL
        priority: Processing priority (0=normal, higher=urgent)
        **kwargs: Additional watermark configuration

    Returns:
        Tuple of (evidence, watermarked_artifact, task_id):
            - evidence: Initial evidence (before forensic enhancement)
            - watermarked_artifact: Watermarked output
            - task_id: Background task ID for status checking

    Example:
        >>> evidence, watermarked, task_id = watermark_ai_output_async(
        ...     artifact=large_pdf_bytes,
        ...     model_id="pdf-gen-v2",
        ...     model_version="1.0",
        ...     actor_id="user:123",
        ...     prompt="Generate report",
        ...     verification_base_url="https://vault.example.com",
        ...     priority=1  # High priority
        ... )
        >>> # Watermarked artifact returned immediately
        >>> # Check processing status later:
        >>> status = get_processing_status(task_id)
    """
    from .unified_interface import watermark_ai_output

    # Step 1: Create immediate watermark (without expensive forensics)
    evidence, watermarked = watermark_ai_output(
        artifact=artifact,
        model_id=model_id,
        model_version=model_version,
        actor_id=actor_id,
        prompt=prompt,
        verification_base_url=verification_base_url,
        enable_forensic_fragments=False,  # Skip expensive processing
        store_in_vault=False,  # Don't store yet
        **kwargs,
    )

    # Step 2: Create background task for forensic processing
    task = ProcessingTask(
        artifact_id=evidence.artifact_id,
        evidence=evidence,
        artifact=artifact,
        priority=priority,
    )

    # Step 3: Enqueue for background processing
    cache, worker = get_async_infrastructure()
    worker.enqueue_task(task)

    # Step 4: Return immediately
    return evidence, watermarked, evidence.artifact_id


def get_processing_status(artifact_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of background processing task.

    Args:
        artifact_id: Artifact/task identifier

    Returns:
        Status dictionary or None if not found
    """
    cache, _ = get_async_infrastructure()

    task_data = cache.get(f"task:{artifact_id}")
    if task_data:
        return {
            "artifact_id": task_data["artifact_id"],
            "status": task_data["status"],
            "created_at": task_data["created_at"],
            "started_at": task_data["started_at"],
            "completed_at": task_data["completed_at"],
            "retry_count": task_data["retry_count"],
            "error_message": task_data["error_message"],
        }

    return None


def finalize_forensics_offline(artifact_id: str) -> bool:
    """
    Manually trigger forensic finalization for an artifact.

    Use this for synchronous "legal-grade" requests that require
    immediate complete forensic analysis.

    Args:
        artifact_id: Artifact identifier

    Returns:
        True if successful, False otherwise
    """
    cache, worker = get_async_infrastructure()

    task_data = cache.get(f"task:{artifact_id}")
    if not task_data:
        return False

    try:
        task = ProcessingTask.from_dict(task_data)
        worker._process_task(task)
        return True
    except Exception as e:
        print(f"Error finalizing forensics: {e}")
        return False


__all__ = [
    "ProcessingStatus",
    "ProcessingTask",
    "InMemoryCache",
    "BackgroundWorker",
    "watermark_ai_output_async",
    "get_processing_status",
    "finalize_forensics_offline",
    "get_async_infrastructure",
]
